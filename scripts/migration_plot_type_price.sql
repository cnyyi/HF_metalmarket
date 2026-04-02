-- =====================================================
-- 地块类型和单价管理功能 - 数据库迁移脚本
-- 执行日期: 2026-03-31
-- =====================================================

-- 1. 为Sys_Dictionary表添加UnitPrice字段
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('Sys_Dictionary') 
    AND name = 'UnitPrice'
)
BEGIN
    ALTER TABLE Sys_Dictionary
    ADD UnitPrice DECIMAL(10,2) NULL;
    
    PRINT '已添加 UnitPrice 字段到 Sys_Dictionary 表';
END
ELSE
BEGIN
    PRINT 'UnitPrice 字段已存在，跳过';
END
GO

-- 添加字段说明
IF EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('Sys_Dictionary') 
    AND name = 'UnitPrice'
)
BEGIN
    EXEC sp_addextendedproperty 
        @name = N'MS_Description', 
        @value = N'单价（仅用于地块类型）', 
        @level0type = N'SCHEMA', @level0name = N'dbo',
        @level1type = N'TABLE',  @level1name = N'Sys_Dictionary',
        @level2type = N'COLUMN', @level2name = N'UnitPrice';
END
GO

-- 2. 为Plot表添加地块类型字段
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('Plot') 
    AND name = 'PlotType'
)
BEGIN
    ALTER TABLE Plot
    ADD PlotType NVARCHAR(50) NULL;
    
    PRINT '已添加 PlotType 字段到 Plot 表';
END
ELSE
BEGIN
    PRINT 'PlotType 字段已存在，跳过';
END
GO

-- 添加字段说明
IF EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('Plot') 
    AND name = 'PlotType'
)
BEGIN
    EXEC sp_addextendedproperty 
        @name = N'MS_Description', 
        @value = N'地块类型', 
        @level0type = N'SCHEMA', @level0name = N'dbo',
        @level1type = N'TABLE',  @level1name = N'Plot',
        @level2type = N'COLUMN', @level2name = N'PlotType';
END
GO

-- 3. 为Plot表添加月租金字段
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('Plot') 
    AND name = 'MonthlyRent'
)
BEGIN
    ALTER TABLE Plot
    ADD MonthlyRent DECIMAL(10,2) NULL;
    
    PRINT '已添加 MonthlyRent 字段到 Plot 表';
END
ELSE
BEGIN
    PRINT 'MonthlyRent 字段已存在，跳过';
END
GO

-- 添加字段说明
IF EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('Plot') 
    AND name = 'MonthlyRent'
)
BEGIN
    EXEC sp_addextendedproperty 
        @name = N'MS_Description', 
        @value = N'月租金', 
        @level0type = N'SCHEMA', @level0name = N'dbo',
        @level1type = N'TABLE',  @level1name = N'Plot',
        @level2type = N'COLUMN', @level2name = N'MonthlyRent';
END
GO

-- 4. 为Plot表添加年租金字段
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('Plot') 
    AND name = 'YearlyRent'
)
BEGIN
    ALTER TABLE Plot
    ADD YearlyRent DECIMAL(10,2) NULL;
    
    PRINT '已添加 YearlyRent 字段到 Plot 表';
END
ELSE
BEGIN
    PRINT 'YearlyRent 字段已存在，跳过';
END
GO

-- 添加字段说明
IF EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('Plot') 
    AND name = 'YearlyRent'
)
BEGIN
    EXEC sp_addextendedproperty 
        @name = N'MS_Description', 
        @value = N'年租金', 
        @level0type = N'SCHEMA', @level0name = N'dbo',
        @level1type = N'TABLE',  @level1name = N'Plot',
        @level2type = N'COLUMN', @level2name = N'YearlyRent';
END
GO

-- 5. 创建索引
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE object_id = OBJECT_ID('Plot') 
    AND name = 'idx_plot_type'
)
BEGIN
    CREATE INDEX idx_plot_type ON Plot(PlotType);
    PRINT '已创建 idx_plot_type 索引';
END
ELSE
BEGIN
    PRINT 'idx_plot_type 索引已存在，跳过';
END
GO

-- 6. 初始化地块类型数据（如果不存在）
IF NOT EXISTS (
    SELECT 1 FROM Sys_Dictionary WHERE DictType = N'plot_type'
)
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, UnitPrice, SortOrder, Description)
    VALUES 
    (N'plot_type', N'cement_ground', N'水泥地皮', 50.00, 1, N'水泥地皮地块'),
    (N'plot_type', N'steel_workshop', N'钢结构厂房', 80.00, 2, N'钢结构厂房地块'),
    (N'plot_type', N'brick_workshop', N'砖混厂房', 70.00, 3, N'砖混厂房地块');
    
    PRINT '已初始化地块类型数据';
END
ELSE
BEGIN
    PRINT '地块类型数据已存在，跳过初始化';
END
GO

PRINT '========================================';
PRINT '数据库迁移完成！';
PRINT '========================================';
