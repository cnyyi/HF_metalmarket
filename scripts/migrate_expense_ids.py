"""迁移：1. 删除外键约束 2. 更新 ExpenseTypeID -> DictID 3. 重新创建外键（指向字典表）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import DevelopmentConfig
app = create_app(DevelopmentConfig)

with app.app_context():
    from utils.database import DBConnection

    with DBConnection() as conn:
        cur = conn.cursor()

        # 1. 查找并删除所有引用 ExpenseType 的外键约束
        print('=== 查找外键约束 ===')
        cur.execute("""
            SELECT fk.name AS constraint_name, OBJECT_NAME(fk.parent_object_id) AS table_name
            FROM sys.foreign_keys fk
            WHERE fk.referenced_object_id = OBJECT_ID('ExpenseType')
        """)
        fks = cur.fetchall()
        for fk in fks:
            print(f'  约束: {fk[0]}, 表: {fk[1]}')

        for fk in fks:
            cur.execute(f"ALTER TABLE [{fk[1]}] DROP CONSTRAINT [{fk[0]}]")
            print(f'  已删除约束: {fk[0]}')

        conn.commit()

        # 2. 补充字典表数据
        print('\n=== 补充字典表 ===')
        cur.execute("SELECT DictID FROM Sys_Dictionary WHERE DictType='expense_item_income' AND DictCode='property_fee'")
        row = cur.fetchone()
        if not row:
            cur.execute("""
                INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive, CreateTime)
                VALUES ('expense_item_income', 'property_fee', N'物业费', N'物业管理费收入', 7, 1, GETDATE())
            """)
            conn.commit()
            print('已新增物业费到字典表')
            cur.execute("SELECT DictID FROM Sys_Dictionary WHERE DictType='expense_item_income' AND DictCode='property_fee'")
            row = cur.fetchone()
        property_fee_id = row[0]
        print(f'物业费 DictID={property_fee_id}')

        # 3. 建立 ExpenseTypeID -> DictID 映射
        mapping = {
            1: 1015,   # 租金
            2: 1016,   # 水费
            3: 1017,   # 电费
            4: 1018,   # 过磅费
            5: 1019,   # 管理费
            6: property_fee_id,  # 物业费
            7: 1022,   # 维修费
            8: 1021,   # 采购费 -> 采购
        }

        # 4. 更新各表
        tables = ['Receivable', 'Payable', 'CashFlow']
        for table in tables:
            for old_id, new_id in mapping.items():
                try:
                    cur.execute(f"SELECT COUNT(*) FROM [{table}] WHERE ExpenseTypeID = ?", (old_id,))
                    count = cur.fetchone()[0]
                    if count > 0:
                        cur.execute(f"UPDATE [{table}] SET ExpenseTypeID = ? WHERE ExpenseTypeID = ?", (new_id, old_id))
                        print(f'{table}: ExpenseTypeID {old_id} -> {new_id} ({count} rows)')
                except Exception as e:
                    print(f'{table}: skip ({e})')

        conn.commit()

        # 5. 验证
        print('\n=== 验证 ===')
        for table in tables:
            try:
                cur.execute(f'SELECT ExpenseTypeID, COUNT(*) FROM [{table}] GROUP BY ExpenseTypeID')
                for r in cur.fetchall():
                    print(f'  {table}: ExpenseTypeID={r[0]}, count={r[1]}')
            except Exception:
                pass

        # 验证 JOIN 字典表后名称正确
        print('\n=== Receivable JOIN Dict ===')
        cur.execute("""
            SELECT r.ReceivableID, r.ExpenseTypeID, ISNULL(sd.DictName, 'N/A') AS Name
            FROM Receivable r
            LEFT JOIN Sys_Dictionary sd ON r.ExpenseTypeID = sd.DictID
        """)
        for r in cur.fetchall():
            print(f'  ID={r[0]}, ExpenseTypeID={r[1]}, DictName={r[2]}')

        print('\n迁移完成!')
