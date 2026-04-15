import pyodbc
from config import Config

conn = pyodbc.connect(Config.ODBC_CONNECTION_STRING)
cursor = conn.cursor()

print("=" * 80)
print("检查数据库表结构")
print("=" * 80)

tables = ['WaterMeter', 'ElectricityMeter']

for table in tables:
    print(f"\n{table} 表结构:")
    print("-" * 80)
    cursor.execute(f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table}'
        ORDER BY ORDINAL_POSITION
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"{row.COLUMN_NAME:30} {row.DATA_TYPE:15} 可空: {row.IS_NULLABLE:3} 默认: {row.COLUMN_DEFAULT}")

conn.close()
