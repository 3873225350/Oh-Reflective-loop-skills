#!/usr/bin/env python3
"""
MOA Loop v2.0 - Main Daemon (DAG驱动的纵向迭代主循环)

架构: 纵向时序迭代 + 横向DAG协同 双层解耦
纵向 = 训练循环 (epoch): optimize/check 交替, Roadmap冻结 + PEFT微调
横向 = 计算图 (DAG): 无依赖并行, 有依赖串行, 共享黑板通信
"""

import os
import sys
import json
import subprocess
import time
import re
from datetime import datetime
from pathlib import Path

# 添加core模块路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from core.dag_scheduler import DAGScheduler, DAG, DAGNode
from core.shared_blackboard import SharedBlackboard
from core.iteration_manager import IterationManager


# ==================== 配置加载 ====================

def load_config() -> dict:
    config_path = SCRIPT_DIR / "config.json"
    with open(config_path) as f:
        return json.load(f)


def detect_available_agents() -> list:
    """检测系统中可用的AI Agent"""
    agent_commands = {
        "gemini": "gemini",
        "claude": "claude",
        "qwen": "qwen",
        "kimi": "kimi",
        "cursor": "cursor",
        "minimax": "mmx",
    }
    available = []
    for agent, cmd in agent_commands.items():
        try:
            result = subprocess.run(
                ["which", cmd], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                available.append(agent)
        except Exception:
            pass
    return available


# ==================== Agent执行器 ====================

class AgentExecutor:
    """Agent调用执行器"""

    def __init__(self, blackboard: SharedBlackboard, config: dict):
        self.blackboard = blackboard
        self.config = config
        self.task_routing = config.get("task_routing", {})
        self.agent_capabilities = config.get("agent_capabilities", {})

    def invoke_agent(self, agent: str, prompt: str) -> str:
        """调用单个Agent执行任务"""
        agent_log_dir = Path(os.environ.get("LOG_DIR", "/tmp/moa_logs"))
        agent_log_dir.mkdir(parents=True, exist_ok=True)
        agent_log = agent_log_dir / f"{agent}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        self.blackboard.set_agent_task(agent, "executing")

        start_time = time.time()
        result_code = -1
        output = ""

        try:
            if agent == "gemini":
                proc = subprocess.run(
                    ["gemini", "--resume", "latest", "--approval-mode", "yolo",
                     "--output-format", "text", prompt],
                    capture_output=True, text=True, timeout=600,
                    cwd=os.environ.get("WORKSPACE", "."),
                )
            elif agent == "claude":
                proc = subprocess.run(
                    ["claude", prompt],
                    capture_output=True, text=True, timeout=600,
                    cwd=os.environ.get("WORKSPACE", "."),
                )
            elif agent == "qwen":
                proc = subprocess.run(
                    ["qwen", "-c", "-p", prompt],
                    capture_output=True, text=True, timeout=600,
                    cwd=os.environ.get("WORKSPACE", "."),
                )
            elif agent == "kimi":
                proc = subprocess.run(
                    ["kimi", "-c", "-p", prompt],
                    capture_output=True, text=True, timeout=600,
                    cwd=os.environ.get("WORKSPACE", "."),
                )
            elif agent == "minimax":
                proc = subprocess.run(
                    ["mmx", "text", "chat", "--non-interactive", "--quiet",
                     "--output", "text", "--message", prompt],
                    capture_output=True, text=True, timeout=600,
                    cwd=os.environ.get("WORKSPACE", "."),
                )
            else:
                return f"Unknown agent: {agent}"

            output = proc.stdout or proc.stderr or ""
            result_code = proc.returncode

        except subprocess.TimeoutExpired:
            output = "Agent timed out (600s)"
            result_code = -1
        except Exception as e:
            output = f"Agent error: {e}"
            result_code = -1

        duration = time.time() - start_time

        # 写入agent日志
        with open(agent_log, "w") as f:
            f.write(f"Agent: {agent}\n")
            f.write(f"Duration: {duration:.1f}s\n")
            f.write(f"Exit code: {result_code}\n")
            f.write(f"Output:\n{output}\n")

        self.blackboard.set_agent_idle(agent)

        if result_code == 0:
            self.blackboard.publish_result(agent, f"agent_{agent}_{int(time.time())}", output)
            return output
        else:
            raise RuntimeError(f"Agent {agent} failed (exit {result_code}): {output[:200]}")

    def route_task(self, task_type: str) -> str:
        """根据任务类型路由到最佳Agent"""
        available = [a.name for a in self.blackboard.get_active_agents()]
        if not available:
            return self.config.get("primary_agent", "gemini")

        # 使用路由表
        preferred = self.task_routing.get(task_type, self.task_routing.get("default", []))
        for agent_name in preferred:
            if agent_name in available:
                return agent_name

        return available[0]


# ==================== DAG节点执行函数 ====================

def make_dag_executor(agent_executor: AgentExecutor,
                      blackboard: SharedBlackboard,
                      iteration_mgr: IterationManager,
                      mode: str,
                      loop_name: str,
                      workspace: str):
    """构造DAG节点执行函数"""

    def execute_node(node: DAGNode) -> str:
        """执行单个DAG节点"""
        # 路由到合适的Agent
        if node.agent:
            agent_name = node.agent
        else:
            agent_name = agent_executor.route_task(node.task_type)

        blackboard.set_agent_task(agent_name, node.id)

        # 构造prompt
        prompt = build_prompt(mode, loop_name, workspace, node, blackboard)

        # 执行
        result = agent_executor.invoke_agent(agent_name, prompt)

        # 如果是check模式，尝试PEFT微调
        if mode == "check" and iteration_mgr.get_current_epoch() > 0:
            try:
                iteration_mgr.adapt_subtask(
                    task_id=node.id,
                    experiment_result={
                        "summary": result[:500],
                        "status": "reviewed",
                        "new_config": {"last_check": datetime.now().isoformat()},
                    },
                    max_changes=iteration_mgr._epoch,
                )
            except Exception:
                pass

        # 写入黑板
        blackboard.write(agent_name, f"node_{node.id}_result", result[:1000],
                         tags=[node.task_type, mode])

        return result

    return execute_node


def build_prompt(mode: str, loop_name: str, workspace: str,
                 node: DAGNode, blackboard: SharedBlackboard) -> str:
    """构造发送给Agent的prompt"""
    role = "implementation" if mode == "optimize" else "checker"

    # 从黑板读取上下文
    context_keys = blackboard.list_keys(pattern=f"node_*")
    context = {}
    for key in context_keys[:10]:
        context[key] = blackboard.read(key)

    return f"""You are the MOA (Mixture of Agents) {role} agent.
Workspace: {workspace}
Loop: {loop_name}
Mode: {mode}
Task Node: {node.id} (type: {node.task_type})

## Your Task
Complete precisely one verifiable slice of work for node {node.id}.

## Context from Shared Blackboard
{json.dumps(context, indent=2, ensure_ascii=False)[:2000]}

## CRITICAL INSTRUCTIONS
1. Complete precisely one verifiable slice of work.
2. MANDATORY: git add and git commit your changes before finishing.
3. Update the roadmap with latest status.
4. You may coordinate with other agents via the shared blackboard.
"""


# ==================== 主循环 ====================

def run():
    """主循环入口"""
    config = load_config()
    loop_name = os.environ.get("LOOP_NAME", "DEFAULT_MOA_ROADMAP")
    workspace = os.environ.get("WORKSPACE", os.getcwd())
    interval = int(os.environ.get("INTERVAL", "60"))

    # 状态目录
    state_dir = Path(workspace) / ".reflective-loop" / "state" / loop_name
    state_dir.mkdir(parents=True, exist_ok=True)
    log_dir = state_dir / "dispatch_logs"
    log_dir.mkdir(exist_ok=True)

    # 初始化三大核心模块
    blackboard = SharedBlackboard(
        persist_path=str(state_dir / "blackboard.json")
    )
    iteration_mgr = IterationManager(
        state_dir=str(state_dir / "iterations"),
        loop_name=loop_name,
    )
    agent_executor = AgentExecutor(blackboard, config)

    # 检测并注册可用Agent
    available = detect_available_agents()
    for agent in available:
        caps = config.get("agent_capabilities", {}).get(agent, {}).get("best_for", ["general"])
        blackboard.register_agent(agent, caps)

    primary = config.get("primary_agent", available[0] if available else "gemini")

    # 设置日志
    active_log = state_dir / "active.log"

    def log(msg: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        epoch = iteration_mgr.get_current_epoch()
        line = f"[{timestamp}] [Epoch:{epoch}] [PROVIDER:moa] {msg}"
        print(line)
        with open(active_log, "a") as f:
            f.write(line + "\n")

    # ========= 启动Banner =========
    log("=" * 60)
    log("  MOA Loop v2.0 — DAG + Blackboard + PEFT")
    log(f"  Loop: {loop_name}")
    log(f"  Available Agents: {', '.join(available) if available else 'None'}")
    log(f"  Primary Agent: {primary}")
    log(f"  Interval: {interval}s")
    log("=" * 60)

    # ========= 主循环 =========
    while True:
        log("NEW EPOCH START")

        # 1. 纵向: 确定模式 (optimize/check交替)
        mode = iteration_mgr.next_mode()
        epoch = iteration_mgr.new_epoch(mode)
        log(f"Epoch {epoch} | Mode: {mode}")

        # 2. 纵向: 加载/冻结Roadmap
        roadmap_path = state_dir / f"{loop_name}.md"
        if roadmap_path.exists():
            with open(roadmap_path) as f:
                roadmap_md = f.read()
            if epoch == 1:
                frozen = iteration_mgr.freeze_roadmap(roadmap_md)
                log(f"Roadmap frozen: {len(frozen)} tasks")

        # 3. 横向: 构建DAG
        dag_config = config.get("dag", {"nodes": []})
        if not dag_config.get("nodes"):
            # 没有DAG配置，创建默认单节点
            dag_config = {"nodes": [
                {"id": "main", "type": "default", "deps": []}
            ]}

        dag = DAG.from_config(dag_config)
        scheduler = DAGScheduler(dag)

        if scheduler.detect_cycle():
            log("ERROR: DAG has cycle, skipping epoch")
            continue

        # 4. 横向: 可视化DAG执行计划
        log("DAG Plan:")
        for line in scheduler.visualize_ascii().split("\n"):
            log(f"  {line}")

        # 5. 横向: 执行DAG
        node_executor = make_dag_executor(
            agent_executor, blackboard, iteration_mgr,
            mode, loop_name, str(workspace)
        )

        max_parallel = config.get("max_parallel", 3)

        def on_start(node):
            log(f"  START: {node.id} (type={node.task_type})")

        def on_done(node, result):
            log(f"  DONE:  {node.id} ({len(result)} chars)")

        def on_fail(node, error):
            log(f"  FAIL:  {node.id} — {error[:100]}")

        summary = scheduler.execute(
            executor=node_executor,
            max_parallel=max_parallel,
            on_node_start=on_start,
            on_node_done=on_done,
            on_node_fail=on_fail,
        )

        # 6. 纵向: 保存快照
        iteration_mgr.snapshot()

        # 7. 报告
        progress = scheduler.get_progress()
        log(f"Epoch {epoch} Complete: {progress['done']}/{progress['total']} "
            f"({progress['progress_pct']}%)")
        log(f"  Succeeded: {summary['succeeded']}, Failed: {summary['failed']}")

        # 写入last_mode
        last_mode_path = state_dir / "last_mode.txt"
        with open(last_mode_path, "w") as f:
            f.write(mode)

        log(f"Resting {interval}s...")
        time.sleep(interval)


if __name__ == "__main__":
    run()
