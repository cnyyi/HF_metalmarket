# -*- coding: utf-8 -*-
"""迁移脚本：Receivable 表增加品名/规格/数量/单位/单价字段 + 字典表增加 unit_type"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyodbc
from dotenv import load_dotenv
load_dotenv()

def get_conn():
    conn_str = os.getenv('ODBC_CONNECTION_STRING', '')
    if not conn_str:
        server = os.getenv('DB_SERVER', '')
        db = os.getenv('DB_DATABASE', '')
        uid = os.getenv('DB_UID', '')
        pwd = os.getenv('DB_PWD', '')
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}'
    return pyodbc.connect(conn_str, autocommit=True)

def main():
    conn = get_conn()
    cursor = conn.cursor()

    # 1. Add columns to Receivable
    cols = [
        ('ProductName', 'NVARCHAR(200) NULL'),
        ('Specification', 'NVARCHAR(200) NULL'),
        ('Quantity', 'DECIMAL(18,4) NULL'),
        ('UnitID', 'INT NULL'),
        ('UnitPrice', 'DECIMAL(18,4) NULL'),
    ]
    for col_name, col_type in cols:
        cursor.execute(
            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='Receivable' AND COLUMN_NAME=?",
            (col_name,)
        )
        if cursor.fetchone()[0] == 0:
            cursor.execute(f'ALTER TABLE Receivable ADD {col_name} {col_type}')
            print(f'Added column: {col_name}')
        else:
            print(f'Column already exists: {col_name}')

    # 2. Add dictionary entries for unit_type
    units = [('kg', 'Kg', 1), ('ton', '吨', 2), ('vehicle', '车', 3), ('bottle', '瓶', 4)]
    for code, name, sort in units:
        cursor.execute(
            "SELECT COUNT(*) FROM Sys_Dictionary WHERE DictType='unit_type' AND DictCode=?",
            (code,)
        )
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive) VALUES ('unit_type', ?, ?, ?, 1)",
                (code, name, sort)
            )
            print(f'Added dict: unit_type/{code} = {name}')
        else:
            print(f'Dict already exists: unit_type/{code}')

    conn.close()
    print('Migration done!')

if __name__ == '__main__':
    main()
