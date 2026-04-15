"""检查当前数据库中 ExpenseType 和 Sys_Dictionary 费用项的对应关系"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import DevelopmentConfig
app = create_app(DevelopmentConfig)

with app.app_context():
    from utils.database import DBConnection

    with DBConnection() as conn:
        cur = conn.cursor()

        # 1. 查看 ExpenseType 表现有数据
        print('=== ExpenseType 表 ===')
        cur.execute('SELECT ExpenseTypeID, ExpenseTypeName, ExpenseDirection, ExpenseTypeCode FROM ExpenseType WHERE IsActive=1 ORDER BY ExpenseTypeID')
        expense_types = cur.fetchall()
        for r in expense_types:
            print(f'  ID={r[0]}, Name={r[1]}, Dir={r[2]}, Code={r[3]}')

        # 2. 查看字典表费用项
        print('\n=== Sys_Dictionary 费用项 ===')
        cur.execute("""
            SELECT DictID, DictCode, DictName, DictType
            FROM Sys_Dictionary
            WHERE DictType IN ('expense_item_income', 'expense_item_expend')
            ORDER BY DictType, SortOrder
        """)
        dict_items = cur.fetchall()
        for r in dict_items:
            print(f'  DictID={r[0]}, Code={r[1]}, Name={r[2]}, Type={r[3]}')

        # 3. 查看 Payable 表中有多少条用了 ExpenseTypeID
        print('\n=== Payable 表 ExpenseTypeID 使用情况 ===')
        cur.execute('SELECT COUNT(*), COUNT(DISTINCT ExpenseTypeID) FROM Payable')
        row = cur.fetchone()
        print(f'  总记录数={row[0]}, 使用的不同ExpenseTypeID数={row[1]}')

        cur.execute('SELECT DISTINCT ExpenseTypeID FROM Payable')
        ids = [r[0] for r in cur.fetchall()]
        if ids:
            print(f'  已使用的 ExpenseTypeID: {ids}')

        # 4. 查看 Receivable 表
        print('\n=== Receivable 表 ExpenseTypeID 使用情况 ===')
        cur.execute('SELECT COUNT(*), COUNT(DISTINCT ExpenseTypeID) FROM Receivable')
        row = cur.fetchone()
        print(f'  总记录数={row[0]}, 使用的不同ExpenseTypeID数={row[1]}')

        cur.execute('SELECT DISTINCT ExpenseTypeID FROM Receivable')
        ids = [r[0] for r in cur.fetchall()]
        if ids:
            print(f'  已使用的 ExpenseTypeID: {ids}')

        # 5. 查看 CashFlow 表
        print('\n=== CashFlow 表 ExpenseTypeID 使用情况 ===')
        cur.execute('SELECT COUNT(*), COUNT(DISTINCT ExpenseTypeID) FROM CashFlow')
        row = cur.fetchone()
        print(f'  总记录数={row[0]}, 使用的不同ExpenseTypeID数={row[1]}')
