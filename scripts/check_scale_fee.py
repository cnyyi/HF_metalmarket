import os
for line in open('.env', encoding='utf-8'):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        os.environ[k] = v

import pyodbc
from datetime import datetime

conn_str = os.environ.get('ODBC_CONNECTION_STRING', 
    f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={os.environ['DB_SERVER']};DATABASE={os.environ['DB_DATABASE']};UID={os.environ['DB_UID']};PWD={os.environ['DB_PWD']}")
conn = pyodbc.connect(conn_str)
cur = conn.cursor()
today = datetime.now().strftime('%Y-%m-%d')

# ScaleTime filter
cur.execute("""
    SELECT COUNT(*), ISNULL(SUM(NetWeight), 0), ISNULL(SUM(ScaleFee), 0)
    FROM ScaleRecord
    WHERE CAST(ScaleTime AS DATE) = ?
""", (today,))
row = cur.fetchone()
print(f'ScaleTime filter: count={row[0]}, weight={row[1]}, fee={row[2]}')

# Show today's records with details
cur.execute("""
    SELECT ScaleRecordID, ScaleTime, NetWeight, ScaleFee, LicensePlate
    FROM ScaleRecord
    WHERE CAST(ScaleTime AS DATE) = ?
    ORDER BY ScaleTime DESC
""", (today,))
rows = cur.fetchall()
for r in rows:
    print(f'  ID={r[0]}, ScaleTime={r[1]}, Net={r[2]}, Fee={r[3]}, Plate={r[4]}')

conn.close()
