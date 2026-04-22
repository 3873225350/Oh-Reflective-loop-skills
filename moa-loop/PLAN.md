# MOA Loop v2.0 重构计划

## 核心设计思想

本架构将 ML 训练范式搬到 Agent 协作调度上：

- **Roadmap 主脊任务 = 预训练权重（冻结）** — 稳定、不轻易改动、定义整体方向
- **实验反思微调 = PEFT/Adapter（可训练）** — 只改局部、不动主架构、快速适应
- **Sub-tasks / 实验结果 = 微调数据** — 具体任务、具体反馈、驱动 adapter 更新
- **纵向迭代 = 训练循环（epoch级别）** — 时间轴串行，一轮推进一轮
- **横向 DAG = 计算图（op 级别）** — 无依赖并行，有依赖串行

---

## 一、纵向设计：时间轴迭代进化（固定串行）

### 1.1 核心原则

- 纵向严格按照时间顺序执行，完全串行，一轮推进一轮，不可乱序、不可并行
- 每一轮 = 一个 epoch，包含 optimize + check 两个阶段

### 1.2 数据流转路径

```
Markdown（人类+机器双可读）→ JSON（结构化，省token）→ SQL（持久化，可回溯）
```

- Markdown：适合人类与机器双可读，便于内容分段编辑
- JSON：结构化后去掉冗余文本，大幅节省 token、减少上下文长度
- SQL：存储速度快、索引高效、占用内存小，支持历史版本回溯、迭代复盘、断点续跑

### 1.3 PEFT/Adapter 微调机制

```
Roadmap 主脊任务 (冻结，= 预训练权重)
├── T1: 核心任务A (freeze)
├── T2: 核心任务B (freeze)
└── T3: 核心任务C (freeze)

实验反思 → Adapter 微调 (可训练，= PEFT)
├── A1: 根据实验结果调整子任务执行策略
├── A2: 局部计划修正，不动主架构
└── A3: 任务特定适配，轻量插入
```

- 主脊不动 → 大方向不错
- Adapter 微调 → 快速适应具体场景
- 只改局部 → 省 token、省时间
- 换任务只需换 Adapter，Base 复用

### 1.4 纵向通信特点

- 不追求低延迟、不使用共享内存
- 追求高可靠、可持久、可复现、可审计
- 每一步状态落盘，为后续迭代提供稳定依据

---

## 二、横向设计：DAG 有向无环图调度（并行+混合串行）

### 2.1 核心原则

- 横向任务基于 DAG 组织，节点代表子任务，边代表依赖关系
- 核心目标：**在依赖约束下，并行最大化、串行最小化**

### 2.2 执行规则

```
无依赖、无前置因果关系的节点 → 允许真正并行执行
有依赖、有前置条件的节点   → 必须严格串行，等待前置完成
```

### 2.3 并行 vs 串行

| 维度 | 并行 | 串行 |
|------|------|------|
| 优势 | 多 Agent 同时工作，提升效率；充分利用算力，缩短耗时 | 保证逻辑因果正确，避免内容冲突、逻辑矛盾 |
| 适用 | 无先后约束的独立模块 | 有依赖关系的任务 |
| ML类比 | Data Parallelism / Model Parallelism | Pipeline Parallelism |

---

## 三、双层通信机制

### 3.1 横向通信：共享黑板（Shared Blackboard）

- 中心化共享内存模式
- 所有 Agent 统一读写公共状态，不点对点通信
- N 个 Agent 只需 O(1) 通道（vs FIFO 的 O(N²)）

```
┌─────────────────────────────────────┐
│           Shared Blackboard         │
│  ┌─────┬─────┬─────┬─────┬─────┐   │
│  │ K1  │ K2  │ K3  │ ... │ Kn  │   │
│  └─────┴─────┴─────┴─────┴─────┘   │
└─────────────────────────────────────┘
     ↑ write    ↑ read    ↑ read
   Agent A    Agent B   Agent C
```

优点：低延迟、高并发、无消息风暴、易于实时可视化、支持大规模 Agent 协同

### 3.2 纵向通信：JSON + SQL 结构化持久化

- 省内存、省 token、稳定可回溯
- 适合长期迭代进化

---

## 四、文件结构

```
moa-loop/scripts/
├── core/
│   ├── __init__.py
│   ├── dag_scheduler.py       ← 横向DAG调度核心
│   ├── shared_blackboard.py   ← 共享黑板（横向通信）
│   └── iteration_manager.py   ← 纵向迭代管理 + PEFT思想
├── dispatch_agent.sh          ← 重写：调用新架构
├── run_daemon.sh              ← 重写：DAG驱动主循环入口
├── run_daemon.py              ← 重写：DAG驱动主循环
├── config.json                ← 扩展：DAG定义 + PEFT配置
├── detect_agents.sh           ← 保留不变
├── init_moa_loop.cjs          ← 扩展：初始化新目录结构
├── moa_bus.py                 ← 保留兼容（旧SQLite层）
├── moa_bus.sh                 ← 保留兼容
├── agent_bus.sh               ← 保留兼容
├── collab_writer.sh           ← 保留兼容
└── shared_context.sh          ← 保留兼容
```

---

## 五、各模块详细设计

### 5.1 dag_scheduler.py — 横向 DAG 调度核心

职责：
- 解析 DAG 定义（JSON 格式）
- 拓扑排序，检测环
- 按依赖关系分层：同一层内并行，层间串行
- 调度 Agent 执行节点任务
- 收集执行结果，推进 DAG 状态

核心数据结构：
```python
@dataclass
class DAGNode:
    id: str                    # 节点ID
    task_type: str             # coding/writing/analysis/...
    agent: str                 # 指定agent（可选）
    dependencies: List[str]    # 依赖的节点ID列表
    status: str                # pending/running/done/failed
    result: Optional[str]      # 执行结果

@dataclass
class DAG:
    nodes: Dict[str, DAGNode]
    entry_nodes: List[str]     # 无依赖的入口节点

class DAGScheduler:
    def topological_sort(self) -> List[List[str]]  # 返回分层结果
    def get_ready_nodes(self) -> List[str]          # 当前可执行的节点
    def mark_done(self, node_id, result)            # 标记完成，解锁下游
    def is_complete(self) -> bool                   # 所有节点完成
```

### 5.2 shared_blackboard.py — 共享黑板

职责：
- 中心化读写公共状态
- 支持 Agent 注册、心跳
- 支持 key-value 知识存储
- 支持任务结果发布
- 线程安全（锁机制）

核心数据结构：
```python
class SharedBlackboard:
    _knowledge: Dict[str, Any]       # 共享知识库
    _agent_status: Dict[str, dict]   # Agent 状态注册表
    _task_results: Dict[str, Any]    # 任务结果
    _lock: threading.RLock           # 线程安全锁

    def write(self, agent, key, value)       # Agent 写入
    def read(self, key) -> Any               # 任意 Agent 读取
    def subscribe(self, agent, pattern)      # 订阅 key 模式
    def publish_result(self, task_id, result) # 发布任务结果
    def get_snapshot(self) -> dict           # 获取完整快照
```

### 5.3 iteration_manager.py — 纵向迭代管理 + PEFT

职责：
- 管理纵向 epoch 迭代循环
- Markdown → JSON → SQL 数据流转
- Roadmap 主脊冻结管理（= 预训练权重）
- Sub-task Adapter 微调（= PEFT）
- 版本快照、断点续跑、历史回溯

核心数据结构：
```python
class IterationManager:
    _epoch: int                        # 当前迭代轮次
    _roadmap_base: Dict                # Roadmap 主脊（冻结）
    _adapters: Dict[str, dict]         # PEFT Adapter 层
    _history: List[IterationSnapshot]  # 历史快照

    def new_epoch(self) -> int                          # 开启新轮次
    def freeze_roadmap(self, roadmap_md)                # 冻结主脊
    def adapt_subtask(self, task_id, experiment_result) # PEFT微调
    def snapshot(self) -> IterationSnapshot             # 保存快照
    def rollback(self, epoch)                           # 回溯到指定轮次
    def markdown_to_json(self, md_text) -> dict         # 结构化转换
    def persist_to_sql(self, data)                      # SQL持久化
```

---

## 六、config.json 扩展结构

```json
{
  "primary_agent": "gemini",
  "enabled_agents": ["gemini", "claude", "qwen", "kimi"],
  "max_parallel": 3,

  "dag": {
    "nodes": [
      {"id": "research", "type": "research", "deps": []},
      {"id": "code", "type": "coding", "deps": ["research"]},
      {"id": "test", "type": "coding", "deps": ["code"]},
      {"id": "doc", "type": "writing", "deps": ["code"]},
      {"id": "review", "type": "analysis", "deps": ["test", "doc"]}
    ]
  },

  "peft": {
    "freeze_roadmap": true,
    "adapter_scope": "sub-tasks",
    "max_adapter_changes_per_epoch": 5
  },

  "iteration": {
    "max_epochs": 100,
    "snapshot_interval": 1,
    "rollback_on_failure": true
  }
}
```

---

## 七、实施顺序

1. ✅ Git init + v1.0 备份
2. 🔄 创建 `core/dag_scheduler.py`
3. 🔄 创建 `core/shared_blackboard.py`
4. 🔄 创建 `core/iteration_manager.py`
5. ⬜ 重写 `dispatch_agent.sh` 调用新架构
6. ⬜ 重写 `run_daemon.py` DAG 驱动主循环
7. ⬜ 扩展 `config.json` 添加 DAG + PEFT 配置
8. ⬜ 扩展 `init_moa_loop.cjs` 初始化新目录
9. ⬜ 更新 `SKILL.md` / `README.md`
10. ⬜ Git commit v2.0

---

## 八、整体优化目标

- 依赖关系清晰，DAG 调度合理
- 可并行任务绝不串行，提高效率
- 必须串行任务严格有序，保证正确性
- 通信分层清晰：横向高效实时（共享黑板），纵向稳定轻量化（JSON+SQL）
- Roadmap 主脊冻结稳定，Adapter 微调灵活适应
- 整体结构可扩展、可进化、可可视化、易落地
