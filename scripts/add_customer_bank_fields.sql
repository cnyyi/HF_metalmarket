-- ============================================================
-- Customer 表新增银行信息字段
-- 开户银行、银行账号、户名
-- ============================================================

USE [hf_metalmarket];
GO

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Customer' AND COLUMN_NAME = 'BankName')
BEGIN
    ALTER TABLE [Customer] ADD BankName NVARCHAR(100) NULL;
    PRINT 'Customer.BankName 字段添加成功';
END
GO

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Customer' AND COLUMN_NAME = 'BankAccount')
BEGIN
    ALTER TABLE [Customer] ADD BankAccount NVARCHAR(50) NULL;
    PRINT 'Customer.BankAccount 字段添加成功';
END
GO

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Customer' AND COLUMN_NAME = 'AccountName')
BEGIN
    ALTER TABLE [Customer] ADD AccountName NVARCHAR(100) NULL;
    PRINT 'Customer.AccountName 字段添加成功';
END
GO

PRINT '银行信息字段迁移完成！';
GO
