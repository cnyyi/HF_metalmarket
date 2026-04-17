# -*- coding: utf-8 -*-
"""端到端测试：费用单模块"""
import os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

env_path = os.path.join(PROJECT_ROOT, '.env')
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

from app import create_app
app = create_app()
with app.app_context():
    from app.services.expense_service import ExpenseService
    from app.services.dict_service import DictService
    svc = ExpenseService()

    # 测试1: 获取支出费用项
    items = DictService.get_expense_items('expense_item_expend')
    print(f'支出费用项({len(items)}个): {[(i["dict_id"], i["dict_name"]) for i in items]}')

    # 测试2: 获取费用大类
    cat_items, cat_total, _ = DictService.get_dict_list(dict_type='expense_category', per_page=100)
    print(f'费用大类({cat_total}个): {[(i["dict_id"], i["dict_name"]) for i in cat_items]}')

    # 测试3: 创建费用单
    first_expense_id = items[0]['dict_id']
    result = svc.create_order(
        expense_category='垃圾清运',
        vendor_name='测试清运公司',
        order_date='2026-04-16',
        description='测试费用单',
        created_by=1,
        items=[
            {'expense_type_id': first_expense_id, 'item_description': '4月垃圾运费', 'amount': 2000.00, 'worker_name': '', 'work_date': ''},
            {'expense_type_id': first_expense_id, 'item_description': '4月垃圾处置费', 'amount': 1000.00, 'worker_name': '', 'work_date': ''},
        ]
    )
    print(f'创建结果: {result}')

    # 测试4: 查看列表
    orders = svc.get_orders()
    print(f'费用单数量: {orders["total"]}')
    if orders['items']:
        first = orders['items'][0]
        print(f'第一笔: {first["order_no"]} / {first["expense_category"]} / {first["vendor_name"]} / {first["total_amount"]}元')

        # 测试5: 查看详情
        detail = svc.get_order_detail(first['order_id'])
        print(f'详情 - 明细行数: {len(detail["items"])}')
        for item in detail['items']:
            print(f'  明细: {item["item_description"]} / {item["amount"]}元 / PayableID={item.get("payable_id")} / status={item.get("payable_status")}')

    # 测试6: 汇总
    summary = svc.get_summary()
    print(f'汇总金额: {summary}元')

    print('\n=== E2E Test Passed ===')
