"""修复 contract_status 字典乱码 + 统一 Contract 表状态值"""
import sys
sys.path.insert(0, '.')
from app import create_app
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)
with app.app_context():
    from utils.database import DBConnection
    with DBConnection() as conn:
        cursor = conn.cursor()

        # 1. 修复字典表 contract_status 乱码
        cursor.execute("SELECT DictID, DictCode, DictName FROM Sys_Dictionary WHERE DictType='contract_status'")
        rows = cursor.fetchall()
        print("=== 修复前 ===")
        for r in rows:
            print(f"  ID={r[0]} Code={r[1]} Name='{r[2]}'")

        # 删除乱码的字典项，重新插入正确的
        cursor.execute("DELETE FROM Sys_Dictionary WHERE DictType='contract_status'")
        cursor.execute("""
            INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive, CreateTime)
            VALUES
                ('contract_status', 'active', N'生效', N'合同生效中', 1, 1, GETDATE()),
                ('contract_status', 'expired', N'已到期', N'合同已到期', 2, 1, GETDATE()),
                ('contract_status', 'terminated', N'已终止', N'合同已终止', 3, 1, GETDATE())
        """)
        print("已修复字典表 contract_status")

        # 2. 统一 Contract 表中 '有效' -> '生效'
        cursor.execute("SELECT COUNT(*) FROM Contract WHERE Status = N'有效'")
        count = cursor.fetchone()[0]
        print(f"\nContract Status='有效' 的记录数: {count}")
        if count > 0:
            cursor.execute("UPDATE Contract SET Status = N'生效' WHERE Status = N'有效'")
            print(f"已将 {count} 条 '有效' 更新为 '生效'")

        conn.commit()

        # 3. 验证
        cursor.execute("SELECT Status, COUNT(*) FROM Contract GROUP BY Status")
        print("\n=== 修复后 Contract 状态分布 ===")
        for r in cursor.fetchall():
            print(f"  Status='{r[0]}' count={r[1]}")

        cursor.execute("SELECT DictCode, DictName FROM Sys_Dictionary WHERE DictType='contract_status' AND IsActive=1 ORDER BY SortOrder")
        print("\n=== 修复后 contract_status 字典 ===")
        for r in cursor.fetchall():
            print(f"  Code={r[0]} Name='{r[1]}'")
