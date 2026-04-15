-- 删除水电表UnitPrice字段的SQL脚本
-- 执行前请确保已备份数据库

-- 1. 删除WaterMeter表中的UnitPrice字段
ALTER TABLE [hf_metalmarket].[dbo].[WaterMeter]
DROP COLUMN [UnitPrice];

-- 2. 删除ElectricityMeter表中的UnitPrice字段
ALTER TABLE [hf_metalmarket].[dbo].[ElectricityMeter]
DROP COLUMN [UnitPrice];

-- 3. 检查删除结果
SELECT * FROM [hf_metalmarket].[dbo].[WaterMeter] WHERE 1=0;
SELECT * FROM [hf_metalmarket].[dbo].[ElectricityMeter] WHERE 1=0;

PRINT 'UnitPrice字段删除完成';