"""验证应付/应收/现金流的费用类型API是否正常返回字典表数据"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import DevelopmentConfig
app = create_app(DevelopmentConfig)

with app.app_context():
    from app.services.dict_service import DictService
    from app.services.finance_service import FinanceService
    from app.services.receivable_service import ReceivableService

    # 1. DictService.get_expense_items
    print('=== DictService.get_expense_items ===')
    income = DictService.get_expense_items('expense_item_income')
    print(f'  收入项 ({len(income)} 个):')
    for item in income:
        print(f'    dict_id={item["dict_id"]}, code={item["dict_code"]}, name={item["dict_name"]}')

    expend = DictService.get_expense_items('expense_item_expend')
    print(f'  支出项 ({len(expend)} 个):')
    for item in expend:
        print(f'    dict_id={item["dict_id"]}, code={item["dict_code"]}, name={item["dict_name"]}')

    # 2. Payable 列表查询
    print('\n=== Payable 列表 ===')
    finance_svc = FinanceService()
    result = finance_svc.get_payables(page=1, per_page=5)
    print(f'  共 {result["total_count"]} 条')
    for item in result['items']:
        print(f'  ID={item["payable_id"]}, ExpenseType={item["expense_type_name"]}')

    # 3. Receivable 列表查询
    print('\n=== Receivable 列表 ===')
    receivable_svc = ReceivableService()
    result = receivable_svc.get_receivables(page=1, per_page=5)
    print(f'  共 {result["total_count"]} 条')
    for item in result['items']:
        print(f'  ID={item["receivable_id"]}, ExpenseType={item["expense_type_name"]}')

    print('\n验证完成!')
