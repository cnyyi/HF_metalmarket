-- AI Agent 对话会话表
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'AgentConversation')
BEGIN
    CREATE TABLE AgentConversation (
        ConversationID INT IDENTITY(1,1) PRIMARY KEY,
        UserID INT NOT NULL,
        Title NVARCHAR(200) NOT NULL DEFAULT N'新对话',
        Source NVARCHAR(20) NOT NULL DEFAULT N'admin',
        CreateTime DATETIME NOT NULL DEFAULT GETDATE(),
        UpdateTime DATETIME NOT NULL DEFAULT GETDATE(),
        FOREIGN KEY (UserID) REFERENCES [User](UserID)
    );
END;
GO

-- AI Agent 对话消息表
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'AgentMessage')
BEGIN
    CREATE TABLE AgentMessage (
        MessageID INT IDENTITY(1,1) PRIMARY KEY,
        ConversationID INT NOT NULL,
        Role NVARCHAR(20) NOT NULL,
        Content NVARCHAR(MAX) NOT NULL,
        GeneratedSQL NVARCHAR(MAX) NULL,
        QueryResult NVARCHAR(MAX) NULL,
        CreateTime DATETIME NOT NULL DEFAULT GETDATE(),
        FOREIGN KEY (ConversationID) REFERENCES AgentConversation(ConversationID)
    );
END;
GO

-- 索引
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AgentConversation_UserID')
    CREATE INDEX IX_AgentConversation_UserID ON AgentConversation(UserID);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AgentMessage_ConversationID')
    CREATE INDEX IX_AgentMessage_ConversationID ON AgentMessage(ConversationID);
GO
