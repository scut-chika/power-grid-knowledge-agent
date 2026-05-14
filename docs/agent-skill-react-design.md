# Agent Skill + ReAct 设计说明

## 1. 目标

在尽量不改动现有 RAG 主流程的前提下，将系统从“单次问答”升级为“可多步执行的技能型 Agent”。

本阶段实现重点：

1. 将现有 `tool` 适配为标准 `skill`
2. 增加 `ReActExecutor`，支持多步技能调用与状态传递
3. 通过配置开关切换 `legacy/react`，默认仍为 `legacy`

## 2. 设计原则

- 最小侵入：旧模块保留，新增模块承载新能力
- 向后兼容：默认执行模式不变
- 可观测：返回执行模式与 trace，便于调试
- 可扩展：后续可平滑迁移 LangGraph

## 3. 新增模块

- `src/agent/skills/base.py`
  - 定义 `SkillMeta` 与 `Skill` 协议
- `src/agent/skills/registry.py`
  - 统一注册、查找、运行 skill
- `src/agent/skills/adapters/legacy_tools_adapter.py`
  - 将现有 `knowledge/graph/device/scenario` tool 封装为 skill
- `src/agent/skills/executor_react.py`
  - ReAct 风格执行器，包含：
    - 下一步技能选择
    - 运行时上下文更新
    - 终止条件控制
    - trace 记录

## 4. 主流程改造点

### `agent_core`

新增 `execute_agent_pipeline(query)` 作为统一执行入口：

1. `preprocess_query`
2. `recognize_intent`
3. 根据 `AGENT_EXECUTION_MODE` 选择执行方式：
   - `legacy`：原 planner + call_tool
   - `react`：registry + ReActExecutor
4. 统一生成 `reasoning` 与 `final_data`

`run_agent` 保持原有对外行为，同时新增返回：

- `execution_mode`
- `trace`

### `chat_api` 流式接口

流式接口改为复用 `execute_agent_pipeline`，避免出现“普通问答走新逻辑、流式仍走旧逻辑”的分叉。

## 5. 执行模式与开关

环境变量：

- `AGENT_EXECUTION_MODE=legacy|react`

默认：

- 未配置时使用 `legacy`

建议上线策略：

1. 测试环境启用 `react`
2. 生产先灰度少量会话
3. 观察 trace 后再全量切换

## 6. ReAct 执行策略（当前版本）

当前为轻量规则驱动策略：

- 优先遵循 `initial_plan`（由现有 `make_plan(intent)` 生成）
- 若计划不足，再按意图组补选技能
- 强制 `max_steps` 限制
- 遇到错误/关键技能完成时提前停止

这样可以在不引入复杂依赖的情况下先跑通多步 Agent 形态。

## 7. 下一阶段（LangGraph 迁移建议）

可将现有执行节点映射为 graph node：

- `intent_node`
- `skill_select_node`
- `skill_run_node`
- `observe_node`
- `answer_node`

并增加：

- 人工审批节点（高风险操作前）
- 失败重试与恢复节点
- 长任务持久化状态

## 8. 电力技能扩展建议

优先新增：

1. 文档解析 skill（PDF/Word/Excel/OCR）
2. 规程条款比对 skill
3. 操作票风险核查 skill
4. 报告生成 skill

每个 skill 建议带：

- 输入 schema（必填字段、默认值）
- 输出 schema（结果、引用、结构化字段）
- 错误码约定（可重试/不可重试）
