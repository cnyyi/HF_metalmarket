# 垃圾费管理模块设计

## 概述

新增垃圾费管理模块，按商户业态类型及租赁面积核算垃圾费，独立于现有垃圾清运模块。

- 现有垃圾清运模块（`/garbage`）：市场向供应商支付清运费 → 应付账款
- 新垃圾费模块（`/garbage_fee`）：向商户收取垃圾费 → 应收账款

## 核心规则

| 项目 | 说明 |
|------|------|
| 计算公式 | 垃圾费 = max(业态单价 × 租赁面积, 保底金额) |
| 面积单位 | 亩 |
| 面积来源 | 商户当前有效合同关联地块面积合计（SUM(ContractPlot.Area)） |
| 单价来源 | Sys_Dictionary 中 business_type 字典项的 UnitPrice 字段 |
| 保底金额 | Sys_Dictionary 中 business_type 字典项的 MinAmount 字段 |
| 计费周期 | 按年 |
| 生成方式 | 批量生成所有商户，生成后可单个修改 |
| 应收联动 | 自动创建 Receivable，金额变更时联动更新 |

## 数据库设计

### Sys_Dictionary 表扩展

新增 `MinAmount` 字段：

```sql
ALTER TABLE Sys_Dictionary ADD MinAmount DECIMAL(10,2) NULL;
```

为 `business_type` 字典项设置垃圾费单价和保底金额（通过字典管理页面维护）：

| DictCode | DictName | UnitPrice(元/亩/年) | MinAmount(保底/年) |
|----------|----------|---------------------|-------------------|
| metal_material | 金属材料 | 待设置 | 待设置 |
| hardware | 五金工具 | 待设置 | 待设置 |
| machinery | 机械配件 | 待设置 | 待设置 |
| equipment | 设备租赁 | 待设置 | 待设置 |

新增收入类费用项字典：

```sql
INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive)
VALUES (N'expense_item_income', N'garbage_fee', N'垃圾费', N'商户垃圾费收入', 8, 1);
```

### GarbageFee 表

```sql
CREATE TABLE GarbageFee (
    GarbageFeeID    INT IDENTITY(1,1) PRIMARY KEY,
    MerchantID      INT NOT NULL,
    Year            INT NOT NULL,
    BusinessType    NVARCHAR(100) NULL,
    RentalArea      DECIMAL(10,2) NULL,
    UnitPrice       DECIMAL(10,2) NULL,
    MinAmount       DECIMAL(10,2) NULL,
    CalculatedFee   DECIMAL(10,2) NULL,
    FinalFee        DECIMAL(10,2) NOT NULL,
    ReceivableID    INT NULL,
    Status          NVARCHAR(20) NOT NULL DEFAULT N'待收取',
    Description     NVARCHAR(500) NULL,
    CreateBy        INT NULL,
    CreateTime      DATETIME NULL DEFAULT GETDATE(),
    UpdateBy        INT NULL,
    UpdateTime      DATETIME NULL,
    CONSTRAINT UQ_GarbageFee_Merchant_Year UNIQUE (MerchantID, Year)
);
```

字段说明：
- `BusinessType`、`RentalArea`、`UnitPrice`、`MinAmount` 为快照字段，生成时从字典/合同读取并固化
- `CalculatedFee` = UnitPrice × RentalArea
- `FinalFee` = max(CalculatedFee, MinAmount)，为实际收取金额
- `UNIQUE (MerchantID, Year)` 确保每商户每年只生成一条

## 业务流程

### 批量生成流程

1. 用户选择年度，点击批量生成
2. 系统查询所有有有效合同的商户
3. 对每个商户：
   - 汇总有效合同关联地块面积 → RentalArea
   - 读取商户 BusinessType → 查字典获取 UnitPrice 和 MinAmount
   - CalculatedFee = UnitPrice × RentalArea
   - FinalFee = max(CalculatedFee, MinAmount)
   - 插入 GarbageFee 记录
   - 联动创建 Receivable（费用类型=垃圾费）
   - 回写 ReceivableID 到 GarbageFee
4. 返回生成结果（成功N条，跳过N条已存在，错误N条）

跳过规则：
- 该商户该年度已有 GarbageFee 记录 → 跳过
- 商户未设置 BusinessType 或字典中无对应单价 → 跳过并在结果中提示

### 应收账款联动规则

| 操作 | Receivable 联动 |
|------|----------------|
| 批量生成 | 自动创建 Receivable，费用类型为"垃圾费" |
| 修改金额（FinalFee 变更） | 更新 Receivable 的 Amount 和 RemainingAmount（仅未收款状态） |
| 修改状态→已收取 | 更新 Receivable 状态为已收款 |
| 删除记录 | 保留 Receivable（由应收管理模块处理），解除关联 |

### 面积计算 SQL

```sql
SELECT SUM(cp.Area)
FROM ContractPlot cp
JOIN Contract c ON cp.ContractID = c.ContractID
WHERE c.MerchantID = ?
  AND c.Status = N'有效'
  AND c.StartDate <= ?
  AND c.EndDate >= ?
```

## 路由设计

| URL | 方法 | 权限 | 说明 |
|-----|------|------|------|
| `/garbage_fee/` | GET | garbage_fee_view | 列表页 |
| `/garbage_fee/list` | GET | garbage_fee_view | 列表数据 API |
| `/garbage_fee/generate` | GET | garbage_fee_create | 批量生成页面 |
| `/garbage_fee/generate` | POST | garbage_fee_create | 执行批量生成 |
| `/garbage_fee/edit/<id>` | POST | garbage_fee_edit | 更新记录（模态窗口提交） |
| `/garbage_fee/detail/<id>` | GET | garbage_fee_view | 详情页面 |
| `/garbage_fee/detail/<id>/data` | GET | garbage_fee_view | 详情数据 API |
| `/garbage_fee/delete/<id>` | POST | garbage_fee_delete | 删除记录 |
| `/garbage_fee/export` | GET | garbage_fee_view | 导出 Excel |

## 页面设计

### 列表页（garbage_fee/list.html）

- 筛选条件：年度、业态类型、状态、搜索（商户名）
- 表格列：序号、商户名称、年度、业态类型、租赁面积(亩)、业态单价、保底金额、计算金额、最终金额、状态、操作
- 合计行：汇总面积和金额
- 操作按钮：批量生成、导出 Excel
- 编辑模态窗口：点击编辑按钮弹出 Modal，包含可编辑字段（面积、单价、保底、最终金额、状态、备注），Ajax 提交

### 批量生成页（garbage_fee/generate.html）

- 选择年度（下拉或输入）
- 预览：显示待生成的商户列表（商户名、业态、面积、单价、保底、预计金额）
- 确认生成按钮

### 详情页（garbage_fee/detail.html）

- 展示所有字段，含关联应收账款信息

## 服务层设计

### GarbageFeeService 主要方法

```python
class GarbageFeeService:
    def get_list(page, per_page, year, business_type, status, search)
    def get_detail(garbage_fee_id)
    def batch_generate(year, created_by)
    def update_fee(garbage_fee_id, rental_area, unit_price, min_amount, final_fee, status, description, updated_by)
    def delete_fee(garbage_fee_id)
    def get_preview(year)
    def get_merchants_with_contracts(year)
    def export_fees(year, business_type, status, search)
```

## 文件结构

```
app/routes/garbage_fee.py
app/services/garbage_fee_service.py
templates/garbage_fee/
    list.html
    generate.html
    detail.html
scripts/add_garbage_fee_tables.sql
```

## 权限项

- garbage_fee_view
- garbage_fee_create
- garbage_fee_edit
- garbage_fee_delete
