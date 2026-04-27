# CRUD 四级权限精细化 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将权限系统从模块级（`xxx_manage`）升级为 CRUD 四级（`xxx_view/create/edit/delete`）+ 特殊操作（`utility_reading/pay`），共 74 个权限码，渐进兼容旧代码。

**架构：** 数据库新增 OperationCode/SortOrder 字段 → Permission 模型扩展 → User.has_permission() 增加兼容映射 → 路由层逐模块替换权限码 → 模板层侧边栏/按钮替换 → 新增角色管理页面（含树形权限分配）

**技术栈：** Flask + pyodbc (SQL Server) + Jinja2 + Bootstrap 5 + jQuery

---

## 文件结构

| 操作 | 文件路径 | 职责 |
|------|---------|------|
| 创建 | `utils/migrate_crud_permissions.py` | 数据库迁移脚本：新增字段、插入权限、迁移赋权 |
| 修改 | `app/models/permission.py` | Permission 模型新增 operation_code/sort_order 字段 |
| 修改 | `app/models/user.py` | User.has_permission() 增加 LEGACY_PERMISSION_MAP 兼容 |
| 修改 | `app/services/auth_service.py` | get_user_permissions() SQL 查询新增字段 |
| 修改 | `app/routes/user.py` | check_permission 装饰器提取到独立模块；用户路由权限码替换 |
| 创建 | `app/routes/role.py` | 角色管理路由（列表/新增/编辑/删除 + 权限分配 API） |
| 创建 | `app/services/role_service.py` | 角色管理服务层 |
| 创建 | `app/templates/role/list.html` | 角色列表页 |
| 创建 | `app/templates/role/add.html` | 角色新增页 |
| 创建 | `app/templates/role/edit.html` | 角色编辑页（含树形权限分配） |
| 修改 | `app/routes/merchant.py` | 权限码 xxx_manage → xxx_view/create/edit/delete |
| 修改 | `app/routes/contract.py` | 权限码替换 |
| 修改 | `app/routes/plot.py` | 权限码替换 |
| 修改 | `app/routes/utility.py` | 权限码替换 + 新增 reading/pay |
| 修改 | `app/routes/scale.py` | 权限码替换 |
| 修改 | `app/routes/expense.py` | 权限码替换 |
| 修改 | `app/routes/garbage.py` | 权限码替换 |
| 修改 | `app/routes/dorm.py` | 权限码替换 |
| 修改 | `app/routes/finance.py` | 权限码替换 + account 模块拆分 |
| 修改 | `app/routes/salary.py` | 权限码替换 |
| 修改 | `app/routes/customer.py` | 权限码替换 |
| 修改 | `app/routes/dict.py` | 权限码替换 |
| 修改 | `templates/admin_base.html` | 侧边栏权限码 xxx_manage → xxx_view |
| 修改 | `app/__init__.py` | 注册 role_bp 蓝图 |

---

### 任务 1：数据库迁移脚本

**文件：**
- 创建：`utils/migrate_crud_permissions.py`

- [ ] **步骤 1：创建迁移脚本**

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from utils.database import execute_query

PERMISSIONS_DATA = [
    # 市场管理
    ('plot_view', N'地块查看', N'市场管理', 'view', 101),
    ('plot_create', N'地块新增', N'市场管理', 'create', 102),
    ('plot_edit', N'地块编辑', N'市场管理', 'edit', 103),
    ('plot_delete', N'地块删除', N'市场管理', 'delete', 104),
    ('merchant_view', N'商户查看', N'市场管理', 'view', 201),
    ('merchant_create', N'商户新增', N'市场管理', 'create', 202),
    ('merchant_edit', N'商户编辑', N'市场管理', 'edit', 203),
    ('merchant_delete', N'商户删除', N'市场管理', 'delete', 204),
    ('contract_view', N'合同查看', N'市场管理', 'view', 301),
    ('contract_create', N'合同新增', N'市场管理', 'create', 302),
    ('contract_edit', N'合同编辑', N'市场管理', 'edit', 303),
    ('contract_delete', N'合同删除', N'市场管理', 'delete', 304),
    ('utility_view', N'水电查看', N'市场管理', 'view', 401),
    ('utility_create', N'水电新增', N'市场管理', 'create', 402),
    ('utility_edit', N'水电编辑', N'市场管理', 'edit', 403),
    ('utility_delete', N'水电删除', N'市场管理', 'delete', 404),
    ('utility_reading', N'水电抄表', N'市场管理', 'reading', 405),
    ('utility_pay', N'水电缴费', N'市场管理', 'pay', 406),
    ('scale_view', N'磅秤查看', N'市场管理', 'view', 501),
    ('scale_create', N'磅秤新增', N'市场管理', 'create', 502),
    ('scale_edit', N'磅秤编辑', N'市场管理', 'edit', 503),
    ('scale_delete', N'磅秤删除', N'市场管理', 'delete', 504),
    ('expense_view', N'费用单查看', N'市场管理', 'view', 601),
    ('expense_create', N'费用单新增', N'市场管理', 'create', 602),
    ('expense_edit', N'费用单编辑', N'市场管理', 'edit', 603),
    ('expense_delete', N'费用单删除', N'市场管理', 'delete', 604),
    ('garbage_view', N'垃圾清运查看', N'市场管理', 'view', 701),
    ('garbage_create', N'垃圾清运新增', N'市场管理', 'create', 702),
    ('garbage_edit', N'垃圾清运编辑', N'市场管理', 'edit', 703),
    ('garbage_delete', N'垃圾清运删除', N'市场管理', 'delete', 704),
    ('dorm_view', N'宿舍查看', N'市场管理', 'view', 801),
    ('dorm_create', N'宿舍新增', N'市场管理', 'create', 802),
    ('dorm_edit', N'宿舍编辑', N'市场管理', 'edit', 803),
    ('dorm_delete', N'宿舍删除', N'市场管理', 'delete', 804),
    # 财务管理
    ('finance_view', N'财务查看', N'财务管理', 'view', 1001),
    ('finance_create', N'财务新增', N'财务管理', 'create', 1002),
    ('finance_edit', N'财务编辑', N'财务管理', 'edit', 1003),
    ('finance_delete', N'财务删除', N'财务管理', 'delete', 1004),
    ('account_view', N'账户查看', N'财务管理', 'view', 1101),
    ('account_create', N'账户新增', N'财务管理', 'create', 1102),
    ('account_edit', N'账户编辑', N'财务管理', 'edit', 1103),
    ('account_delete', N'账户删除', N'财务管理', 'delete', 1104),
    ('prepayment_view', N'预收预付查看', N'财务管理', 'view', 1201),
    ('prepayment_create', N'预收预付新增', N'财务管理', 'create', 1202),
    ('prepayment_edit', N'预收预付编辑', N'财务管理', 'edit', 1203),
    ('prepayment_delete', N'预收预付删除', N'财务管理', 'delete', 1204),
    ('deposit_view', N'押金查看', N'财务管理', 'view', 1301),
    ('deposit_create', N'押金新增', N'财务管理', 'create', 1302),
    ('deposit_edit', N'押金编辑', N'财务管理', 'edit', 1303),
    ('deposit_delete', N'押金删除', N'财务管理', 'delete', 1304),
    ('customer_view', N'往来客户查看', N'财务管理', 'view', 1401),
    ('customer_create', N'往来客户新增', N'财务管理', 'create', 1402),
    ('customer_edit', N'往来客户编辑', N'财务管理', 'edit', 1403),
    ('customer_delete', N'往来客户删除', N'财务管理', 'delete', 1404),
    ('salary_view', N'工资查看', N'财务管理', 'view', 1501),
    ('salary_create', N'工资新增', N'财务管理', 'create', 1502),
    ('salary_edit', N'工资编辑', N'财务管理', 'edit', 1503),
    ('salary_delete', N'工资删除', N'财务管理', 'delete', 1504),
    # 系统管理
    ('user_view', N'用户查看', N'系统管理', 'view', 2001),
    ('user_create', N'用户新增', N'系统管理', 'create', 2002),
    ('user_edit', N'用户编辑', N'系统管理', 'edit', 2003),
    ('user_delete', N'用户删除', N'系统管理', 'delete', 2004),
    ('role_view', N'角色查看', N'系统管理', 'view', 2101),
    ('role_create', N'角色新增', N'系统管理', 'create', 2102),
    ('role_edit', N'角色编辑', N'系统管理', 'edit', 2103),
    ('role_delete', N'角色删除', N'系统管理', 'delete', 2104),
    ('permission_view', N'权限查看', N'系统管理', 'view', 2201),
    ('permission_create', N'权限新增', N'系统管理', 'create', 2202),
    ('permission_edit', N'权限编辑', N'系统管理', 'edit', 2203),
    ('permission_delete', N'权限删除', N'系统管理', 'delete', 2204),
    ('dict_view', N'字典查看', N'系统管理', 'view', 2301),
    ('dict_create', N'字典新增', N'系统管理', 'create', 2302),
    ('dict_edit', N'字典编辑', N'系统管理', 'edit', 2303),
    ('dict_delete', N'字典删除', N'系统管理', 'delete', 2304),
]

MANAGE_TO_CRUD = {
    'plot_manage': ['plot_view', 'plot_create', 'plot_edit', 'plot_delete'],
    'merchant_manage': ['merchant_view', 'merchant_create', 'merchant_edit', 'merchant_delete'],
    'contract_manage': ['contract_view', 'contract_create', 'contract_edit', 'contract_delete'],
    'utility_manage': ['utility_view', 'utility_create', 'utility_edit', 'utility_delete', 'utility_reading', 'utility_pay'],
    'scale_manage': ['scale_view', 'scale_create', 'scale_edit', 'scale_delete'],
    'expense_manage': ['expense_view', 'expense_create', 'expense_edit', 'expense_delete'],
    'garbage_manage': ['garbage_view', 'garbage_create', 'garbage_edit', 'garbage_delete'],
    'dorm_manage': ['dorm_view', 'dorm_create', 'dorm_edit', 'dorm_delete'],
    'finance_manage': ['finance_view', 'finance_create', 'finance_edit', 'finance_delete'],
    'account_manage': ['account_view', 'account_create', 'account_edit', 'account_delete'],
    'direct_entry': ['account_create'],
    'prepayment_manage': ['prepayment_view', 'prepayment_create', 'prepayment_edit', 'prepayment_delete'],
    'deposit_manage': ['deposit_view', 'deposit_create', 'deposit_edit', 'deposit_delete'],
    'customer_manage': ['customer_view', 'customer_create', 'customer_edit', 'customer_delete'],
    'salary_manage': ['salary_view', 'salary_create', 'salary_edit', 'salary_delete'],
    'user_manage': ['user_view', 'user_create', 'user_edit', 'user_delete'],
    'dict_manage': ['dict_view', 'dict_create', 'dict_edit', 'dict_delete'],
}


def step1_add_columns():
    print('步骤1: 检查并添加 OperationCode/SortOrder 字段...')
    try:
        execute_query("ALTER TABLE Permission ADD OperationCode NVARCHAR(20) NULL", fetch_type='none')
        print('  已添加 OperationCode 字段')
    except Exception as e:
        if 'already exists' in str(e) or '列名已存在' in str(e):
            print('  OperationCode 字段已存在，跳过')
        else:
            raise
    try:
        execute_query("ALTER TABLE Permission ADD SortOrder INT NULL DEFAULT 0", fetch_type='none')
        print('  已添加 SortOrder 字段')
    except Exception as e:
        if 'already exists' in str(e) or '列名已存在' in str(e):
            print('  SortOrder 字段已存在，跳过')
        else:
            raise


def step2_mark_old_permissions():
    print('步骤2: 标记旧权限 OperationCode = manage...')
    execute_query(
        "UPDATE Permission SET OperationCode = N'manage' WHERE OperationCode IS NULL AND (PermissionCode LIKE N'%_manage' OR PermissionCode IN (N'direct_entry', N'utility_reading'))",
        fetch_type='none'
    )
    print('  旧权限已标记')


def step3_insert_new_permissions():
    print('步骤3: 插入 74 个新权限...')
    for code, name, module, op_code, sort_order in PERMISSIONS_DATA:
        existing = execute_query(
            "SELECT PermissionID FROM Permission WHERE PermissionCode = ?",
            (code,), fetch_type='one'
        )
        if existing:
            execute_query(
                "UPDATE Permission SET PermissionName = ?, ModuleName = ?, OperationCode = ?, SortOrder = ? WHERE PermissionCode = ?",
                (name, module, op_code, sort_order, code), fetch_type='none'
            )
        else:
            execute_query(
                "INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, IsActive, OperationCode, SortOrder, CreateTime) VALUES (?, ?, N'', ?, 1, ?, ?, GETDATE())",
                (name, code, module, op_code, sort_order), fetch_type='none'
            )
    print(f'  已处理 {len(PERMISSIONS_DATA)} 个权限')


def step4_migrate_role_permissions():
    print('步骤4: 迁移角色赋权...')
    for old_code, new_codes in MANAGE_TO_CRUD.items():
        old_perm = execute_query(
            "SELECT PermissionID FROM Permission WHERE PermissionCode = ?",
            (old_code,), fetch_type='one'
        )
        if not old_perm:
            print(f'  旧权限 {old_code} 不存在，跳过')
            continue
        old_perm_id = old_perm.PermissionID
        role_ids = execute_query(
            "SELECT DISTINCT RoleID FROM RolePermission WHERE PermissionID = ?",
            (old_perm_id,), fetch_type='all'
        )
        for row in role_ids:
            role_id = row.RoleID
            for new_code in new_codes:
                new_perm = execute_query(
                    "SELECT PermissionID FROM Permission WHERE PermissionCode = ?",
                    (new_code,), fetch_type='one'
                )
                if not new_perm:
                    continue
                exists = execute_query(
                    "SELECT RolePermissionID FROM RolePermission WHERE RoleID = ? AND PermissionID = ?",
                    (role_id, new_perm.PermissionID), fetch_type='one'
                )
                if not exists:
                    execute_query(
                        "INSERT INTO RolePermission (RoleID, PermissionID, CreateTime) VALUES (?, ?, GETDATE())",
                        (role_id, new_perm.PermissionID), fetch_type='none'
                    )
        print(f'  {old_code} → {new_codes}: 已迁移 {len(role_ids)} 个角色')
    print('  角色赋权迁移完成')


def step5_deactivate_old_permissions():
    print('步骤5: 停用旧权限（IsActive = 0）...')
    old_codes = list(MANAGE_TO_CRUD.keys())
    placeholders = ','.join(['?'] * len(old_codes))
    execute_query(
        f"UPDATE Permission SET IsActive = 0 WHERE PermissionCode IN ({placeholders})",
        tuple(old_codes), fetch_type='none'
    )
    print(f'  已停用 {len(old_codes)} 个旧权限')


def main():
    print('=== CRUD 权限迁移开始 ===')
    step1_add_columns()
    step2_mark_old_permissions()
    step3_insert_new_permissions()
    step4_migrate_role_permissions()
    step5_deactivate_old_permissions()
    print('=== CRUD 权限迁移完成 ===')


if __name__ == '__main__':
    main()
```

- [ ] **步骤 2：运行迁移脚本**

运行：`python utils/migrate_crud_permissions.py`
预期：输出 "CRUD 权限迁移完成"，无报错

- [ ] **步骤 3：验证数据库**

运行以下 SQL 确认：
1. `SELECT COUNT(*) FROM Permission WHERE OperationCode IN ('view','create','edit','delete','reading','pay')` → 74
2. `SELECT COUNT(*) FROM Permission WHERE OperationCode = 'manage' AND IsActive = 0` → 旧权限数
3. `SELECT COUNT(*) FROM RolePermission` → 应比迁移前多（每个旧权限扩展为 4-6 个新权限）

- [ ] **步骤 4：Commit**

```bash
git add utils/migrate_crud_permissions.py
git commit -m "feat: 添加 CRUD 权限数据库迁移脚本（74 个权限码）"
```

---

### 任务 2：模型层变更

**文件：**
- 修改：`app/models/permission.py`
- 修改：`app/models/user.py`
- 修改：`app/services/auth_service.py`

- [ ] **步骤 1：更新 Permission 模型**

修改 `app/models/permission.py`，在 `__init__` 中新增 `operation_code` 和 `sort_order` 参数：

```python
class Permission:
    def __init__(self, permission_id=None, permission_name=None, permission_code=None,
                 description=None, module_name=None, operation_code=None, sort_order=0,
                 is_active=True, create_time=None, update_time=None):
        self.permission_id = permission_id
        self.permission_name = permission_name
        self.permission_code = permission_code
        self.description = description
        self.module_name = module_name
        self.operation_code = operation_code
        self.sort_order = sort_order
        self.is_active = is_active
        self.create_time = create_time or datetime.datetime.now()
        self.update_time = update_time
```

- [ ] **步骤 2：更新 User.has_permission() 兼容逻辑**

修改 `app/models/user.py`，在类前添加 `LEGACY_PERMISSION_MAP`，修改 `has_permission` 方法：

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


class User(UserMixin):
    # ... 保持 __init__ 不变 ...

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

- [ ] **步骤 3：更新 auth_service.py 权限查询 SQL**

修改 `app/services/auth_service.py` 的 `get_user_permissions` 方法，SQL 新增 `OperationCode` 和 `SortOrder` 字段：

```python
query = """
    SELECT DISTINCT p.PermissionID, p.PermissionName, p.PermissionCode,
        p.Description, p.ModuleName, p.OperationCode, p.SortOrder,
        p.IsActive, p.CreateTime, p.UpdateTime
    FROM Permission p
    INNER JOIN RolePermission rp ON p.PermissionID = rp.PermissionID
    INNER JOIN UserRole ur ON rp.RoleID = ur.RoleID
    WHERE ur.UserID = ? AND p.IsActive = 1
"""
```

同时更新 Permission 对象构造，新增 `operation_code` 和 `sort_order`：

```python
permission = Permission(
    permission_id=result.PermissionID,
    permission_name=result.PermissionName,
    permission_code=result.PermissionCode,
    description=result.Description,
    module_name=result.ModuleName,
    operation_code=getattr(result, 'OperationCode', None),
    sort_order=getattr(result, 'SortOrder', 0),
    is_active=result.IsActive,
    create_time=result.CreateTime,
    update_time=result.UpdateTime
)
```

- [ ] **步骤 4：启动服务验证兼容性**

运行：`python app.py`
验证：用 admin 账号登录，访问各页面，确认旧权限码通过兼容映射仍然生效

- [ ] **步骤 5：Commit**

```bash
git add app/models/permission.py app/models/user.py app/services/auth_service.py
git commit -m "feat: Permission 模型新增 operation_code/sort_order，has_permission 增加兼容映射"
```

---

### 任务 3：路由层权限码替换（市场管理模块）

**文件：**
- 修改：`app/routes/plot.py`
- 修改：`app/routes/merchant.py`
- 修改：`app/routes/contract.py`
- 修改：`app/routes/utility.py`
- 修改：`app/routes/scale.py`
- 修改：`app/routes/expense.py`
- 修改：`app/routes/garbage.py`
- 修改：`app/routes/dorm.py`

- [ ] **步骤 1：替换 plot.py 权限码**

全局替换规则：
- `check_permission('plot_manage')` 列表页 → `check_permission('plot_view')`
- `check_permission('plot_manage')` 新增页 → `check_permission('plot_create')`
- `check_permission('plot_manage')` 编辑页 → `check_permission('plot_edit')`
- `check_api_permission('plot_manage')` 删除API → `check_api_permission('plot_delete')`

对每个路由函数，根据其操作类型选择对应权限码。具体映射：
- 列表/详情 GET 路由 → `plot_view`
- 新增 GET/POST 路由 → `plot_create`
- 编辑 GET/POST 路由 → `plot_edit`
- 删除 POST 路由 → `plot_delete`

- [ ] **步骤 2：替换 merchant.py 权限码**

同上规则，`merchant_manage` → `merchant_view/create/edit/delete`

- [ ] **步骤 3：替换 contract.py 权限码**

`contract_manage` → `contract_view/create/edit/delete`

- [ ] **步骤 4：替换 utility.py 权限码**

`utility_manage` → `utility_view/create/edit/delete`
额外：
- 抄表相关路由 → `utility_reading`
- 缴费相关路由 → `utility_pay`

- [ ] **步骤 5：替换 scale.py 权限码**

`scale_manage` → `scale_view/create/edit/delete`

- [ ] **步骤 6：替换 expense.py 权限码**

`expense_manage` → `expense_view/create/edit/delete`

- [ ] **步骤 7：替换 garbage.py 权限码**

`garbage_manage` → `garbage_view/create/edit/delete`

- [ ] **步骤 8：替换 dorm.py 权限码**

`dorm_manage` → `dorm_view/create/edit/delete`

- [ ] **步骤 9：启动服务验证**

运行：`python app.py`
验证：admin 登录后访问所有市场管理页面，确认权限检查正常

- [ ] **步骤 10：Commit**

```bash
git add app/routes/plot.py app/routes/merchant.py app/routes/contract.py app/routes/utility.py app/routes/scale.py app/routes/expense.py app/routes/garbage.py app/routes/dorm.py
git commit -m "feat: 市场管理模块路由权限码替换为 CRUD 四级"
```

---

### 任务 4：路由层权限码替换（财务 + 系统管理模块）

**文件：**
- 修改：`app/routes/finance.py`
- 修改：`app/routes/salary.py`
- 修改：`app/routes/customer.py`
- 修改：`app/routes/user.py`
- 修改：`app/routes/dict.py`

- [ ] **步骤 1：替换 finance.py 权限码**

`finance_manage` → `finance_view/create/edit/delete`
`account_manage` → `account_view/create/edit/delete`
`direct_entry` → `account_create`
`prepayment_manage` → `prepayment_view/create/edit/delete`
`deposit_manage` → `deposit_view/create/edit/delete`

具体映射：
- 应收/应付/流水列表 → `finance_view`
- 收款/付款操作 → `finance_create`
- 编辑操作 → `finance_edit`
- 删除操作 → `finance_delete`
- 账户列表 → `account_view`
- 账户新增 → `account_create`
- 直接记账 → `account_create`
- 预收预付列表 → `prepayment_view`
- 预收预付操作 → `prepayment_create/edit/delete`
- 押金列表 → `deposit_view`
- 押金操作 → `deposit_create/edit/delete`

- [ ] **步骤 2：替换 salary.py 权限码**

`salary_manage` → `salary_view/create/edit/delete`

- [ ] **步骤 3：替换 customer.py 权限码**

`customer_manage` → `customer_view/create/edit/delete`

- [ ] **步骤 4：替换 user.py 权限码**

`user_manage` → `user_view/create/edit/delete`

- [ ] **步骤 5：替换 dict.py 权限码**

`dict_manage` → `dict_view/create/edit/delete`

- [ ] **步骤 6：启动服务验证**

运行：`python app.py`
验证：admin 登录后访问所有财务和系统管理页面

- [ ] **步骤 7：Commit**

```bash
git add app/routes/finance.py app/routes/salary.py app/routes/customer.py app/routes/user.py app/routes/dict.py
git commit -m "feat: 财务+系统管理模块路由权限码替换为 CRUD 四级"
```

---

### 任务 5：模板层权限码替换

**文件：**
- 修改：`templates/admin_base.html`
- 修改：所有业务模块模板中的操作按钮权限检查

- [ ] **步骤 1：替换 admin_base.html 侧边栏权限码**

所有 `has_permission('xxx_manage')` 替换为 `has_permission('xxx_view')`：

```
has_permission('plot_manage') → has_permission('plot_view')
has_permission('merchant_manage') → has_permission('merchant_view')
has_permission('contract_manage') → has_permission('contract_view')
has_permission('utility_manage') → has_permission('utility_view')
has_permission('scale_manage') → has_permission('scale_view')
has_permission('expense_manage') → has_permission('expense_view')
has_permission('garbage_manage') → has_permission('garbage_view')
has_permission('dorm_manage') → has_permission('dorm_view')
has_permission('finance_manage') → has_permission('finance_view')
has_permission('salary_manage') → has_permission('salary_view')
has_permission('prepayment_manage') → has_permission('prepayment_view')
has_permission('deposit_manage') → has_permission('deposit_view')
has_permission('user_manage') → has_permission('user_view')
has_permission('dict_manage') → has_permission('dict_view')
```

侧边栏新增角色管理和权限管理菜单项：

```html
{% if current_user.has_permission('role_view') %}
<a class="sidebar-item {% if request.endpoint and 'role' in request.endpoint %}active{% endif %}" href="{{ url_for('role.role_list') }}">
    <i class="fa fa-user-shield"></i>
    <span class="sidebar-item-text">角色管理</span>
</a>
{% endif %}
{% if current_user.has_permission('permission_view') %}
<a class="sidebar-item {% if request.endpoint and 'permission' in request.endpoint %}active{% endif %}" href="{{ url_for('role.permission_list') }}">
    <i class="fa fa-key"></i>
    <span class="sidebar-item-text">权限管理</span>
</a>
{% endif %}
```

- [ ] **步骤 2：替换各业务模板中的操作按钮权限检查**

对每个列表页模板，将操作按钮的权限检查从 `xxx_manage` 替换为具体操作权限：

- "新增"按钮 → `has_permission('xxx_create')`
- "编辑"按钮 → `has_permission('xxx_edit')`
- "删除"按钮 → `has_permission('xxx_delete')`
- "抄表"按钮 → `has_permission('utility_reading')`
- "缴费"按钮 → `has_permission('utility_pay')`

涉及的模板文件（按需检查和修改）：
- `templates/merchant/list.html`
- `templates/contract/list.html`
- `templates/plot/list.html`
- `templates/utility/list.html`
- `templates/scale/list.html`
- `templates/expense/list.html`
- `templates/garbage/list.html`
- `templates/dorm/rooms.html`
- `templates/finance/receivable.html`
- `templates/finance/payable.html`
- `templates/finance/cash_flow.html`
- `templates/finance/account.html`
- `templates/finance/deposit.html`
- `templates/finance/prepayment.html`
- `templates/finance/direct_entry.html`
- `templates/salary/profile.html`
- `templates/customer/list.html`
- `templates/user/list.html`
- `templates/dict/list.html`

- [ ] **步骤 3：启动服务验证**

运行：`python app.py`
验证：侧边栏菜单显示正确，操作按钮权限控制生效

- [ ] **步骤 4：Commit**

```bash
git add templates/admin_base.html templates/merchant/ templates/contract/ templates/plot/ templates/utility/ templates/scale/ templates/expense/ templates/garbage/ templates/dorm/ templates/finance/ templates/salary/ templates/customer/ templates/user/ templates/dict/
git commit -m "feat: 模板层权限码替换为 CRUD 四级，侧边栏新增角色/权限管理菜单"
```

---

### 任务 6：角色管理路由和服务层

**文件：**
- 创建：`app/routes/role.py`
- 创建：`app/services/role_service.py`
- 修改：`app/__init__.py`

- [ ] **步骤 1：创建 role_service.py**

```python
from utils.database import execute_query
from app.models.role import Role
from app.models.permission import Permission


class RoleService:
    @staticmethod
    def get_all_roles():
        query = "SELECT RoleID, RoleName, RoleCode, Description, IsActive, CreateTime, UpdateTime FROM Role ORDER BY RoleID"
        results = execute_query(query, fetch_type='all')
        return [Role(role_id=r.RoleID, role_name=r.RoleName, role_code=r.RoleCode,
                     description=r.Description, is_active=r.IsActive,
                     create_time=r.CreateTime, update_time=r.UpdateTime) for r in results]

    @staticmethod
    def get_role_by_id(role_id):
        query = "SELECT RoleID, RoleName, RoleCode, Description, IsActive, CreateTime, UpdateTime FROM Role WHERE RoleID = ?"
        r = execute_query(query, (role_id,), fetch_type='one')
        if not r:
            return None
        return Role(role_id=r.RoleID, role_name=r.RoleName, role_code=r.RoleCode,
                    description=r.Description, is_active=r.IsActive,
                    create_time=r.CreateTime, update_time=r.UpdateTime)

    @staticmethod
    def create_role(role_name, role_code, description=None):
        existing = execute_query("SELECT RoleID FROM Role WHERE RoleCode = ?", (role_code,), fetch_type='one')
        if existing:
            return None
        execute_query(
            "INSERT INTO Role (RoleName, RoleCode, Description, IsActive, CreateTime) VALUES (?, ?, ?, 1, GETDATE())",
            (role_name, role_code, description), fetch_type='none'
        )
        result = execute_query("SELECT RoleID FROM Role WHERE RoleCode = ?", (role_code,), fetch_type='one')
        return result.RoleID if result else None

    @staticmethod
    def update_role(role_id, role_name, description=None):
        execute_query(
            "UPDATE Role SET RoleName = ?, Description = ?, UpdateTime = GETDATE() WHERE RoleID = ?",
            (role_name, description, role_id), fetch_type='none'
        )

    @staticmethod
    def delete_role(role_id):
        if role_id <= 3:
            return False
        execute_query("DELETE FROM RolePermission WHERE RoleID = ?", (role_id,), fetch_type='none')
        execute_query("DELETE FROM UserRole WHERE RoleID = ?", (role_id,), fetch_type='none')
        execute_query("DELETE FROM Role WHERE RoleID = ?", (role_id,), fetch_type='none')
        return True

    @staticmethod
    def get_all_permissions_grouped():
        query = """SELECT PermissionID, PermissionName, PermissionCode, Description, ModuleName,
                   OperationCode, SortOrder, IsActive, CreateTime, UpdateTime
                   FROM Permission WHERE IsActive = 1 AND OperationCode IN ('view','create','edit','delete','reading','pay')
                   ORDER BY ModuleName, SortOrder"""
        results = execute_query(query, fetch_type='all')
        permissions = []
        for r in results:
            permissions.append(Permission(
                permission_id=r.PermissionID, permission_name=r.PermissionName,
                permission_code=r.PermissionCode, description=r.Description,
                module_name=r.ModuleName, operation_code=getattr(r, 'OperationCode', None),
                sort_order=getattr(r, 'SortOrder', 0), is_active=r.IsActive,
                create_time=r.CreateTime, update_time=r.UpdateTime
            ))
        grouped = {}
        for p in permissions:
            if p.module_name not in grouped:
                grouped[p.module_name] = []
            grouped[p.module_name].append(p)
        return grouped

    @staticmethod
    def get_role_permissions(role_id):
        query = "SELECT PermissionID FROM RolePermission WHERE RoleID = ?"
        results = execute_query(query, (role_id,), fetch_type='all')
        return set(r.PermissionID for r in results)

    @staticmethod
    def update_role_permissions(role_id, permission_ids):
        execute_query("DELETE FROM RolePermission WHERE RoleID = ?", (role_id,), fetch_type='none')
        for pid in permission_ids:
            execute_query(
                "INSERT INTO RolePermission (RoleID, PermissionID, CreateTime) VALUES (?, ?, GETDATE())",
                (role_id, pid), fetch_type='none'
            )

    @staticmethod
    def get_all_permissions():
        query = """SELECT PermissionID, PermissionName, PermissionCode, Description, ModuleName,
                   OperationCode, SortOrder, IsActive, CreateTime, UpdateTime
                   FROM Permission ORDER BY ModuleName, SortOrder"""
        results = execute_query(query, fetch_type='all')
        return [Permission(
            permission_id=r.PermissionID, permission_name=r.PermissionName,
            permission_code=r.PermissionCode, description=r.Description,
            module_name=r.ModuleName, operation_code=getattr(r, 'OperationCode', None),
            sort_order=getattr(r, 'SortOrder', 0), is_active=r.IsActive,
            create_time=r.CreateTime, update_time=r.UpdateTime
        ) for r in results]
```

- [ ] **步骤 2：创建 role.py 路由**

```python
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.services.role_service import RoleService
from functools import wraps

role_bp = Blueprint('role', __name__)


def check_permission(permission_code):
    def decorator(f):
        @login_required
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(current_user, 'has_permission') or not current_user.has_permission(permission_code):
                flash('您没有权限执行此操作', 'danger')
                return redirect(url_for('auth.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_api_permission(permission_code):
    def decorator(f):
        @login_required
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(current_user, 'has_permission') or not current_user.has_permission(permission_code):
                return jsonify({'success': False, 'message': '您没有权限执行此操作'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@role_bp.route('/list')
@login_required
@check_permission('role_view')
def role_list():
    roles = RoleService.get_all_roles()
    return render_template('role/list.html', roles=roles)


@role_bp.route('/add', methods=['GET', 'POST'])
@login_required
@check_permission('role_create')
def role_add():
    if request.method == 'POST':
        role_name = request.form.get('role_name', '').strip()
        role_code = request.form.get('role_code', '').strip()
        description = request.form.get('description', '').strip()
        if not role_name or not role_code:
            flash('角色名称和编码不能为空', 'danger')
            return redirect(url_for('role.role_add'))
        result = RoleService.create_role(role_name, role_code, description)
        if result is None:
            flash('角色编码已存在', 'danger')
            return redirect(url_for('role.role_add'))
        flash('角色创建成功', 'success')
        return redirect(url_for('role.role_list'))
    return render_template('role/add.html')


@role_bp.route('/edit/<int:role_id>', methods=['GET', 'POST'])
@login_required
@check_permission('role_edit')
def role_edit(role_id):
    role = RoleService.get_role_by_id(role_id)
    if not role:
        flash('角色不存在', 'danger')
        return redirect(url_for('role.role_list'))
    if request.method == 'POST':
        role_name = request.form.get('role_name', '').strip()
        description = request.form.get('description', '').strip()
        permission_ids = request.form.getlist('permission_ids', type=int)
        RoleService.update_role(role_id, role_name, description)
        RoleService.update_role_permissions(role_id, permission_ids)
        flash('角色更新成功', 'success')
        return redirect(url_for('role.role_list'))
    permissions_grouped = RoleService.get_all_permissions_grouped()
    role_permission_ids = RoleService.get_role_permissions(role_id)
    return render_template('role/edit.html', role=role, permissions_grouped=permissions_grouped, role_permission_ids=role_permission_ids)


@role_bp.route('/delete/<int:role_id>', methods=['POST'])
@login_required
@check_api_permission('role_delete')
def role_delete(role_id):
    if role_id <= 3:
        return jsonify({'success': False, 'message': '系统内置角色不允许删除'})
    result = RoleService.delete_role(role_id)
    if result:
        return jsonify({'success': True, 'message': '删除成功'})
    return jsonify({'success': False, 'message': '删除失败'})


@role_bp.route('/permissions')
@login_required
@check_permission('permission_view')
def permission_list():
    permissions = RoleService.get_all_permissions()
    return render_template('role/permissions.html', permissions=permissions)
```

- [ ] **步骤 3：注册 role_bp 蓝图**

修改 `app/__init__.py`，在蓝图注册区域添加：

```python
from app.routes.role import role_bp
app.register_blueprint(role_bp, url_prefix='/role')
```

- [ ] **步骤 4：Commit**

```bash
git add app/routes/role.py app/services/role_service.py app/__init__.py
git commit -m "feat: 添加角色管理路由和服务层（列表/新增/编辑/删除/权限分配）"
```

---

### 任务 7：角色管理前端页面

**文件：**
- 创建：`app/templates/role/list.html`
- 创建：`app/templates/role/add.html`
- 创建：`app/templates/role/edit.html`
- 创建：`app/templates/role/permissions.html`

- [ ] **步骤 1：创建角色列表页 `role/list.html`**

继承 `admin_base.html`，展示角色列表表格（角色名称、编码、描述、操作按钮），操作按钮受 `role_edit`/`role_delete` 权限控制。新增按钮受 `role_create` 权限控制。

- [ ] **步骤 2：创建角色新增页 `role/add.html`**

继承 `admin_base.html`，包含角色名称、编码、描述表单，Ajax POST 提交。

- [ ] **步骤 3：创建角色编辑页 `role/edit.html`（含树形权限分配）**

继承 `admin_base.html`，包含角色名称、描述表单 + 权限分配区域。

权限分配区域按 ModuleName 分组，每组内按模块前缀排列，每个模块一行 checkbox。交互逻辑：
- 勾选非 view 操作时自动勾选 view
- 取消 view 时自动取消同模块其他操作
- 快捷操作按钮：全选查看/新增/编辑/删除

关键 JS 逻辑：

```javascript
function onPermissionChange(checkbox) {
    var code = checkbox.value;
    var module = code.substring(0, code.lastIndexOf('_'));
    var op = code.substring(code.lastIndexOf('_') + 1);

    if (checkbox.checked && op !== 'view') {
        var viewCb = document.querySelector('input[name="permission_ids"][value="' + module + '_view"]');
        if (viewCb && !viewCb.checked) viewCb.checked = true;
    }

    if (!checkbox.checked && op === 'view') {
        document.querySelectorAll('input[name="permission_ids"]').forEach(function(cb) {
            if (cb.value.startsWith(module + '_') && cb.value !== module + '_view') {
                cb.checked = false;
            }
        });
    }
}
```

- [ ] **步骤 4：创建权限列表页 `role/permissions.html`**

继承 `admin_base.html`，只读展示所有权限（按 ModuleName 分组），显示权限码、名称、操作类型、排序。

- [ ] **步骤 5：启动服务验证**

运行：`python app.py`
验证：访问 `/role/list`、`/role/add`、`/role/edit/1`、`/role/permissions` 页面正常显示

- [ ] **步骤 6：Commit**

```bash
git add app/templates/role/
git commit -m "feat: 添加角色管理前端页面（列表/新增/编辑含权限分配/权限查看）"
```

---

### 任务 8：端到端验证

**文件：** 无新文件

- [ ] **步骤 1：运行迁移脚本**

运行：`python utils/migrate_crud_permissions.py`
预期：输出 "CRUD 权限迁移完成"

- [ ] **步骤 2：启动服务**

运行：`python app.py`

- [ ] **步骤 3：验证 admin 角色**

1. 用 admin 账号登录
2. 访问所有页面，确认功能正常
3. 访问 `/role/edit/1`，确认 admin 角色拥有所有 74 个权限
4. 访问 `/role/permissions`，确认 74 个权限码全部显示

- [ ] **步骤 4：验证 staff 角色**

1. 访问 `/role/edit/2`，确认 staff 角色拥有除 user 模块外的所有 CRUD 权限
2. 用 staff 账号登录，确认无法访问用户管理页面

- [ ] **步骤 5：验证 merchant 角色**

1. 访问 `/role/edit/3`，确认 merchant 角色仅拥有 contract_view、utility_view、scale_view
2. 用 merchant 账号登录，确认只能查看，无法新增/编辑/删除

- [ ] **步骤 6：验证兼容映射**

1. 临时在模板中添加 `{{ current_user.has_permission('merchant_manage') }}` 测试
2. 确认返回 True（通过 LEGACY_PERMISSION_MAP 映射到 merchant_view）

- [ ] **步骤 7：验证权限分配交互**

1. 访问 `/role/add`，创建新角色 "测试角色"
2. 勾选 "商户新增"，确认自动勾选 "商户查看"
3. 取消 "商户查看"，确认自动取消 "商户新增/编辑/删除"
4. 保存后确认权限正确写入数据库

- [ ] **步骤 8：Commit 验证通过标记**

```bash
git commit --allow-empty -m "verify: CRUD 四级权限系统端到端验证通过"
```
