# AI Agent Framework — 养老医疗机器人多智能体决策系统

[![CI](https://github.com/your-username/agent_framework/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/agent_framework/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

> 基于 Plan-Execute-Review 架构，从零实现的多 Agent 协作框架。以养老医疗机器人作为落地场景，覆盖健康监护、用药管理、跌倒应急、康复指导四大业务。

---

## 项目简介

这是一个**不依赖 LangChain 等任何 Agent 框架**、完全手写的多智能体系统。核心架构约 1400 行 Python，包含：

- **ReAct 循环引擎**：Think → Act → Observe 全透明实现
- **三级记忆架构**：短期上下文 / 工作记忆 / 长期持久化
- **Plan-Execute-Review 三 Agent 协作**：任务分解 → 带工具执行的子任务 → 安全审查
- **装饰器式工具注册**：自动从函数签名生成 OpenAI function calling JSON Schema

```text
User Input → Planner (拆解) → Executor (执行 + 工具调用) → Reviewer (安全审查) → 输出
                                                              ↓
                                                         REVISE (最多 3 轮退回)
```

---

## 架构

```text
┌───────────────────────────────────┐
│  apps/elderly_care.py   应用层    │  4 个医疗场景 Demo
├───────────────────────────────────┤
│  orchestrator.py        编排层    │  Plan → Execute → Review 主流程
├───────────────────────────────────┤
│  agents/ {planner,               │  3 种 Agent 角色
│   executor, reviewer}.py Agent层  │  继承 Agent 基类，独立系统提示词
├───────────────────────────────────┤
│  core/ {llm, tools,               │  LLM 抽象 / 工具注册
│   memory, agent}.py    基础设施层   │  三级记忆 / ReAct 引擎
└───────────────────────────────────┘
```

依赖方向：上层依赖下层，下层不感知上层。核心框架不绑定任何业务场景——换个场景只需改提示词 + 注册新工具。

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置 API Key

```bash
# 方式 A：环境变量（推荐）
export DEEPSEEK_API_KEY="sk-your-key-here"

# 方式 B：编辑 config.yaml 的 api_key 字段
```

### 3. 运行

```bash
# 养老医疗 Demo（4 个场景）
python main.py demo

# 注册的工具列表
python main.py tools

# 单 Agent 交互模式
python main.py chat
```

---

## 四个医疗场景

| 场景 | 工具 | 描述 |
|------|------|------|
| **健康监护** | `get_vital_signs` / `get_heart_rate_history` | 监测生命体征、对比历史趋势、评估健康风险 |
| **用药管理** | `get_medication_schedule` / `log_medication_dose` / `check_medication_compliance` | 管理服药计划、检测漏服、安全补服决策 |
| **跌倒应急** | `detect_fall` / `get_patient_location` / `call_ambulance` / `notify_emergency_contacts` | 加速度计检测跌倒 → 定位 → 调度急救 |
| **康复指导** | `get_rehab_plan` / `check_exercise_safety` / `log_training_session` | 生成康复计划、检查运动安全、记录训练进度 |

---

## 项目结构

```text
agent_framework/
├── core/                   基础设施（零业务绑定）
│   ├── llm.py              LLM 抽象层（支持 DeepSeek/GPT/Qwen）
│   ├── tools.py            装饰器式工具注册系统
│   ├── memory.py           三级记忆管理
│   ├── agent.py            ReAct 循环引擎
│   └── logger.py           结构化日志
├── agents/                 三个 Agent 角色
│   ├── planner.py          任务分解
│   ├── executor.py         带工具调用的任务执行
│   └── reviewer.py         质量 + 安全检查
├── tools/                  IoT 模拟工具
│   ├── health_monitor.py   生命体征监测
│   ├── medication.py       用药管理
│   ├── fall_detection.py   跌倒检测
│   ├── recovery.py         康复训练
│   └── basic.py            通用工具
├── apps/
│   └── elderly_care.py     养老医疗 Demo 入口
├── orchestrator.py         多 Agent 编排引擎
├── main.py                 CLI 入口
├── config.yaml             配置文件
├── tests/                  单元测试
├── .github/workflows/      CI/CD 配置
├── TECH_ROADMAP.md         技术路线手册（面试参考）
└── README.md               本文件
```

---

## 与 LangChain 的对比

|  | 本框架 | LangChain |
|------|--------|-----------|
| ReAct 循环 | 透明，45 行 | 黑盒封装 |
| 工具调用 | 装饰器自动生成 schema | 手动定义 BaseTool |
| 死循环检测 | ✅ 内置 | ❌ 需自定义 |
| 安全审查 | Reviewer Agent | ❌ 无内置 |
| 记忆管理 | 三级架构（短/工/长） | ConversationBufferMemory |
| 代码量 | 核心 ~800 行 | 依赖 ~100MB |
| 医疗定制 | 领域提示词 + 安全权重 | 通用 Agent |

---

## 面试 Q&A（精选）

<details>
<summary>为什么不调 LangChain 选择手写？</summary>

我想深入理解 Agent 的底层原理。LangChain 封装了 ReAct 循环和工具调用，用起来方便但不清楚内部逻辑。从零实现让我真正懂了 function calling 协议、上下文窗口管理、以及防死循环这些工程细节。核心 800 行代码，每一行我都知道为什么这样写。
</details>

<details>
<summary>如何保证医疗场景的安全性？</summary>

两层防护。第一层在 Agent 循环：死循环检测、步数限制。第二层在 Reviewer Agent：系统提示词包含医疗专项安全规则——用药剂量检查、急救决策二次确认、异常体征标注紧急等级。Emergency 场景的审查 weight 最高。这不是替代人工决策，是辅助。
</details>

<details>
<summary>工具注册系统怎么做到自动生成 schema？</summary>

装饰器 `@tools.register` 在注册时用 `inspect.signature()` 和 `typing.get_type_hints()` 解析函数签名——参数名、类型、默认值、docstring——自动生成符合 OpenAI function calling 协议的 JSON Schema。不需要手动写任何 JSON 描述。
</details>

---

## 运行环境

- Python 3.10+
- httpx >= 0.27
- pyyaml >= 6.0
- DeepSeek API Key（或其他 OpenAI 兼容模型）

---

## 未来路线

- [x] 核心三 Agent 架构 + ReAct 循环
- [x] 四个医疗场景工具
- [x] `.gitignore` + 工程化基础
- [ ] 异步并行 Executor（子任务无依赖时并行）
- [ ] 人机协同对接（关键决策暂停并要求人工确认）
- [ ] FastAPI Web 接口
- [ ] Docker 一键部署
