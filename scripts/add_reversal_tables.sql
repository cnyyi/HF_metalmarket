-- 收款/付款冲销功能 - 数据库迁移
-- 日期: 2026-04-29

-- 新建冲销记录表
CREATE TABLE ReversalRecord (
    ReversalID         INT IDENTITY(1,1) PRIMARY KEY,
    OriginalType       NVARCHAR(50) NOT NULL,
    OriginalID         INT NOT NULL,
    ReversalAmount     DECIMAL(18,2) NOT NULL,
    Reason             NVARCHAR(500) NOT NULL,
    ReversalCashFlowID INT NULL,
    CreatedBy          INT NOT NULL,
    CreateTime         DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Reversal_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES [User](UserID)
);

-- CollectionRecord 增加冲销标记
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('CollectionRecord') AND name = 'IsReversed')
    ALTER TABLE CollectionRecord ADD IsReversed BIT DEFAULT 0;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('CollectionRecord') AND name = 'ReversalID')
    ALTER TABLE CollectionRecord ADD ReversalID INT NULL;

-- PaymentRecord 增加冲销标记
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('PaymentRecord') AND name = 'IsReversed')
    ALTER TABLE PaymentRecord ADD IsReversed BIT DEFAULT 0;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('PaymentRecord') AND name = 'ReversalID')
    ALTER TABLE PaymentRecord ADD ReversalID INT NULL;
