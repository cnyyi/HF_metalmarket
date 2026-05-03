# AI 数据查询助手 v2 — Function Calling 方案

## 变更原因

v1（Text-to-SQL）存在根本问题：AI 生成的 SQL 可能使用错误的状态值或关联条件，导致查询结果不准确。例如用 `Status = N'执行中'` 查合同，但实际系统中该字段值是 `N'已到期'` 等。

v2 改为 **Function Calling**（工具调用），让 LLM 调用现有业务 Service 方法，数据准确性由 Service 层保障。

## 决策记录

| 项目 | 决策 |
|------|------|
| LLM | DeepSeek V4 Pro（已配置） |
| 数据访问 | Function Calling → 现有 Service 方法 |
| 覆盖范围 | 全部模块（~50 个工具） |
| 工具调用 | 并行多工具 |
| 权限控制 | executor 注入 `_merchant_id` / `_source` |
| 文件变更 | 新建 agent_tools.py，重写 agent_service.py，简化 prompt_builder，废弃 sql_validator |

## 整体架构

```
用户提问 → Agent Routes → AgentService
                              ↓ 构建 messages + tools
                          DeepSeek API → 返回 tool_calls
                              ↓
                          AgentToolRegistry.execute()
                              ↓
                          现有 Service 层 (FinanceService, ContractService...)
                              ↓
                          结果汇总 → 喂回 DeepSeek API → 自然语言回答
```

## 文件变更

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `app/services/agent_tools.py` | 工具 schema 定义 + registry + executor 函数 |
| 重写 | `app/services/agent_service.py` | Function Calling 替代 Text-to-SQL |
| 简化 | `app/services/agent_prompt_builder.py` | 移除 schema，只保留角色定义 |
| 废弃 | `app/services/agent_sql_validator.py` | 不再需要 SQL 校验 |
| 不变 | `app/routes/agent.py` | 接口不变 |
| 不变 | `templates/agent/*.html` | 前端不变 |

## AgentToolRegistry 设计

每个工具有两个部分：

1. **schema** — OpenAI Function Calling 格式的函数描述，供 LLM 理解
2. **executor** — Python 可调用对象，实际执行业务逻辑

```python
class AgentToolRegistry:
    def __init__(self):
        self._tools = {}  # name → {'schema': dict, 'executor': callable}

    def register(self, name, schema, executor):
        self._tools[name] = {'schema': schema, 'executor': executor}

    def get_all_schemas(self):
        return [t['schema'] for t in self._tools.values()]

    def execute(self, name, **kwargs):
        tool = self._tools[name]
        return tool['executor'](**kwargs)
```

## 工具清单（~50 个）

### 通用（3）
- `query_today` — 获取当前日期、月份信息
- `query_finance_summary` — 综合财务汇总（应收/应付/流水总体情况）
- `query_monthly_trend` — 月度收支趋势（按月汇总收入/支出）

### 商户（2）
- `query_merchants` — 商户列表/搜索（name, type, status）
- `query_merchant_detail` — 商户详情（含合同数、应收应付余额）

### 合同（4）
- `query_contracts` — 合同列表/搜索（merchant_id, status, keyword）
- `query_expiring_contracts` — 即将到期合同（days: 30/60/90 天内到期）
- `query_contract_stats` — 合同统计（按状态/业态分组统计）
- `query_contract_detail` — 合同详情

### 地块（2）
- `query_plots` — 地块列表/搜索（plot_type, status）
- `query_plot_stats` — 地块统计（按类型汇总面积/数量/空闲率）

### 财务-应收（3）
- `query_receivables` — 应收账款列表（merchant_id, status, period）
- `query_receivable_summary` — 应收账款汇总（总金额/已收/剩余，按商户分组）
- `query_overdue_receivables` — 逾期应收账款

### 财务-应付（3）
- `query_payables` — 应付账款列表（vendor_name, status, period）
- `query_payable_summary` — 应付账款汇总（总金额/已付/剩余，按供应商分组）
- `query_overdue_payables` — 逾期应付账款

### 财务-流水（2）
- `query_cash_flows` — 现金流水列表（direction, period, expense_type_id）
- `query_cash_flow_summary` — 现金流统计（收入/支出汇总，按费用类型分组）

### 财务-账户（2）
- `query_accounts` — 账户列表（account_type, status）
- `query_account_balance` — 账户余额汇总

### 财务-预收预付（2）
- `query_prepayments` — 预收预付列表（direction, customer_type, status）
- `query_prepayment_summary` — 预收预付汇总（总金额/已核销/剩余）

### 财务-押金（2）
- `query_deposits` — 押金列表（deposit_type, status）
- `query_deposit_summary` — 押金汇总（总收取/已退还/已扣除/剩余）

### 财务-收付款记录（2）
- `query_collection_records` — 收款记录（period, payment_method, merchant_id）
- `query_payment_records` — 付款记录（period, payment_method, vendor_name）

### 水电（4）
- `query_meters` — 电表/水表列表（meter_type）
- `query_meter_readings` — 抄表记录（meter_type, month, merchant_id）
- `query_electricity_stats` — 电费统计（按月份/商户汇总）
- `query_water_stats` — 水费统计（按月份/商户汇总）

### 磅秤（3）
- `query_scales` — 磅秤列表
- `query_scale_records` — 过磅记录（period, product_name, vehicle_number）
- `query_scale_stats` — 过磅统计（按日期/产品汇总）

### 宿舍（3）
- `query_dorm_rooms` — 宿舍房间列表（room_type, status）
- `query_dorm_bills` — 宿舍账单（month, status, tenant_name）
- `query_dorm_occupancy` — 入住记录

### 垃圾（2）
- `query_garbage_collections` — 垃圾清运记录（period, garbage_type）
- `query_garbage_fees` — 商户垃圾费（year, merchant_id）

### 工资（2）
- `query_salary_records` — 工资记录（month, employee_name, status）
- `query_salary_stats` — 工资统计（按月汇总应发/实发）

### 费用单（2）
- `query_expense_orders` — 费用单列表（category, period, vendor_id）
- `query_expense_item_summary` — 费用按类型汇总

### 客户（2）
- `query_customers` — 往来客户列表/搜索
- `query_customer_transactions` — 客户交易历史（应收/应付/预收预付/押金/流水）

### 字典（1）
- `query_dictionary` — 查询系统字典（dict_type）

## 工具 Schema 格式（示例）

```python
{
    "type": "function",
    "function": {
        "name": "query_payable_summary",
        "description": "查询应付账款汇总统计。返回总笔数、总金额、已付金额、剩余金额。",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["this_month", "this_year", "last_month", "all"],
                    "description": "时间范围"
                },
                "status": {
                    "type": "string",
                    "enum": ["all", "待付款", "部分付款", "已付款"],
                    "description": "付款状态筛选"
                }
            },
            "required": []
        }
    }
}
```

## AgentService 核心流程

```python
def chat(self, user_id, conversation_id, message, source='admin', 
         merchant_id=None, merchant_name=None):
    # 1. 创建/加载会话
    # 2. 保存用户消息
    # 3. 加载对话历史
    # 4. 构建 messages = [system] + history + [user提问]
    # 5. 构建 tools = registry.get_all_schemas()
    # 6. 第一次 LLM 调用 → 可能返回 tool_calls 或直接文本
    # 7. 如果有 tool_calls：
    #    a. 并行执行所有工具（注入 _merchant_id, _source）
    #    b. tool_call + tool_result 追加到 messages
    #    c. 第二次 LLM 调用 → 自然语言回答
    # 8. 如果无 tool_calls：直接返回 LLM 文本
    # 9. 保存消息 + 返回结果
```

## System Prompt

```
你是宏发金属交易市场的数据查询助手。你可以调用工具函数查询
数据库，然后用自然语言回答用户的问题。

- 金额使用 ¥ 符号，保留两位小数
- 日期使用 yyyy年MM月dd日 格式
- 回答简洁明了，先给总体结论再给明细数据

{如果 source=='wx'}
你只能查询当前商户的数据，不能查看其他商户的信息。
```

## 商户端权限控制

所有 executor 接受隐式参数 `_merchant_id` 和 `_source`：

```python
def _exec_query_contracts(period='this_month', _merchant_id=None, _source='admin'):
    result = contract_svc.get_contracts(...)
    if _source == 'wx' and _merchant_id:
        result = [c for c in result if c.get('merchant_id') == _merchant_id]
    return result
```

## 前端

前后端接口不变，UI 不变。只需确保 `ajaxPost` / `agentPost` 的问题已修复（Content-Type: application/json）。

## 部署影响

- 数据库不变（AgentConversation + AgentMessage 表继续使用）
- 环境变量不变
- 依赖不变（openai 包已安装）
