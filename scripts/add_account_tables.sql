-- ============================================================
-- P1: 账户体系 + 直接记账 + CashFlow扩展
-- 执行方式: sqlcmd 逐段执行
-- ============================================================

-- 1. 创建 Account 表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Account')
BEGIN
    CREATE TABLE Account (
        AccountID       INT IDENTITY(1,1) PRIMARY KEY,
        AccountName     NVARCHAR(50)   NOT NULL,
        AccountType     NVARCHAR(20)   NOT NULL,  -- Cash/Bank/WeChat
        BankName        NVARCHAR(100)  NULL,
        BankAccount     NVARCHAR(50)   NULL,
        Balance         DECIMAL(18,2)  NOT NULL DEFAULT 0,
        IsDefault       BIT            NOT NULL DEFAULT 0,
        Status          NVARCHAR(20)   NOT NULL DEFAULT N'有效',
        Remark          NVARCHAR(200)  NULL,
        CreateTime      DATETIME       NOT NULL DEFAULT GETDATE(),
        UpdateTime      DATETIME       NULL
    );
    PRINT 'Account 表创建成功';
END
ELSE
    PRINT 'Account 表已存在，跳过';

-- 2. CashFlow 表新增 AccountID 和 TransactionNo 字段
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('CashFlow') AND name = 'AccountID')
BEGIN
    ALTER TABLE CashFlow ADD AccountID INT NULL;
    PRINT 'CashFlow.AccountID 字段添加成功';
END
ELSE
    PRINT 'CashFlow.AccountID 字段已存在，跳过';

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('CashFlow') AND name = 'TransactionNo')
BEGIN
    ALTER TABLE CashFlow ADD TransactionNo NVARCHAR(30) NULL;
    PRINT 'CashFlow.TransactionNo 字段添加成功';
END
ELSE
    PRINT 'CashFlow.TransactionNo 字段已存在，跳过';

-- 3. 字典数据：账户类型
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'account_type' AND DictCode = 'Cash')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, Status)
    VALUES ('account_type', 'Cash', N'现金', 1, 1);

IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'account_type' AND DictCode = 'Bank')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, Status)
    VALUES ('account_type', 'Bank', N'银行', 2, 1);

IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'account_type' AND DictCode = 'WeChat')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, Status)
    VALUES ('account_type', 'WeChat', N'微信', 3, 1);

-- 4. 字典数据：账户状态
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'account_status' AND DictCode = 'Active')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, Status)
    VALUES ('account_status', 'Active', N'有效', 1, 1);

IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'account_status' AND DictCode = 'Inactive')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, Status)
    VALUES ('account_status', 'Inactive', N'停用', 2, 1);

-- 5. 权限：account_manage
IF NOT EXISTS (SELECT 1 FROM Permission WHERE PermissionCode = 'account_manage')
    INSERT INTO Permission (PermissionName, PermissionCode, Description)
    VALUES (N'账户管理', 'account_manage', N'管理资金账户（新增/编辑/停用）');

-- 6. 权限：direct_entry
IF NOT EXISTS (SELECT 1 FROM Permission WHERE PermissionCode = 'direct_entry')
    INSERT INTO Permission (PermissionName, PermissionCode, Description)
    VALUES (N'直接记账', 'direct_entry', N'直接录入收支流水（无需应收/应付）');

-- 7. 角色-权限关联：admin + staff 获得 account_manage 和 direct_entry
DECLARE @AdminRoleID INT, @StaffRoleID INT;
SELECT @AdminRoleID = RoleID FROM Role WHERE RoleCode = 'admin';
SELECT @StaffRoleID = RoleID FROM Role WHERE RoleCode = 'staff';

IF @AdminRoleID IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM RolePermission WHERE RoleID = @AdminRoleID AND PermissionCode = 'account_manage'
)
    INSERT INTO RolePermission (RoleID, PermissionCode) VALUES (@AdminRoleID, 'account_manage');

IF @StaffRoleID IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM RolePermission WHERE RoleID = @StaffRoleID AND PermissionCode = 'account_manage'
)
    INSERT INTO RolePermission (RoleID, PermissionCode) VALUES (@StaffRoleID, 'account_manage');

IF @AdminRoleID IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM RolePermission WHERE RoleID = @AdminRoleID AND PermissionCode = 'direct_entry'
)
    INSERT INTO RolePermission (RoleID, PermissionCode) VALUES (@AdminRoleID, 'direct_entry');

IF @StaffRoleID IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM RolePermission WHERE RoleID = @StaffRoleID AND PermissionCode = 'direct_entry'
)
    INSERT INTO RolePermission (RoleID, PermissionCode) VALUES (@StaffRoleID, 'direct_entry');

-- 8. 初始化默认账户（仅在 Account 表为空时）
IF NOT EXISTS (SELECT 1 FROM Account)
BEGIN
    INSERT INTO Account (AccountName, AccountType, Balance, IsDefault, Status) VALUES (N'现金', 'Cash', 0, 1, N'有效');
    INSERT INTO Account (AccountName, AccountType, Balance, IsDefault, Status) VALUES (N'银行（对公）', 'Bank', 0, 0, N'有效');
    INSERT INTO Account (AccountName, AccountType, Balance, IsDefault, Status) VALUES (N'银行（对私）', 'Bank', 0, 0, N'有效');
    INSERT INTO Account (AccountName, AccountType, Balance, IsDefault, Status) VALUES (N'微信', 'WeChat', 0, 0, N'有效');
    PRINT '默认账户初始化成功（现金/银行对公/银行对私/微信）';
END
ELSE
    PRINT 'Account 表已有数据，跳过默认账户初始化';

PRINT 'P1 迁移完成';
