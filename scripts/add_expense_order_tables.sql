-- =====================================================
-- 费用单模块数据库迁移脚本
-- 日期：2026-04-16
-- 说明：新增 ExpenseOrder / ExpenseOrderItem 表，
--       Payable 表新增 ExpenseOrderID 字段，
--       新增字典数据和权限数据
-- =====================================================

USE hf_metalmarket;
GO

-- 1. 创建费用单主表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ExpenseOrder')
BEGIN
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
    );
    PRINT '✓ ExpenseOrder 表创建成功';
END
ELSE
    PRINT '✓ ExpenseOrder 表已存在，跳过';
GO

-- 2. 创建费用单明细表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ExpenseOrderItem')
BEGIN
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
    );
    PRINT '✓ ExpenseOrderItem 表创建成功';
END
ELSE
    PRINT '✓ ExpenseOrderItem 表已存在，跳过';
GO

-- 3. Payable 表新增 ExpenseOrderID 字段
IF NOT EXISTS (
    SELECT * FROM sys.columns
    WHERE object_id = OBJECT_ID('Payable') AND name = 'ExpenseOrderID'
)
BEGIN
    ALTER TABLE Payable ADD ExpenseOrderID INT NULL;
    PRINT '✓ Payable.ExpenseOrderID 字段添加成功';
END
ELSE
    PRINT '✓ Payable.ExpenseOrderID 字段已存在，跳过';
GO

-- 4. 字典数据：费用大类（expense_category）
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = N'expense_category' AND DictCode = N'garbage_transport')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive) VALUES (N'expense_category', N'garbage_transport', N'垃圾清运', 1, 1);
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = N'expense_category' AND DictCode = N'temp_labor')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive) VALUES (N'expense_category', N'temp_labor', N'临时用工', 2, 1);
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = N'expense_category' AND DictCode = N'maintenance')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive) VALUES (N'expense_category', N'maintenance', N'维修维护', 3, 1);
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = N'expense_category' AND DictCode = N'other_expense')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive) VALUES (N'expense_category', N'other_expense', N'其他支出', 4, 1);
PRINT '✓ 费用大类字典数据写入完成';
GO

-- 5. 字典数据：支出费用项新增项（expense_item_expend）
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = N'expense_item_expend' AND DictCode = N'transport_fee')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive) VALUES (N'expense_item_expend', N'transport_fee', N'运费', 6, 1);
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = N'expense_item_expend' AND DictCode = N'disposal_fee')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive) VALUES (N'expense_item_expend', N'disposal_fee', N'处置费', 7, 1);
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = N'expense_item_expend' AND DictCode = N'temp_labor_fee')
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive) VALUES (N'expense_item_expend', N'temp_labor_fee', N'临时工费', 8, 1);
PRINT '✓ 支出费用项字典数据写入完成';
GO

-- 6. 权限数据
IF NOT EXISTS (SELECT 1 FROM Permission WHERE PermissionCode = N'expense_manage')
BEGIN
    INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, IsActive)
    VALUES (N'费用单管理', N'expense_manage', N'管理费用单的创建、查看', N'业务管理', 1);
    PRINT '✓ 权限 expense_manage 创建成功';
END
ELSE
    PRINT '✓ 权限 expense_manage 已存在，跳过';
GO

-- 7. 给管理员和工作人员角色赋权
DECLARE @AdminRoleID INT = (SELECT RoleID FROM Role WHERE RoleCode = 'admin');
DECLARE @StaffRoleID INT = (SELECT RoleID FROM Role WHERE RoleCode = 'staff');
DECLARE @PermID INT = (SELECT PermissionID FROM Permission WHERE PermissionCode = 'expense_manage');

IF @AdminRoleID IS NOT NULL AND @PermID IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM RolePermission WHERE RoleID = @AdminRoleID AND PermissionID = @PermID)
BEGIN
    INSERT INTO RolePermission (RoleID, PermissionID) VALUES (@AdminRoleID, @PermID);
    PRINT '✓ 管理员角色赋权完成';
END

IF @StaffRoleID IS NOT NULL AND @PermID IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM RolePermission WHERE RoleID = @StaffRoleID AND PermissionID = @PermID)
BEGIN
    INSERT INTO RolePermission (RoleID, PermissionID) VALUES (@StaffRoleID, @PermID);
    PRINT '✓ 工作人员角色赋权完成';
END
GO

PRINT '========== 费用单模块迁移完成 ==========';
GO
