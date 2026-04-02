# -*- coding: utf-8 -*-
"""
检查FileAttachment表是否存在
"""
import pyodbc

ODBC_CONNECTION_STRING = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=yyi.myds.me;' 
    'DATABASE=hf_metalmarket;' 
    'UID=sa;' 
    'PWD=yyI.123212;' 
    'Encrypt=no;' 
    'TrustServerCertificate=yes;' 
    'charset=utf-8;'
)

try:
    conn = pyodbc.connect(ODBC_CONNECTION_STRING)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = 'FileAttachment'
    """)
    
    count = cursor.fetchone()[0]
    
    if count > 0:
        print("FileAttachment表存在")
        
        cursor.execute("SELECT COUNT(*) FROM FileAttachment")
        row_count = cursor.fetchone()[0]
        print(f"表中有 {row_count} 条记录")
        
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'FileAttachment'
            ORDER BY ORDINAL_POSITION
        """)
        
        print("\n表结构:")
        for row in cursor.fetchall():
            print(f"  {row.COLUMN_NAME}: {row.DATA_TYPE}({row.CHARACTER_MAXIMUM_LENGTH}), Nullable={row.IS_NULLABLE}")
    else:
        print("FileAttachment表不存在，需要创建")
    
    conn.close()
    
except Exception as e:
    print(f"错误: {e}")
