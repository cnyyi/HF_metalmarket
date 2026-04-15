-- 迁移脚本：给 UtilityReading 表新增 BelongMonth 字段
-- 执行日期：2026-04-14
-- 说明：BelongMonth 存储费用所属月份，格式"YYYY年MM月"（如"2026年03月"）
--       由用户在抄表页面通过下拉框选择，与抄表日期（ReadingDate）相互独立

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'UtilityReading'
      AND COLUMN_NAME = 'BelongMonth'
)
BEGIN
    ALTER TABLE UtilityReading
    ADD BelongMonth NVARCHAR(20) NULL;

    PRINT 'BelongMonth 列已成功添加到 UtilityReading 表。';
END
ELSE
BEGIN
    PRINT 'BelongMonth 列已存在，跳过添加。';
END
