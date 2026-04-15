-- ============================================================
-- 给 ContractElectricityMeter 和 ContractWaterMeter 表添加 Status 字段
-- 默认值为 N'启用'，历史数据全部设为启用
-- ============================================================

USE [hf_metalmarket]
GO

-- 1. ContractElectricityMeter 添加 Status 字段
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'ContractElectricityMeter' AND COLUMN_NAME = 'Status'
)
BEGIN
    ALTER TABLE [ContractElectricityMeter] ADD [Status] NVARCHAR(20) DEFAULT N'启用'
    PRINT '[OK] ContractElectricityMeter.Status 字段已添加'
END
ELSE
BEGIN
    PRINT '[SKIP] ContractElectricityMeter.Status 字段已存在'
END
GO

-- 回填历史数据：NULL 值设为启用
UPDATE [ContractElectricityMeter] SET [Status] = N'启用' WHERE [Status] IS NULL
GO

PRINT '[OK] ContractElectricityMeter 历史数据已回填'
GO

-- 2. ContractWaterMeter 添加 Status 字段
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'ContractWaterMeter' AND COLUMN_NAME = 'Status'
)
BEGIN
    ALTER TABLE [ContractWaterMeter] ADD [Status] NVARCHAR(20) DEFAULT N'启用'
    PRINT '[OK] ContractWaterMeter.Status 字段已添加'
END
ELSE
BEGIN
    PRINT '[SKIP] ContractWaterMeter.Status 字段已存在'
END
GO

-- 回填历史数据
UPDATE [ContractWaterMeter] SET [Status] = N'启用' WHERE [Status] IS NULL
GO

PRINT '[OK] ContractWaterMeter 历史数据已回填'
GO

PRINT '========== 迁移完成 =========='
GO
