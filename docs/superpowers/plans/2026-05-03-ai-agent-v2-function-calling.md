# AI 数据查询助手 v2 Function Calling 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将 AI Agent 从 Text-to-SQL 重构为 Function Calling 架构，让 LLM 调用现有业务 Service 方法查询数据，消除 SQL 生成不准确的问题。

**架构：** AgentToolRegistry 管理 ~50 个工具（schema + executor），AgentService.chat() 通过两轮 LLM 调用实现 Function Calling：第一轮 LLM 返回 tool_calls → 并行执行工具 → 工具结果喂回 LLM → 生成自然语言回答。

**技术栈：** Python 3 / Flask / DeepSeek API (OpenAI SDK) / pyodbc / SQL Server

---

## 文件结构

| 操作 | 文件 | 职责 |
|------|------|------|
| 新建 | `app/services/agent_tools.py` | 工具 schema 定义 + AgentToolRegistry + 所有 executor 函数 |
| 重写 | `app/services/agent_service.py` | Function Calling 核心流程（替代 Text-to-SQL） |
| 简化 | `app/services/agent_prompt_builder.py` | 仅保留简单角色定义（~20 行） |
| 废弃 | `app/services/agent_sql_validator.py` | 不再需要（保留文件不删，移除 import） |

不变的文件：
- `app/routes/agent.py` — 接口不变
- `templates/agent/chat.html` — 前端不变
- `templates/agent/wx_chat.html` — 前端不变
- `config/base.py` — 配置不变
- `.env` — 环境变量不变

---

### 任务 1：创建 AgentToolRegistry 框架

**文件：**
- 创建：`app/services/agent_tools.py`

- [ ] **步骤 1：创建文件骨架 — AgentToolRegistry 类 + 服务实例化**

```python
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name, schema, executor):
        self._tools[name] = {'schema': schema, 'executor': executor}

    def get_all_schemas(self):
        return [t['schema'] for t in self._tools.values()]

    def execute(self, name, **kwargs):
        tool = self._tools[name]
        return tool['executor'](**kwargs)


_registry = None


def get_registry():
    global _registry
    if _registry is None:
        _registry = AgentToolRegistry()
        _register_all_tools(_registry)
    return _registry


def _register_all_tools(reg):
    from app.services.merchant_service import MerchantService
    from app.services.contract_service import ContractService
    from app.services.plot_service import PlotService
    from app.services.finance_service import FinanceService
    from app.services.receivable_service import ReceivableService
    from app.services.prepayment_service import PrepaymentService
    from app.services.deposit_service import DepositService
    from app.services.account_service import AccountService
    from app.services.utility_service import UtilityService
    from app.services.scale_service import ScaleService
    from app.services.dorm_service import DormService
    from app.services.salary_service import SalaryService
    from app.services.garbage_service import GarbageService
    from app.services.expense_service import ExpenseService
    from app.services.customer_service import CustomerService
    from app.services.dict_service import DictService

    merchant_svc = MerchantService()
    contract_svc = ContractService()
    plot_svc = PlotService()
    finance_svc = FinanceService()
    receivable_svc = ReceivableService()
    prepayment_svc = PrepaymentService()
    deposit_svc = DepositService()
    account_svc = AccountService()
    utility_svc = UtilityService()
    scale_svc = ScaleService()
    dorm_svc = DormService()
    salary_svc = SalaryService()
    garbage_svc = GarbageService()
    expense_svc = ExpenseService()
    customer_svc = CustomerService()
    dict_svc = DictService()

    _register_common_tools(reg)
    _register_dictionary_tools(reg, dict_svc)
    _register_merchant_tools(reg, merchant_svc)
    _register_contract_tools(reg, contract_svc)
    _register_plot_tools(reg, plot_svc)
    _register_receivable_tools(reg, receivable_svc)
    _register_payable_tools(reg, finance_svc)
    _register_cashflow_tools(reg, finance_svc)
    _register_account_tools(reg, account_svc)
    _register_prepayment_tools(reg, prepayment_svc)
    _register_deposit_tools(reg, deposit_svc)
    _register_collection_payment_tools(reg, finance_svc)
    _register_utility_tools(reg, utility_svc)
    _register_scale_tools(reg, scale_svc)
    _register_dorm_tools(reg, dorm_svc)
    _register_garbage_tools(reg, garbage_svc)
    _register_salary_tools(reg, salary_svc)
    _register_expense_tools(reg, expense_svc)
    _register_customer_tools(reg, customer_svc, finance_svc)
```

- [ ] **步骤 2：验证文件可导入**

运行：
```bash
python -c "from app.services.agent_tools import get_registry; r = get_registry(); print('Registry created')"
```
预期：无报错，输出 "Registry created"（即使工具还未注册）

---

### 任务 2：通用工具 + 字典工具（4 个）

**文件：**
- 修改：`app/services/agent_tools.py`

- [ ] **步骤 1：注册通用工具（query_today, query_finance_summary, query_monthly_trend）**

```python
def _register_common_tools(reg):
    reg.register('query_today', {
        "type": "function",
        "function": {
            "name": "query_today",
            "description": "获取当前日期信息，包括年月日、本月月初日期、下月月初日期、当前月份名称",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }, _exec_query_today)

    reg.register('query_finance_summary', {
        "type": "function",
        "function": {
            "name": "query_finance_summary",
            "description": "查询综合财务汇总数据，包括应收账款总额/已收/未收、应付账款总额/已付/未付、本月收入/支出/结余",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["this_month", "this_year", "all"],
                        "description": "统计时间范围"
                    }
                },
                "required": []
            }
        }
    }, _exec_query_finance_summary)

    reg.register('query_monthly_trend', {
        "type": "function",
        "function": {
            "name": "query_monthly_trend",
            "description": "查询月度收支趋势，按月汇总收入/支出金额，用于分析经营走势",
            "parameters": {
                "type": "object",
                "properties": {
                    "months": {
                        "type": "integer",
                        "description": "查询最近几个月的趋势，默认6个月"
                    }
                },
                "required": []
            }
        }
    }, _exec_query_monthly_trend)


def _exec_query_today(_merchant_id=None, _source='admin'):
    now = datetime.now()
    first_day = datetime(now.year, now.month, 1)
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    return {
        'today': now.strftime('%Y-%m-%d'),
        'year': now.year,
        'month': now.month,
        'month_name': f'{now.year}年{now.month}月',
        'first_day_of_month': first_day.strftime('%Y-%m-%d'),
        'first_day_of_next_month': next_month.strftime('%Y-%m-%d'),
        'current_year': now.year
    }


def _exec_query_finance_summary(period='this_month', _merchant_id=None, _source='admin'):
    from utils.database import DBConnection
    with DBConnection() as conn:
        cursor = conn.cursor()

        date_filter = ''
        if period == 'this_month':
            date_filter = "AND CreateTime >= DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0)"
        elif period == 'this_year':
            date_filter = "AND CreateTime >= DATEADD(YEAR, DATEDIFF(YEAR, 0, GETDATE()), 0)"

        merchant_filter = ''
        params = []
        if _source == 'wx' and _merchant_id:
            merchant_filter = "AND MerchantID = ?"
            params = [_merchant_id]

        cursor.execute(f"""
            SELECT SUM(Amount) AS total_receivable,
                   SUM(PaidAmount) AS total_paid_receivable,
                   SUM(RemainingAmount) AS total_remaining_receivable
            FROM Receivable
            WHERE IsActive = 1 {date_filter} {merchant_filter}
        """, params)
        receivable = cursor.fetchone()

        cursor.execute(f"""
            SELECT SUM(Amount) AS total_payable,
                   SUM(PaidAmount) AS total_paid_payable,
                   SUM(RemainingAmount) AS total_remaining_payable
            FROM Payable
            WHERE IsActive = 1 {date_filter} {merchant_filter.replace('MerchantID', 'CustomerID')}
        """, params)
        payable = cursor.fetchone()

        cash_filter = date_filter.replace('CreateTime', 'TransactionDate')
        cursor.execute(f"""
            SELECT
                SUM(CASE WHEN Direction = N'收入' THEN Amount ELSE 0 END) AS total_income,
                SUM(CASE WHEN Direction = N'支出' THEN Amount ELSE 0 END) AS total_expense
            FROM CashFlow
            WHERE 1=1 {cash_filter}
        """)
        cash = cursor.fetchone()

        return {
            'period': period,
            'total_receivable': float(receivable.total_receivable or 0),
            'total_paid_receivable': float(receivable.total_paid_receivable or 0),
            'total_remaining_receivable': float(receivable.total_remaining_receivable or 0),
            'total_payable': float(payable.total_payable or 0),
            'total_paid_payable': float(payable.total_paid_payable or 0),
            'total_remaining_payable': float(payable.total_remaining_payable or 0),
            'total_income': float(cash.total_income or 0),
            'total_expense': float(cash.total_expense or 0),
            'balance': float((cash.total_income or 0) - (cash.total_expense or 0))
        }


def _exec_query_monthly_trend(months=6, _merchant_id=None, _source='admin'):
    from utils.database import DBConnection
    with DBConnection() as conn:
        cursor = conn.cursor()

        merchant_filter = ''
        params = []
        if _source == 'wx' and _merchant_id:
            merchant_filter = "AND MerchantID = ?"
            params = [_merchant_id]

        cursor.execute(f"""
            SELECT TOP {int(months)}
                FORMAT(TransactionDate, 'yyyy-MM') AS month_label,
                SUM(CASE WHEN Direction = N'收入' THEN Amount ELSE 0 END) AS income,
                SUM(CASE WHEN Direction = N'支出' THEN Amount ELSE 0 END) AS expense
            FROM CashFlow
            WHERE TransactionDate >= DATEADD(MONTH, -{int(months)}, GETDATE())
            GROUP BY FORMAT(TransactionDate, 'yyyy-MM')
            ORDER BY month_label
        """)
        rows = cursor.fetchall()
        return [{'month': row.month_label, 'income': float(row.income or 0), 'expense': float(row.expense or 0)} for row in rows]
```

- [ ] **步骤 2：注册字典工具（query_dictionary）**

```python
def _register_dictionary_tools(reg, dict_svc):
    reg.register('query_dictionary', {
        "type": "function",
        "function": {
            "name": "query_dictionary",
            "description": "查询系统字典表，获取费用类型、商户类型、业态、支付方式等枚举列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "dict_type": {
                        "type": "string",
                        "enum": ["merchant_type", "business_type", "expense_item_income", "expense_item_expend",
                                 "unit_type", "payment_method", "salary_status", "dorm_room_type"],
                        "description": "字典类型编码"
                    }
                },
                "required": ["dict_type"]
            }
        }
    }, _make_dict_executor(dict_svc))


def _make_dict_executor(dict_svc):
    def executor(dict_type, _merchant_id=None, _source='admin'):
        result = dict_svc.get_dict_list(dict_type=dict_type, per_page=1000)
        return result.get('items', []) if isinstance(result, dict) else result
    return executor
```

- [ ] **步骤 3：验证工具注册**

运行：
```bash
python -c "from app.services.agent_tools import get_registry; r = get_registry(); schemas = r.get_all_schemas(); print(f'Tools registered: {len(schemas)}'); [print(s['function']['name']) for s in schemas]"
```
预期：输出 "Tools registered: 4" 及工具名称列表

---

### 任务 3：商户工具 + 合同工具（6 个）

**文件：**
- 修改：`app/services/agent_tools.py`

- [ ] **步骤 1：注册商户工具**

```python
def _register_merchant_tools(reg, merchant_svc):
    reg.register('query_merchants', {
        "type": "function",
        "function": {
            "name": "query_merchants",
            "description": "查询商户列表，支持按名称搜索、按类型和状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "商户名称关键词搜索"},
                    "merchant_type": {"type": "string", "description": "商户类型，如 company/个体工商户/业务往来"},
                    "status": {"type": "string", "description": "商户状态，如 正常"}
                },
                "required": []
            }
        }
    }, _make_merchants_executor(merchant_svc))

    reg.register('query_merchant_detail', {
        "type": "function",
        "function": {
            "name": "query_merchant_detail",
            "description": "查询单个商户的详细信息，包括基本信息、关联合同数量、应收应付余额",
            "parameters": {
                "type": "object",
                "properties": {
                    "merchant_id": {"type": "integer", "description": "商户ID"},
                    "merchant_name": {"type": "string", "description": "商户名称（如果不知道ID可以用名称查）"}
                },
                "required": []
            }
        }
    }, _make_merchant_detail_executor(merchant_svc))


def _make_merchants_executor(merchant_svc):
    def executor(search=None, merchant_type=None, status=None, _merchant_id=None, _source='admin'):
        if _source == 'wx' and _merchant_id:
            search = None
        result = merchant_svc.get_merchants(page=1, per_page=500, search=search)
        items = result.get('items', []) if isinstance(result, dict) else result
        if merchant_type:
            items = [m for m in items if m.get('MerchantType') == merchant_type or m.get('merchant_type') == merchant_type]
        if status:
            items = [m for m in items if m.get('Status') == status or m.get('status') == status]
        if _source == 'wx' and _merchant_id:
            items = [m for m in items if m.get('MerchantID') == _merchant_id or m.get('merchant_id') == _merchant_id]
        return items
    return executor


def _make_merchant_detail_executor(merchant_svc):
    def executor(merchant_id=None, merchant_name=None, _merchant_id=None, _source='admin'):
        if _source == 'wx' and _merchant_id:
            merchant_id = _merchant_id
        if merchant_id:
            return merchant_svc.get_merchant_by_id(merchant_id)
        if merchant_name:
            result = merchant_svc.get_merchants(page=1, per_page=500, search=merchant_name)
            items = result.get('items', []) if isinstance(result, dict) else result
            if items:
                return items[0]
        return {'error': '请提供商户ID或商户名称'}
    return executor
```

- [ ] **步骤 2：注册合同工具**

```python
def _register_contract_tools(reg, contract_svc):
    reg.register('query_contracts', {
        "type": "function",
        "function": {
            "name": "query_contracts",
            "description": "查询合同列表，支持按商户、状态、关键词筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "合同号或商户名关键词"},
                    "status": {"type": "string", "description": "合同状态，如 生效"},
                    "sort_by": {"type": "string", "enum": ["create_time", "end_date", "start_date"], "description": "排序字段"},
                    "sort_order": {"type": "string", "enum": ["asc", "desc"], "description": "排序方向"}
                },
                "required": []
            }
        }
    }, _make_contracts_executor(contract_svc))

    reg.register('query_expiring_contracts', {
        "type": "function",
        "function": {
            "name": "query_expiring_contracts",
            "description": "查询即将到期的合同，可按天数筛选（30天/60天/90天内到期）",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "未来多少天内到期，默认30天", "enum": [30, 60, 90]}
                },
                "required": []
            }
        }
    }, _make_expiring_contracts_executor(contract_svc))

    reg.register('query_contract_stats', {
        "type": "function",
        "function": {
            "name": "query_contract_stats",
            "description": "统计合同数量、金额，可按状态和业态分组",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }, _make_contract_stats_executor(contract_svc))

    reg.register('query_contract_detail', {
        "type": "function",
        "function": {
            "name": "query_contract_detail",
            "description": "查询单个合同的详细信息，包括关联地块、租金明细",
            "parameters": {
                "type": "object",
                "properties": {
                    "contract_id": {"type": "integer", "description": "合同ID"}
                },
                "required": ["contract_id"]
            }
        }
    }, _make_contract_detail_executor(contract_svc))


def _make_contracts_executor(contract_svc):
    def executor(search=None, status=None, sort_by='create_time', sort_order='desc',
                  _merchant_id=None, _source='admin'):
        if _source == 'wx' and _merchant_id:
            search = str(_merchant_id)
        result = contract_svc.get_contract_list(
            page=1, per_page=500, search=search,
            sort_by=sort_by, sort_order=sort_order
        )
        items = result.get('items', []) if isinstance(result, dict) else result
        if status:
            items = [c for c in items if c.get('Status') == status or c.get('status') == status]
        if _source == 'wx' and _merchant_id:
            items = [c for c in items if c.get('MerchantID') == _merchant_id or c.get('merchant_id') == _merchant_id]
        return items
    return executor


def _make_expiring_contracts_executor(contract_svc):
    def executor(days=30, _merchant_id=None, _source='admin'):
        from utils.database import DBConnection
        with DBConnection() as conn:
            cursor = conn.cursor()
            merchant_filter = ''
            params = []
            if _source == 'wx' and _merchant_id:
                merchant_filter = "AND c.MerchantID = ?"
                params = [_merchant_id]
            cursor.execute(f"""
                SELECT TOP 500 c.ContractID, c.ContractNo, c.EndDate, c.ActualAmount,
                       c.Status, m.MerchantName
                FROM Contract c
                INNER JOIN Merchant m ON c.MerchantID = m.MerchantID
                WHERE c.EndDate >= CAST(GETDATE() AS DATE)
                  AND c.EndDate <= DATEADD(DAY, ?, CAST(GETDATE() AS DATE))
                  AND c.Status = N'生效'
                  {merchant_filter}
                ORDER BY c.EndDate
            """, [days] + params)
            rows = cursor.fetchall()
            return [{
                'contract_id': row.ContractID, 'contract_no': row.ContractNo,
                'end_date': row.EndDate.strftime('%Y-%m-%d') if row.EndDate else '',
                'actual_amount': float(row.ActualAmount or 0),
                'status': row.Status, 'merchant_name': row.MerchantName
            } for row in rows]
    return executor


def _make_contract_stats_executor(contract_svc):
    def executor(_merchant_id=None, _source='admin'):
        from utils.database import DBConnection
        with DBConnection() as conn:
            cursor = conn.cursor()
            merchant_filter = ''
            params = []
            if _source == 'wx' and _merchant_id:
                merchant_filter = "WHERE MerchantID = ?"
                params = [_merchant_id]
            cursor.execute(f"""
                SELECT Status, COUNT(*) AS count, SUM(ISNULL(ActualAmount, 0)) AS total_amount
                FROM Contract
                {merchant_filter}
                GROUP BY Status
            """, params)
            rows = cursor.fetchall()
            return [{'status': row.Status, 'count': row.count, 'total_amount': float(row.total_amount or 0)} for row in rows]
    return executor


def _make_contract_detail_executor(contract_svc):
    def executor(contract_id, _merchant_id=None, _source='admin'):
        return contract_svc.get_contract_detail(contract_id)
    return executor
```

- [ ] **步骤 3：验证**

运行：
```bash
python -c "from app.services.agent_tools import get_registry; r = get_registry(); print(f'Tools: {len(r.get_all_schemas())}')"
```
预期：输出 "Tools: 10"

---

### 任务 4：地块工具（2 个）

**文件：**
- 修改：`app/services/agent_tools.py`

- [ ] **步骤 1：注册地块工具**

```python
def _register_plot_tools(reg, plot_svc):
    reg.register('query_plots', {
        "type": "function",
        "function": {
            "name": "query_plots",
            "description": "查询地块/铺位列表，支持按类型、状态、出租状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "plot_type": {"type": "string", "description": "地块类型：水泥/钢材/砖类/其他"},
                    "status": {"type": "string", "description": "状态：空闲/已出租"},
                    "rent_status": {"type": "string", "description": "出租状态"},
                    "search": {"type": "string", "description": "地块编号关键词搜索"}
                },
                "required": []
            }
        }
    }, _make_plots_executor(plot_svc))

    reg.register('query_plot_stats', {
        "type": "function",
        "function": {
            "name": "query_plot_stats",
            "description": "按类型统计地块的面积、数量和空闲率",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }, _make_plot_stats_executor(plot_svc))


def _make_plots_executor(plot_svc):
    def executor(plot_type=None, status=None, rent_status=None, search=None,
                  _merchant_id=None, _source='admin'):
        result = plot_svc.get_plot_list(
            page=1, per_page=500, search=search, status=status,
            plot_type=plot_type, rent_status=rent_status,
            sort_by='plot_number', sort_dir='asc'
        )
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_plot_stats_executor(plot_svc):
    def executor(_merchant_id=None, _source='admin'):
        from utils.database import DBConnection
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT PlotType, COUNT(*) AS count, SUM(ISNULL(Area, 0)) AS total_area,
                       SUM(CASE WHEN Status = N'空闲' THEN 1 ELSE 0 END) AS vacant_count,
                       SUM(CASE WHEN Status = N'空闲' THEN ISNULL(Area, 0) ELSE 0 END) AS vacant_area
                FROM Plot
                GROUP BY PlotType
                ORDER BY PlotType
            """)
            rows = cursor.fetchall()
            result = []
            for row in rows:
                total_area = float(row.total_area or 0)
                vacant_area = float(row.vacant_area or 0)
                result.append({
                    'plot_type': row.PlotType, 'count': row.count,
                    'total_area': total_area, 'vacant_count': row.vacant_count,
                    'vacant_area': vacant_area,
                    'vacancy_rate': f'{round(vacant_area / total_area * 100, 1)}%' if total_area > 0 else '0%'
                })
            return result
    return executor
```

- [ ] **步骤 2：验证**

运行：
```bash
python -c "from app.services.agent_tools import get_registry; r = get_registry(); print(f'Tools: {len(r.get_all_schemas())}')"
```
预期：输出 "Tools: 12"

---

### 任务 5：财务应收工具 + 应付工具（6 个）

**文件：**
- 修改：`app/services/agent_tools.py`

- [ ] **步骤 1：注册应收工具**

```python
def _register_receivable_tools(reg, receivable_svc):
    reg.register('query_receivables', {
        "type": "function",
        "function": {
            "name": "query_receivables",
            "description": "查询应收账款列表，支持按商户、状态、期间筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "商户名关键词"},
                    "status": {"type": "string", "enum": ["未付款", "部分付款", "已付款", "all"], "description": "付款状态"},
                    "expense_type_id": {"type": "integer", "description": "费用类型ID"}
                },
                "required": []
            }
        }
    }, _make_receivables_executor(receivable_svc))

    reg.register('query_receivable_summary', {
        "type": "function",
        "function": {
            "name": "query_receivable_summary",
            "description": "查询应收账款汇总，包括总金额、已收金额、剩余金额，可按商户分组",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by_merchant": {"type": "boolean", "description": "是否按商户分组汇总"}
                },
                "required": []
            }
        }
    }, _make_receivable_summary_executor(receivable_svc))

    reg.register('query_overdue_receivables', {
        "type": "function",
        "function": {
            "name": "query_overdue_receivables",
            "description": "查询逾期未付的应收账款（超过到期日仍未付清）",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }, _make_overdue_receivables_executor(receivable_svc))


def _make_receivables_executor(receivable_svc):
    def executor(search=None, status=None, expense_type_id=None,
                  _merchant_id=None, _source='admin'):
        if _source == 'wx' and _merchant_id:
            search = str(_merchant_id)
        result = receivable_svc.get_receivables(
            page=1, per_page=500, search=search,
            status=status, expense_type_id=expense_type_id
        )
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_receivable_summary_executor(receivable_svc):
    def executor(group_by_merchant=False, _merchant_id=None, _source='admin'):
        from utils.database import DBConnection
        with DBConnection() as conn:
            cursor = conn.cursor()
            merchant_filter = ''
            params = []
            if _source == 'wx' and _merchant_id:
                merchant_filter = "AND r.MerchantID = ?"
                params = [_merchant_id]
            if group_by_merchant:
                cursor.execute(f"""
                    SELECT m.MerchantName,
                           SUM(r.Amount) AS total_amount,
                           SUM(r.PaidAmount) AS paid_amount,
                           SUM(r.RemainingAmount) AS remaining_amount,
                           COUNT(*) AS count
                    FROM Receivable r
                    INNER JOIN Merchant m ON r.MerchantID = m.MerchantID
                    WHERE r.IsActive = 1 {merchant_filter}
                    GROUP BY m.MerchantName
                    ORDER BY remaining_amount DESC
                """, params)
                rows = cursor.fetchall()
                return [{'merchant_name': row.MerchantName, 'count': row.count,
                         'total_amount': float(row.total_amount or 0),
                         'paid_amount': float(row.paid_amount or 0),
                         'remaining_amount': float(row.remaining_amount or 0)} for row in rows]
            else:
                cursor.execute(f"""
                    SELECT COUNT(*) AS total_count,
                           SUM(r.Amount) AS total_amount,
                           SUM(r.PaidAmount) AS paid_amount,
                           SUM(r.RemainingAmount) AS remaining_amount
                    FROM Receivable r
                    WHERE r.IsActive = 1 {merchant_filter}
                """, params)
                row = cursor.fetchone()
                return {'total_count': row.total_count,
                        'total_amount': float(row.total_amount or 0),
                        'paid_amount': float(row.paid_amount or 0),
                        'remaining_amount': float(row.remaining_amount or 0)}
    return executor


def _make_overdue_receivables_executor(receivable_svc):
    def executor(_merchant_id=None, _source='admin'):
        from utils.database import DBConnection
        with DBConnection() as conn:
            cursor = conn.cursor()
            merchant_filter = ''
            params = []
            if _source == 'wx' and _merchant_id:
                merchant_filter = "AND r.MerchantID = ?"
                params = [_merchant_id]
            cursor.execute(f"""
                SELECT TOP 500 r.ReceivableID, m.MerchantName, r.Amount, r.PaidAmount,
                       r.RemainingAmount, r.DueDate, r.Status,
                       sd.DictName AS expense_type_name
                FROM Receivable r
                INNER JOIN Merchant m ON r.MerchantID = m.MerchantID
                LEFT JOIN Sys_Dictionary sd ON r.ExpenseTypeID = sd.DictID
                WHERE r.IsActive = 1
                  AND r.DueDate < CAST(GETDATE() AS DATE)
                  AND r.Status IN (N'未付款', N'部分付款')
                  AND r.RemainingAmount > 0
                  {merchant_filter}
                ORDER BY r.DueDate
            """, params)
            rows = cursor.fetchall()
            return [{'receivable_id': row.ReceivableID, 'merchant_name': row.MerchantName,
                     'amount': float(row.Amount or 0), 'paid_amount': float(row.PaidAmount or 0),
                     'remaining_amount': float(row.RemainingAmount or 0),
                     'due_date': row.DueDate.strftime('%Y-%m-%d') if row.DueDate else '',
                     'status': row.Status, 'expense_type': row.expense_type_name} for row in rows]
    return executor
```

- [ ] **步骤 2：注册应付工具**

```python
def _register_payable_tools(reg, finance_svc):
    reg.register('query_payables', {
        "type": "function",
        "function": {
            "name": "query_payables",
            "description": "查询应付账款列表，支持按供应商、状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "供应商名关键词"},
                    "status": {"type": "string", "enum": ["未付款", "部分付款", "已付款", "all"], "description": "付款状态"}
                },
                "required": []
            }
        }
    }, _make_payables_executor(finance_svc))

    reg.register('query_payable_summary', {
        "type": "function",
        "function": {
            "name": "query_payable_summary",
            "description": "查询应付账款汇总，按供应商分组或总览",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by_vendor": {"type": "boolean", "description": "是否按供应商分组汇总"}
                },
                "required": []
            }
        }
    }, _make_payable_summary_executor(finance_svc))

    reg.register('query_overdue_payables', {
        "type": "function",
        "function": {
            "name": "query_overdue_payables",
            "description": "查询逾期未付的应付账款（超过到期日仍未付清）",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }, _make_overdue_payables_executor(finance_svc))


def _make_payables_executor(finance_svc):
    def executor(search=None, status=None, _merchant_id=None, _source='admin'):
        result = finance_svc.get_payables(page=1, per_page=500, search=search, status=status)
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_payable_summary_executor(finance_svc):
    def executor(group_by_vendor=False, _merchant_id=None, _source='admin'):
        from utils.database import DBConnection
        with DBConnection() as conn:
            cursor = conn.cursor()
            if group_by_vendor:
                cursor.execute("""
                    SELECT VendorName,
                           SUM(Amount) AS total_amount,
                           SUM(PaidAmount) AS paid_amount,
                           SUM(RemainingAmount) AS remaining_amount,
                           COUNT(*) AS count
                    FROM Payable
                    WHERE IsActive = 1 AND VendorName IS NOT NULL
                    GROUP BY VendorName
                    ORDER BY remaining_amount DESC
                """)
                rows = cursor.fetchall()
                return [{'vendor_name': row.VendorName, 'count': row.count,
                         'total_amount': float(row.total_amount or 0),
                         'paid_amount': float(row.paid_amount or 0),
                         'remaining_amount': float(row.remaining_amount or 0)} for row in rows]
            else:
                cursor.execute("""
                    SELECT COUNT(*) AS total_count,
                           SUM(Amount) AS total_amount,
                           SUM(PaidAmount) AS paid_amount,
                           SUM(RemainingAmount) AS remaining_amount
                    FROM Payable
                    WHERE IsActive = 1
                """)
                row = cursor.fetchone()
                return {'total_count': row.total_count,
                        'total_amount': float(row.total_amount or 0),
                        'paid_amount': float(row.paid_amount or 0),
                        'remaining_amount': float(row.remaining_amount or 0)}
    return executor


def _make_overdue_payables_executor(finance_svc):
    def executor(_merchant_id=None, _source='admin'):
        from utils.database import DBConnection
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 500 PayableID, VendorName, Amount, PaidAmount,
                       RemainingAmount, DueDate, Status
                FROM Payable
                WHERE IsActive = 1
                  AND DueDate < CAST(GETDATE() AS DATE)
                  AND Status IN (N'未付款', N'部分付款')
                  AND RemainingAmount > 0
                ORDER BY DueDate
            """)
            rows = cursor.fetchall()
            return [{'payable_id': row.PayableID, 'vendor_name': row.VendorName,
                     'amount': float(row.Amount or 0), 'paid_amount': float(row.PaidAmount or 0),
                     'remaining_amount': float(row.RemainingAmount or 0),
                     'due_date': row.DueDate.strftime('%Y-%m-%d') if row.DueDate else '',
                     'status': row.Status} for row in rows]
    return executor
```

- [ ] **步骤 3：验证工具总数**

运行：
```bash
python -c "from app.services.agent_tools import get_registry; r = get_registry(); schemas = r.get_all_schemas(); print(f'Tools: {len(schemas)}'); [print(s['function']['name']) for s in schemas]"
```
预期：输出 "Tools: 18"

---

### 任务 6：财务流水 + 账户 + 预收预付 + 押金 + 收付款工具（10 个）

**文件：**
- 修改：`app/services/agent_tools.py`

- [ ] **步骤 1：注册现金流工具 + 账户工具 + 预收预付工具 + 押金工具 + 收付款记录工具**

```python
def _register_cashflow_tools(reg, finance_svc):
    reg.register('query_cash_flows', {
        "type": "function",
        "function": {
            "name": "query_cash_flows",
            "description": "查询现金流水记录，支持按方向（收入/支出）、期间、费用类型筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["收入", "支出", "all"], "description": "流水方向"},
                    "start_date": {"type": "string", "description": "开始日期 yyyy-MM-dd"},
                    "end_date": {"type": "string", "description": "结束日期 yyyy-MM-dd"}
                },
                "required": []
            }
        }
    }, _make_cashflows_executor(finance_svc))

    reg.register('query_cash_flow_summary', {
        "type": "function",
        "function": {
            "name": "query_cash_flow_summary",
            "description": "查询现金流汇总统计，按费用类型分组汇总收入/支出",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "开始日期"},
                    "end_date": {"type": "string", "description": "结束日期"}
                },
                "required": []
            }
        }
    }, _make_cashflow_summary_executor(finance_svc))


def _make_cashflows_executor(finance_svc):
    def executor(direction=None, start_date=None, end_date=None,
                  _merchant_id=None, _source='admin'):
        result = finance_svc.get_cash_flows(
            page=1, per_page=500, direction=direction if direction and direction != 'all' else None,
            start_date=start_date, end_date=end_date
        )
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_cashflow_summary_executor(finance_svc):
    def executor(start_date=None, end_date=None, _merchant_id=None, _source='admin'):
        return finance_svc.get_cash_flow_summary(start_date=start_date, end_date=end_date)
    return executor


def _register_account_tools(reg, account_svc):
    reg.register('query_accounts', {
        "type": "function",
        "function": {
            "name": "query_accounts",
            "description": "查询资金账户列表，返回所有账户信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "账户状态筛选"}
                },
                "required": []
            }
        }
    }, _make_accounts_executor(account_svc))

    reg.register('query_account_balance', {
        "type": "function",
        "function": {
            "name": "query_account_balance",
            "description": "查询所有账户的余额汇总",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }, _make_account_balance_executor(account_svc))


def _make_accounts_executor(account_svc):
    def executor(status=None, _merchant_id=None, _source='admin'):
        result = account_svc.get_accounts(status=status)
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_account_balance_executor(account_svc):
    def executor(_merchant_id=None, _source='admin'):
        return account_svc.get_balance_summary()
    return executor


def _register_prepayment_tools(reg, prepayment_svc):
    reg.register('query_prepayments', {
        "type": "function",
        "function": {
            "name": "query_prepayments",
            "description": "查询预收/预付款列表，按方向和状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["预收", "预付", "all"], "description": "预收或预付"},
                    "status": {"type": "string", "enum": ["有效", "已核销", "已关闭", "all"], "description": "状态"}
                },
                "required": []
            }
        }
    }, _make_prepayments_executor(prepayment_svc))

    reg.register('query_prepayment_summary', {
        "type": "function",
        "function": {
            "name": "query_prepayment_summary",
            "description": "查询预收/预付汇总：总金额、已核销、剩余金额",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["预收", "预付", "all"], "description": "方向筛选"}
                },
                "required": []
            }
        }
    }, _make_prepayment_summary_executor(prepayment_svc))


def _make_prepayments_executor(prepayment_svc):
    def executor(direction=None, status=None, _merchant_id=None, _source='admin'):
        result = prepayment_svc.get_prepayments(
            page=1, per_page=500,
            direction=direction if direction and direction != 'all' else None,
            status=status if status and status != 'all' else None
        )
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_prepayment_summary_executor(prepayment_svc):
    def executor(direction=None, _merchant_id=None, _source='admin'):
        return prepayment_svc.get_summary(direction=direction if direction and direction != 'all' else None)
    return executor


def _register_deposit_tools(reg, deposit_svc):
    reg.register('query_deposits', {
        "type": "function",
        "function": {
            "name": "query_deposits",
            "description": "查询押金列表，按押金类型和状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "deposit_type": {"type": "string", "enum": ["合同押金", "水电押金", "其他"], "description": "押金类型"},
                    "status": {"type": "string", "enum": ["有效", "已退还", "已扣除", "已转抵"], "description": "押金状态"}
                },
                "required": []
            }
        }
    }, _make_deposits_executor(deposit_svc))

    reg.register('query_deposit_summary', {
        "type": "function",
        "function": {
            "name": "query_deposit_summary",
            "description": "查询押金汇总：总收取金额、已退还、已扣除、剩余金额",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }, _make_deposit_summary_executor(deposit_svc))


def _make_deposits_executor(deposit_svc):
    def executor(deposit_type=None, status=None, _merchant_id=None, _source='admin'):
        result = deposit_svc.get_deposits(page=1, per_page=500, deposit_type=deposit_type, status=status)
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_deposit_summary_executor(deposit_svc):
    def executor(_merchant_id=None, _source='admin'):
        return deposit_svc.get_summary()
    return executor


def _register_collection_payment_tools(reg, finance_svc):
    reg.register('query_collection_records', {
        "type": "function",
        "function": {
            "name": "query_collection_records",
            "description": "查询收款记录列表，按期间、支付方式、商户筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "商户名或备注关键词"},
                    "start_date": {"type": "string", "description": "开始日期"},
                    "end_date": {"type": "string", "description": "结束日期"}
                },
                "required": []
            }
        }
    }, _make_collection_records_executor(finance_svc))

    reg.register('query_payment_records', {
        "type": "function",
        "function": {
            "name": "query_payment_records",
            "description": "查询付款记录列表，按期间、供应商筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "供应商名关键词"},
                    "start_date": {"type": "string", "description": "开始日期"},
                    "end_date": {"type": "string", "description": "结束日期"}
                },
                "required": []
            }
        }
    }, _make_payment_records_executor(finance_svc))


def _make_collection_records_executor(finance_svc):
    def executor(search=None, start_date=None, end_date=None,
                  _merchant_id=None, _source='admin'):
        result = finance_svc.get_collection_records(
            page=1, per_page=500, search=search,
            start_date=start_date, end_date=end_date
        )
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_payment_records_executor(finance_svc):
    def executor(search=None, start_date=None, end_date=None,
                  _merchant_id=None, _source='admin'):
        result = finance_svc.get_payment_records_list(
            page=1, per_page=500, search=search,
            start_date=start_date, end_date=end_date
        )
        return result.get('items', []) if isinstance(result, dict) else result
    return executor
```

- [ ] **步骤 2：验证**

运行：
```bash
python -c "from app.services.agent_tools import get_registry; r = get_registry(); print(f'Tools: {len(r.get_all_schemas())}')"
```
预期：输出 "Tools: 28"

---

### 任务 7：水电表工具 + 磅秤工具（7 个）

**文件：**
- 修改：`app/services/agent_tools.py`

- [ ] **步骤 1：注册水电工具（4 个）+ 磅秤工具（3 个）**

```python
def _register_utility_tools(reg, utility_svc):
    reg.register('query_meters', {
        "type": "function",
        "function": {
            "name": "query_meters",
            "description": "查询电表/水表列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "meter_type": {"type": "string", "enum": ["electricity", "water", "all"], "description": "表类型"}
                },
                "required": []
            }
        }
    }, _make_meters_executor(utility_svc))

    reg.register('query_meter_readings', {
        "type": "function",
        "function": {
            "name": "query_meter_readings",
            "description": "查询抄表记录，按类型、月份、商户筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "meter_type": {"type": "string", "enum": ["electricity", "water", "all"], "description": "表类型"},
                    "belong_month": {"type": "string", "description": "月份，如 2026-05"}
                },
                "required": []
            }
        }
    }, _make_meter_readings_executor(utility_svc))

    reg.register('query_electricity_stats', {
        "type": "function",
        "function": {
            "name": "query_electricity_stats",
            "description": "电费统计，按月份/商户汇总电费金额",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by_month": {"type": "boolean", "description": "是否按月份汇总"}
                },
                "required": []
            }
        }
    }, _make_electricity_stats_executor(utility_svc))

    reg.register('query_water_stats', {
        "type": "function",
        "function": {
            "name": "query_water_stats",
            "description": "水费统计，按月份/商户汇总水费金额",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by_month": {"type": "boolean", "description": "是否按月份汇总"}
                },
                "required": []
            }
        }
    }, _make_water_stats_executor(utility_svc))


def _make_meters_executor(utility_svc):
    def executor(meter_type='all', _merchant_id=None, _source='admin'):
        result = utility_svc.get_meter_list_paginated(meter_type=meter_type, page_size=500)
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_meter_readings_executor(utility_svc):
    def executor(meter_type=None, belong_month=None, _merchant_id=None, _source='admin'):
        result = utility_svc.get_reading_data(belong_month=belong_month, meter_type=meter_type)
        return result
    return executor


def _make_electricity_stats_executor(utility_svc):
    def executor(group_by_month=False, _merchant_id=None, _source='admin'):
        from utils.database import DBConnection
        with DBConnection() as conn:
            cursor = conn.cursor()
            if group_by_month:
                cursor.execute("""
                    SELECT ur.ReadingMonth,
                           SUM(ur.Amount) AS total_amount,
                           COUNT(DISTINCT ur.ContractMeterID) AS meter_count
                    FROM UtilityReading ur
                    INNER JOIN ContractElectricityMeter cem ON ur.ContractMeterID = cem.ContractMeterID
                    GROUP BY ur.ReadingMonth
                    ORDER BY ur.ReadingMonth DESC
                """)
                rows = cursor.fetchall()
                return [{'month': row.ReadingMonth, 'total_amount': float(row.total_amount or 0),
                         'meter_count': row.meter_count} for row in rows]
            else:
                cursor.execute("""
                    SELECT m.MerchantName, SUM(ur.Amount) AS total_amount, MAX(ur.ReadingMonth) AS last_month
                    FROM UtilityReading ur
                    INNER JOIN ContractElectricityMeter cem ON ur.ContractMeterID = cem.ContractMeterID
                    INNER JOIN Contract c ON cem.ContractID = c.ContractID
                    INNER JOIN Merchant m ON c.MerchantID = m.MerchantID
                    WHERE cem.IsActive = 1
                    GROUP BY m.MerchantName
                    ORDER BY total_amount DESC
                """)
                rows = cursor.fetchall()
                return [{'merchant_name': row.MerchantName, 'total_amount': float(row.total_amount or 0),
                         'last_month': row.last_month} for row in rows]
    return executor


def _make_water_stats_executor(utility_svc):
    def executor(group_by_month=False, _merchant_id=None, _source='admin'):
        from utils.database import DBConnection
        with DBConnection() as conn:
            cursor = conn.cursor()
            if group_by_month:
                cursor.execute("""
                    SELECT ur.ReadingMonth,
                           SUM(ur.Amount) AS total_amount,
                           COUNT(DISTINCT ur.ContractMeterID) AS meter_count
                    FROM UtilityReading ur
                    INNER JOIN ContractWaterMeter cwm ON ur.ContractMeterID = cwm.ContractMeterID
                    GROUP BY ur.ReadingMonth
                    ORDER BY ur.ReadingMonth DESC
                """)
                rows = cursor.fetchall()
                return [{'month': row.ReadingMonth, 'total_amount': float(row.total_amount or 0),
                         'meter_count': row.meter_count} for row in rows]
            else:
                cursor.execute("""
                    SELECT m.MerchantName, SUM(ur.Amount) AS total_amount, MAX(ur.ReadingMonth) AS last_month
                    FROM UtilityReading ur
                    INNER JOIN ContractWaterMeter cwm ON ur.ContractMeterID = cwm.ContractMeterID
                    INNER JOIN Contract c ON cwm.ContractID = c.ContractID
                    INNER JOIN Merchant m ON c.MerchantID = m.MerchantID
                    WHERE cwm.IsActive = 1
                    GROUP BY m.MerchantName
                    ORDER BY total_amount DESC
                """)
                rows = cursor.fetchall()
                return [{'merchant_name': row.MerchantName, 'total_amount': float(row.total_amount or 0),
                         'last_month': row.last_month} for row in rows]
    return executor


def _register_scale_tools(reg, scale_svc):
    reg.register('query_scales', {
        "type": "function",
        "function": {
            "name": "query_scales",
            "description": "查询磅秤列表",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }, _make_scales_executor(scale_svc))

    reg.register('query_scale_records', {
        "type": "function",
        "function": {
            "name": "query_scale_records",
            "description": "查询过磅记录列表，按日期、产品、车牌筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "产品名称或车牌号关键词"},
                    "start_date": {"type": "string", "description": "开始日期"},
                    "end_date": {"type": "string", "description": "结束日期"}
                },
                "required": []
            }
        }
    }, _make_scale_records_executor(scale_svc))

    reg.register('query_scale_stats', {
        "type": "function",
        "function": {
            "name": "query_scale_stats",
            "description": "过磅统计概览：今日/本月/年度过磅次数及收入汇总",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }, _make_scale_stats_executor(scale_svc))


def _make_scales_executor(scale_svc):
    def executor(_merchant_id=None, _source='admin'):
        return scale_svc.get_scale_list()
    return executor


def _make_scale_records_executor(scale_svc):
    def executor(keyword=None, start_date=None, end_date=None,
                  _merchant_id=None, _source='admin'):
        result = scale_svc.get_scale_records(
            page=1, per_page=500, keyword=keyword,
            start_date=start_date, end_date=end_date
        )
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_scale_stats_executor(scale_svc):
    def executor(_merchant_id=None, _source='admin'):
        return scale_svc.get_dashboard_overview()
    return executor
```

- [ ] **步骤 2：验证工具总数**

运行：
```bash
python -c "from app.services.agent_tools import get_registry; r = get_registry(); print(f'Tools: {len(r.get_all_schemas())}')"
```
预期：输出 "Tools: 35"

---

### 任务 8：宿舍工具 + 垃圾工具（6 个）

**文件：**
- 修改：`app/services/agent_tools.py`

- [ ] **步骤 1：注册宿舍工具 + 垃圾工具**

```python
def _register_dorm_tools(reg, dorm_svc):
    reg.register('query_dorm_rooms', {
        "type": "function",
        "function": {
            "name": "query_dorm_rooms",
            "description": "查询宿舍房间列表，按房型和状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["空闲", "已住", "维修中"], "description": "房间状态"},
                    "room_type": {"type": "string", "enum": ["单间", "标间", "套间"], "description": "房间类型"},
                    "search": {"type": "string", "description": "房间号关键词"}
                },
                "required": []
            }
        }
    }, _make_dorm_rooms_executor(dorm_svc))

    reg.register('query_dorm_bills', {
        "type": "function",
        "function": {
            "name": "query_dorm_bills",
            "description": "查询宿舍月度账单，按月份、状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "year_month": {"type": "string", "description": "月份，如 2026-05"},
                    "status": {"type": "string", "description": "账单状态：待确认/已确认/已开账/已收清"}
                },
                "required": []
            }
        }
    }, _make_dorm_bills_executor(dorm_svc))

    reg.register('query_dorm_occupancy', {
        "type": "function",
        "function": {
            "name": "query_dorm_occupancy",
            "description": "查询宿舍入住记录，按状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["在住", "已退房", "all"], "description": "入住状态"}
                },
                "required": []
            }
        }
    }, _make_dorm_occupancy_executor(dorm_svc))


def _make_dorm_rooms_executor(dorm_svc):
    def executor(status=None, room_type=None, search=None, _merchant_id=None, _source='admin'):
        result = dorm_svc.get_rooms(page=1, per_page=500, search=search, status=status, room_type=room_type)
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_dorm_bills_executor(dorm_svc):
    def executor(year_month=None, status=None, _merchant_id=None, _source='admin'):
        result = dorm_svc.get_bills(page=1, per_page=500, year_month=year_month, status=status)
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_dorm_occupancy_executor(dorm_svc):
    def executor(status=None, _merchant_id=None, _source='admin'):
        result = dorm_svc.get_occupancies(page=1, per_page=500, status=status if status and status != 'all' else None)
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _register_garbage_tools(reg, garbage_svc):
    reg.register('query_garbage_collections', {
        "type": "function",
        "function": {
            "name": "query_garbage_collections",
            "description": "查询垃圾清运记录列表，按日期范围和垃圾类型筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "开始日期"},
                    "date_to": {"type": "string", "description": "结束日期"}
                },
                "required": []
            }
        }
    }, _make_garbage_collections_executor(garbage_svc))

    reg.register('query_garbage_fees', {
        "type": "function",
        "function": {
            "name": "query_garbage_fees",
            "description": "查询商户垃圾费收取记录，按年份、商户筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "年份"}
                },
                "required": []
            }
        }
    }, _make_garbage_fees_executor())


def _make_garbage_collections_executor(garbage_svc):
    def executor(date_from=None, date_to=None, _merchant_id=None, _source='admin'):
        result = garbage_svc.get_collections(page=1, per_page=500, date_from=date_from, date_to=date_to)
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_garbage_fees_executor():
    def executor(year=None, _merchant_id=None, _source='admin'):
        from utils.database import DBConnection
        year_filter = ''
        params = []
        if year:
            year_filter = "AND gf.Year = ?"
            params = [year]
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT TOP 500 gf.GarbageFeeID, m.MerchantName, gf.Year,
                       gf.BusinessType, gf.Area, gf.FeeAmount
                FROM GarbageFee gf
                INNER JOIN Merchant m ON gf.MerchantID = m.MerchantID
                WHERE 1=1 {year_filter}
                ORDER BY gf.Year DESC, gf.FeeAmount DESC
            """, params)
            rows = cursor.fetchall()
            return [{'garbage_fee_id': row.GarbageFeeID, 'merchant_name': row.MerchantName,
                     'year': row.Year, 'business_type': row.BusinessType,
                     'area': float(row.Area or 0), 'fee_amount': float(row.FeeAmount or 0)} for row in rows]
    return executor
```

- [ ] **步骤 2：验证**

运行：
```bash
python -c "from app.services.agent_tools import get_registry; r = get_registry(); print(f'Tools: {len(r.get_all_schemas())}')"
```
预期：输出 "Tools: 41"

---

### 任务 9：工资工具 + 费用单工具 + 客户工具（8 个）

**文件：**
- 修改：`app/services/agent_tools.py`

- [ ] **步骤 1：全部注册**

```python
def _register_salary_tools(reg, salary_svc):
    reg.register('query_salary_records', {
        "type": "function",
        "function": {
            "name": "query_salary_records",
            "description": "查询工资记录列表，按月份、员工名、状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "year_month": {"type": "string", "description": "月份，如 2026-05"},
                    "search": {"type": "string", "description": "员工名关键词"},
                    "status": {"type": "string", "enum": ["待审核", "已审核", "已发放"], "description": "工资状态"}
                },
                "required": []
            }
        }
    }, _make_salary_records_executor(salary_svc))

    reg.register('query_salary_stats', {
        "type": "function",
        "function": {
            "name": "query_salary_stats",
            "description": "工资统计，返回某月的汇总数据（总人数、应发合计、实发合计）",
            "parameters": {
                "type": "object",
                "properties": {
                    "year_month": {"type": "string", "description": "月份，如 2026-05"}
                },
                "required": ["year_month"]
            }
        }
    }, _make_salary_stats_executor(salary_svc))


def _make_salary_records_executor(salary_svc):
    def executor(year_month=None, search=None, status=None, _merchant_id=None, _source='admin'):
        result = salary_svc.get_salary_records(
            page=1, per_page=500, year_month=year_month, search=search, status=status
        )
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_salary_stats_executor(salary_svc):
    def executor(year_month, _merchant_id=None, _source='admin'):
        return salary_svc.get_monthly_summary(year_month)
    return executor


def _register_expense_tools(reg, expense_svc):
    reg.register('query_expense_orders', {
        "type": "function",
        "function": {
            "name": "query_expense_orders",
            "description": "查询费用单列表，按类别和期间筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "费用类别"},
                    "search": {"type": "string", "description": "供应商名关键词"},
                    "date_from": {"type": "string", "description": "开始日期"},
                    "date_to": {"type": "string", "description": "结束日期"}
                },
                "required": []
            }
        }
    }, _make_expense_orders_executor(expense_svc))

    reg.register('query_expense_item_summary', {
        "type": "function",
        "function": {
            "name": "query_expense_item_summary",
            "description": "费用单按类型汇总统计",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "开始日期"},
                    "date_to": {"type": "string", "description": "结束日期"}
                },
                "required": []
            }
        }
    }, _make_expense_summary_executor(expense_svc))


def _make_expense_orders_executor(expense_svc):
    def executor(category=None, search=None, date_from=None, date_to=None,
                  _merchant_id=None, _source='admin'):
        result = expense_svc.get_orders(
            page=1, per_page=500, search=search, category=category,
            date_from=date_from, date_to=date_to
        )
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_expense_summary_executor(expense_svc):
    def executor(date_from=None, date_to=None, _merchant_id=None, _source='admin'):
        return expense_svc.get_summary(date_from=date_from, date_to=date_to)
    return executor


def _register_customer_tools(reg, customer_svc, finance_svc):
    reg.register('query_customers', {
        "type": "function",
        "function": {
            "name": "query_customers",
            "description": "查询往来客户（供应商/服务商等非商户单位）列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "客户名关键词"}
                },
                "required": []
            }
        }
    }, _make_customers_executor(customer_svc))

    reg.register('query_customer_transactions', {
        "type": "function",
        "function": {
            "name": "query_customer_transactions",
            "description": "查询某往来客户的完整交易历史，包括应收/应付/预收预付/押金/流水",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer", "description": "客户ID"},
                    "customer_type": {"type": "string", "description": "客户类型：Customer"}
                },
                "required": ["customer_id"]
            }
        }
    }, _make_customer_transactions_executor(finance_svc))


def _make_customers_executor(customer_svc):
    def executor(search=None, _merchant_id=None, _source='admin'):
        result = customer_svc.get_customers(page=1, per_page=500, search=search)
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_customer_transactions_executor(finance_svc):
    def executor(customer_id, customer_type='Customer', _merchant_id=None, _source='admin'):
        return finance_svc.get_customer_transactions(
            customer_type=customer_type, customer_id=customer_id
        )
    return executor
```

- [ ] **步骤 2：验证全部工具已注册**

运行：
```bash
python -c "from app.services.agent_tools import get_registry; r = get_registry(); schemas = r.get_all_schemas(); print(f'Total tools registered: {len(schemas)}')"
```
预期：输出 "Total tools registered: 46"

---

### 任务 10：重写 AgentService.chat() 为 Function Calling 流程

**文件：**
- 修改：`app/services/agent_service.py`

- [ ] **步骤 1：移除旧依赖，改为 Function Calling 导入**

将文件开头（第 1-9 行）替换为：

```python
import json
import logging
from datetime import datetime
from openai import OpenAI
from flask import current_app
from utils.database import DBConnection
from app.services.agent_prompt_builder import build_system_prompt
from app.services.agent_tools import get_registry

logger = logging.getLogger(__name__)
```

移除：`import re`、`from app.services.agent_sql_validator import validate_sql`

- [ ] **步骤 2：重写类文档和 chat() 方法**

将第 13-112 行（类定义注释 + chat 方法 + _retry_sql_fix）替换为：

```python
class AgentService:
    """AI 数据查询助手服务。

    流程：用户提问 → LLM (含 tools) → tool_calls → 并行执行工具 → 结果喂回 LLM → 自然语言回答
    """

    def __init__(self):
        self._client = None
        self._client_config = None

    def chat(self, user_id, conversation_id, message, source='admin', merchant_id=None, merchant_name=None):
        if not conversation_id:
            conversation_id = self._create_conversation(user_id, message, source)

        self._save_message(conversation_id, 'user', message)

        history = self._load_history(conversation_id)
        system_prompt = build_system_prompt(source, merchant_id, merchant_name)

        messages = [{'role': 'system', 'content': system_prompt}]
        for msg in history:
            messages.append({'role': msg['role'], 'content': msg['content']})

        registry = get_registry()
        tools = registry.get_all_schemas()

        injected_kwargs = {'_merchant_id': merchant_id, '_source': source}

        final_content, tool_call_detail = self._chat_with_tools(
            messages, tools, registry, injected_kwargs
        )

        self._save_message(conversation_id, 'assistant', final_content,
                           generated_sql=json.dumps(tool_call_detail, ensure_ascii=False) if tool_call_detail else None)

        return {
            'conversation_id': conversation_id,
            'content': final_content,
            'tool_calls': tool_call_detail,
            'generated_sql': None,
            'query_result': None
        }

    def _chat_with_tools(self, messages, tools, registry, injected_kwargs):
        """两轮 LLM 调用：第一轮可能返回 tool_calls，第二轮生成自然语言回答。
        
        Returns:
            (final_content, tool_call_detail): 最终回答文本 + 工具调用详情（用于调试）
        """
        max_iterations = 3
        tool_call_detail = []

        for iteration in range(max_iterations):
            response = self._call_llm_with_tools(messages, tools)

            if response is None:
                return 'AI 服务暂时不可用，请稍后重试。', tool_call_detail

            finish_reason = response.get('finish_reason')
            content = response.get('content') or ''

            if finish_reason == 'tool_calls' and response.get('tool_calls'):
                tool_calls = response['tool_calls']
                assistant_tool_msg = {
                    'role': 'assistant',
                    'content': content or None,
                    'tool_calls': tool_calls
                }
                messages.append(assistant_tool_msg)

                for tc in tool_calls:
                    fn_name = tc['function']['name']
                    try:
                        fn_args = json.loads(tc['function']['arguments'])
                    except json.JSONDecodeError:
                        fn_args = {}
                    fn_args.update(injected_kwargs)

                    try:
                        result = registry.execute(fn_name, **fn_args)
                    except Exception as e:
                        logger.error(f'Tool {fn_name} execution failed: {e}', exc_info=True)
                        result = f'执行出错：{str(e)}'

                    result_str = json.dumps(result, ensure_ascii=False, default=str) if not isinstance(result, str) else result
                    messages.append({
                        'role': 'tool',
                        'tool_call_id': tc['id'],
                        'content': result_str[:8000]
                    })

                    tool_call_detail.append({
                        'id': tc['id'],
                        'name': fn_name,
                        'arguments': fn_args,
                        'result_preview': result_str[:500]
                    })

                continue

            return content, tool_call_detail

        return '抱歉，查询过程遇到问题，请换个方式描述您的问题。', tool_call_detail
```

- [ ] **步骤 3：重写 _call_llm() → _call_llm_with_tools()**

将第 279-298 行（`_call_llm` 方法）替换为：

```python
    def _call_llm_with_tools(self, messages, tools):
        api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
        model = current_app.config.get('DEEPSEEK_MODEL', 'deepseek-v4-pro')

        if not api_key:
            return {'content': 'AI 助手未配置，请联系管理员设置 DEEPSEEK_API_KEY。', 'finish_reason': 'stop', 'tool_calls': None}

        try:
            client = self._get_client()

            all_tools = [t for t in tools]
            tools_param = None
            if all_tools:
                tools_param = [{'type': 'function', 'function': t['function']} for t in all_tools]

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,
                max_tokens=2000,
                tools=tools_param,
                tool_choice='auto' if tools_param else None
            )

            choice = response.choices[0]
            msg = choice.message

            tool_calls = None
            if msg.tool_calls:
                tool_calls = []
                for tc in msg.tool_calls:
                    tool_calls.append({
                        'id': tc.id,
                        'type': 'function',
                        'function': {
                            'name': tc.function.name,
                            'arguments': tc.function.arguments
                        }
                    })

            return {
                'content': msg.content,
                'finish_reason': choice.finish_reason,
                'tool_calls': tool_calls
            }
        except Exception as e:
            logger.error(f'DeepSeek API 调用失败: {e}', exc_info=True)
            return None
```

- [ ] **步骤 4：删除不再需要的方法**

删除以下整个方法体（保留但清空为 pass，或者整个删除）：
- `_extract_sql()` — 第 300-303 行 → 整段删除
- `_execute_sql()` — 第 305-335 行 → 整段删除
- `_format_query_result()` — 第 337-356 行 → 整段删除

- [ ] **步骤 5：保持 CRUD 方法不变**

以下方法保持完全不变（不修改）：
- `get_conversations()` — 第 158-177 行
- `get_history()` — 第 179-207 行
- `create_conversation()` — 第 209-210 行
- `delete_conversation()` — 第 212-225 行
- `_create_conversation()` — 第 227-237 行
- `_save_message()` — 第 239-251 行
- `_load_history()` — 第 253-264 行
- `_get_client()` — 第 266-276 行

---

### 任务 11：简化 agent_prompt_builder.py

**文件：**
- 修改：`app/services/agent_prompt_builder.py`

- [ ] **步骤 1：整个文件重写为简洁的角色 Prompt**

将整个文件内容替换为：

```python
def build_system_prompt(source='admin', merchant_id=None, merchant_name=None):
    prompt = """你是宏发金属交易市场的数据查询助手。你可以调用工具函数查询业务数据，然后用自然语言回答用户的问题。

## 回答规范
- 金额使用 ¥ 符号，保留两位小数
- 日期使用 yyyy年MM月dd日 格式
- 回答简洁明了，先给总体结论再给明细数据
- 如果工具返回空数据，如实告知用户"""
    
    if source == 'wx' and merchant_id is not None:
        prompt += f"""

## 权限约束
当前用户是商户「{merchant_name}」（ID: {merchant_id}）的工作人员。
你只能查询本商户的数据，不能查看其他商户的信息。
如果用户问其他商户的数据，告知没有权限。"""
    
    return prompt
```

- [ ] **步骤 2：验证 prompt_builder 可导入**

运行：
```bash
python -c "from app.services.agent_prompt_builder import build_system_prompt; p = build_system_prompt('admin'); print(len(p)); assert len(p) > 100; print('OK')"
```
预期：输出 "OK"

---

### 任务 12：清理 agent_sql_validator.py 引用

**文件：**
- 不修改：`app/services/agent_sql_validator.py`（保留不删，作为历史参考）
- 修改：`app/services/agent_service.py`（已在任务 10 中移除 import）

- [ ] **步骤 1：确认 agent_service.py 中不存在 validate_sql 或 agent_sql_validator 的 import**

运行：
```bash
python -c "
import sys
sys.path.insert(0, 'd:/BaiduSyncdisk/HF_metalmarket')
from app.services.agent_service import AgentService
print('AgentService imported successfully without sql_validator')
"
```
预期：无报错，输出 "AgentService imported successfully without sql_validator"

- [ ] **步骤 2：确认 agent_service.py 中没有残留引用**

搜索 `agent_service.py` 中是否包含 `validate_sql` 或 `agent_sql_validator`。

运行：
```bash
python -c "
with open('d:/BaiduSyncdisk/HF_metalmarket/app/services/agent_service.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'validate_sql' in content or 'agent_sql_validator' in content:
        print('WARNING: Stale references found!')
    else:
        print('Clean: no stale references')
"
```
预期：输出 "Clean: no stale references"

---

### 任务 13：集成验证

- [ ] **步骤 1：启动 Flask 应用确认无导入错误**

运行：
```bash
cd d:/BaiduSyncdisk/HF_metalmarket && python -c "from app import create_app; app = create_app(); print('App created successfully')"
```
预期：输出 "App created successfully"，无 ImportError

- [ ] **步骤 2：验证工具总数完整**

运行：
```bash
python -c "
from app.services.agent_tools import get_registry
r = get_registry()
schemas = r.get_all_schemas()
names = [s['function']['name'] for s in schemas]
print(f'Total tools: {len(names)}')
assert len(names) >= 46, f'Expected >= 46 tools, got {len(names)}'
# 检查关键工具
expected = ['query_today', 'query_contracts', 'query_payable_summary', 'query_salary_stats']
for name in expected:
    assert name in names, f'Missing tool: {name}'
print('All expected tools present')
"
```
预期：输出工具总数 >= 49 且 "All expected tools present"

- [ ] **步骤 3：启动开发服务器确认 UI 可访问**

运行：
```bash
cd d:/BaiduSyncdisk/HF_metalmarket && python app.py
```

打开浏览器访问：
- `http://localhost:5000/agent/chat` — 确认 AI 助手页面能加载
- `http://localhost:5000/agent/wx/chat` — 确认微信端页面能加载

- [ ] **步骤 4：端到端测试 — 后台提问**

在 AI 助手页面发送消息："当前有多少份生效的合同？"
预期：Agent 调用 `query_contracts(status='生效')` → DeepSeek 总结回答 "当前共有 X 份生效的合同..."

- [ ] **步骤 5：端到端测试 — 财务查询**

发送："本月应付账款汇总"
预期：Agent 调用 `query_payable_summary(group_by_vendor=false)` → DeepSeek 总结回答 "本月应付账款共 X 笔..."

- [ ] **步骤 6：确认回答中不出现 SQL 代码块**

发送任意数据查询，预期回答中不出现 `\`\`\`sql` 代码块，只包含自然语言和格式化数据。

- [ ] **步骤 7：Commit**

```bash
git add app/services/agent_tools.py app/services/agent_service.py app/services/agent_prompt_builder.py
git commit -m "feat: Agent v2 Function Calling 重构 — 用 ~50 个业务工具替代 Text-to-SQL"
```

---

## 自检

### 1. 规格覆盖度

逐章对照规格文档 `2026-05-03-ai-agent-v2-function-calling.md`：

| 规格章节 | 对应任务 | 状态 |
|---------|---------|------|
| AgentToolRegistry 设计 | 任务 1 | ✓ |
| 通用工具 (3) | 任务 2 | ✓ |
| 字典工具 (1) | 任务 2 | ✓ |
| 商户工具 (2) | 任务 3 | ✓ |
| 合同工具 (4) | 任务 3 | ✓ |
| 地块工具 (2) | 任务 4 | ✓ |
| 财务-应收 (3) | 任务 5 | ✓ |
| 财务-应付 (3) | 任务 5 | ✓ |
| 财务-流水 (2) | 任务 6 | ✓ |
| 财务-账户 (2) | 任务 6 | ✓ |
| 财务-预收预付 (2) | 任务 6 | ✓ |
| 财务-押金 (2) | 任务 6 | ✓ |
| 财务-收付款记录 (2) | 任务 6 | ✓ |
| 水电 (4) | 任务 7 | ✓ |
| 磅秤 (3) | 任务 7 | ✓ |
| 宿舍 (3) | 任务 8 | ✓ |
| 垃圾 (2) | 任务 8 | ✓ |
| 工资 (2) | 任务 9 | ✓ |
| 费用单 (2) | 任务 9 | ✓ |
| 客户 (2) | 任务 9 | ✓ |
| AgentService 核心流程 | 任务 10 | ✓ |
| System Prompt 简化 | 任务 11 | ✓ |
| 废弃 sql_validator | 任务 12 | ✓ |
| 商户端权限控制 | 所有 executor 函数 | ✓ |

**遗漏：** 无

### 2. 占位符扫描

搜索 `待定`、`TODO`、`后续实现`、`补充细节`、`类似任务`：
- 无占位符

搜索 `添加错误处理`、`添加验证`、`处理边界情况`（无具体代码的描述）：
- 每个 executor 都有具体实现代码

### 3. 类型一致性

检查 executor 签名中的参数名：
- 所有 executor 接受 `_merchant_id` 和 `_source` 隐式参数 ✓
- registry.execute() 接受 `**kwargs` → 传递给 executor ✓
- controller 层传入 `injected_kwargs = {'_merchant_id': ..., '_source': ...}` → 通过 `fn_args.update(injected_kwargs)` 注入 ✓
- `query_today` executor 的签名是 `(_merchant_id=None, _source='admin')` → 匹配 ✓

检查 front-end response 格式：
- 当前返回格式：`{conversation_id, content, tool_calls, generated_sql, query_result}`（任务 10）→ routes 用 `success_response(result)` 返回 → 前端已有代码使用 `result.content` ✓

---

## 执行交接

**计划已完成并保存到 `docs/superpowers/plans/2026-05-03-ai-agent-v2-function-calling.md`。两种执行方式：**

**1. 子代理驱动（推荐）** - 每个任务调度一个新的子代理，任务间进行审查，快速迭代

**2. 内联执行** - 在当前会话中使用 executing-plans 执行任务，批量执行并设有检查点

**选哪种方式？**
