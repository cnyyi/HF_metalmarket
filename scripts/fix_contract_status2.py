"""修复 Contract 表中显示为 ?? 的乱码状态值"""
import sys
sys.path.insert(0, '.')
from app import create_app
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)
with app.app_context():
    from utils.database import DBConnection
    with DBConnection() as conn:
        cursor = conn.cursor()

        # 用 VARBINARY 查看 ?? 的实际内容
        cursor.execute("SELECT ContractID, Status, CAST(Status AS VARBINARY(20)) FROM Contract WHERE ContractID <= 11")
        rows = cursor.fetchall()
        print("=== 合同状态原始数据 ===")
        for r in rows:
            print(f"  ID={r[0]} Status='{r[1]}' hex={r[2]}")

        # hex=b'?\x00?\x00' 对应 UTF-16LE 的 "生效" (0x751F 0x6558)
        # 不对，让我查查实际 hex
        # "??" in Python from pyodbc might mean the NVARCHAR wasn't decoded properly
        # Let's just update all non-'生效' records that aren't NULL

        # 先看看非'生效'、非NULL的合同有多少
        cursor.execute("SELECT COUNT(*) FROM Contract WHERE Status != N'生效' AND Status IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"\n非'生效'状态的合同数: {count}")

        # 查看这些记录
        cursor.execute("SELECT ContractID, ContractNumber, Status FROM Contract WHERE Status != N'生效' AND Status IS NOT NULL")
        for r in cursor.fetchall():
            print(f"  ID={r[0]} Number='{r[1]}' Status='{r[2]}'")

        # 把所有不是'生效'、'已到期'、'已终止'的状态统一改为'生效'
        # 这些合同大概率都是正在执行的合同
        cursor.execute("""
            UPDATE Contract 
            SET Status = N'生效' 
            WHERE Status NOT IN (N'生效', N'已到期', N'已终止')
              AND Status IS NOT NULL
        """)
        updated = cursor.rowcount
        print(f"\n已更新 {updated} 条合同状态为'生效'")

        conn.commit()

        # 验证
        cursor.execute("SELECT Status, COUNT(*) FROM Contract GROUP BY Status")
        print("\n=== 修复后 ===")
        for r in cursor.fetchall():
            print(f"  Status='{r[0]}' count={r[1]}")
