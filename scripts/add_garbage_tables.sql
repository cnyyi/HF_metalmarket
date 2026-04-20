-- ================================================
-- 垃圾清运模块基础数据初始化
-- 执行时间：2026-04-20
-- ================================================

-- 1. 创建 GarbageCollection 表（垃圾清运主表）
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'GarbageCollection')
BEGIN
    CREATE TABLE GarbageCollection (
        CollectionID       INT IDENTITY(1,1) PRIMARY KEY,
        CollectionDate    DATE          NOT NULL,          -- 清运日期
        CustomerID         INT           NULL,              -- 供应商ID（关联Customer表）
        GarbageType        NVARCHAR(50)  NOT NULL,          -- 垃圾类型
        Amount            DECIMAL(18,4) NOT NULL,           -- 数量
        Unit              NVARCHAR(20)  NOT NULL,           -- 单位（吨/车/立方米）
        UnitPrice         DECIMAL(18,2) NOT NULL,          -- 单价
        TotalAmount       DECIMAL(18,2) NOT NULL,           -- 总金额
        Status            NVARCHAR(20)  NOT NULL DEFAULT N'待结算',  -- 待结算/已结算
        Description       NVARCHAR(500) NULL,               -- 备注
        PayableID         INT           NULL,               -- 关联应付账款ID
        CreateBy          INT           NULL,
        CreateTime        DATETIME      NULL DEFAULT GETDATE(),
        UpdateBy          INT           NULL,
        UpdateTime        DATETIME      NULL
    );
    PRINT '✅ GarbageCollection 表创建成功';
END ELSE BEGIN
    PRINT 'ℹ️ GarbageCollection 表已存在，跳过';
END
GO

-- 2. 添加垃圾清运费用项字典（处置费）
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'expense_item_expend' AND DictCode = 'disposal_fee')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive, CreateTime)
    VALUES (N'expense_item_expend', N'disposal_fee', N'处置费', N'垃圾清运处置费支出', 7, 1, GETDATE());
    PRINT '✅ 添加字典：处置费（垃圾清运）';
END

-- 3. 添加垃圾清运供应商（往来客户-服务商类型）
-- 注意：实际供应商名称需要用户确认，以下为占位示例
IF NOT EXISTS (SELECT 1 FROM Customer WHERE CustomerName LIKE N'%垃圾%' OR CustomerType = N'服务商')
BEGIN
    -- 如果还没有服务商类型客户，插入占位供应商（实际使用时替换为真实数据）
    IF NOT EXISTS (SELECT 1 FROM Customer WHERE CustomerType = N'服务商')
    BEGIN
        INSERT INTO Customer (CustomerName, CustomerType, Status, CreateTime)
        VALUES (N'垃圾清运供应商（待确认）', N'服务商', N'正常', GETDATE());
        PRINT '✅ 添加垃圾清运供应商占位记录';
    END
END
GO

PRINT '========================================';
PRINT '✅ 垃圾清运模块数据初始化完成';
PRINT '========================================';
