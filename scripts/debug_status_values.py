"""查看所有状态值的实际分布"""
import sys
sys.path.insert(0, '.')
from app import create_app
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)
with app.app_context():
    from utils.database import DBConnection
    with DBConnection() as conn:
        cursor = conn.cursor()

        # Receivable 状态
        print("=== Receivable Status ===")
        cursor.execute("SELECT DISTINCT Status FROM Receivable")
        for r in cursor.fetchall():
            # 显示原始字节
            s = r[0]
            print(f"  '{s}' (len={len(s) if s else 0}, bytes={s.encode('utf-8') if s else b''})")
        
        # Payable 状态
        print("\n=== Payable Status ===")
        cursor.execute("SELECT DISTINCT Status FROM Payable")
        for r in cursor.fetchall():
            s = r[0]
            print(f"  '{s}' (len={len(s) if s else 0}, bytes={s.encode('utf-8') if s else b''})")

        # Contract 状态
        print("\n=== Contract Status ===")
        cursor.execute("SELECT DISTINCT Status FROM Contract")
        for r in cursor.fetchall():
            s = r[0]
            print(f"  '{s}' (len={len(s) if s else 0}, bytes={s.encode('utf-8') if s else b''})")

        # 字典表中定义的状态
        print("\n=== Dict: receivable_status ===")
        cursor.execute("SELECT DictCode, DictName FROM Sys_Dictionary WHERE DictType = 'receivable_status' AND IsActive = 1 ORDER BY SortOrder")
        for r in cursor.fetchall():
            print(f"  Code={r[0]} Name='{r[1]}'")

        print("\n=== Dict: payable_status ===")
        cursor.execute("SELECT DictCode, DictName FROM Sys_Dictionary WHERE DictType = 'payable_status' AND IsActive = 1 ORDER BY SortOrder")
        for r in cursor.fetchall():
            print(f"  Code={r[0]} Name='{r[1]}'")

        print("\n=== Dict: contract_status ===")
        cursor.execute("SELECT DictCode, DictName FROM Sys_Dictionary WHERE DictType = 'contract_status' AND IsActive = 1 ORDER BY SortOrder")
        for r in cursor.fetchall():
            print(f"  Code={r[0]} Name='{r[1]}'")
