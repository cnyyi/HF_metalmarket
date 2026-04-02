# 宏发金属交易市场管理系统 - 需求规格说明书（工程版）

## 文档信息

| 项目名称 | 宏发金属交易市场管理系统 |
| ---- | ------------ |
| 文档版本 | V2.0         |
| 编写日期 | 2026-03-30   |
| 文档状态 | 工程版          |
| 编写人员 | 系统分析员        |

***

## 1. 项目概述

### 1.1 项目背景

宏发金属交易市场管理系统是一个面向金属交易市场的企业内部管理系统，旨在实现市场日常管理的数字化、智能化。系统涵盖用户管理、商户管理、地块管理、合同管理、水电计费、财务管理和磅秤管理等核心业务功能。

### 1.2 项目目标

- 实现市场管理业务流程的数字化
- 提高管理效率，降低人工成本
- 规范业务操作，减少人为错误
- 提供实时数据分析和报表功能
- 实现财务数据的精准管理

### 1.3 目标用户

- **系统管理员**：负责系统配置、用户管理、权限分配
- **工作人员**：负责日常业务操作，如商户管理、合同管理等
- **商户**：查看自己的合同、账单、水电使用情况等信息

***

## 2. 全局约束（强制执行）

### 2.1 技术栈

- **后端框架**：Flask 2.3.3
- **数据库**：SQL Server（pyodbc）+ **SQLAlchemy 2.0.48**
- **前端框架**：Bootstrap 5+jQuery(4.0.0)
- **认证**：Flask-Login
- **Python版本**：3.8+

### 2.2 架构规范

```
项目结构：
├── app/
│   ├── routes/              # 路由层：只处理请求
│   │   ├── __init__.py      # 蓝图注册
│   │   ├── auth.py          # 认证路由
│   │   ├── user.py          # 用户管理路由
│   │   ├── merchant.py      # 商户管理路由
│   │   ├── plot.py          # 地块管理路由
│   │   ├── contract.py      # 合同管理路由
│   │   ├── utility.py       # 水电计费路由
│   │   ├── finance.py       # 财务管理路由
│   │   └── scale.py         # 磅秤管理路由
│   ├── services/            # 业务层：业务逻辑
│   │   ├── auth_service.py  # 认证服务
│   │   ├── user_service.py  # 用户服务
│   │   └── merchant_service.py # 商户服务
│   ├── models/              # 数据层：数据库操作
│   │   ├── user.py          # 用户模型
│   │   ├── role.py          # 角色模型
│   │   ├── permission.py    # 权限模型
│   │   └── merchant.py      # 商户模型
│   ├── forms/               # 表单定义
│   │   ├── auth_form.py     # 认证表单
│   │   ├── user_form.py     # 用户表单
│   │   └── merchant_form.py # 商户表单
│   └── extensions.py        # Flask扩展配置
├── utils/                   # 工具类（数据库操作等）
│   ├── database.py          # 数据库连接工具
│   ├── init_database.py     # 数据库初始化
│   └── run_sql_script.py    # SQL脚本执行
├── templates/               # HTML模板
│   ├── admin_base.html      # 管理端母版
│   ├── public_base.html     # 公用母版
│   ├── merchant_base.html   # 商户端母版
│   ├── base.html            # 基础母版
│   ├── index.html           # 首页
│   ├── auth/                # 认证模块页面
│   │   ├── login.html       # 登录页
│   │   └── register.html    # 注册页
│   ├── user/                # 用户管理页面
│   │   ├── list.html        # 用户列表
│   │   ├── add.html         # 添加用户
│   │   ├── edit.html        # 编辑用户
│   │   └── change_password.html # 修改密码
│   ├── merchant/            # 商户管理页面
│   │   ├── list.html        # 商户列表
│   │   ├── add.html         # 添加商户
│   │   └── edit.html        # 编辑商户
│   ├── plot/                # 地块管理页面
│   │   ├── list.html        # 地块列表
│   │   ├── add.html         # 添加地块
│   │   └── edit.html        # 编辑地块
│   ├── contract/            # 合同管理页面
│   │   ├── list.html        # 合同列表
│   │   ├── add.html         # 添加合同
│   │   └── edit.html        # 编辑合同
│   ├── utility/             # 水电计费页面
│   │   ├── list.html        # 水电表列表
│   │   ├── add.html         # 添加水电表
│   │   ├── edit.html        # 编辑水电表
│   │   ├── water_meter.html # 水表抄表
│   │   └── electricity_meter.html # 电表抄表
│   ├── finance/             # 财务管理页面
│   │   ├── receivable.html  # 应收账款
│   │   ├── payable.html     # 应付账款
│   │   └── cash_flow.html   # 现金流水
│   └── scale/               # 磅秤管理页面
│       ├── list.html        # 磅秤列表
│       └── records.html     # 过磅记录
├── static/                  # 静态资源（CSS、JS、图片等）
├── app.py                   # 应用入口
└── config.py                # 配置文件（可选）
```
    【强制执行 - 架构隔离规则】
    1. 严禁在 routes 层中出现以下内容：
    - SQL语句（SELECT / INSERT / UPDATE / DELETE）
    - pyodbc / SQLAlchemy 直接操作
    - cursor.execute / session.execute
    - 数据库连接代码
    2. routes 层职责仅限：
    - 接收请求（request）
    - 参数校验（简单校验）
    - 调用 Service 层
    - 返回 JSON / 渲染模板
    3. 所有数据库操作必须放在：
    → models 层 或 services 层
    4. 所有业务逻辑必须放在：
    → services 层
    5. 如果生成的代码中 routes 出现 SQL：
    → 判定为错误代码，必须重写
    6. 正确调用结构必须如下：
    routes:
        result = PlotService.create_plot(data)
    services:
        调用 models 完成数据库操作
    models:
        只负责数据库 CRUD
    7. 不允许跳过 service 层直接访问数据库

### 2.3 开发规则

1. **HTML规则**：所有HTML必须在 `templates/` 目录
2. **路由规则**：必须使用 Blueprint，一个模块一个 Blueprint
3. **SQL规则**：所有SQL使用参数化查询，禁止拼接SQL
4. **返回格式**：所有接口返回统一JSON格式
5. **文件管理**：所有文件必须走 `/uploads/`，数据库存路径，不存文件
6. **表单提交**：所有表单提交必须使用 jQuery Ajax 提交，禁止使用表单提交
7. 创建及编辑功能：小于等于5个输入项使用模态窗口在列表页面打开，大于5个输入项使用独立页面打开
8. **功能实现**：所有功能的实现（含页面+后端）均按照Spec进行，有模糊的地方，需要与我沟通确认
9. 统一字典管理：所有字典数据均从Sys_Dictionary表动态获取，禁止硬编码（如商户类型、业务类型等）

***

## 3. 统一返回格式

所有接口必须遵守以下返回格式：

```json
{
  "code": 0,        // 0: 成功, 1: 失败
  "message": "success",
  "data": {}        // 返回数据
}
```

**错误返回示例**：

```json
{
  "code": 1,
  "message": "用户名或密码错误",
  "data": null
}
```

***

## 4. 数据库结构（基于现有项目）

### 4.1 用户表 (User)

```sql
CREATE TABLE User (
    UserID INT PRIMARY KEY IDENTITY,
    Username VARCHAR(50) NOT NULL,
    Password NVARCHAR(255) NOT NULL,
    RealName NVARCHAR(50) NULL,
    Phone NVARCHAR(20) NULL,
    Email NVARCHAR(100) NULL,
    IsActive BIT DEFAULT ((1)) NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    UpdateTime DATETIME NULL,
    LastLoginTime DATETIME NULL,
    WeChatOpenID NVARCHAR(100) NULL,
    MerchantID INT NULL,
    FOREIGN KEY (MerchantID) REFERENCES User(MerchantID),
    FOREIGN KEY (MerchantID) REFERENCES User(MerchantID)
);
```

### 4.2 角色表 (Role)

```sql
CREATE TABLE Role (
    RoleID INT PRIMARY KEY IDENTITY,
    RoleName NVARCHAR(50) NOT NULL,
    RoleCode NVARCHAR(50) NOT NULL,
    Description NVARCHAR(200) NULL,
    IsActive BIT DEFAULT ((1)) NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    UpdateTime DATETIME NULL
);
```

### 4.3 权限表 (Permission)

```sql
CREATE TABLE Permission (
    PermissionID INT PRIMARY KEY IDENTITY,
    PermissionName NVARCHAR(100) NOT NULL,
    PermissionCode NVARCHAR(100) NOT NULL,
    Description NVARCHAR(200) NULL,
    ModuleName NVARCHAR(50) NULL,
    IsActive BIT DEFAULT ((1)) NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    UpdateTime DATETIME NULL
);
```

### 4.4 用户角色关联表 (UserRole)

```sql
CREATE TABLE UserRole (
    UserRoleID INT PRIMARY KEY IDENTITY,
    UserID INT NOT NULL,
    RoleID INT NOT NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    FOREIGN KEY (UserID) REFERENCES UserRole(UserID),
    FOREIGN KEY (RoleID) REFERENCES UserRole(RoleID)
);
```

### 4.5 角色权限关联表 (RolePermission)

```sql
CREATE TABLE RolePermission (
    RolePermissionID INT PRIMARY KEY IDENTITY,
    RoleID INT NOT NULL,
    PermissionID INT NOT NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    FOREIGN KEY (RoleID) REFERENCES RolePermission(RoleID),
    FOREIGN KEY (PermissionID) REFERENCES RolePermission(PermissionID)
);
```

### 4.6 商户表 (Merchant)

```sql
CREATE TABLE Merchant (
    MerchantID INT PRIMARY KEY IDENTITY,
    MerchantName NVARCHAR(100) NOT NULL,
    LegalPerson NVARCHAR(50) NOT NULL,
    ContactPerson NVARCHAR(50) NOT NULL,
    Phone NVARCHAR(20) NOT NULL,
    Address NVARCHAR(200) NULL,
    MerchantType NVARCHAR(50) NOT NULL,
    BusinessLicense NVARCHAR(100) NULL,
    TaxRegistration NVARCHAR(100) NULL,
    Description NVARCHAR(500) NULL,
    Status VARCHAR(50) DEFAULT ('??') NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    UpdateTime DATETIME NULL,
    BusinessType NVARCHAR(100) NULL
);
```

### 4.7 地块表 (Plot)

```sql
CREATE TABLE Plot (
    PlotID INT PRIMARY KEY IDENTITY,
    PlotNumber VARCHAR(50) NOT NULL,
    PlotName NVARCHAR(100) NOT NULL,
    Area DECIMAL(10,2) NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,
    TotalPrice DECIMAL(10,2) NOT NULL,
    Location NVARCHAR(200) NULL,
    Description NVARCHAR(500) NULL,
    ImagePath NVARCHAR(255) NULL,
    Status VARCHAR(50) DEFAULT ('??') NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    UpdateTime DATETIME NULL
);
```

### 4.8 合同表 (Contract)

```sql
CREATE TABLE Contract (
    ContractID INT PRIMARY KEY IDENTITY,
    ContractNumber VARCHAR(50) NOT NULL,
    MerchantID INT NOT NULL,
    ContractName NVARCHAR(100) NOT NULL,
    StartDate DATETIME NOT NULL,
    EndDate DATETIME NOT NULL,
    ContractAmount DECIMAL(12,2) NOT NULL,
    AmountReduction DECIMAL(12,2) DEFAULT ((0)) NULL,
    ActualAmount DECIMAL(12,2) NOT NULL,
    PaymentMethod NVARCHAR(50) NOT NULL,
    ContractPeriodYear INT NOT NULL,
    BusinessType NVARCHAR(50) NOT NULL,
    Description NVARCHAR(500) NULL,
    Status VARCHAR(50) DEFAULT ('??') NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    UpdateTime DATETIME NULL,
    FOREIGN KEY (MerchantID) REFERENCES Contract(MerchantID)
);
```

### 4.9 合同地块关联表 (ContractPlot)

```sql
CREATE TABLE ContractPlot (
    ContractPlotID INT PRIMARY KEY IDENTITY,
    ContractID INT NOT NULL,
    PlotID INT NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,
    Area DECIMAL(10,2) NOT NULL,
    MonthlyPrice DECIMAL(10,2) NOT NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    FOREIGN KEY (ContractID) REFERENCES ContractPlot(ContractID),
    FOREIGN KEY (PlotID) REFERENCES ContractPlot(PlotID)
);
```

### 4.10 电表信息表 (ElectricityMeter)

```sql
CREATE TABLE ElectricityMeter (
    MeterID INT PRIMARY KEY IDENTITY,
    MeterNumber VARCHAR(50) NOT NULL,
    MeterType VARCHAR(50) DEFAULT ('electricity') NOT NULL,
    InstallationLocation NVARCHAR(200) NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,
    LastReading DECIMAL(10,2) DEFAULT ((0)) NULL,
    CurrentReading DECIMAL(10,2) DEFAULT ((0)) NULL,
    Status VARCHAR(50) DEFAULT ('??') NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    UpdateTime DATETIME NULL
);
```

### 4.11 水表信息表 (WaterMeter)

```sql
CREATE TABLE WaterMeter (
    MeterID INT PRIMARY KEY IDENTITY,
    MeterNumber VARCHAR(50) NOT NULL,
    MeterType VARCHAR(50) DEFAULT ('water') NOT NULL,
    InstallationLocation NVARCHAR(200) NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,
    LastReading DECIMAL(10,2) DEFAULT ((0)) NULL,
    CurrentReading DECIMAL(10,2) DEFAULT ((0)) NULL,
    Status VARCHAR(50) DEFAULT ('??') NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    UpdateTime DATETIME NULL
);
```

### 4.12 合同电表关联表 (ContractElectricityMeter)

```sql
CREATE TABLE ContractElectricityMeter (
    ContractMeterID INT PRIMARY KEY IDENTITY,
    ContractID INT NOT NULL,
    MeterID INT NOT NULL,
    StartReading DECIMAL(10,2) NOT NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    FOREIGN KEY (ContractID) REFERENCES ContractElectricityMeter(ContractID),
    FOREIGN KEY (MeterID) REFERENCES ContractElectricityMeter(MeterID)
);
```

### 4.13 合同水表关联表 (ContractWaterMeter)

```sql
CREATE TABLE ContractWaterMeter (
    ContractMeterID INT PRIMARY KEY IDENTITY,
    ContractID INT NOT NULL,
    MeterID INT NOT NULL,
    StartReading DECIMAL(10,2) NOT NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    FOREIGN KEY (ContractID) REFERENCES ContractWaterMeter(ContractID),
    FOREIGN KEY (MeterID) REFERENCES ContractWaterMeter(MeterID)
);
```

### 4.14 换表记录表 (MeterChangeRecord)

```sql
CREATE TABLE MeterChangeRecord (
    ChangeRecordID INT PRIMARY KEY IDENTITY,
    OldMeterID INT NOT NULL,
    NewMeterID INT NOT NULL,
    MeterType NVARCHAR(50) NOT NULL,
    ContractID INT NOT NULL,
    MerchantID INT NOT NULL,
    OldMeterLastReading DECIMAL(10,2) NOT NULL,
    NewMeterStartReading DECIMAL(10,2) NOT NULL,
    ChangeDate DATETIME DEFAULT (getdate()) NULL,
    Reason NVARCHAR(500) NULL,
    CreatedBy INT NOT NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    FOREIGN KEY (ContractID) REFERENCES MeterChangeRecord(ContractID),
    FOREIGN KEY (MerchantID) REFERENCES MeterChangeRecord(MerchantID),
    FOREIGN KEY (CreatedBy) REFERENCES MeterChangeRecord(CreatedBy)
);
```

### 4.15 水电费抄表记录表 (UtilityReading)

```sql
CREATE TABLE UtilityReading (
    ReadingID INT PRIMARY KEY IDENTITY,
    MeterID INT NOT NULL,
    MeterType NVARCHAR(50) NOT NULL,
    ContractID INT NOT NULL,
    MerchantID INT NOT NULL,
    LastReading DECIMAL(10,2) NOT NULL,
    CurrentReading DECIMAL(10,2) NOT NULL,
    Usage DECIMAL(10,2) NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,
    TotalAmount DECIMAL(12,2) NOT NULL,
    ReadingDate DATETIME DEFAULT (getdate()) NULL,
    ReadingMonth NVARCHAR(7) NOT NULL,
    CreatedBy INT NOT NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    FOREIGN KEY (ContractID) REFERENCES UtilityReading(ContractID),
    FOREIGN KEY (MerchantID) REFERENCES UtilityReading(MerchantID),
    FOREIGN KEY (CreatedBy) REFERENCES UtilityReading(CreatedBy)
);
```

### 4.16 应收账款表 (Receivable)

```sql
CREATE TABLE Receivable (
    ReceivableID INT PRIMARY KEY IDENTITY,
    MerchantID INT NOT NULL,
    ExpenseTypeID INT NOT NULL,
    Amount DECIMAL(12,2) NOT NULL,
    Description NVARCHAR(500) NULL,
    DueDate DATETIME NOT NULL,
    Status VARCHAR(50) DEFAULT ('???') NULL,
    PaidAmount DECIMAL(12,2) DEFAULT ((0)) NULL,
    RemainingAmount DECIMAL(12,2) NOT NULL,
    ReferenceID INT NULL,
    ReferenceType NVARCHAR(50) NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    UpdateTime DATETIME NULL,
    FOREIGN KEY (MerchantID) REFERENCES Receivable(MerchantID),
    FOREIGN KEY (ExpenseTypeID) REFERENCES Receivable(ExpenseTypeID)
);
```

### 4.17 应付账款表 (Payable)

```sql
CREATE TABLE Payable (
    PayableID INT PRIMARY KEY IDENTITY,
    VendorName NVARCHAR(100) NOT NULL,
    ExpenseTypeID INT NOT NULL,
    Amount DECIMAL(12,2) NOT NULL,
    Description NVARCHAR(500) NULL,
    DueDate DATETIME NOT NULL,
    Status VARCHAR(50) DEFAULT ('???') NULL,
    PaidAmount DECIMAL(12,2) DEFAULT ((0)) NULL,
    RemainingAmount DECIMAL(12,2) NOT NULL,
    ReferenceID INT NULL,
    ReferenceType NVARCHAR(50) NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    UpdateTime DATETIME NULL,
    FOREIGN KEY (ExpenseTypeID) REFERENCES Payable(ExpenseTypeID)
);
```

### 4.18 现金流水表 (CashFlow)

```sql
CREATE TABLE CashFlow (
    CashFlowID INT PRIMARY KEY IDENTITY,
    Amount DECIMAL(12,2) NOT NULL,
    Direction NVARCHAR(20) NOT NULL,
    ExpenseTypeID INT NOT NULL,
    Description NVARCHAR(500) NULL,
    TransactionDate DATETIME DEFAULT (getdate()) NULL,
    ReferenceID INT NULL,
    ReferenceType NVARCHAR(50) NULL,
    CreatedBy INT NOT NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    FOREIGN KEY (ExpenseTypeID) REFERENCES CashFlow(ExpenseTypeID),
    FOREIGN KEY (CreatedBy) REFERENCES CashFlow(CreatedBy)
);
```

### 4.19 收款记录表 (CollectionRecord)

```sql
CREATE TABLE CollectionRecord (
    CollectionRecordID INT PRIMARY KEY IDENTITY,
    ReceivableID INT NOT NULL,
    MerchantID INT NOT NULL,
    Amount DECIMAL(12,2) NOT NULL,
    PaymentMethod NVARCHAR(50) NOT NULL,
    TransactionDate DATETIME DEFAULT (getdate()) NULL,
    Description NVARCHAR(500) NULL,
    CreatedBy INT NOT NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    FOREIGN KEY (ReceivableID) REFERENCES CollectionRecord(ReceivableID),
    FOREIGN KEY (MerchantID) REFERENCES CollectionRecord(MerchantID),
    FOREIGN KEY (CreatedBy) REFERENCES CollectionRecord(CreatedBy)
);
```

### 4.20 付款记录表 (PaymentRecord)

```sql
CREATE TABLE PaymentRecord (
    PaymentRecordID INT PRIMARY KEY IDENTITY,
    PayableID INT NOT NULL,
    VendorName NVARCHAR(100) NOT NULL,
    Amount DECIMAL(12,2) NOT NULL,
    PaymentMethod NVARCHAR(50) NOT NULL,
    TransactionDate DATETIME DEFAULT (getdate()) NULL,
    Description NVARCHAR(500) NULL,
    CreatedBy INT NOT NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    FOREIGN KEY (PayableID) REFERENCES PaymentRecord(PayableID),
    FOREIGN KEY (CreatedBy) REFERENCES PaymentRecord(CreatedBy)
);
```

### 4.21 磅秤信息表 (Scale)

```sql
CREATE TABLE Scale (
    ScaleID INT PRIMARY KEY IDENTITY,
    ScaleNumber VARCHAR(50) NOT NULL,
    ScaleName NVARCHAR(100) NOT NULL,
    Location NVARCHAR(200) NOT NULL,
    MaximumCapacity DECIMAL(10,2) NOT NULL,
    Unit NVARCHAR(10) NOT NULL,
    Status VARCHAR(50) DEFAULT ('??') NULL,
    Description NVARCHAR(500) NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    UpdateTime DATETIME NULL
);
```

### 4.22 过磅记录表 (ScaleRecord)

```sql
CREATE TABLE ScaleRecord (
    ScaleRecordID INT PRIMARY KEY IDENTITY,
    ScaleID INT NOT NULL,
    MerchantID INT NOT NULL,
    GrossWeight DECIMAL(10,2) NOT NULL,
    TareWeight DECIMAL(10,2) NOT NULL,
    NetWeight DECIMAL(10,2) NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,
    TotalAmount DECIMAL(12,2) NOT NULL,
    LicensePlate NVARCHAR(50) NULL,
    ProductName NVARCHAR(100) NULL,
    Operator NVARCHAR(50) NOT NULL,
    ScaleTime DATETIME DEFAULT (getdate()) NULL,
    Description NVARCHAR(500) NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    FOREIGN KEY (ScaleID) REFERENCES ScaleRecord(ScaleID),
    FOREIGN KEY (MerchantID) REFERENCES ScaleRecord(MerchantID)
);
```

### 4.23 系统字典表 (Sys\_Dictionary)

```sql
CREATE TABLE Sys_Dictionary (
    DictID INT PRIMARY KEY IDENTITY,
    DictType NVARCHAR(50) NOT NULL,
    DictCode NVARCHAR(50) NOT NULL,
    DictName NVARCHAR(100) NOT NULL,
    Description NVARCHAR(200) NULL,
    SortOrder INT DEFAULT ((0)) NULL,
    IsActive BIT DEFAULT ((1)) NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    UpdateTime DATETIME NULL
);
```

### 4.24 文件管理表 (FileAttachment)

```sql
CREATE TABLE FileAttachment (
    FileID INT PRIMARY KEY IDENTITY,
    FileName NVARCHAR(200) NOT NULL,
    OriginalName NVARCHAR(200) NULL,
    FilePath NVARCHAR(500) NOT NULL,
    FileSize INT NULL,
    FileType NVARCHAR(50) NULL,
    BizType NVARCHAR(50) NOT NULL,
    BizID INT NULL,
    CreateBy INT NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL
);
```

### 4.25 费用类型表 (ExpenseType)

```sql
CREATE TABLE ExpenseType (
    ExpenseTypeID INT PRIMARY KEY IDENTITY,
    ExpenseTypeName VARCHAR(100) NOT NULL,
    ExpenseTypeCode VARCHAR(50) NOT NULL,
    ExpenseDirection NVARCHAR(20) NOT NULL,
    Description NVARCHAR(200) NULL,
    IsActive BIT DEFAULT ((1)) NULL,
    CreateTime DATETIME DEFAULT (getdate()) NULL,
    UpdateTime DATETIME NULL
);
```

状态机定义

### 5.1 合同状态流转

```
草稿 → 生效中 → 已到期
           ↓
         已终止
```

**状态说明**：

- **草稿**：合同创建但未生效
- **生效中**：合同正在执行
- **已到期**：合同到期
- **已终止**：合同提前终止

### 5.2 地块状态流转

```
空闲 → 已出租 → 维护中
  ↑       ↓
  └───────┘
```

**状态说明**：

- **空闲**：地块未出租
- **已出租**：地块已出租
- **维护中**：地块维护中

### 5.3 应收账款状态

```
未支付 → 部分支付 → 已支付
```

**状态说明**：

- **未支付**：未收到款项
- **部分支付**：部分收到款项
- **已支付**：全部收到款项

### 5.4 商户状态流转

```
空闲 ⇄ 在租
```

**状态说明**：

- **空闲**：商户无有效合同
- **在租**：商户有有效合同

**自动化规则**：

- 商户有有效合同 → 自动变为"在租"
- 商户无合同 → 自动变为"空闲"

***

## 6. 业务规则

### 6.1 合同约束规则

| 规则编号   | 规则名称   | 规则描述                       | 触发时机     |
| ------ | ------ | -------------------------- | -------- |
| BR-001 | 地块唯一性  | 一个地块同一时间只能属于一个有效合同         | 创建/编辑合同时 |
| BR-002 | 时间不重叠  | 同一地块的合同时间不能重叠              | 创建/编辑合同时 |
| BR-003 | 合同编号唯一 | 合同编号必须唯一，格式：HT-YYYYMMDD-序号 | 创建合同时    |
| BR-004 | 租金自动计算 | 租金 = Σ(地块面积 × 地块单价)        | 创建/编辑合同时 |

**合同时间重叠检查逻辑**：

```
新合同开始日期 < 已有合同结束日期 AND 新合同结束日期 > 已有合同开始日期
→ 存在重叠，不允许创建
```

### 6.2 抄表规则

| 规则编号   | 规则名称 | 规则描述              | 触发时机  |
| ------ | ---- | ----------------- | ----- |
| BR-005 | 抄表周期 | 按月抄表，每月一次         | 抄表录入时 |
| BR-006 | 读数递增 | 当前读数 ≥ 上次读数，不允许倒退 | 抄表录入时 |
| BR-007 | 用量计算 | 用量 = 当前读数 - 上次读数  | 抄表录入时 |
| BR-008 | 费用计算 | 金额 = 用量 × 单价      | 抄表录入时 |

**抄表校验逻辑**：

```
IF 当前读数 < 上次读数 THEN
    提示错误："当前读数不能小于上次读数（上次读数：XXX）"
    不允许保存
END IF
```

### 6.3 商户状态自动化规则

| 规则编号   | 规则名称   | 规则描述                       | 触发时机     |
| ------ | ------ | -------------------------- | -------- |
| BR-009 | 状态自动更新 | 商户状态根据合同状态自动更新             | 合同状态变更时  |
| BR-010 | 在租判定   | 商户有"生效中"状态的合同 → 商户状态变为"在租" | 合同生效时    |
| BR-011 | 空闲判定   | 商户无"生效中"状态的合同 → 商户状态变为"空闲" | 合同到期/终止时 |

**商户状态自动更新逻辑**：

```
ON 合同状态变更:
    IF 合同状态 = "生效中" THEN
        UPDATE 商户状态 = "在租"
    ELSE IF 合同状态 IN ("已到期", "已终止") THEN
        IF 商户无其他生效中合同 THEN
            UPDATE 商户状态 = "空闲"
        END IF
    END IF
```

### 6.4 地块状态联动规则

| 规则编号   | 规则名称 | 规则描述                    | 触发时机     |
| ------ | ---- | ----------------------- | -------- |
| BR-012 | 地块出租 | 地块被加入生效合同 → 地块状态变为"已出租" | 合同生效时    |
| BR-013 | 地块释放 | 地块无生效合同 → 地块状态变为"空闲"    | 合同到期/终止时 |

### 6.5 应收账款规则

| 规则编号   | 规则名称 | 规则描述                                 | 触发时机  |
| ------ | ---- | ------------------------------------ | ----- |
| BR-014 | 自动生成 | 合同生效时自动生成应收账款记录                      | 合同生效时 |
| BR-015 | 状态更新 | 核销后更新应收账款状态                          | 核销记录时 |
| BR-016 | 部分支付 | 0 < PaidAmount < Amount → 状态变为"部分支付" | 核销记录时 |
| BR-017 | 全部支付 | PaidAmount = Amount → 状态变为"已支付"      | 核销记录时 |

**核销流程**：

```
1. 创建收款记录 (Receipt)
   - 记录实际收到的款项
   
2. 选择待核销的应收账款
   - 可选择一笔或多笔应收账款
   
3. 创建核销记录 (ReceivableWriteOff)
   - 绑定收款ID和应收ID
   - 记录核销金额
   
4. 更新应收账款
   - PaidAmount = PaidAmount + 核销金额
   - RemainAmount = Amount - PaidAmount
   - 更新状态（未支付/部分支付/已支付）
```

**核销约束**：

- 单笔核销金额 ≤ 收款记录剩余金额
- 单笔核销金额 ≤ 应收账款剩余金额
- 核销总额不能超过收款金额

***

## 7. 接口定义（基于现有项目路由）

### 7.1 用户认证模块

#### 7.1.1 用户登录

**路由**：`GET/POST /auth/login`

**页面**：`templates/auth/login.html`

**功能**：

- 显示登录表单（GET）
- 处理登录请求（POST）
- 验证用户名和密码
- 创建用户会话

**表单字段**：

- username: 用户名
- password: 密码

#### 7.1.2 用户登出

**路由**：`GET /auth/logout`

**功能**：

- 清除用户会话
- 重定向到登录页面

#### 7.1.3 用户注册

**路由**：`GET/POST /auth/register`

**页面**：`templates/auth/register.html`

**功能**：

- 显示注册表单（GET）
- 处理注册请求（POST）

#### 7.1.4 首页

**路由**：`GET /auth/`

**页面**：`templates/index.html`

**功能**：

- 显示系统首页
- 显示功能菜单

***

### 7.2 用户管理模块

#### 7.2.1 用户列表

**路由**：`GET /user/list`

**页面**：`templates/user/list.html`

**参数**：

- page: 页码（默认1）
- search: 搜索关键词（可选）

**功能**：

- 显示用户列表
- 支持分页
- 支持搜索

#### 7.2.2 添加用户

**路由**：`GET/POST /user/add`

**页面**：`templates/user/add.html`

**权限**：需要 `user_manage` 权限

**表单字段**：

- username: 用户名
- real\_name: 真实姓名
- password: 密码
- confirm\_password: 确认密码
- phone: 电话
- email: 邮箱
- roles: 角色选择
- merchant\_id: 关联商户

#### 7.2.3 编辑用户

**路由**：`GET/POST /user/edit/<int:user_id>`

**页面**：`templates/user/edit.html`

**权限**：需要 `user_manage` 权限

#### 7.2.4 删除用户

**路由**：`GET /user/delete/<int:user_id>`

**权限**：需要 `user_manage` 权限

#### 7.2.5 修改密码

**路由**：`GET/POST /user/change_password`

**页面**：`templates/user/change_password.html`

**表单字段**：

- current\_password: 当前密码
- new\_password: 新密码
- confirm\_new\_password: 确认新密码

***

### 7.3 商户管理模块

#### 7.3.1 商户列表

**路由**：`GET /merchant/list`

**页面**：`templates/merchant/list.html`

**参数**：

- page: 页码（默认1）
- search: 搜索关键词（可选）

**功能**：

- 显示商户列表
- 支持分页
- 支持搜索

#### 7.3.2 添加商户

**路由**：`GET/POST /merchant/add`

**页面**：`templates/merchant/add.html`

**表单字段**：

- merchant\_name: 商户名称
- legal\_person: 法人代表
- contact\_person: 联系人
- phone: 联系电话
- address: 地址
- merchant\_type: 商户类型
- business\_license: 营业执照号
- description: 商户描述

#### 7.3.3 编辑商户

**路由**：`GET/POST /merchant/edit/<int:merchant_id>`

**页面**：`templates/merchant/edit.html`

***

### 7.4 地块管理模块

#### 7.4.1 地块列表

**路由**：`GET /plot/list`

**页面**：`templates/plot/list.html`

**功能**：

- 显示地块列表
- 显示租金计算结果

#### 7.4.2 添加地块

**路由**：`GET/POST /plot/add`

**页面**：`templates/plot/add.html`

**表单字段**：

- plot\_code: 地块编号
- plot\_name: 地块名称
- area: 面积
- price: 单价
- location: 位置
- description: 描述

#### 7.4.3 编辑地块

**路由**：`GET/POST /plot/edit/<int:plot_id>`

**页面**：`templates/plot/edit.html`

***

### 7.5 合同管理模块

#### 7.5.1 合同列表

**路由**：`GET /contract/list`

**页面**：`templates/contract/list.html`

**功能**：

- 显示合同列表
- 显示合同状态

#### 7.5.2 添加合同

**路由**：`GET/POST /contract/add`

**页面**：`templates/contract/add.html`

**表单字段**：

- merchant\_id: 商户选择
- plot\_ids: 地块选择（多选）
- start\_date: 开始日期
- end\_date: 结束日期
- description: 合同描述

**自动功能**：

- 合同编号自动生成：生成共12位，格式为"ZTHYHT"+“YYYYMMDD"+商户编号三位数字（取商户ID，不足3位的前面加0补足3位）
- 合同金额默认为0
- 合同租金默认为0
- 租金自动计算

#### 7.5.3 编辑合同

**路由**：`GET/POST /contract/edit/<int:contract_id>`

**页面**：`templates/contract/edit.html`

***

### 7.6 水电计费模块

#### 7.6.1 水电表列表

**路由**：`GET /utility/list`

**页面**：`templates/utility/list.html`

**功能**：

- 显示水电表列表
- 显示当前读数

#### 7.6.2 添加水电表

**路由**：`GET/POST /utility/add`

**页面**：`templates/utility/add.html`

#### 7.6.3 水表抄表

**路由**：`GET/POST /utility/water_meter`

**页面**：`templates/utility/water_meter.html`

**功能**：

- 录入水表读数
- 自动计算用量和费用

#### 7.6.4 电表抄表

**路由**：`GET/POST /utility/electricity_meter`

**页面**：`templates/utility/electricity_meter.html`

**功能**：

- 录入电表读数
- 自动计算用量和费用

***

### 7.7 财务管理模块

#### 7.7.1 应收账款

**路由**：`GET /finance/receivable`

**页面**：`templates/finance/receivable.html`

**功能**：

- 显示应收账款列表
- 显示收款状态

#### 7.7.2 应付账款

**路由**：`GET /finance/payable`

**页面**：`templates/finance/payable.html`

#### 7.7.3 现金流水

**路由**：`GET /finance/cash_flow`

**页面**：`templates/finance/cash_flow.html`

#### 7.7.4 财务列表（重定向）

**路由**：`GET /finance/list`

**功能**：

- 重定向到 `/finance/receivable`

***

### 7.8 磅秤管理模块

#### 7.8.1 磅秤列表

**路由**：`GET /scale/list`

**页面**：`templates/scale/list.html`

#### 7.8.2 过磅记录

**路由**：`GET /scale/records`

**页面**：`templates/scale/records.html`

**功能**：

- 显示过磅记录列表
- 显示净重计算结果

***

## 8. 页面结构

### 8.1 管理端页面

```
/auth/                        # 系统首页（仪表盘）
/auth/login                   # 登录页面
/auth/register                # 注册页面
/auth/logout                  # 登出

/user/list                    # 用户列表
/user/add                     # 添加用户（独立页面）
/user/edit/{id}               # 编辑用户（独立页面）
/user/change_password         # 修改密码

/merchant/list                # 商户列表
/merchant/add                 # 添加商户（独立页面）
/merchant/edit/{id}           # 编辑商户（独立页面）

/plot/list                    # 地块列表
/plot/add                     # 添加地块（独立页面）
/plot/edit/{id}               # 编辑地块（独立页面）

/contract/list                # 合同列表
/contract/add                 # 添加合同（独立页面）
/contract/edit/{id}           # 编辑合同（独立页面）

/utility/list                 # 水电表列表
/utility/add                  # 添加水电表（独立页面）
/utility/edit/{id}            # 编辑水电表（独立页面）
/utility/water_meter          # 水表抄表
/utility/electricity_meter    # 电表抄表

/finance/receivable           # 应收账款
/finance/payable              # 应付账款
/finance/cash_flow            # 现金流水
/finance/list                 # 财务首页（重定向到应收账款）

/scale/list                   # 磅秤列表
/scale/records                # 过磅记录
```

### 8.2 模板继承结构

```
base.html                     # 基础母版（空框架）
├── admin_base.html           # 管理端母版（带导航和权限控制）
├── public_base.html          # 公用母版（预留）
└── merchant_base.html        # 商户端母版（预留）
```

### 8.3 页面规则

- **输入项 ≤ 5个**：使用模态窗口在列表页面打开
- **输入项 > 5个**：使用独立页面
- **所有页面**：必须继承相应的母版模板

***

## 9. 开发执行指令

### 第一步：项目初始化 ✅ 已完成

根据 Spec 生成 Flask 项目结构（Blueprint + 分层架构）

**已完成任务**：

- ✅ 创建项目目录结构
- ✅ 配置 Flask 应用
- ✅ 配置数据库连接（utils/database.py）
- ✅ 创建基础模板（admin\_base.html, public\_base.html, merchant\_base.html）
- ✅ 创建数据库初始化脚本（utils/init\_database.py）

### 第二步：用户认证模块 ✅ 已完成

实现用户登录模块（含数据库 + session）

**已完成任务**：

- ✅ 创建用户表（User）
- ✅ 创建角色表（Role）
- ✅ 创建权限表（Permission）
- ✅ 创建用户角色关联表（UserRole）
- ✅ 创建角色权限关联表（RolePermission）
- ✅ 实现登录接口（/auth/login）
- ✅ 实现登出接口（/auth/logout）
- ✅ 实现注册接口（/auth/register）
- ✅ 实现密码修改接口（/user/change\_password）
- ✅ 创建登录页面（templates/auth/login.html）
- ✅ 创建注册页面（templates/auth/register.html）
- ✅ 实现RBAC权限控制

### 第三步：用户管理模块 ✅ 已完成

实现用户管理 CRUD（含页面）

**已完成任务**：

- ✅ 实现用户列表接口（/user/list）
- ✅ 实现添加用户接口（/user/add）
- ✅ 实现编辑用户接口（/user/edit/<id>）
- ✅ 实现删除用户接口（/user/delete/<id>）
- ✅ 创建用户列表页面（templates/user/list.html）
- ✅ 创建添加用户页面（templates/user/add.html）
- ✅ 创建编辑用户页面（templates/user/edit.html）
- ✅ 创建修改密码页面（templates/user/change\_password.html）
- ✅ 实现搜索和分页

### 第四步：商户管理模块 ✅ 已完成

实现商户管理 CRUD（含页面）

**已完成任务**：

- ✅ 创建商户表（Merchant）
- ✅ 实现商户列表接口（/merchant/list）
- ✅ 实现添加商户接口（/merchant/add）
- ✅ 实现编辑商户接口（/merchant/edit/<id>）
- ✅ 创建商户列表页面（templates/merchant/list.html）
- ✅ 创建添加商户页面（templates/merchant/add.html）
- ✅ 创建编辑商户页面（templates/merchant/edit.html）
- ✅ 实现搜索和分页

### 第五步：地块与合同模块 🔄 进行中

实现地块 + 合同模块（含租金计算）

**已完成任务**：

- ✅ 创建地块表（Plot）
- ✅ 创建合同表（Contract）
- ✅ 创建地块列表页面（templates/plot/list.html）
- ✅ 创建添加地块页面（templates/plot/add.html）
- ✅ 创建编辑地块页面（templates/plot/edit.html）
- ✅ 创建合同列表页面（templates/contract/list.html）
- ✅ 创建添加合同页面（templates/contract/add.html）
- ✅ 创建编辑合同页面（templates/contract/edit.html）

**待完成任务**：

- ⬜ 实现地块 CRUD 业务逻辑
- ⬜ 实现合同 CRUD 业务逻辑
- ⬜ 实现租金自动计算
- ⬜ 实现合同编号自动生成
- ⬜ 实现合同状态流转

### 第六步：水电计费与财务模块 🔄 进行中

实现水电计费 + 财务系统

**已完成任务**：

- ✅ 创建水电表读数表（MeterReading）
- ✅ 创建应收账款表（Receivable）
- ✅ 创建水电表列表页面（templates/utility/list.html）
- ✅ 创建添加水电表页面（templates/utility/add.html）
- ✅ 创建编辑水电表页面（templates/utility/edit.html）
- ✅ 创建水表抄表页面（templates/utility/water\_meter.html）
- ✅ 创建电表抄表页面（templates/utility/electricity\_meter.html）
- ✅ 创建应收账款页面（templates/finance/receivable.html）
- ✅ 创建应付账款页面（templates/finance/payable.html）
- ✅ 创建现金流水页面（templates/finance/cash\_flow\.html）

**待完成任务**：

- ⬜ 实现水电表 CRUD 业务逻辑
- ⬜ 实现抄表录入业务逻辑
- ⬜ 实现费用自动计算
- ⬜ 实现应收账款管理
- ⬜ 实现收款记录

### 第七步：磅秤管理模块 🔄 进行中

实现磅秤管理模块

**已完成任务**：

- ✅ 创建磅秤记录表（WeighRecord）
- ✅ 创建磅秤列表页面（templates/scale/list.html）
- ✅ 创建过磅记录页面（templates/scale/records.html）

**待完成任务**：

- ⬜ 实现磅秤管理业务逻辑
- ⬜ 实现过磅记录业务逻辑
- ⬜ 实现净重计算

### 第八步：仪表盘与统计 ⬜ 待开始

实现仪表盘统计

**待完成任务**：

- ⬜ 实现统计数据接口
- ⬜ 创建仪表盘页面
- ⬜ 实现数据可视化

***

## 10. 非功能需求

### 10.1 性能需求

| 编号      | 需求描述   | 指标             |
| ------- | ------ | -------------- |
| NFR-001 | 页面加载时间 | 普通页面加载时间不超过3秒  |
| NFR-002 | 数据查询响应 | 列表查询响应时间不超过2秒  |
| NFR-003 | 并发用户数  | 支持至少50个用户同时在线  |
| NFR-004 | 数据库性能  | 单表数据量支持100万条记录 |

### 10.2 安全需求

| 编号      | 需求描述                       |
| ------- | -------------------------- |
| NFR-005 | 用户认证：所有用户必须登录后才能访问系统       |
| NFR-006 | 权限控制：基于RBAC模型实现细粒度权限控制     |
| NFR-007 | 密码加密：密码使用PBKDF2-SHA256加密存储 |
| NFR-008 | SQL注入防护：所有数据库操作使用参数化查询     |
| NFR-009 | CSRF防护：所有表单提交验证CSRF Token  |
| NFR-010 | 会话管理：用户会话超时自动退出            |
| NFR-011 | 数据备份：定期自动备份数据库             |

### 10.3 可用性需求

| 编号      | 需求描述                           |
| ------- | ------------------------------ |
| NFR-012 | 界面友好：采用Bootstrap 5响应式设计，支持多种设备 |
| NFR-013 | 操作简便：常用操作不超过3次点击               |
| NFR-014 | 错误提示：提供清晰的错误提示信息               |
| NFR-015 | 帮助文档：提供在线帮助文档                  |

### 10.4 可维护性需求

| 编号      | 需求描述                    |
| ------- | ----------------------- |
| NFR-016 | 代码规范：遵循PEP 8 Python代码规范 |
| NFR-017 | 模块化设计：采用模块化架构，便于维护和扩展   |
| NFR-018 | 文档完善：提供完整的开发文档和部署文档     |
| NFR-019 | 日志记录：记录关键操作日志和错误日志      |

***

## 11. 验收标准

### 11.1 功能验收

- 所有功能模块按需求文档实现
- 功能测试通过率达到100%
- 无严重和重大缺陷

### 11.2 性能验收

- 页面加载时间满足性能需求
- 并发测试通过

### 11.3 安全验收

- 安全测试通过
- 无安全漏洞

***

## 12. 附录

### 12.1 术语表

| 术语   | 说明              |
| ---- | --------------- |
| RBAC | 基于角色的访问控制       |
| CRUD | 创建、读取、更新、删除     |
| CSRF | 跨站请求伪造          |
| API  | 应用程序接口          |
| JSON | JavaScript对象表示法 |

### 11.2 参考文档

- 《数据库设计文档》
- 《接口设计文档》
- 《部署指南》
- 《用户手册》

***

**文档结束**
