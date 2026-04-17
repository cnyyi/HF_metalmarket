"""验证首页统计修复后结果"""
import sys
sys.path.insert(0, '.')
from app import create_app
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)
with app.app_context():
    from utils.database import DBConnection
    with DBConnection() as conn:
        cursor = conn.cursor()

        # 1. 应收统计（修复后SQL）
        cursor.execute("""
            SELECT
                ISNULL(SUM(CASE WHEN Status = N'未付款' THEN RemainingAmount ELSE 0 END), 0),
                ISNULL(SUM(CASE WHEN Status = N'部分付款' THEN RemainingAmount ELSE 0 END), 0),
                ISNULL(SUM(CASE WHEN Status = N'已付清' THEN Amount ELSE 0 END), 0),
                COUNT(CASE WHEN Status = N'未付款' THEN 1 END),
                COUNT(CASE WHEN Status = N'部分付款' THEN 1 END)
            FROM Receivable
        """)
        r = cursor.fetchone()
        print(f"应收 - 未付款: {r[0]}, 部分付款: {r[1]}, 已付清: {r[2]}, 未付款笔数: {r[3]}, 部分付款笔数: {r[4]}")

        # 2. 在租商户
        cursor.execute("SELECT COUNT(*) FROM Merchant WHERE Status = N'正常'")
        print(f"在租商户(正常状态): {cursor.fetchone()[0]}")

        # 3. 合同状态
        cursor.execute("SELECT Status, COUNT(*) FROM Contract GROUP BY Status")
        for r in cursor.fetchall():
            print(f"合同状态: '{r[0]}' count={r[1]}")

        # 4. 有有效合同的独立商户数
        cursor.execute("""
            SELECT COUNT(DISTINCT MerchantID) FROM Contract WHERE Status IN (N'生效', N'有效')
        """)
        print(f"有生效合同的商户数: {cursor.fetchone()[0]}")

        # 5. Plot状态
        cursor.execute("SELECT Status, COUNT(*) FROM Plot GROUP BY Status")
        for r in cursor.fetchall():
            print(f"地块状态: '{r[0]}' count={r[1]}")
