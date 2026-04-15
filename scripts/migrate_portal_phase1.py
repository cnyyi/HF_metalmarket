"""Phase 1 数据库迁移：User表加UserType，Merchant表加PortalEnabled"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import DevelopmentConfig
app = create_app(DevelopmentConfig)

with app.app_context():
    from utils.database import DBConnection

    with DBConnection() as conn:
        cur = conn.cursor()

        # 1. User 表加 UserType 字段
        cur.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'User' AND COLUMN_NAME = 'UserType'
        """)
        if cur.fetchone()[0] == 0:
            cur.execute("ALTER TABLE [User] ADD UserType NVARCHAR(20) DEFAULT N'Admin'")
            print('Added UserType column to [User] table')
        else:
            print('UserType column already exists')

        # 更新现有数据
        cur.execute("UPDATE [User] SET UserType = N'Admin' WHERE UserType IS NULL OR UserType = ''")
        print(f'Updated {cur.rowcount} existing users to Admin type')

        # 2. Merchant 表加 PortalEnabled
        cur.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'Merchant' AND COLUMN_NAME = 'PortalEnabled'
        """)
        if cur.fetchone()[0] == 0:
            cur.execute("ALTER TABLE Merchant ADD PortalEnabled BIT DEFAULT 0")
            print('Added PortalEnabled column to Merchant table')
        else:
            print('PortalEnabled column already exists')

        # 3. Merchant 表加 PortalOpenTime
        cur.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'Merchant' AND COLUMN_NAME = 'PortalOpenTime'
        """)
        if cur.fetchone()[0] == 0:
            cur.execute("ALTER TABLE Merchant ADD PortalOpenTime DATETIME NULL")
            print('Added PortalOpenTime column to Merchant table')
        else:
            print('PortalOpenTime column already exists')

        conn.commit()

        # 4. 确保 merchant 角色存在
        cur.execute("SELECT RoleID FROM Role WHERE RoleCode = 'merchant'")
        role = cur.fetchone()
        if not role:
            cur.execute("""
                INSERT INTO Role (RoleName, RoleCode, Description, IsActive, CreateTime)
                VALUES (N'商户用户', 'merchant', N'商户门户用户角色', 1, GETDATE())
            """)
            print('Created merchant role')
        else:
            print('merchant role already exists')

        # 5. 确保门户权限存在
        portal_permissions = [
            ('portal_view', '门户访问', '访问商户门户', 'portal'),
            ('portal_contract', '合同查看', '查看本商户合同', 'portal'),
            ('portal_finance', '财务查看', '查看本商户缴费记录', 'portal'),
            ('portal_scale', '过磅查看', '查看本商户过磅记录', 'portal'),
            ('portal_utility', '水电查看', '查看本商户水电抄表', 'portal'),
        ]

        for code, name, desc, module in portal_permissions:
            cur.execute("SELECT PermissionID FROM Permission WHERE PermissionCode = ?", (code,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, IsActive, CreateTime)
                    VALUES (?, ?, ?, ?, 1, GETDATE())
                """, (name, code, desc, module))
                print(f'Created permission: {code}')
            else:
                print(f'Permission already exists: {code}')

        conn.commit()

        # 6. 将门户权限分配给 merchant 角色
        cur.execute("SELECT RoleID FROM Role WHERE RoleCode = 'merchant'")
        role_row = cur.fetchone()
        if role_row:
            role_id = role_row[0]
            for code, _, _, _ in portal_permissions:
                cur.execute("SELECT PermissionID FROM Permission WHERE PermissionCode = ?", (code,))
                perm_row = cur.fetchone()
                if perm_row:
                    perm_id = perm_row[0]
                    cur.execute("""
                        SELECT COUNT(*) FROM RolePermission WHERE RoleID = ? AND PermissionID = ?
                    """, (role_id, perm_id))
                    if cur.fetchone()[0] == 0:
                        cur.execute("""
                            INSERT INTO RolePermission (RoleID, PermissionID, CreateTime)
                            VALUES (?, ?, GETDATE())
                        """, (role_id, perm_id))
                        print(f'Assigned permission {code} to merchant role')

        conn.commit()
        print('\n迁移完成!')
