-- 微信门户所需表结构
-- 执行时间: 2026-04-24

-- WxUser: 微信用户表
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WxUser')
BEGIN
    CREATE TABLE WxUser (
        WxUserID INT IDENTITY(1,1) PRIMARY KEY,
        OpenID NVARCHAR(100) NOT NULL,
        UnionID NVARCHAR(100) DEFAULT '',
        UserID INT,
        Nickname NVARCHAR(100) DEFAULT '',
        HeadImgUrl NVARCHAR(500) DEFAULT '',
        PhoneNumber NVARCHAR(20) DEFAULT '',
        CurrentMerchantID INT DEFAULT NULL,
        CreateTime DATETIME DEFAULT GETDATE(),
        UpdateTime DATETIME DEFAULT NULL
    );
    
    CREATE UNIQUE INDEX IX_WxUser_OpenID ON WxUser(OpenID);
    CREATE INDEX IX_WxUser_UserID ON WxUser(UserID);
END
GO

-- MerchantBinding: 商户绑定申请表
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'MerchantBinding')
BEGIN
    CREATE TABLE MerchantBinding (
        BindingID INT IDENTITY(1,1) PRIMARY KEY,
        UserID INT NOT NULL,
        MerchantID INT NOT NULL,
        BindRole NVARCHAR(20) DEFAULT 'Staff',
        Status NVARCHAR(20) DEFAULT 'Pending',
        ApplyTime DATETIME DEFAULT GETDATE(),
        ApproveTime DATETIME DEFAULT NULL,
        ApproverID INT DEFAULT NULL,
        RejectReason NVARCHAR(500) DEFAULT '',
        Remark NVARCHAR(500) DEFAULT '',
        IsActive BIT DEFAULT 1
    );
    
    CREATE INDEX IX_MerchantBinding_UserID ON MerchantBinding(UserID);
    CREATE INDEX IX_MerchantBinding_MerchantID ON MerchantBinding(MerchantID);
    CREATE INDEX IX_MerchantBinding_Status ON MerchantBinding(Status);
END
GO
