# -*- coding: utf-8 -*-
"""执行费用单模块数据库迁移"""
import os
import sys

# 确保项目根目录在 sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 加载 .env
env_path = os.path.join(PROJECT_ROOT, '.env')
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()

from app import create_app

app = create_app()
with app.app_context():
    from utils.database import DBConnection
    with DBConnection() as conn:
        cursor = conn.cursor()

        # 1. 创建 ExpenseOrder 表
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ExpenseOrder')
            CREATE TABLE ExpenseOrder (
                OrderID INT PRIMARY KEY IDENTITY(1,1),
                OrderNo NVARCHAR(20) NOT NULL UNIQUE,
                ExpenseCategory NVARCHAR(50) NOT NULL,
                VendorName NVARCHAR(100) NOT NULL,
                TotalAmount DECIMAL(12,2) NOT NULL,
                OrderDate DATE NOT NULL,
                Description NVARCHAR(500) NULL,
                Status NVARCHAR(20) NOT NULL DEFAULT N'已确认',
                CreateBy INT NOT NULL,
                CreateTime DATETIME DEFAULT GETDATE()
            )
        """)
        conn.commit()
        print('1. ExpenseOrder table OK')

        # 2. 创建 ExpenseOrderItem 表
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ExpenseOrderItem')
            CREATE TABLE ExpenseOrderItem (
                ItemID INT PRIMARY KEY IDENTITY(1,1),
                OrderID INT NOT NULL,
                ExpenseTypeID INT NOT NULL,
                ItemDescription NVARCHAR(200) NULL,
                Amount DECIMAL(12,2) NOT NULL,
                WorkerName NVARCHAR(50) NULL,
                WorkDate DATE NULL,
                PayableID INT NULL,
                CreateTime DATETIME DEFAULT GETDATE()
            )
        """)
        conn.commit()
        print('2. ExpenseOrderItem table OK')

        # 3. Payable 表加字段
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Payable') AND name = 'ExpenseOrderID')
            ALTER TABLE Payable ADD ExpenseOrderID INT NULL
        """)
        conn.commit()
        print('3. Payable.ExpenseOrderID OK')

        # 4. 字典：费用大类
        cats = [
            ('garbage_transport', '垃圾清运', 1),
            ('temp_labor', '临时用工', 2),
            ('maintenance', '维修维护', 3),
            ('other_expense', '其他支出', 4),
        ]
        for code, name, sort in cats:
            cursor.execute(
                f"IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType=N'expense_category' AND DictCode='{code}') "
                f"INSERT INTO Sys_Dictionary (DictType,DictCode,DictName,SortOrder,IsActive) "
                f"VALUES (N'expense_category',N'{code}',N'{name}',{sort},1)"
            )
        conn.commit()
        print('4. expense_category dict OK')

        # 5. 字典：支出费用项新增
        items = [
            ('transport_fee', '运费', 6),
            ('disposal_fee', '处置费', 7),
            ('temp_labor_fee', '临时工费', 8),
        ]
        for code, name, sort in items:
            cursor.execute(
                f"IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType=N'expense_item_expend' AND DictCode='{code}') "
                f"INSERT INTO Sys_Dictionary (DictType,DictCode,DictName,SortOrder,IsActive) "
                f"VALUES (N'expense_item_expend',N'{code}',N'{name}',{sort},1)"
            )
        conn.commit()
        print('5. expense_item_expend dict OK')

        # 6. 权限
        cursor.execute(
            "IF NOT EXISTS (SELECT 1 FROM Permission WHERE PermissionCode=N'expense_manage') "
            "INSERT INTO Permission (PermissionName,PermissionCode,Description,ModuleName,IsActive) "
            "VALUES (N'费用单管理',N'expense_manage',N'管理费用单的创建、查看',N'业务管理',1)"
        )
        conn.commit()
        print('6. Permission OK')

        # 7. 角色赋权 - admin
        cursor.execute("""
            DECLARE @AdminRoleID INT=(SELECT RoleID FROM Role WHERE RoleCode='admin');
            DECLARE @PermID INT=(SELECT PermissionID FROM Permission WHERE PermissionCode='expense_manage');
            IF @AdminRoleID IS NOT NULL AND @PermID IS NOT NULL
                AND NOT EXISTS(SELECT 1 FROM RolePermission WHERE RoleID=@AdminRoleID AND PermissionID=@PermID)
                INSERT INTO RolePermission (RoleID,PermissionID) VALUES (@AdminRoleID,@PermID)
        """)
        conn.commit()
        print('7a. Admin role permission OK')

        # 7b. 角色赋权 - staff
        cursor.execute("""
            DECLARE @StaffRoleID INT=(SELECT RoleID FROM Role WHERE RoleCode='staff');
            DECLARE @PermID INT=(SELECT PermissionID FROM Permission WHERE PermissionCode='expense_manage');
            IF @StaffRoleID IS NOT NULL AND @PermID IS NOT NULL
                AND NOT EXISTS(SELECT 1 FROM RolePermission WHERE RoleID=@StaffRoleID AND PermissionID=@PermID)
                INSERT INTO RolePermission (RoleID,PermissionID) VALUES (@StaffRoleID,@PermID)
        """)
        conn.commit()
        print('7b. Staff role permission OK')

        # 验证
        cursor.execute("SELECT COUNT(*) FROM Sys_Dictionary WHERE DictType=N'expense_category'")
        print(f'expense_category count: {cursor.fetchone()[0]}')

        cursor.execute("SELECT COUNT(*) FROM Sys_Dictionary WHERE DictType=N'expense_item_expend' AND DictCode IN ('transport_fee','disposal_fee','temp_labor_fee')")
        print(f'new expense_item_expend count: {cursor.fetchone()[0]}')

        cursor.execute("SELECT COUNT(*) FROM Permission WHERE PermissionCode=N'expense_manage'")
        print(f'expense_manage permission count: {cursor.fetchone()[0]}')

        cursor.execute("SELECT name FROM sys.tables WHERE name IN ('ExpenseOrder','ExpenseOrderItem')")
        tables = [row[0] for row in cursor.fetchall()]
        print(f'Created tables: {tables}')

        print('\n=== Migration completed successfully ===')
