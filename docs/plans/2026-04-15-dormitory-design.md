# 宿舍管理模块设计说明

## 背景与目标

宏发金属交易市场有自建宿舍楼，按房间租赁给商户或个人居住，需要收取租金、水费（定额）和电费（抄表）。目前宿舍管理无系统化支持，需要新增宿舍管理模块实现：

- 房间信息管理（CRUD + 租金/水费/电费标准）
- 入住/退房管理（支持商户和个人两种租户类型，含身份证信息）
- 电表抄表（内嵌独立抄表功能，按月录入读数自动计算电费）
- 月度账单（自动汇总租金+水费+电费，确认后联动应收模块）

## 现状与约束

- **技术栈**：Flask 3.1.3 + pyodbc + Bootstrap 5.3.0 + jQuery 3.7.1
- **架构**：Routes → Services → DBConnection（禁止在routes层直接写SQL）
- **数据库**：SQL Server，字段命名 PascalCase
- **已有模块**：水电抄表（绑定商户）、应收/应付/现金流水（FinanceService）、往来客户（CustomerService）
- **文件上传**：已有 `uploads/` 目录 + `/uploads/<path:filename>` 路由
- **字典系统**：Sys_Dictionary 表管理所有枚举值
- **权限系统**：`@check_permission('xxx_manage')` 装饰器

## 方案对比

### 方案一：极简三表（Room + Reading + Bill）

房间表直接存当前租户信息，没有入住历史。

- 优点：最简单，开发快
- 缺点：换租户时历史丢失，无法追溯谁什么时候住过

### 方案二：四表分离（Room + Occupancy + Reading + Bill）⭐ 推荐

把入住关系独立出来，Room 只存房间物理信息，Occupancy 记录入住/退房。

- 优点：有完整入住历史，换租不断档；账单关联具体入住记录，金额可追溯
- 缺点：多一张表，逻辑稍复杂

### 方案三：复用铺面模式（模仿 Plot+Contract+Utility）

- 优点：和现有系统风格一致
- 缺点：过度设计，宿舍比铺面简单得多，不需要合同到期续签、保证金等逻辑

## 推荐方案

**方案二：四表分离**。宿舍管理核心就是"谁住了哪间房+每月收多少钱"，Occupancy 表精准对应"谁住了"的需求，又不引入合同那种重逻辑。多一张表的成本很小，但换来的追溯能力很有价值。

## 详细设计

### 数据库表结构

#### DormRoom（宿舍房间）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| RoomID | INT | PK, IDENTITY | 房间ID |
| RoomNumber | NVARCHAR(20) | NOT NULL, UNIQUE | 房间编号（如"宿舍101"） |
| RoomType | NVARCHAR(20) | NOT NULL | 房型（字典：dorm_room_type） |
| Area | DECIMAL(8,2) | NULL | 面积（㎡） |
| MonthlyRent | DECIMAL(10,2) | NOT NULL | 月租金 |
| WaterQuota | DECIMAL(10,2) | NOT NULL DEFAULT 0 | 每月水费定额 |
| ElectricityUnitPrice | DECIMAL(6,2) | NOT NULL DEFAULT 1.0 | 电费单价（元/度） |
| MeterNumber | NVARCHAR(30) | NULL | 电表号 |
| LastReading | DECIMAL(10,2) | NULL | 上次电表读数（冗余字段，方便显示） |
| Status | NVARCHAR(20) | NOT NULL DEFAULT N'空闲' | 状态（字典：dorm_room_status） |
| Description | NVARCHAR(200) | NULL | 备注 |
| CreateTime | DATETIME | DEFAULT GETDATE() | |
| UpdateTime | DATETIME | NULL | |

#### DormOccupancy（入住记录）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| OccupancyID | INT | PK, IDENTITY | 入住ID |
| RoomID | INT | NOT NULL, FK→DormRoom | 房间 |
| TenantType | NVARCHAR(20) | NOT NULL | 租户类型（字典：dorm_tenant_type：商户/个人） |
| MerchantID | INT | NULL | 关联商户（TenantType=商户时填写） |
| TenantName | NVARCHAR(50) | NOT NULL | 租户姓名 |
| TenantPhone | NVARCHAR(20) | NULL | 联系电话 |
| IDCardNumber | NVARCHAR(18) | NULL | 身份证号 |
| IDCardFrontPhoto | NVARCHAR(200) | NULL | 身份证正面照路径 |
| IDCardBackPhoto | NVARCHAR(200) | NULL | 身份证背面照路径 |
| MoveInDate | DATE | NOT NULL | 入住日期 |
| MoveOutDate | DATE | NULL | 退房日期（NULL=在住） |
| Status | NVARCHAR(20) | NOT NULL DEFAULT N'在住' | 状态（字典：dorm_occupancy_status） |
| Description | NVARCHAR(200) | NULL | 备注 |
| CreateTime | DATETIME | DEFAULT GETDATE() | |
| UpdateTime | DATETIME | NULL | |

#### DormReading（电表读数）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| ReadingID | INT | PK, IDENTITY | 读数ID |
| RoomID | INT | NOT NULL, FK→DormRoom | 房间 |
| YearMonth | NVARCHAR(7) | NOT NULL | 抄表月份（YYYY-MM） |
| PreviousReading | DECIMAL(10,2) | NOT NULL | 上次读数 |
| CurrentReading | DECIMAL(10,2) | NOT NULL | 本次读数 |
| Consumption | DECIMAL(10,2) | NOT NULL | 用电量 |
| UnitPrice | DECIMAL(6,2) | NOT NULL | 电费单价 |
| Amount | DECIMAL(10,2) | NOT NULL | 电费金额 |
| ReadingDate | DATE | NOT NULL | 抄表日期 |
| OccupancyID | INT | NULL | 关联入住记录 |
| CreateTime | DATETIME | DEFAULT GETDATE() | |

唯一约束：(RoomID, YearMonth)

#### DormBill（月度账单）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| BillID | INT | PK, IDENTITY | 账单ID |
| RoomID | INT | NOT NULL, FK→DormRoom | 房间 |
| OccupancyID | INT | NOT NULL, FK→DormOccupancy | 入住记录 |
| YearMonth | NVARCHAR(7) | NOT NULL | 账单月份 |
| RentAmount | DECIMAL(10,2) | NOT NULL DEFAULT 0 | 租金 |
| WaterAmount | DECIMAL(10,2) | NOT NULL DEFAULT 0 | 水费（定额） |
| ElectricityAmount | DECIMAL(10,2) | NOT NULL DEFAULT 0 | 电费 |
| TotalAmount | DECIMAL(10,2) | NOT NULL | 合计 |
| ReadingID | INT | NULL, FK→DormReading | 关联电表读数 |
| ReceivableID | INT | NULL | 关联应收（生成后回写） |
| Status | NVARCHAR(20) | NOT NULL DEFAULT N'待确认' | 状态（字典：dorm_bill_status） |
| CreateTime | DATETIME | DEFAULT GETDATE() | |

唯一约束：(RoomID, YearMonth)

### 字典数据

| 字典类型 | 字典编码 | 字典名称 |
|---|---|---|
| dorm_room_type | single | 单间 |
| dorm_room_type | standard | 标间 |
| dorm_room_type | suite | 套间 |
| dorm_room_status | vacant | 空闲 |
| dorm_room_status | occupied | 已住 |
| dorm_room_status | maintenance | 维修中 |
| dorm_tenant_type | merchant | 商户 |
| dorm_tenant_type | personal | 个人 |
| dorm_occupancy_status | living | 在住 |
| dorm_occupancy_status | moved_out | 已退房 |
| dorm_bill_status | pending | 待确认 |
| dorm_bill_status | confirmed | 已确认 |
| dorm_bill_status | invoiced | 已开账 |
| dorm_bill_status | settled | 已收清 |
| customer_type | dorm_personal | 宿舍个人 |
| expense_item_income | dorm_rent | 宿舍租金 |
| expense_item_income | dorm_water | 宿舍水费 |
| expense_item_income | dorm_electricity | 宿舍电费 |

### 权限

- `dorm_manage`：宿舍管理权限，赋给 admin + staff 角色

### 业务流程

```
1. 录入房间 → 2. 办理入住 → 3. 每月抄电表 → 4. 生成月度账单 → 5. 确认开账 → 6. 缴费核销
      ↑                ↓                                    ↓
   房间管理        退房（释放房间）                      联动应收模块
```

### 财务联动逻辑

账单确认 → create_receivable：

1. 按 TenantType 确定客户：
   - 商户 → Customer 表查找/创建（关联 MerchantID）
   - 个人 → Customer 表查找/创建（按姓名+手机号，CustomerType=宿舍个人）
2. 创建3条 Receivable（宿舍租金/宿舍水费/宿舍电费）
3. 回写 ReceivableID 到 DormBill
4. DormBill.Status → '已开账'
5. 缴费走现有 finance.receivable 收款核销流程

### 页面与接口

#### 页面（4个）

| 页面 | 路由 | 功能 |
|---|---|---|
| 房间管理 | /dorm/rooms | 房间CRUD + 查看当前入住人 + 快速入住/退房入口 |
| 入住管理 | /dorm/occupancy | 入住/退房记录列表，查看身份证照片 |
| 电表抄表 | /dorm/reading | 按月批量录入电表读数 |
| 月度账单 | /dorm/bill | 按月生成/确认账单，联动应收 |

#### 接口清单

**房间管理**

| 方法 | 路由 | 说明 |
|---|---|---|
| GET | /dorm/rooms | 房间管理页面 |
| GET | /dorm/rooms/list | 房间列表（支持状态/类型筛选+搜索） |
| POST | /dorm/rooms/add | 新增房间 |
| POST | /dorm/rooms/edit/\<id\> | 编辑房间 |
| POST | /dorm/rooms/delete/\<id\> | 删除房间（仅空闲可删） |

**入住管理**

| 方法 | 路由 | 说明 |
|---|---|---|
| GET | /dorm/occupancy | 入住管理页面 |
| GET | /dorm/occupancy/list | 入住记录列表 |
| POST | /dorm/occupancy/check_in | 办理入住 |
| POST | /dorm/occupancy/check_out/\<id\> | 办理退房 |
| POST | /dorm/upload_idcard | 上传身份证照片 |

**电表抄表**

| 方法 | 路由 | 说明 |
|---|---|---|
| GET | /dorm/reading | 抄表页面 |
| GET | /dorm/reading/list | 某月抄表记录 |
| POST | /dorm/reading/save | 保存电表读数 |
| GET | /dorm/reading/room_status | 获取需抄表的在住房间列表 |

**月度账单**

| 方法 | 路由 | 说明 |
|---|---|---|
| GET | /dorm/bill | 账单页面 |
| GET | /dorm/bill/list | 某月账单列表 |
| POST | /dorm/bill/generate | 批量生成月度账单 |
| POST | /dorm/bill/confirm/\<id\> | 确认单条账单 |
| POST | /dorm/bill/batch_confirm | 批量确认 |
| POST | /dorm/bill/create_receivable/\<id\> | 开账→联动应收 |

### 导航入口

市场管理下拉菜单内，磅秤数据下方加分隔线，新增宿舍管理4项：

```
市场管理 ▾
├── 商户管理
├── 地块管理
├── 合同管理
├── 水电计费
├── 磅秤数据
├── ─────────
├── 宿舍房间    fa-bed
├── 入住管理    fa-sign-in
├── 电表抄表    fa-bolt
└── 宿舍账单    fa-file-invoice
```

### 异常与边界处理

| 场景 | 处理方式 |
|---|---|
| 房间已住，再次入住 | 拒绝，提示"该房间已有在住人员，请先办理退房" |
| 退房时当月账单未结 | 允许退房，账单保持"已开账"状态，需正常缴费核销 |
| 退房时当月未抄表 | 警告提示，允许强制退房，按上次读数生成账单 |
| 月末生成账单时房间无人住 | 跳过，不生成账单 |
| 月中入住/退房 | 按整月收租金和水费（不做按天折算），电费按实际抄表 |
| 电表读数小于上次 | 拒绝保存，提示"读数不能小于上次读数" |
| 重复生成同月账单 | 拒绝，唯一约束 (RoomID+YearMonth) 兜底 |
| 删除房间 | 仅"空闲"状态可删 |
| 个人租户在Customer表重复 | 按姓名+手机号查重复用 |
| 身份证照片上传 | 预检 ≤5MB，仅 jpg/png |

### 不做的事（YAGNI）

- ❌ 按天折算租金
- ❌ 宿舍合同管理
- ❌ 水表抄表（水费固定定额）
- ❌ 宿舍可视化/3D
- ❌ 商户门户宿舍自助查询

## 风险与待确认项

- 月中入住/退房按整月收费，后续如需按天折算需额外开发
- 个人租户在 Customer 表的统一管理需确认是否影响其他模块
- 身份证照片的隐私保护，目前仅登录后可访问，无额外权限控制
