-- ================================================
-- 垃圾费管理模块数据库迁移
-- ================================================

-- 1. Sys_Dictionary 添加 MinAmount 字段
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('Sys_Dictionary') AND name = 'MinAmount'
)
BEGIN
    ALTER TABLE Sys_Dictionary ADD MinAmount DECIMAL(10,2) NULL;
    PRINT '已添加 MinAmount 字段到 Sys_Dictionary 表';
END
ELSE
BEGIN
    PRINT 'MinAmount 字段已存在，跳过';
END
GO

-- 2. 创建 GarbageFee 表
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'GarbageFee')
BEGIN
    CREATE TABLE GarbageFee (
        GarbageFeeID    INT IDENTITY(1,1) PRIMARY KEY,
        MerchantID      INT NOT NULL,
        Year            INT NOT NULL,
        BusinessType    NVARCHAR(100) NULL,
        RentalArea      DECIMAL(10,2) NULL,
        UnitPrice       DECIMAL(10,2) NULL,
        MinAmount       DECIMAL(10,2) NULL,
        CalculatedFee   DECIMAL(10,2) NULL,
        FinalFee        DECIMAL(10,2) NOT NULL,
        ReceivableID    INT NULL,
        Status          NVARCHAR(20) NOT NULL DEFAULT N'待收取',
        Description     NVARCHAR(500) NULL,
        CreateBy        INT NULL,
        CreateTime      DATETIME NULL DEFAULT GETDATE(),
        UpdateBy        INT NULL,
        UpdateTime      DATETIME NULL,
        CONSTRAINT UQ_GarbageFee_Merchant_Year UNIQUE (MerchantID, Year)
    );
    PRINT 'GarbageFee 表创建成功';
END
ELSE
BEGIN
    PRINT 'GarbageFee 表已存在，跳过';
END
GO

-- 3. 添加垃圾费收入类费用项字典
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = N'expense_item_income' AND DictCode = N'garbage_fee')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive, CreateTime)
    VALUES (N'expense_item_income', N'garbage_fee', N'垃圾费', N'商户垃圾费收入', 8, 1, GETDATE());
    PRINT '已添加垃圾费费用项字典';
END
GO

-- 4. 创建索引
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('GarbageFee') AND name = 'idx_garbage_fee_year'
)
BEGIN
    CREATE INDEX idx_garbage_fee_year ON GarbageFee(Year);
    PRINT '已创建 idx_garbage_fee_year 索引';
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('GarbageFee') AND name = 'idx_garbage_fee_status'
)
BEGIN
    CREATE INDEX idx_garbage_fee_status ON GarbageFee(Status);
    PRINT '已创建 idx_garbage_fee_status 索引';
END
GO

PRINT '========================================';
PRINT '垃圾费管理模块数据库迁移完成';
PRINT '========================================';
