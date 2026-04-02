# 地块类型和单价管理功能设计文档

## 文档信息

| 项目名称 | 宏发金属交易市场管理系统 - 地块类型和单价管理 |
| --- | --- |
| 文档版本 | V1.0 |
| 编写日期 | 2026-03-31 |
| 文档状态 | 设计阶段 |
| 编写人员 | 系统分析员 |

---

## 1. 功能概述

### 1.1 背景

当前地块管理系统中：
- 地块没有类型分类，无法区分不同类型的地块
- 地块单价由用户手动输入，无法实现标准化管理
- 缺少租金自动计算功能，需要人工计算
- 无法根据地块类型快速统计和分析

### 1.2 目标

实现地块类型和单价管理功能，包括：
- 为地块添加类型属性（水泥地皮、钢结构厂房、砖混厂房）
- 地块类型与单价关联，实现标准化定价
- 自动计算月租金和年租金
- 提供友好的用户界面

### 1.3 目标用户

- **系统管理员**：配置地块类型和单价
- **工作人员**：创建和管理地块

---

## 2. 功能需求

### 2.1 核心功能

#### 2.1.1 地块类型管理

**功能描述**：
- 在字典表中添加三种地块类型：水泥地皮、钢结构厂房、砖混厂房
- 每种类型配置对应的单价
- 支持后续扩展新的地块类型

**数据结构**：
| DictType | DictCode | DictName | UnitPrice | SortOrder |
|----------|----------|----------|-----------|-----------|
| plot_type | cement_ground | 水泥地皮 | 50.00 | 1 |
| plot_type | steel_workshop | 钢结构厂房 | 80.00 | 2 |
| plot_type | brick_workshop | 砖混厂房 | 70.00 | 3 |

#### 2.1.2 地块创建/编辑功能

**功能描述**：
- 添加地块类型选择控件（下拉框）
- 选择地块类型后自动填充单价（只读）
- 用户输入面积
- 系统自动计算月租金和年租金（只读展示）
- 保存时存储所有值

**计算公式**：
- 月租金 = 面积 × 单价
- 年租金 = 月租金 × 12

**界面交互**：
1. 用户选择地块类型
2. 系统自动填充单价（只读，灰色背景）
3. 用户输入面积
4. 系统自动计算并显示月租金和年租金（只读，灰色背景）
5. 用户填写其他信息
6. 点击保存

#### 2.1.3 地块列表显示

**功能描述**：
- 列表显示地块类型
- 列表显示单价、月租金、年租金
- 支持按地块类型筛选

#### 2.1.4 数据统计和报表

**功能描述**：
- 按地块类型统计数量和面积
- 按地块类型统计租金收入
- 支持导出报表

---

## 3. 技术设计

### 3.1 数据库设计

#### 3.1.1 扩展Sys_Dictionary表

```sql
-- 添加UnitPrice字段
ALTER TABLE Sys_Dictionary
ADD UnitPrice DECIMAL(10,2) NULL;

-- 添加字段说明
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'单价（仅用于地块类型）', 
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE',  @level1name = N'Sys_Dictionary',
    @level2type = N'COLUMN', @level2name = N'UnitPrice';
```

#### 3.1.2 扩展Plot表

```sql
-- 添加地块类型字段
ALTER TABLE Plot
ADD PlotType NVARCHAR(50) NULL;

-- 添加月租金字段
ALTER TABLE Plot
ADD MonthlyRent DECIMAL(10,2) NULL;

-- 添加年租金字段
ALTER TABLE Plot
ADD YearlyRent DECIMAL(10,2) NULL;

-- 添加字段说明
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'地块类型', 
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE',  @level1name = N'Plot',
    @level2type = N'COLUMN', @level2name = N'PlotType';

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'月租金', 
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE',  @level1name = N'Plot',
    @level2type = N'COLUMN', @level2name = N'MonthlyRent';

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'年租金', 
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE',  @level1name = N'Plot',
    @level2type = N'COLUMN', @level2name = N'YearlyRent';

-- 创建索引
CREATE INDEX idx_plot_type ON Plot(PlotType);
```

#### 3.1.3 初始化地块类型数据

```sql
-- 插入地块类型数据
INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, UnitPrice, SortOrder, Description)
VALUES 
('plot_type', 'cement_ground', N'水泥地皮', 50.00, 1, N'水泥地皮地块'),
('plot_type', 'steel_workshop', N'钢结构厂房', 80.00, 2, N'钢结构厂房地块'),
('plot_type', 'brick_workshop', N'砖混厂房', 70.00, 3, N'砖混厂房地块');
```

### 3.2 后端设计

#### 3.2.1 修改地块路由

**新增功能**：
- 获取地块类型列表（含单价）
- 创建地块时自动计算租金
- 编辑地块时自动计算租金

**关键代码逻辑**：

```python
# 获取地块类型列表
@plot_bp.route('/types', methods=['GET'])
@login_required
def get_plot_types():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DictCode, DictName, UnitPrice
        FROM Sys_Dictionary
        WHERE DictType = 'plot_type'
        ORDER BY SortOrder
    """)
    
    types = [{
        'dict_code': r.DictCode,
        'dict_name': r.DictName,
        'unit_price': float(r.UnitPrice) if r.UnitPrice else 0
    } for r in cursor.fetchall()]
    
    conn.close()
    return jsonify({'success': True, 'data': types})

# 创建地块时计算租金
def calculate_rent(area, unit_price):
    monthly_rent = area * unit_price
    yearly_rent = monthly_rent * 12
    return monthly_rent, yearly_rent
```

### 3.3 前端设计

#### 3.3.1 添加地块页面

**界面布局**：
```
+--------------------------------------------------+
| 添加地块                                          |
+--------------------------------------------------+
| 地块编号*:   [_______________]                   |
| 地块名称*:   [_______________]                   |
| 地块类型*:   [水泥地皮 ▼]                         |
| 面积*:       [_____] 平方米                       |
| 单价*:       [50.00] 元/平方米（只读）            |
| 月租金:      [计算值] 元（只读）                  |
| 年租金:      [计算值] 元（只读）                  |
| 位置:        [_______________]                   |
| 描述:        [_______________]                   |
|              [保存]  [取消]                      |
+--------------------------------------------------+
```

**JavaScript逻辑**：
```javascript
// 地块类型改变时
$('#plot_type').change(function() {
    var selectedOption = $(this).find('option:selected');
    var unitPrice = selectedOption.data('unit-price');
    
    // 填充单价（只读）
    $('#price').val(unitPrice);
    
    // 计算租金
    calculateRent();
});

// 面积改变时
$('#area').on('input', function() {
    calculateRent();
});

// 计算租金
function calculateRent() {
    var area = parseFloat($('#area').val()) || 0;
    var unitPrice = parseFloat($('#price').val()) || 0;
    
    var monthlyRent = area * unitPrice;
    var yearlyRent = monthlyRent * 12;
    
    $('#monthly_rent').val(monthlyRent.toFixed(2));
    $('#yearly_rent').val(yearlyRent.toFixed(2));
}
```

#### 3.3.2 编辑地块页面

**界面布局**：
与添加页面相同，但预填充现有数据。

#### 3.3.3 地块列表页面

**界面布局**：
```
+----------------------------------------------------------------------------------+
| 地块列表                                                           [添加] [导出] |
+----------------------------------------------------------------------------------+
| 地块类型: [全部 ▼]  搜索: [______] [搜索] [重置]                                 |
+----------------------------------------------------------------------------------+
| 编号 | 名称 | 类型     | 面积  | 单价 | 月租金 | 年租金 | 位置 | 状态 | 操作   |
|------|------|----------|-------|------|--------|--------|------|------|--------|
| P001 | A区  | 水泥地皮 | 100.5 | 50   | 5025   | 60300  | 东区 | 空闲 | 编辑 删除 |
+----------------------------------------------------------------------------------+
```

---

## 4. 数据流程

### 4.1 创建地块流程

```
用户选择地块类型
    ↓
前端获取类型单价
    ↓
自动填充单价（只读）
    ↓
用户输入面积
    ↓
前端计算月租金和年租金
    ↓
用户填写其他信息
    ↓
提交表单
    ↓
后端验证数据
    ↓
后端重新计算租金（确保准确性）
    ↓
保存到数据库
    ↓
返回成功
```

### 4.2 编辑地块流程

```
加载地块数据
    ↓
显示现有信息
    ↓
用户修改地块类型或面积
    ↓
前端重新计算租金
    ↓
提交表单
    ↓
后端验证数据
    ↓
后端重新计算租金
    ↓
更新数据库
    ↓
返回成功
```

---

## 5. 接口设计

### 5.1 获取地块类型列表

**接口**：`GET /plot/types`

**返回格式**：
```json
{
  "success": true,
  "data": [
    {
      "dict_code": "cement_ground",
      "dict_name": "水泥地皮",
      "unit_price": 50.00
    },
    {
      "dict_code": "steel_workshop",
      "dict_name": "钢结构厂房",
      "unit_price": 80.00
    },
    {
      "dict_code": "brick_workshop",
      "dict_name": "砖混厂房",
      "unit_price": 70.00
    }
  ]
}
```

### 5.2 创建地块

**接口**：`POST /plot/add`

**参数**：
```json
{
  "plot_code": "P001",
  "plot_name": "A区地块",
  "plot_type": "cement_ground",
  "area": 100.5,
  "price": 50.00,
  "monthly_rent": 5025.00,
  "yearly_rent": 60300.00,
  "location": "东区",
  "status": "空闲",
  "description": "A区水泥地皮"
}
```

**返回格式**：
```json
{
  "success": true,
  "message": "添加成功",
  "data": {
    "plot_id": 1
  }
}
```

### 5.3 编辑地块

**接口**：`POST /plot/edit/<int:plot_id>`

**参数**：同创建地块

**返回格式**：
```json
{
  "success": true,
  "message": "更新成功"
}
```

---

## 6. 安全设计

### 6.1 数据验证

- 前端验证：必填项、数值范围
- 后端验证：
  - 地块类型必须在字典表中存在
  - 面积必须大于0
  - 单价必须与地块类型匹配
  - 租金计算必须正确

### 6.2 权限控制

- 所有操作需要登录认证
- 创建、编辑、删除需要相应权限

---

## 7. 测试计划

### 7.1 单元测试

- 租金计算函数测试
- 地块类型获取测试
- 数据验证测试

### 7.2 集成测试

- 创建地块完整流程
- 编辑地块完整流程
- 地块类型变更测试
- 租金自动计算测试

### 7.3 UI测试

- 地块类型选择交互
- 租金自动计算显示
- 表单验证提示

---

## 8. 部署方案

### 8.1 数据库迁移

1. 执行数据库迁移脚本
2. 初始化地块类型数据
3. 验证数据完整性

### 8.2 代码部署

1. 更新地块路由代码
2. 更新前端页面
3. 清除缓存

---

## 9. 验收标准

### 9.1 功能验收

- ✅ 地块类型正确显示
- ✅ 单价自动填充正确
- ✅ 租金计算正确
- ✅ 列表显示完整
- ✅ 筛选功能正常
- ✅ 数据保存正确

### 9.2 性能验收

- ✅ 页面加载时间<2秒
- ✅ 计算响应及时

### 9.3 安全验收

- ✅ 权限控制有效
- ✅ 数据验证正确

---

**文档结束**