-- ============================================================
-- 工资管理模块迁移脚本
-- 1. 创建 SalaryProfile 员工工资档案表
-- 2. 创建 SalaryRecord 月度工资单表
-- 3. 新增字典数据（工资项、工资状态）
-- 4. 新增权限数据
-- 可重复执行（IF NOT EXISTS 判断）
-- ============================================================

USE [hf_metalmarket];
GO

-- ============================================================
-- 1. 创建 SalaryProfile 员工工资档案表
-- ============================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'SalaryProfile')
BEGIN
    CREATE TABLE [SalaryProfile] (
        ProfileID       INT PRIMARY KEY IDENTITY(1,1),
        UserID          INT NOT NULL FOREIGN KEY REFERENCES [User](UserID),
        BaseSalary      DECIMAL(12,2) DEFAULT 0,       -- 基本工资
        PostSalary      DECIMAL(12,2) DEFAULT 0,       -- 岗位工资
        Subsidy         DECIMAL(12,2) DEFAULT 0,       -- 补贴
        Insurance       DECIMAL(12,2) DEFAULT 0,       -- 社保个人部分
        HousingFund     DECIMAL(12,2) DEFAULT 0,       -- 公积金个人部分
        EffectiveDate   DATE NOT NULL,                 -- 生效日期
        Status          NVARCHAR(20) DEFAULT N'有效',   -- 状态：有效/停用
        Description     NVARCHAR(500) NULL,            -- 备注
        CreateTime      DATETIME DEFAULT GETDATE(),
        UpdateTime      DATETIME NULL
    );

    -- 唯一约束：同一用户同一时间只有一个有效的工资档案
    CREATE UNIQUE INDEX IX_SalaryProfile_User_Effective
        ON [SalaryProfile](UserID, EffectiveDate);

    PRINT 'SalaryProfile 表创建成功';
END
ELSE
BEGIN
    PRINT 'SalaryProfile 表已存在，跳过创建';
END
GO

-- ============================================================
-- 2. 创建 SalaryRecord 月度工资单表
-- ============================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'SalaryRecord')
BEGIN
    CREATE TABLE [SalaryRecord] (
        RecordID        INT PRIMARY KEY IDENTITY(1,1),
        UserID          INT NOT NULL FOREIGN KEY REFERENCES [User](UserID),
        YearMonth       NVARCHAR(7) NOT NULL,           -- 工资月份 YYYY-MM
        BaseSalary      DECIMAL(12,2) DEFAULT 0,       -- 基本工资
        PostSalary      DECIMAL(12,2) DEFAULT 0,       -- 岗位工资
        Subsidy         DECIMAL(12,2) DEFAULT 0,       -- 补贴
        OvertimePay     DECIMAL(12,2) DEFAULT 0,       -- 加班费
        Bonus           DECIMAL(12,2) DEFAULT 0,       -- 奖金
        OtherIncome     DECIMAL(12,2) DEFAULT 0,       -- 其他收入
        GrossPay        DECIMAL(12,2) DEFAULT 0,       -- 应发合计（自动计算）
        Insurance       DECIMAL(12,2) DEFAULT 0,       -- 社保扣款
        HousingFund     DECIMAL(12,2) DEFAULT 0,       -- 公积金扣款
        Tax             DECIMAL(12,2) DEFAULT 0,       -- 个税
        Deduction       DECIMAL(12,2) DEFAULT 0,       -- 其他扣款
        TotalDeduction  DECIMAL(12,2) DEFAULT 0,       -- 扣款合计（自动计算）
        NetPay          DECIMAL(12,2) DEFAULT 0,       -- 实发合计（自动计算）
        WorkDays        INT DEFAULT 0,                 -- 应出勤天数
        ActualDays      INT DEFAULT 0,                 -- 实出勤天数
        Status          NVARCHAR(20) DEFAULT N'待审核', -- 状态：待审核/已审核/已发放
        PayableID       INT NULL,                       -- 关联应付ID（发放后填入）
        ApprovedBy      INT NULL FOREIGN KEY REFERENCES [User](UserID), -- 审核人
        ApprovedTime    DATETIME NULL,                  -- 审核时间
        Description     NVARCHAR(500) NULL,             -- 备注
        CreateTime      DATETIME DEFAULT GETDATE(),
        UpdateTime      DATETIME NULL,

        -- 同一用户同一月份只能有一条工资记录
        CONSTRAINT UQ_SalaryRecord_User_Month UNIQUE (UserID, YearMonth)
    );

    PRINT 'SalaryRecord 表创建成功';
END
ELSE
BEGIN
    PRINT 'SalaryRecord 表已存在，跳过创建';
END
GO

-- ============================================================
-- 3. 新增字典数据 — 工资相关
-- ============================================================

-- 3.1 salary_status: 工资单状态
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'salary_status' AND DictCode = 'pending')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive)
    VALUES
        (N'salary_status', N'pending',  N'待审核', N'工资单待审核', 1, 1),
        (N'salary_status', N'approved', N'已审核', N'工资单已审核', 2, 1),
        (N'salary_status', N'paid',     N'已发放', N'工资已发放',   3, 1);
    PRINT '字典 salary_status 插入成功';
END
GO

-- 3.2 salary_profile_status: 工资档案状态
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'salary_profile_status' AND DictCode = 'active')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive)
    VALUES
        (N'salary_profile_status', N'active',   N'有效', N'工资档案有效', 1, 1),
        (N'salary_profile_status', N'inactive', N'停用', N'工资档案停用', 2, 1);
    PRINT '字典 salary_profile_status 插入成功';
END
GO

-- 3.3 在支出方向费用项中增加"工资"（如果不存在）
IF NOT EXISTS (SELECT 1 FROM Sys_Dictionary WHERE DictType = 'expense_item_expend' AND DictName = N'工资')
BEGIN
    INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive)
    VALUES (N'expense_item_expend', N'salary', N'工资', N'员工工资发放', 1, 1);
    PRINT '费用项 工资 插入成功';
END
GO

-- ============================================================
-- 4. 新增权限
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM Permission WHERE PermissionCode = 'salary_manage')
BEGIN
    INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, IsActive)
    VALUES (N'工资管理', N'salary_manage', N'管理员工工资档案、月度核算和发放', N'财务管理', 1);
    PRINT '权限 salary_manage 插入成功';
END
GO

-- 给管理员角色赋权
DECLARE @AdminRoleID INT = (SELECT TOP 1 RoleID FROM Role WHERE RoleCode = 'admin');
DECLARE @PermID INT = (SELECT PermissionID FROM Permission WHERE PermissionCode = 'salary_manage');
IF @AdminRoleID IS NOT NULL AND @PermID IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM RolePermission WHERE RoleID = @AdminRoleID AND PermissionID = @PermID)
BEGIN
    INSERT INTO RolePermission (RoleID, PermissionID) VALUES (@AdminRoleID, @PermID);
    PRINT '管理员角色已赋权 salary_manage';
END
GO

-- 给工作人员角色赋权
DECLARE @StaffRoleID INT = (SELECT TOP 1 RoleID FROM Role WHERE RoleCode = 'staff');
IF @StaffRoleID IS NOT NULL AND @PermID IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM RolePermission WHERE RoleID = @StaffRoleID AND PermissionID = @PermID)
BEGIN
    INSERT INTO RolePermission (RoleID, PermissionID) VALUES (@StaffRoleID, @PermID);
    PRINT '工作人员角色已赋权 salary_manage';
END
GO

PRINT '工资管理模块迁移完成！';
GO
