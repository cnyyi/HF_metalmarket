# V3 Agent 智能分析系统设计文档

## 变更原因

V2（Function Calling）虽已让 LLM 不直接写 SQL，但存在两个问题：
1. `agent_tools.py` 中约 15 个 executor 仍包含原始 SQL，绕过 Service 层
2. 缺乏多步骤推理、风险识别、图表生成、结构化报告等高级分析能力

V3 升级为 **Planner → Executor → Memory → Chart/Risk/Report → Explainer** 架构，实现智能分析系统。

## 决策记录

| 项目 | 决策 |
|------|------|
| 架构 | 三阶段：Planner → Executor → Explainer，中间插入 Memory/Chart/Risk/Report |
| Planner | LLM 驱动（Function Calling），规则兜底 |
| Executor | 支持 `$step1.xxx` 变量引用，SQL 迁移到 Service 层 |
| Memory | 字典存储，支持点号路径访问 |
| Chart Builder | 规则驱动，自动判断图表类型（饼图/折线图/柱状图） |
| Risk Engine | 纯规则引擎，不依赖 LLM |
| Report Builder | 从 Memory + Risks 生成结构化报告（总体/费用/风险/建议） |
| Explainer | Prompt 约束输出格式，替换 system prompt |
| API | 扩展现有 `/agent/chat/send` 返回格式，新增 chart/risks/steps 字段 |
| 目录 | `app/services/agent/` 子包，8 个模块文件 |

## 整体架构

```
用户问题
    ↓
Planner（LLM 规划 + 规则兜底）
    ↓ 输出: Plan = [{id, tool, args}]
    ↓
Executor（逐步执行，支持 $step1.xxx 变量引用）
    ↓ 每步结果写入 Memory
    ↓
Memory（存储中间结果）
    ↓
Chart Builder（从 Memory 生成图表数据）
Risk Engine（从 Memory 识别风险）
Report Builder（从 Memory + Risks 生成结构化报告）
    ↓
Explainer（LLM 格式化输出，替换 system prompt）
    ↓
返回: {content, chart, risks, steps, tool_calls, conversation_id}
```

## 目录结构

```
app/services/agent/
├── __init__.py              # 导出 AgentService
├── agent_service.py         # 主入口，编排三阶段流程
├── planner.py               # Planner — LLM 规划 + 规则兜底
├── executor.py              # Executor — 工具执行 + 变量引用
├── memory.py                # Memory — 中间结果存储
├── tools.py                 # Tools — 工具注册（SQL 已迁移到 Service）
├── chart_builder.py         # Chart Builder — 图表数据生成
├── risk_engine.py           # Risk Engine — 规则引擎
├── report_builder.py        # Report Builder — 结构化报告
└── prompts.py               # Planner + Explainer prompt
```

## 文件变更清单

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `app/services/agent/__init__.py` | 包初始化，导出 AgentService |
| 新建 | `app/services/agent/agent_service.py` | 主入口，编排三阶段 |
| 新建 | `app/services/agent/planner.py` | Planner 模块 |
| 新建 | `app/services/agent/executor.py` | Executor 模块 |
| 新建 | `app/services/agent/memory.py` | Memory 模块 |
| 新建 | `app/services/agent/tools.py` | 工具注册（从 agent_tools.py 迁移重构） |
| 新建 | `app/services/agent/chart_builder.py` | 图表构建 |
| 新建 | `app/services/agent/risk_engine.py` | 风险引擎 |
| 新建 | `app/services/agent/report_builder.py` | 报告生成 |
| 新建 | `app/services/agent/prompts.py` | Prompt 定义 |
| 修改 | `app/services/agent_service.py` | 改为从 agent 包导入，保持向后兼容 |
| 修改 | `app/services/agent_tools.py` | 改为从 agent 包导入，保持向后兼容 |
| 修改 | `app/services/agent_prompt_builder.py` | 改为从 agent 包导入，保持向后兼容 |
| 修改 | `app/routes/agent.py` | 适配新返回格式 |
| 修改 | `templates/agent/chat.html` | 增加图表渲染 + 风险提示样式 |
| 修改 | `templates/agent/wx_chat.html` | 增加图表渲染 + 风险提示样式 |
| 修改 | 6 个 Service 文件 | 新增方法承接迁移的 SQL |

## 模块详细设计

### 1. Planner

两种模式，自适应切换：

**LLM 模式**（默认）：LLM 通过 Function Calling 返回 tool_calls，每个 tool_call 就是一个步骤。LLM 可一次返回多个 tool_calls 实现多步骤规划。

**规则模式**（兜底）：当 LLM 不可用或超时时，用关键词匹配：

| 关键词 | 工具 |
|--------|------|
| 应付 | query_payable_summary |
| 合同到期 | query_expiring_contracts |
| 商户概况 | query_merchant_overview |
| 应收 | query_receivable_summary |
| 逾期 | query_overdue_receivables |
| 水电 | query_electricity_stats, query_water_stats |
| 趋势 | query_monthly_trend |
| 财务汇总 | query_finance_summary |

Planner 输出格式（统一）：
```python
[{"id": "step1", "tool": "query_payable_summary", "args": {"period": "this_month"}}]
```

### 2. Executor

核心能力：
- 按 Plan 顺序执行工具
- 支持 `$step1.amount` 变量引用（从 Memory 中解析）
- 自动注入 `_merchant_id` 和 `_source` 权限参数
- 每步结果写入 Memory

```python
class Executor:
    def __init__(self, registry, memory):
        self.registry = registry
        self.memory = memory

    def execute_plan(self, plan, injected_kwargs):
        for step in plan:
            resolved_args = self._resolve_args(step['args'])
            resolved_args.update(injected_kwargs)
            result = self.registry.execute(step['tool'], **resolved_args)
            self.memory.set(step['id'], result)
        return self.memory.get_all()

    def _resolve_args(self, args):
        resolved = {}
        for key, value in args.items():
            if isinstance(value, str) and value.startswith('$'):
                resolved[key] = self.memory.get(value[1:])
            else:
                resolved[key] = value
        return resolved
```

### 3. Memory

```python
class Memory:
    def __init__(self):
        self._data = {}

    def set(self, step_id, result):
        self._data[step_id] = result

    def get(self, path):
        parts = path.split('.')
        value = self._data.get(parts[0])
        for key in parts[1:]:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    def get_all(self):
        return dict(self._data)
```

### 4. Tools（SQL 迁移）

#### 迁移清单

| 当前 executor | SQL 涉及的表 | 迁移目标 Service | 新增方法名 |
|---|---|---|---|
| `_exec_query_finance_summary` | Receivable, Payable, CashFlow | FinanceService | `get_finance_summary` |
| `_exec_query_monthly_trend` | CashFlow | FinanceService | `get_monthly_trend` |
| `_make_expiring_contracts_executor` | Contract, Merchant | ContractService | `get_expiring_contracts` |
| `_make_contract_stats_executor` | Contract | ContractService | `get_contract_stats` |
| `_make_receivable_summary_executor` | Receivable, Merchant | ReceivableService | `get_receivable_summary` |
| `_make_overdue_receivables_executor` | Receivable, Merchant, Sys_Dictionary | ReceivableService | `get_overdue_receivables` |
| `_make_payable_summary_executor` | Payable | FinanceService | `get_payable_summary` |
| `_make_overdue_payables_executor` | Payable | FinanceService | `get_overdue_payables` |
| `_make_plot_stats_executor` | Plot | PlotService | `get_plot_stats` |
| `_make_electricity_stats_executor` | UtilityReading, ContractElectricityMeter, Contract, Merchant | UtilityService | `get_electricity_stats` |
| `_make_water_stats_executor` | UtilityReading, ContractWaterMeter, Contract, Merchant | UtilityService | `get_water_stats` |
| `_make_prepayment_summary_executor` (wx) | Prepayment | PrepaymentService | `get_merchant_prepayment_summary` |
| `_make_deposit_summary_executor` (wx) | Deposit | DepositService | `get_merchant_deposit_summary` |
| `_make_garbage_fees_executor` | GarbageFee, Merchant | GarbageService | `get_garbage_fees` |
| `_make_merchant_overview_executor` | Contract, Receivable, UtilityReading | MerchantService | `get_merchant_overview` |

#### 迁移原则

1. SQL 搬到 Service 层，executor 只做一行调用
2. Service 方法签名包含 `merchant_id` 和 `source` 参数，权限控制在 Service 内完成
3. 内存过滤改为 SQL 过滤（当前很多 executor 先取 500 条再 Python 过滤）
4. 保持现有 Service 方法不变，只新增方法

#### 迁移后 executor 示例

```python
def _make_receivable_summary_executor(receivable_svc):
    def executor(group_by_merchant=False, _merchant_id=None, _source='admin'):
        return receivable_svc.get_receivable_summary(
            group_by_merchant=group_by_merchant,
            merchant_id=_merchant_id if _source == 'wx' else None
        )
    return executor
```

### 5. Chart Builder

规则驱动，从 Memory 中的数据自动判断图表类型：

```python
class ChartBuilder:
    def build(self, memory_data):
        charts = []
        for step_id, data in memory_data.items():
            if self._is_fee_breakdown(data):
                charts.append(self._build_pie(data, "费用构成"))
            elif self._is_time_series(data):
                charts.append(self._build_line(data, "趋势"))
            elif self._is_category_stats(data):
                charts.append(self._build_bar(data, "分类统计"))
        return charts
```

判断规则：
- 存在 name + value 键值对列表 → 饼图（费用构成、押金类型分布等）
- 存在 month + income/expense 字段 → 折线图（收支趋势）
- 存在 status + count 字段 → 柱状图（合同状态分布等）

输出格式（ECharts 兼容）：
```json
{
  "type": "pie",
  "title": "费用构成",
  "data": [{"name": "租金", "value": 80000}, {"name": "电费", "value": 20000}]
}
```

### 6. Risk Engine

纯规则引擎，不依赖 LLM：

```python
class RiskEngine:
    def analyze(self, memory_data):
        risks = []
        for step_id, data in memory_data.items():
            risks.extend(self._check_contract_risks(data))
            risks.extend(self._check_cost_risks(data))
            risks.extend(self._check_finance_risks(data))
        return risks
```

风险规则：

| 类型 | 条件 | 等级 |
|------|------|------|
| 合同风险 | 有合同 30 天内到期 | high |
| 合同风险 | 有合同 60 天内到期 | medium |
| 成本风险 | 单项费用占比 > 70% | medium |
| 资金风险 | 逾期应收 > 0 | high |
| 资金风险 | 应收余额 > 应付余额 3 倍 | medium |

输出格式：
```json
[{"level": "high", "type": "contract", "message": "3个合同30天内到期"}]
```

### 7. Report Builder

从 Memory + Risks 生成结构化报告：

```python
class ReportBuilder:
    def build(self, memory_data, risks):
        sections = []
        sections.append(self._build_summary(memory_data))
        sections.append(self._build_details(memory_data))
        sections.append(self._build_risks(risks))
        sections.append(self._build_suggestions(risks))
        return '\n\n'.join(s for s in sections if s)
```

报告结构：
```
【总体情况】
本月应付 ¥120,000.00，已付 ¥80,000.00，剩余 ¥40,000.00

【费用结构】
- 租金：¥80,000.00
- 电费：¥20,000.00
- 水费：¥5,000.00

【风险提示】
⚠️ 3个合同30天内到期
⚠️ 逾期应收账款 ¥15,000.00

【建议措施】
- 关注即将到期合同的续签情况
- 跟进逾期应收账款的催收
```

### 8. Prompts

#### Planner Prompt

```
你是宏发金属交易市场的数据分析规划师。根据用户问题，决定需要查询哪些数据。

规则：
1. 如果问题只需一个工具就能回答，直接调用该工具
2. 如果问题需要多个数据维度，同时调用多个工具
3. 不要编造数据，只使用可用工具
4. 优先使用汇总类工具（如 query_finance_summary），再按需查明细

可用工具：{tool_list}
```

#### Explainer Prompt

```
你是宏发金属交易市场的数据分析师。根据查询结果，用自然语言回答用户问题。

输出规范：
1. 先给结论，再给数据支撑
2. 金额用 ¥ 符号，保留两位小数（如 ¥12,345.67）
3. 日期用 yyyy年MM月dd日 格式
4. 多条数据用表格或列表呈现
5. 如果数据为空，如实告知"暂无相关数据"
6. 不要重复原始数据，要提炼关键信息
7. 涉及对比时，指出变化趋势（上升/下降/持平）

输出格式选择：
- 单个数值 → 一句话总结
- 2-5 条记录 → 列表
- 6+ 条记录 → Markdown 表格
- 趋势数据 → 文字描述 + 关键节点
```

### 9. AgentService 主流程

```python
class AgentService:
    def chat(self, user_id, conversation_id, message, source='admin',
             merchant_id=None, merchant_name=None):
        # 1. 会话管理
        if not conversation_id:
            conversation_id = self._create_conversation(user_id, message, source)
        self._save_message(conversation_id, 'user', message)
        history = self._load_history(conversation_id)

        # 2. 初始化组件
        registry = get_registry()
        memory = Memory()
        planner = Planner(self._get_client, registry)
        executor = Executor(registry, memory)
        chart_builder = ChartBuilder()
        risk_engine = RiskEngine()
        report_builder = ReportBuilder()

        injected_kwargs = {'_merchant_id': merchant_id, '_source': source}

        # 3. Phase 1: Planner
        plan, tool_call_detail = planner.plan(
            history, message, source, merchant_id, merchant_name, injected_kwargs
        )

        # 4. Phase 2: Executor
        if plan:
            memory_data = executor.execute_plan(plan, injected_kwargs)
        else:
            memory_data = {}

        # 5. 后处理
        charts = chart_builder.build(memory_data)
        risks = risk_engine.analyze(memory_data)
        report = report_builder.build(memory_data, risks)

        # 6. Phase 3: Explainer
        if plan and memory_data:
            final_content = self._explain(
                history, message, plan, memory_data, report, source, merchant_name
            )
        else:
            final_content = planner.get_direct_response() or '暂无法回答该问题'

        # 7. 保存消息
        self._save_message(conversation_id, 'assistant', final_content,
                          generated_sql=json.dumps(tool_call_detail, ensure_ascii=False) if tool_call_detail else None)

        return {
            'conversation_id': conversation_id,
            'content': final_content,
            'chart': charts,
            'risks': risks,
            'steps': [{'id': s['id'], 'tool': s['tool'], 'args': s['args']} for s in plan] if plan else [],
            'tool_calls': tool_call_detail,
            'generated_sql': None,
            'query_result': None
        }
```

### 10. API 返回格式扩展

当前返回：
```json
{
  "conversation_id": 1,
  "content": "...",
  "tool_calls": [...],
  "generated_sql": null,
  "query_result": null
}
```

V3 返回：
```json
{
  "conversation_id": 1,
  "content": "结构化报告文本...",
  "chart": null,
  "risks": [],
  "steps": [],
  "tool_calls": [...],
  "generated_sql": null,
  "query_result": null
}
```

新增字段：
- `chart`: ChartBuilder 输出，null 或 `{"type": "pie", "title": "...", "data": [...]}`
- `risks`: RiskEngine 输出，`[{"level": "high", "type": "contract", "message": "..."}]`
- `steps`: 执行步骤列表，`[{"id": "step1", "tool": "query_payables", "args": {...}}]`

### 11. 前端变更

#### chat.html 变更

1. 消息渲染增加图表区域：当 `chart` 不为 null 时，用 ECharts 渲染
2. 风险提示样式：`risks` 数组非空时，在消息下方显示醒目的风险标签
3. 需要引入 ECharts CDN

#### wx_chat.html 变更

同 chat.html，增加图表渲染和风险提示。

### 12. 向后兼容

- `app/services/agent_service.py` 保留，改为从 `app/services/agent/` 导入
- `app/services/agent_tools.py` 保留，改为从 `app/services/agent/` 导入
- `app/services/agent_prompt_builder.py` 保留，改为从 `app/services/agent/` 导入
- 数据库表不变
- 环境变量不变
