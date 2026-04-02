# 商户业务类型字段功能需求

## 1. 功能概述

在商户表中添加BusinessType字段，用于区分商户的业务类型。该字段的值来源于系统字典表（business_type），并在整个应用中统一使用字典名称（dictname）进行显示和存储。

## 2. 数据库设计

### 2.1 商户表修改

在Merchant表中添加BusinessType字段：

```sql
ALTER TABLE Merchant
ADD BusinessType NVARCHAR(100) NULL;
```

### 2.2 业务类型字典数据

系统字典表中已定义的业务类型（business_type）：

| DictCode | DictName | Description | SortOrder |
|----------|----------|-------------|-----------|
| metal_material | 金属材料 | 金属原材料销售 | 1 |
| hardware | 五金工具 | 五金工具销售 | 2 |
| machinery | 机械配件 | 机械配件销售 | 3 |
| equipment | 设备租赁 | 设备租赁业务 | 4 |

## 3. 功能需求

### 3.1 显示功能

**需求**：在商户列表和详情页面显示业务类型的中文名称（dictname）。

**实现方式**：
- 商户列表页面：在表格中添加"业务类型"列，显示BusinessType字段值
- 商户详情页面：显示业务类型的中文名称
- 商户编辑页面：显示当前业务类型

**示例**：
```
商户名称：创峰建材有限公司
业务类型：金属材料
```

### 3.2 保存功能

**需求**：在编辑商户时，保存业务类型的字典名称（dictname）到BusinessType字段。

**实现方式**：
- 后端接收业务类型值（dictname）
- 直接将dictname存储到BusinessType字段
- 无需进行字典转换

**示例**：
```
用户选择："金属材料"
存储值：BusinessType = "金属材料"
```

### 3.3 新增记录功能

**需求**：在添加新商户时，允许选择业务类型，并保存字典名称（dictname）。

**实现方式**：
- 前端显示业务类型下拉框，选项来自字典表（business_type）
- 下拉框显示dictname，提交时发送dictname
- 后端接收dictname并直接存储到BusinessType字段

**示例**：
```
前端下拉框选项：
- 金属材料
- 五金工具
- 机械配件
- 设备租赁

用户选择："金属材料"
存储值：BusinessType = "金属材料"
```

### 3.4 删除功能

**需求**：删除商户记录时，BusinessType字段随记录一起删除，无需特殊处理。

**实现方式**：
- 直接删除商户记录
- BusinessType字段作为记录的一部分自动删除
- 无需额外的清理操作

## 4. 技术实现

### 4.1 后端实现

#### 4.1.1 Merchant模型修改

在Merchant模型中添加business_type属性：

```python
class Merchant:
    def __init__(self, merchant_id=None, merchant_name=None, legal_person=None, 
                 contact_person=None, phone=None, address=None, merchant_type=None, 
                 business_license=None, tax_registration=None, description=None, 
                 status=None, create_time=None, update_time=None, business_type=None):
        # ... 其他属性
        self.business_type = business_type
```

#### 4.1.2 MerchantService修改

在MerchantService中添加获取业务类型列表的方法：

```python
@staticmethod
def get_business_types():
    """
    获取所有业务类型
    
    Returns:
        业务类型列表，格式为[(dictname, dictname), ...]
    """
    query = """
        SELECT DictName 
        FROM Sys_Dictionary 
        WHERE DictType = 'business_type' 
        ORDER BY SortOrder
    """
    results = execute_query(query, fetch_type='all')
    
    # 返回(dictname, dictname)格式，因为我们要存储和显示dictname
    return [(result.DictName, result.DictName) for result in results]
```

修改get_merchants方法，包含BusinessType字段：

```python
base_query = """
    SELECT MerchantID, MerchantName, LegalPerson, ContactPerson, Phone, 
           MerchantType, BusinessType, Address, Description, Status, 
           CreateTime, UpdateTime
    FROM Merchant
"""

# 在创建Merchant对象时添加business_type参数
merchant = Merchant(
    merchant_id=result.MerchantID,
    merchant_name=result.MerchantName,
    legal_person=result.LegalPerson,
    contact_person=result.ContactPerson,
    phone=result.Phone,
    merchant_type=result.MerchantType,
    business_type=result.BusinessType,  # 新增
    address=result.Address,
    description=result.Description,
    status=result.Status,
    create_time=result.CreateTime,
    update_time=result.UpdateTime
)
```

修改create_merchant和update_merchant方法，包含business_type参数：

```python
@staticmethod
def create_merchant(merchant_name, legal_person, contact_person, phone, 
                   merchant_type, business_license, address, description, 
                   tax_registration=None, business_type=None):  # 新增参数
    insert_query = """
        INSERT INTO Merchant (MerchantName, LegalPerson, ContactPerson, Phone, 
                             MerchantType, BusinessLicense, TaxRegistration, 
                             Address, Description, Status, CreateTime, BusinessType)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '正常', ?, ?)
    """
    execute_update(insert_query, (merchant_name, legal_person, contact_person, 
                                  phone, merchant_type, business_license, 
                                  tax_registration, address, description, 
                                  datetime.datetime.now(), business_type))
```

#### 4.1.3 路由修改

在merchant路由中添加业务类型选项：

```python
@merchant_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = MerchantAddForm()
    
    # 获取商户类型和业务类型
    merchant_types = MerchantService.get_merchant_types()
    form.merchant_type.choices = merchant_types
    
    business_types = MerchantService.get_business_types()  # 新增
    form.business_type.choices = business_types  # 新增
    
    # ... 其他逻辑
```

### 4.2 前端实现

#### 4.2.1 表单修改

在MerchantAddForm和MerchantEditForm中添加business_type字段：

```python
class MerchantAddForm(FlaskForm):
    # ... 其他字段
    business_type = SelectField('业务类型', coerce=str, validators=[
        Optional()
    ])
    # ... 其他字段
```

#### 4.2.2 列表页面修改

在商户列表页面添加业务类型列：

```html
<thead>
    <tr>
        <th>ID</th>
        <th>商户名称</th>
        <th>法人代表</th>
        <th>联系人</th>
        <th>联系电话</th>
        <th>商户类型</th>
        <th>业务类型</th>  <!-- 新增 -->
        <th>状态</th>
        <th>创建时间</th>
        <th>操作</th>
    </tr>
</thead>
<tbody>
    {% for merchant in merchants %}
    <tr>
        <td>{{ merchant.merchant_id }}</td>
        <td>{{ merchant.merchant_name }}</td>
        <td>{{ merchant.legal_person }}</td>
        <td>{{ merchant.contact_person }}</td>
        <td>{{ merchant.phone }}</td>
        <td><span class="badge bg-primary">{{ merchant.merchant_type }}</span></td>
        <td><span class="badge bg-info">{{ merchant.business_type or '未设置' }}</span></td>  <!-- 新增 -->
        <td><span class="badge bg-success">正常</span></td>
        <td>{{ merchant.create_time.strftime('%Y-%m-%d %H:%M') }}</td>
        <td class="table-actions">
            <!-- 操作按钮 -->
        </td>
    </tr>
    {% endfor %}
</tbody>
```

#### 4.2.3 添加/编辑页面修改

在商户添加和编辑页面添加业务类型选择框：

```html
<div class="row mb-3">
    <div class="col-md-6">
        {{ form.business_type.label(class="form-label") }}
        {{ form.business_type(class="form-control" + (" is-invalid" if form.business_type.errors else "")) }}
        {% if form.business_type.errors %}
            <div class="invalid-feedback">
                {% for error in form.business_type.errors %}{{ error }}{% endfor %}
            </div>
        {% endif %}
    </div>
</div>
```

## 5. 数据迁移

### 5.1 数据库表修改

创建数据库迁移脚本，添加BusinessType字段：

```sql
-- 添加BusinessType字段
ALTER TABLE Merchant
ADD BusinessType NVARCHAR(100) NULL;

-- 添加字段说明
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'业务类型', 
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE',  @level1name = N'Merchant',
    @level2type = N'COLUMN', @level2name = N'BusinessType';
```

### 5.2 数据初始化

由于BusinessType字段为可选字段，现有数据无需初始化，可以为NULL。

## 6. 测试用例

### 6.1 显示功能测试

- [ ] 商户列表页面正确显示业务类型
- [ ] 未设置业务类型的商户显示"未设置"
- [ ] 商户详情页面正确显示业务类型

### 6.2 保存功能测试

- [ ] 编辑商户时可以修改业务类型
- [ ] 保存后业务类型正确存储到数据库
- [ ] 业务类型显示为字典名称（如"金属材料"）

### 6.3 新增功能测试

- [ ] 添加商户时可以选择业务类型
- [ ] 业务类型下拉框显示所有选项
- [ ] 保存后业务类型正确存储到数据库

### 6.4 删除功能测试

- [ ] 删除商户记录时BusinessType字段随记录一起删除
- [ ] 无数据库错误或约束违反

## 7. 注意事项

1. **数据一致性**：BusinessType字段存储的是字典名称（dictname），而不是字典编码（dictcode），与MerchantType字段的处理方式一致。

2. **可选字段**：BusinessType字段允许为NULL，商户可以不设置业务类型。

3. **字典维护**：如果字典表中的业务类型名称发生变化，需要同步更新Merchant表中的BusinessType字段值。

4. **性能优化**：由于直接存储dictname，无需进行字典转换，查询性能更好。

## 8. 实施步骤

1. [ ] 执行数据库迁移脚本，添加BusinessType字段
2. [ ] 修改Merchant模型，添加business_type属性
3. [ ] 修改MerchantService，添加get_business_types方法
4. [ ] 修改MerchantService，更新get_merchants、create_merchant、update_merchant方法
5. [ ] 修改表单类，添加business_type字段
6. [ ] 修改路由，添加业务类型选项
7. [ ] 修改列表页面，添加业务类型列
8. [ ] 修改添加/编辑页面，添加业务类型选择框
9. [ ] 执行功能测试
10. [ ] 更新相关文档