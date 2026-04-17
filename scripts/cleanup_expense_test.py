# -*- coding: utf-8 -*-
"""清理测试数据"""
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
    from utils.database import DBConnection
    with DBConnection() as conn:
        cursor = conn.cursor()
        # 删除测试生成的 Payable
        cursor.execute("DELETE FROM Payable WHERE ReferenceType = N'expense_order'")
        r1 = cursor.rowcount
        # 删除明细行
        cursor.execute("DELETE FROM ExpenseOrderItem")
        r2 = cursor.rowcount
        # 删除费用单
        cursor.execute("DELETE FROM ExpenseOrder")
        r3 = cursor.rowcount
        conn.commit()
        print(f'Cleaned up: {r1} Payable, {r2} ExpenseOrderItem, {r3} ExpenseOrder')
