import pyodbc

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=yyi.myds.me;'
    'DATABASE=hf_metalmarket;'
    'UID=sa;'
    'PWD=yyI.123212;'
    'Encrypt=no;'
    'TrustServerCertificate=yes;'
)
cursor = conn.cursor()

# 1. Plot 总量统计
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        ISNULL(SUM(CASE WHEN Status = N'已出租' THEN 1 ELSE 0 END), 0) as rented,
        ISNULL(SUM(CASE WHEN Status != N'已出租' OR Status IS NULL THEN 1 ELSE 0 END), 0) as available
    FROM Plot
""")
r = cursor.fetchone()
print(f"Plot: total={r[0]}, rented={r[1]}, available={r[2]}")

# 2. Plot 前5条
cursor.execute("SELECT TOP 5 PlotID, PlotNumber, Status, Area, PlotType FROM Plot")
rows = cursor.fetchall()
for row in rows:
    print(f"  PlotID={row[0]}, PlotNumber={row[1]}, Status={row[2]}, Area={row[3]}, PlotType={row[4]}")

# 3. Merchant Status 统计
cursor.execute("""
    SELECT Status, COUNT(*) as cnt FROM Merchant GROUP BY Status
""")
rows = cursor.fetchall()
print("\nMerchant Status:")
for row in rows:
    print(f"  Status='{row[0]}' (hex={row[0].encode('utf-8').hex() if row[0] else 'NULL'}), count={row[1]}")

# 4. Plot Status 统计
cursor.execute("""
    SELECT ISNULL(Status, 'NULL') as Status, COUNT(*) as cnt FROM Plot GROUP BY Status
""")
rows = cursor.fetchall()
print("\nPlot Status:")
for row in rows:
    status = row[0] if row[0] != 'NULL' else None
    hex_str = status.encode('utf-8').hex() if status else 'NULL'
    print(f"  Status='{status}' (hex={hex_str}), count={row[1]}")

# 5. Receivable 统计
cursor.execute("""
    SELECT Status, COUNT(*), SUM(Amount) FROM Receivable GROUP BY Status
""")
rows = cursor.fetchall()
print("\nReceivable Status:")
for row in rows:
    print(f"  Status='{row[0]}', count={row[1]}, sum={row[2]}")

# 6. Merchant count
cursor.execute("SELECT COUNT(*) FROM Merchant WHERE Status = N'正常'")
r = cursor.fetchone()
print(f"\nActive merchants (Status=正常): {r[0]}")

conn.close()
