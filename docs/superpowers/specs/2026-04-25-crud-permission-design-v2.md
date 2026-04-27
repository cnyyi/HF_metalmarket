# CRUD 四级权限精细化设计（v2）

## 背景

当前系统权限粒度停留在模块级别（如 `merchant_manage`），一个权限标识控制整个模块的所有操作。拥有 `merchant_manage` 的用户要么什么都能做，要么什么都做不了，无法区分"只能查看"和"可以编辑/删除"。

## 设计决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 操作粒度 | CRUD 四级 + 特殊操作 | 覆盖绝大多数业务场景，水电模块增加 reading/pay |
| 权限组织 | 两级平铺（ModuleName 分组 + 操作权限） | 实现简单，查询高效，前端动态构建树形展示 |
| 兼容策略 | 渐进兼容 | 旧权限映射到 view，不破坏现有代码 |
| 财务拆分 | 6 模块细化 | finance + account + prepayment + deposit + customer + salary |
| 系统管理 | 4 模块 | user + role + permission + dict |
| 水电特殊操作 | 6 权限 | view/create/edit/delete/reading/pay |

## 一、权限编码规范

### 1.1 命名规则

`{module}_{operation}` 两段式，operation 固定为 `view` / `create` / `edit` / `delete`，水电模块额外增加 `reading` / `pay`。

### 1.2 完整权限清单（74 个）

#### 市场管理（34 个）

| PermissionCode | PermissionName | ModuleName | OperationCode | SortOrder |
|---|---|---|---|---|
| plot_view | 地块查看 | 市场管理 | view | 101 |
| plot_create | 地块新增 | 市场管理 | create | 102 |
| plot_edit | 地块编辑 | 市场管理 | edit | 103 |
| plot_delete | 地块删除 | 市场管理 | delete | 104 |
| merchant_view | 商户查看 | 市场管理 | view | 201 |
| merchant_create | 商户新增 | 市场管理 | create | 202 |
| merchant_edit | 商户编辑 | 市场管理 | edit | 203 |
| merchant_delete | 商户删除 | 市场管理 | delete | 204 |
| contract_view | 合同查看 | 市场管理 | view | 301 |
| contract_create | 合同新增 | 市场管理 | create | 302 |
| contract_edit | 合同编辑 | 市场管理 | edit | 303 |
| contract_delete | 合同删除 | 市场管理 | delete | 304 |
| utility_view | 水电查看 | 市场管理 | view | 401 |
| utility_create | 水电新增 | 市场管理 | create | 402 |
| utility_edit | 水电编辑 | 市场管理 | edit | 403 |
| utility_delete | 水电删除 | 市场管理 | delete | 404 |
| utility_reading | 水电抄表 | 市场管理 | reading | 405 |
| utility_pay | 水电缴费 | 市场管理 | pay | 406 |
| scale_view | 磅秤查看 | 市场管理 | view | 501 |
| scale_create | 磅秤新增 | 市场管理 | create | 502 |
| scale_edit | 磅秤编辑 | 市场管理 | edit | 503 |
| scale_delete | 磅秤删除 | 市场管理 | delete | 504 |
| expense_view | 费用单查看 | 市场管理 | view | 601 |
| expense_create | 费用单新增 | 市场管理 | create | 602 |
| expense_edit | 费用单编辑 | 市场管理 | edit | 603 |
| expense_delete | 费用单删除 | 市场管理 | delete | 604 |
| garbage_view | 垃圾清运查看 | 市场管理 | view | 701 |
| garbage_create | 垃圾清运新增 | 市场管理 | create | 702 |
| garbage_edit | 垃圾清运编辑 | 市场管理 | edit | 703 |
| garbage_delete | 垃圾清运删除 | 市场管理 | delete | 704 |
| dorm_view | 宿舍查看 | 市场管理 | view | 801 |
| dorm_create | 宿舍新增 | 市场管理 | create | 802 |
| dorm_edit | 宿舍编辑 | 市场管理 | edit | 803 |
| dorm_delete | 宿舍删除 | 市场管理 | delete | 804 |

#### 财务管理（24 个）

| PermissionCode | PermissionName | ModuleName | OperationCode | SortOrder |
|---|---|---|---|---|
| finance_view | 财务查看 | 财务管理 | view | 1001 |
| finance_create | 财务新增 | 财务管理 | create | 1002 |
| finance_edit | 财务编辑 | 财务管理 | edit | 1003 |
| finance_delete | 财务删除 | 财务管理 | delete | 1004 |
| account_view | 账户查看 | 财务管理 | view | 1101 |
| account_create | 账户新增 | 财务管理 | create | 1102 |
| account_edit | 账户编辑 | 财务管理 | edit | 1103 |
| account_delete | 账户删除 | 财务管理 | delete | 1104 |
| prepayment_view | 预收预付查看 | 财务管理 | view | 1201 |
| prepayment_create | 预收预付新增 | 财务管理 | create | 1202 |
| prepayment_edit | 预收预付编辑 | 财务管理 | edit | 1203 |
| prepayment_delete | 预收预付删除 | 财务管理 | delete | 1204 |
| deposit_view | 押金查看 | 财务管理 | view | 1301 |
| deposit_create | 押金新增 | 财务管理 | create | 1302 |
| deposit_edit | 押金编辑 | 财务管理 | edit | 1303 |
| deposit_delete | 押金删除 | 财务管理 | delete | 1304 |
| customer_view | 往来客户查看 | 财务管理 | view | 1401 |
| customer_create | 往来客户新增 | 财务管理 | create | 1402 |
| customer_edit | 往来客户编辑 | 财务管理 | edit | 1403 |
| customer_delete | 往来客户删除 | 财务管理 | delete | 1404 |
| salary_view | 工资查看 | 财务管理 | view | 1501 |
| salary_create | 工资新增 | 财务管理 | create | 1502 |
| salary_edit | 工资编辑 | 财务管理 | edit | 1503 |
| salary_delete | 工资删除 | 财务管理 | delete | 1504 |

#### 系统管理（16 个）

| PermissionCode | PermissionName | ModuleName | OperationCode | SortOrder |
|---|---|---|---|---|
| user_view | 用户查看 | 系统管理 | view | 2001 |
| user_create | 用户新增 | 系统管理 | create | 2002 |
| user_edit | 用户编辑 | 系统管理 | edit | 2003 |
| user_delete | 用户删除 | 系统管理 | delete | 2004 |
| role_view | 角色查看 | 系统管理 | view | 2101 |
| role_create | 角色新增 | 系统管理 | create | 2102 |
| role_edit | 角色编辑 | 系统管理 | edit | 2103 |
| role_delete | 角色删除 | 系统管理 | delete | 2104 |
| permission_view | 权限查看 | 系统管理 | view | 2201 |
| permission_create | 权限新增 | 系统管理 | create | 2202 |
| permission_edit | 权限编辑 | 系统管理 | edit | 2203 |
| permission_delete | 权限删除 | 系统管理 | delete | 2204 |
| dict_view | 字典查看 | 系统管理 | view | 2301 |
| dict_create | 字典新增 | 系统管理 | create | 2302 |
| dict_edit | 字典编辑 | 系统管理 | edit | 2303 |
| dict_delete | 字典删除 | 系统管理 | delete | 2304 |

## 二、数据库变更

### 2.1 Permission 表新增字段

```sql
ALTER TABLE Permission ADD OperationCode NVARCHAR(20) NULL;
ALTER TABLE Permission ADD SortOrder INT NULL DEFAULT 0;
```

- `OperationCode`：操作类型，值为 `view` / `create` / `edit` / `delete` / `reading` / `pay`，旧权限标记为 `manage`
- `SortOrder`：同模块内排序，用于前端树形展示

### 2.2 旧权限标记

对现有粗粒度权限，设置 `OperationCode = 'manage'`，不删除：

```sql
UPDATE Permission SET OperationCode = N'manage' WHERE PermissionCode LIKE N'%_manage' OR PermissionCode IN (N'direct_entry', N'utility_reading');
```

### 2.3 ModuleName 规范化

```sql
UPDATE Permission SET ModuleName = N'市场管理' WHERE PermissionCode IN (
    N'plot_view',N'plot_create',N'plot_edit',N'plot_delete',
    N'merchant_view',N'merchant_create',N'merchant_edit',N'merchant_delete',
    N'contract_view',N'contract_create',N'contract_edit',N'contract_delete',
    N'utility_view',N'utility_create',N'utility_edit',N'utility_delete',N'utility_reading',N'utility_pay',
    N'scale_view',N'scale_create',N'scale_edit',N'scale_delete',
    N'expense_view',N'expense_create',N'expense_edit',N'expense_delete',
    N'garbage_view',N'garbage_create',N'garbage_edit',N'garbage_delete',
    N'dorm_view',N'dorm_create',N'dorm_edit',N'dorm_delete'
);
UPDATE Permission SET ModuleName = N'财务管理' WHERE PermissionCode IN (
    N'finance_view',N'finance_create',N'finance_edit',N'finance_delete',
    N'account_view',N'account_create',N'account_edit',N'account_delete',
    N'prepayment_view',N'prepayment_create',N'prepayment_edit',N'prepayment_delete',
    N'deposit_view',N'deposit_create',N'deposit_edit',N'deposit_delete',
    N'customer_view',N'customer_create',N'customer_edit',N'customer_delete',
    N'salary_view',N'salary_create',N'salary_edit',N'salary_delete'
);
UPDATE Permission SET ModuleName = N'系统管理' WHERE PermissionCode IN (
    N'user_view',N'user_create',N'user_edit',N'user_delete',
    N'role_view',N'role_create',N'role_edit',N'role_delete',
    N'permission_view',N'permission_create',N'permission_edit',N'permission_delete',
    N'dict_view',N'dict_create',N'dict_edit',N'dict_delete'
);
```

## 三、渐进兼容策略

### 3.1 旧权限 → 新权限映射

```python
LEGACY_PERMISSION_MAP = {
    'plot_manage': 'plot_view',
    'merchant_manage': 'merchant_view',
    'contract_manage': 'contract_view',
    'utility_manage': 'utility_view',
    'utility_reading': 'utility_reading',
    'scale_manage': 'scale_view',
    'expense_manage': 'expense_view',
    'garbage_manage': 'garbage_view',
    'dorm_manage': 'dorm_view',
    'finance_manage': 'finance_view',
    'account_manage': 'account_view',
    'direct_entry': 'account_create',
    'prepayment_manage': 'prepayment_view',
    'deposit_manage': 'deposit_view',
    'customer_manage': 'customer_view',
    'salary_manage': 'salary_view',
    'user_manage': 'user_view',
    'role_manage': 'role_view',
    'permission_manage': 'permission_view',
    'dict_manage': 'dict_view',
}
```

### 3.2 has_permission 兼容逻辑

```python
def has_permission(self, permission_code):
    for p in self.permissions:
        if p.permission_code == permission_code:
            return True
    mapped = LEGACY_PERMISSION_MAP.get(permission_code)
    if mapped:
        for p in self.permissions:
            if p.permission_code == mapped:
                return True
    return False
```

### 3.3 角色赋权迁移

原来拥有 `xxx_manage` 的角色，自动获得对应模块的 CRUD 四级权限（+ 特殊操作权限）：

```sql
-- 以 merchant 为例：拥有 merchant_manage 的角色，自动获得 merchant_view/create/edit/delete
INSERT INTO RolePermission (RoleID, PermissionID, CreateTime)
SELECT rp.RoleID, p.PermissionID, GETDATE()
FROM RolePermission rp
INNER JOIN Permission old_p ON rp.PermissionID = old_p.PermissionID
INNER JOIN Permission p ON p.ModuleName = old_p.ModuleName
    AND p.OperationCode IN (N'view', N'create', N'edit', N'delete', N'reading', N'pay')
    AND SUBSTRING(p.PermissionCode, 1, LEN(p.PermissionCode) - CHARINDEX(N'_', REVERSE(p.PermissionCode)))
        = SUBSTRING(old_p.PermissionCode, 1, LEN(old_p.PermissionCode) - CHARINDEX(N'_', REVERSE(old_p.PermissionCode)))
WHERE old_p.OperationCode = N'manage'
    AND NOT EXISTS (
        SELECT 1 FROM RolePermission rp2 WHERE rp2.RoleID = rp.RoleID AND rp2.PermissionID = p.PermissionID
    );
```

### 3.4 迁移完成后旧权限处理

旧权限（`OperationCode = 'manage'`）在迁移完成后设置 `IsActive = 0`，不物理删除。兼容映射保证旧代码继续工作。

## 四、前端权限分配界面

### 4.1 角色编辑页权限分配区域

按 ModuleName 分组，每组内按模块排列，每个模块一行 checkbox：

```
☑ 市场管理
   地块管理    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]
   商户管理    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]
   合同管理    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]
   水电计费    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑] [抄表 ☑] [缴费 ☑]
   磅秤数据    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]
   费用单      [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]
   垃圾清运    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]
   宿舍管理    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]

☑ 财务管理
   财务管理    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]
   账户管理    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]
   预收预付    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]
   押金管理    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]
   往来客户    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]
   工资管理    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]

☑ 系统管理
   用户管理    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]
   角色管理    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]
   权限管理    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]
   字典管理    [查看 ☑] [新增 ☑] [编辑 ☑] [删除 ☑]

快捷操作：[全选查看] [全选新增] [全选编辑] [全选删除]
```

### 4.2 交互逻辑

- 勾选"新增/编辑/删除/抄表/缴费"时，自动勾选"查看"（没有查看权限就无法进入页面）
- 取消"查看"时，自动取消同模块的其他操作权限
- 模块组标题的勾选状态 = 该组内所有权限是否全选

## 五、路由层改造

### 5.1 改造规则

| 操作类型 | 使用的权限标识 | 说明 |
|---------|-------------|------|
| 列表页 / 详情页 | `xxx_view` | 查看类页面 |
| 新增页面 / 新增 API | `xxx_create` | 创建操作 |
| 编辑页面 / 编辑 API | `xxx_edit` | 修改操作 |
| 删除 API | `xxx_delete` | 删除操作 |
| 抄表操作 | `xxx_reading` | 水电抄表 |
| 缴费操作 | `xxx_pay` | 水电缴费 |

### 5.2 改造示例（商户管理）

```python
# 改造前
@merchant_bp.route('/list')
@check_permission('merchant_manage')
def merchant_list(): ...

@merchant_bp.route('/add', methods=['GET','POST'])
@check_permission('merchant_manage')
def merchant_add(): ...

@merchant_bp.route('/edit/<int:id>', methods=['GET','POST'])
@check_permission('merchant_manage')
def merchant_edit(id): ...

@merchant_bp.route('/delete/<int:id>', methods=['POST'])
@check_api_permission('merchant_manage')
def merchant_delete(id): ...

# 改造后
@merchant_bp.route('/list')
@check_permission('merchant_view')
def merchant_list(): ...

@merchant_bp.route('/add', methods=['GET','POST'])
@check_permission('merchant_create')
def merchant_add(): ...

@merchant_bp.route('/edit/<int:id>', methods=['GET','POST'])
@check_permission('merchant_edit')
def merchant_edit(id): ...

@merchant_bp.route('/delete/<int:id>', methods=['POST'])
@check_api_permission('merchant_delete')
def merchant_delete(id): ...
```

### 5.3 水电模块改造示例

```python
# 抄表相关路由
@utility_bp.route('/reading/add', methods=['POST'])
@check_api_permission('utility_reading')
def add_reading(): ...

# 缴费相关路由
@utility_bp.route('/pay', methods=['POST'])
@check_api_permission('utility_pay')
def pay_reading(): ...
```

### 5.4 财务模块改造示例

```python
# 账户管理路由
@finance_bp.route('/account')
@check_permission('account_view')
def account_list(): ...

@finance_bp.route('/account/add', methods=['POST'])
@check_api_permission('account_create')
def account_add(): ...

# 直接记账路由
@finance_bp.route('/direct_entry', methods=['GET','POST'])
@check_permission('account_create')
def direct_entry(): ...
```

## 六、模板层改造

### 6.1 侧边栏菜单（admin_base.html）

侧边栏菜单项的可见性由 `xxx_view` 控制：

```html
<!-- 改造前 -->
{% if current_user.has_permission('merchant_manage') %}

<!-- 改造后 -->
{% if current_user.has_permission('merchant_view') %}
```

### 6.2 页面内操作按钮

```html
<!-- 新增按钮 -->
{% if current_user.has_permission('merchant_create') %}
<a class="btn btn-primary" href="/merchant/add">新增商户</a>
{% endif %}

<!-- 编辑按钮 -->
{% if current_user.has_permission('merchant_edit') %}
<button class="btn btn-sm btn-outline-primary edit-btn">编辑</button>
{% endif %}

<!-- 删除按钮 -->
{% if current_user.has_permission('merchant_delete') %}
<button class="btn btn-sm btn-outline-danger delete-btn">删除</button>
{% endif %}

<!-- 抄表按钮 -->
{% if current_user.has_permission('utility_reading') %}
<button class="btn btn-sm btn-outline-info reading-btn">抄表</button>
{% endif %}

<!-- 缴费按钮 -->
{% if current_user.has_permission('utility_pay') %}
<button class="btn btn-sm btn-outline-success pay-btn">缴费</button>
{% endif %}
```

## 七、Permission 模型变更

```python
class Permission:
    def __init__(self, permission_id=None, permission_name=None,
                 permission_code=None, description=None, module_name=None,
                 operation_code=None, sort_order=0, is_active=True, ...):
        self.permission_id = permission_id
        self.permission_name = permission_name
        self.permission_code = permission_code
        self.description = description
        self.module_name = module_name
        self.operation_code = operation_code   # 新增：view/create/edit/delete/reading/pay/manage
        self.sort_order = sort_order           # 新增：排序
        self.is_active = is_active
```

## 八、实施步骤

1. **数据库迁移脚本**：添加 OperationCode、SortOrder 字段，插入 74 个新权限，迁移角色赋权，标记旧权限
2. **模型层**：Permission 模型新增字段，User 模型增加 LEGACY_PERMISSION_MAP 和兼容逻辑
3. **路由层**：逐模块替换 check_permission 参数（旧代码仍可工作，可分批改造）
4. **模板层**：侧边栏改用 `xxx_view`，页面内按钮改用 `xxx_create/edit/delete/reading/pay`
5. **角色管理页面**：新增角色列表/新增/编辑页，含树形权限分配界面
6. **权限管理页面**：新增权限列表页（只读查看）
7. **验证**：确保旧权限兼容、新权限生效、前端展示正确
