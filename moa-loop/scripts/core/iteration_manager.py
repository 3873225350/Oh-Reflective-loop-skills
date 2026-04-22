#!/usr/bin/env python3
"""
MOA Loop v2.0 - Iteration Manager (纵向迭代管理 + PEFT思想)

设计思想:
  纵向 = 训练循环 (epoch级别)
  - 严格按照时间顺序，完全串行，一轮推进一轮
  - 数据流转: Markdown → JSON → SQL
  - Roadmap主脊 = 预训练权重（冻结）
  - 实验反思微调 = PEFT/Adapter（只改局部，不动主架构）
  - 每一步状态落盘，支持断点续跑、历史回溯
"""

import json
import re
import os
import sqlite3
import shutil
import threading
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class IterationSnapshot:
    """一次迭代的完整快照"""
    epoch: int
    timestamp: str
    mode: str                         # optimize / check
    roadmap_hash: str                 # 主脊hash，检测是否被非法修改
    frozen_tasks: List[str]           # 冻结的主脊任务ID
    adapter_changes: List[dict]       # 本轮Adapter微调记录
    subtask_status: Dict[str, str]    # subtask → status
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "epoch": self.epoch,
            "timestamp": self.timestamp,
            "mode": self.mode,
            "roadmap_hash": self.roadmap_hash,
            "frozen_tasks": self.frozen_tasks,
            "adapter_changes": self.adapter_changes,
            "subtask_status": self.subtask_status,
            "metrics": self.metrics,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "IterationSnapshot":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class IterationManager:
    """
    纵向迭代管理器 — 纵向核心

    核心设计 (ML训练范式):
    - Roadmap主脊 = 预训练权重（冻结, freeze）
    - Sub-task Adapter = PEFT/LoRA（只训练局部参数）
    - 每轮epoch = optimize + check
    - Markdown → JSON → SQL 数据流转
    - 快照/回溯/断点续跑
    """

    def __init__(self, state_dir: str, loop_name: str = "DEFAULT"):
        self.state_dir = Path(state_dir)
        self.loop_name = loop_name
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self._epoch: int = 0
        self._roadmap_base: Dict = {}           # 冻结的主脊 (= 预训练权重)
        self._roadmap_hash: str = ""            # 主脊hash
        self._adapters: Dict[str, dict] = {}    # PEFT Adapter层
        self._history: List[IterationSnapshot] = []
        self._frozen_task_ids: List[str] = []   # 冻结的任务ID列表
        self._lock = threading.RLock()

        # 数据库路径
        self._db_path = self.state_dir / "iteration.db"
        self._snapshot_dir = self.state_dir / "snapshots"
        self._snapshot_dir.mkdir(exist_ok=True)

        # 初始化
        self._init_db()
        self._load_state()

    # ==================== 数据库初始化 ====================

    def _init_db(self):
        """初始化SQLite数据库 (纵向持久化层)"""
        conn = sqlite3.connect(str(self._db_path))
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS iterations (
                epoch INTEGER PRIMARY KEY,
                timestamp TEXT,
                mode TEXT,
                roadmap_hash TEXT,
                frozen_tasks TEXT,
                adapter_changes TEXT,
                subtask_status TEXT,
                metrics TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS roadmap (
                key TEXT PRIMARY KEY,
                value TEXT,
                frozen INTEGER DEFAULT 0,
                updated_at TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS adapters (
                task_id TEXT PRIMARY KEY,
                adapter_data TEXT,
                epoch INTEGER,
                updated_at TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS subtasks (
                task_id TEXT PRIMARY KEY,
                parent_task TEXT,
                status TEXT DEFAULT 'pending',
                adapter_config TEXT,
                result TEXT,
                epoch INTEGER,
                updated_at TEXT
            )
        """)

        conn.commit()
        conn.close()

    def _load_state(self):
        """从持久化状态恢复"""
        conn = sqlite3.connect(str(self._db_path))
        c = conn.cursor()

        # 恢复epoch
        c.execute("SELECT MAX(epoch) FROM iterations")
        row = c.fetchone()
        if row and row[0] is not None:
            self._epoch = row[0]

        # 恢复roadmap冻结状态
        c.execute("SELECT key, value, frozen FROM roadmap WHERE frozen = 1")
        for key, value, frozen in c.fetchall():
            self._roadmap_base[key] = json.loads(value)
            self._frozen_task_ids.append(key)

        # 恢复adapter
        c.execute("SELECT task_id, adapter_data FROM adapters")
        for task_id, adapter_data in c.fetchall():
            self._adapters[task_id] = json.loads(adapter_data)

        conn.close()

        # 计算roadmap hash
        self._roadmap_hash = self._hash_dict(self._roadmap_base)

        # 恢复历史
        self._load_history()

    def _load_history(self):
        """从数据库加载历史快照"""
        conn = sqlite3.connect(str(self._db_path))
        c = conn.cursor()
        c.execute("SELECT * FROM iterations ORDER BY epoch")
        cols = [d[0] for d in c.description]
        for row in c.fetchall():
            data = dict(zip(cols, row))
            snapshot = IterationSnapshot(
                epoch=data["epoch"],
                timestamp=data["timestamp"],
                mode=data["mode"],
                roadmap_hash=data["roadmap_hash"],
                frozen_tasks=json.loads(data["frozen_tasks"]),
                adapter_changes=json.loads(data["adapter_changes"]),
                subtask_status=json.loads(data["subtask_status"]),
                metrics=json.loads(data["metrics"]) if data["metrics"] else {},
            )
            self._history.append(snapshot)
        conn.close()

    # ==================== Epoch管理 ====================

    def new_epoch(self, mode: str = "optimize") -> int:
        """
        开启新轮次。

        类比ML: 一个新的epoch开始。
        记录当前状态快照，推进epoch计数器。
        """
        with self._lock:
            self._epoch += 1
            now = datetime.now().isoformat()

            # 收集当前subtask状态
            subtask_status = self._get_all_subtask_status()

            # 记录本轮adapter变更（空列表，执行中会填充）
            snapshot = IterationSnapshot(
                epoch=self._epoch,
                timestamp=now,
                mode=mode,
                roadmap_hash=self._roadmap_hash,
                frozen_tasks=list(self._frozen_task_ids),
                adapter_changes=[],
                subtask_status=subtask_status,
            )
            self._history.append(snapshot)

            # 持久化到SQLite
            conn = sqlite3.connect(str(self._db_path))
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO iterations
                (epoch, timestamp, mode, roadmap_hash, frozen_tasks,
                 adapter_changes, subtask_status, metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self._epoch, now, mode, self._roadmap_hash,
                json.dumps(self._frozen_task_ids),
                json.dumps([]),
                json.dumps(subtask_status),
                json.dumps({}),
            ))
            conn.commit()
            conn.close()

            return self._epoch

    def get_current_epoch(self) -> int:
        return self._epoch

    def get_mode(self) -> str:
        """获取当前模式: optimize 或 check"""
        if self._history:
            return self._history[-1].mode
        return "optimize"

    def next_mode(self) -> str:
        """获取下一轮模式（optimize/check交替）"""
        current = self.get_mode()
        return "check" if current == "optimize" else "optimize"

    # ==================== Roadmap冻结 (= 预训练权重) ====================

    def freeze_roadmap(self, roadmap_md: str) -> List[str]:
        """
        冻结Roadmap主脊任务。

        类比ML: 加载预训练权重并冻结参数。
        冻结后主脊不可修改，保证大方向稳定。

        Args:
            roadmap_md: Markdown格式的Roadmap

        Returns:
            被冻结的任务ID列表
        """
        with self._lock:
            # Markdown → JSON 结构化
            tasks = self.markdown_to_json(roadmap_md)

            frozen_ids = []
            conn = sqlite3.connect(str(self._db_path))
            c = conn.cursor()

            for task in tasks:
                task_id = task.get("id", "")
                if not task_id:
                    continue

                self._roadmap_base[task_id] = task
                self._frozen_task_ids.append(task_id)
                frozen_ids.append(task_id)

                # 写入数据库并标记冻结
                c.execute("""
                    INSERT OR REPLACE INTO roadmap (key, value, frozen, updated_at)
                    VALUES (?, ?, 1, ?)
                """, (task_id, json.dumps(task), datetime.now().isoformat()))

            conn.commit()
            conn.close()

            # 更新hash
            self._roadmap_hash = self._hash_dict(self._roadmap_base)

            return frozen_ids

    def is_frozen(self, task_id: str) -> bool:
        """检查任务是否在冻结的主脊中"""
        return task_id in self._frozen_task_ids

    def verify_roadmap_integrity(self) -> bool:
        """
        验证Roadmap主脊完整性。

        类比ML: 验证预训练权重未被非法修改。
        """
        current_hash = self._hash_dict(self._roadmap_base)
        return current_hash == self._roadmap_hash

    # ==================== PEFT Adapter微调 ====================

    def adapt_subtask(self, task_id: str, experiment_result: dict,
                      max_changes: int = 5) -> dict:
        """
        PEFT式微调: 根据实验结果调整子任务。

        类比ML:
        - 只更新Adapter参数（subtask配置），不动Base权重（主脊）
        - 限制每轮最大变更数，防止过度修改
        - 如果task在冻结主脊中，拒绝修改

        Args:
            task_id: 要调整的子任务ID
            experiment_result: 实验结果/反馈
            max_changes: 每轮最大变更数

        Returns:
            Adapter更新记录
        """
        with self._lock:
            # 安全检查: 主脊冻结
            if self.is_frozen(task_id):
                return {
                    "status": "rejected",
                    "reason": f"Task {task_id} is frozen (part of roadmap backbone)",
                    "task_id": task_id,
                }

            # 检查本轮变更数量
            if self._history:
                current_changes = len(self._history[-1].adapter_changes)
                if current_changes >= max_changes:
                    return {
                        "status": "rejected",
                        "reason": f"Max adapter changes ({max_changes}) reached this epoch",
                        "task_id": task_id,
                    }

            now = datetime.now().isoformat()

            # 构建adapter更新
            adapter_update = {
                "task_id": task_id,
                "epoch": self._epoch,
                "timestamp": now,
                "experiment_summary": experiment_result.get("summary", ""),
                "adjustments": experiment_result.get("adjustments", {}),
                "old_config": self._adapters.get(task_id, {}),
                "new_config": experiment_result.get("new_config", {}),
            }

            # 应用adapter更新
            self._adapters[task_id] = experiment_result.get("new_config", {})

            # 持久化adapter
            conn = sqlite3.connect(str(self._db_path))
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO adapters (task_id, adapter_data, epoch, updated_at)
                VALUES (?, ?, ?, ?)
            """, (task_id, json.dumps(self._adapters[task_id]), self._epoch, now))

            # 更新subtask状态
            c.execute("""
                INSERT OR REPLACE INTO subtasks (task_id, status, adapter_config, epoch, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                task_id,
                experiment_result.get("status", "adapted"),
                json.dumps(self._adapters[task_id]),
                self._epoch,
                now,
            ))
            conn.commit()
            conn.close()

            # 记录到当前epoch的adapter_changes
            if self._history:
                self._history[-1].adapter_changes.append(adapter_update)
                # 更新数据库中的adapter_changes
                conn = sqlite3.connect(str(self._db_path))
                c = conn.cursor()
                c.execute("""
                    UPDATE iterations SET adapter_changes = ?
                    WHERE epoch = ?
                """, (json.dumps(self._history[-1].adapter_changes), self._epoch))
                conn.commit()
                conn.close()

            return {
                "status": "adapted",
                "task_id": task_id,
                "epoch": self._epoch,
                "changes": adapter_update,
            }

    def get_adapter(self, task_id: str) -> dict:
        """获取任务的Adapter配置"""
        return self._adapters.get(task_id, {})

    # ==================== Markdown → JSON → SQL ====================

    def markdown_to_json(self, md_text: str) -> List[dict]:
        """
        Markdown → JSON 结构化转换。

        去掉冗余文本，大幅节省token，减少上下文长度。
        """
        tasks = []
        lines = md_text.split("\n")
        current_task = None

        for line in lines:
            # 匹配任务行: - [ ] **T1** — 描述  或  - [x] **T1** — 描述
            match = re.match(
                r"^\s*- \[([ xX])\] \*\*([^*]+)\*\*\s*[—\-]\s*(.*)",
                line
            )
            if match:
                checked, task_id, description = match.groups()
                current_task = {
                    "id": task_id.strip(),
                    "description": description.strip(),
                    "status": "done" if checked.lower() == "x" else "pending",
                    "sub_items": [],
                }
                tasks.append(current_task)
                continue

            # 匹配子项:   - 子任务描述
            if current_task and line.strip().startswith("-") and not re.match(r"^\s*- \[[ xX]\]", line):
                sub_text = line.strip().lstrip("- ").strip()
                if sub_text:
                    current_task["sub_items"].append(sub_text)

        return tasks

    def json_to_sql(self, tasks: List[dict]):
        """JSON → SQL 持久化"""
        conn = sqlite3.connect(str(self._db_path))
        c = conn.cursor()
        for task in tasks:
            c.execute("""
                INSERT OR REPLACE INTO subtasks
                (task_id, status, result, epoch, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                task["id"],
                task.get("status", "pending"),
                task.get("description", ""),
                self._epoch,
                datetime.now().isoformat(),
            ))
        conn.commit()
        conn.close()

    # ==================== 快照/回溯 ====================

    def snapshot(self) -> IterationSnapshot:
        """保存当前状态快照"""
        with self._lock:
            now = datetime.now().isoformat()
            subtask_status = self._get_all_subtask_status()

            snap = IterationSnapshot(
                epoch=self._epoch,
                timestamp=now,
                mode=self.get_mode(),
                roadmap_hash=self._roadmap_hash,
                frozen_tasks=list(self._frozen_task_ids),
                adapter_changes=[] if not self._history else self._history[-1].adapter_changes,
                subtask_status=subtask_status,
            )

            # 保存快照文件
            snap_file = self._snapshot_dir / f"epoch_{self._epoch:04d}.json"
            with open(snap_file, "w") as f:
                json.dump(snap.to_dict(), f, indent=2, ensure_ascii=False)

            return snap

    def rollback(self, target_epoch: int) -> bool:
        """
        回溯到指定epoch。

        类比ML: 恢复到之前的checkpoint。
        """
        with self._lock:
            if target_epoch < 1 or target_epoch > self._epoch:
                return False

            # 恢复快照
            snap_file = self._snapshot_dir / f"epoch_{target_epoch:04d}.json"
            if snap_file.exists():
                with open(snap_file) as f:
                    data = json.load(f)
                snapshot = IterationSnapshot.from_dict(data)

                # 恢复adapter状态
                self._epoch = target_epoch
                self._roadmap_hash = snapshot.roadmap_hash

                # 删除后续epoch的数据
                conn = sqlite3.connect(str(self._db_path))
                c = conn.cursor()
                c.execute("DELETE FROM iterations WHERE epoch > ?", (target_epoch,))
                c.execute("DELETE FROM adapters WHERE epoch > ?", (target_epoch,))
                conn.commit()
                conn.close()

                # 清理后续快照文件
                for f in self._snapshot_dir.glob("epoch_*.json"):
                    epoch_num = int(f.stem.split("_")[1])
                    if epoch_num > target_epoch:
                        f.unlink()

                # 截断历史
                self._history = [s for s in self._history if s.epoch <= target_epoch]

                return True

            return False

    def get_history(self, limit: int = 20) -> List[dict]:
        """获取历史快照"""
        with self._lock:
            return [s.to_dict() for s in self._history[-limit:]]

    # ==================== 辅助方法 ====================

    def _get_all_subtask_status(self) -> Dict[str, str]:
        """获取所有subtask状态"""
        conn = sqlite3.connect(str(self._db_path))
        c = conn.cursor()
        c.execute("SELECT task_id, status FROM subtasks")
        return {row[0]: row[1] for row in c.fetchall()}

    @staticmethod
    def _hash_dict(d: dict) -> str:
        """计算字典的简单hash"""
        content = json.dumps(d, sort_keys=True, ensure_ascii=False)
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def show_status(self) -> str:
        """显示当前迭代状态"""
        lines = [
            "=" * 60,
            f"  Iteration Manager — {self.loop_name}",
            "=" * 60,
            "",
            f"  Current Epoch: {self._epoch}",
            f"  Current Mode:  {self.get_mode()}",
            f"  Next Mode:     {self.next_mode()}",
            f"  Roadmap Hash:  {self._roadmap_hash}",
            f"  Frozen Tasks:  {len(self._frozen_task_ids)}",
            f"  Adapters:      {len(self._adapters)}",
            f"  History Depth: {len(self._history)}",
            "",
            "  ML Analogy:",
            f"    Base Weights (frozen): {len(self._frozen_task_ids)} params",
            f"    PEFT Adapters (train): {len(self._adapters)} params",
            f"    Epoch: {self._epoch}",
            "",
            "  Recent Epochs:",
        ]

        for snap in self._history[-5:]:
            changes = len(snap.adapter_changes)
            done = sum(1 for s in snap.subtask_status.values() if s == "done")
            total = len(snap.subtask_status)
            lines.append(
                f"    Epoch {snap.epoch} [{snap.mode}] "
                f"adapter_changes={changes} "
                f"subtasks={done}/{total}"
            )

        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)


# ==================== CLI ====================

def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: iteration_manager.py <command> [args...]")
        print("\nCommands:")
        print("  status <state_dir>              Show status")
        print("  snapshot <state_dir>            Take snapshot")
        print("  rollback <state_dir> <epoch>    Rollback to epoch")
        print("  history <state_dir> [limit]     Show history")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "status" and len(sys.argv) >= 3:
        mgr = IterationManager(sys.argv[2])
        print(mgr.show_status())
    elif cmd == "snapshot" and len(sys.argv) >= 3:
        mgr = IterationManager(sys.argv[2])
        snap = mgr.snapshot()
        print(f"Snapshot saved: epoch {snap.epoch}")
    elif cmd == "rollback" and len(sys.argv) >= 4:
        mgr = IterationManager(sys.argv[2])
        epoch = int(sys.argv[3])
        if mgr.rollback(epoch):
            print(f"Rolled back to epoch {epoch}")
        else:
            print(f"Rollback to epoch {epoch} failed")
    elif cmd == "history" and len(sys.argv) >= 3:
        mgr = IterationManager(sys.argv[2])
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        for entry in mgr.get_history(limit):
            print(f"Epoch {entry['epoch']} [{entry['mode']}] {entry['timestamp']}")
    else:
        print("Unknown command or missing args")


if __name__ == "__main__":
    main()
