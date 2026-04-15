-- ============================================================
-- 宿舍管理模块迁移脚本
-- 1. 创建 DormRoom 宿舍房间表
-- 2. 创建 DormOccupancy 入住记录表
-- 3. 创建 DormReading 电表读数表
-- 4. 创建 DormBill 月度账单表
-- 5. 新增字典数据（房型/房间状态/租户类型/入住状态/账单状态）
-- 6. 新增费用项（宿舍租金/宿舍水费/宿舍电费）
-- 7. 新增客户类型（宿舍个人）
-- 8. 新增权限 dorm_manage 并赋权
-- 可重复执行（IF NOT EXISTS 判断）
-- ============================================================

USE [hf_metalmarket];
GO

-- ============================================================
-- 1. 创建 DormRoom 宿舍房间表
-- ============================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'DormRoom')
BEGIN
    CREATE TABLE [DormRoom] (
        RoomID              INT PRIMARY KEY IDENTITY(1,1),
        RoomNumber          NVARCHAR(20) NOT NULL,               -- 房间编号（如"宿舍101"）
        RoomType            NVARCHAR(20) NOT NULL DEFAULT N'单间', -- 房型：单间/标间/套间
        Area                DECIMAL(8,2) NULL,                   -- 面积（㎡）
        MonthlyRent         DECIMAL(10,2) NOT NULL DEFAULT 0,    -- 月租金
        WaterQuota          DECIMAL(10,2) NOT NULL DEFAULT 0,    -- 每月水费定额
        ElectricityUnitPrice DECIMAL(6,2) NOT NULL DEFAULT 1.0,  -- 电费单价（元/度）
        MeterNumber         NVARCHAR(30) NULL,                   -- 电表号
        LastReading         DECIMAL(10,2) NULL,                  -- 上次电表读数
        Status              NVARCHAR(20) NOT NULL DEFAULT N'空闲', -- 状态：空闲/已住/维修中
        Description         NVARCHAR(200) NULL,                  -- 备注
        CreateTime          DATETIME DEFAULT GETDATE(),
        UpdateTime          DATETIME NULL,

        CONSTRAINT UQ_DormRoom_Number UNIQUE (RoomNumber)
    );

    PRINT 'DormRoom 表创建成功';
END
ELSE
BEGIN
    PRINT 'DormRoom 表已存在，跳过创建';
END
GO

-- ============================================================
-- 2. 创建 DormOccupancy 入住记录表
-- ============================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'DormOccupancy')
BEGIN
    CREATE TABLE [DormOccupancy] (
        OccupancyID         INT PRIMARY KEY IDENTITY(1,1),
        RoomID              INT NOT NULL FOREIGN KEY REFERENCES [DormRoom](RoomID),
        TenantType          NVARCHAR(20) NOT NULL DEFAULT N'个人', -- 租户类型：商户/个人
        MerchantID          INT NULL FOREIGN KEY REFERENCES [Merchant](MerchantID), -- 关联商户
        TenantName          NVARCHAR(50) NOT NULL,               -- 租户姓名
        TenantPhone         NVARCHAR(20) NULL,                   -- 联系电话
        IDCardNumber        NVARCHAR(18) NULL,                   -- 身份证号
        IDCardFrontPhoto    NVARCHAR(200) NULL,                  -- 身份证正面照路径
        IDCardBackPhoto     NVARCHAR(200) NULL,                  -- 身份证背面照路径
        MoveInDate          DATE NOT NULL,                       -- 入住日期
        MoveOutDate         DATE NULL,                           -- 退房日期
        Status              NVARCHAR(20) NOT NULL DEFAULT N'在住', -- 状态：在住/已退房
        Description         NVARCHAR(200) NULL,                  -- 备注
        CreateTime          DATETIME DEFAULT GETDATE(),
        UpdateTime          DATETIME NULL
    );

    CREATE INDEX IX_DormOccupancy_Room ON [DormOccupancy](RoomID);
    CREATE INDEX IX_DormOccupancy_Merchant ON [DormOccupancy](MerchantID);

    PRINT 'DormOccupancy 表创建成功';
END
ELSE
BEGIN
    PRINT 'DormOccupancy 表已存在，跳过创建';
END
GO

-- ============================================================
-- 3. 创建 DormReading 电表读数表
-- ============================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'DormReading')
BEGIN
    CREATE TABLE [DormReading] (
        ReadingID           INT PRIMARY KEY IDENTITY(1,1),
        RoomID              INT NOT NULL FOREIGN KEY REFERENCES [DormRoom](RoomID),
        YearMonth           NVARCHAR(7) NOT NULL,                -- 抄表月份 YYYY-MM
        PreviousReading     DECIMAL(10,2) NOT NULL DEFAULT 0,   -- 上次读数
        CurrentReading      DECIMAL(10,2) NOT NULL DEFAULT 0,   -- 本次读数
        Consumption         DECIMAL(10,2) NOT NULL DEFAULT 0,   -- 用电量
        UnitPrice           DECIMAL(6,2) NOT NULL DEFAULT 1.0,  -- 电费单价
        Amount              DECIMAL(10,2) NOT NULL DEFAULT 0,   -- 电费金额
        ReadingDate         DATE NOT NULL,                       -- 抄表日期
        OccupancyID         INT NULL FOREIGN KEY REFERENCES [DormOccupancy](OccupancyID), -- 关联入住记录
        CreateTime          DATETIME DEFAULT GETDATE(),

        CONSTRAINT UQ_DormReading_Room_Month UNIQUE (RoomID, YearMonth)
    );

    PRINT 'DormReading 表创建成功';
END
ELSE
BEGIN
    PRINT 'DormReading 表已存在，跳过创建';
END
GO

-- ============================================================
-- 4. 创建 DormBill 月度账单表
-- ============================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'DormBill')
BEGIN
    CREATE TABLE [DormBill] (
        BillID              INT PRIMARY KEY IDENTITY(1,1),
        RoomID              INT NOT NULL FOREIGN KEY REFERENCES [DormRoom](RoomID),
        OccupancyID         INT NOT NULL FOREIGN KEY REFERENCES [DormOccupancy](OccupancyID),
        YearMonth           NVARCHAR(7) NOT NULL,                -- 账单月份
        RentAmount          DECIMAL(10,2) NOT NULL DEFAULT 0,   -- 租金
        WaterAmount         DECIMAL(10,2) NOT NULL DEFAULT 0,   -- 水费（定额）
        ElectricityAmount   DECIMAL(10,2) NOT NULL DEFAULT 0,   -- 电费
        TotalAmount         DECIMAL(10,2) NOT NULL DEFAULT 0,   -- 合计
        ReadingID           INT NULL FOREIGN KEY REFERENCES [DormReading](ReadingID), -- 关联电表读数
        ReceivableID        INT NULL,                            -- 关联应收ID（生成后回写）
        Status              NVARCHAR(20) NOT NULL DEFAULT N'待确认', -- 状态：待确认/已确认/已开账/已收清
        CreateTime          DATETIME DEFAULT GETDATE(),

        CONSTRAINT UQ_DormBill_Room_Month UNIQUE (RoomID, YearMonth)
    );

    PRINT 'DormBill 表创建成功';
END
ELSE
BEGIN
    PRINT 'DormBill 表已存在，跳过创建';
END
GO

-- ============================================================
-- 5. 新增字典数据 — 宿舍相关
-- ============================================================

-- 5.1 dorm_room_type: 房型
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'dorm_room_type' AND DictCode = 'single')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive)
    VALUES
        (N'dorm_room_type', N'single',   N'单间', N'宿舍单间', 1, 1),
        (N'dorm_room_type', N'standard', N'标间', N'宿舍标间', 2, 1),
        (N'dorm_room_type', N'suite',    N'套间', N'宿舍套间', 3, 1);
    PRINT '字典 dorm_room_type 插入成功';
END
GO

-- 5.2 dorm_room_status: 房间状态
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'dorm_room_status' AND DictCode = 'vacant')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive)
    VALUES
        (N'dorm_room_status', N'vacant',    N'空闲', N'房间空闲', 1, 1),
        (N'dorm_room_status', N'occupied',  N'已住', N'房间已住', 2, 1),
        (N'dorm_room_status', N'maintenance', N'维修中', N'房间维修中', 3, 1);
    PRINT '字典 dorm_room_status 插入成功';
END
GO

-- 5.3 dorm_tenant_type: 租户类型
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'dorm_tenant_type' AND DictCode = 'merchant')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive)
    VALUES
        (N'dorm_tenant_type', N'merchant', N'商户', N'商户租用', 1, 1),
        (N'dorm_tenant_type', N'personal', N'个人', N'个人租用', 2, 1);
    PRINT '字典 dorm_tenant_type 插入成功';
END
GO

-- 5.4 dorm_occupancy_status: 入住状态
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'dorm_occupancy_status' AND DictCode = 'living')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive)
    VALUES
        (N'dorm_occupancy_status', N'living',    N'在住', N'当前在住', 1, 1),
        (N'dorm_occupancy_status', N'checked_out', N'已退房', N'已退房', 2, 1);
    PRINT '字典 dorm_occupancy_status 插入成功';
END
GO

-- 5.5 dorm_bill_status: 账单状态
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'dorm_bill_status' AND DictCode = 'pending')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive)
    VALUES
        (N'dorm_bill_status', N'pending',    N'待确认', N'账单待确认', 1, 1),
        (N'dorm_bill_status', N'confirmed',  N'已确认', N'账单已确认', 2, 1),
        (N'dorm_bill_status', N'invoiced',   N'已开账', N'已生成应收', 3, 1),
        (N'dorm_bill_status', N'paid',       N'已收清', N'账单已收清', 4, 1);
    PRINT '字典 dorm_bill_status 插入成功';
END
GO

-- ============================================================
-- 6. 新增费用项 — 宿舍收入
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'expense_item_income' AND DictCode = 'dorm_rent')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive)
    VALUES
        (N'expense_item_income', N'dorm_rent',   N'宿舍租金', N'宿舍房间月租金', 8, 1),
        (N'expense_item_income', N'dorm_water',  N'宿舍水费', N'宿舍水费定额', 9, 1),
        (N'expense_item_income', N'dorm_elec',   N'宿舍电费', N'宿舍电费按表计收', 10, 1);
    PRINT '宿舍费用项插入成功';
END
GO

-- ============================================================
-- 7. 新增客户类型 — 宿舍个人
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'customer_type' AND DictCode = 'dorm_personal')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive)
    VALUES (N'customer_type', N'dorm_personal', N'宿舍个人', N'宿舍个人租户', 5, 1);
    PRINT '客户类型 宿舍个人 插入成功';
END
GO

-- ============================================================
-- 8. 新增权限 dorm_manage
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM Permission WHERE PermissionCode = 'dorm_manage')
BEGIN
    INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, IsActive)
    VALUES (N'宿舍管理', N'dorm_manage', N'管理宿舍房间、入住、抄表和账单', N'市场管理', 1);
    PRINT '权限 dorm_manage 插入成功';
END
GO

-- 给管理员角色赋权
DECLARE @AdminRoleID INT = (SELECT TOP 1 RoleID FROM Role WHERE RoleCode = 'admin');
DECLARE @DormPermID INT = (SELECT PermissionID FROM Permission WHERE PermissionCode = 'dorm_manage');
IF @AdminRoleID IS NOT NULL AND @DormPermID IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM RolePermission WHERE RoleID = @AdminRoleID AND PermissionID = @DormPermID)
BEGIN
    INSERT INTO RolePermission (RoleID, PermissionID) VALUES (@AdminRoleID, @DormPermID);
    PRINT '管理员角色已赋权 dorm_manage';
END
GO

-- 给工作人员角色赋权
DECLARE @StaffRoleID INT = (SELECT TOP 1 RoleID FROM Role WHERE RoleCode = 'staff');
IF @StaffRoleID IS NOT NULL AND @DormPermID IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM RolePermission WHERE RoleID = @StaffRoleID AND PermissionID = @DormPermID)
BEGIN
    INSERT INTO RolePermission (RoleID, PermissionID) VALUES (@StaffRoleID, @DormPermID);
    PRINT '工作人员角色已赋权 dorm_manage';
END
GO

PRINT '宿舍管理模块迁移完成！';
GO
