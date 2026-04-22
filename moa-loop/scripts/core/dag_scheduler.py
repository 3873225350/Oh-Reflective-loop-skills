#!/usr/bin/env python3
"""
MOA Loop v2.0 - DAG Scheduler (横向DAG调度核心)

设计思想:
  横向任务基于DAG组织，节点=子任务，边=依赖关系。
  无依赖节点并行执行（= Data Parallelism）
  有依赖节点串行等待（= Pipeline Parallelism）
  核心目标: 在依赖约束下，并行最大化、串行最小化。
"""

import json
import threading
import concurrent.futures
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime
from pathlib import Path
import fnmatch


@dataclass
class DAGNode:
    """DAG节点 = 一个子任务"""
    id: str
    task_type: str = "default"          # coding/writing/analysis/research/quick
    agent: Optional[str] = None         # 指定agent，None则按task_type路由
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"             # pending/running/done/failed
    result: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_type": self.task_type,
            "agent": self.agent,
            "dependencies": self.dependencies,
            "status": self.status,
            "result": self.result,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DAGNode":
        return cls(
            id=d["id"],
            task_type=d.get("task_type", "default"),
            agent=d.get("agent"),
            dependencies=d.get("dependencies", []),
            status=d.get("status", "pending"),
            result=d.get("result"),
            started_at=d.get("started_at"),
            completed_at=d.get("completed_at"),
        )


@dataclass
class DAG:
    """有向无环图"""
    nodes: Dict[str, DAGNode] = field(default_factory=dict)

    def add_node(self, node: DAGNode):
        self.nodes[node.id] = node

    def remove_node(self, node_id: str):
        self.nodes.pop(node_id, None)
        for node in self.nodes.values():
            if node_id in node.dependencies:
                node.dependencies.remove(node_id)

    def get_entry_nodes(self) -> List[DAGNode]:
        """获取无依赖的入口节点（可立即并行执行）"""
        return [n for n in self.nodes.values() if not n.dependencies]

    def get_dependents(self, node_id: str) -> List[DAGNode]:
        """获取依赖于指定节点的下游节点"""
        return [n for n in self.nodes.values() if node_id in n.dependencies]

    def to_dict(self) -> dict:
        return {"nodes": {nid: n.to_dict() for nid, n in self.nodes.items()}}

    @classmethod
    def from_dict(cls, d: dict) -> "DAG":
        dag = cls()
        for nid, ndata in d.get("nodes", {}).items():
            dag.add_node(DAGNode.from_dict(ndata))
        return dag

    @classmethod
    def from_config(cls, config: dict) -> "DAG":
        """从config.json的dag字段构建DAG"""
        dag = cls()
        for node_def in config.get("nodes", []):
            dag.add_node(DAGNode(
                id=node_def["id"],
                task_type=node_def.get("type", "default"),
                agent=node_def.get("agent"),
                dependencies=node_def.get("deps", []),
            ))
        return dag


class DAGScheduler:
    """
    DAG调度器 — 横向核心

    职责:
    - 拓扑排序，检测环
    - 按依赖关系分层: 同层并行，层间串行
    - 调度Agent执行节点任务
    - 收集结果，推进DAG状态
    """

    def __init__(self, dag: DAG):
        self.dag = dag
        self._lock = threading.RLock()

    # ==================== 拓扑分析 ====================

    def topological_sort(self) -> List[List[str]]:
        """
        拓扑排序，返回分层结果。
        每层内的节点无互相依赖，可并行执行。
        层间有依赖，必须串行等待。

        例:
            Layer 0: [research]                    ← 入口节点
            Layer 1: [code]                        ← 依赖 research
            Layer 2: [test, doc]                   ← 依赖 code，互相独立可并行
            Layer 3: [review]                      ← 依赖 test + doc
        """
        import concurrent.futures

        in_degree = {nid: 0 for nid in self.dag.nodes}
        for node in self.dag.nodes.values():
            for dep in node.dependencies:
                if dep in self.dag.nodes:
                    in_degree[node.id] += 1

        layers = []
        remaining = set(self.dag.nodes.keys())

        while remaining:
            # 当前层: 入度为0的节点
            layer = [nid for nid in remaining if in_degree[nid] == 0]
            if not layer:
                raise ValueError(f"DAG has cycle! Remaining nodes: {remaining}")
            layers.append(layer)
            for nid in layer:
                remaining.remove(nid)
                # 减少下游节点的入度
                for dependent in self.dag.get_dependents(nid):
                    if dependent.id in in_degree:
                        in_degree[dependent.id] -= 1

        return layers

    def detect_cycle(self) -> bool:
        """检测DAG中是否有环"""
        try:
            self.topological_sort()
            return False
        except ValueError:
            return True

    def get_parallelism_info(self) -> dict:
        """获取并行度分析"""
        layers = self.topological_sort()
        return {
            "total_nodes": len(self.dag.nodes),
            "total_layers": len(layers),
            "max_parallelism": max(len(layer) for layer in layers) if layers else 0,
            "layers": [
                {"layer": i, "nodes": layer, "parallelism": len(layer)}
                for i, layer in enumerate(layers)
            ],
            "critical_path_length": len(layers),
        }

    # ==================== 调度状态管理 ====================

    def get_ready_nodes(self) -> List[DAGNode]:
        """获取当前可执行的节点（所有依赖已完成）"""
        with self._lock:
            ready = []
            for node in self.dag.nodes.values():
                if node.status != "pending":
                    continue
                deps_done = all(
                    self.dag.nodes[dep].status == "done"
                    for dep in node.dependencies
                    if dep in self.dag.nodes
                )
                if deps_done:
                    ready.append(node)
            return ready

    def mark_running(self, node_id: str):
        with self._lock:
            node = self.dag.nodes.get(node_id)
            if node:
                node.status = "running"
                node.started_at = datetime.now().isoformat()

    def mark_done(self, node_id: str, result: str = ""):
        with self._lock:
            node = self.dag.nodes.get(node_id)
            if node:
                node.status = "done"
                node.result = result
                node.completed_at = datetime.now().isoformat()

    def mark_failed(self, node_id: str, error: str = ""):
        with self._lock:
            node = self.dag.nodes.get(node_id)
            if node:
                node.status = "failed"
                node.result = error
                node.completed_at = datetime.now().isoformat()

    def is_complete(self) -> bool:
        """所有节点是否完成"""
        return all(n.status == "done" for n in self.dag.nodes.values())

    def has_failure(self) -> bool:
        """是否有失败节点"""
        return any(n.status == "failed" for n in self.dag.nodes.values())

    def get_progress(self) -> dict:
        """获取执行进度"""
        statuses = {}
        for node in self.dag.nodes.values():
            statuses.setdefault(node.status, 0)
            statuses[node.status] += 1
        total = len(self.dag.nodes)
        done = statuses.get("done", 0)
        return {
            "total": total,
            "done": done,
            "pending": statuses.get("pending", 0),
            "running": statuses.get("running", 0),
            "failed": statuses.get("failed", 0),
            "progress_pct": round(done / total * 100, 1) if total else 0,
        }

    # ==================== 执行调度 ====================

    def execute(self,
                executor: Callable[[DAGNode], str],
                max_parallel: int = 3,
                on_node_start: Optional[Callable] = None,
                on_node_done: Optional[Callable] = None,
                on_node_fail: Optional[Callable] = None) -> dict:
        """
        按DAG依赖关系执行所有节点。

        执行策略:
        - 按拓扑分层，层内并行（受max_parallel限制），层间串行
        - 无依赖节点: 并行执行（= Data Parallelism）
        - 有依赖节点: 等待前置完成后执行（= Pipeline Parallelism）

        Args:
            executor: 执行函数，接收DAGNode，返回结果字符串
            max_parallel: 最大并行度
            on_node_start/done/fail: 回调钩子

        Returns:
            执行摘要 dict
        """
        summary = {
            "started_at": datetime.now().isoformat(),
            "total": len(self.dag.nodes),
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
        }

        while not self.is_complete():
            ready = self.get_ready_nodes()
            if not ready:
                if self.has_failure():
                    # 有失败且无更多可执行节点 → 跳过剩余
                    for n in self.dag.nodes.values():
                        if n.status == "pending":
                            n.status = "failed"
                            n.result = "skipped_due_to_upstream_failure"
                            summary["skipped"] += 1
                    break
                break

            # 限制并行度
            batch = ready[:max_parallel]

            if len(batch) == 1:
                # 单节点直接执行，避免线程池开销
                node = batch[0]
                self.mark_running(node.id)
                if on_node_start:
                    on_node_start(node)
                try:
                    result = executor(node)
                    self.mark_done(node.id, result)
                    summary["succeeded"] += 1
                    if on_node_done:
                        on_node_done(node, result)
                except Exception as e:
                    self.mark_failed(node.id, str(e))
                    summary["failed"] += 1
                    if on_node_fail:
                        on_node_fail(node, str(e))
            else:
                # 多节点并行执行
                with concurrent.futures.ThreadPoolExecutor(max_workers=len(batch)) as pool:
                    futures = {}
                    for node in batch:
                        self.mark_running(node.id)
                        if on_node_start:
                            on_node_start(node)
                        futures[pool.submit(executor, node)] = node

                    for future in concurrent.futures.as_completed(futures):
                        node = futures[future]
                        try:
                            result = future.result()
                            self.mark_done(node.id, result)
                            summary["succeeded"] += 1
                            if on_node_done:
                                on_node_done(node, result)
                        except Exception as e:
                            self.mark_failed(node.id, str(e))
                            summary["failed"] += 1
                            if on_node_fail:
                                on_node_fail(node, str(e))

        summary["completed_at"] = datetime.now().isoformat()
        summary["progress"] = self.get_progress()
        return summary

    # ==================== 持久化 ====================

    def save(self, path: str):
        """持久化DAG状态到JSON"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.dag.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "DAGScheduler":
        """从JSON加载DAG状态"""
        with open(path) as f:
            data = json.load(f)
        return cls(DAG.from_dict(data))

    def visualize_ascii(self) -> str:
        """ASCII可视化DAG分层结构"""
        layers = self.topological_sort()
        lines = ["DAG Execution Plan:"]
        for i, layer in enumerate(layers):
            nodes_str = " | ".join(
                f"[{nid}:{self.dag.nodes[nid].status}]"
                for nid in layer
            )
            parallel_tag = "PARALLEL" if len(layer) > 1 else "SERIAL"
            lines.append(f"  Layer {i} ({parallel_tag}): {nodes_str}")
        return "\n".join(lines)


# ==================== CLI ====================

def main():
    """CLI入口: 分析DAG配置"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: dag_scheduler.py <config.json> [--visualize|--analyze]")
        sys.exit(1)

    config_path = sys.argv[1]
    with open(config_path) as f:
        config = json.load(f)

    dag = DAG.from_config(config)
    scheduler = DAGScheduler(dag)

    if scheduler.detect_cycle():
        print("ERROR: DAG contains a cycle!")
        sys.exit(1)

    if "--visualize" in sys.argv:
        print(scheduler.visualize_ascii())
    elif "--analyze" in sys.argv:
        info = scheduler.get_parallelism_info()
        print(json.dumps(info, indent=2))
    else:
        print(scheduler.visualize_ascii())
        print()
        info = scheduler.get_parallelism_info()
        print(f"Total nodes: {info['total_nodes']}")
        print(f"Max parallelism: {info['max_parallelism']}")
        print(f"Critical path: {info['critical_path_length']} layers")


if __name__ == "__main__":
    main()
