-- 补充修改剩余的 VARCHAR 字段
-- 执行时间：2026-04-04

USE hf_metalmarket;
GO

-- ============================================================
-- 1. Plot 表
-- ============================================================

-- 删除约束
ALTER TABLE [Plot] DROP CONSTRAINT IF EXISTS [UQ__Plot__0DFF834700EE45BE];
ALTER TABLE [Plot] DROP CONSTRAINT IF EXISTS [DF__Plot__Status__48CFD27E];
GO

-- 修改字段类型
ALTER TABLE [Plot] ALTER COLUMN [PlotNumber] NVARCHAR(50) NOT NULL;
ALTER TABLE [Plot] ALTER COLUMN [Status] NVARCHAR(50) NULL;
GO

-- 重新创建约束
ALTER TABLE [Plot] ADD CONSTRAINT UQ_Plot_PlotNumber UNIQUE ([PlotNumber]);
ALTER TABLE [Plot] ADD CONSTRAINT DF_Plot_Status DEFAULT N'空闲' FOR [Status];
GO


-- ============================================================
-- 2. Receivable 表
-- ============================================================

-- 删除约束
ALTER TABLE [Receivable] DROP CONSTRAINT IF EXISTS [DF__Receivabl__Statu__05D8E0BE];
GO

-- 修改字段类型
ALTER TABLE [Receivable] ALTER COLUMN [Status] NVARCHAR(50) NULL;
GO

-- 重新创建约束
ALTER TABLE [Receivable] ADD CONSTRAINT DF_Receivable_Status DEFAULT N'未收款' FOR [Status];
GO


-- ============================================================
-- 验证修改结果
-- ============================================================

PRINT '验证修改结果：';
PRINT '';

SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE DATA_TYPE = 'varchar'
AND TABLE_NAME NOT IN ('sysdiagrams', 'dtproperties', 'Merchant_Backup_20260331_123354')
ORDER BY TABLE_NAME, COLUMN_NAME;

PRINT '';
PRINT '如果上面的查询没有结果，说明所有 VARCHAR 字段都已成功修改为 NVARCHAR';
PRINT '修改完成！';
GO
