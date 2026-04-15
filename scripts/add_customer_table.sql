-- ============================================================
-- 客户表迁移脚本
-- 1. 创建 Customer 表
-- 2. Receivable/Payable 新增 CustomerType + CustomerID
-- 3. CollectionRecord/PaymentRecord 新增 CustomerType
-- 可重复执行（IF NOT EXISTS 判断）
-- ============================================================

USE [hf_metalmarket];
GO

-- ============================================================
-- 1. 创建 Customer 表
-- ============================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Customer')
BEGIN
    CREATE TABLE [Customer] (
        CustomerID INT PRIMARY KEY IDENTITY(1,1),
        CustomerName NVARCHAR(100) NOT NULL,
        ShortName NVARCHAR(50) NULL,
        ContactPerson NVARCHAR(50) NULL,
        Phone NVARCHAR(20) NULL,
        Address NVARCHAR(200) NULL,
        CustomerType NVARCHAR(50) NULL,
        BusinessScope NVARCHAR(200) NULL,
        TaxNumber NVARCHAR(100) NULL,
        Description NVARCHAR(500) NULL,
        Status NVARCHAR(50) DEFAULT N'正常',
        CreateTime DATETIME DEFAULT GETDATE(),
        UpdateTime DATETIME NULL
    );
    PRINT 'Customer 表创建成功';
END
ELSE
BEGIN
    PRINT 'Customer 表已存在，跳过创建';
END
GO

-- ============================================================
-- 2. Receivable 表新增字段
-- ============================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Receivable' AND COLUMN_NAME = 'CustomerType')
BEGIN
    ALTER TABLE [Receivable] ADD CustomerType NVARCHAR(20) NULL;
    PRINT 'Receivable.CustomerType 字段添加成功';
END
GO

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Receivable' AND COLUMN_NAME = 'CustomerID')
BEGIN
    ALTER TABLE [Receivable] ADD CustomerID INT NULL;
    PRINT 'Receivable.CustomerID 字段添加成功';
END
GO

-- ============================================================
-- 3. Payable 表新增字段
-- ============================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Payable' AND COLUMN_NAME = 'CustomerType')
BEGIN
    ALTER TABLE [Payable] ADD CustomerType NVARCHAR(20) NULL;
    PRINT 'Payable.CustomerType 字段添加成功';
END
GO

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Payable' AND COLUMN_NAME = 'CustomerID')
BEGIN
    ALTER TABLE [Payable] ADD CustomerID INT NULL;
    PRINT 'Payable.CustomerID 字段添加成功';
END
GO

-- ============================================================
-- 4. CollectionRecord 表新增字段
-- ============================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'CollectionRecord' AND COLUMN_NAME = 'CustomerType')
BEGIN
    ALTER TABLE [CollectionRecord] ADD CustomerType NVARCHAR(20) NULL;
    PRINT 'CollectionRecord.CustomerType 字段添加成功';
END
GO

-- ============================================================
-- 5. PaymentRecord 表新增字段
-- ============================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PaymentRecord' AND COLUMN_NAME = 'CustomerType')
BEGIN
    ALTER TABLE [PaymentRecord] ADD CustomerType NVARCHAR(20) NULL;
    PRINT 'PaymentRecord.CustomerType 字段添加成功';
END
GO

-- ============================================================
-- 6. 将已有数据的 CustomerType 回填为 Merchant
-- ============================================================
UPDATE [Receivable] SET CustomerType = 'Merchant', CustomerID = MerchantID WHERE CustomerType IS NULL AND MerchantID IS NOT NULL;
UPDATE [Payable] SET CustomerType = 'Merchant' WHERE CustomerType IS NULL AND VendorName IS NOT NULL;
UPDATE [CollectionRecord] SET CustomerType = 'Merchant' WHERE CustomerType IS NULL AND MerchantID IS NOT NULL;
UPDATE [PaymentRecord] SET CustomerType = 'Merchant' WHERE CustomerType IS NULL;
PRINT '历史数据回填完成';
GO

PRINT '迁移完成！';
GO
