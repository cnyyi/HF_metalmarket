# 合同管理模块 - 代码、数据库与 Spec 差异对比

## 文档信息

| 项目 | 内容 |
|------|------|
| 对比日期 | 2026-04-01 |
| 对比范围 | 合同管理模块（Contract） |
| Spec 版本 | 2026-04-01-contract-list-spec.md, spec.md (V2.0) |

---

## 一、数据库结构差异

### 1.1 Contract 表对比

| 字段 | Spec 定义 | 实际数据库 | 状态 |
|------|-----------|------------|------|
| ContractID | INT PRIMARY KEY IDENTITY | ✅ 存在 | ✅ 一致 |
| ContractNumber | VARCHAR(50) NOT NULL | ✅ VARCHAR NOT NULL | ✅ 一致 |
| MerchantID | INT NOT NULL | ✅ INT NOT NULL | ✅ 一致 |
| ContractName | NVARCHAR(100) NOT NULL | ✅ NVARCHAR NOT NULL | ✅ 一致 |
| StartDate | DATETIME NOT NULL | ✅ DATETIME NOT NULL | ✅ 一致 |
| EndDate | DATETIME NOT NULL | ✅ DATETIME NOT NULL | ✅ 一致 |
| ContractAmount | DECIMAL(12,2) NOT NULL | ✅ DECIMAL NOT NULL | ✅ 一致 |
| AmountReduction | DECIMAL(12,2) DEFAULT(0) | ✅ DECIMAL NULL DEFAULT((0)) | ⚠️ 略有差异（Spec 要求 NOT NULL） |
| ActualAmount | DECIMAL(12,2) NOT NULL | ✅ DECIMAL NOT NULL | ✅ 一致 |
| PaymentMethod | NVARCHAR(50) NOT NULL | ✅ NVARCHAR NOT NULL | ✅ 一致 |
| ContractPeriodYear | INT NOT NULL | ✅ INT NOT NULL | ✅ 一致 |
| BusinessType | NVARCHAR(50) NOT NULL | ✅ NVARCHAR NOT NULL | ✅ 一致 |
| Description | NVARCHAR(500) NULL | ✅ NVARCHAR NULL | ✅ 一致 |
| Status | VARCHAR(50) DEFAULT('有效') | ✅ VARCHAR NULL DEFAULT(('??')) | ⚠️ 默认值应为'有效' |
| CreateTime | DATETIME DEFAULT(getdate()) | ✅ DATETIME DEFAULT(getdate()) | ✅ 一致 |
| UpdateTime | DATETIME NULL | ✅ DATETIME NULL | ✅ 一致 |
| **ContractPeriod** | ❌ **Spec 未定义** | ✅ NVARCHAR NULL | ⚠️ **额外字段** |

**问题总结**：
1. ⚠️ `AmountReduction` 字段：Spec 要求 NOT NULL，实际为 NULL
2. ⚠️ `Status` 字段：默认值应为'有效'，实际为'??'
3. ⚠️ `ContractPeriod` 字段：Spec 未定义，但实际存在（用于存储期年信息）

---

### 1.2 Merchant 表对比

| 字段 | Spec 定义 | 实际数据库 | 状态 |
|------|-----------|------------|------|
| ContactPerson | NVARCHAR(50) NOT NULL | ✅ NVARCHAR NOT NULL | ✅ 一致 |

**问题总结**：
- ✅ Merchant 表结构完全符合 Spec 要求

---

### 1.3 Plot 表对比

| 字段 | Spec 定义 | 实际数据库 | 状态 |
|------|-----------|------------|------|
| ImagePath | NVARCHAR(255) NULL | ✅ NVARCHAR NULL | ✅ 一致 |
| PlotType | ❌ Spec 未定义 | ✅ NVARCHAR NULL | ⚠️ 额外字段 |
| MonthlyRent | ❌ Spec 未定义 | ✅ DECIMAL NULL | ⚠️ 额外字段 |
| YearlyRent | ❌ Spec 未定义 | ✅ DECIMAL NULL | ⚠️ 额外字段 |

**问题总结**：
- ⚠️ `PlotType`、`MonthlyRent`、`YearlyRent` 为额外字段（可能是后续功能扩展）

---

## 二、API 接口差异

### 2.1 Spec 要求的 API

| 接口 | Spec 定义 | 实际实现 | 状态 |
|------|-----------|----------|------|
| GET /contract/list | ✅ 合同列表页面 | ✅ `/contract/list` | ✅ 已实现 |
| GET /contract/list_data | ✅ 获取列表数据（带分页） | ✅ `/contract/list_data` | ✅ 已实现 |
| GET /contract/detail/{id} | ✅ 获取合同详情 | ❌ **未实现** | ❌ **缺失** |
| POST /contract/delete/{id} | ✅ 删除合同 | ✅ `/contract/delete/{id}` | ✅ 已实现 |
| GET /contract/edit/{id} | ✅ 获取编辑页面 | ✅ `/contract/edit/{id}` | ✅ 已实现 |
| POST /contract/add | ✅ 添加合同 | ✅ `/contract/add` | ✅ 已实现 |
| POST /contract/generate/{id} | ❌ Spec 未定义 | ✅ `/contract/generate/{id}` | ⚠️ 额外功能（合同文档生成） |
| GET /contract/download/{file} | ❌ Spec 未定义 | ✅ `/contract/download/{file}` | ⚠️ 额外功能（合同下载） |

**问题总结**：
1. ❌ **缺失接口**：`GET /contract/detail/{id}` - 合同详情接口未实现
2. ⚠️ **额外功能**：合同文档生成和下载功能（已实现但 Spec 未定义）

---

### 2.2 list_data API 详细对比

#### Spec 要求的返回字段：

```json
{
  "contract_id": int,
  "contract_number": string,
  "contract_name": string,
  "merchant_name": string,
  "contact_person": string,  // ← Spec 要求
  "start_date": string,
  "end_date": string,
  "status": string,
  "create_time": string,
  "plot_count": int  // ← Spec 要求
}
```

#### 实际返回字段：

```json
{
  "contract_id": int,
  "contract_number": string,
  "contract_name": string,
  "merchant_name": string,
  "contact_person": string,  // ✅ 已实现
  "start_date": string,
  "end_date": string,
  "actual_amount": decimal,  // ⚠️ 额外字段
  "status": string,
  "plot_count": int  // ✅ 已实现
}
```

**差异**：
- ✅ `contact_person` 已实现
- ✅ `plot_count` 已实现
- ⚠️ `actual_amount` 额外返回（Spec 未要求）
- ❌ `create_time` 未返回

---

## 三、页面功能差异

### 3.1 合同列表页面（list.html）

#### Spec 要求的表格列：

| 列名 | 类型 | 宽度 | Spec 要求 | 实际实现 | 状态 |
|------|------|------|----------|----------|------|
| 序号 | 数值 | 50px | ✅ 自动递增 | ✅ 已实现 | ✅ |
| 合同编号 | 文本 | 150px | ✅ 可点击跳转详情 | ⚠️ 可点击但详情接口未实现 | ⚠️ |
| 合同名称 | 文本 | 150px | ✅ 仅显示 | ✅ 已实现 | ✅ |
| 商户名称 | 文本 | 120px | ✅ 仅显示 | ✅ 已实现 | ✅ |
| 联系人 | 文本 | 100px | ✅ 显示联系人 | ✅ 已实现 | ✅ |
| 开始日期 | 日期 | 100px | ✅ YYYY-MM-DD | ✅ 已实现 | ✅ |
| 结束日期 | 日期 | 100px | ✅ YYYY-MM-DD | ✅ 已实现 | ✅ |
| 合同金额 | 数值 | 120px | ✅ 右对齐，货币格式 | ✅ 显示 ActualAmount，右对齐 | ✅ |
| 操作 | 按钮 | 100px | ✅ 编辑、删除 | ✅ 编辑、删除、下载 | ⚠️ 额外功能 |

**问题总结**：
1. ⚠️ 合同编号点击后跳转详情，但详情接口未实现
2. ⚠️ 操作列多了"下载"按钮（合同文档下载功能）

---

### 3.2 Spec 要求的交互功能

| 功能 | Spec 要求 | 实际实现 | 状态 |
|------|-----------|----------|------|
| 合同编号点击 | 跳转到详情页 `/contract/detail/{id}` | ⚠️ 跳转但接口未实现 | ⚠️ |
| 编辑按钮 | 跳转到 `/contract/edit/{id}` | ✅ 已实现 | ✅ |
| 删除按钮 | 显示删除确认模态框 | ✅ 已实现 | ✅ |
| 确认删除 | AJAX 删除 | ✅ 已实现 | ✅ |
| 分页链接 | 切换页码 | ✅ 已实现 | ✅ |
| 搜索框回车 | 提交搜索 | ✅ 已实现 | ✅ |
| 表头排序 | ❌ Spec 未要求 | ❌ 未实现 | ✅ |
| 表格行 hover | 隔行变色 | ✅ 已实现 | ✅ |
| 分页控件 | 悬浮效果 | ✅ 已实现 | ✅ |

**问题总结**：
- ✅ 大部分交互功能已实现
- ⚠️ 合同详情页缺失

---

## 四、合同文档生成功能差异

### 4.1 Spec vs 实现

| 功能 | Spec 定义 | 实际实现 | 状态 |
|------|-----------|----------|------|
| 合同文档生成 | ❌ 未定义 | ✅ 已实现 | ⚠️ 额外功能 |
| 地块图片插入 | ❌ 未定义 | ✅ 已实现 | ⚠️ 额外功能 |
| 模板渲染 | ❌ 未定义 | ✅ docxtpl | ⚠️ 额外功能 |

**说明**：
- 合同文档生成功能是后续添加的增强功能
- Spec 未包含此功能，但实际已完整实现

---

## 五、路由层架构差异

### 5.1 Spec 架构规范要求

```
routes 层：
- 只能接收请求、参数校验、调用 Service 层、返回 JSON/渲染模板
- 严禁出现 SQL 语句
- 所有数据库操作必须在 models 层或 services 层

services 层：
- 所有业务逻辑
```

### 5.2 实际 contract.py 实现

```python
# ❌ 问题：contract.py 中直接包含数据库操作
def get_contract_periods():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DictName FROM Sys_Dictionary ...")  # ❌ SQL 直接在 routes 层

def get_available_merchants(period):
    cursor.execute("SELECT m.MerchantID, m.MerchantName FROM Merchant m ...")  # ❌ SQL

def generate_contract_number(period, merchant_id):
    # ✅ 纯业务逻辑，符合规范

@contract_bp.route('/add', methods=['POST'])
def contract_add():
    cursor.execute("INSERT INTO Contract ...")  # ❌ SQL 直接在 routes 层
    cursor.execute("INSERT INTO ContractPlot ...")  # ❌ SQL
```

**问题总结**：
- ❌ **严重违反架构规范**：所有数据库操作直接在 routes 层
- ❌ **缺少 Service 层**：没有 contract_service.py
- ❌ **缺少 Model 层**：没有 Contract 模型类

---

## 六、合同编号生成逻辑差异

### 6.1 Spec 要求

```
格式：ZTHYHT + "YYYYMMDD" + 商户编号三位数字
示例：ZTHYHT20260401026
```

### 6.2 实际实现

```python
def generate_contract_number(period, merchant_id):
    match = re.search(r'第 (\d+) 期第 (\d+) 年', period)
    if match:
        period_code = match.group(1) + match.group(2)  # 期年代码
    else:
        return None
    
    date_str = datetime.now().strftime('%Y%m%d')
    merchant_id_padded = str(merchant_id).zfill(3)
    return f"ZTHYHT{period_code}{date_str}{merchant_id_padded}"
```

**实际格式**：`ZTHYHT + 期年代码 (2 位) + YYYYMMDD + 商户 ID(3 位)`
**示例**：`ZTHYHT1220260401026`（第 1 期第 2 年）

**差异**：
- ⚠️ Spec 要求固定格式，实际实现包含期年信息
- ✅ 商户 ID 补 3 位已正确实现

---

## 七、合同状态流转差异

### 7.1 Spec 定义的状态机

```
草稿 → 生效中 → 已到期
           ↓
         已终止
```

### 7.2 实际实现

- ⚠️ **未实现状态流转逻辑**
- ⚠️ **未实现自动状态更新**
- ❌ **缺少 BR-009 ~ BR-013 业务规则**

**缺失功能**：
- ❌ 商户状态根据合同状态自动更新
- ❌ 地块状态根据合同状态自动更新
- ❌ 合同到期自动检测

---

## 八、业务规则差异

### 8.1 Spec 定义的业务规则

| 规则编号 | 规则名称 | Spec 要求 | 实际实现 | 状态 |
|---------|---------|-----------|----------|------|
| BR-001 | 地块唯一性 | 一个地块同一时间只能属于一个有效合同 | ❌ 未实现 | ❌ |
| BR-002 | 时间不重叠 | 同一地块的合同时间不能重叠 | ❌ 未实现 | ❌ |
| BR-003 | 合同编号唯一 | 合同编号必须唯一 | ✅ 已实现 | ✅ |
| BR-004 | 租金自动计算 | 租金 = Σ(地块面积 × 地块单价) | ✅ 已实现 | ✅ |
| BR-009 | 状态自动更新 | 商户状态根据合同自动更新 | ❌ 未实现 | ❌ |
| BR-010 | 在租判定 | 商户有生效合同 → 在租 | ❌ 未实现 | ❌ |
| BR-011 | 空闲判定 | 商户无生效合同 → 空闲 | ❌ 未实现 | ❌ |
| BR-012 | 地块出租 | 地块被加入生效合同 → 已出租 | ❌ 未实现 | ❌ |
| BR-013 | 地块释放 | 地块无生效合同 → 空闲 | ❌ 未实现 | ❌ |

**问题总结**：
- ❌ **大部分业务规则未实现**
- ✅ 仅实现了基础的租金计算和合同编号生成

---

## 九、合同详情页面差异

### 9.1 Spec 要求

```
路由：GET /contract/detail/{id}
页面：templates/contract/detail.html
功能：显示完整的合同信息（基本信息、地块信息、备注）
```

### 9.2 实际实现

- ❌ **路由未实现**
- ❌ **页面未创建**
- ❌ **详情数据接口未实现**

**影响**：
- ⚠️ 合同编号点击后无法查看详情

---

## 十、总结与改进建议

### 10.1 高优先级问题（必须修复）

| 编号 | 问题 | 影响 | 建议 |
|------|------|------|------|
| P001 | ❌ routes 层直接操作数据库 | 违反架构规范，代码难维护 | 创建 ContractService 和 Contract 模型 |
| P002 | ❌ 缺少合同详情接口 | 用户无法查看详情 | 实现 `/contract/detail/{id}` |
| P003 | ❌ 业务规则未实现 | 数据一致性风险 | 实现 BR-001 ~ BR-002 校验 |
| P004 | ⚠️ Status 默认值错误 | 状态显示异常 | 更新默认值为'有效' |

---

### 10.2 中优先级问题（建议改进）

| 编号 | 问题 | 影响 | 建议 |
|------|------|------|------|
| M001 | ⚠️ AmountReduction 为 NULL | 可能为 NULL 导致计算错误 | 改为 NOT NULL DEFAULT(0) |
| M002 | ⚠️ 缺少状态流转逻辑 | 需手动更新状态 | 实现自动状态更新 |
| M003 | ⚠️ ContractPeriod 字段冗余 | Spec 未定义 | 考虑是否必要 |

---

### 10.3 低优先级问题（可选优化）

| 编号 | 问题 | 影响 | 建议 |
|------|------|------|------|
| L001 | ⚠️ 额外返回 actual_amount | 数据冗余 | 考虑是否必要 |
| L002 | ⚠️ 缺少表头排序 | 用户体验 | 可选功能 |

---

### 10.4 额外功能（Spec 未定义但已实现）

| 功能 | 说明 | 建议 |
|------|------|------|
| ✅ 合同文档生成 | 基于 docxtpl 生成 Word 合同 | 建议补充到 Spec |
| ✅ 地块图片插入 | 合同文档末尾插入地块图片 | 建议补充到 Spec |
| ✅ 合同下载 | 支持下载生成的合同 | 建议补充到 Spec |

---

## 十一、待完成任务清单

### 11.1 架构重构（必须）

- [ ] 创建 `app/services/contract_service.py`
- [ ] 创建 `app/models/contract.py`
- [ ] 重构 `contract.py` 移除所有 SQL
- [ ] 实现 Service 层调用 Model 层

### 11.2 功能完善（必须）

- [ ] 实现 `/contract/detail/{id}` 接口
- [ ] 创建 `templates/contract/detail.html`
- [ ] 实现 BR-001 地块唯一性校验
- [ ] 实现 BR-002 合同时间重叠校验
- [ ] 实现合同状态自动更新

### 11.3 数据库修正（建议）

- [ ] 修改 `AmountReduction` 为 NOT NULL DEFAULT(0)
- [ ] 修改 `Status` 默认值为'有效'
- [ ] 评估 `ContractPeriod` 字段必要性

### 11.4 Spec 更新（建议）

- [ ] 补充合同文档生成功能
- [ ] 补充地块图片插入功能
- [ ] 补充合同下载功能
- [ ] 更新合同编号生成规则

---

**文档结束**
