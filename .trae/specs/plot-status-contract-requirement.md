# 地块状态与合同关联功能需求

## 1. 功能概述

实现地块状态与合同的自动关联，根据合同有效期自动判断地块状态，并限制已出租地块的编辑权限。

## 2. 当前数据库结构分析

### 2.1 地块表 (Plot)
```sql
CREATE TABLE Plot (
    PlotID INT PRIMARY KEY IDENTITY,
    PlotCode NVARCHAR(50) UNIQUE NOT NULL,
    PlotName NVARCHAR(100),
    Area DECIMAL(10,2) NOT NULL,
    Price DECIMAL(10,2) NOT NULL,
    Location NVARCHAR(200),
    Status NVARCHAR(20) DEFAULT N'空闲',
    Description NVARCHAR(500),
    CreateTime DATETIME DEFAULT GETDATE(),
    UpdateTime DATETIME
);
```

### 2.2 合同表 (Contract)
```sql
CREATE TABLE Contract (
    ContractID INT PRIMARY KEY IDENTITY,
    ContractNo NVARCHAR(50) UNIQUE,
    MerchantID INT NOT NULL,
    StartDate DATE NOT NULL,
    EndDate DATE NOT NULL,
    TotalRent DECIMAL(10,2),
    Status NVARCHAR(20) DEFAULT N'草稿',
    Description NVARCHAR(500),
    CreateTime DATETIME DEFAULT GETDATE(),
    UpdateTime DATETIME,
    FOREIGN KEY (MerchantID) REFERENCES Merchant(MerchantID)
);
```

### 2.3 合同地块关联表 (ContractPlot)
```sql
CREATE TABLE ContractPlot (
    ContractPlotID INT PRIMARY KEY IDENTITY,
    ContractID INT NOT NULL,
    PlotID INT NOT NULL,
    Rent DECIMAL(10,2),
    CreateTime DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (ContractID) REFERENCES Contract(ContractID),
    FOREIGN KEY (PlotID) REFERENCES Plot(PlotID)
);
```

## 3. 需求澄清问题

### 3.1 合同状态问题
**问题**：合同表中的Status字段默认为"草稿"，请问合同状态有哪些？
- 草稿
- 生效中
- 已过期
- 已取消
- 其他？

**影响**：需要明确哪些状态的合同会影响地块状态判断。

### 3.2 地块状态判断逻辑
**需求描述**：当前日期处于合同有效期内，地块状态为"已出租"，否则为"空闲"。

**需要澄清**：
1. **合同有效期判断**：
   - 是否只判断 StartDate <= 当前日期 <= EndDate？
   - 是否需要考虑合同状态？只有"生效中"的合同才判断？
   
2. **多合同关联**：
   - 一个地块可能关联多个合同，如何处理？
   - 只要有一个合同在有效期内，就显示"已出租"？
   - 还是需要其他逻辑？

3. **状态存储方式**：
   - **方案A**：实时计算（推荐）
     - 不修改Plot表的Status字段
     - 每次查询时动态计算状态
     - 优点：数据一致性好，无需维护
     - 缺点：查询性能稍低
   
   - **方案B**：存储状态
     - 在ContractPlot表中添加状态字段
     - 合同创建/修改/删除时更新地块状态
     - 优点：查询性能好
     - 缺点：需要维护状态一致性

### 3.3 编辑限制问题
**需求描述**：已出租的地块信息不能被修改。

**需要澄清**：
1. **限制范围**：
   - 限制所有字段的编辑？
   - 还是只限制部分字段（如面积、价格、位置）？
   - 允许修改的字段：描述、备注？

2. **特殊情况**：
   - 如果合同即将到期，是否允许提前编辑？
   - 是否需要"强制编辑"功能（管理员权限）？

### 3.4 用户权限问题
**需求描述**：用户不能修改该状态。

**需要澄清**：
1. **用户类型**：
   - 所有用户都不能修改？
   - 管理员是否可以修改？
   
2. **前端控制**：
   - 已出租地块在列表中不显示"编辑"按钮？
   - 还是显示但点击时提示"地块已出租，无法编辑"？

## 4. 建议的实现方案

### 4.1 地块状态实时计算方案（推荐）

#### 4.1.1 后端实现
在 `PlotService` 中添加方法：

```python
@staticmethod
def get_plot_status(plot_id):
    """
    根据合同情况计算地块状态
    
    Args:
        plot_id: 地块ID
    
    Returns:
        '已出租' 或 '空闲'
    """
    today = datetime.now().date()
    
    # 查询该地块关联的所有有效合同
    query = """
        SELECT c.ContractID, c.StartDate, c.EndDate, c.Status
        FROM Contract c
        INNER JOIN ContractPlot cp ON c.ContractID = cp.ContractID
        WHERE cp.PlotID = ?
        AND c.Status IN ('生效中', '已批准')  -- 需要确认合同状态
        AND c.StartDate <= ?
        AND c.EndDate >= ?
    """
    
    results = execute_query(query, (plot_id, today, today), fetch_type='all')
    
    if results:
        return '已出租'
    else:
        return '空闲'
```

#### 4.1.2 前端显示
在地块列表和详情页面显示实时计算的状态：

```python
@staticmethod
def get_plots(page=1, per_page=10, search=None):
    """
    获取地块列表，包含实时计算的状态
    """
    # 查询地块基本信息
    plots = execute_query(base_query, params, fetch_type='all')
    
    # 为每个地块计算状态
    for plot in plots:
        plot.RealStatus = PlotService.get_plot_status(plot.PlotID)
    
    return plots
```

### 4.2 编辑限制实现

#### 4.2.1 后端验证
在编辑接口中添加验证：

```python
@staticmethod
def update_plot(plot_id, **kwargs):
    """
    更新地块信息（带状态验证）
    """
    # 检查地块状态
    status = PlotService.get_plot_status(plot_id)
    
    if status == '已出租':
        raise ValueError('地块已出租，无法编辑')
    
    # 执行更新操作
    # ...
```

#### 4.2.2 前端控制
在地块列表中根据状态显示/隐藏编辑按钮：

```html
{% if plot.RealStatus == '空闲' %}
    <a href="{{ url_for('plot.edit', plot_id=plot.PlotID) }}" 
       class="btn btn-sm btn-warning" title="编辑">
        <i class="fa fa-edit"></i>
    </a>
{% else %}
    <button class="btn btn-sm btn-secondary" disabled title="地块已出租，无法编辑">
        <i class="fa fa-edit"></i>
    </button>
{% endif %}
```

## 5. 需求确认结果

✅ **已确认的需求**：

1. **合同状态**：
   - 生效中：影响地块状态判断
   - 已过期：影响地块状态判断
   - 已取消：影响地块状态判断
   - 草稿：不影响地块状态判断

2. **地块状态计算**：
   - ✅ 方案A：实时计算（已确认）

3. **编辑限制范围**：
   - ✅ 限制部分字段：
     - 地块编码 (PlotCode)
     - 面积 (Area)
     - 单价 (Price)
     - 位置 (Location)
   - 允许编辑的字段：
     - 地块名称 (PlotName)
     - 描述 (Description)

4. **管理员权限**：
   - 所有用户（包括管理员）都受限制

5. **前端显示**：
   - ✅ 显示禁用的编辑按钮（灰色）
   - 鼠标悬停提示"地块已出租，无法编辑核心信息"

6. **多合同处理**：
   - ✅ 只要有一个合同在有效期内就显示"已出租"

## 6. 最终实现方案

### 6.1 地块状态实时计算

#### 6.1.1 后端实现
在 `PlotService` 中添加方法：

```python
@staticmethod
def get_plot_status(plot_id):
    """
    根据合同情况计算地块状态
    
    Args:
        plot_id: 地块ID
    
    Returns:
        '已出租' 或 '空闲'
    """
    today = datetime.now().date()
    
    # 查询该地块关联的所有有效合同
    query = """
        SELECT c.ContractID, c.StartDate, c.EndDate, c.Status
        FROM Contract c
        INNER JOIN ContractPlot cp ON c.ContractID = cp.ContractID
        WHERE cp.PlotID = ?
        AND c.Status IN ('生效中', '已过期', '已取消')
        AND c.StartDate <= ?
        AND c.EndDate >= ?
    """
    
    results = execute_query(query, (plot_id, today, today), fetch_type='all')
    
    if results:
        return '已出租'
    else:
        return '空闲'
```

#### 6.1.2 前端显示
在地块列表和详情页面显示实时计算的状态：

```python
@staticmethod
def get_plots(page=1, per_page=10, search=None):
    """
    获取地块列表，包含实时计算的状态
    """
    # 查询地块基本信息
    plots = execute_query(base_query, params, fetch_type='all')
    
    # 为每个地块计算状态
    for plot in plots:
        plot.RealStatus = PlotService.get_plot_status(plot.PlotID)
    
    return plots
```

### 6.2 编辑限制实现

#### 6.2.1 后端验证
在编辑接口中添加验证：

```python
@staticmethod
def update_plot(plot_id, **kwargs):
    """
    更新地块信息（带状态验证）
    """
    # 检查地块状态
    status = PlotService.get_plot_status(plot_id)
    
    if status == '已出租':
        # 限制字段：地块编码、面积、单价、位置
        restricted_fields = ['plot_code', 'area', 'price', 'location']
        
        # 检查是否尝试修改限制字段
        for field in restricted_fields:
            if field in kwargs and kwargs[field] != getattr(plot, field):
                raise ValueError(f'地块已出租，无法修改字段：{field}')
    
    # 执行更新操作
    # ...
```

#### 6.2.2 前端控制
在地块编辑页面根据状态禁用字段：

```html
{% if plot.RealStatus == '已出租' %}
    <!-- 禁用核心字段 -->
    {{ form.plot_code(class="form-control", disabled=True) }}
    {{ form.area(class="form-control", disabled=True) }}
    {{ form.price(class="form-control", disabled=True) }}
    {{ form.location(class="form-control", disabled=True) }}
    
    <!-- 允许编辑的字段 -->
    {{ form.plot_name(class="form-control") }}
    {{ form.description(class="form-control") }}
{% else %}
    <!-- 所有字段可编辑 -->
    {{ form.plot_code(class="form-control") }}
    {{ form.area(class="form-control") }}
    {{ form.price(class="form-control") }}
    {{ form.location(class="form-control") }}
    {{ form.plot_name(class="form-control") }}
    {{ form.description(class="form-control") }}
{% endif %}
```

在地块列表中显示禁用的编辑按钮：

```html
{% if plot.RealStatus == '空闲' %}
    <a href="{{ url_for('plot.edit', plot_id=plot.PlotID) }}" 
       class="btn btn-sm btn-warning" title="编辑">
        <i class="fa fa-edit"></i>
    </a>
{% else %}
    <button class="btn btn-sm btn-secondary" disabled 
            title="地块已出租，无法编辑核心信息">
        <i class="fa fa-edit"></i>
    </button>
{% endif %}
```

### 6.3 实施步骤

1. **后端实现**：
   - [ ] 在 `PlotService` 中添加 `get_plot_status()` 方法
   - [ ] 修改 `get_plots()` 方法，添加实时状态计算
   - [ ] 修改 `get_plot_by_id()` 方法，添加实时状态计算
   - [ ] 修改 `update_plot()` 方法，添加字段限制验证

2. **前端实现**：
   - [ ] 修改地块列表页面，显示实时状态
   - [ ] 修改地块编辑页面，根据状态禁用字段
   - [ ] 添加提示信息，说明限制原因

3. **测试验证**：
   - [ ] 测试空闲地块的编辑功能
   - [ ] 测试已出租地块的字段限制
   - [ ] 测试合同状态变化对地块状态的影响
   - [ ] 测试多合同关联的地块状态判断

## 7. 注意事项

1. **性能优化**：
   - 地块列表查询时批量计算状态，避免N+1查询问题
   - 考虑使用缓存优化频繁查询的地块状态

2. **数据一致性**：
   - 确保合同状态变更时，相关地块的状态能正确反映
   - 添加必要的索引优化查询性能

3. **用户体验**：
   - 提供清晰的状态提示信息
   - 在编辑页面明确标识哪些字段被限制编辑