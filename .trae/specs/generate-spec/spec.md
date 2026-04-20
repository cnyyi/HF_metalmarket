# 宏发金属交易市场管理系统 - 需求规格说明书（工程版）

## 文档信息

| 项目名称 | 宏发金属交易市场管理系统 |
| ---- | ------------ |
| 文档版本 | V3.0         |
| 编写日期 | 2026-04-13   |
| 文档状态 | 工程版（与实际代码对齐） |
| 编写人员 | 系统分析员        |
| 权威数据库设计 | `docs/design/数据库设计.md` |

---

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

### 1.4 模块完成度总览

| 模块 | 完成度 | 说明 |
|------|--------|------|
| 用户认证 | 100% | 登录/登出/注册/密码修改/RBAC权限，全部通过AuthService实现 |
| 用户管理 | 95% | CRUD完整，关联商户选择待完善 |
| 商户管理 | 100% | CRUD完整，字典数据动态获取，支持搜索分页 |
| 地块管理 | 90% | CRUD完整，图片上传/删除，**但存在架构违规（SQL在routes层）** |
| 合同管理 | 85% | CRUD+文档生成，**存在架构违规（SQL在routes层）** |
| 水电计费 | 95% | 表管理/抄表/合同绑定/应收生成，架构合理 |
| 合同文档生成 | 100% | docxtpl模板渲染，支持图片插入，金额大写转换 |
| 财务管理 | 70% | 应收/应付/现金流水、账户、预收/押金相关功能已实现，但仍有部分查询逻辑滞留在 routes 层 |
| 磅秤管理 | 55% | 列表、记录查询与看板统计已实现，但新增/编辑/删除与采集写入流程仍待完善 |

---

## 2. 全局约束（强制执行）

### 2.1 技术栈

| 分类 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 后端框架 | Flask | 3.1.3 | 通过 `app/__init__.py` 的 `create_app()` 工厂创建 |
| 数据库驱动 | pyodbc | - | **原生SQL**，不使用SQLAlchemy ORM |
| 数据库 | SQL Server | - | 连接串通过 `ODBC_CONNECTION_STRING` 配置 |
| 前端框架 | Bootstrap | 5 | CDN引入 |
| 前端JS | jQuery | 3.6.0 | CDN引入 |
| 图标 | Font Awesome | 4.7.0 | CDN引入 |
| 认证 | Flask-Login | - | session-based认证 |
| 表单验证 | Flask-WTF | - | CSRF保护 |
| 密码加密 | passlib (PBKDF2-SHA256) | - | `hashlib.pbkdf2_hmac` |
| 文档生成 | docxtpl (Jinja2 Word模板) | - | 合同文档生成 |
| Python | 3.14 | - | 运行时版本 |

> **注意**：项目最初设计包含SQLAlchemy，但实际代码全部使用原生pyodbc。`SQLAlchemy` 仍保留在 requirements.txt 但未实际使用。开发中不应引入ORM操作。

### 2.2 架构规范（强制执行）

#### 2.2.1 标准分层架构

```
请求流入 → Routes（路由层）→ Services（业务层）→ DBConnection（数据层）
                ↓                    ↓
          参数校验/渲染        业务逻辑/SQL
```

#### 2.2.2 项目结构

```
项目结构：
├── app/                          # 主应用目录
│   ├── __init__.py               # 应用工厂 create_app()
│   ├── extensions.py             # [废弃] 未被引用，应删除
│   ├── routes/                   # 路由层：只处理请求
│   │   ├── __init__.py
│   │   ├── auth.py               # 认证路由 (auth_bp)
│   │   ├── user.py               # 用户管理路由 (user_bp)
│   │   ├── merchant.py           # 商户管理路由 (merchant_bp)
│   │   ├── plot.py               # 地块管理路由 (plot_bp)
│   │   ├── contract.py           # 合同管理路由 (contract_bp)
│   │   ├── utility.py            # 水电计费路由 (utility_bp)
│   │   ├── finance.py            # 财务管理路由 (finance_bp)
│   │   ├── scale.py              # 磅秤管理路由 (scale_bp)
│   │   └── admin.py              # 后台首页与仪表盘路由 (admin_bp)
│   ├── services/                 # 业务层：业务逻辑
│   │   ├── auth_service.py       # 认证服务
│   │   ├── user_service.py       # 用户管理服务
│   │   ├── merchant_service.py   # 商户管理服务
│   │   ├── utility_service.py    # 水电计费服务（最完整）
│   │   ├── plot_service.py       # 地块管理服务
│   │   ├── contract_service.py   # 合同管理服务
│   │   ├── finance_service.py    # 财务核心联动服务
│   │   ├── scale_service.py      # 磅秤查询与看板服务
│   │   └── contract_doc_service.py # 合同文档生成服务
│   ├── models/                   # 数据模型层
│   │   ├── user.py               # 用户模型
│   │   ├── role.py               # 角色模型
│   │   ├── permission.py         # 权限模型
│   │   ├── merchant.py           # 商户模型
│   │   ├── meter.py              # 水电表模型
│   │   └── [finance.py]          # [待创建] 财务模型
│   ├── forms/                    # WTForms 表单定义
│   │   ├── auth_form.py          # LoginForm, RegisterForm
│   │   ├── user_form.py          # UserAddForm, UserEditForm, PasswordChangeForm
│   │   └── merchant_form.py      # MerchantAddForm, MerchantEditForm
│   └── repositories/             # [实验性] 数据仓储层
│       └── receivable_repo.py    # [存在Bug] 字段名/表名错误
├── utils/                        # 工具类
│   ├── database.py               # DBConnection 上下文管理器（核心）
│   ├── init_database.py          # 数据库初始化
│   └── run_sql_script.py         # SQL脚本执行
├── config/                       # 配置文件
│   ├── base.py                   # 基础配置（Config类）
│   ├── development.py            # 开发环境配置
│   ├── production.py             # 生产环境配置
│   └── testing.py                # 测试环境配置
├── templates/                    # HTML模板（Jinja2）
│   ├── base.html                 # 基础母版
│   ├── admin_base.html           # 管理端母版（带导航+权限控制）
│   ├── public_base.html          # 公用母版（预留）
│   ├── merchant_base.html        # 商户端母版（预留）
│   ├── index.html                # 系统首页
│   └── [各模块模板...]           # 参见目录结构设计.md
├── static/                       # 静态资源（CSS/JS/图片）
├── uploads/                      # 上传文件存储
│   └── plot/                     # 地块图片
├── scripts/                      # 数据库脚本
├── docs/                         # 项目文档
├── app.py                        # 应用入口
└── requirements.txt              # 项目依赖
```

#### 2.2.3 蓝图注册

```python
# app/__init__.py 中当前注册的主要蓝图（节选）
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(merchant_bp, url_prefix='/merchant')
app.register_blueprint(contract_bp, url_prefix='/contract')
app.register_blueprint(finance_bp, url_prefix='/finance')
app.register_blueprint(plot_bp, url_prefix='/plot')
app.register_blueprint(scale_bp, url_prefix='/scale')
app.register_blueprint(utility_bp, url_prefix='/utility')
app.register_blueprint(admin_bp, url_prefix='/admin')
```

#### 2.2.4 架构隔离规则（强制执行）

```
【强制执行 - 架构隔离规则】
1. 严禁在 routes 层中出现以下内容：
   - SQL语句（SELECT / INSERT / UPDATE / DELETE）
   - pyodbc 直接操作（from utils.database import DBConnection）
   - cursor.execute / cursor.fetchone
   - 数据库连接代码

2. routes 层职责仅限：
   - 接收请求（request）
   - 参数校验（简单校验）
   - 调用 Service 层
   - 返回 JSON / 渲染模板

3. 所有数据库操作必须放在：
   → services 层（通过 DBConnection）
   → models 层（仅限纯数据访问对象）

4. 所有业务逻辑必须放在：
   → services 层

5. 正确调用结构必须如下：
   routes:
       result = XxxService.some_method(params)
       return jsonify(result)
   services:
       with DBConnection() as conn:
           cursor = conn.cursor()
           cursor.execute("...", params)
           ...

6. 不允许跳过 service 层直接在 routes 中操作数据库
```

#### 2.2.5 数据库连接规范

```python
# 标准用法 - 上下文管理器（推荐）
from utils.database import DBConnection

with DBConnection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Table WHERE id = ?", (id,))
    rows = cursor.fetchall()
    conn.commit()  # 写操作需手动提交

# DBConnection 特性：
# - 自动从 current_app.config['ODBC_CONNECTION_STRING'] 获取连接串
# - __exit__ 时自动回滚未提交的事务
# - __exit__ 时自动关闭连接
# - 所有SQL必须使用参数化查询（?占位符）
```

### 2.3 开发规则

1. **HTML规则**：所有HTML必须在 `templates/` 目录
2. **路由规则**：必须使用 Blueprint，一个模块一个 Blueprint
3. **SQL规则**：所有SQL使用参数化查询，禁止拼接SQL
4. **返回格式**：AJAX接口返回 `{success: True/False, message: "...", data: ...}`
5. **文件管理**：所有文件必须走 `/uploads/`，数据库存路径，不存文件
6. **表单提交**：所有表单提交必须使用 jQuery Ajax 提交，禁止使用传统表单提交（地块添加除外，当前使用form submit）
7. **创建及编辑功能**：小于等于5个输入项使用模态窗口在列表页面打开，大于5个输入项使用独立页面打开
8. **功能实现**：所有功能的实现（含页面+后端）均按照Spec进行，有模糊的地方需要沟通确认
9. **统一字典管理**：所有字典数据均从 `Sys_Dictionary` 表动态获取，禁止硬编码
10. **字符类型**：数据库表不得使用 `varchar` 类型，必须使用 `nvarchar` 类型
11. **日志规范**：禁止使用 `print()` 调试，统一使用 `logging` 模块
12. **权限装饰器**：使用 `@check_permission('xxx_manage')` 装饰器控制访问权限（定义在 `app/routes/user.py`）

---

## 3. 统一返回格式

### 3.1 AJAX接口返回格式

```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

```json
{
  "success": false,
  "message": "错误描述"
}
```

### 3.2 分页数据返回格式

```json
{
  "success": true,
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "per_page": 10,
    "total_pages": 10
  }
}
```

> **注意**：当前实际使用的分页键名为 `contracts`/`plots` 等（非统一 `items`），此为历史遗留，新模块应统一使用 `items`。

---

## 4. 数据库结构

> **权威来源**：以 `docs/design/数据库设计.md` 为准。以下为概要，详细字段说明参见原文档。

### 4.1 系统基础表

#### Sys_Dictionary（系统字典表）

| 字段 | 类型 | 说明 |
|------|------|------|
| DictID | INT PK IDENTITY | 字典ID |
| DictType | NVARCHAR(50) | 字典类型 |
| DictCode | NVARCHAR(50) | 字典编码 |
| DictName | NVARCHAR(100) | 字典名称 |
| Description | NVARCHAR(200) | 描述 |
| SortOrder | INT | 排序 |
| IsActive | BIT | 是否有效 |
| CreateTime | DATETIME | 创建时间 |
| UpdateTime | DATETIME | 更新时间 |

**已使用的字典类型**：
- `merchant_type`: 商户类型
- `plot_type`: 地块类型（含 UnitPrice 扩展字段）
- `contract_period`: 合同期
- `business_type`: 业态类型
- `contract_status`: 合同状态
- `payment_method`: 付款方式
- `expense_item`: 费用项目
- `plot_status`: 地块状态

#### Role（角色表）

| 字段 | 类型 | 说明 |
|------|------|------|
| RoleID | INT PK IDENTITY | 角色ID |
| RoleName | NVARCHAR(50) UNIQUE | 角色名称 |
| RoleCode | NVARCHAR(50) UNIQUE | 角色编码 |
| Description | NVARCHAR(200) | 描述 |
| IsActive | BIT | 是否有效 |
| CreateTime | DATETIME | 创建时间 |
| UpdateTime | DATETIME | 更新时间 |

**初始角色**：admin（管理员）、staff（工作人员）、merchant（商户）

#### Permission（权限表）

| 字段 | 类型 | 说明 |
|------|------|------|
| PermissionID | INT PK IDENTITY | 权限ID |
| PermissionName | NVARCHAR(100) UNIQUE | 权限名称 |
| PermissionCode | NVARCHAR(100) UNIQUE | 权限编码 |
| Description | NVARCHAR(200) | 描述 |
| ModuleName | NVARCHAR(50) | 所属模块 |
| IsActive | BIT | 是否有效 |
| CreateTime | DATETIME | 创建时间 |
| UpdateTime | DATETIME | 更新时间 |

#### RolePermission（角色权限关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| RolePermissionID | INT PK IDENTITY | 关联ID |
| RoleID | INT FK→Role | 角色ID |
| PermissionID | INT FK→Permission | 权限ID |
| CreateTime | DATETIME | 创建时间 |

### 4.2 用户相关表

#### User（用户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| UserID | INT PK IDENTITY | 用户ID |
| Username | NVARCHAR(50) UNIQUE | 用户名 |
| Password | NVARCHAR(255) | 密码（PBKDF2加密） |
| RealName | NVARCHAR(50) | 真实姓名 |
| Phone | NVARCHAR(20) | 电话 |
| Email | NVARCHAR(100) | 邮箱 |
| IsActive | BIT | 是否有效 |
| CreateTime | DATETIME | 创建时间 |
| UpdateTime | DATETIME | 更新时间 |
| LastLoginTime | DATETIME | 最后登录时间 |
| WeChatOpenID | NVARCHAR(100) | 微信OpenID |
| MerchantID | INT FK→Merchant | 关联商户（商户用户） |

#### UserRole（用户角色关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| UserRoleID | INT PK IDENTITY | 关联ID |
| UserID | INT FK→User | 用户ID |
| RoleID | INT FK→Role | 角色ID |
| CreateTime | DATETIME | 创建时间 |

### 4.3 商户与地块

#### Merchant（商户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| MerchantID | INT PK IDENTITY | 商户ID |
| MerchantName | NVARCHAR(100) | 商户名称 |
| LegalPerson | NVARCHAR(50) | 法人 |
| ContactPerson | NVARCHAR(50) | 联系人 |
| Phone | NVARCHAR(20) | 电话 |
| Address | NVARCHAR(200) | 地址 |
| MerchantType | NVARCHAR(50) | 商户类型（字典） |
| BusinessLicense | NVARCHAR(100) | 营业执照 |
| TaxRegistration | NVARCHAR(100) | 税务登记证 |
| Description | NVARCHAR(500) | 描述 |
| Status | NVARCHAR(50) DEFAULT N'正常' | 状态 |
| BusinessType | NVARCHAR(100) | 业态类型 |
| CreateTime | DATETIME | 创建时间 |
| UpdateTime | DATETIME | 更新时间 |

#### Plot（地块表）

| 字段 | 类型 | 说明 |
|------|------|------|
| PlotID | INT PK IDENTITY | 地块ID |
| PlotNumber | NVARCHAR(50) UNIQUE | 地块编号 |
| PlotName | NVARCHAR(100) | 地块名称 |
| Area | DECIMAL(10,2) | 面积（㎡） |
| UnitPrice | DECIMAL(10,2) | 单价（元/㎡/月） |
| TotalPrice | DECIMAL(10,2) | 月总价 |
| Location | NVARCHAR(200) | 位置 |
| Description | NVARCHAR(500) | 描述 |
| ImagePath | NVARCHAR(255) | 图片路径 |
| Status | NVARCHAR(50) DEFAULT N'空闲' | 状态 |
| PlotType | NVARCHAR(50) | 地块类型 |
| **MonthlyRent** | DECIMAL(10,2) | 月租金（代码实际使用） |
| **YearlyRent** | DECIMAL(10,2) | 年租金（代码实际使用） |
| CreateTime | DATETIME | 创建时间 |
| UpdateTime | DATETIME | 更新时间 |

> **注意**：`MonthlyRent` 和 `YearlyRent` 字段在 `docs/design/数据库设计.md` 中未列出，但实际代码中使用（`plot.py` 中的 INSERT 语句包含这些字段）。需确认是否已在数据库中通过迁移脚本添加。

### 4.4 合同相关表

#### Contract（合同表）

| 字段 | 类型 | 说明 |
|------|------|------|
| ContractID | INT PK IDENTITY | 合同ID |
| ContractNumber | NVARCHAR(50) UNIQUE | 合同编号 |
| MerchantID | INT FK→Merchant | 商户ID |
| ContractName | NVARCHAR(100) | 合同名称 |
| StartDate | DATE | 开始日期 |
| EndDate | DATE | 结束日期 |
| ContractAmount | DECIMAL(12,2) | 合同金额 |
| AmountReduction | DECIMAL(12,2) DEFAULT 0 | 金额减免 |
| ActualAmount | DECIMAL(12,2) | 实际金额 |
| PaymentMethod | NVARCHAR(50) | 付款方式 |
| ContractPeriodYear | INT | 合同期年 |
| **ContractPeriod** | NVARCHAR(50) | 合同期限描述（如"第1期第1年"） |
| BusinessType | NVARCHAR(50) | 业态类型 |
| Description | NVARCHAR(500) | 描述 |
| Status | NVARCHAR(50) DEFAULT N'有效' | 状态 |
| CreateTime | DATETIME | 创建时间 |
| UpdateTime | DATETIME | 更新时间 |

**合同编号生成规则**：
```
格式：ZTHYHT + 期号(1位) + 年份(1位) + YYYYMMDD + 商户ID(3位补零)
示例：ZTHYHT1120260401026
解析：ZTHYHT + 第1期第1年 + 2026年04月01日 + 商户026号
```

#### ContractPlot（合同地块关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| ContractPlotID | INT PK IDENTITY | 关联ID |
| ContractID | INT FK→Contract | 合同ID |
| PlotID | INT FK→Plot | 地块ID |
| UnitPrice | DECIMAL(10,2) | 签约时单价（快照） |
| Area | DECIMAL(10,2) | 面积（快照） |
| MonthlyPrice | DECIMAL(10,2) | 月租金 |
| CreateTime | DATETIME | 创建时间 |

### 4.5 水电计费相关表

#### ElectricityMeter（电表表）

| 字段 | 类型 | 说明 |
|------|------|------|
| MeterID | INT PK IDENTITY | 电表ID |
| MeterNumber | NVARCHAR(50) UNIQUE | 电表编号 |
| MeterType | NVARCHAR(50) DEFAULT N'electricity' | 类型 |
| InstallationLocation | NVARCHAR(200) | 安装位置 |
| Status | NVARCHAR(50) DEFAULT N'正常' | 状态（正常/故障/停用） |
| CreateTime | DATETIME | 创建时间 |
| UpdateTime | DATETIME | 更新时间 |

> **注意**：设计文档中已删除 UnitPrice、LastReading、CurrentReading 字段。单价通过 ContractElectricityMeter 表按合同管理。

#### WaterMeter（水表表）

| 字段 | 类型 | 说明 |
|------|------|------|
| MeterID | INT PK IDENTITY | 水表ID |
| MeterNumber | NVARCHAR(50) UNIQUE | 水表编号 |
| MeterType | NVARCHAR(50) DEFAULT N'water' | 类型 |
| InstallationLocation | NVARCHAR(200) | 安装位置 |
| Status | NVARCHAR(50) DEFAULT N'正常' | 状态 |
| CreateTime | DATETIME | 创建时间 |
| UpdateTime | DATETIME | 更新时间 |

#### ContractElectricityMeter（合同电表关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| ContractMeterID | INT PK IDENTITY | 关联ID |
| ContractID | INT FK→Contract | 合同ID |
| MeterID | INT FK→ElectricityMeter | 电表ID |
| StartReading | DECIMAL(10,2) | 起始表底 |
| **UnitPrice** | DECIMAL(10,4) DEFAULT 0 | 单价（元/度），按合同设定 |
| CreateTime | DATETIME | 创建时间 |

#### ContractWaterMeter（合同水表关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| ContractMeterID | INT PK IDENTITY | 关联ID |
| ContractID | INT FK→Contract | 合同ID |
| MeterID | INT FK→WaterMeter | 水表ID |
| StartReading | DECIMAL(10,2) | 起始表底 |
| **UnitPrice** | DECIMAL(10,4) DEFAULT 0 | 单价（元/吨），按合同设定 |
| CreateTime | DATETIME | 创建时间 |

#### UtilityReading（水电费抄表记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| ReadingID | INT PK IDENTITY | 记录ID |
| MeterID | INT | 表ID |
| MeterType | NVARCHAR(50) | 表类型（electricity/water） |
| LastReading | DECIMAL(10,2) | 上次表底 |
| CurrentReading | DECIMAL(10,2) | 当前表底 |
| Usage | DECIMAL(10,2) | 用量 |
| UnitPrice | DECIMAL(10,2) | 单价（从合同关联表获取） |
| TotalAmount | DECIMAL(12,2) | 总金额 |
| ReadingDate | DATETIME | 抄表日期 |
| ReadingMonth | NVARCHAR(7) | 抄表月份（YYYY-MM） |
| CreateTime | DATETIME | 创建时间 |

> **注意**：设计文档中已删除 ContractID、MerchantID、CreatedBy 字段。合同/商户信息通过 ContractXxxMeter 关联表查询获取。

#### MeterChangeRecord（换表记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| ChangeRecordID | INT PK IDENTITY | 记录ID |
| OldMeterID | INT | 旧表ID |
| NewMeterID | INT | 新表ID |
| MeterType | NVARCHAR(50) | 表类型 |
| ContractID | INT FK→Contract | 合同ID |
| MerchantID | INT FK→Merchant | 商户ID |
| OldMeterLastReading | DECIMAL(10,2) | 旧表最后底数 |
| NewMeterStartReading | DECIMAL(10,2) | 新表起始底数 |
| ChangeDate | DATETIME | 换表日期 |
| Reason | NVARCHAR(500) | 原因 |
| CreatedBy | INT FK→User | 操作人 |
| CreateTime | DATETIME | 创建时间 |

### 4.6 财务相关表

#### ExpenseType（费用类型表）

| 字段 | 类型 | 说明 |
|------|------|------|
| ExpenseTypeID | INT PK IDENTITY | 费用类型ID |
| ExpenseTypeName | NVARCHAR(100) UNIQUE | 名称 |
| ExpenseTypeCode | NVARCHAR(50) UNIQUE | 编码 |
| ExpenseDirection | NVARCHAR(20) | 方向（收入/支出） |
| Description | NVARCHAR(200) | 描述 |
| IsActive | BIT | 是否有效 |
| CreateTime | DATETIME | 创建时间 |
| UpdateTime | DATETIME | 更新时间 |

#### Receivable（应收账款表）

| 字段 | 类型 | 说明 |
|------|------|------|
| ReceivableID | INT PK IDENTITY | 应收ID |
| MerchantID | INT FK→Merchant | 商户ID |
| ExpenseTypeID | INT FK→ExpenseType | 费用类型 |
| Amount | DECIMAL(12,2) | 金额 |
| Description | NVARCHAR(500) | 描述 |
| DueDate | DATETIME | 到期日期 |
| Status | NVARCHAR(50) DEFAULT N'未付款' | 状态（未付款/部分付款/已付款） |
| PaidAmount | DECIMAL(12,2) DEFAULT 0 | 已付金额 |
| RemainingAmount | DECIMAL(12,2) | 剩余金额 |
| ReferenceID | INT | 参考ID（如抄表记录ID） |
| ReferenceType | NVARCHAR(50) | 参考类型（如utility_reading） |
| CreateTime | DATETIME | 创建时间 |
| UpdateTime | DATETIME | 更新时间 |

#### Payable（应付账款表）

| 字段 | 类型 | 说明 |
|------|------|------|
| PayableID | INT PK IDENTITY | 应付ID |
| VendorName | NVARCHAR(100) | 供应商名称 |
| ExpenseTypeID | INT FK→ExpenseType | 费用类型 |
| Amount | DECIMAL(12,2) | 金额 |
| Description | NVARCHAR(500) | 描述 |
| DueDate | DATETIME | 到期日期 |
| Status | NVARCHAR(50) DEFAULT N'未付款' | 状态 |
| PaidAmount | DECIMAL(12,2) DEFAULT 0 | 已付金额 |
| RemainingAmount | DECIMAL(12,2) | 剩余金额 |
| ReferenceID | INT | 参考ID |
| ReferenceType | NVARCHAR(50) | 参考类型 |
| CreateTime | DATETIME | 创建时间 |
| UpdateTime | DATETIME | 更新时间 |

#### CashFlow（现金流水表）

| 字段 | 类型 | 说明 |
|------|------|------|
| CashFlowID | INT PK IDENTITY | 流水ID |
| Amount | DECIMAL(12,2) | 金额 |
| Direction | NVARCHAR(20) | 方向（收入/支出） |
| ExpenseTypeID | INT FK→ExpenseType | 费用类型 |
| Description | NVARCHAR(500) | 描述 |
| TransactionDate | DATETIME | 交易日期 |
| ReferenceID | INT | 参考ID |
| ReferenceType | NVARCHAR(50) | 参考类型 |
| CreatedBy | INT FK→User | 操作人 |
| CreateTime | DATETIME | 创建时间 |

#### CollectionRecord（收款记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| CollectionRecordID | INT PK IDENTITY | 收款ID |
| ReceivableID | INT FK→Receivable | 应收ID |
| MerchantID | INT FK→Merchant | 商户ID |
| Amount | DECIMAL(12,2) | 收款金额 |
| PaymentMethod | NVARCHAR(50) | 付款方式 |
| TransactionDate | DATETIME | 交易日期 |
| Description | NVARCHAR(500) | 描述 |
| CreatedBy | INT FK→User | 操作人 |
| CreateTime | DATETIME | 创建时间 |

#### PaymentRecord（付款记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| PaymentRecordID | INT PK IDENTITY | 付款ID |
| PayableID | INT FK→Payable | 应付ID |
| VendorName | NVARCHAR(100) | 供应商名称 |
| Amount | DECIMAL(12,2) | 付款金额 |
| PaymentMethod | NVARCHAR(50) | 付款方式 |
| TransactionDate | DATETIME | 交易日期 |
| Description | NVARCHAR(500) | 描述 |
| CreatedBy | INT FK→User | 操作人 |
| CreateTime | DATETIME | 创建时间 |

### 4.7 磅秤相关表

#### Scale（磅秤表）

| 字段 | 类型 | 说明 |
|------|------|------|
| ScaleID | INT PK IDENTITY | 磅秤ID |
| ScaleNumber | NVARCHAR(50) UNIQUE | 磅秤编号 |
| ScaleName | NVARCHAR(100) | 名称 |
| Location | NVARCHAR(200) | 安装位置 |
| MaximumCapacity | DECIMAL(10,2) | 最大量程 |
| Unit | NVARCHAR(10) | 单位（吨/千克） |
| Status | NVARCHAR(50) DEFAULT N'正常' | 状态 |
| Description | NVARCHAR(500) | 描述 |
| CreateTime | DATETIME | 创建时间 |
| UpdateTime | DATETIME | 更新时间 |

#### ScaleRecord（过磅记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| ScaleRecordID | INT PK IDENTITY | 记录ID |
| ScaleID | INT FK→Scale | 磅秤ID |
| MerchantID | INT FK→Merchant | 商户ID |
| GrossWeight | DECIMAL(10,2) | 毛重 |
| TareWeight | DECIMAL(10,2) | 皮重 |
| NetWeight | DECIMAL(10,2) | 净重 |
| UnitPrice | DECIMAL(10,2) | 单价 |
| TotalAmount | DECIMAL(12,2) | 总金额 |
| LicensePlate | NVARCHAR(50) | 车牌号 |
| ProductName | NVARCHAR(100) | 产品名称 |
| Operator | NVARCHAR(50) | 操作员 |
| ScaleTime | DATETIME | 过磅时间 |
| Description | NVARCHAR(500) | 描述 |
| CreateTime | DATETIME | 创建时间 |

### 4.8 表关系图

```
User 1:n UserRole n:1 Role
Role 1:n RolePermission n:1 Permission

User n:1 Merchant（商户用户关联）

Merchant 1:n Contract
Contract 1:n ContractPlot n:1 Plot

Contract 1:n ContractElectricityMeter n:1 ElectricityMeter
Contract 1:n ContractWaterMeter n:1 WaterMeter

Meter 1:n UtilityReading
Contract 1:n UtilityReading（通过关联表）
Merchant 1:n UtilityReading（通过关联表）

Contract 1:n MeterChangeRecord
Merchant 1:n MeterChangeRecord

Merchant 1:n Receivable
Receivable 1:n CollectionRecord

ExpenseType 1:n Receivable
ExpenseType 1:n Payable
ExpenseType 1:n CashFlow

CashFlow → CollectionRecord / PaymentRecord（通过ReferenceID）

Merchant 1:n ScaleRecord
Scale 1:n ScaleRecord
```

---

## 5. 状态机定义

### 5.1 合同状态流转

```
有效 → 已到期
有效 → 已终止
```

**状态说明**：
- **有效**：合同正在执行中（当前实际使用的默认值）
- **已到期**：合同已到期
- **已终止**：合同提前终止

### 5.2 地块状态流转

```
空闲 → 已租（合同创建时）
已租 → 空闲（合同到期/终止时）
空闲/已租 → 维修中（手动设置）
维修中 → 空闲（维修完成）
```

### 5.3 应收/应付账款状态

```
未付款 → 部分付款 → 已付款
```

### 5.4 商户状态

```
正常 ⇄ 在租（根据合同状态自动切换）
正常 ⇄ 暂停（手动）
正常 → 注销（手动）
```

### 5.5 水电表状态

```
正常 → 故障（手动）
故障 → 正常（维修完成）
正常 → 停用（手动）
停用 → 正常（重新启用）
```

### 5.6 磅秤状态

```
正常 → 故障
正常 → 维修中
故障/维修中 → 正常
```

---

## 6. 业务规则

### 6.1 合同约束规则

| 规则编号 | 规则名称 | 规则描述 | 触发时机 |
|---------|---------|---------|---------|
| BR-001 | 地块唯一性 | 一个地块同一时间只能属于一个有效合同 | 创建/编辑合同时 |
| BR-002 | 时间不重叠 | 同一地块的合同时间不能重叠 | 创建/编辑合同时 |
| BR-003 | 合同编号唯一 | 格式：ZTHYHT + 期号 + 年份 + YYYYMMDD + 商户ID(3位) | 创建合同时 |
| BR-004 | 租金自动计算 | 合同金额 = Σ(各地块年租金)，实际金额 = 合同金额 + 减免金额 | 创建/编辑合同时 |

**地块可用性检查逻辑（当前实现）**：
```sql
-- 排除结束日期在近1个月内到期的合同所关联的地块
WHERE p.PlotID NOT IN (
    SELECT cp.PlotID FROM ContractPlot cp
    INNER JOIN Contract c ON cp.ContractID = c.ContractID
    WHERE c.EndDate > DATEADD(MONTH, -1, GETDATE())
)
```

### 6.2 抄表规则

| 规则编号 | 规则名称 | 规则描述 | 触发时机 |
|---------|---------|---------|---------|
| BR-005 | 抄表周期 | 按月抄表，每月一次 | 抄表录入时 |
| BR-006 | 读数递增 | 当前读数 ≥ 上次读数，不允许倒退 | 抄表录入时 |
| BR-007 | 用量计算 | 用量 = 当前读数 - 上次读数 | 抄表录入时 |
| BR-008 | 费用计算 | 金额 = 用量 × 单价（单价来自合同关联表的 UnitPrice） | 抄表录入时 |
| BR-009 | 单价来源 | 水电费单价从 ContractElectricityMeter/ContractWaterMeter 的 UnitPrice 字段获取 | 抄表/绑定时 |
| BR-010 | 应收自动生成 | 抄表提交后自动创建应收账款记录 | 抄表提交时 |

**抄表校验逻辑**：
```
IF 当前读数 < 上次读数 THEN
    提示错误："当前读数不能小于上次读数（上次读数：XXX）"
    不允许保存
END IF
```

### 6.3 商户状态自动化规则

| 规则编号 | 规则名称 | 规则描述 | 触发时机 |
|---------|---------|---------|---------|
| BR-011 | 状态自动更新 | 商户状态根据合同状态自动更新 | 合同状态变更时 |
| BR-012 | 在租判定 | 商户有"有效"状态的合同 → 商户状态变为"在租" | 合同生效时 |
| BR-013 | 空闲判定 | 商户无"有效"状态的合同 → 商户状态变为"空闲" | 合同到期/终止时 |

### 6.4 地块状态联动规则

| 规则编号 | 规则名称 | 规则描述 | 触发时机 |
|---------|---------|---------|---------|
| BR-014 | 地块出租 | 地块被加入有效合同 → 地块状态变为"已租" | 合同创建时 |
| BR-015 | 地块释放 | 地块无有效合同 → 地块状态变为"空闲" | 合同到期/终止时 |

### 6.5 应收账款规则

| 规则编号 | 规则名称 | 规则描述 | 触发时机 |
|---------|---------|---------|---------|
| BR-016 | 自动生成 | 抄表提交后自动生成应收账款 | 抄表提交时 |
| BR-017 | 状态更新 | 收款后更新应收账款状态 | 收款记录时 |
| BR-018 | 部分支付 | 0 < PaidAmount < Amount → "部分付款" | 收款记录时 |
| BR-019 | 全部支付 | PaidAmount >= Amount → "已付款" | 收款记录时 |

**核销流程**：
```
1. 创建收款记录 (CollectionRecord)
   - 记录实际收到的款项
   
2. 选择待核销的应收账款
   - 可选择一笔或多笔
   
3. 更新应收账款
   - PaidAmount = PaidAmount + 收款金额
   - RemainingAmount = Amount - PaidAmount
   - 更新状态（未付款/部分付款/已付款）
   
4. 创建现金流水 (CashFlow)
   - 方向：收入
   - 关联收款记录
```

---

## 7. 接口定义

### 7.1 用户认证模块

#### 7.1.1 用户登录

**路由**：`GET/POST /auth/login`

**页面**：`templates/auth/login.html`

**实现**：✅ 已完成（通过 `AuthService.login()`）

**表单**：`LoginForm`（username, password）

#### 7.1.2 用户登出

**路由**：`GET /auth/logout`

**实现**：✅ 已完成

#### 7.1.3 用户注册

**路由**：`GET/POST /auth/register`

**页面**：`templates/auth/register.html`

**实现**：✅ 已完成（默认注册为 staff 角色）

**表单**：`RegisterForm`（username, password, real_name, phone, email）

> **安全建议**：生产环境应限制注册功能，增加邀请码或审批机制。

#### 7.1.4 系统首页

**路由**：`GET /auth/`

**页面**：`templates/index.html`

**实现**：✅ 已完成

**根路径**：`GET /` 重定向到 `admin.index`

### 7.2 用户管理模块

#### 7.2.1 用户列表

**路由**：`GET /user/list`

**页面**：`templates/user/list.html`

**实现**：✅ 已完成（`UserService.get_users()`，支持分页搜索）

**参数**：page, search

#### 7.2.2 添加用户

**路由**：`GET/POST /user/add`

**页面**：`templates/user/add.html`

**权限**：`@check_permission('user_manage')`

**实现**：✅ 已完成

**表单字段**：username, password, confirm_password, real_name, phone, email, roles(多选), merchant_id

#### 7.2.3 编辑用户

**路由**：`GET/POST /user/edit/<int:user_id>`

**页面**：`templates/user/edit.html`

**权限**：`@check_permission('user_manage')`

**实现**：✅ 已完成

#### 7.2.4 删除用户

**路由**：`GET /user/delete/<int:user_id>`

**权限**：`@check_permission('user_manage')`

**实现**：✅ 已完成（不能删除自己）

#### 7.2.5 修改密码

**路由**：`GET/POST /user/change_password`

**页面**：`templates/user/change_password.html`

**实现**：✅ 已完成

**表单字段**：current_password, new_password, confirm_new_password

### 7.3 商户管理模块

#### 7.3.1 商户列表

**路由**：`GET /merchant/list`

**页面**：`templates/merchant/list.html`

**实现**：✅ 已完成（`MerchantService.get_merchants()`，支持分页搜索）

**参数**：page, search

#### 7.3.2 添加商户

**路由**：`GET/POST /merchant/add`

**页面**：`templates/merchant/add.html`

**实现**：✅ 已完成

**表单字段**：merchant_name, legal_person, contact_person, phone, address, merchant_type(字典), business_license, tax_registration, description, business_type(字典)

#### 7.3.3 编辑商户

**路由**：`GET/POST /merchant/edit/<int:merchant_id>`

**页面**：`templates/merchant/edit.html`

**实现**：✅ 已完成

### 7.4 地块管理模块

> **架构警告**：当前实现在 routes 层直接操作数据库（`from utils.database import DBConnection`），违反架构规范。需要重构为 Service 层。

#### 7.4.1 地块列表

**路由**：`GET /plot/list`

**页面**：`templates/plot/list.html`

**实现**：✅ 已完成（架构违规）

**数据接口**：`GET /plot/list_data`（支持分页、搜索、状态筛选、类型筛选）

#### 7.4.2 获取地块类型

**路由**：`GET /plot/types`

**实现**：✅ 已完成（从 Sys_Dictionary 获取 plot_type）

#### 7.4.3 添加地块

**路由**：`GET/POST /plot/add`

**页面**：`templates/plot/add.html`

**实现**：✅ 已完成（架构违规）

**表单字段**：plot_code, plot_name, plot_type(字典联动单价), area, price, location, status, description, image(文件上传)

**自动计算**：
- TotalPrice = area × unit_price
- MonthlyRent = area × unit_price
- YearlyRent = MonthlyRent × 12

#### 7.4.4 编辑地块

**路由**：`GET/POST /plot/edit/<int:plot_id>`

**页面**：`templates/plot/edit.html`

**实现**：✅ 已完成（架构违规，AJAX提交）

#### 7.4.5 上传地块图片

**路由**：`POST /plot/upload_image/<int:plot_id>`

**实现**：✅ 已完成（支持 png/jpg/jpeg/gif/bmp/webp，UUID命名，旧图片自动删除）

#### 7.4.6 删除地块

**路由**：`POST /plot/delete/<int:plot_id>`

**实现**：✅ 已完成（关联图片同步删除）

#### 7.4.7 地块详情

**路由**：`GET /plot/detail/<int:plot_id>`

**实现**：✅ 已完成

### 7.5 合同管理模块

> **架构警告**：当前实现在 routes 层直接操作数据库，需要重构。

#### 7.5.1 合同列表

**路由**：`GET /contract/list`

**页面**：`templates/contract/list.html`

**实现**：✅ 已完成（架构违规）

**数据接口**：`GET /contract/list_data`（支持分页搜索）

**交互优化**：点击合同编号打开详情模态框（非跳转页面）

#### 7.5.2 合同详情

**路由**：`GET /contract/detail/<int:contract_id>`

**实现**：✅ 已完成（返回合同信息+关联地块列表，模态框展示）

#### 7.5.3 添加合同

**路由**：`GET/POST /contract/add`

**页面**：`templates/contract/add.html`

**实现**：✅ 已完成（架构违规）

**表单字段**：period(合同期), merchant_id, plot_ids(多选), start_date, end_date, rent_adjust(金额减免), description

**级联查询**：
- `GET /contract/periods` → 获取合同期列表
- `GET /contract/merchants/<period>` → 获取该期可用商户
- `GET /contract/plots/<period>` → 获取可用地块

**自动生成**：
- 合同编号：`ZTHYHT{期号}{年份}{YYYYMMDD}{商户ID}`
- 合同名称：`{period}-{merchant_id}号合同`
- 合同金额：Σ(各地块年租金)
- 实际金额：合同金额 + 金额减免

#### 7.5.4 编辑合同

**路由**：`GET/POST /contract/edit/<int:contract_id>`

**页面**：`templates/contract/edit.html`

**实现**：✅ 已完成（架构违规）

**可编辑字段**：start_date, end_date, rent_adjust, description, status, plot_ids

#### 7.5.5 删除合同

**路由**：`POST /contract/delete/<int:contract_id>`

**实现**：✅ 已完成（级联删除 ContractPlot）

#### 7.5.6 生成合同文档

**路由**：`POST /contract/generate/<int:contract_id>`

**实现**：✅ 已完成（委托 `contract_doc_service`）

**功能**：
- 使用 docxtpl 从 Word 模板生成合同文档
- 自动插入关联地块的图片
- 金额自动转换为人民币大写
- 生成文件保存在服务器，返回文件名

#### 7.5.7 下载合同文档

**路由**：`GET /contract/download/<path:file_name>`

**实现**：✅ 已完成（委托 `contract_doc_service`，`send_file` 下载）

### 7.6 水电计费模块

#### 7.6.1 水电表列表

**路由**：`GET /utility/list`

**页面**：`templates/utility/list.html`

**实现**：✅ 已完成（`UtilityService.get_meter_list_paginated()`，架构合理）

**数据接口**：`GET /utility/list_data`（支持表号搜索、类型筛选、分页）

**功能**：
- 查看所有水电表及其绑定状态
- 按类型（电表/水表）筛选
- 绑定/解绑合同
- 编辑/删除表信息

**关联操作接口**：
- `POST /utility/bind` → 绑定表到合同（含单价设置）
- `POST /utility/unbind` → 解绑
- `GET /utility/merchants` → 获取商户列表（筛选用）
- `GET /utility/contracts` → 获取可关联合同列表
- `GET /utility/valid_contracts` → 获取有效合同（结束日期+3个月内）

#### 7.6.2 水表抄表

**路由**：`GET /utility/water_meter`

**页面**：`templates/utility/water_meter.html`

**实现**：✅ 已完成

**URL参数**：`?date=YYYY-MM-DD`（默认当月1号）

**数据接口**：
- `GET /utility/water_meter_data` → 获取待抄水表列表（已绑定合同的）
- `POST /utility/water_meter_submit` → 批量提交抄表数据

#### 7.6.3 电表抄表

**路由**：`GET /utility/electricity_meter`

**页面**：`templates/utility/electricity_meter.html`

**实现**：✅ 已完成

**URL参数**：`?date=YYYY-MM-DD`

**数据接口**：
- `GET /utility/electricity_meter_data` → 获取待抄电表列表
- `POST /utility/electricity_meter_submit` → 批量提交抄表数据

#### 7.6.4 抄表数据提交流程

```
1. 前端获取待抄表列表（已绑定有效合同的表）
2. 用户输入各表当前读数
3. 前端批量提交 {readings: [...], reading_date: "YYYY-MM-DD"}
4. UtilityService.submit_meter_readings() 处理：
   a. 遍历每条抄表数据
   b. 获取上次表底（最近抄表记录或起始表底）
   c. 校验：当前读数 >= 上次表底
   d. 计算用量 = 当前读数 - 上次表底
   e. 获取单价（从合同关联表）
   f. 计算金额 = 用量 × 单价
   g. 写入 UtilityReading 表
   h. 调用 _create_receivable() 创建应收账款
```

### 7.7 财务管理模块

> **状态：已具备主要业务能力**。当前已实现应收/应付/现金流水、账户、直接记账、预收/预付、押金管理，但仍存在部分查询/聚合逻辑位于 routes 层的架构问题。

#### 7.7.1 应收账款管理

**路由**：`GET /finance/receivable`

**页面**：`templates/finance/receivable.html`

**实现状态**：✅ 已实现列表、创建、软删除、详情、收款核销及关联查询

**详细需求**：

**页面功能**：
- 应收账款列表（DataTable展示）
- 搜索筛选：按商户、费用类型、状态、日期范围
- 分页

**列表字段**：
| 列 | 说明 |
|----|------|
| 应收ID | ReceivableID |
| 商户名称 | MerchantName（关联查询） |
| 费用类型 | ExpenseTypeName |
| 应收金额 | Amount |
| 已付金额 | PaidAmount |
| 剩余金额 | RemainingAmount |
| 到期日期 | DueDate |
| 状态 | Status（未付款/部分付款/已付款） |
| 创建时间 | CreateTime |

**操作**：
- 查看详情（模态框）
- 记录收款（模态框/独立页面）
  - 收款金额
  - 付款方式（字典 payment_method）
  - 收款日期
  - 备注
  - 创建 CollectionRecord
  - 更新 Receivable 的 PaidAmount/RemainingAmount/Status
  - 创建 CashFlow（方向：收入）

**数据接口**：
- `GET /finance/receivable/list` → 分页列表数据
- `POST /finance/receivable/create` → 新增应收
- `POST /finance/receivable/collect/<int:receivable_id>` → 记录收款
- `GET /finance/receivable/detail/<int:receivable_id>` → 详情

#### 7.7.2 应付账款管理

**路由**：`GET /finance/payable`

**页面**：`templates/finance/payable.html`

**实现状态**：✅ 已实现列表、新增、详情、付款核销

**详细需求**：

**页面功能**：
- 应付账款列表
- 搜索筛选：按供应商、费用类型、状态、日期范围
- 新增应付账款（独立页面，输入项>5）

**新增应付表单字段**：
| 字段 | 必填 | 说明 |
|------|------|------|
| vendor_name | 是 | 供应商名称 |
| expense_type_id | 是 | 费用类型（下拉选择） |
| amount | 是 | 金额 |
| due_date | 是 | 到期日期 |
| description | 否 | 描述 |

**列表字段**：
| 列 | 说明 |
|----|------|
| 应付ID | PayableID |
| 供应商 | VendorName |
| 费用类型 | ExpenseTypeName |
| 应付金额 | Amount |
| 已付金额 | PaidAmount |
| 剩余金额 | RemainingAmount |
| 到期日期 | DueDate |
| 状态 | Status |
| 创建时间 | CreateTime |

**操作**：
- 新增应付
- 查看详情
- 记录付款
  - 创建 PaymentRecord
  - 更新 Payable 的 PaidAmount/RemainingAmount/Status
  - 创建 CashFlow（方向：支出）

**数据接口**：
- `GET /finance/payable/list` → 分页列表
- `POST /finance/payable/add` → 新增应付
- `POST /finance/payable/pay/<int:payable_id>` → 记录付款
- `GET /finance/payable/detail/<int:payable_id>` → 详情

#### 7.7.3 现金流水

**路由**：`GET /finance/cash_flow`

**页面**：`templates/finance/cash_flow.html`

**实现状态**：✅ 已实现列表查询与汇总统计

**详细需求**：

**页面功能**：
- 现金流水列表
- 搜索筛选：按方向（收入/支出）、费用类型、日期范围、操作人
- 统计汇总：总收入、总支出、净现金流

**列表字段**：
| 列 | 说明 |
|----|------|
| 流水ID | CashFlowID |
| 方向 | Direction（收入→红色，支出→绿色） |
| 金额 | Amount |
| 费用类型 | ExpenseTypeName |
| 描述 | Description |
| 交易日期 | TransactionDate |
| 操作人 | 操作人姓名 |
| 创建时间 | CreateTime |

**数据来源**：
- 收款时自动创建（方向：收入）
- 付款时自动创建（方向：支出）
- 支持手动录入

**数据接口**：
- `GET /finance/cash_flow/list` → 分页列表+汇总统计

#### 7.7.4 财务管理首页（重定向）

**路由**：`GET /finance/list`

**实现**：✅ 已完成（重定向到 `/finance/receivable`）

### 7.8 磅秤管理模块

> **状态：已实现查询与看板，写入流程待完善**。当前已具备磅秤列表、过磅记录列表/详情、日看板与月趋势统计能力。

#### 7.8.1 磅秤列表

**路由**：`GET /scale/list`

**页面**：`templates/scale/list.html`

**实现状态**：✅ 已实现列表页面和查询接口

**详细需求**：

**页面功能**：
- 磅秤列表（DataTable展示）
- 搜索筛选：按编号、名称、状态
- 新增磅秤（模态框，输入项≤5）
- 编辑磅秤（模态框，输入项≤5）
- 删除磅秤

**新增/编辑磅秤表单字段**：
| 字段 | 必填 | 说明 |
|------|------|------|
| scale_number | 是 | 磅秤编号（唯一） |
| scale_name | 是 | 磅秤名称 |
| location | 是 | 安装位置 |
| maximum_capacity | 是 | 最大量程 |
| unit | 是 | 单位（吨/千克） |
| description | 否 | 描述 |

**列表字段**：
| 列 | 说明 |
|----|------|
| 磅秤ID | ScaleID |
| 磅秤编号 | ScaleNumber |
| 磅秤名称 | ScaleName |
| 安装位置 | Location |
| 最大量程 | MaximumCapacity |
| 单位 | Unit |
| 状态 | Status（正常/故障/维修中） |
| 创建时间 | CreateTime |

**数据接口**：
- `GET /scale/api/list` → 磅秤列表

#### 7.8.2 过磅记录

**路由**：`GET /scale/records`

**页面**：`templates/scale/records.html`

**实现状态**：✅ 已实现记录列表、详情和看板查询接口

**详细需求**：

**页面功能**：
- 过磅记录列表（DataTable展示）
- 搜索筛选：按商户、磅秤、车牌号、日期范围
- 新增过磅记录（独立页面，输入项>5）
- 查看过磅单详情（模态框或打印）
- 自动计算：净重 = 毛重 - 皮重，总金额 = 净重 × 单价

**新增过磅记录表单字段**：
| 字段 | 必填 | 说明 |
|------|------|------|
| scale_id | 是 | 磅秤（下拉选择） |
| merchant_id | 是 | 商户（下拉选择） |
| gross_weight | 是 | 毛重 |
| tare_weight | 是 | 皮重 |
| unit_price | 是 | 单价（元/单位） |
| license_plate | 否 | 车牌号 |
| product_name | 否 | 产品名称 |
| operator | 是 | 操作员 |
| description | 否 | 描述 |
| scale_time | 是 | 过磅时间（默认当前时间） |

**自动计算**：
```
NetWeight = GrossWeight - TareWeight
TotalAmount = NetWeight × UnitPrice
```

**列表字段**：
| 列 | 说明 |
|----|------|
| 记录ID | ScaleRecordID |
| 磅秤 | ScaleName |
| 商户 | MerchantName |
| 毛重 | GrossWeight |
| 皮重 | TareWeight |
| 净重 | NetWeight |
| 单价 | UnitPrice |
| 总金额 | TotalAmount |
| 车牌号 | LicensePlate |
| 操作员 | Operator |
| 过磅时间 | ScaleTime |

**数据接口**：
- `GET /scale/api/records` → 分页列表
- `GET /scale/api/records/<int:record_id>` → 详情
- `GET /scale/api/dashboard/overview` → 今日概览
- `GET /scale/api/dashboard/trend` → 月趋势
- `GET /scale/api/dashboard/today` → 今日记录

---

## 8. 页面结构

### 8.1 管理端页面

```
/                              # 根路径（重定向到 /admin/）
/auth/                         # 系统首页（仪表盘）
/auth/login                    # 登录页面
/auth/register                 # 注册页面
/auth/logout                   # 登出

/user/list                     # 用户列表
/user/add                      # 添加用户（独立页面）
/user/edit/{id}                # 编辑用户（独立页面）
/user/change_password          # 修改密码

/merchant/list                 # 商户列表
/merchant/add                  # 添加商户（独立页面）
/merchant/edit/{id}            # 编辑商户（独立页面）

/plot/list                     # 地块列表
/plot/add                      # 添加地块（独立页面）
/plot/edit/{id}                # 编辑地块（AJAX提交）

/contract/list                 # 合同列表
/contract/add                  # 添加合同（独立页面）
/contract/edit/{id}            # 编辑合同（AJAX提交）

/utility/list                  # 水电表管理列表
/utility/water_meter           # 水表抄表
/utility/electricity_meter     # 电表抄表

/finance/receivable            # 应收账款管理
/finance/payable               # 应付账款管理
/finance/cash_flow             # 现金流水
/finance/list                  # 财务首页（重定向）
/finance/account               # 账户管理
/finance/direct_entry          # 直接记账
/finance/prepayment            # 预收/预付管理
/finance/deposit               # 押金管理

/scale/list                    # 磅秤列表
/scale/records                 # 过磅记录

/uploads/<path:filename>       # 上传文件访问（带路径遍历防护）
```

### 8.2 模板继承结构

```
base.html                     # 基础母版（Bootstrap5 + jQuery3.6.0 + FA4.7.0）
├── admin_base.html           # 管理端母版（带左侧导航+权限控制+用户信息）
├── public_base.html          # 公用母版（预留）
└── merchant_base.html        # 商户端母版（预留）
```

### 8.3 页面规则

- **输入项 ≤ 5个**：使用模态窗口在列表页面打开
- **输入项 > 5个**：使用独立页面
- **所有页面**：必须继承相应的母版模板
- **列表页面**：使用 DataTable 或自定义分页组件
- **操作反馈**：使用 Flash 消息或 Toast 提示

---

## 9. 技术债务清单

> 以下为当前代码中已识别的问题，需要后续修复。

### 9.1 架构违规 [高优先级]

| 编号 | 文件 | 问题 | 修复方案 |
|------|------|------|---------|
| TD-001 | `app/routes/contract.py` | 整个文件在 routes 层直接使用 `DBConnection` 执行SQL | 创建 `ContractService`，将所有数据库操作迁移 |
| TD-002 | `app/routes/plot.py` | 整个文件在 routes 层直接使用 `DBConnection` 执行SQL | 创建 `PlotService`，将所有数据库操作迁移 |
| TD-003 | `app/routes/finance.py` | 存在辅助函数直接使用 `DBConnection` 执行 SQL | 迁移到 `FinanceService` 或相关 repository |
| TD-004 | `app/routes/admin.py` | 仪表盘统计逻辑直接写在 routes 层 | 抽取到独立 dashboard service |

### 9.2 代码质量 [中优先级]

| 编号 | 文件 | 问题 | 修复方案 |
|------|------|------|---------|
| TD-005 | `app/extensions.py` | 死代码，未被任何文件引用 | 删除此文件 |
| TD-006 | `app/__init__.py` | 重复实例化 LoginManager/CSRFProtect | 统一使用 extensions.py 或删除 extensions.py |
| TD-007 | `app/routes/utility.py` | 大量 `print()` 调试语句（约15处） | 替换为 `logger.debug()` |
| TD-008 | `README.md` / `.env.example` / `config/*` | 配置说明曾长期分叉，需保持与正式入口一致 | 统一维护启动和环境变量文档 |

### 9.3 Bug修复 [高优先级]

| 编号 | 文件 | 问题 | 修复方案 |
|------|------|------|---------|
| TD-009 | `app/repositories/receivable_repo.py` | 表名错误：使用 `Receivables`（应为 `Receivable`） | 修正表名 |
| TD-010 | `app/repositories/receivable_repo.py` | 字段名使用 snake_case（如 `merchant_id`），应为 PascalCase（如 `MerchantID`） | 修正所有字段名 |

### 9.4 功能缺失 [待开发]

| 编号 | 模块 | 缺失内容 | 优先级 |
|------|------|---------|--------|
| TD-011 | 财务管理 | 财务详情查询与聚合逻辑下沉到 service / repository | 高 |
| TD-012 | 磅秤管理 | 补齐新增/编辑/删除与采集写入流程 | 高 |
| TD-013 | 合同管理 | ContractService 持续重构（将SQL从routes迁移） | 中 |
| TD-014 | 地块管理 | PlotService 持续重构（将SQL从routes迁移） | 中 |
| TD-015 | 用户管理 | 关联商户选择功能（当前硬编码为"无"） | 低 |
| TD-016 | 文档治理 | Spec 与代码保持同步，避免再次出现“空壳模块”误判 | 低 |

---

## 10. 已实现的特性（补充说明）

### 10.1 合同文档生成

- **实现文件**：`app/services/contract_doc_service.py`
- **模板**：`app/services/templates/` 中的 Word 模板（.docx）
- **功能**：
  - Jinja2模板渲染（docxtpl）
  - 自动插入关联地块图片（`_insert_plot_images()`）
  - 金额大写转换（`amount_to_chinese()`）
  - 文件命名安全处理

### 10.2 合同详情模态框

- 点击合同编号打开模态框查看详情（非跳转独立页面）
- 显示合同基本信息 + 关联地块列表 + 地块图片
- 支持生成和下载合同文档

### 10.3 抄表日期参数

- 水表/电表抄表页面支持 `?date=YYYY-MM-DD` URL参数
- 默认值为当月1号
- 用于外部链接跳转到指定月份的抄表页面

### 10.4 按合同设定水电费单价

- 电表/水表绑定合同时可设定单价
- 单价存储在 `ContractElectricityMeter.UnitPrice` / `ContractWaterMeter.UnitPrice`
- 抄表时自动使用合同绑定的单价计算费用

---

## 11. 开发执行指令

### 第一步：项目初始化 ✅ 已完成

- ✅ 创建项目目录结构
- ✅ 配置 Flask 应用（工厂模式）
- ✅ 配置数据库连接（utils/database.py + pyodbc）
- ✅ 创建基础模板
- ✅ 创建数据库初始化脚本

### 第二步：用户认证模块 ✅ 已完成

- ✅ RBAC权限控制（Role + Permission + RolePermission）
- ✅ 登录/登出/注册
- ✅ 密码修改
- ✅ 权限装饰器 `@check_permission()`

### 第三步：用户管理模块 ✅ 已完成

- ✅ CRUD完整实现（通过 UserService）
- ✅ 搜索和分页
- ✅ 角色分配

### 第四步：商户管理模块 ✅ 已完成

- ✅ CRUD完整实现（通过 MerchantService）
- ✅ 字典数据动态获取
- ✅ 搜索和分页

### 第五步：地块管理模块 ✅ 已完成（需重构）

- ✅ CRUD完整实现
- ✅ 图片上传/删除（带安全防护）
- ✅ 地块类型联动单价
- ⚠️ **架构违规**：SQL在routes层，需迁移到PlotService

### 第六步：合同管理模块 ✅ 已完成（需重构）

- ✅ CRUD完整实现
- ✅ 合同编号自动生成
- ✅ 合同文档生成/下载
- ✅ 合同详情模态框
- ⚠️ **架构违规**：SQL在routes层，需迁移到ContractService

### 第七步：水电计费模块 ✅ 已完成

- ✅ 水电表CRUD（通过UtilityService）
- ✅ 合同绑定/解绑
- ✅ 按合同设定单价
- ✅ 抄表提交 + 应收自动生成
- ✅ 日期参数支持

### 第八步：财务管理模块 ✅ 已进入可用阶段

- ✅ FinanceService 已实现核心联动逻辑
- ✅ 应收账款管理（列表/新增/收款/详情/软删除）
- ✅ 应付账款管理（列表/新增/付款/详情）
- ✅ 现金流水（列表/汇总）
- ✅ 账户、直接记账、预收/预付、押金管理已落地
- ⚠️ **待优化**：详情查询与统计聚合仍有部分逻辑位于 routes 层

### 第九步：磅秤管理模块 ✅ 已实现查询与看板

- ✅ ScaleService 已提供列表、记录、详情、统计能力
- ✅ 磅秤列表与过磅记录查询页面可用
- ✅ 今日概览、月趋势、当日记录接口已实现
- ⚠️ **待开发**：新增/编辑/删除与采集写入流程

### 第十步：架构重构 ⬜ 待执行

- ⬜ 创建 ContractService，迁移 contract.py 中的SQL
- ⬜ 创建 PlotService，迁移 plot.py 中的SQL
- ⬜ 清理 dead code（extensions.py、print调试语句）

### 第十一步：仪表盘与统计 ⬜ 待开始

- ⬜ 实现统计数据接口
- ⬜ 创建仪表盘页面
- ⬜ 实现数据可视化

---

## 12. 非功能需求

### 12.1 性能需求

| 编号 | 需求描述 | 指标 |
|------|---------|------|
| NFR-001 | 页面加载时间 | 普通页面加载时间不超过3秒 |
| NFR-002 | 数据查询响应 | 列表查询响应时间不超过2秒 |
| NFR-003 | 并发用户数 | 支持至少50个用户同时在线 |
| NFR-004 | 数据库性能 | 单表数据量支持100万条记录 |

### 12.2 安全需求

| 编号 | 需求描述 |
|------|---------|
| NFR-005 | 用户认证：所有用户必须登录后才能访问系统 |
| NFR-006 | 权限控制：基于RBAC模型实现细粒度权限控制 |
| NFR-007 | 密码加密：使用PBKDF2-SHA256加密存储 |
| NFR-008 | SQL注入防护：所有数据库操作使用参数化查询 |
| NFR-009 | CSRF防护：Flask-WTF CSRF Token验证 |
| NFR-010 | 文件上传安全：白名单扩展名、UUID重命名、路径遍历防护 |
| NFR-011 | 会话管理：24小时超时自动退出 |

### 12.3 可用性需求

| 编号 | 需求描述 |
|------|---------|
| NFR-012 | 界面友好：Bootstrap 5响应式设计 |
| NFR-013 | 操作简便：常用操作不超过3次点击 |
| NFR-014 | 错误提示：提供清晰的Flash/Toast错误提示 |
| NFR-015 | 交互优化：模态框查看详情，避免页面跳转 |

### 12.4 可维护性需求

| 编号 | 需求描述 |
|------|---------|
| NFR-016 | 代码规范：遵循PEP 8 |
| NFR-017 | 分层架构：Routes → Services → DBConnection |
| NFR-018 | 日志规范：使用logging模块，禁止print调试 |
| NFR-019 | 文档完善：Spec与代码保持同步 |

---

## 13. 验收标准

### 13.1 功能验收

- 所有功能模块按需求文档实现
- 功能测试通过率达到100%
- 无严重和重大缺陷

### 13.2 架构验收

- 所有模块遵循 Routes → Services → DBConnection 分层架构
- routes 层无任何 SQL 语句或 DBConnection 直接调用
- 无 print() 调试语句残留

### 13.3 安全验收

- 安全测试通过
- 无SQL注入风险
- 无路径遍历漏洞
- CSRF保护生效

---

## 14. 附录

### 14.1 术语表

| 术语 | 说明 |
|------|------|
| RBAC | 基于角色的访问控制 |
| CRUD | 创建、读取、更新、删除 |
| CSRF | 跨站请求伪造 |
| Blueprint | Flask蓝图（模块化路由） |
| DBConnection | 项目数据库连接上下文管理器 |
| docxtpl | Python Word模板渲染库 |

### 14.2 参考文档

- `docs/design/数据库设计.md` — 权威数据库结构设计
- `docs/目录结构设计.md` — 项目目录结构规范
- `docs/features/contract-document-generation.md` — 合同文档生成功能
- `docs/features/contract-view-modal.md` — 合同详情模态框
- `docs/水电表抄表日期参数功能说明.md` — 抄表日期参数
- `docs/水电费单价功能实现说明.md` — 按合同设定单价

### 14.3 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| V1.0 | 2026-03-30 | 初始版本 |
| V2.0 | 2026-03-30 | 补充数据库结构和业务规则 |
| V3.0 | 2026-04-13 | 全面对齐实际代码：修正技术栈（Flask 3.1.3+pyodbc）、更新数据库结构（以设计文档为准）、修正完成度、补充财务/磅秤详细需求、新增技术债务清单、新增已实现特性文档、新增架构规范 |

---

**文档结束**
