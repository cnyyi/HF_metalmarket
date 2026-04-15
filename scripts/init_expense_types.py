import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DevelopmentConfig
from app import create_app

app = create_app(DevelopmentConfig)

with app.app_context():
    from utils.database import DBConnection

    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM ExpenseType')
        count = cursor.fetchone()[0]
        print(f'ExpenseType records: {count}')
        if count == 0:
            cursor.execute("""
                INSERT INTO ExpenseType (ExpenseTypeName, ExpenseTypeCode, ExpenseDirection, Description, IsActive)
                VALUES 
                    (N'租金', N'rent', N'收入', N'地块租金', 1),
                    (N'水费', N'water', N'收入', N'自来水费用', 1),
                    (N'电费', N'electricity', N'收入', N'电力费用', 1),
                    (N'过磅费', N'scale_fee', N'收入', N'磅秤使用费用', 1),
                    (N'管理费', N'management_fee', N'收入', N'市场管理费用', 1),
                    (N'物业费', N'property_fee', N'收入', N'物业服务费用', 1),
                    (N'维修费', N'repair_fee', N'支出', N'设备维修费用', 1),
                    (N'采购费', N'purchase_fee', N'支出', N'物资采购费用', 1)
            """)
            conn.commit()
            print('ExpenseType data inserted successfully')
        else:
            cursor.execute('SELECT ExpenseTypeID, ExpenseTypeName, ExpenseTypeCode, ExpenseDirection FROM ExpenseType')
            rows = cursor.fetchall()
            for r in rows:
                print(f'  ID={r.ExpenseTypeID}, Name={r.ExpenseTypeName}, Code={r.ExpenseTypeCode}, Dir={r.ExpenseDirection}')
