-- ============================================================
-- P2 迁移脚本：预收/预付 + 保证金/押金
-- 执行日期：2026-04-15
-- ============================================================

-- 1. 预收/预付表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Prepayment')
BEGIN
    CREATE TABLE Prepayment (
        PrepaymentID      INT IDENTITY(1,1) PRIMARY KEY,
        Direction         NVARCHAR(10)    NOT NULL,           -- income(预收) / expense(预付)
        CustomerType      NVARCHAR(20)    NOT NULL DEFAULT 'Merchant',  -- Merchant/Supplier/Customer
        CustomerID        INT             NOT NULL,           -- 客户ID
        CustomerName      NVARCHAR(100)   NOT NULL,           -- 客户名称（冗余）
        ExpenseTypeID     INT             NULL,               -- 费用类型（关联字典表）
        TotalAmount       DECIMAL(18,2)   NOT NULL DEFAULT 0, -- 预收/预付总金额
        AppliedAmount     DECIMAL(18,2)   NOT NULL DEFAULT 0, -- 已核销金额
        RemainingAmount   DECIMAL(18,2)   NOT NULL DEFAULT 0, -- 剩余金额
        Description       NVARCHAR(500)   NULL,               -- 说明
        Status            NVARCHAR(20)    NOT NULL DEFAULT N'未核销', -- 未核销/部分核销/已核销
        AccountID         INT             NULL,               -- 收款/付款账户
        CashFlowID        INT             NULL,               -- 关联的CashFlow记录
        CreatedBy         INT             NULL,               -- 操作人
        CreateTime        DATETIME        NOT NULL DEFAULT GETDATE(),
        UpdateTime        DATETIME        NULL
    );
    PRINT '✅ Prepayment 表创建成功';
END
ELSE
    PRINT '⏭️ Prepayment 表已存在，跳过';

-- 2. 预收冲抵明细表（一条预收冲抵多条应收）
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'PrepaymentApply')
BEGIN
    CREATE TABLE PrepaymentApply (
        ApplyID           INT IDENTITY(1,1) PRIMARY KEY,
        PrepaymentID      INT             NOT NULL,           -- 预收/预付ID
        ReceivableID      INT             NULL,               -- 冲抵的应收ID（Direction=income时）
        PayableID         INT             NULL,               -- 冲抵的应付ID（Direction=expense时）
        Amount            DECIMAL(18,2)   NOT NULL,           -- 本次冲抵金额
        Description       NVARCHAR(500)   NULL,
        CreatedBy         INT             NULL,
        CreateTime        DATETIME        NOT NULL DEFAULT GETDATE()
    );
    PRINT '✅ PrepaymentApply 表创建成功';
END
ELSE
    PRINT '⏭️ PrepaymentApply 表已存在，跳过';

-- 3. 保证金/押金表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Deposit')
BEGIN
    CREATE TABLE Deposit (
        DepositID         INT IDENTITY(1,1) PRIMARY KEY,
        CustomerType      NVARCHAR(20)    NOT NULL DEFAULT 'Merchant',
        CustomerID        INT             NOT NULL,
        CustomerName      NVARCHAR(100)   NOT NULL,
        DepositType       NVARCHAR(50)    NOT NULL,           -- 押金类型（字典：deposit_type）
        Amount            DECIMAL(18,2)   NOT NULL DEFAULT 0, -- 押金金额
        RefundAmount      DECIMAL(18,2)   NOT NULL DEFAULT 0, -- 已退金额
        DeductAmount      DECIMAL(18,2)   NOT NULL DEFAULT 0, -- 已扣金额
        TransferAmount    DECIMAL(18,2)   NOT NULL DEFAULT 0, -- 已转抵金额
        Status            NVARCHAR(20)    NOT NULL DEFAULT N'收取中', -- 收取中/部分退还/已结清
        AccountID         INT             NULL,               -- 收款账户
        CashFlowID        INT             NULL,               -- 收取时产生的CashFlow
        RelatedContractID INT             NULL,               -- 关联合同ID
        Description       NVARCHAR(500)   NULL,
        CreatedBy         INT             NULL,
        CreateTime        DATETIME        NOT NULL DEFAULT GETDATE(),
        UpdateTime        DATETIME        NULL
    );
    PRINT '✅ Deposit 表创建成功';
END
ELSE
    PRINT '⏭️ Deposit 表已存在，跳过';

-- 4. 押金操作记录表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DepositOperation')
BEGIN
    CREATE TABLE DepositOperation (
        OperationID       INT IDENTITY(1,1) PRIMARY KEY,
        DepositID         INT             NOT NULL,
        OperationType     NVARCHAR(20)    NOT NULL,           -- refund(退还)/deduct(扣除)/transfer(转抵)
        Amount            DECIMAL(18,2)   NOT NULL,
        AccountID         INT             NULL,               -- 退还时扣款的账户
        ReceivableID      INT             NULL,               -- 转抵时的应收ID
        CashFlowID        INT             NULL,               -- 产生的CashFlow
        Description       NVARCHAR(500)   NULL,
        CreatedBy         INT             NULL,
        CreateTime        DATETIME        NOT NULL DEFAULT GETDATE()
    );
    PRINT '✅ DepositOperation 表创建成功';
END
ELSE
    PRINT '⏭️ DepositOperation 表已存在，跳过';

-- ============================================================
-- 字典数据
-- ============================================================

-- 预收/预付状态
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'prepayment_status' AND DictCode = 'unsettled')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive, CreateTime)
    VALUES ('prepayment_status', 'unsettled', N'未核销', 1, 1, GETDATE());

IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'prepayment_status' AND DictCode = 'partial')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive, CreateTime)
    VALUES ('prepayment_status', 'partial', N'部分核销', 2, 1, GETDATE());

IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'prepayment_status' AND DictCode = 'settled')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive, CreateTime)
    VALUES ('prepayment_status', 'settled', N'已核销', 3, 1, GETDATE());

-- 押金类型
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'deposit_type' AND DictCode = 'contract')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive, CreateTime)
    VALUES ('deposit_type', 'contract', N'合同押金', 1, 1, GETDATE());

IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'deposit_type' AND DictCode = 'decoration')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive, CreateTime)
    VALUES ('deposit_type', 'decoration', N'装修押金', 2, 1, GETDATE());

IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'deposit_type' AND DictCode = 'other')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive, CreateTime)
    VALUES ('deposit_type', 'other', N'其他押金', 3, 1, GETDATE());

-- 押金状态
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'deposit_status' AND DictCode = 'holding')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive, CreateTime)
    VALUES ('deposit_status', 'holding', N'收取中', 1, 1, GETDATE());

IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'deposit_status' AND DictCode = 'partial_refund')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive, CreateTime)
    VALUES ('deposit_status', 'partial_refund', N'部分退还', 2, 1, GETDATE());

IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'deposit_status' AND DictCode = 'settled')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive, CreateTime)
    VALUES ('deposit_status', 'settled', N'已结清', 3, 1, GETDATE());

-- 预收/预付方向
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'prepayment_direction' AND DictCode = 'income')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive, CreateTime)
    VALUES ('prepayment_direction', 'income', N'预收', 1, 1, GETDATE());

IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'prepayment_direction' AND DictCode = 'expense')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive, CreateTime)
    VALUES ('prepayment_direction', 'expense', N'预付', 2, 1, GETDATE());

PRINT '✅ 字典数据插入完成';

-- ============================================================
-- 权限数据
-- ============================================================

-- 预收预付管理
IF NOT EXISTS (SELECT 1 FROM Permission WHERE PermissionCode = 'prepayment_manage')
BEGIN
    INSERT INTO Permission (PermissionName, PermissionCode, Description)
    VALUES (N'预收预付管理', 'prepayment_manage', N'管理预收/预付款项及核销');
    PRINT '✅ 权限 prepayment_manage 创建成功';
END

-- 押金管理
IF NOT EXISTS (SELECT 1 FROM Permission WHERE PermissionCode = 'deposit_manage')
BEGIN
    INSERT INTO Permission (PermissionName, PermissionCode, Description)
    VALUES (N'押金管理', 'deposit_manage', N'管理保证金/押金的收取、退还、扣除、转抵');
    PRINT '✅ 权限 deposit_manage 创建成功';
END

-- 给管理员角色赋权
DECLARE @AdminRoleID INT = (SELECT TOP 1 RoleID FROM Role WHERE RoleName = N'管理员');
DECLARE @StaffRoleID INT = (SELECT TOP 1 RoleID FROM Role WHERE RoleName = N'工作人员');
DECLARE @PrepaymentPermID INT = (SELECT PermissionID FROM Permission WHERE PermissionCode = 'prepayment_manage');
DECLARE @DepositPermID INT = (SELECT PermissionID FROM Permission WHERE PermissionCode = 'deposit_manage');

IF @AdminRoleID IS NOT NULL AND @PrepaymentPermID IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM RolePermission WHERE RoleID = @AdminRoleID AND PermissionID = @PrepaymentPermID)
BEGIN
    INSERT INTO RolePermission (RoleID, PermissionID) VALUES (@AdminRoleID, @PrepaymentPermID);
    PRINT '✅ 管理员角色已赋权 prepayment_manage';
END

IF @AdminRoleID IS NOT NULL AND @DepositPermID IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM RolePermission WHERE RoleID = @AdminRoleID AND PermissionID = @DepositPermID)
BEGIN
    INSERT INTO RolePermission (RoleID, PermissionID) VALUES (@AdminRoleID, @DepositPermID);
    PRINT '✅ 管理员角色已赋权 deposit_manage';
END

IF @StaffRoleID IS NOT NULL AND @PrepaymentPermID IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM RolePermission WHERE RoleID = @StaffRoleID AND PermissionID = @PrepaymentPermID)
BEGIN
    INSERT INTO RolePermission (RoleID, PermissionID) VALUES (@StaffRoleID, @PrepaymentPermID);
    PRINT '✅ 工作人员角色已赋权 prepayment_manage';
END

IF @StaffRoleID IS NOT NULL AND @DepositPermID IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM RolePermission WHERE RoleID = @StaffRoleID AND PermissionID = @DepositPermID)
BEGIN
    INSERT INTO RolePermission (RoleID, PermissionID) VALUES (@StaffRoleID, @DepositPermID);
    PRINT '✅ 工作人员角色已赋权 deposit_manage';
END

PRINT '';
PRINT '========================================';
PRINT 'P2 迁移脚本执行完成';
PRINT '========================================';
