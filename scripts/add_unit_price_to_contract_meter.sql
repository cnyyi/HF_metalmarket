-- 为合同水电表关联表添加单价字段
-- 执行时间：2026-04-03
-- 说明：方案A - 在合同关联表中添加单价字段，允许不同合同有不同的水电费单价

USE hf_metalmarket;
GO

-- 1. 为 ContractElectricityMeter 表添加 UnitPrice 字段
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'ContractElectricityMeter' 
    AND COLUMN_NAME = 'UnitPrice'
)
BEGIN
    PRINT '正在为 ContractElectricityMeter 表添加 UnitPrice 字段...';
    
    ALTER TABLE ContractElectricityMeter
    ADD UnitPrice DECIMAL(10,4) DEFAULT 0;
    
    PRINT 'ContractElectricityMeter.UnitPrice 字段添加成功';
END
ELSE
BEGIN
    PRINT 'ContractElectricityMeter.UnitPrice 字段已存在，跳过';
END
GO

-- 2. 为 ContractWaterMeter 表添加 UnitPrice 字段
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'ContractWaterMeter' 
    AND COLUMN_NAME = 'UnitPrice'
)
BEGIN
    PRINT '正在为 ContractWaterMeter 表添加 UnitPrice 字段...';
    
    ALTER TABLE ContractWaterMeter
    ADD UnitPrice DECIMAL(10,4) DEFAULT 0;
    
    PRINT 'ContractWaterMeter.UnitPrice 字段添加成功';
END
ELSE
BEGIN
    PRINT 'ContractWaterMeter.UnitPrice 字段已存在，跳过';
END
GO

-- 3. 验证字段是否添加成功
PRINT '';
PRINT '=== 验证结果 ===';
PRINT '';

PRINT 'ContractElectricityMeter 表结构：';
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'ContractElectricityMeter'
ORDER BY ORDINAL_POSITION;

PRINT '';
PRINT 'ContractWaterMeter 表结构：';
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'ContractWaterMeter'
ORDER BY ORDINAL_POSITION;

PRINT '';
PRINT '数据库迁移完成！';
GO
