-- ============================================================
-- Receivable 表增加品名/规格/数量/单位/单价字段
-- 字典表增加 unit_type 类型
-- 执行时间：2026-04-18
-- ============================================================

USE hf_metalmarket;
GO

-- 1. Receivable 表增加 5 个字段
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='Receivable' AND COLUMN_NAME='ProductName')
BEGIN
    ALTER TABLE Receivable ADD ProductName NVARCHAR(200) NULL;
END
GO

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='Receivable' AND COLUMN_NAME='Specification')
BEGIN
    ALTER TABLE Receivable ADD Specification NVARCHAR(200) NULL;
END
GO

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='Receivable' AND COLUMN_NAME='Quantity')
BEGIN
    ALTER TABLE Receivable ADD Quantity DECIMAL(18,4) NULL;
END
GO

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='Receivable' AND COLUMN_NAME='UnitID')
BEGIN
    ALTER TABLE Receivable ADD UnitID INT NULL;
END
GO

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='Receivable' AND COLUMN_NAME='UnitPrice')
BEGIN
    ALTER TABLE Receivable ADD UnitPrice DECIMAL(18,4) NULL;
END
GO

-- 2. 字典表增加 unit_type 类型
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType='unit_type' AND DictCode='kg')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive)
    VALUES ('unit_type', 'kg', N'Kg', 1, 1);
END
GO

IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType='unit_type' AND DictCode='ton')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive)
    VALUES ('unit_type', 'ton', N'吨', 2, 1);
END
GO

IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType='unit_type' AND DictCode='vehicle')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive)
    VALUES ('unit_type', 'vehicle', N'车', 3, 1);
END
GO

IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType='unit_type' AND DictCode='bottle')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, SortOrder, IsActive)
    VALUES ('unit_type', 'bottle', N'瓶', 4, 1);
END
GO

PRINT '迁移完成：Receivable 增加5字段 + unit_type 字典4条';
GO
