-- =============================================
-- 微信门户数据库迁移脚本
-- 创建 WxUser 和 MerchantBinding 表
-- =============================================

-- 1. 微信用户关联表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'WxUser')
BEGIN
    CREATE TABLE WxUser (
        WxUserID      INT IDENTITY(1,1) PRIMARY KEY,
        OpenID        NVARCHAR(100) NOT NULL,
        UnionID       NVARCHAR(100) NULL,
        UserID        INT NULL FOREIGN KEY REFERENCES [User](UserID),
        Nickname      NVARCHAR(50) NULL,
        HeadImgUrl    NVARCHAR(500) NULL,
        PhoneNumber   NVARCHAR(20) NULL,
        CurrentMerchantID INT NULL FOREIGN KEY REFERENCES Merchant(MerchantID),
        CreateTime    DATETIME DEFAULT GETDATE(),
        UpdateTime    DATETIME NULL
    );

    -- OpenID 唯一索引
    CREATE UNIQUE INDEX IX_WxUser_OpenID ON WxUser(OpenID);

    -- UnionID 索引
    CREATE INDEX IX_WxUser_UnionID ON WxUser(UnionID) WHERE UnionID IS NOT NULL;

    -- UserID 索引
    CREATE INDEX IX_WxUser_UserID ON WxUser(UserID) WHERE UserID IS NOT NULL;
END
GO

-- 2. 商户绑定申请表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'MerchantBinding')
BEGIN
    CREATE TABLE MerchantBinding (
        BindingID     INT IDENTITY(1,1) PRIMARY KEY,
        UserID        INT NOT NULL FOREIGN KEY REFERENCES [User](UserID),
        MerchantID    INT NOT NULL FOREIGN KEY REFERENCES Merchant(MerchantID),
        BindRole      NVARCHAR(20) NOT NULL,
        Status        NVARCHAR(20) NOT NULL DEFAULT N'Pending',
        ApplyTime     DATETIME DEFAULT GETDATE(),
        ApproveTime   DATETIME NULL,
        ApproverID    INT NULL FOREIGN KEY REFERENCES [User](UserID),
        RejectReason  NVARCHAR(200) NULL,
        Remark        NVARCHAR(200) NULL,
        IsActive      BIT DEFAULT 1
    );

    -- 用户+商户+状态 复合索引
    CREATE INDEX IX_MerchantBinding_UserMerchant
        ON MerchantBinding(UserID, MerchantID, Status);

    -- 状态索引
    CREATE INDEX IX_MerchantBinding_Status
        ON MerchantBinding(Status) WHERE Status = N'Pending';
END
GO

PRINT N'微信门户数据库迁移完成';
