import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()
import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=" + os.getenv('DB_SERVER') + ";"
    "DATABASE=" + os.getenv('DB_DATABASE') + ";"
    "UID=" + os.getenv('DB_UID') + ";"
    "PWD=" + os.getenv('DB_PWD')
)
conn = pyodbc.connect(conn_str)
cur = conn.cursor()

# 找所有用户相关的表
cur.execute("""
    SELECT TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE='BASE TABLE'
      AND (TABLE_NAME LIKE '%User%' OR TABLE_NAME LIKE '%user%')
""")
print("用户相关表:")
for row in cur.fetchall():
    print("  ", row.TABLE_NAME)

# 查 User 表列
cur.execute("""
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME='User'
    ORDER BY ORDINAL_POSITION
""")
print("\nUser 表字段:")
for row in cur.fetchall():
    print("  " + str(row.COLUMN_NAME) + " (" + str(row.DATA_TYPE) + ")")

# 看其他路由怎么用 current_user 的
conn.close()
