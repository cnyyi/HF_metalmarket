-- ============================================================
-- 迁移：费用类型从 ExpenseType 表迁移到 Sys_Dictionary 字典表
-- 说明：按收入/支出方向拆分为两个 DictType
--   expense_item_income  = 收入方向费用类型（应收账款使用）
--   expense_item_expend  = 支出方向费用类型（应付账款使用）
-- 日期：2026-04-15
-- ============================================================

-- 1. 检查并插入收入方向费用类型
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'expense_item_income')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive, CreateTime)
    VALUES
    ('expense_item_income', 'rent',          N'租金',   N'地块租金收入',     1, 1, GETDATE()),
    ('expense_item_income', 'water',         N'水费',   N'自来水费收入',     2, 1, GETDATE()),
    ('expense_item_income', 'electricity',   N'电费',   N'电力费收入',       3, 1, GETDATE()),
    ('expense_item_income', 'scale_fee',     N'过磅费', N'磅秤使用费收入',   4, 1, GETDATE()),
    ('expense_item_income', 'management_fee',N'管理费', N'市场管理费收入',   5, 1, GETDATE()),
    ('expense_item_income', 'other_income',  N'其他收入', N'其他收入项',     6, 1, GETDATE());
    PRINT '已插入收入方向费用类型字典数据 (expense_item_income)';
END
ELSE
BEGIN
    PRINT '收入方向费用类型字典数据已存在，跳过';
END
GO

-- 2. 检查并插入支出方向费用类型
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'expense_item_expend')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive, CreateTime)
    VALUES
    ('expense_item_expend', 'purchase',       N'采购',     N'物资采购支出',     1, 1, GETDATE()),
    ('expense_item_expend', 'maintenance',    N'维修费',   N'设施设备维修支出', 2, 1, GETDATE()),
    ('expense_item_expend', 'salary',         N'工资',     N'员工工资支出',     3, 1, GETDATE()),
    ('expense_item_expend', 'utility_expend', N'水电费',   N'市场水电费支出',   4, 1, GETDATE()),
    ('expense_item_expend', 'tax',            N'税费',     N'各项税费支出',     5, 1, GETDATE()),
    ('expense_item_expend', 'other_expend',   N'其他支出', N'其他支出项',       6, 1, GETDATE());
    PRINT '已插入支出方向费用类型字典数据 (expense_item_expend)';
END
ELSE
BEGIN
    PRINT '支出方向费用类型字典数据已存在，跳过';
END
GO

-- 3. （可选）如果旧 expense_item 字典类型不再需要，可执行以下语句删除
-- DELETE FROM Sys_Dictionary WHERE DictType = 'expense_item';
-- GO

PRINT '迁移完成：费用类型已迁移到字典表';
GO
