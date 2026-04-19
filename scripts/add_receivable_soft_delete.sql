-- =====================================================
-- 应收账款软删除支持
-- 新增字段：IsActive, DeletedBy, DeletedAt, DeleteReason
-- =====================================================

-- IsActive 字段
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('Receivable') AND name = 'IsActive'
)
BEGIN
    ALTER TABLE Receivable ADD IsActive BIT NOT NULL DEFAULT 1;
    PRINT '字段 IsActive 添加成功';
END
ELSE
BEGIN
    PRINT '字段 IsActive 已存在，跳过';
END
GO

-- DeletedBy 字段
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('Receivable') AND name = 'DeletedBy'
)
BEGIN
    ALTER TABLE Receivable ADD DeletedBy INT NULL;
    PRINT '字段 DeletedBy 添加成功';
END
ELSE
BEGIN
    PRINT '字段 DeletedBy 已存在，跳过';
END
GO

-- DeletedAt 字段
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('Receivable') AND name = 'DeletedAt'
)
BEGIN
    ALTER TABLE Receivable ADD DeletedAt DATETIME NULL;
    PRINT '字段 DeletedAt 添加成功';
END
ELSE
BEGIN
    PRINT '字段 DeletedAt 已存在，跳过';
END
GO

-- DeleteReason 字段
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('Receivable') AND name = 'DeleteReason'
)
BEGIN
    ALTER TABLE Receivable ADD DeleteReason NVARCHAR(500) NULL;
    PRINT '字段 DeleteReason 添加成功';
END
ELSE
BEGIN
    PRINT '字段 DeleteReason 已存在，跳过';
END
GO

-- 确保 IsActive 有默认值约束
IF NOT EXISTS (
    SELECT 1 FROM sys.default_constraints dc
    INNER JOIN sys.columns c ON dc.parent_column_id = c.column_id AND dc.parent_object_id = c.object_id
    WHERE c.object_id = OBJECT_ID('Receivable') AND c.name = 'IsActive'
)
BEGIN
    ALTER TABLE Receivable ADD CONSTRAINT DF_Receivable_IsActive DEFAULT 1 FOR IsActive;
    PRINT '默认值约束 DF_Receivable_IsActive 添加成功';
END
GO

PRINT '==== 应收账款软删除字段迁移完成 ====';
GO
