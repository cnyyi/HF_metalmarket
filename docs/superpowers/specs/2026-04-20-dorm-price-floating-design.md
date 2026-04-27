# 宿舍管理业务逻辑调整设计 — 价格浮动与水费双模式

> **目标：** 将宿舍租金和水电单价从房间级别移到入住级别，支持每次入住期间价格不同；水费支持定额和抄表两种模式。

---

## 1. 需求背景

当前宿舍的月租金（MonthlyRent）、水费定额（WaterQuota）、电费单价（ElectricityUnitPrice）都存储在 DormRoom 表上，是房间级别的固定值。实际业务中租赁价格存在浮动，同一房间不同入住期间的单价可能不同。此外，部分宿舍有水表需要抄表计费，部分没有水表只能按定额收取。

## 2. 设计方案

**方案：在 DormOccupancy 表上增加价格字段，入住时确定，期间不变。**

房间表保留价格字段作为默认值来源，入住时自动填入，用户可修改。

## 3. 数据库变更

### 3.1 DormOccupancy 表新增字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| MonthlyRent | DECIMAL(10,2) | 0 | 本次入住月租金 |
| WaterMode | NVARCHAR(10) | N'quota' | 水费模式：quota(定额)/meter(抄表) |
| WaterQuota | DECIMAL(10,2) | 0 | 水费定额（WaterMode=quota时使用） |
| WaterUnitPrice | DECIMAL(6,2) | 0 | 水费单价（WaterMode=meter时使用） |
| ElectricityUnitPrice | DECIMAL(6,2) | 1.0 | 电费单价 |

### 3.2 DormRoom 表新增字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| WaterMode | NVARCHAR(10) | N'quota' | 默认水费模式：quota(定额)/meter(抄表) |
| WaterUnitPrice | DECIMAL(6,2) | 0 | 默认水费单价 |

DormRoom 保留的现有字段（作为默认值来源）：
- MonthlyRent — 默认月租金
- WaterQuota — 默认水费定额
- ElectricityUnitPrice — 默认电费单价

### 3.3 新增 DormWaterReading 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| ReadingID | INT | PK, IDENTITY | 读数ID |
| RoomID | INT | NOT NULL, FK→DormRoom | 房间 |
| YearMonth | NVARCHAR(7) | NOT NULL | 抄表月份 YYYY-MM |
| PreviousReading | DECIMAL(10,2) | DEFAULT 0 | 上次读数 |
| CurrentReading | DECIMAL(10,2) | DEFAULT 0 | 本次读数 |
| Consumption | DECIMAL(10,2) | DEFAULT 0 | 用水量 |
| UnitPrice | DECIMAL(6,2) | DEFAULT 0 | 水费单价 |
| Amount | DECIMAL(10,2) | DEFAULT 0 | 水费金额 |
| ReadingDate | DATE | NOT NULL | 抄表日期 |
| OccupancyID | INT | NULL, FK→DormOccupancy | 关联入住记录 |
| CreateTime | DATETIME | DEFAULT GETDATE() | |

唯一约束：`UQ_DormWaterReading_Room_Month` (RoomID, YearMonth)

### 3.4 字典数据新增

| 字典类型 | 编码 | 名称 |
|----------|------|------|
| dorm_water_mode | quota | 定额 |
| dorm_water_mode | meter | 抄表 |

## 4. 业务逻辑变更

### 4.1 入住流程（check_in）

1. 选择房间后，从 DormRoom 读取默认价格，填充到表单：
   - MonthlyRent ← DormRoom.MonthlyRent
   - WaterMode ← DormRoom.WaterMode
   - WaterQuota ← DormRoom.WaterQuota
   - WaterUnitPrice ← DormRoom.WaterUnitPrice
   - ElectricityUnitPrice ← DormRoom.ElectricityUnitPrice
2. 用户可修改各项价格
3. 提交后写入 DormOccupancy 的价格字段

### 4.2 账单生成（generate_bills）

- **租金**：从 DormOccupancy.MonthlyRent 读取（不再从 DormRoom）
- **水费**：
  - WaterMode=quota 时：取 DormOccupancy.WaterQuota 作为定额
  - WaterMode=meter 时：取 DormWaterReading.Amount
- **电费**：取 DormReading.Amount（单价从 DormOccupancy.ElectricityUnitPrice）

### 4.3 抄表流程

- **电表抄表**：不变，仍用 DormReading
- **水表抄表**：新增，使用 DormWaterReading，流程与电表类似
  - 仅 WaterMode=meter 的在住房间需要水表抄表
  - 抄表时从 DormOccupancy.WaterUnitPrice 读取单价

### 4.4 开账联动（create_receivable）

- 租金应收：金额取 DormOccupancy.MonthlyRent
- 水费应收：金额根据 WaterMode 取定额或抄表金额
- 电费应收：不变

## 5. 前端变更

### 5.1 入住表单

增加字段：月租金、水费模式（定额/抄表）、水费定额、水费单价、电费单价
- 选择房间后自动填充默认值
- 水费模式切换时显示/隐藏定额和单价字段

### 5.2 房间管理

增加字段：水费模式、水费单价（编辑房间时可设置默认值）

### 5.3 抄表页面

增加水表抄表 Tab：
- 仅显示 WaterMode=meter 的在住房间
- 流程与电表抄表一致

### 5.4 账单页面

水费列显示逻辑：
- WaterMode=quota 时显示定额金额
- WaterMode=meter 时显示抄表金额

## 6. SQL 迁移脚本

需编写迁移脚本：
1. DormOccupancy 表新增 5 个字段
2. DormRoom 表新增 2 个字段
3. 创建 DormWaterReading 表
4. 将现有 DormRoom 的价格数据回写到当前在住的 DormOccupancy 记录
