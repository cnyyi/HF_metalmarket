-- 给 UtilityReading 表增加 BelongMonth 字段
-- 用于记录抄表数据所属月份，格式为 "YYYY年MM月"
-- 与 ReadingMonth (格式 YYYY-MM) 区分，BelongMonth 用于用户界面显示

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'UtilityReading' AND COLUMN_NAME = 'BelongMonth'
)
BEGIN
    ALTER TABLE UtilityReading ADD BelongMonth NVARCHAR(20) NULL;
    PRINT '已添加 BelongMonth 字段到 UtilityReading 表';
END
ELSE
BEGIN
    PRINT 'BelongMonth 字段已存在，跳过';
END
GO
