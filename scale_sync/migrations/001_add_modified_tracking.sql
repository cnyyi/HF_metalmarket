-- ============================================================
-- 过磅记录表增加修改追踪字段
-- 用于检测 Access 磅单修改，标记原记录并插入新版本
-- ============================================================

-- 1. 标记该记录是否被修改过（原记录被标记为1，表示已过时）
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ScaleRecord' AND COLUMN_NAME = 'IsModified'
)
BEGIN
    ALTER TABLE ScaleRecord ADD IsModified BIT DEFAULT 0;
END
GO

-- 2. 新记录指向被修改的原记录ID（仅修改产生的新记录有值）
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ScaleRecord' AND COLUMN_NAME = 'ModifiedFromRecordID'
)
BEGIN
    ALTER TABLE ScaleRecord ADD ModifiedFromRecordID INT NULL;
END
GO

-- 3. 存储 Access 端的更新时间，用于变更检测对比
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ScaleRecord' AND COLUMN_NAME = 'SourceUpdateTime'
)
BEGIN
    ALTER TABLE ScaleRecord ADD SourceUpdateTime DATETIME NULL;
END
GO

-- 4. 为 IsModified 建索引，方便查询过滤
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_ScaleRecord_IsModified' AND object_id = OBJECT_ID('ScaleRecord')
)
BEGIN
    CREATE INDEX IX_ScaleRecord_IsModified ON ScaleRecord (IsModified) WHERE IsModified = 1;
END
GO

-- 5. 为 ModifiedFromRecordID 建索引
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_ScaleRecord_ModifiedFrom' AND object_id = OBJECT_ID('ScaleRecord')
)
BEGIN
    CREATE INDEX IX_ScaleRecord_ModifiedFrom ON ScaleRecord (ModifiedFromRecordID) WHERE ModifiedFromRecordID IS NOT NULL;
END
GO

PRINT 'ScaleRecord 修改追踪字段添加完成';
