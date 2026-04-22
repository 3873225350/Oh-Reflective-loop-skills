#!/usr/bin/env python3
"""
MOA Loop v2.0 - Shared Blackboard (共享黑板)

设计思想:
  横向通信采用中心化共享内存（Shared Blackboard）模式。
  所有Agent统一读写公共状态，不点对点通信。
  N个Agent只需O(1)通道（vs FIFO的O(N²)）。

  优点: 低延迟、高并发、无消息风暴、易于可视化、支持大规模Agent协同。
"""

import json
import threading
import time
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
import copy


@dataclass
class AgentStatus:
    """Agent注册状态"""
    name: str
    capabilities: List[str] = field(default_factory=list)
    status: str = "active"         # active/idle/offline
    registered_at: str = ""
    last_seen: str = ""
    current_task: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "capabilities": self.capabilities,
            "status": self.status,
            "registered_at": self.registered_at,
            "last_seen": self.last_seen,
            "current_task": self.current_task,
            "metadata": self.metadata,
        }


@dataclass
class BlackboardEntry:
    """黑板上的一个条目"""
    key: str
    value: Any
    written_by: str
    timestamp: str
    version: int = 1
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "written_by": self.written_by,
            "timestamp": self.timestamp,
            "version": self.version,
            "tags": self.tags,
        }


class SharedBlackboard:
    """
    共享黑板 — 横向通信核心

    核心设计:
    - 中心化读写，所有Agent访问同一块公共状态
    - 线程安全（RLock保护）
    - 支持 key-value 知识存储
    - 支持 Agent 注册/心跳
    - 支持 订阅/通知模式
    - 支持 快照/持久化
    """

    def __init__(self, persist_path: Optional[str] = None):
        self._knowledge: Dict[str, BlackboardEntry] = {}
        self._agents: Dict[str, AgentStatus] = {}
        self._task_results: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._subscribers: Dict[str, List[Callable]] = {}
        self._persist_path = persist_path
        self._event_log: List[dict] = []

        if persist_path:
            self._load(persist_path)

    # ==================== 知识读写 ====================

    def write(self, agent: str, key: str, value: Any, tags: List[str] = None):
        """
        Agent写入黑板。

        类比ML: 一个op写入计算图的中间结果，
        后续op可以直接读取，无需点对点传递。
        """
        with self._lock:
            now = datetime.now().isoformat()
            existing = self._knowledge.get(key)
            version = existing.version + 1 if existing else 1

            entry = BlackboardEntry(
                key=key,
                value=value,
                written_by=agent,
                timestamp=now,
                version=version,
                tags=tags or [],
            )
            self._knowledge[key] = entry

            self._log_event("write", agent, key, value)

            # 通知订阅者
            self._notify_subscribers(key, entry)

            self._maybe_persist()

    def read(self, key: str, default: Any = None) -> Any:
        """任意Agent读取黑板"""
        with self._lock:
            entry = self._knowledge.get(key)
            return entry.value if entry else default

    def read_entry(self, key: str) -> Optional[BlackboardEntry]:
        """读取完整条目（含元数据）"""
        with self._lock:
            return self._knowledge.get(key)

    def delete(self, key: str):
        """删除条目"""
        with self._lock:
            self._knowledge.pop(key, None)
            self._maybe_persist()

    def list_keys(self, pattern: str = None) -> List[str]:
        """列出所有key，支持简单通配符"""
        with self._lock:
            keys = list(self._knowledge.keys())
            if pattern:
                import fnmatch
                keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]
            return keys

    def query(self, tags: List[str] = None, written_by: str = None) -> Dict[str, Any]:
        """按标签或写入者查询"""
        with self._lock:
            results = {}
            for key, entry in self._knowledge.items():
                if tags and not any(t in entry.tags for t in tags):
                    continue
                if written_by and entry.written_by != written_by:
                    continue
                results[key] = entry.value
            return results

    # ==================== Agent管理 ====================

    def register_agent(self, name: str, capabilities: List[str], metadata: dict = None):
        """注册Agent"""
        with self._lock:
            now = datetime.now().isoformat()
            self._agents[name] = AgentStatus(
                name=name,
                capabilities=capabilities,
                status="active",
                registered_at=now,
                last_seen=now,
                metadata=metadata or {},
            )
            self._log_event("register", name, "", "")
            self._maybe_persist()

    def heartbeat(self, agent: str):
        """Agent心跳更新"""
        with self._lock:
            if agent in self._agents:
                self._agents[agent].last_seen = datetime.now().isoformat()
                self._agents[agent].status = "active"

    def set_agent_idle(self, agent: str):
        """标记Agent为空闲"""
        with self._lock:
            if agent in self._agents:
                self._agents[agent].status = "idle"
                self._agents[agent].current_task = None

    def set_agent_task(self, agent: str, task_id: str):
        """标记Agent正在执行任务"""
        with self._lock:
            if agent in self._agents:
                self._agents[agent].status = "active"
                self._agents[agent].current_task = task_id

    def get_active_agents(self, timeout_seconds: int = 120) -> List[AgentStatus]:
        """获取活跃Agent（超时内有心跳）"""
        with self._lock:
            now = datetime.now().timestamp()
            active = []
            for agent in self._agents.values():
                if agent.status == "offline":
                    continue
                try:
                    last = datetime.fromisoformat(agent.last_seen).timestamp()
                    if now - last < timeout_seconds:
                        active.append(agent)
                except (ValueError, TypeError):
                    active.append(agent)
            return active

    def get_agent_capabilities(self, agent: str) -> List[str]:
        """获取Agent能力列表"""
        with self._lock:
            a = self._agents.get(agent)
            return a.capabilities if a else []

    def route_task(self, task_type: str, routing_table: dict = None) -> Optional[str]:
        """
        根据任务类型路由到最佳Agent。

        优先级: 指定routing_table → Agent能力匹配 → 第一个活跃Agent
        """
        with self._lock:
            active = self.get_active_agents()
            if not active:
                return None

            # 使用路由表
            if routing_table and task_type in routing_table:
                preferred = routing_table[task_type]
                for agent_name in preferred:
                    for a in active:
                        if a.name == agent_name:
                            return agent_name

            # 能力匹配
            for a in active:
                if task_type in a.capabilities:
                    return a.name

            # 兜底: 第一个活跃Agent
            return active[0].name

    # ==================== 任务结果 ====================

    def publish_result(self, agent: str, task_id: str, result: Any):
        """Agent发布任务结果到黑板"""
        with self._lock:
            self._task_results[task_id] = {
                "result": result,
                "completed_by": agent,
                "timestamp": datetime.now().isoformat(),
            }
            self._log_event("result", agent, task_id, str(result)[:200])
            self._maybe_persist()

    def get_result(self, task_id: str) -> Optional[dict]:
        """获取任务结果"""
        with self._lock:
            return self._task_results.get(task_id)

    def list_results(self) -> Dict[str, dict]:
        """列出所有任务结果"""
        with self._lock:
            return copy.deepcopy(self._task_results)

    # ==================== 订阅/通知 ====================

    def subscribe(self, agent: str, key_pattern: str, callback: Callable):
        """订阅key变化通知"""
        with self._lock:
            if key_pattern not in self._subscribers:
                self._subscribers[key_pattern] = []
            self._subscribers[key_pattern].append(callback)

    def _notify_subscribers(self, key: str, entry: BlackboardEntry):
        """通知匹配的订阅者（在锁内调用）"""
        import fnmatch
        for pattern, callbacks in self._subscribers.items():
            if fnmatch.fnmatch(key, pattern):
                for cb in callbacks:
                    try:
                        cb(key, entry)
                    except Exception:
                        pass

    # ==================== 快照/持久化 ====================

    def get_snapshot(self) -> dict:
        """获取黑板完整快照"""
        with self._lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "knowledge": {k: e.to_dict() for k, e in self._knowledge.items()},
                "agents": {k: a.to_dict() for k, a in self._agents.items()},
                "task_results": copy.deepcopy(self._task_results),
                "event_log": self._event_log[-100:],  # 最近100条事件
            }

    def _maybe_persist(self):
        """条件持久化"""
        if self._persist_path:
            self._save(self._persist_path)

    def _save(self, path: str):
        """持久化到JSON文件"""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            snapshot = self.get_snapshot()
            with open(path, "w") as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load(self, path: str):
        """从JSON文件加载"""
        try:
            if not Path(path).exists():
                return
            with open(path) as f:
                data = json.load(f)

            for k, v in data.get("knowledge", {}).items():
                self._knowledge[k] = BlackboardEntry(
                    key=v["key"],
                    value=v["value"],
                    written_by=v["written_by"],
                    timestamp=v["timestamp"],
                    version=v.get("version", 1),
                    tags=v.get("tags", []),
                )

            for k, v in data.get("agents", {}).items():
                self._agents[k] = AgentStatus(
                    name=v["name"],
                    capabilities=v.get("capabilities", []),
                    status=v.get("status", "offline"),
                    registered_at=v.get("registered_at", ""),
                    last_seen=v.get("last_seen", ""),
                    current_task=v.get("current_task"),
                    metadata=v.get("metadata", {}),
                )

            self._task_results = data.get("task_results", {})
            self._event_log = data.get("event_log", [])
        except Exception:
            pass

    # ==================== 事件日志 ====================

    def _log_event(self, event_type: str, agent: str, key: str, value: Any):
        """记录事件"""
        self._event_log.append({
            "type": event_type,
            "agent": agent,
            "key": key,
            "value": str(value)[:200] if value else "",
            "timestamp": datetime.now().isoformat(),
        })
        # 保留最近1000条
        if len(self._event_log) > 1000:
            self._event_log = self._event_log[-1000:]

    def get_event_log(self, limit: int = 50) -> List[dict]:
        """获取事件日志"""
        with self._lock:
            return self._event_log[-limit:]

    # ==================== 可视化 ====================

    def show_summary(self) -> str:
        """黑板状态摘要"""
        lines = [
            "=" * 60,
            "  Shared Blackboard Summary",
            "=" * 60,
            "",
            f"  Knowledge entries: {len(self._knowledge)}",
            f"  Registered agents: {len(self._agents)}",
            f"  Task results: {len(self._task_results)}",
            "",
            "  Active Agents:",
        ]

        active = self.get_active_agents()
        if active:
            for a in active:
                caps = ", ".join(a.capabilities)
                task = a.current_task or "idle"
                lines.append(f"    {a.name}: [{caps}] -> {task}")
        else:
            lines.append("    (none)")

        lines.extend([
            "",
            "  Knowledge Keys:",
        ])
        for key in list(self._knowledge.keys())[:10]:
            entry = self._knowledge[key]
            lines.append(f"    {key} (v{entry.version}, by {entry.written_by})")

        if len(self._knowledge) > 10:
            lines.append(f"    ... and {len(self._knowledge) - 10} more")

        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)


# ==================== CLI ====================

def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: shared_blackboard.py <command> [args...]")
        print("\nCommands:")
        print("  summary [persist_path]       Show summary")
        print("  write <key> <value> <agent>  Write entry")
        print("  read <key>                   Read entry")
        print("  list                         List all keys")
        print("  register <name> <caps>       Register agent")
        print("  agents                       List active agents")
        sys.exit(1)

    cmd = sys.argv[1]
    persist = "/tmp/moa_blackboard.json"
    bb = SharedBlackboard(persist_path=persist)

    if cmd == "summary":
        print(bb.show_summary())
    elif cmd == "write" and len(sys.argv) >= 5:
        bb.write(sys.argv[4], sys.argv[2], sys.argv[3])
        print(f"Written: {sys.argv[2]}")
    elif cmd == "read" and len(sys.argv) >= 3:
        val = bb.read(sys.argv[2])
        print(json.dumps(val, indent=2, ensure_ascii=False) if val else "(empty)")
    elif cmd == "list":
        for k in bb.list_keys():
            print(k)
    elif cmd == "register" and len(sys.argv) >= 4:
        caps = sys.argv[3].split(",")
        bb.register_agent(sys.argv[2], caps)
        print(f"Registered: {sys.argv[2]}")
    elif cmd == "agents":
        for a in bb.get_active_agents():
            print(f"{a.name}: {', '.join(a.capabilities)}")
    else:
        print("Unknown command or missing args")


if __name__ == "__main__":
    main()
