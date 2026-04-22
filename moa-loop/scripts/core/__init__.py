"""
MOA Loop v2.0 Core Modules

Architecture: 纵向时序迭代 + 横向DAG协同 双层解耦

纵向 = 训练循环 (epoch级别): Markdown → JSON → SQL, Roadmap冻结 + PEFT微调
横向 = 计算图 (op级别): DAG调度, 无依赖并行, 有依赖串行
通信 = 横向共享黑板 + 纵向结构化持久化
"""

from .dag_scheduler import DAGScheduler, DAGNode, DAG
from .shared_blackboard import SharedBlackboard
from .iteration_manager import IterationManager, IterationSnapshot

__all__ = [
    "DAGScheduler", "DAGNode", "DAG",
    "SharedBlackboard",
    "IterationManager", "IterationSnapshot",
]
