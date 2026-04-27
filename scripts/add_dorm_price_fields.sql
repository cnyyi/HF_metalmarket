-- ========================================
-- 宿舍管理业务逻辑调整：价格浮动 + 水费双模式
-- ========================================

USE [hf_metalmarket];
GO

-- 1. DormOccupancy 表新增价格字段
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('DormOccupancy') AND name = 'MonthlyRent')
BEGIN
    ALTER TABLE DormOccupancy ADD MonthlyRent DECIMAL(10,2) NOT NULL DEFAULT 0;
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('DormOccupancy') AND name = 'WaterMode')
BEGIN
    ALTER TABLE DormOccupancy ADD WaterMode NVARCHAR(10) NOT NULL DEFAULT N'quota';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('DormOccupancy') AND name = 'WaterQuota')
BEGIN
    ALTER TABLE DormOccupancy ADD WaterQuota DECIMAL(10,2) NOT NULL DEFAULT 0;
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('DormOccupancy') AND name = 'WaterUnitPrice')
BEGIN
    ALTER TABLE DormOccupancy ADD WaterUnitPrice DECIMAL(6,2) NOT NULL DEFAULT 0;
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('DormOccupancy') AND name = 'ElectricityUnitPrice')
BEGIN
    ALTER TABLE DormOccupancy ADD ElectricityUnitPrice DECIMAL(6,2) NOT NULL DEFAULT 1.0;
END
GO

-- 2. DormRoom 表新增水费模式字段
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('DormRoom') AND name = 'WaterMode')
BEGIN
    ALTER TABLE DormRoom ADD WaterMode NVARCHAR(10) NOT NULL DEFAULT N'quota';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('DormRoom') AND name = 'WaterUnitPrice')
BEGIN
    ALTER TABLE DormRoom ADD WaterUnitPrice DECIMAL(6,2) NOT NULL DEFAULT 0;
END
GO

-- 3. 创建 DormWaterReading 表
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'DormWaterReading')
BEGIN
    CREATE TABLE DormWaterReading (
        ReadingID INT IDENTITY(1,1) PRIMARY KEY,
        RoomID INT NOT NULL,
        YearMonth NVARCHAR(7) NOT NULL,
        PreviousReading DECIMAL(10,2) NOT NULL DEFAULT 0,
        CurrentReading DECIMAL(10,2) NOT NULL DEFAULT 0,
        Consumption DECIMAL(10,2) NOT NULL DEFAULT 0,
        UnitPrice DECIMAL(6,2) NOT NULL DEFAULT 0,
        Amount DECIMAL(10,2) NOT NULL DEFAULT 0,
        ReadingDate DATE NOT NULL,
        OccupancyID INT NULL,
        CreateTime DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_DormWaterReading_Room FOREIGN KEY (RoomID) REFERENCES DormRoom(RoomID),
        CONSTRAINT FK_DormWaterReading_Occupancy FOREIGN KEY (OccupancyID) REFERENCES DormOccupancy(OccupancyID),
        CONSTRAINT UQ_DormWaterReading_Room_Month UNIQUE (RoomID, YearMonth)
    );

    CREATE INDEX IX_DormWaterReading_YearMonth ON DormWaterReading(YearMonth);

    PRINT 'DormWaterReading 表创建成功';
END
GO

-- 4. 回写现有在住记录的价格（从 DormRoom 复制到 DormOccupancy）
UPDATE o
SET o.MonthlyRent = r.MonthlyRent,
    o.WaterMode = r.WaterMode,
    o.WaterQuota = r.WaterQuota,
    o.WaterUnitPrice = r.WaterUnitPrice,
    o.ElectricityUnitPrice = r.ElectricityUnitPrice
FROM DormOccupancy o
INNER JOIN DormRoom r ON o.RoomID = r.RoomID
WHERE o.Status = N'在住';
GO

PRINT '宿舍价格浮动 + 水费双模式迁移完成！';
GO
