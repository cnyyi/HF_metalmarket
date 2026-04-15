"""迁移费用类型数据到字典表"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)

with app.app_context():
    from utils.database import DBConnection

    with DBConnection() as conn:
        cursor = conn.cursor()

        # 检查是否已有数据
        cursor.execute("SELECT COUNT(*) FROM Sys_Dictionary WHERE DictType = 'expense_item_income'")
        income_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM Sys_Dictionary WHERE DictType = 'expense_item_expend'")
        expend_count = cursor.fetchone()[0]
        print(f'expense_item_income: {income_count} records')
        print(f'expense_item_expend: {expend_count} records')

        if income_count == 0:
            cursor.execute("""
                INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive, CreateTime)
                VALUES
                ('expense_item_income', 'rent', N'租金', N'地块租金收入', 1, 1, GETDATE()),
                ('expense_item_income', 'water', N'水费', N'自来水费收入', 2, 1, GETDATE()),
                ('expense_item_income', 'electricity', N'电费', N'电力费收入', 3, 1, GETDATE()),
                ('expense_item_income', 'scale_fee', N'过磅费', N'磅秤使用费收入', 4, 1, GETDATE()),
                ('expense_item_income', 'management_fee', N'管理费', N'市场管理费收入', 5, 1, GETDATE()),
                ('expense_item_income', 'other_income', N'其他收入', N'其他收入项', 6, 1, GETDATE())
            """)
            print('Inserted expense_item_income records')

        if expend_count == 0:
            cursor.execute("""
                INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive, CreateTime)
                VALUES
                ('expense_item_expend', 'purchase', N'采购', N'物资采购支出', 1, 1, GETDATE()),
                ('expense_item_expend', 'maintenance', N'维修费', N'设施设备维修支出', 2, 1, GETDATE()),
                ('expense_item_expend', 'salary', N'工资', N'员工工资支出', 3, 1, GETDATE()),
                ('expense_item_expend', 'utility_expend', N'水电费', N'市场水电费支出', 4, 1, GETDATE()),
                ('expense_item_expend', 'tax', N'税费', N'各项税费支出', 5, 1, GETDATE()),
                ('expense_item_expend', 'other_expend', N'其他支出', N'其他支出项', 6, 1, GETDATE())
            """)
            print('Inserted expense_item_expend records')

        conn.commit()

        # 验证
        print('\n--- expense_item_income ---')
        cursor.execute("SELECT DictCode, DictName FROM Sys_Dictionary WHERE DictType = 'expense_item_income' ORDER BY SortOrder")
        for r in cursor.fetchall():
            print(f'  {r[0]}: {r[1]}')

        print('\n--- expense_item_expend ---')
        cursor.execute("SELECT DictCode, DictName FROM Sys_Dictionary WHERE DictType = 'expense_item_expend' ORDER BY SortOrder")
        for r in cursor.fetchall():
            print(f'  {r[0]}: {r[1]}')

        print('\n迁移完成!')
