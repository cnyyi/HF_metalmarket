# CRUD 四级权限精细化 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将现有模块级权限（`merchant_manage`）拆分为 CRUD 四级权限（`merchant_view/create/edit/delete`），渐进兼容旧权限，新增角色权限管理页面。

**架构：** 在现有 RBAC 框架上扩展——Permission 表新增 OperationCode/SortOrder 字段，User.has_permission 增加旧权限映射兼容，路由装饰器和模板逐步替换为细粒度权限码，新增角色管理路由和树形权限分配页面。

**技术栈：** Python / Flask / Jinja2 / SQL Server / jQuery + Bootstrap 5

---

## 文件结构

| 操作 | 文件 | 职责 |
|------|------|------|
| 创建 | `utils/migrations/add_crud_permissions.py` | 数据库迁移脚本：新增字段、插入新权限、迁移角色赋权 |
| 修改 | `app/models/permission.py` | Permission 模型新增 operation_code、sort_order 字段 |
| 修改 | `app/models/user.py` | User 模型新增 LEGACY_PERMISSION_MAP 和 has_permission 兼容逻辑 |
| 修改 | `app/services/auth_service.py` | 权限加载 SQL 新增 OperationCode/SortOrder 列 |
| 修改 | `app/routes/user.py` | 路由装饰器权限码替换 |
| 修改 | `app/routes/merchant.py` | 路由装饰器权限码替换 |
| 修改 | `app/routes/contract.py` | 路由装饰器权限码替换 |
| 修改 | `app/routes/plot.py` | 路由装饰器权限码替换 |
| 修改 | `app/routes/salary.py` | 路由装饰器权限码替换 |
| 修改 | `app/routes/customer.py` | 路由装饰器权限码替换 |
| 修改 | `app/routes/finance.py` | 路由装饰器权限码替换 |
| 修改 | `app/routes/dorm.py` | 路由装饰器权限码替换 |
| 修改 | `app/routes/garbage.py` | 路由装饰器权限码替换 |
| 修改 | `app/routes/expense.py` | 路由装饰器权限码替换 |
| 修改 | `app/routes/dict.py` | 路由装饰器权限码替换 + 统一装饰器来源 |
| 创建 | `app/routes/role.py` | 角色管理路由（列表、编辑、权限分配 API） |
| 创建 | `app/services/role_service.py` | 角色管理业务逻辑 |
| 修改 | `app/routes/__init__.py` | 注册 role 蓝图 |
| 修改 | `templates/admin_base.html` | 侧边栏权限码替换 |
| 修改 | `templates/user/list.html` | 操作按钮权限码替换 |
| 修改 | `templates/dict/list.html` | 操作按钮权限码替换 |
| 创建 | `templates/role/list.html` | 角色列表页 |
| 创建 | `templates/role/edit.html` | 角色编辑页（含树形权限分配） |

---

### 任务 1：数据库迁移脚本

**文件：**
- 创建：`utils/migrations/add_crud_permissions.py`

- [ ] **步骤 1：编写迁移脚本**

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.db_connection import execute_query, execute_update

def migrate():
    print("=== CRUD 四级权限迁移开始 ===")

    print("[1/5] 添加 OperationCode、SortOrder 字段...")
    try:
        execute_update("""
            ALTER TABLE Permission ADD OperationCode NVARCHAR(20) NULL
        """)
    except Exception:
        print("  OperationCode 字段已存在，跳过")

    try:
        execute_update("""
            ALTER TABLE Permission ADD SortOrder INT NULL DEFAULT 0
        """)
    except Exception:
        print("  SortOrder 字段已存在，跳过")

    print("[2/5] 标记旧权限 OperationCode = 'manage'...")
    execute_update("""
        UPDATE Permission SET OperationCode = 'manage'
        WHERE OperationCode IS NULL AND (
            PermissionCode LIKE '%_manage'
            OR PermissionCode IN ('direct_entry', 'utility_reading')
        )
    """)

    print("[3/5] 插入 CRUD 四级新权限...")
    new_permissions = [
        ('地块查看', 'plot_view', '查看地块信息', '市场管理', 'view', 101),
        ('地块新增', 'plot_create', '新增地块', '市场管理', 'create', 102),
        ('地块编辑', 'plot_edit', '编辑地块信息', '市场管理', 'edit', 103),
        ('地块删除', 'plot_delete', '删除地块', '市场管理', 'delete', 104),
        ('商户查看', 'merchant_view', '查看商户信息', '市场管理', 'view', 201),
        ('商户新增', 'merchant_create', '新增商户', '市场管理', 'create', 202),
        ('商户编辑', 'merchant_edit', '编辑商户信息', '市场管理', 'edit', 203),
        ('商户删除', 'merchant_delete', '删除商户', '市场管理', 'delete', 204),
        ('合同查看', 'contract_view', '查看合同信息', '市场管理', 'view', 301),
        ('合同新增', 'contract_create', '新增合同', '市场管理', 'create', 302),
        ('合同编辑', 'contract_edit', '编辑合同信息', '市场管理', 'edit', 303),
        ('合同删除', 'contract_delete', '删除合同', '市场管理', 'delete', 304),
        ('水电查看', 'utility_view', '查看水电计费信息', '市场管理', 'view', 401),
        ('水电新增', 'utility_create', '新增水电抄表', '市场管理', 'create', 402),
        ('水电编辑', 'utility_edit', '编辑水电计费信息', '市场管理', 'edit', 403),
        ('水电删除', 'utility_delete', '删除水电记录', '市场管理', 'delete', 404),
        ('磅秤查看', 'scale_view', '查看磅秤数据', '市场管理', 'view', 501),
        ('磅秤新增', 'scale_create', '新增磅秤记录', '市场管理', 'create', 502),
        ('磅秤编辑', 'scale_edit', '编辑磅秤数据', '市场管理', 'edit', 503),
        ('磅秤删除', 'scale_delete', '删除磅秤记录', '市场管理', 'delete', 504),
        ('费用单查看', 'expense_view', '查看费用单', '市场管理', 'view', 601),
        ('费用单新增', 'expense_create', '新增费用单', '市场管理', 'create', 602),
        ('费用单编辑', 'expense_edit', '编辑费用单', '市场管理', 'edit', 603),
        ('费用单删除', 'expense_delete', '删除费用单', '市场管理', 'delete', 604),
        ('垃圾清运查看', 'garbage_view', '查看垃圾清运信息', '市场管理', 'view', 701),
        ('垃圾清运新增', 'garbage_create', '新增垃圾清运记录', '市场管理', 'create', 702),
        ('垃圾清运编辑', 'garbage_edit', '编辑垃圾清运信息', '市场管理', 'edit', 703),
        ('垃圾清运删除', 'garbage_delete', '删除垃圾清运记录', '市场管理', 'delete', 704),
        ('宿舍查看', 'dorm_view', '查看宿舍信息', '市场管理', 'view', 801),
        ('宿舍新增', 'dorm_create', '新增宿舍记录', '市场管理', 'create', 802),
        ('宿舍编辑', 'dorm_edit', '编辑宿舍信息', '市场管理', 'edit', 803),
        ('宿舍删除', 'dorm_delete', '删除宿舍记录', '市场管理', 'delete', 804),
        ('财务查看', 'finance_view', '查看财务信息', '财务管理', 'view', 1001),
        ('财务新增', 'finance_create', '新增财务记录', '财务管理', 'create', 1002),
        ('财务编辑', 'finance_edit', '编辑财务信息', '财务管理', 'edit', 1003),
        ('财务删除', 'finance_delete', '删除财务记录', '财务管理', 'delete', 1004),
        ('预收预付查看', 'prepayment_view', '查看预收预付信息', '财务管理', 'view', 1101),
        ('预收预付新增', 'prepayment_create', '新增预收预付', '财务管理', 'create', 1102),
        ('预收预付编辑', 'prepayment_edit', '编辑预收预付信息', '财务管理', 'edit', 1103),
        ('预收预付删除', 'prepayment_delete', '删除预收预付记录', '财务管理', 'delete', 1104),
        ('押金查看', 'deposit_view', '查看押金信息', '财务管理', 'view', 1201),
        ('押金新增', 'deposit_create', '新增押金', '财务管理', 'create', 1202),
        ('押金编辑', 'deposit_edit', '编辑押金信息', '财务管理', 'edit', 1203),
        ('押金删除', 'deposit_delete', '删除押金记录', '财务管理', 'delete', 1204),
        ('往来客户查看', 'customer_view', '查看往来客户信息', '财务管理', 'view', 1301),
        ('往来客户新增', 'customer_create', '新增往来客户', '财务管理', 'create', 1302),
        ('往来客户编辑', 'customer_edit', '编辑往来客户信息', '财务管理', 'edit', 1303),
        ('往来客户删除', 'customer_delete', '删除往来客户', '财务管理', 'delete', 1304),
        ('工资查看', 'salary_view', '查看工资信息', '财务管理', 'view', 1401),
        ('工资新增', 'salary_create', '新增工资记录', '财务管理', 'create', 1402),
        ('工资编辑', 'salary_edit', '编辑工资信息', '财务管理', 'edit', 1403),
        ('工资删除', 'salary_delete', '删除工资记录', '财务管理', 'delete', 1404),
        ('用户查看', 'user_view', '查看用户信息', '系统管理', 'view', 2001),
        ('用户新增', 'user_create', '新增用户', '系统管理', 'create', 2002),
        ('用户编辑', 'user_edit', '编辑用户信息', '系统管理', 'edit', 2003),
        ('用户删除', 'user_delete', '删除用户', '系统管理', 'delete', 2004),
        ('角色查看', 'role_view', '查看角色信息', '系统管理', 'view', 2101),
        ('角色新增', 'role_create', '新增角色', '系统管理', 'create', 2102),
        ('角色编辑', 'role_edit', '编辑角色信息', '系统管理', 'edit', 2103),
        ('角色删除', 'role_delete', '删除角色', '系统管理', 'delete', 2104),
        ('权限查看', 'permission_view', '查看权限信息', '系统管理', 'view', 2201),
        ('权限新增', 'permission_create', '新增权限', '系统管理', 'create', 2202),
        ('权限编辑', 'permission_edit', '编辑权限信息', '系统管理', 'edit', 2203),
        ('权限删除', 'permission_delete', '删除权限', '系统管理', 'delete', 2204),
        ('字典查看', 'dict_view', '查看字典信息', '系统管理', 'view', 2301),
        ('字典新增', 'dict_create', '新增字典', '系统管理', 'create', 2302),
        ('字典编辑', 'dict_edit', '编辑字典信息', '系统管理', 'edit', 2303),
        ('字典删除', 'dict_delete', '删除字典', '系统管理', 'delete', 2304),
    ]

    for pname, pcode, pdesc, mname, op_code, sort_order in new_permissions:
        existing = execute_query(
            "SELECT PermissionID FROM Permission WHERE PermissionCode = ?",
            (pcode,), fetch_type='one'
        )
        if existing:
            execute_update("""
                UPDATE Permission SET PermissionName=?, Description=?, ModuleName=?, OperationCode=?, SortOrder=?
                WHERE PermissionCode=?
            """, (pname, pdesc, mname, op_code, sort_order, pcode))
        else:
            execute_update("""
                INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, OperationCode, SortOrder, IsActive)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (pname, pcode, pdesc, mname, op_code, sort_order))

    print("[4/5] 迁移角色赋权：拥有旧 manage 权限的角色自动获得对应 CRUD 权限...")
    legacy_map = {
        'plot_manage': ['plot_view', 'plot_create', 'plot_edit', 'plot_delete'],
        'merchant_manage': ['merchant_view', 'merchant_create', 'merchant_edit', 'merchant_delete'],
        'contract_manage': ['contract_view', 'contract_create', 'contract_edit', 'contract_delete'],
        'utility_manage': ['utility_view', 'utility_create', 'utility_edit', 'utility_delete'],
        'scale_manage': ['scale_view', 'scale_create', 'scale_edit', 'scale_delete'],
        'expense_manage': ['expense_view', 'expense_create', 'expense_edit', 'expense_delete'],
        'garbage_manage': ['garbage_view', 'garbage_create', 'garbage_edit', 'garbage_delete'],
        'dorm_manage': ['dorm_view', 'dorm_create', 'dorm_edit', 'dorm_delete'],
        'finance_manage': ['finance_view', 'finance_create', 'finance_edit', 'finance_delete'],
        'salary_manage': ['salary_view', 'salary_create', 'salary_edit', 'salary_delete'],
        'user_manage': ['user_view', 'user_create', 'user_edit', 'user_delete'],
        'dict_manage': ['dict_view', 'dict_create', 'dict_edit', 'dict_delete'],
        'prepayment_manage': ['prepayment_view', 'prepayment_create', 'prepayment_edit', 'prepayment_delete'],
        'deposit_manage': ['deposit_view', 'deposit_create', 'deposit_edit', 'deposit_delete'],
        'customer_manage': ['customer_view', 'customer_create', 'customer_edit', 'customer_delete'],
        'role_manage': ['role_view', 'role_create', 'role_edit', 'role_delete'],
        'permission_manage': ['permission_view', 'permission_create', 'permission_edit', 'permission_delete'],
        'account_manage': ['finance_view', 'finance_create', 'finance_edit', 'finance_delete'],
        'direct_entry': ['finance_create'],
        'utility_reading': ['utility_view', 'utility_create'],
    }

    for old_code, new_codes in legacy_map.items():
        old_perm = execute_query(
            "SELECT PermissionID FROM Permission WHERE PermissionCode = ?", (old_code,), fetch_type='one'
        )
        if not old_perm:
            continue
        role_ids = execute_query("""
            SELECT DISTINCT RoleID FROM RolePermission WHERE PermissionID = ?
        """, (old_perm.permission_id,), fetch_type='all')
        for role_row in role_ids:
            rid = role_row.role_id
            for nc in new_codes:
                new_perm = execute_query(
                    "SELECT PermissionID FROM Permission WHERE PermissionCode = ?", (nc,), fetch_type='one'
                )
                if not new_perm:
                    continue
                exists = execute_query("""
                    SELECT RolePermissionID FROM RolePermission
                    WHERE RoleID = ? AND PermissionID = ?
                """, (rid, new_perm.permission_id), fetch_type='one')
                if not exists:
                    execute_update("""
                        INSERT INTO RolePermission (RoleID, PermissionID, CreateTime) VALUES (?, ?, GETDATE())
                    """, (rid, new_perm.permission_id))

    print("[5/5] 标记旧权限为不活跃...")
    for old_code in legacy_map.keys():
        execute_update("""
            UPDATE Permission SET IsActive = 0 WHERE PermissionCode = ?
        """, (old_code,))

    print("=== CRUD 四级权限迁移完成 ===")

if __name__ == '__main__':
    migrate()
```

- [ ] **步骤 2：运行迁移脚本**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python utils/migrations/add_crud_permissions.py`
预期：输出迁移步骤日志，无报错

- [ ] **步骤 3：验证数据库**

运行 SQL 验证新权限已插入、旧权限已标记不活跃、角色赋权已迁移：
```sql
SELECT PermissionCode, OperationCode, SortOrder, IsActive FROM Permission WHERE OperationCode IN ('view','create','edit','delete') ORDER BY SortOrder;
SELECT COUNT(*) FROM Permission WHERE OperationCode = 'manage' AND IsActive = 1;
SELECT r.RoleCode, p.PermissionCode FROM Role r JOIN RolePermission rp ON r.RoleID = rp.RoleID JOIN Permission p ON rp.PermissionID = p.PermissionID WHERE r.RoleCode = 'admin' AND p.OperationCode = 'view' ORDER BY p.SortOrder;
```

- [ ] **步骤 4：Commit**

```bash
git add utils/migrations/add_crud_permissions.py
git commit -m "feat: 添加 CRUD 四级权限数据库迁移脚本"
```

---

### 任务 2：模型层改造

**文件：**
- 修改：`app/models/permission.py`
- 修改：`app/models/user.py`
- 修改：`app/services/auth_service.py`

- [ ] **步骤 1：修改 Permission 模型**

在 `app/models/permission.py` 中新增 `operation_code` 和 `sort_order` 字段：

```python
import datetime

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
        self.sort_order = sort_order or 0
        self.is_active = is_active
        self.create_time = create_time or datetime.datetime.now()
        self.update_time = update_time
```

- [ ] **步骤 2：修改 User 模型，增加 LEGACY_PERMISSION_MAP 和兼容逻辑**

在 `app/models/user.py` 中，在 User 类之前添加映射表，修改 `has_permission` 方法：

```python
LEGACY_PERMISSION_MAP = {
    'plot_manage': 'plot_view',
    'merchant_manage': 'merchant_view',
    'contract_manage': 'contract_view',
    'utility_manage': 'utility_view',
    'scale_manage': 'scale_view',
    'expense_manage': 'expense_view',
    'garbage_manage': 'garbage_view',
    'dorm_manage': 'dorm_view',
    'finance_manage': 'finance_view',
    'salary_manage': 'salary_view',
    'user_manage': 'user_view',
    'dict_manage': 'dict_view',
    'prepayment_manage': 'prepayment_view',
    'deposit_manage': 'deposit_view',
    'customer_manage': 'customer_view',
    'role_manage': 'role_view',
    'permission_manage': 'permission_view',
    'account_manage': 'finance_view',
    'direct_entry': 'finance_create',
    'utility_reading': 'utility_view',
}
```

修改 `has_permission` 方法：

```python
    def has_permission(self, permission_code):
        for permission in self.permissions:
            if permission.permission_code == permission_code:
                return True
        mapped = LEGACY_PERMISSION_MAP.get(permission_code)
        if mapped:
            for permission in self.permissions:
                if permission.permission_code == mapped:
                    return True
        return False
```

- [ ] **步骤 3：修改 auth_service.py 权限加载 SQL**

在 `app/services/auth_service.py` 的 `get_user_permissions` 方法中，SQL 查询新增 `OperationCode` 和 `SortOrder` 列：

```python
@staticmethod
def get_user_permissions(user_id):
    query = """
        SELECT DISTINCT p.PermissionID, p.PermissionName, p.PermissionCode,
            p.Description, p.ModuleName, p.OperationCode, p.SortOrder,
            p.IsActive, p.CreateTime, p.UpdateTime
        FROM Permission p
        INNER JOIN RolePermission rp ON p.PermissionID = rp.PermissionID
        INNER JOIN UserRole ur ON rp.RoleID = ur.RoleID
        WHERE ur.UserID = ? AND p.IsActive = 1
        ORDER BY p.SortOrder
    """
    results = execute_query(query, (user_id,), fetch_type='all')
    permissions = []
    if results:
        for row in results:
            permissions.append(Permission(
                permission_id=row.PermissionID,
                permission_name=row.PermissionName,
                permission_code=row.PermissionCode,
                description=row.Description,
                module_name=row.ModuleName,
                operation_code=getattr(row, 'OperationCode', None),
                sort_order=getattr(row, 'SortOrder', 0),
                is_active=row.IsActive,
                create_time=row.CreateTime,
                update_time=row.UpdateTime
            ))
    return permissions
```

同样修改 `AuthService.has_permission` 静态方法，增加兼容逻辑：

```python
@staticmethod
def has_permission(user_id, permission_code):
    query = """
        SELECT COUNT(*) as count
        FROM Permission p
        INNER JOIN RolePermission rp ON p.PermissionID = rp.PermissionID
        INNER JOIN UserRole ur ON rp.RoleID = ur.RoleID
        WHERE ur.UserID = ? AND p.PermissionCode = ? AND p.IsActive = 1
    """
    result = execute_query(query, (user_id, permission_code), fetch_type='one')
    if result.count > 0:
        return True
    from app.models.user import LEGACY_PERMISSION_MAP
    mapped = LEGACY_PERMISSION_MAP.get(permission_code)
    if mapped:
        result2 = execute_query(query, (user_id, mapped), fetch_type='one')
        return result2.count > 0
    return False
```

- [ ] **步骤 4：验证应用启动**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app.models.user import User, LEGACY_PERMISSION_MAP; print(f'映射表条目数: {len(LEGACY_PERMISSION_MAP)}'); u = User(); print(f'has_permission 测试: {u.has_permission(\"merchant_manage\")}')"`

- [ ] **步骤 5：Commit**

```bash
git add app/models/permission.py app/models/user.py app/services/auth_service.py
git commit -m "feat: Permission 模型新增 OperationCode/SortOrder，User.has_permission 增加旧权限兼容映射"
```

---

### 任务 3：路由层权限码替换

**文件：**
- 修改：`app/routes/user.py`
- 修改：`app/routes/merchant.py`
- 修改：`app/routes/contract.py`
- 修改：`app/routes/plot.py`
- 修改：`app/routes/salary.py`
- 修改：`app/routes/customer.py`
- 修改：`app/routes/finance.py`
- 修改：`app/routes/dorm.py`
- 修改：`app/routes/garbage.py`
- 修改：`app/routes/expense.py`
- 修改：`app/routes/dict.py`

替换规则：
- 列表页路由：`xxx_manage` → `xxx_view`
- 新增页/新增 API：`xxx_manage` → `xxx_create`
- 编辑页/编辑 API：`xxx_manage` → `xxx_edit`
- 删除 API：`xxx_manage` → `xxx_delete`
- 导出/特殊 API：根据业务语义选择 `xxx_view` 或 `xxx_edit`

- [ ] **步骤 1：替换 user.py**

`app/routes/user.py` 中：
- 列表页（user_list 等）的 `check_permission('user_manage')` → `check_permission('user_view')`
- 新增用户 API 的 `has_permission('user_manage')` → `has_permission('user_create')`
- 编辑用户 API 的 `has_permission('user_manage')` → `has_permission('user_edit')`
- 删除用户 API 的 `has_permission('user_manage')` → `has_permission('user_delete')`

- [ ] **步骤 2：替换 merchant.py**

`app/routes/merchant.py` 中：
- 列表页 `check_permission('merchant_manage')` → `check_permission('merchant_view')`
- 新增页 `check_permission('merchant_manage')` → `check_permission('merchant_create')`
- 编辑页 `check_permission('merchant_manage')` → `check_permission('merchant_edit')`
- 删除 API `check_permission('merchant_manage')` → `check_api_permission('merchant_delete')`

- [ ] **步骤 3：替换 contract.py**

`app/routes/contract.py` 中：
- 列表页 `check_permission('contract_manage')` → `check_permission('contract_view')`
- 新增 API `check_api_permission('contract_manage')` → `check_api_permission('contract_create')`
- 编辑 API `check_api_permission('contract_manage')` → `check_api_permission('contract_edit')`
- 删除 API `check_api_permission('contract_manage')` → `check_api_permission('contract_delete')`
- 详情/导出等 API `check_api_permission('contract_manage')` → `check_api_permission('contract_view')`

- [ ] **步骤 4：替换 plot.py**

同 merchant.py 模式：列表→view，新增→create，编辑→edit，删除→delete。

- [ ] **步骤 5：替换 salary.py**

- 列表页 `check_permission('salary_manage')` → `check_permission('salary_view')`
- 新增/编辑/删除 API 按操作类型分别替换

- [ ] **步骤 6：替换 customer.py**

- 列表页 `check_permission('customer_manage')` → `check_permission('customer_view')`
- API 路由按操作类型替换

- [ ] **步骤 7：替换 finance.py**

- 列表页 `check_permission('finance_manage')` → `check_permission('finance_view')`
- 新增/编辑 API → `finance_create` / `finance_edit`
- 预收预付路由 `check_permission('prepayment_manage')` → 对应 `prepayment_view/create/edit`
- 押金路由 `check_permission('deposit_manage')` → 对应 `deposit_view/create/edit`

- [ ] **步骤 8：替换 dorm.py**

- 列表页 `check_permission('dorm_manage')` → `check_permission('dorm_view')`
- 新增/编辑/删除路由按操作类型替换

- [ ] **步骤 9：替换 garbage.py**

同 dorm.py 模式。

- [ ] **步骤 10：替换 expense.py**

同 dorm.py 模式。

- [ ] **步骤 11：替换 dict.py**

- 将 dict.py 中自带的 `check_permission` 装饰器改为从 user.py 导入
- 替换所有 `check_api_permission('dict_manage')` → 按操作类型替换为 `dict_view/create/edit/delete`

- [ ] **步骤 12：验证应用启动**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app import create_app; app = create_app(); print('应用启动成功')"`

- [ ] **步骤 13：Commit**

```bash
git add app/routes/
git commit -m "feat: 路由层权限码从模块级替换为 CRUD 四级"
```

---

### 任务 4：模板层权限码替换

**文件：**
- 修改：`templates/admin_base.html`
- 修改：`templates/user/list.html`
- 修改：`templates/dict/list.html`

- [ ] **步骤 1：替换 admin_base.html 侧边栏**

将所有侧边栏菜单可见性权限从 `xxx_manage` 替换为 `xxx_view`：
- `has_permission('plot_manage')` → `has_permission('plot_view')`
- `has_permission('merchant_manage')` → `has_permission('merchant_view')`
- `has_permission('contract_manage')` → `has_permission('contract_view')`
- `has_permission('utility_manage')` → `has_permission('utility_view')`
- `has_permission('scale_manage')` → `has_permission('scale_view')`
- `has_permission('expense_manage')` → `has_permission('expense_view')`
- `has_permission('garbage_manage')` → `has_permission('garbage_view')`
- `has_permission('dorm_manage')` → `has_permission('dorm_view')`
- `has_permission('finance_manage')` → `has_permission('finance_view')`
- `has_permission('salary_manage')` → `has_permission('salary_view')`
- `has_permission('prepayment_manage')` → `has_permission('prepayment_view')`
- `has_permission('deposit_manage')` → `has_permission('deposit_view')`
- `has_permission('user_manage')` → `has_permission('user_view')`
- `has_permission('dict_manage')` → `has_permission('dict_view')`

- [ ] **步骤 2：替换 user/list.html 操作按钮**

- "添加用户"按钮：`has_permission('user_manage')` → `has_permission('user_create')`
- "编辑"按钮：`has_permission('user_manage')` → `has_permission('user_edit')`

- [ ] **步骤 3：替换 dict/list.html 操作按钮**

- "新增"按钮：`has_permission('dict_manage')` → `has_permission('dict_create')`
- "编辑"操作：`has_permission('dict_manage')` → `has_permission('dict_edit')`
- "删除"操作：`has_permission('dict_manage')` → `has_permission('dict_delete')`

- [ ] **步骤 4：Commit**

```bash
git add templates/admin_base.html templates/user/list.html templates/dict/list.html
git commit -m "feat: 模板层权限码从模块级替换为 CRUD 四级"
```

---

### 任务 5：角色管理路由和服务

**文件：**
- 创建：`app/services/role_service.py`
- 创建：`app/routes/role.py`
- 修改：`app/routes/__init__.py`

- [ ] **步骤 1：创建 role_service.py**

```python
from app.db_connection import execute_query, execute_update
from app.models.role import Role
from app.models.permission import Permission


class RoleService:

    @staticmethod
    def get_all_roles():
        query = """
            SELECT RoleID, RoleName, RoleCode, Description, IsActive, CreateTime, UpdateTime
            FROM Role ORDER BY RoleID
        """
        results = execute_query(query, fetch_type='all')
        roles = []
        if results:
            for row in results:
                roles.append(Role(
                    role_id=row.RoleID,
                    role_name=row.RoleName,
                    role_code=row.RoleCode,
                    description=row.Description,
                    is_active=row.IsActive,
                    create_time=row.CreateTime,
                    update_time=row.UpdateTime
                ))
        return roles

    @staticmethod
    def get_role_by_id(role_id):
        query = """
            SELECT RoleID, RoleName, RoleCode, Description, IsActive, CreateTime, UpdateTime
            FROM Role WHERE RoleID = ?
        """
        row = execute_query(query, (role_id,), fetch_type='one')
        if row:
            return Role(
                role_id=row.RoleID,
                role_name=row.RoleName,
                role_code=row.RoleCode,
                description=row.Description,
                is_active=row.IsActive,
                create_time=row.CreateTime,
                update_time=row.UpdateTime
            )
        return None

    @staticmethod
    def get_all_permissions_grouped():
        query = """
            SELECT PermissionID, PermissionName, PermissionCode, Description,
                   ModuleName, OperationCode, SortOrder, IsActive
            FROM Permission
            WHERE IsActive = 1 AND OperationCode IN ('view','create','edit','delete')
            ORDER BY SortOrder
        """
        results = execute_query(query, fetch_type='all')
        permissions = []
        if results:
            for row in results:
                permissions.append(Permission(
                    permission_id=row.PermissionID,
                    permission_name=row.PermissionName,
                    permission_code=row.PermissionCode,
                    description=row.Description,
                    module_name=row.ModuleName,
                    operation_code=getattr(row, 'OperationCode', None),
                    sort_order=getattr(row, 'SortOrder', 0),
                    is_active=row.IsActive
                ))
        grouped = {}
        for p in permissions:
            if p.module_name not in grouped:
                grouped[p.module_name] = []
            grouped[p.module_name].append(p)
        return grouped

    @staticmethod
    def get_role_permissions(role_id):
        query = """
            SELECT p.PermissionID FROM Permission p
            INNER JOIN RolePermission rp ON p.PermissionID = rp.PermissionID
            WHERE rp.RoleID = ? AND p.IsActive = 1
        """
        results = execute_query(query, (role_id,), fetch_type='all')
        if results:
            return [row.PermissionID for row in results]
        return []

    @staticmethod
    def update_role_permissions(role_id, permission_ids):
        execute_update("DELETE FROM RolePermission WHERE RoleID = ?", (role_id,))
        for pid in permission_ids:
            execute_update(
                "INSERT INTO RolePermission (RoleID, PermissionID, CreateTime) VALUES (?, ?, GETDATE())",
                (role_id, pid)
            )

    @staticmethod
    def create_role(role_name, role_code, description):
        execute_update(
            "INSERT INTO Role (RoleName, RoleCode, Description, IsActive) VALUES (?, ?, ?, 1)",
            (role_name, role_code, description)
        )

    @staticmethod
    def update_role(role_id, role_name, description, is_active):
        execute_update(
            "UPDATE Role SET RoleName=?, Description=?, IsActive=?, UpdateTime=GETDATE() WHERE RoleID=?",
            (role_name, description, is_active, role_id)
        )

    @staticmethod
    def delete_role(role_id):
        execute_update("DELETE FROM RolePermission WHERE RoleID = ?", (role_id,))
        execute_update("DELETE FROM UserRole WHERE RoleID = ?", (role_id,))
        execute_update("DELETE FROM Role WHERE RoleID = ?", (role_id,))
```

- [ ] **步骤 2：创建 role.py 路由**

```python
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.routes.user import check_permission, check_api_permission
from app.services.role_service import RoleService

role_bp = Blueprint('role', __name__, url_prefix='/role')


@role_bp.route('/list')
@login_required
@check_permission('role_view')
def role_list():
    roles = RoleService.get_all_roles()
    return render_template('role/list.html', roles=roles)


@role_bp.route('/edit/<int:role_id>', methods=['GET'])
@login_required
@check_permission('role_edit')
def role_edit(role_id):
    role = RoleService.get_role_by_id(role_id)
    if not role:
        flash('角色不存在', 'danger')
        return redirect(url_for('role.role_list'))
    permissions_grouped = RoleService.get_all_permissions_grouped()
    role_permission_ids = RoleService.get_role_permissions(role_id)
    return render_template('role/edit.html',
                           role=role,
                           permissions_grouped=permissions_grouped,
                           role_permission_ids=role_permission_ids)


@role_bp.route('/api/permissions', methods=['GET'])
@login_required
@check_api_permission('role_view')
def api_permissions():
    grouped = RoleService.get_all_permissions_grouped()
    result = {}
    for module_name, perms in grouped.items():
        result[module_name] = [
            {'id': p.permission_id, 'code': p.permission_code,
             'name': p.permission_name, 'operation': p.operation_code}
            for p in perms
        ]
    return jsonify({'success': True, 'data': result})


@role_bp.route('/api/update_permissions/<int:role_id>', methods=['POST'])
@login_required
@check_api_permission('role_edit')
def api_update_permissions(role_id):
    data = request.get_json()
    permission_ids = data.get('permission_ids', [])
    RoleService.update_role_permissions(role_id, permission_ids)
    return jsonify({'success': True, 'message': '权限更新成功'})


@role_bp.route('/api/create', methods=['POST'])
@login_required
@check_api_permission('role_create')
def api_create():
    data = request.get_json()
    role_name = data.get('role_name', '').strip()
    role_code = data.get('role_code', '').strip()
    description = data.get('description', '').strip()
    if not role_name or not role_code:
        return jsonify({'success': False, 'message': '角色名称和编码不能为空'}), 400
    RoleService.create_role(role_name, role_code, description)
    return jsonify({'success': True, 'message': '角色创建成功'})


@role_bp.route('/api/update/<int:role_id>', methods=['POST'])
@login_required
@check_api_permission('role_edit')
def api_update(role_id):
    data = request.get_json()
    role_name = data.get('role_name', '').strip()
    description = data.get('description', '').strip()
    is_active = data.get('is_active', True)
    if not role_name:
        return jsonify({'success': False, 'message': '角色名称不能为空'}), 400
    RoleService.update_role(role_id, role_name, description, is_active)
    return jsonify({'success': True, 'message': '角色更新成功'})


@role_bp.route('/api/delete/<int:role_id>', methods=['POST'])
@login_required
@check_api_permission('role_delete')
def api_delete(role_id):
    if role_id <= 3:
        return jsonify({'success': False, 'message': '系统内置角色不可删除'}), 400
    RoleService.delete_role(role_id)
    return jsonify({'success': True, 'message': '角色删除成功'})
```

- [ ] **步骤 3：注册蓝图**

在 `app/routes/__init__.py` 中注册 role 蓝图：

```python
from app.routes.role import role_bp
app.register_blueprint(role_bp)
```

- [ ] **步骤 4：验证蓝图注册**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python -c "from app import create_app; app = create_app(); print([r.rule for r in app.url_map.iter_rules() if '/role' in r.rule])"`

- [ ] **步骤 5：Commit**

```bash
git add app/services/role_service.py app/routes/role.py app/routes/__init__.py
git commit -m "feat: 新增角色管理路由和服务（CRUD + 树形权限分配 API）"
```

---

### 任务 6：角色管理前端页面

**文件：**
- 创建：`templates/role/list.html`
- 创建：`templates/role/edit.html`

- [ ] **步骤 1：创建角色列表页 `templates/role/list.html`**

继承 admin_base.html，展示角色列表，支持新增/编辑/删除操作。使用 Ajax 提交，CSRF 令牌，列表删除后异步刷新。

- [ ] **步骤 2：创建角色编辑页 `templates/role/edit.html`**

继承 admin_base.html，展示树形权限分配界面：
- 按 ModuleName 分组（市场管理/财务管理/系统管理）
- 每组内按模块排列，每模块一行 4 个 checkbox（查看/新增/编辑/删除）
- 勾选 create/edit/delete 自动勾选 view
- 取消 view 自动取消同模块其他操作
- 列级快捷操作：全选查看/全选新增/全选编辑/全选删除
- Ajax 提交权限变更

- [ ] **步骤 3：在 admin_base.html 侧边栏添加角色管理菜单项**

在系统管理分区中，字典管理之后添加：

```html
{% if current_user.has_permission('role_view') %}
<a class="sidebar-item {% if request.endpoint and 'role' in request.endpoint %}active{% endif %}" href="{{ url_for('role.role_list') }}">
    <i class="fa fa-users-cog"></i>
    <span class="sidebar-item-text">角色管理</span>
</a>
{% endif %}
```

- [ ] **步骤 4：验证页面渲染**

启动应用，以 admin 用户登录，访问 `/role/list` 和 `/role/edit/1`，确认页面正常显示。

- [ ] **步骤 5：Commit**

```bash
git add templates/role/ templates/admin_base.html
git commit -m "feat: 新增角色管理前端页面（列表 + 树形权限分配编辑）"
```

---

### 任务 7：端到端验证

- [ ] **步骤 1：启动应用**

运行：`cd d:\BaiduSyncdisk\HF_metalmarket && python run.py`

- [ ] **步骤 2：验证旧权限兼容**

以 admin 用户登录，访问各模块页面，确认旧权限码（通过 LEGACY_PERMISSION_MAP）仍可正常工作。

- [ ] **步骤 3：验证新权限生效**

在角色管理页面，修改 staff 角色权限（如取消 merchant_delete），以 staff 用户登录，确认删除按钮不可见、删除 API 返回 403。

- [ ] **步骤 4：验证侧边栏**

确认侧边栏菜单按 `xxx_view` 权限正确显示/隐藏。

- [ ] **步骤 5：Final Commit**

```bash
git add -A
git commit -m "feat: CRUD 四级权限精细化改造完成"
```
