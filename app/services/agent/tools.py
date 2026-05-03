# -*- coding: utf-8 -*-
import json
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

    _register_common_tools(reg, finance_svc)
    _register_dictionary_tools(reg, dict_svc)
    _register_merchant_tools(reg, merchant_svc)
    _register_overview_tools(reg, merchant_svc)
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


def _register_common_tools(reg, finance_svc):
    reg.register('query_today', {
        "type": "function",
        "function": {
            "name": "query_today",
            "description": u"获取当前日期信息，包括年月日、本月月初日期、当前月份名称",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }, _exec_query_today)

    reg.register('query_finance_summary', {
        "type": "function",
        "function": {
            "name": "query_finance_summary",
            "description": u"查询综合财务汇总数据，包括应收账款总额/已收/未收、应付账款总额/已付/未付、本月收入/支出/结余",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["this_month", "this_year", "all"],
                        "description": u"统计时间范围"
                    }
                },
                "required": []
            }
        }
    }, _make_finance_summary_executor(finance_svc))

    reg.register('query_monthly_trend', {
        "type": "function",
        "function": {
            "name": "query_monthly_trend",
            "description": u"查询月度收支趋势，按月汇总收入/支出金额，用于分析经营走势",
            "parameters": {
                "type": "object",
                "properties": {
                    "months": {
                        "type": "integer",
                        "description": u"查询最近几个月的趋势，默认6个月"
                    }
                },
                "required": []
            }
        }
    }, _make_monthly_trend_executor(finance_svc))


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
        'month_name': f'{now.year}\u5e74{now.month}\u6708',
        'first_day_of_month': first_day.strftime('%Y-%m-%d'),
        'first_day_of_next_month': next_month.strftime('%Y-%m-%d'),
        'current_year': now.year
    }


def _make_finance_summary_executor(finance_svc):
    def executor(period='this_month', _merchant_id=None, _source='admin'):
        return finance_svc.get_finance_summary(
            period=period,
            merchant_id=_merchant_id if _source == 'wx' else None,
            source=_source
        )
    return executor


def _make_monthly_trend_executor(finance_svc):
    def executor(months=6, _merchant_id=None, _source='admin'):
        return finance_svc.get_monthly_trend(
            months=months,
            merchant_id=_merchant_id if _source == 'wx' else None,
            source=_source
        )
    return executor


def _register_dictionary_tools(reg, dict_svc):
    reg.register('query_dictionary', {
        "type": "function",
        "function": {
            "name": "query_dictionary",
            "description": u"查询系统字典表，获取费用类型、商户类型、业态、支付方式等枚举列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "dict_type": {
                        "type": "string",
                        "enum": ["merchant_type", "business_type", "expense_item_income", "expense_item_expend",
                                 "unit_type", "payment_method", "salary_status", "dorm_room_type"],
                        "description": u"字典类型编码"
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


def _register_merchant_tools(reg, merchant_svc):
    reg.register('query_merchants', {
        "type": "function",
        "function": {
            "name": "query_merchants",
            "description": u"查询商户列表，支持按名称搜索、按类型和状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": u"商户名称关键词搜索"},
                    "merchant_type": {"type": "string", "description": u"商户类型"},
                    "status": {"type": "string", "description": u"商户状态"}
                },
                "required": []
            }
        }
    }, _make_merchants_executor(merchant_svc))

    reg.register('query_merchant_detail', {
        "type": "function",
        "function": {
            "name": "query_merchant_detail",
            "description": u"查询单个商户的详细信息，包括基本信息、关联合同数量、应收应付余额",
            "parameters": {
                "type": "object",
                "properties": {
                    "merchant_id": {"type": "integer", "description": u"商户ID"},
                    "merchant_name": {"type": "string", "description": u"商户名称（如果不知道ID可用名称查）"}
                },
                "required": []
            }
        }
    }, _make_merchant_detail_executor(merchant_svc))


def _make_merchants_executor(merchant_svc):
    def executor(search=None, merchant_type=None, status=None, _merchant_id=None, _source='admin'):
        kwargs = {'page': 1, 'per_page': 500, 'search': search}
        result = merchant_svc.get_merchants(**kwargs)
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
        return {'error': u'请提供商户ID或商户名称'}
    return executor


def _register_overview_tools(reg, merchant_svc):
    reg.register('query_merchant_overview', {
        "type": "function",
        "function": {
            "name": "query_merchant_overview",
            "description": u"查询商户的整体经营概况，包括基本信息、合同、应收、预付款、押金、本月水电费等汇总数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "merchant_id": {"type": "integer", "description": u"商户ID"},
                    "merchant_name": {"type": "string", "description": u"商户名称（模糊搜索）"}
                },
                "required": []
            }
        }
    }, _make_merchant_overview_executor(merchant_svc))


def _make_merchant_overview_executor(merchant_svc):
    def executor(merchant_id=None, merchant_name=None, _merchant_id=None, _source='admin'):
        if _source == 'wx' and _merchant_id:
            merchant_id = _merchant_id
        if not merchant_id and merchant_name:
            result = merchant_svc.get_merchants(page=1, per_page=500, search=merchant_name)
            items = result.get('items', []) if isinstance(result, dict) else result
            if items:
                merchant_id = items[0].get('MerchantID') or items[0].get('merchant_id')
        if not merchant_id:
            return {'error': u'请提供商户ID或商户名称'}
        return merchant_svc.get_merchant_overview(
            merchant_id=merchant_id,
            source=_source
        )
    return executor


def _register_contract_tools(reg, contract_svc):
    reg.register('query_contracts', {
        "type": "function",
        "function": {
            "name": "query_contracts",
            "description": u"查询合同列表，支持按商户、状态、关键词筛选。注意：生效合同的Status值为'生效'，不是'执行中'。",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": u"合同号或商户名关键词"},
                    "status": {"type": "string", "description": u"合同状态，如 生效"},
                    "sort_by": {"type": "string", "enum": ["create_time", "end_date", "start_date"], "description": u"排序字段"},
                    "sort_order": {"type": "string", "enum": ["asc", "desc"], "description": u"排序方向"}
                },
                "required": []
            }
        }
    }, _make_contracts_executor(contract_svc))

    reg.register('query_expiring_contracts', {
        "type": "function",
        "function": {
            "name": "query_expiring_contracts",
            "description": u"查询即将到期的合同。支持两种模式：1) 按天数（days参数）查未来N天内到期；2) 按日期范围（start_date/end_date参数）查指定时间段内到期。例如查7月到期的合同，传start_date=2026-07-01, end_date=2026-07-31。",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": u"未来多少天内到期，默认30天。与start_date/end_date二选一"},
                    "start_date": {"type": "string", "description": u"到期日期范围起始，格式yyyy-MM-dd，如2026-07-01"},
                    "end_date": {"type": "string", "description": u"到期日期范围结束，格式yyyy-MM-dd，如2026-07-31"}
                },
                "required": []
            }
        }
    }, _make_expiring_contracts_executor(contract_svc))

    reg.register('query_contract_stats', {
        "type": "function",
        "function": {
            "name": "query_contract_stats",
            "description": u"统计合同数量、金额，按状态分组汇总",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }, _make_contract_stats_executor(contract_svc))

    reg.register('query_contract_detail', {
        "type": "function",
        "function": {
            "name": "query_contract_detail",
            "description": u"查询单个合同的详细信息，包括关联地块、租金明细",
            "parameters": {
                "type": "object",
                "properties": {"contract_id": {"type": "integer", "description": u"合同ID"}},
                "required": ["contract_id"]
            }
        }
    }, _make_contract_detail_executor(contract_svc))


def _make_contracts_executor(contract_svc):
    def executor(search=None, status=None, sort_by='create_time', sort_order='desc',
                  _merchant_id=None, _source='admin'):
        result = contract_svc.get_contract_list(
            page=1, per_page=500, search=search,
            sort_by=sort_by, sort_order=sort_order
        )
        items = result.get('items', []) if isinstance(result, dict) else result
        if status:
            items = [c for c in items if c.get('Status') == status or c.get('status') == status]
        if _source == 'wx' and _merchant_id:
            items = [c for c in items if c.get('MerchantID') == _merchant_id or c.get('merchant_id') == _merchant_id]
        return items[:500]
    return executor


def _make_expiring_contracts_executor(contract_svc):
    def executor(days=None, start_date=None, end_date=None, _merchant_id=None, _source='admin'):
        return contract_svc.get_expiring_contracts(
            days=days,
            start_date=start_date,
            end_date=end_date,
            merchant_id=_merchant_id if _source == 'wx' else None,
            source=_source
        )
    return executor


def _make_contract_stats_executor(contract_svc):
    def executor(_merchant_id=None, _source='admin'):
        return contract_svc.get_contract_stats(
            merchant_id=_merchant_id if _source == 'wx' else None,
            source=_source
        )
    return executor


def _make_contract_detail_executor(contract_svc):
    def executor(contract_id, _merchant_id=None, _source='admin'):
        detail = contract_svc.get_contract_detail(contract_id)
        if _source == 'wx' and _merchant_id:
            if detail and isinstance(detail, dict):
                if detail.get('MerchantID') != _merchant_id and detail.get('merchant_id') != _merchant_id:
                    return u'无权查看该合同'
        return detail
    return executor


def _register_plot_tools(reg, plot_svc):
    reg.register('query_plots', {
        "type": "function",
        "function": {
            "name": "query_plots",
            "description": u"查询地块/铺位列表，支持按类型、状态、出租状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "plot_type": {"type": "string", "description": u"地块类型：水泥/钢材/砖类/其他"},
                    "status": {"type": "string", "description": u"状态：空闲/已出租"},
                    "rent_status": {"type": "string", "description": u"出租状态"},
                    "search": {"type": "string", "description": u"地块编号关键词搜索"}
                },
                "required": []
            }
        }
    }, _make_plots_executor(plot_svc))

    reg.register('query_plot_stats', {
        "type": "function",
        "function": {
            "name": "query_plot_stats",
            "description": u"按类型统计地块的面积、数量和空闲率",
            "parameters": {"type": "object", "properties": {}, "required": []}
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
        return plot_svc.get_plot_stats(source=_source)
    return executor


def _register_receivable_tools(reg, receivable_svc):
    reg.register('query_receivables', {
        "type": "function",
        "function": {
            "name": "query_receivables",
            "description": u"查询应收账款列表，支持按商户、状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": u"商户名关键词"},
                    "status": {"type": "string", "enum": [u"未付款", u"部分付款", u"已付款", "all"],
                              "description": u"付款状态"},
                    "expense_type_id": {"type": "integer", "description": u"费用类型ID"}
                },
                "required": []
            }
        }
    }, _make_receivables_executor(receivable_svc))

    reg.register('query_receivable_summary', {
        "type": "function",
        "function": {
            "name": "query_receivable_summary",
            "description": u"查询应收账款汇总，包括总金额、已收金额、剩余金额，可按商户分组",
            "parameters": {
                "type": "object",
                "properties": {"group_by_merchant": {"type": "boolean", "description": u"是否按商户分组汇总"}},
                "required": []
            }
        }
    }, _make_receivable_summary_executor(receivable_svc))

    reg.register('query_overdue_receivables', {
        "type": "function",
        "function": {
            "name": "query_overdue_receivables",
            "description": u"查询逾期未付的应收账款（超过到期日仍未付清）",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }, _make_overdue_receivables_executor(receivable_svc))


def _make_receivables_executor(receivable_svc):
    def executor(search=None, status=None, expense_type_id=None, _merchant_id=None, _source='admin'):
        kwargs = {'page': 1, 'per_page': 500, 'search': search, 'expense_type_id': expense_type_id}
        if status and status != 'all':
            kwargs['status'] = status
        result = receivable_svc.get_receivables(**kwargs)
        items = result.get('items', []) if isinstance(result, dict) else result
        if _source == 'wx' and _merchant_id:
            items = [r for r in items if r.get('MerchantID') == _merchant_id or r.get('merchant_id') == _merchant_id]
        return items
    return executor


def _make_receivable_summary_executor(receivable_svc):
    def executor(group_by_merchant=False, _merchant_id=None, _source='admin'):
        return receivable_svc.get_receivable_summary(
            group_by_merchant=group_by_merchant,
            merchant_id=_merchant_id if _source == 'wx' else None,
            source=_source
        )
    return executor


def _make_overdue_receivables_executor(receivable_svc):
    def executor(_merchant_id=None, _source='admin'):
        return receivable_svc.get_overdue_receivables(
            merchant_id=_merchant_id if _source == 'wx' else None,
            source=_source
        )
    return executor


def _register_payable_tools(reg, finance_svc):
    reg.register('query_payables', {
        "type": "function",
        "function": {
            "name": "query_payables",
            "description": u"查询应付账款列表，支持按供应商、状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": u"供应商名关键词"},
                    "status": {"type": "string", "enum": [u"未付款", u"部分付款", u"已付款", "all"],
                              "description": u"付款状态"}
                },
                "required": []
            }
        }
    }, _make_payables_executor(finance_svc))

    reg.register('query_payable_summary', {
        "type": "function",
        "function": {
            "name": "query_payable_summary",
            "description": u"查询应付账款汇总，按供应商分组或总览",
            "parameters": {
                "type": "object",
                "properties": {"group_by_vendor": {"type": "boolean", "description": u"是否按供应商分组汇总"}},
                "required": []
            }
        }
    }, _make_payable_summary_executor(finance_svc))

    reg.register('query_overdue_payables', {
        "type": "function",
        "function": {
            "name": "query_overdue_payables",
            "description": u"查询逾期未付的应付账款（超过到期日仍未付清）",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }, _make_overdue_payables_executor(finance_svc))


def _make_payables_executor(finance_svc):
    def executor(search=None, status=None, _merchant_id=None, _source='admin'):
        if _source == 'wx':
            return u'商户无权查看应付账款'
        kwargs = {'page': 1, 'per_page': 500, 'search': search}
        if status and status != 'all':
            kwargs['status'] = status
        result = finance_svc.get_payables(**kwargs)
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_payable_summary_executor(finance_svc):
    def executor(group_by_vendor=False, _merchant_id=None, _source='admin'):
        if _source == 'wx':
            return u'商户无权查看应付账款汇总'
        return finance_svc.get_payable_summary(
            group_by_vendor=group_by_vendor,
            merchant_id=_merchant_id if _source == 'wx' else None,
            source=_source
        )
    return executor


def _make_overdue_payables_executor(finance_svc):
    def executor(_merchant_id=None, _source='admin'):
        if _source == 'wx':
            return u'商户无权查看逾期应付账款'
        return finance_svc.get_overdue_payables(
            merchant_id=_merchant_id if _source == 'wx' else None,
            source=_source
        )
    return executor


def _register_cashflow_tools(reg, finance_svc):
    reg.register('query_cash_flows', {
        "type": "function",
        "function": {
            "name": "query_cash_flows",
            "description": u"查询现金流水记录，支持按方向（收入/支出）、期间筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": [u"收入", u"支出", "all"], "description": u"流水方向"},
                    "start_date": {"type": "string", "description": u"开始日期 yyyy-MM-dd"},
                    "end_date": {"type": "string", "description": u"结束日期 yyyy-MM-dd"}
                },
                "required": []
            }
        }
    }, _make_cashflows_executor(finance_svc))

    reg.register('query_cash_flow_summary', {
        "type": "function",
        "function": {
            "name": "query_cash_flow_summary",
            "description": u"查询现金流汇总统计，按费用类型分组汇总收入/支出",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": u"开始日期"},
                    "end_date": {"type": "string", "description": u"结束日期"}
                },
                "required": []
            }
        }
    }, _make_cashflow_summary_executor(finance_svc))


def _make_cashflows_executor(finance_svc):
    def executor(direction=None, start_date=None, end_date=None, _merchant_id=None, _source='admin'):
        if _source == 'wx':
            return u'商户无权查看收支流水'
        d = direction if direction and direction != 'all' else None
        result = finance_svc.get_cash_flows(
            page=1, per_page=500, direction=d, start_date=start_date, end_date=end_date
        )
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_cashflow_summary_executor(finance_svc):
    def executor(start_date=None, end_date=None, _merchant_id=None, _source='admin'):
        if _source == 'wx':
            return u'商户无权查看收支汇总'
        return finance_svc.get_cash_flow_summary(start_date=start_date, end_date=end_date)
    return executor


def _register_account_tools(reg, account_svc):
    reg.register('query_accounts', {
        "type": "function",
        "function": {
            "name": "query_accounts",
            "description": u"查询资金账户列表，返回所有账户信息",
            "parameters": {
                "type": "object",
                "properties": {"status": {"type": "string", "description": u"账户状态筛选"}},
                "required": []
            }
        }
    }, _make_accounts_executor(account_svc))

    reg.register('query_account_balance', {
        "type": "function",
        "function": {
            "name": "query_account_balance",
            "description": u"查询所有账户的余额汇总",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }, _make_account_balance_executor(account_svc))


def _make_accounts_executor(account_svc):
    def executor(status=None, _merchant_id=None, _source='admin'):
        if _source == 'wx':
            return u'商户无权查看资金账户'
        result = account_svc.get_accounts(status=status)
        return result.get('items', result) if isinstance(result, dict) else result
    return executor


def _make_account_balance_executor(account_svc):
    def executor(_merchant_id=None, _source='admin'):
        if _source == 'wx':
            return u'商户无权查看账户余额'
        return account_svc.get_balance_summary()
    return executor


def _register_prepayment_tools(reg, prepayment_svc):
    reg.register('query_prepayments', {
        "type": "function",
        "function": {
            "name": "query_prepayments",
            "description": u"查询预收/预付款列表，按方向和状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": [u"预收", u"预付", "all"], "description": u"预收或预付"},
                    "status": {"type": "string", "enum": [u"有效", u"已核销", u"已关闭", "all"], "description": u"状态"}
                },
                "required": []
            }
        }
    }, _make_prepayments_executor(prepayment_svc))

    reg.register('query_prepayment_summary', {
        "type": "function",
        "function": {
            "name": "query_prepayment_summary",
            "description": u"查询预收/预付汇总：总金额、已核销、剩余金额",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": [u"预收", u"预付", "all"], "description": u"方向筛选"}
                },
                "required": []
            }
        }
    }, _make_prepayment_summary_executor(prepayment_svc))


def _make_prepayments_executor(prepayment_svc):
    def executor(direction=None, status=None, _merchant_id=None, _source='admin'):
        d = direction if direction and direction != 'all' else None
        s = status if status and status != 'all' else None
        result = prepayment_svc.get_prepayments(page=1, per_page=500, direction=d, status=s)
        items = result.get('items', []) if isinstance(result, dict) else result
        if _source == 'wx' and _merchant_id:
            items = [p for p in items if p.get('MerchantID') == _merchant_id or p.get('merchant_id') == _merchant_id]
        return items
    return executor


def _make_prepayment_summary_executor(prepayment_svc):
    def executor(direction=None, _merchant_id=None, _source='admin'):
        d = direction if direction and direction != 'all' else None
        if _source == 'wx' and _merchant_id:
            return prepayment_svc.get_merchant_prepayment_summary(
                merchant_id=_merchant_id,
                direction=d
            )
        return prepayment_svc.get_summary(direction=d)
    return executor


def _register_deposit_tools(reg, deposit_svc):
    reg.register('query_deposits', {
        "type": "function",
        "function": {
            "name": "query_deposits",
            "description": u"查询押金列表，按押金类型和状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "deposit_type": {"type": "string", "enum": [u"合同押金", u"水电押金", u"其他"], "description": u"押金类型"},
                    "status": {"type": "string", "enum": [u"有效", u"已退还", u"已扣除", u"已转抵"], "description": u"押金状态"}
                },
                "required": []
            }
        }
    }, _make_deposits_executor(deposit_svc))

    reg.register('query_deposit_summary', {
        "type": "function",
        "function": {
            "name": "query_deposit_summary",
            "description": u"查询押金汇总：总收取金额、已退还、已扣除、剩余金额",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }, _make_deposit_summary_executor(deposit_svc))


def _make_deposits_executor(deposit_svc):
    def executor(deposit_type=None, status=None, _merchant_id=None, _source='admin'):
        result = deposit_svc.get_deposits(page=1, per_page=500, deposit_type=deposit_type, status=status)
        items = result.get('items', []) if isinstance(result, dict) else result
        if _source == 'wx' and _merchant_id:
            items = [d for d in items if d.get('MerchantID') == _merchant_id or d.get('merchant_id') == _merchant_id]
        return items
    return executor


def _make_deposit_summary_executor(deposit_svc):
    def executor(_merchant_id=None, _source='admin'):
        if _source == 'wx' and _merchant_id:
            return deposit_svc.get_merchant_deposit_summary(merchant_id=_merchant_id)
        return deposit_svc.get_summary()
    return executor


def _register_collection_payment_tools(reg, finance_svc):
    reg.register('query_collection_records', {
        "type": "function",
        "function": {
            "name": "query_collection_records",
            "description": u"查询收款记录列表，按期间、支付方式、商户筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": u"商户名或备注关键词"},
                    "start_date": {"type": "string", "description": u"开始日期"},
                    "end_date": {"type": "string", "description": u"结束日期"}
                },
                "required": []
            }
        }
    }, _make_collection_records_executor(finance_svc))

    reg.register('query_payment_records', {
        "type": "function",
        "function": {
            "name": "query_payment_records",
            "description": u"查询付款记录列表，按期间、供应商筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": u"供应商名关键词"},
                    "start_date": {"type": "string", "description": u"开始日期"},
                    "end_date": {"type": "string", "description": u"结束日期"}
                },
                "required": []
            }
        }
    }, _make_payment_records_executor(finance_svc))


def _make_collection_records_executor(finance_svc):
    def executor(search=None, start_date=None, end_date=None, _merchant_id=None, _source='admin'):
        result = finance_svc.get_collection_records(
            page=1, per_page=500, search=search, start_date=start_date, end_date=end_date
        )
        items = result.get('items', []) if isinstance(result, dict) else result
        if _source == 'wx' and _merchant_id:
            items = [r for r in items if r.get('MerchantID') == _merchant_id or r.get('merchant_id') == _merchant_id]
        return items
    return executor


def _make_payment_records_executor(finance_svc):
    def executor(search=None, start_date=None, end_date=None, _merchant_id=None, _source='admin'):
        if _source == 'wx':
            return u'商户无权查看付款记录'
        result = finance_svc.get_payment_records_list(
            page=1, per_page=500, search=search, start_date=start_date, end_date=end_date
        )
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _register_utility_tools(reg, utility_svc):
    reg.register('query_meters', {
        "type": "function",
        "function": {
            "name": "query_meters",
            "description": u"查询电表/水表列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "meter_type": {"type": "string", "enum": ["electricity", "water", "all"], "description": u"表类型"}
                },
                "required": []
            }
        }
    }, _make_meters_executor(utility_svc))

    reg.register('query_meter_readings', {
        "type": "function",
        "function": {
            "name": "query_meter_readings",
            "description": u"查询抄表记录，按类型、月份筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "meter_type": {"type": "string", "enum": ["electricity", "water", "all"], "description": u"表类型"},
                    "belong_month": {"type": "string", "description": u"月份，如 2026-05"}
                },
                "required": []
            }
        }
    }, _make_meter_readings_executor(utility_svc))

    reg.register('query_electricity_stats', {
        "type": "function",
        "function": {
            "name": "query_electricity_stats",
            "description": u"电费统计，按月份/商户汇总电费金额",
            "parameters": {
                "type": "object",
                "properties": {"group_by_month": {"type": "boolean", "description": u"是否按月份汇总"}},
                "required": []
            }
        }
    }, _make_electricity_stats_executor(utility_svc))

    reg.register('query_water_stats', {
        "type": "function",
        "function": {
            "name": "query_water_stats",
            "description": u"水费统计，按月份/商户汇总水费金额",
            "parameters": {
                "type": "object",
                "properties": {"group_by_month": {"type": "boolean", "description": u"是否按月份汇总"}},
                "required": []
            }
        }
    }, _make_water_stats_executor(utility_svc))


def _make_meters_executor(utility_svc):
    def executor(meter_type='all', _merchant_id=None, _source='admin'):
        result = utility_svc.get_meter_list_paginated(meter_type=meter_type, page_size=500)
        items = result.get('items', []) if isinstance(result, dict) else result
        if _source == 'wx' and _merchant_id:
            items = [m for m in items if m.get('MerchantID') == _merchant_id or m.get('merchant_id') == _merchant_id]
        return items
    return executor


def _make_meter_readings_executor(utility_svc):
    def executor(meter_type=None, belong_month=None, _merchant_id=None, _source='admin'):
        result = utility_svc.get_reading_data(belong_month=belong_month, meter_type=meter_type)
        if _source == 'wx' and _merchant_id:
            if isinstance(result, dict):
                items = result.get('items', result.get('readings', []))
                items = [r for r in items if r.get('MerchantID') == _merchant_id or r.get('merchant_id') == _merchant_id]
                result['items'] = items
                return result
            elif isinstance(result, list):
                return [r for r in result if r.get('MerchantID') == _merchant_id or r.get('merchant_id') == _merchant_id]
        return result
    return executor


def _make_electricity_stats_executor(utility_svc):
    def executor(group_by_month=False, _merchant_id=None, _source='admin'):
        return utility_svc.get_electricity_stats(
            group_by_month=group_by_month,
            merchant_id=_merchant_id if _source == 'wx' else None,
            source=_source
        )
    return executor


def _make_water_stats_executor(utility_svc):
    def executor(group_by_month=False, _merchant_id=None, _source='admin'):
        return utility_svc.get_water_stats(
            group_by_month=group_by_month,
            merchant_id=_merchant_id if _source == 'wx' else None,
            source=_source
        )
    return executor


def _register_scale_tools(reg, scale_svc):
    reg.register('query_scales', {
        "type": "function",
        "function": {
            "name": "query_scales",
            "description": u"查询磅秤列表",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }, _make_scales_executor(scale_svc))

    reg.register('query_scale_records', {
        "type": "function",
        "function": {
            "name": "query_scale_records",
            "description": u"查询过磅记录列表，按日期、产品、车牌筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": u"产品名称或车牌号关键词"},
                    "start_date": {"type": "string", "description": u"开始日期"},
                    "end_date": {"type": "string", "description": u"结束日期"}
                },
                "required": []
            }
        }
    }, _make_scale_records_executor(scale_svc))

    reg.register('query_scale_stats', {
        "type": "function",
        "function": {
            "name": "query_scale_stats",
            "description": u"过磅统计概览：今日/本月/年度过磅次数及收入汇总",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }, _make_scale_stats_executor(scale_svc))


def _make_scales_executor(scale_svc):
    def executor(_merchant_id=None, _source='admin'):
        return scale_svc.get_scale_list()
    return executor


def _make_scale_records_executor(scale_svc):
    def executor(keyword=None, start_date=None, end_date=None, _merchant_id=None, _source='admin'):
        result = scale_svc.get_scale_records(
            page=1, per_page=500, keyword=keyword, start_date=start_date, end_date=end_date
        )
        items = result.get('items', []) if isinstance(result, dict) else result
        if _source == 'wx' and _merchant_id:
            items = [r for r in items if r.get('MerchantID') == _merchant_id or r.get('merchant_id') == _merchant_id]
        return items
    return executor


def _make_scale_stats_executor(scale_svc):
    def executor(_merchant_id=None, _source='admin'):
        if _source == 'wx':
            return u'商户无权查看过磅统计'
        return scale_svc.get_dashboard_overview()
    return executor


def _register_dorm_tools(reg, dorm_svc):
    reg.register('query_dorm_rooms', {
        "type": "function",
        "function": {
            "name": "query_dorm_rooms",
            "description": u"查询宿舍房间列表，按房型和状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": [u"空闲", u"已住", u"维修中"], "description": u"房间状态"},
                    "room_type": {"type": "string", "enum": [u"单间", u"标间", u"套间"], "description": u"房间类型"},
                    "search": {"type": "string", "description": u"房间号关键词"}
                },
                "required": []
            }
        }
    }, _make_dorm_rooms_executor(dorm_svc))

    reg.register('query_dorm_bills', {
        "type": "function",
        "function": {
            "name": "query_dorm_bills",
            "description": u"查询宿舍月度账单，按月份、状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "year_month": {"type": "string", "description": u"月份，如 2026-05"},
                    "status": {"type": "string", "description": u"账单状态：待确认/已确认/已开账/已收清"}
                },
                "required": []
            }
        }
    }, _make_dorm_bills_executor(dorm_svc))

    reg.register('query_dorm_occupancy', {
        "type": "function",
        "function": {
            "name": "query_dorm_occupancy",
            "description": u"查询宿舍入住记录，按状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": [u"在住", u"已退房", "all"], "description": u"入住状态"}
                },
                "required": []
            }
        }
    }, _make_dorm_occupancy_executor(dorm_svc))


def _make_dorm_rooms_executor(dorm_svc):
    def executor(status=None, room_type=None, search=None, _merchant_id=None, _source='admin'):
        result = dorm_svc.get_rooms(page=1, per_page=500, search=search, status=status, room_type=room_type)
        items = result.get('items', []) if isinstance(result, dict) else result
        if _source == 'wx' and _merchant_id:
            items = [r for r in items if r.get('MerchantID') == _merchant_id or r.get('merchant_id') == _merchant_id]
        return items
    return executor


def _make_dorm_bills_executor(dorm_svc):
    def executor(year_month=None, status=None, _merchant_id=None, _source='admin'):
        result = dorm_svc.get_bills(page=1, per_page=500, year_month=year_month, status=status)
        items = result.get('items', []) if isinstance(result, dict) else result
        if _source == 'wx' and _merchant_id:
            items = [b for b in items if b.get('MerchantID') == _merchant_id or b.get('merchant_id') == _merchant_id]
        return items
    return executor


def _make_dorm_occupancy_executor(dorm_svc):
    def executor(status=None, _merchant_id=None, _source='admin'):
        s = status if status and status != 'all' else None
        result = dorm_svc.get_occupancies(page=1, per_page=500, status=s)
        items = result.get('items', []) if isinstance(result, dict) else result
        if _source == 'wx' and _merchant_id:
            items = [o for o in items if o.get('MerchantID') == _merchant_id or o.get('merchant_id') == _merchant_id]
        return items
    return executor


def _register_garbage_tools(reg, garbage_svc):
    reg.register('query_garbage_collections', {
        "type": "function",
        "function": {
            "name": "query_garbage_collections",
            "description": u"查询垃圾清运记录列表，按日期范围和垃圾类型筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": u"开始日期"},
                    "date_to": {"type": "string", "description": u"结束日期"}
                },
                "required": []
            }
        }
    }, _make_garbage_collections_executor(garbage_svc))

    reg.register('query_garbage_fees', {
        "type": "function",
        "function": {
            "name": "query_garbage_fees",
            "description": u"查询商户垃圾费收取记录，按年份、商户筛选",
            "parameters": {
                "type": "object",
                "properties": {"year": {"type": "integer", "description": u"年份"}},
                "required": []
            }
        }
    }, _make_garbage_fees_executor(garbage_svc))


def _make_garbage_collections_executor(garbage_svc):
    def executor(date_from=None, date_to=None, _merchant_id=None, _source='admin'):
        result = garbage_svc.get_collections(page=1, per_page=500, date_from=date_from, date_to=date_to)
        items = result.get('items', []) if isinstance(result, dict) else result
        if _source == 'wx' and _merchant_id:
            items = [g for g in items if g.get('MerchantID') == _merchant_id or g.get('merchant_id') == _merchant_id]
        return items
    return executor


def _make_garbage_fees_executor(garbage_svc):
    def executor(year=None, _merchant_id=None, _source='admin'):
        return garbage_svc.get_garbage_fees(
            year=year,
            merchant_id=_merchant_id if _source == 'wx' else None,
            source=_source
        )
    return executor


def _register_salary_tools(reg, salary_svc):
    reg.register('query_salary_records', {
        "type": "function",
        "function": {
            "name": "query_salary_records",
            "description": u"查询工资记录列表，按月份、状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "year_month": {"type": "string", "description": u"月份，如 2026-05"},
                    "search": {"type": "string", "description": u"员工名关键词"},
                    "status": {"type": "string", "enum": [u"待审核", u"已审核", u"已发放"], "description": u"工资状态"}
                },
                "required": []
            }
        }
    }, _make_salary_records_executor(salary_svc))

    reg.register('query_salary_stats', {
        "type": "function",
        "function": {
            "name": "query_salary_stats",
            "description": u"工资统计，返回某月的汇总数据（总人数、应发合计、实发合计）",
            "parameters": {
                "type": "object",
                "properties": {"year_month": {"type": "string", "description": u"月份，如 2026-05"}},
                "required": ["year_month"]
            }
        }
    }, _make_salary_stats_executor(salary_svc))


def _make_salary_records_executor(salary_svc):
    def executor(year_month=None, search=None, status=None, _merchant_id=None, _source='admin'):
        if _source == 'wx':
            return u'商户无权查看工资记录'
        result = salary_svc.get_salary_records(
            page=1, per_page=500, year_month=year_month, search=search, status=status
        )
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_salary_stats_executor(salary_svc):
    def executor(year_month, _merchant_id=None, _source='admin'):
        if _source == 'wx':
            return u'商户无权查看工资统计'
        return salary_svc.get_monthly_summary(year_month)
    return executor


def _register_expense_tools(reg, expense_svc):
    reg.register('query_expense_orders', {
        "type": "function",
        "function": {
            "name": "query_expense_orders",
            "description": u"查询费用单列表，按类别和期间筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": u"费用类别"},
                    "search": {"type": "string", "description": u"供应商名关键词"},
                    "date_from": {"type": "string", "description": u"开始日期"},
                    "date_to": {"type": "string", "description": u"结束日期"}
                },
                "required": []
            }
        }
    }, _make_expense_orders_executor(expense_svc))

    reg.register('query_expense_item_summary', {
        "type": "function",
        "function": {
            "name": "query_expense_item_summary",
            "description": u"费用单按类型汇总统计",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": u"开始日期"},
                    "date_to": {"type": "string", "description": u"结束日期"}
                },
                "required": []
            }
        }
    }, _make_expense_summary_executor(expense_svc))


def _make_expense_orders_executor(expense_svc):
    def executor(category=None, search=None, date_from=None, date_to=None,
                  _merchant_id=None, _source='admin'):
        if _source == 'wx':
            return u'商户无权查看费用单'
        result = expense_svc.get_orders(
            page=1, per_page=500, search=search, category=category,
            date_from=date_from, date_to=date_to
        )
        return result.get('items', []) if isinstance(result, dict) else result
    return executor


def _make_expense_summary_executor(expense_svc):
    def executor(date_from=None, date_to=None, _merchant_id=None, _source='admin'):
        if _source == 'wx':
            return u'商户无权查看费用汇总'
        return expense_svc.get_summary(date_from=date_from, date_to=date_to)
    return executor


def _register_customer_tools(reg, customer_svc, finance_svc):
    reg.register('query_customers', {
        "type": "function",
        "function": {
            "name": "query_customers",
            "description": u"查询往来客户（供应商/服务商等非商户单位）列表",
            "parameters": {
                "type": "object",
                "properties": {"search": {"type": "string", "description": u"客户名关键词"}},
                "required": []
            }
        }
    }, _make_customers_executor(customer_svc))

    reg.register('query_customer_transactions', {
        "type": "function",
        "function": {
            "name": "query_customer_transactions",
            "description": u"查询某往来客户的完整交易历史，包括应收/应付/预收预付/押金/流水",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer", "description": u"客户ID"},
                    "customer_type": {"type": "string", "description": u"客户类型：Customer"}
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
        if _source == 'wx' and _merchant_id:
            customer_id = _merchant_id
            customer_type = 'Merchant'
        return finance_svc.get_customer_transactions(customer_type=customer_type, customer_id=customer_id)
    return executor
