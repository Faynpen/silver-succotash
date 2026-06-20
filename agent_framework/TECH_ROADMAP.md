# 养老医疗机器人多 Agent 决策系统 — 技术路线手册

> Multi-Agent Decision System for Elderly Care Robotics  
> Plan-Execute-Review Architecture · From Zero to Interview-Ready

---

## 目录

1. [项目定位](#1-项目定位)
2. [系统架构](#2-系统架构)
3. [技术栈](#3-技术栈)
4. [核心模块详解](#4-核心模块详解)
5. [数据流与调用链](#5-数据流与调用链)
6. [四个业务场景](#6-四个业务场景)
7. [安全设计](#7-安全设计)
8. [扩展指南](#8-扩展指南)
9. [面试 Q&A 预案](#9-面试-qa-预案)
10. [文件索引](#10-文件索引)

---

## 1. 项目定位

### 一句话描述

> 基于 Plan-Execute-Review 架构，从零实现多 Agent 协作框架，并以养老医疗机器人作为差异化落地场景——健康监护、用药管理、跌倒应急、康复指导四个场景全覆盖。

### 为什么要做这个方向

| 维度 | 价值 |
|------|------|
| 技术深度 | 不调包，从 ReAct 循环到多 Agent 编排全部手写 |
| 场景差异化 | 养老医疗赛道避开烂大街的聊天机器人/RAG 问答 |
| 政策风口 | 2025-2026 银发经济政策密集出台 |
| 安全设计 | Reviewer 的安全审查机制在医疗场景是关键亮点 |
| 面试记忆点 | 99% 的候选人做通用 Agent，你做的是医疗 Agent |

### 与调 LangChain 的本质区别

```
调 LangChain 30 行代码 = 你会用框架
手写 ReAct 循环 100 行 = 你理解 Agent 原理
```

---

## 2. 系统架构

### 分层架构

```
┌─────────────────────────────────────────────┐
│  apps/elderly_care.py    应用层              │  健康监护 / 用药管理
│                           4 个医疗场景        │  跌倒应急 / 康复指导
├─────────────────────────────────────────────┤
│  orchestrator.py         编排层              │  Plan→Execute→Review 主流程
│                           任务分配+审查循环    │  最多 3 轮退回修改
├─────────────────────────────────────────────┤
│  agents/{planner,         Agent 角色层        │  3 种角色, 继承 Agent 基类
│   executor,reviewer}.py                      │  各配独立系统提示词
├─────────────────────────────────────────────┤
│  core/{llm,tools,         基础设施层           │  LLM 抽象 / 工具系统
│   memory,agent}.py                           │  三级记忆 / ReAct 引擎
└─────────────────────────────────────────────┘
```

**依赖方向**：上层依赖下层，下层不感知上层。核心框架不绑定任何业务场景。

### Plan-Execute-Review 工作流

```
User Input
    │
    ▼
┌──────────┐
│ PLANNER  │  "拆成 3 个子任务"
└────┬─────┘
     │ subtask list
     ▼
┌──────────┐    ┌──────────┐    ┌──────────┐
│ EXECUTOR │───▶│ EXECUTOR │───▶│ EXECUTOR │  串行执行
│ task 1   │    │ task 2   │    │ task 3   │  可调用工具
└──────────┘    └──────────┘    └──────────┘
     │               │               │
     └───────────────┼───────────────┘
                     │ results
                     ▼
               ┌──────────┐
               │ REVIEWER │  "安全吗？完整吗？"
               └────┬─────┘
                    │
          ┌─────────┴─────────┐
          │                   │
       PASS                REVISE
          │                   │
          ▼                   ▼
    返回用户          回 Executor 重做
                    (最多 3 轮)
```

---

## 3. 技术栈

| 层 | 技术 | 理由 |
|----|------|------|
| 语言 | Python 3.10+ | AI 生态第一语言 |
| LLM | DeepSeek API (`deepseek-chat`) | 国产模型, OpenAI 兼容接口, 性价比高 |
| HTTP 客户端 | `httpx` | 异步支持, 比 requests 更现代 |
| 配置管理 | `pyyaml` | 标准 YAML 解析 |
| 数据类 | `dataclasses` (stdlib) | 零依赖, 类型安全 |
| 运行环境 | 无框架依赖 | 全部手写, 核心代码约 800 行 |

### 为什么不依赖 LangChain/LlamaIndex

1. **面试含金量**："我用 LangChain 调的" vs "我从零实现的"——差距 10 倍
2. **可控性**：死循环检测、安全边界、医疗场景的特殊审查逻辑，框架做不到
3. **学习深度**：写一遍 ReAct 循环比读 10 篇博客理解更深
4. **代码量不大**：核心约 800 行, 完全可控

---

## 4. 核心模块详解

### 4.1 `core/llm.py` — LLM 抽象层

**职责**：统一对接 LLM, 屏蔽模型差异。

```python
class LLMClient:
    def chat(messages, tools, temperature, max_tokens) -> LLMResponse
```

**设计要点**：
- OpenAI 兼容协议 → DeepSeek/GPT/Qwen/Claude 切换零改动
- 自动重试：5xx 错误重试 3 次
- 模型 fallback：主模型挂了自动切备用模型
- Token 累计追踪：`client.total_tokens` 实时统计
- 工具调用结果格式化：`tool_call_to_message()` 生成标准 tool 消息

**扩展点**：新增模型只需加一个类，实现 `chat()` 方法。

---

### 4.2 `core/tools.py` — 工具注册系统

**职责**：把 Python 函数自动转成 OpenAI function calling 格式。

```python
tools = ToolRegistry()

@tools.register
def get_vital_signs(patient_id: str) -> str:
    """Read current vital signs from wearable sensors."""
    ...
```

**自动生成的 JSON Schema**：
```json
{
  "type": "function",
  "function": {
    "name": "get_vital_signs",
    "description": "Read current vital signs from wearable sensors.",
    "parameters": {
      "type": "object",
      "properties": {
        "patient_id": {"type": "string"}
      },
      "required": ["patient_id"]
    }
  }
}
```

**设计要点**：
- `inspect.signature()` + `typing.get_type_hints()` → 自动 schema
- 安全执行：异常捕获 + 执行时间统计
- 工具不存在 → 友好报错并列出可用工具

**面试亮点**："我不需要手动写 JSON Schema，装饰器自动从函数签名和 docstring 生成。"

---

### 4.3 `core/memory.py` — 三级记忆系统

```
┌──────────────────────────────────┐
│  Short-Term (上下文窗口)           │  ← 当前对话, 自动裁剪
│  max_turns=20, FIFO 淘汰          │
├──────────────────────────────────┤
│  Working Memory (任务状态)         │  ← 单任务内跨工具调用
│  key-value, clear_working() 重置   │
├──────────────────────────────────┤
│  Long-Term Memory (持久化)         │  ← 病人档案/用药历史
│  JSON 文件, 跨会话存活            │
└──────────────────────────────────┘
```

**设计要点**：
- 短期记忆自动裁剪：防 token 溢出
- 工作记忆隔离：每个任务独立, 不相污染
- 长期记忆文件存储：`long_term_memory.json`

**面试亮点**："我设计的三级记忆架构解决了 LLM 上下文窗口限制、跨工具调用的状态保持、以及跨会话的知识积累。"

---

### 4.4 `core/agent.py` — ReAct 循环引擎

**这是整个框架的心脏。**

```
┌──────────────────────────────────────┐
│           Agent.run(task)             │
│                                      │
│  for step in range(max_steps):       │
│    ┌──────────────────────────┐      │
│    │ THINK: llm.chat(messages)│      │
│    └──────────┬───────────────┘      │
│               │                      │
│        tool_calls?                   │
│         /        \                   │
│       YES        NO                  │
│       /            \                 │
│   ┌──────┐    ┌──────────┐          │
│   │ ACT  │    │ FINAL    │          │
│   │ execute│  │ ANSWER  │           │
│   │ tools │   │ return   │           │
│   └──┬───┘    └──────────┘          │
│      │                               │
│   ┌──────┐                           │
│   │OBSERVE│  喂回结果                 │
│   │ result│  进入下一轮               │
│   └──────┘                           │
│                                      │
│  Safety:                             │
│  - 死循环检测: 同一工具连调 3 次       │
│  - 最大步数: 10 步强制终止            │
└──────────────────────────────────────┘
```

**死循环检测**：
```python
self.last_tool_calls.append(tool_name)
if len(set(self.last_tool_calls[-3:])) == 1:
    # Same tool called 3 times → inject "stop and answer" message
    self.memory.add_message("user", "[System: Stop and provide your best answer]")
```

**面试亮点**："我的 Agent 有防死循环机制——监测连续相同的工具调用并注入终止信号，这在 LangChain 里很容易被忽略。"

---

### 4.5 `agents/` — 三种 Agent 角色

| Agent | 职责 | 工具有无 | temperature | 特殊设计 |
|-------|------|---------|-------------|---------|
| Planner | 任务拆解 | 无 | 0.3（低） | 只推理，不执行 |
| Executor | 执行子任务 | 有 | 0.5（中） | 唯一能动工具的 Agent |
| Reviewer | 安全审查 | 无 | 0.2（极低） | 医疗场景加重安全权重 |

**Agent 的独立性**：每个 Agent 有独立的 `Memory` 实例——互不干扰。协作通过 Orchestrator 的 `shared_memory` 桥接。

---

### 4.6 `orchestrator.py` — 多 Agent 编排引擎

```
orchestrator.run(user_input)
  │
  ├─ Phase 1: PLAN
  │   planner.run(user_input) → 解析出子任务列表
  │
  ├─ Phase 2: EXECUTE
  │   for each subtask: executor.run(subtask)
  │
  ├─ Phase 3: REVIEW + REVISE (最多 3 轮)
  │   while not passed and rounds < 3:
  │       reviewer.run(review_prompt)
  │       if REVISE: executor.run(feedback + original task)
  │
  └─ Phase 4: FORMAT
      汇总 → 返回结构化结果
```

---

## 5. 数据流与调用链

### 一次完整的医疗场景执行

```
用户: "Patient P001 reports dizziness. Check vitals, assess risk."

                ┌─ Planner ──────────────────────────────┐
                │  TASK PLAN:                             │
                │  1. Read vitals from wearable           │
                │  2. Compare with 6h history             │
                │  3. Assess emergency risk               │
                │  4. Generate nurse summary              │
                └────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌─ Executor ─┐ ┌─ Executor ─┐ ┌─ Executor ─┐
        │ THINK: need │ │ THINK: need│ │ THINK:      │
        │ get_vitals  │ │ history +  │ │ 直接推理    │
        │             │ │ vitals     │ │             │
        │ ACT: call   │ │            │ │ FINAL:      │
        │ get_vital_  │ │ ACT: call  │ │ 风险评级    │
        │ signs(P001) │ │ get_heart_ │ │             │
        │             │ │ rate_hist  │ │             │
        │ OBSERVE:    │ │ (P001, 6)  │ │             │
        │ HR=98,      │ │            │ │             │
        │ BP=145/92   │ │ OBSERVE:   │ │             │
        │             │ │ 6h trend   │ │             │
        │ FINAL:      │ │            │ │             │
        │ 生命体征     │ │ FINAL:     │ │             │
        │ 报告         │ │ 对比分析   │ │             │
        └─────────────┘ └─────────────┘ └─────────────┘
                                │
                ┌─ Reviewer ────────────────────────────┐
                │  DECISION: PASS                        │
                │  所有生命体征已检查 ✓                    │
                │  历史对比已完成 ✓                       │
                │  风险评估有依据 ✓                       │
                │  无安全风险 ✓                           │
                └────────────────────────────────────────┘
                                │
                    返回用户：完整的健康评估报告
```

---

## 6. 四个业务场景

### 场景 1：健康监护 (Health Monitoring)

| 步骤 | 谁做 | 做什么 |
|------|------|--------|
| 触发 | 可穿戴设备 | 检测到异常心率 / 用户自述不适 |
| Plan | Planner | 拆为：读数据 → 比基线 → 评风险 → 写报告 |
| Execute | Executor | 调 `get_vital_signs`、`get_heart_rate_history` |
| Review | Reviewer | 检查数据完整性、异常标记是否正确、报告是否有遗漏 |
| 输出 | 汇总 | 护士站报告："P001 心率 98, 血压偏高 145/92, 建议..." |

### 场景 2：用药管理 (Medication Management)

| 步骤 | 谁做 | 做什么 |
|------|------|--------|
| 触发 | 到点未服药 | 传感器检测到药盒未开启 |
| Plan | Planner | 查用药计划 → 检查漏服 → 决定补服方案 |
| Execute | Executor | 调 `get_medication_schedule`、`log_medication_dose`、`check_medication_compliance` |
| Review | Reviewer | **重点审查：补服剂量是否安全、是否有药物相互作用** |
| 输出 | 处理 | 安全补服 → 记录；不安全 → 跳过并通知医生 |

### 场景 3：跌倒应急 (Fall Detection)

| 步骤 | 谁做 | 做什么 |
|------|------|--------|
| 触发 | 加速度计 | 检测到 8g+ 冲击 |
| Plan | Planner | 确认跌倒 → 评估伤情 → 决定方案 |
| Execute | Executor | 调 `detect_fall`、`get_patient_location`、`call_ambulance`、`notify_emergency_contacts` |
| Review | Reviewer | **最高安全级别审查：急救决策是否正确、是否通知了所有人、定位是否准确** |
| 输出 | 应急 | 120 已调度、家属已通知、病历已同步给急救中心 |

### 场景 4：康复指导 (Rehabilitation)

| 步骤 | 谁做 | 做什么 |
|------|------|--------|
| 触发 | 康复计划 | 到康复训练时间 |
| Plan | Planner | 查生命体征 → 确定安全 → 分步指导 |
| Execute | Executor | 调 `get_vital_signs`、生成逐动作语音指导 |
| Review | Reviewer | 确认生命体征适合运动、动作规范、进度合理 |
| 输出 | 报告 | 康复训练报告 → 推送物理治疗师 |

---

## 7. 安全设计

### 为什么医疗场景需要特别的安全设计

> "AI 在聊天场景说错话是尴尬，在医疗场景说错话是要命的。"

### 安全机制全景

| 层级 | 机制 | 作用 |
|------|------|------|
| Agent 层 | 死循环检测 | 同一工具连续 3 次 → 强制终止并输出 |
| Agent 层 | 最大步数限制 | 10 步强制停止，防止失控 |
| Tool 层 | 异常捕获 | 工具执行失败 → 返回结构化错误，不崩溃 |
| Tool 层 | 执行时间统计 | 监控工具性能，慢调用可追踪 |
| Reviewer 层 | **安全审查** | 医疗场景加重了安全审查权重（系统提示词明确要求） |
| Reviewer 层 | 用药安全检查 | 补服决策 → Reviewer 二次确认剂量和相互作用 |
| Reviewer 层 | 急救决策审查 | 是否呼叫 120 → Reviewer 独立判断，不盲从 Executor |
| Orchestrator 层 | 退回重做 | Reviewer 不通过 → 回 Executor 重做（最多 3 轮） |
| Orchestrator 层 | 结构化输出 | 所有结果统一格式，便于审计和追溯 |

### Reviewer 的医疗专项提示词

```
For HEALTHCARE scenarios, apply EXTRA scrutiny:
- Medication: Double-check dosage, timing, interactions
- Emergency: Verify severity assessment is appropriate
- Vitals: Flag any abnormal readings with urgency level
```

**面试亮点**："我在 Reviewer 层内建了医疗安全审查机制——用药剂量、急救决策、异常体征都会触发二次确认。这是 LangChain 等通用框架做不到的领域定制。"

---

## 8. 扩展指南

### 8.1 换一个模型

```python
# 只需修改 config.yaml
llm:
  provider: openai  # 或其他
  api_key: "sk-..."
  base_url: "https://api.openai.com/v1"
  model: "gpt-4o"
```

`LLMClient` 使用 OpenAI 兼容协议，任何兼容的 API 都零改动接入。

### 8.2 加一个新工具

```python
@tools.register
def measure_blood_oxygen(patient_id: str) -> str:
    """Measure blood oxygen level (SpO2) for a patient."""
    spo2 = random.randint(90, 100)
    return f"Patient[{patient_id}] SpO2: {spo2}%"
```

装饰器自动注册 + 自动生成 schema。重新运行 `python main.py tools` 即可看到。

### 8.3 换一个业务场景

只需改三个地方：

1. **系统提示词**：修改 Planner/Executor/Reviewer 的角色描述
2. **工具注册**：注册新场景需要的工具
3. **场景配置**：修改 `apps/` 下的场景提示词

**框架代码零改动。**

### 8.4 加第四种 Agent 角色

```python
class AlertAgent(Agent):
    def __init__(self, llm, memory):
        super().__init__(
            llm=llm,
            tools=None,
            memory=memory,
            system_prompt="你是告警分级专家...",
        )
```

然后在 `Orchestrator` 中插入新的编排步骤即可。

---

## 9. 面试 Q&A 预案

### Q1: "为什么不用 LangChain？"

> "我想深入理解 Agent 的底层原理。LangChain 封装了 ReAct 循环、工具调用、记忆管理，用起来方便但不清楚内部逻辑。我选择从零实现——这让我真正懂了 LLM function calling 协议、上下文窗口管理、以及防死循环这些工程细节。800 行核心代码，每一行我都知道为什么这样写。"

### Q2: "你的框架和 LangChain 的核心区别在哪？"

> "三点：第一，LangChain 的 Agent 循环是黑盒，我的 ReAct 循环完全透明，死循环检测、步数限制都是显式的。第二，LangChain 的记忆管理是通用的，我的三级记忆架构针对医疗场景做了长短期分离——病人档案跨会话持久化，会话上下文自动裁剪。第三，LangChain 没有 Reviewer 角色，我的三 Agent 架构带安全审查，这对医疗场景至关重要。"

### Q3: "为什么选养老医疗这个场景？"

> "三个原因。一是差异化——99% 的候选人做通用聊天或 RAG 问答，我做医疗 Agent。二是政策风口——2025-2026 银发经济政策密集出台，养老科技是确定性趋势。三是技术挑战——医疗场景对安全性和可靠性要求极高，这倒逼我设计 Reviewer 审查机制，反而成了技术亮点。"

### Q4: "如果 Reviewer 也判断错了怎么办？"

> "首先，Reviewer 不是最终决策者——它只做质量审查，最终决策权在人（护士/医生/家属）。其次，Reviewer 的退回重做机制给 Executor 3 次修正机会。最后，在医疗场景，Reviewer 的系统提示词包含了专项安全规则（药物剂量检查、急救决策审查等），比通用 Review 更严格。当然，这不能替代人工审核——我设计的定位是辅助决策，不是替代。"

### Q5: "工具调用的安全问题怎么处理？"

> "两层防护。第一层在 ToolRegistry：每个工具调用都包在 try-except 里，失败不崩溃，返回结构化错误。第二层在 Agent 循环：死循环检测、步数限制、以及注入终止信号——确保 Agent 不会陷入无限工具调用。在医疗场景，Reviewer 还会额外审查工具调用的结果是否合理。"

### Q6: "如果让你重新设计，你会改什么？"

> "三点改进方向。一是加异步并行——当前 Executor 串行执行子任务，但子任务间无依赖时可以并行，减少延迟。二是加人机协同——在关键决策点（比如是否呼叫 120）暂停并请求人工确认。三是加向量检索——用 embedding 做语义相似任务匹配，避免每次从零规划。"

### Q7: "这个系统怎么部署到真实机器人上？"

> "四步部署路径。第一步：把 mock 工具替换为真实硬件驱动（ROS 节点、传感器 SDK）。第二步：Agent 循环加实时性约束——跌倒应急场景要求秒级响应，需要异步架构。第三步：加边缘推理——核心决策在边缘设备上跑，减少云端延迟。第四步：接入医院 HIS 系统——用药记录、病历同步需要标准化接口（HL7/FHIR）。"

---

## 10. 文件索引

```
agent_framework/
│
├── core/                      基础设施（不依赖任何上层模块）
│   ├── llm.py                 LLM 抽象层 (126 行)
│   ├── tools.py               工具注册系统 (141 行)
│   ├── memory.py              三级记忆管理 (136 行)
│   └── agent.py               ReAct 循环引擎 (140 行)
│       └── 核心总计: 543 行
│
├── agents/                    Agent 角色定义（继承 core/agent.py）
│   ├── planner.py             任务规划者 (45 行)
│   ├── executor.py            任务执行者 (40 行)
│   └── reviewer.py            安全审查者 (48 行)
│       └── 角色总计: 133 行
│
├── tools/                     IoT 模拟工具（装饰器注册）
│   ├── health_monitor.py      生命体征监测 (93 行)
│   ├── medication.py          用药管理系统 (97 行)
│   ├── fall_detection.py      跌倒检测 + 应急响应 (74 行)
│   ├── basic.py               通用工具 (50 行)
│       └── 工具总计: 314 行
│
├── orchestrator.py            多 Agent 编排引擎 (191 行)
│
├── apps/
│   └── elderly_care.py        养老医疗 Demo (158 行)
│
├── main.py                    CLI 入口 (128 行)
├── config.yaml                配置文件 (28 行)
├── requirements.txt           依赖 (2 个包)
│
├── TECH_ROADMAP.md            本手册
│
└── .agent_memory/             长期记忆存储 (自动生成)
    └── long_term_memory.json
```

**总代码量**：约 1,400 行 Python（含注释和文档字符串）

---

## 附录 A：运行方式

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置 API Key（二选一）
#    方式 A: 编辑 config.yaml
#    方式 B: export DEEPSEEK_API_KEY="sk-..."

# 3. 运行养老医疗 Demo
python main.py demo

# 4. 单 Agent 交互模式
python main.py chat

# 5. 查看所有注册的工具
python main.py tools
```

---

## 附录 B：关键术语

| 术语 | 解释 |
|------|------|
| ReAct | Reasoning + Acting，Agent 的"思考-行动-观察"循环 |
| Function Calling | LLM 输出结构化 JSON, 触发外部函数执行 |
| Orchestrator | 编排器，协调多个 Agent 完成复杂任务 |
| Context Window | LLM 一次能处理的最大文本量 |
| Hallucination | LLM 生成不实信息，Reviewer 的作用之一就是检测幻觉 |
| Tool Schema | 工具的 JSON Schema 描述，LLM 据此决定调用哪个工具 |

---

*手册版本: v1.0 · 最后更新: 2026-06-19*
