-- =====================================================
-- 新增应收明细关联表 ReceivableDetail
-- 用于记录合并应收与多条抄表记录的多对多关系
-- =====================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ReceivableDetail')
BEGIN
    CREATE TABLE ReceivableDetail (
        DetailID       INT IDENTITY(1,1) PRIMARY KEY,
        ReceivableID   INT NOT NULL FOREIGN KEY REFERENCES Receivable(ReceivableID),
        ReadingID      INT NOT NULL FOREIGN KEY REFERENCES UtilityReading(ReadingID),
        CreateTime     DATETIME DEFAULT GETDATE(),

        -- 防止重复关联
        CONSTRAINT UQ_ReceivableDetail_Unique UNIQUE (ReceivableID, ReadingID)
    );

    PRINT '表 ReceivableDetail 创建成功';
END
ELSE
BEGIN
    PRINT '表 ReceivableDetail 已存在，跳过创建';
END
GO
