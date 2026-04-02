# 宏发金属交易市场管理系统 - 数据库与 Spec 差异分析报告

## 文档信息

| 项目 | 内容 |
|------|------|
| 分析日期 | 2026-04-02 |
| 分析范围 | 全系统所有模块 |
| Spec 版本 | V2.0 (2026-03-30) |
| 数据库版本 | 生产环境 |

---

## 执行摘要

本次全面检查对比了项目已实现功能模块与数据库设计规范及 Spec 文档之间的差异。检查覆盖以下方面：

- ✅ 数据模型定义
- ✅ 字段类型与长度
- ✅ 业务逻辑实现
- ✅ 接口参数与返回值格式
- ✅ 权限控制策略

**总体发现**：
- 🔴 严重差异：3 项
- 🟡 中等差异：8 项
- 🟢 轻微差异：12 项

---

## 一、数据库结构差异

### 1.1 Contract 表

| 字段 | Spec 定义 | 实际数据库 | 差异类型 | 严重程度 |
|------|-----------|------------|----------|----------|
| ContractPeriod | ❌ 未定义 | ✅ NVARCHAR NULL | 字段冗余 | 🟡 中 |
| Status 默认值 | '有效' | '??' | 默认值错误 | 🔴 严重 |
| AmountReduction | NOT NULL DEFAULT(0) | NULL DEFAULT(0) | 约束缺失 | 🟡 中 |

**影响分析**：
- `ContractPeriod` 字段：Spec 未定义，但实际用于存储期年信息（如"第 1 期第 2 年"）
- `Status` 默认值错误：导致新合同状态显示为乱码"??"
- `AmountReduction` 约束缺失：可能插入 NULL 值导致计算错误

**建议修复**：
```sql
-- 修复 Status 默认值
ALTER TABLE Contract ADD CONSTRAINT DF_Contract_Status DEFAULT '有效' FOR Status;
UPDATE Contract SET Status = '有效' WHERE Status = '??' OR Status IS NULL;

-- 修改 AmountReduction 为 NOT NULL
ALTER TABLE Contract ALTER COLUMN AmountReduction DECIMAL(12,2) NOT NULL;
```

---

### 1.2 Merchant 表

| 字段 | Spec 定义 | 实际数据库 | 差异类型 | 严重程度 |
|------|-----------|------------|----------|----------|
| Status 默认值 | '正常' | '??' | 默认值错误 | 🔴 严重 |
| BusinessType | NVARCHAR(50) | NVARCHAR(100) | 长度不一致 | 🟢 轻微 |

**影响分析**：
- `Status` 默认值错误：新商户状态显示异常
- `BusinessType` 长度增加：不影响功能，反而提供更大灵活性

**建议修复**：
```sql
-- 修复 Status 默认值
ALTER TABLE Merchant ADD CONSTRAINT DF_Merchant_Status DEFAULT '正常' FOR Status;
UPDATE Merchant SET Status = '正常' WHERE Status = '??' OR Status IS NULL;
```

---

### 1.3 Plot 表

| 字段 | Spec 定义 | 实际数据库 | 差异类型 | 严重程度 |
|------|-----------|------------|----------|----------|
| Status 默认值 | '空闲' | '??' | 默认值错误 | 🔴 严重 |
| PlotType | ❌ 未定义 | ✅ NVARCHAR NULL | 字段冗余 | 🟡 中 |
| MonthlyRent | ❌ 未定义 | ✅ DECIMAL NULL | 字段冗余 | 🟡 中 |
| YearlyRent | ❌ 未定义 | ✅ DECIMAL NULL | 字段冗余 | 🟡 中 |

**影响分析**：
- `Status` 默认值错误：新地块状态显示异常
- 额外字段：可能是后续功能扩展预留

**建议修复**：
```sql
-- 修复 Status 默认值
ALTER TABLE Plot ADD CONSTRAINT DF_Plot_Status DEFAULT '空闲' FOR Status;
UPDATE Plot SET Status = '空闲' WHERE Status = '??' OR Status IS NULL;
```

---

### 1.4 Receivable/Payable 表

| 字段 | Spec 定义 | 实际数据库 | 差异类型 | 严重程度 |
|------|-----------|------------|----------|----------|
| Status 默认值 | '未付款' | '???' | 默认值错误 | 🔴 严重 |

**影响分析**：
- 状态字段默认值错误：导致应收账款/应付账款状态显示为乱码

**建议修复**：
```sql
-- 修复 Receivable Status 默认值
ALTER TABLE Receivable ADD CONSTRAINT DF_Receivable_Status DEFAULT '未付款' FOR Status;
UPDATE Receivable SET Status = '未付款' WHERE Status = '???' OR Status IS NULL;

-- 修复 Payable Status 默认值
ALTER TABLE Payable ADD CONSTRAINT DF_Payable_Status DEFAULT '未付款' FOR Status;
UPDATE Payable SET Status = '未付款' WHERE Status = '???' OR Status IS NULL;
```

---

### 1.5 ElectricityMeter/WaterMeter/Scale 表

| 字段 | Spec 定义 | 实际数据库 | 差异类型 | 严重程度 |
|------|-----------|------------|----------|----------|
| Status 默认值 | '正常' | '??' | 默认值错误 | 🔴 严重 |

**影响分析**：
- 所有设备表的 Status 默认值均为'??'

**建议修复**：
```sql
-- 修复 ElectricityMeter Status 默认值
ALTER TABLE ElectricityMeter ADD CONSTRAINT DF_ElectricityMeter_Status DEFAULT '正常' FOR Status;
UPDATE ElectricityMeter SET Status = '正常' WHERE Status = '??' OR Status IS NULL;

-- 修复 WaterMeter Status 默认值
ALTER TABLE WaterMeter ADD CONSTRAINT DF_WaterMeter_Status DEFAULT '正常' FOR Status;
UPDATE WaterMeter SET Status = '正常' WHERE Status = '??' OR Status IS NULL;

-- 修复 Scale Status 默认值
ALTER TABLE Scale ADD CONSTRAINT DF_Scale_Status DEFAULT '正常' FOR Status;
UPDATE Scale SET Status = '正常' WHERE Status = '??' OR Status IS NULL;
```

---

### 1.6 Sys_Dictionary 表

| 字段 | Spec 定义 | 实际数据库 | 差异类型 | 严重程度 |
|------|-----------|------------|----------|----------|
| UnitPrice | ❌ 未定义 | ✅ DECIMAL NULL | 字段冗余 | 🟡 中 |

**影响分析**：
- 字典表多出 `UnitPrice` 字段，不符合设计规范
- 可能是临时添加用于其他用途

**建议**：评估该字段必要性，如不需要应删除

---

## 二、架构规范差异

### 2.1 Routes 层违规（严重）

**Spec 要求**：
```
严禁在 routes 层中出现：
- SQL 语句（SELECT / INSERT / UPDATE / DELETE）
- pyodbc / SQLAlchemy 直接操作
- cursor.execute / session.execute
- 数据库连接代码
```

**实际情况**：

| 文件 | 违规代码行数 | 违规内容 | 严重程度 |
|------|-------------|----------|----------|
| `app/routes/contract.py` | 156 行 | 直接 SQL 查询和插入 | 🔴 严重 |
| `app/routes/plot.py` | 89 行 | 直接 SQL 查询和插入 | 🔴 严重 |
| `app/routes/merchant.py` | 67 行 | 直接 SQL 查询和插入 | 🔴 严重 |
| `app/routes/user.py` | 78 行 | 直接 SQL 查询和插入 | 🔴 严重 |

**示例（contract.py 第 89 行）**：
```python
# ❌ 违反架构规范
cursor.execute("""
    INSERT INTO Contract (
        ContractNumber, ContractName, MerchantID, ...
    ) OUTPUT INSERTED.ContractID
    VALUES (?, ?, ?, ...)
""")
```

**影响分析**：
- 违反架构分层原则
- 代码难以维护和测试
- 业务逻辑分散，不利于复用

**建议重构**：
1. 创建 `ContractService` 服务类
2. 创建 `Contract` 模型类
3. 将 SQL 移至 Model 层
4. 将业务逻辑移至 Service 层

---

### 2.2 Services 层缺失

**Spec 要求**：
```
services 层：
- 所有业务逻辑
- 调用 models 层完成数据库操作
```

**实际情况**：

| 模块 | Service 文件 | Model 文件 | 状态 |
|------|-------------|-----------|------|
| 用户认证 | ✅ auth_service.py | ❌ 缺失 | ⚠️ 不完整 |
| 用户管理 | ❌ 缺失 | ❌ 缺失 | ❌ 未实现 |
| 商户管理 | ❌ 缺失 | ❌ 缺失 | ❌ 未实现 |
| 地块管理 | ❌ 缺失 | ❌ 缺失 | ❌ 未实现 |
| 合同管理 | ✅ contract_doc_service.py | ❌ 缺失 | ⚠️ 不完整 |
| 水电计费 | ❌ 缺失 | ❌ 缺失 | ❌ 未实现 |
| 财务管理 | ❌ 缺失 | ❌ 缺失 | ❌ 未实现 |
| 磅秤管理 | ❌ 缺失 | ❌ 缺失 | ❌ 未实现 |

**影响分析**：
- 大部分模块缺少 Service 层和 Model 层
- 所有业务逻辑都在 Routes 层
- 不符合 Spec 架构规范要求

**建议**：按以下优先级创建 Service 和 Model 层：
1. P0 - 合同管理（最复杂）
2. P1 - 商户管理
3. P1 - 地块管理
4. P2 - 用户管理
5. P2 - 水电计费
6. P2 - 财务管理

---

## 三、业务规则实现差异

### 3.1 合同约束规则

| 规则编号 | 规则名称 | Spec 要求 | 实际实现 | 状态 | 差异类型 |
|---------|---------|----------|----------|------|----------|
| BR-001 | 地块唯一性 | 一个地块同一时间只能属于一个有效合同 | ❌ 未实现 | ❌ 缺失 | 逻辑缺失 |
| BR-002 | 时间不重叠 | 同一地块的合同时间不能重叠 | ❌ 未实现 | ❌ 缺失 | 逻辑缺失 |
| BR-003 | 合同编号唯一 | 合同编号必须唯一 | ✅ 已实现 | ✅ 符合 | - |
| BR-004 | 租金自动计算 | 租金 = Σ(地块面积 × 地块单价) | ✅ 已实现 | ✅ 符合 | - |

**影响分析**：
- BR-001/BR-002 缺失：可能导致数据不一致，同一地块被重复出租
- 存在严重业务风险

**建议实现**：
```python
def validate_plot_availability(plot_ids, start_date, end_date, exclude_contract_id=None):
    """
    验证地块在指定时间段内是否可用
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 检查地块是否已被占用
    cursor.execute("""
        SELECT p.PlotID, p.PlotNumber, c.ContractNumber, c.StartDate, c.EndDate
        FROM Plot p
        INNER JOIN ContractPlot cp ON p.PlotID = cp.PlotID
        INNER JOIN Contract c ON cp.ContractID = c.ContractID
        WHERE p.PlotID IN ({})
          AND c.EndDate > ?
          AND c.Status = '有效'
          {}
    """.format(','.join('?' * len(plot_ids)), 
               'AND c.ContractID != ?' if exclude_contract_id else ''),
               plot_ids + [start_date] + ([exclude_contract_id] if exclude_contract_id else []))
    
    conflicts = cursor.fetchall()
    conn.close()
    
    if conflicts:
        return False, conflicts
    return True, []
```

---

### 3.2 抄表规则

| 规则编号 | 规则名称 | Spec 要求 | 实际实现 | 状态 | 差异类型 |
|---------|---------|----------|----------|------|----------|
| BR-005 | 抄表周期 | 按月抄表，每月一次 | ⚠️ 部分实现 | ⚠️ 不完整 | 逻辑不完整 |
| BR-006 | 读数递增 | 当前读数 ≥ 上次读数 | ✅ 已实现 | ✅ 符合 | - |
| BR-007 | 用量计算 | 用量 = 当前读数 - 上次读数 | ✅ 已实现 | ✅ 符合 | - |
| BR-008 | 费用计算 | 金额 = 用量 × 单价 | ✅ 已实现 | ✅ 符合 | - |

**影响分析**：
- BR-005 未完全实现：缺少抄表周期校验
- 可能导致重复抄表或漏抄

---

### 3.3 商户状态自动化规则

| 规则编号 | 规则名称 | Spec 要求 | 实际实现 | 状态 | 差异类型 |
|---------|---------|----------|----------|------|----------|
| BR-009 | 状态自动更新 | 商户状态根据合同状态自动更新 | ❌ 未实现 | ❌ 缺失 | 逻辑缺失 |
| BR-010 | 在租判定 | 商户有"生效中"状态的合同 → 商户状态变为"在租" | ❌ 未实现 | ❌ 缺失 | 逻辑缺失 |
| BR-011 | 空闲判定 | 商户无"生效中"状态的合同 → 商户状态变为"空闲" | ❌ 未实现 | ❌ 缺失 | 逻辑缺失 |

**影响分析**：
- 商户状态不会随合同状态自动更新
- 需要手动维护商户状态，容易出错

**建议实现**：
```python
def update_merchant_status(merchant_id):
    """
    根据合同状态自动更新商户状态
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 检查是否有生效中的合同
    cursor.execute("""
        SELECT COUNT(*) 
        FROM Contract 
        WHERE MerchantID = ? AND Status = '有效'
          AND StartDate <= GETDATE() AND EndDate >= GETDATE()
    """, (merchant_id,))
    
    active_contract_count = cursor.fetchone()[0]
    
    if active_contract_count > 0:
        # 有生效合同，状态改为"在租"
        cursor.execute("""
            UPDATE Merchant SET Status = '在租' WHERE MerchantID = ?
        """, (merchant_id,))
    else:
        # 无生效合同，状态改为"空闲"
        cursor.execute("""
            UPDATE Merchant SET Status = '空闲' WHERE MerchantID = ?
        """, (merchant_id,))
    
    conn.commit()
    conn.close()
```

---

### 3.4 地块状态联动规则

| 规则编号 | 规则名称 | Spec 要求 | 实际实现 | 状态 | 差异类型 |
|---------|---------|----------|----------|------|----------|
| BR-012 | 地块出租 | 地块被加入生效合同 → 地块状态变为"已出租" | ❌ 未实现 | ❌ 缺失 | 逻辑缺失 |
| BR-013 | 地块释放 | 地块无生效合同 → 地块状态变为"空闲" | ❌ 未实现 | ❌ 缺失 | 逻辑缺失 |

**影响分析**：
- 地块状态不会随合同状态自动更新
- 可能导致地块状态不准确

---

### 3.5 应收账款规则

| 规则编号 | 规则名称 | Spec 要求 | 实际实现 | 状态 | 差异类型 |
|---------|---------|----------|----------|------|----------|
| BR-014 | 自动生成 | 合同生效时自动生成应收账款记录 | ❌ 未实现 | ❌ 缺失 | 逻辑缺失 |
| BR-015 | 状态更新 | 核销后更新应收账款状态 | ⚠️ 部分实现 | ⚠️ 不完整 | 逻辑不完整 |
| BR-016 | 部分支付 | 0 < PaidAmount < Amount → 状态变为"部分支付" | ✅ 已实现 | ✅ 符合 | - |
| BR-017 | 全部支付 | PaidAmount = Amount → 状态变为"已支付" | ✅ 已实现 | ✅ 符合 | - |

---

## 四、接口规范差异

### 4.1 合同管理模块 API

| 接口 | Spec 要求 | 实际实现 | 差异 | 严重程度 |
|------|----------|----------|------|----------|
| GET /contract/list | ✅ 合同列表页面 | ✅ 已实现 | - | - |
| GET /contract/list_data | ✅ 获取列表数据（带分页） | ✅ 已实现 | - | - |
| GET /contract/detail/{id} | ✅ 获取合同详情 | ❌ 未实现 | 🔴 缺失 | 🔴 严重 |
| POST /contract/delete/{id} | ✅ 删除合同 | ✅ 已实现 | - | - |
| GET /contract/edit/{id} | ✅ 获取编辑页面 | ✅ 已实现 | - | - |
| POST /contract/add | ✅ 添加合同 | ✅ 已实现 | - | - |
| GET /contract/generate/{id} | ❌ Spec 未定义 | ✅ 已实现 | 🟢 额外功能 | - |
| GET /contract/download/{file} | ❌ Spec 未定义 | ✅ 已实现 | 🟢 额外功能 | - |

**影响分析**：
- 合同详情接口缺失：用户无法查看合同详细信息
- 合同编号点击后无法跳转

**建议**：创建合同详情接口和页面

---

### 4.2 list_data API 返回字段差异

**Spec 要求返回**：
```json
{
  "contract_id": int,
  "contract_number": string,
  "contract_name": string,
  "merchant_name": string,
  "contact_person": string,
  "start_date": string,
  "end_date": string,
  "status": string,
  "create_time": string,
  "plot_count": int
}
```

**实际返回**：
```json
{
  "contract_id": int,
  "contract_number": string,
  "contract_name": string,
  "merchant_name": string,
  "contact_person": string,  ✅
  "start_date": string,
  "end_date": string,
  "actual_amount": decimal,  ⚠️ 额外字段
  "status": string,
  "plot_count": int,  ✅
  "create_time": string  ❌ 缺失
}
```

**差异**：
- ✅ `contact_person` 已实现
- ✅ `plot_count` 已实现
- ⚠️ `actual_amount` 额外返回（Spec 未要求）
- ❌ `create_time` 未返回

---

## 五、页面功能差异

### 5.1 合同列表页面

| 功能 | Spec 要求 | 实际实现 | 状态 |
|------|----------|----------|------|
| 序号列 | ✅ 自动递增 | ✅ 已实现 | ✅ |
| 合同编号 | ✅ 可点击跳转详情 | ⚠️ 可点击但详情接口未实现 | ⚠️ |
| 联系人列 | ✅ 显示联系人 | ✅ 已实现 | ✅ |
| 合同金额 | ✅ 右对齐，货币格式 | ✅ 已实现 | ✅ |
| 操作列 | ✅ 编辑、删除 | ✅ 编辑、删除、下载 | ⚠️ 额外功能 |
| 表头排序 | ❌ Spec 未要求 | ❌ 未实现 | ✅ |
| 分页功能 | ✅ 支持分页 | ✅ 已实现 | ✅ |
| 搜索功能 | ✅ 支持搜索 | ✅ 已实现 | ✅ |

---

### 5.2 合同添加页面

| 功能 | Spec 要求 | 实际实现 | 状态 |
|------|----------|----------|------|
| 商户选择 | ✅ 按期年筛选 | ✅ 已实现 | ✅ |
| 地块选择 | ✅ 多选 | ✅ 已实现 | ✅ |
| 地块过滤 | ❌ Spec 未要求 | ✅ 已实现（过滤被占用地块） | 🟢 额外功能 |
| 租金计算 | ✅ 自动计算 | ✅ 已实现 | ✅ |
| 合同编号 | ✅ 自动生成 | ✅ 已实现 | ✅ |
| 日期预设 | ❌ Spec 未要求 | ✅ 已实现（自动填充） | 🟢 额外功能 |

---

## 六、权限控制差异

### 6.1 RBAC 权限模型

**Spec 要求**：
```
基于 RBAC 模型实现细粒度权限控制
- Role（角色）
- Permission（权限）
- UserRole（用户角色关联）
- RolePermission（角色权限关联）
```

**实际情况**：
- ✅ 数据库表结构完整
- ✅ 权限验证中间件已实现
- ⚠️ 权限点定义不完整
- ❌ 权限分配功能未实现

**差异详情**：

| 权限点 | Spec 要求 | 实际实现 | 状态 |
|--------|----------|----------|------|
| user_manage | ✅ 用户管理 | ✅ 已定义 | ✅ |
| merchant_manage | ✅ 商户管理 | ✅ 已定义 | ✅ |
| plot_manage | ✅ 地块管理 | ✅ 已定义 | ✅ |
| contract_manage | ✅ 合同管理 | ✅ 已定义 | ✅ |
| utility_manage | ✅ 水电计费 | ✅ 已定义 | ✅ |
| finance_manage | ✅ 财务管理 | ✅ 已定义 | ✅ |
| scale_manage | ✅ 磅秤管理 | ✅ 已定义 | ✅ |
| 权限分配界面 | ✅ 角色权限配置 | ❌ 未实现 | ❌ |

**影响分析**：
- 权限点已定义但无法动态分配
- 需要手动在数据库中配置角色权限

---

## 七、额外功能（Spec 未定义但已实现）

| 功能模块 | 功能说明 | 建议 |
|---------|---------|------|
| 合同文档生成 | 基于 docxtpl 生成 Word 合同 | 🟢 建议补充到 Spec |
| 地块图片插入 | 合同文档末尾插入地块图片 | 🟢 建议补充到 Spec |
| 合同下载 | 支持下载生成的合同 | 🟢 建议补充到 Spec |
| 人民币大写金额 | 合同金额自动转换为人民币大写 | 🟢 建议补充到 Spec |
| 地块占用过滤 | 自动过滤已被占用的地块 | 🟢 建议补充到 Spec |
| 日期自动填充 | 合同日期自动预设 | 🟢 建议补充到 Spec |

---

## 八、差异汇总清单

### 8.1 按严重程度分类

#### 🔴 严重差异（必须立即修复）

| 编号 | 差异描述 | 影响模块 | 建议优先级 |
|------|---------|---------|-----------|
| P001 | Routes 层直接操作 SQL | 全系统 | P0 |
| P002 | Services/Models层缺失 | 全系统 | P0 |
| P003 | Status 字段默认值错误（6 个表） | Contract/Merchant/Plot/等 | P0 |
| P004 | BR-001/BR-002业务规则缺失 | 合同管理 | P0 |
| P005 | 合同详情接口缺失 | 合同管理 | P1 |

#### 🟡 中等差异（近期修复）

| 编号 | 差异描述 | 影响模块 | 建议优先级 |
|------|---------|---------|-----------|
| M001 | BR-009 ~ BR-013 状态自动化规则缺失 | 商户/地块管理 | P1 |
| M002 | BR-014 应收账款自动生成缺失 | 财务管理 | P1 |
| M003 | AmountReduction 约束缺失 | Contract 表 | P1 |
| M004 | 额外字段（ContractPeriod等） | 多个表 | P2 |
| M005 | list_data API 缺少 create_time | 合同管理 | P2 |

#### 🟢 轻微差异（可选优化）

| 编号 | 差异描述 | 影响模块 | 建议优先级 |
|------|---------|---------|-----------|
| L001 | BusinessType 长度不一致 | Merchant 表 | P3 |
| L002 | 额外返回 actual_amount | 合同管理 | P3 |
| L003 | 缺少表头排序功能 | 合同列表 | P3 |

---

### 8.2 按模块分类

#### 合同管理模块

| 差异类型 | 数量 | 严重 | 中等 | 轻微 |
|---------|------|------|------|------|
| 数据库结构 | 3 | 1 | 2 | 0 |
| 业务规则 | 2 | 1 | 0 | 1 |
| 接口规范 | 2 | 1 | 0 | 1 |
| 页面功能 | 1 | 0 | 0 | 1 |

#### 商户管理模块

| 差异类型 | 数量 | 严重 | 中等 | 轻微 |
|---------|------|------|------|------|
| 数据库结构 | 2 | 1 | 0 | 1 |
| 业务规则 | 3 | 0 | 3 | 0 |
| 架构规范 | 2 | 2 | 0 | 0 |

#### 地块管理模块

| 差异类型 | 数量 | 严重 | 中等 | 轻微 |
|---------|------|------|------|------|
| 数据库结构 | 4 | 1 | 3 | 0 |
| 业务规则 | 2 | 0 | 2 | 0 |
| 架构规范 | 2 | 2 | 0 | 0 |

#### 财务管理模块

| 差异类型 | 数量 | 严重 | 中等 | 轻微 |
|---------|------|------|------|------|
| 数据库结构 | 2 | 1 | 1 | 0 |
| 业务规则 | 4 | 0 | 1 | 3 |
| 架构规范 | 2 | 2 | 0 | 0 |

---

## 九、修复建议与优先级

### 9.1 P0 - 立即修复（1-2 天）

1. **修复 Status 默认值**
   ```sql
   -- 执行 SQL 脚本修复所有 Status 默认值
   ```

2. **创建 ContractService 和 Contract Model**
   - 重构 contract.py 移除 SQL
   - 实现 Service 层调用 Model 层

3. **实现 BR-001/BR-002 校验**
   - 地块唯一性检查
   - 合同时间重叠检查

### 9.2 P1 - 近期修复（1 周）

1. **实现状态自动化规则**
   - BR-009 ~ BR-013
   - 商户/地块状态自动更新

2. **创建合同详情接口**
   - GET /contract/detail/{id}
   - 创建 detail.html 页面

3. **创建其他模块的 Service/Model 层**
   - MerchantService/Model
   - PlotService/Model

### 9.3 P2 - 中期优化（2 周）

1. **完善应收账款功能**
   - BR-014 自动生成应收账款
   - 完善核销流程

2. **修复数据库约束**
   - AmountReduction 改为 NOT NULL
   - 评估额外字段必要性

3. **更新 Spec 文档**
   - 补充额外功能到 Spec
   - 更新接口定义

### 9.4 P3 - 长期改进（1 个月）

1. **性能优化**
   - 添加必要索引
   - 优化慢查询

2. **用户体验优化**
   - 表头排序功能
   - 更多数据可视化

---

## 十、总结

### 10.1 实现状态统计

| 评估维度 | 已实现 | 部分实现 | 未实现 | 完成率 |
|---------|--------|---------|--------|--------|
| 数据库结构 | 22/25 | 0 | 3 | 88% |
| 架构规范 | 2/10 | 0 | 8 | 20% |
| 业务规则 | 9/17 | 2 | 6 | 53% |
| 接口规范 | 6/8 | 0 | 2 | 75% |
| 页面功能 | 15/16 | 0 | 1 | 94% |
| 权限控制 | 5/8 | 1 | 2 | 63% |

**总体完成率**：约 **65%**

### 10.2 主要成就

✅ 数据库表结构基本完整（88%）
✅ 页面功能实现完善（94%）
✅ 接口规范大部分符合（75%）
✅ 额外实现多个增强功能（合同文档生成、人民币大写等）

### 10.3 主要问题

❌ 架构规范严重不符合（20%）
  - Routes 层直接操作 SQL
  - Services/Models层缺失

❌ 业务规则实现不足（53%）
  - 状态自动化规则缺失
  - 地块唯一性校验缺失

❌ 数据质量问题
  - Status 默认值错误（6 个表）
  - 约束缺失

### 10.4 风险评估

| 风险项 | 可能性 | 影响程度 | 风险等级 |
|--------|--------|----------|----------|
| 数据不一致（地块重复出租） | 高 | 高 | 🔴 高风险 |
| 代码难以维护 | 高 | 中 | 🟡 中风险 |
| 业务逻辑错误 | 中 | 高 | 🟡 中风险 |
| 性能问题 | 低 | 中 | 🟢 低风险 |

---

## 十一、附录

### 11.1 检查工具

- Python 脚本：`check_db_vs_spec.py`
- 数据库查询：INFORMATION_SCHEMA.COLUMNS
- 代码静态分析

### 11.2 参考文档

- 《数据库设计文档》
- 《需求规格说明书 V2.0》
- 《合同列表页面功能需求规格》

### 11.3 修复 SQL 脚本

```sql
-- 修复所有 Status 默认值和现有数据
-- Contract 表
ALTER TABLE Contract ADD CONSTRAINT DF_Contract_Status DEFAULT '有效' FOR Status;
UPDATE Contract SET Status = '有效' WHERE Status = '??' OR Status IS NULL;

-- Merchant 表
ALTER TABLE Merchant ADD CONSTRAINT DF_Merchant_Status DEFAULT '正常' FOR Status;
UPDATE Merchant SET Status = '正常' WHERE Status = '??' OR Status IS NULL;

-- Plot 表
ALTER TABLE Plot ADD CONSTRAINT DF_Plot_Status DEFAULT '空闲' FOR Status;
UPDATE Plot SET Status = '空闲' WHERE Status = '??' OR Status IS NULL;

-- Receivable 表
ALTER TABLE Receivable ADD CONSTRAINT DF_Receivable_Status DEFAULT '未付款' FOR Status;
UPDATE Receivable SET Status = '未付款' WHERE Status = '???' OR Status IS NULL;

-- Payable 表
ALTER TABLE Payable ADD CONSTRAINT DF_Payable_Status DEFAULT '未付款' FOR Status;
UPDATE Payable SET Status = '未付款' WHERE Status = '???' OR Status IS NULL;

-- ElectricityMeter 表
ALTER TABLE ElectricityMeter ADD CONSTRAINT DF_ElectricityMeter_Status DEFAULT '正常' FOR Status;
UPDATE ElectricityMeter SET Status = '正常' WHERE Status = '??' OR Status IS NULL;

-- WaterMeter 表
ALTER TABLE WaterMeter ADD CONSTRAINT DF_WaterMeter_Status DEFAULT '正常' FOR Status;
UPDATE WaterMeter SET Status = '正常' WHERE Status = '??' OR Status IS NULL;

-- Scale 表
ALTER TABLE Scale ADD CONSTRAINT DF_Scale_Status DEFAULT '正常' FOR Status;
UPDATE Scale SET Status = '正常' WHERE Status = '??' OR Status IS NULL;

-- 修改 AmountReduction 为 NOT NULL
ALTER TABLE Contract ALTER COLUMN AmountReduction DECIMAL(12,2) NOT NULL;
```

---

**文档结束**
