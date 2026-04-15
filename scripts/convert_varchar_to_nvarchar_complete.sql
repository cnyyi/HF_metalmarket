-- 将所有 VARCHAR 字段修改为 NVARCHAR
-- 执行时间：2026-04-04
-- 说明：需要先删除约束，修改字段类型，然后重新创建约束

USE hf_metalmarket;
GO

-- ============================================================
-- 1. Contract 表
-- ============================================================

-- 删除约束
ALTER TABLE [Contract] DROP CONSTRAINT IF EXISTS [UQ__Contract__C51D43DA6DB34517];
ALTER TABLE [Contract] DROP CONSTRAINT IF EXISTS [DF__Contract__Status__4F7CD00D];
GO

-- 修改字段类型
ALTER TABLE [Contract] ALTER COLUMN [ContractNumber] NVARCHAR(50) NOT NULL;
ALTER TABLE [Contract] ALTER COLUMN [Status] NVARCHAR(50) NULL;
GO

-- 重新创建约束
ALTER TABLE [Contract] ADD CONSTRAINT UQ_Contract_ContractNumber UNIQUE ([ContractNumber]);
ALTER TABLE [Contract] ADD CONSTRAINT DF_Contract_Status DEFAULT N'有效' FOR [Status];
GO


-- ============================================================
-- 2. ElectricityMeter 表
-- ============================================================

-- 删除约束
ALTER TABLE [ElectricityMeter] DROP CONSTRAINT IF EXISTS [UQ__Electric__999CDEB387A07A1B];
ALTER TABLE [ElectricityMeter] DROP CONSTRAINT IF EXISTS [DF__Electrici__Meter__59063A47];
GO

-- 修改字段类型
ALTER TABLE [ElectricityMeter] ALTER COLUMN [MeterNumber] NVARCHAR(50) NOT NULL;
ALTER TABLE [ElectricityMeter] ALTER COLUMN [MeterType] NVARCHAR(50) NOT NULL;
GO

-- 重新创建约束
ALTER TABLE [ElectricityMeter] ADD CONSTRAINT UQ_ElectricityMeter_MeterNumber UNIQUE ([MeterNumber]);
ALTER TABLE [ElectricityMeter] ADD CONSTRAINT DF_ElectricityMeter_MeterType DEFAULT N'electricity' FOR [MeterType];
GO


-- ============================================================
-- 3. ExpenseType 表
-- ============================================================

-- 删除约束
ALTER TABLE [ExpenseType] DROP CONSTRAINT IF EXISTS [UQ__ExpenseT__BAECAA60BDF51FF0];
ALTER TABLE [ExpenseType] DROP CONSTRAINT IF EXISTS [UQ__ExpenseT__3218A61DC3BC5545];
GO

-- 修改字段类型
ALTER TABLE [ExpenseType] ALTER COLUMN [ExpenseTypeName] NVARCHAR(100) NOT NULL;
ALTER TABLE [ExpenseType] ALTER COLUMN [ExpenseTypeCode] NVARCHAR(50) NOT NULL;
GO

-- 重新创建约束
ALTER TABLE [ExpenseType] ADD CONSTRAINT UQ_ExpenseType_ExpenseTypeName UNIQUE ([ExpenseTypeName]);
ALTER TABLE [ExpenseType] ADD CONSTRAINT UQ_ExpenseType_ExpenseTypeCode UNIQUE ([ExpenseTypeCode]);
GO


-- ============================================================
-- 4. Merchant 表
-- ============================================================

-- 删除约束
ALTER TABLE [Merchant] DROP CONSTRAINT IF EXISTS [DF__Merchant__Status__4316F928];
GO

-- 修改字段类型
ALTER TABLE [Merchant] ALTER COLUMN [Status] NVARCHAR(50) NULL;
GO

-- 重新创建约束
ALTER TABLE [Merchant] ADD CONSTRAINT DF_Merchant_Status DEFAULT N'正常' FOR [Status];
GO


-- ============================================================
-- 5. Payable 表
-- ============================================================

-- 删除约束
ALTER TABLE [Payable] DROP CONSTRAINT IF EXISTS [DF__Payable__Status__0B91BA14];
GO

-- 修改字段类型
ALTER TABLE [Payable] ALTER COLUMN [Status] NVARCHAR(50) NULL;
GO

-- 重新创建约束
ALTER TABLE [Payable] ADD CONSTRAINT DF_Payable_Status DEFAULT N'未付款' FOR [Status];
GO


-- ============================================================
-- 6. Plot 表
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
-- 7. Receivable 表
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
-- 8. Scale 表
-- ============================================================

-- 删除约束
ALTER TABLE [Scale] DROP CONSTRAINT IF EXISTS [UQ__Scale__EF9EB1B898BD0DB3];
ALTER TABLE [Scale] DROP CONSTRAINT IF EXISTS [DF__Scale__Status__236943A5];
GO

-- 修改字段类型
ALTER TABLE [Scale] ALTER COLUMN [ScaleNumber] NVARCHAR(50) NOT NULL;
ALTER TABLE [Scale] ALTER COLUMN [Status] NVARCHAR(50) NULL;
GO

-- 重新创建约束
ALTER TABLE [Scale] ADD CONSTRAINT UQ_Scale_ScaleNumber UNIQUE ([ScaleNumber]);
ALTER TABLE [Scale] ADD CONSTRAINT DF_Scale_Status DEFAULT N'正常' FOR [Status];
GO


-- ============================================================
-- 9. User 表
-- ============================================================

-- 修改字段类型（User表没有约束）
ALTER TABLE [User] ALTER COLUMN [Username] NVARCHAR(50) NOT NULL;
GO


-- ============================================================
-- 10. WaterMeter 表
-- ============================================================

-- 删除约束
ALTER TABLE [WaterMeter] DROP CONSTRAINT IF EXISTS [UQ__WaterMet__999CDEB369846983];
ALTER TABLE [WaterMeter] DROP CONSTRAINT IF EXISTS [DF__WaterMete__Meter__60A75C0F];
ALTER TABLE [WaterMeter] DROP CONSTRAINT IF EXISTS [DF__WaterMete__Statu__6383C8BA];
GO

-- 修改字段类型
ALTER TABLE [WaterMeter] ALTER COLUMN [MeterNumber] NVARCHAR(50) NOT NULL;
ALTER TABLE [WaterMeter] ALTER COLUMN [MeterType] NVARCHAR(50) NOT NULL;
ALTER TABLE [WaterMeter] ALTER COLUMN [Status] NVARCHAR(50) NULL;
GO

-- 重新创建约束
ALTER TABLE [WaterMeter] ADD CONSTRAINT UQ_WaterMeter_MeterNumber UNIQUE ([MeterNumber]);
ALTER TABLE [WaterMeter] ADD CONSTRAINT DF_WaterMeter_MeterType DEFAULT N'water' FOR [MeterType];
ALTER TABLE [WaterMeter] ADD CONSTRAINT DF_WaterMeter_Status DEFAULT N'正常' FOR [Status];
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
