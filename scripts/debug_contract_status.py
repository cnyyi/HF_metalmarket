"""查看合同状态的实际值（hex方式）"""
import sys
sys.path.insert(0, '.')
from app import create_app
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)
with app.app_context():
    from utils.database import DBConnection
    with DBConnection() as conn:
        cursor = conn.cursor()
        
        # 查看合同状态原始值
        cursor.execute("SELECT ContractID, Status, CAST(Status AS VARBINARY(100)) FROM Contract")
        for r in cursor.fetchall():
            print(f"  ID={r[0]} Status='{r[1]}' hex={r[2]}")
        
        # 同时看看字典定义
        print("\n=== contract_status 字典 ===")
        cursor.execute("SELECT DictID, DictCode, DictName, CAST(DictName AS VARBINARY(100)) FROM Sys_Dictionary WHERE DictType='contract_status'")
        for r in cursor.fetchall():
            print(f"  ID={r[0]} Code={r[1]} Name='{r[2]}' hex={r[3]}")

        # 查看应收状态是否还有 '已付清'
        print("\n=== Receivable 所有不同Status ===")
        cursor.execute("SELECT Status, COUNT(*) FROM Receivable GROUP BY Status")
        for r in cursor.fetchall():
            print(f"  Status='{r[0]}' count={r[1]}")
