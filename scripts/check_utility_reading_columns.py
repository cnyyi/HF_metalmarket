import os
import pyodbc

conn = pyodbc.connect(
    os.environ.get(
        'ODBC_CONNECTION_STRING',
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=localhost;'
        'DATABASE=hf_metalmarket;'
        'UID=sa;'
        'PWD=;'
        'Encrypt=no;'
        'TrustServerCertificate=yes;'
    )
)
cursor = conn.cursor()
rows = cursor.execute("""
    SELECT COLUMN_NAME, IS_NULLABLE, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'UtilityReading' 
    ORDER BY ORDINAL_POSITION
""").fetchall()
for r in rows:
    print(f'{r[0]:25s} | nullable={r[1]:3s} | type={r[2]:10s} | max_len={r[3]}')
conn.close()
