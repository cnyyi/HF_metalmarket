"""诊断首页统计数据问题"""
import sys
sys.path.insert(0, '.')
from app import create_app
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)
with app.app_context():
    from utils.database import DBConnection
    with DBConnection() as conn:
        cursor = conn.cursor()

        # 1. 应收表状态分布
        print("=== Receivable 状态分布 ===")
        cursor.execute("SELECT Status, COUNT(*), SUM(RemainingAmount) FROM Receivable GROUP BY Status")
        for r in cursor.fetchall():
            print(f"  Status='{r[0]}' count={r[1]} remaining={r[2]}")

        # 2. 合同表状态分布
        print("\n=== Contract 状态分布 ===")
        cursor.execute("SELECT Status, COUNT(*) FROM Contract GROUP BY Status")
        for r in cursor.fetchall():
            print(f"  Status='{r[0]}' count={r[1]}")

        # 3. 商户表状态分布
        print("\n=== Merchant 状态分布 ===")
        cursor.execute("SELECT Status, COUNT(*) FROM Merchant GROUP BY Status")
        for r in cursor.fetchall():
            print(f"  Status='{r[0]}' count={r[1]}")

        # 4. 地块表状态分布
        print("\n=== Plot 状态分布 ===")
        cursor.execute("SELECT Status, COUNT(*) FROM Plot GROUP BY Status")
        for r in cursor.fetchall():
            print(f"  Status='{r[0]}' count={r[1]}")

        # 5. 直接执行首页统计SQL验证
        print("\n=== 首页应收统计SQL验证 ===")
        cursor.execute("""
            SELECT 
                ISNULL(SUM(CASE WHEN Status = N'未收' THEN RemainingAmount ELSE 0 END), 0),
                ISNULL(SUM(CASE WHEN Status = N'部分收' THEN RemainingAmount ELSE 0 END), 0),
                ISNULL(SUM(CASE WHEN Status = N'已收' THEN Amount ELSE 0 END), 0),
                COUNT(CASE WHEN Status = N'未收' THEN 1 END),
                COUNT(CASE WHEN Status = N'部分收' THEN 1 END)
            FROM Receivable
        """)
        r = cursor.fetchone()
        print(f"  未收金额={r[0]} 部分收金额={r[1]} 已收金额={r[2]} 未收笔数={r[3]} 部分收笔数={r[4]}")

        # 6. 验证在租商户
        print("\n=== 首页在租商户SQL验证 ===")
        cursor.execute("SELECT COUNT(*) FROM Merchant WHERE Status = N'正常'")
        print(f"  Merchant Status='正常' count={cursor.fetchone()[0]}")

        # 7. 查看有合同的商户
        print("\n=== 有合同的商户 ===")
        cursor.execute("""
            SELECT m.MerchantID, m.MerchantName, m.Status, c.Status as ContractStatus
            FROM Merchant m
            INNER JOIN Contract c ON m.MerchantID = c.MerchantID
        """)
        for r in cursor.fetchall():
            print(f"  MerchantID={r[0]} Name='{r[1]}' MerchantStatus='{r[2]}' ContractStatus='{r[3]}'")
