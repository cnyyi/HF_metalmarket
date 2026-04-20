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

cur.execute("""
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME='[User]'
    ORDER BY ORDINAL_POSITION
""")
print("User 表字段:")
for row in cur.fetchall():
    print("  " + str(row.COLUMN_NAME) + " (" + str(row.DATA_TYPE) + ")")

conn.close()
