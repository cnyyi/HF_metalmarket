import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from config import Config
from utils.database import execute_query, execute_update

app = Flask(__name__)
app.config.from_object(Config)

PERMISSIONS_DATA = [
    ('plot_view', '地块查看', '市场管理', 'view', 101),
    ('plot_create', '地块新增', '市场管理', 'create', 102),
    ('plot_edit', '地块编辑', '市场管理', 'edit', 103),
    ('plot_delete', '地块删除', '市场管理', 'delete', 104),
    ('merchant_view', '商户查看', '市场管理', 'view', 201),
    ('merchant_create', '商户新增', '市场管理', 'create', 202),
    ('merchant_edit', '商户编辑', '市场管理', 'edit', 203),
    ('merchant_delete', '商户删除', '市场管理', 'delete', 204),
    ('contract_view', '合同查看', '市场管理', 'view', 301),
    ('contract_create', '合同新增', '市场管理', 'create', 302),
    ('contract_edit', '合同编辑', '市场管理', 'edit', 303),
    ('contract_delete', '合同删除', '市场管理', 'delete', 304),
    ('utility_view', '水电查看', '市场管理', 'view', 401),
    ('utility_create', '水电新增', '市场管理', 'create', 402),
    ('utility_edit', '水电编辑', '市场管理', 'edit', 403),
    ('utility_delete', '水电删除', '市场管理', 'delete', 404),
    ('utility_reading', '水电抄表', '市场管理', 'reading', 405),
    ('utility_pay', '水电缴费', '市场管理', 'pay', 406),
    ('scale_view', '磅秤查看', '市场管理', 'view', 501),
    ('scale_create', '磅秤新增', '市场管理', 'create', 502),
    ('scale_edit', '磅秤编辑', '市场管理', 'edit', 503),
    ('scale_delete', '磅秤删除', '市场管理', 'delete', 504),
    ('expense_view', '费用单查看', '市场管理', 'view', 601),
    ('expense_create', '费用单新增', '市场管理', 'create', 602),
    ('expense_edit', '费用单编辑', '市场管理', 'edit', 603),
    ('expense_delete', '费用单删除', '市场管理', 'delete', 604),
    ('garbage_view', '垃圾清运查看', '市场管理', 'view', 701),
    ('garbage_create', '垃圾清运新增', '市场管理', 'create', 702),
    ('garbage_edit', '垃圾清运编辑', '市场管理', 'edit', 703),
    ('garbage_delete', '垃圾清运删除', '市场管理', 'delete', 704),
    ('dorm_view', '宿舍查看', '市场管理', 'view', 801),
    ('dorm_create', '宿舍新增', '市场管理', 'create', 802),
    ('dorm_edit', '宿舍编辑', '市场管理', 'edit', 803),
    ('dorm_delete', '宿舍删除', '市场管理', 'delete', 804),
    ('finance_view', '财务查看', '财务管理', 'view', 1001),
    ('finance_create', '财务新增', '财务管理', 'create', 1002),
    ('finance_edit', '财务编辑', '财务管理', 'edit', 1003),
    ('finance_delete', '财务删除', '财务管理', 'delete', 1004),
    ('account_view', '账户查看', '财务管理', 'view', 1101),
    ('account_create', '账户新增', '财务管理', 'create', 1102),
    ('account_edit', '账户编辑', '财务管理', 'edit', 1103),
    ('account_delete', '账户删除', '财务管理', 'delete', 1104),
    ('prepayment_view', '预收预付查看', '财务管理', 'view', 1201),
    ('prepayment_create', '预收预付新增', '财务管理', 'create', 1202),
    ('prepayment_edit', '预收预付编辑', '财务管理', 'edit', 1203),
    ('prepayment_delete', '预收预付删除', '财务管理', 'delete', 1204),
    ('deposit_view', '押金查看', '财务管理', 'view', 1301),
    ('deposit_create', '押金新增', '财务管理', 'create', 1302),
    ('deposit_edit', '押金编辑', '财务管理', 'edit', 1303),
    ('deposit_delete', '押金删除', '财务管理', 'delete', 1304),
    ('customer_view', '往来客户查看', '财务管理', 'view', 1401),
    ('customer_create', '往来客户新增', '财务管理', 'create', 1402),
    ('customer_edit', '往来客户编辑', '财务管理', 'edit', 1403),
    ('customer_delete', '往来客户删除', '财务管理', 'delete', 1404),
    ('salary_view', '工资查看', '财务管理', 'view', 1501),
    ('salary_create', '工资新增', '财务管理', 'create', 1502),
    ('salary_edit', '工资编辑', '财务管理', 'edit', 1503),
    ('salary_delete', '工资删除', '财务管理', 'delete', 1504),
    ('user_view', '用户查看', '系统管理', 'view', 2001),
    ('user_create', '用户新增', '系统管理', 'create', 2002),
    ('user_edit', '用户编辑', '系统管理', 'edit', 2003),
    ('user_delete', '用户删除', '系统管理', 'delete', 2004),
    ('role_view', '角色查看', '系统管理', 'view', 2101),
    ('role_create', '角色新增', '系统管理', 'create', 2102),
    ('role_edit', '角色编辑', '系统管理', 'edit', 2103),
    ('role_delete', '角色删除', '系统管理', 'delete', 2104),
    ('permission_view', '权限查看', '系统管理', 'view', 2201),
    ('permission_create', '权限新增', '系统管理', 'create', 2202),
    ('permission_edit', '权限编辑', '系统管理', 'edit', 2203),
    ('permission_delete', '权限删除', '系统管理', 'delete', 2204),
    ('dict_view', '字典查看', '系统管理', 'view', 2301),
    ('dict_create', '字典新增', '系统管理', 'create', 2302),
    ('dict_edit', '字典编辑', '系统管理', 'edit', 2303),
    ('dict_delete', '字典删除', '系统管理', 'delete', 2304),
    ('garbage_fee_view', '垃圾费查看', '市场管理', 'view', 901),
    ('garbage_fee_create', '垃圾费新增', '市场管理', 'create', 902),
    ('garbage_fee_edit', '垃圾费编辑', '市场管理', 'edit', 903),
    ('garbage_fee_delete', '垃圾费删除', '市场管理', 'delete', 904),
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
    'garbage_fee_manage': ['garbage_fee_view', 'garbage_fee_create', 'garbage_fee_edit', 'garbage_fee_delete'],
}


def step1_add_columns():
    print('步骤1: 检查并添加 OperationCode/SortOrder 字段...')
    try:
        execute_update("ALTER TABLE Permission ADD OperationCode NVARCHAR(20) NULL")
        print('  已添加 OperationCode 字段')
    except Exception as e:
        err = str(e).lower()
        if 'already exists' in err or '列名已存在' in err or 'must be unique' in err:
            print('  OperationCode 字段已存在，跳过')
        else:
            raise
    try:
        execute_update("ALTER TABLE Permission ADD SortOrder INT NULL DEFAULT 0")
        print('  已添加 SortOrder 字段')
    except Exception as e:
        err = str(e).lower()
        if 'already exists' in err or '列名已存在' in err or 'must be unique' in err:
            print('  SortOrder 字段已存在，跳过')
        else:
            raise


def step2_mark_old_permissions():
    print('步骤2: 标记旧权限 OperationCode = manage...')
    execute_update(
        "UPDATE Permission SET OperationCode = N'manage' WHERE OperationCode IS NULL AND (PermissionCode LIKE N'%_manage' OR PermissionCode IN (N'direct_entry', N'utility_reading'))"
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
            execute_update(
                "UPDATE Permission SET PermissionName = ?, ModuleName = ?, OperationCode = ?, SortOrder = ? WHERE PermissionCode = ?",
                (name, module, op_code, sort_order, code)
            )
        else:
            conflict = execute_query(
                "SELECT PermissionID FROM Permission WHERE PermissionName = ?",
                (name,), fetch_type='one'
            )
            if conflict:
                execute_update(
                    "UPDATE Permission SET PermissionCode = ?, ModuleName = ?, OperationCode = ?, SortOrder = ? WHERE PermissionName = ?",
                    (code, module, op_code, sort_order, name)
                )
            else:
                execute_update(
                    "INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, IsActive, OperationCode, SortOrder, CreateTime) VALUES (?, ?, N'', ?, 1, ?, ?, GETDATE())",
                    (name, code, module, op_code, sort_order)
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
                    execute_update(
                        "INSERT INTO RolePermission (RoleID, PermissionID, CreateTime) VALUES (?, ?, GETDATE())",
                        (role_id, new_perm.PermissionID)
                    )
        print(f'  {old_code} → {new_codes}: 已迁移 {len(role_ids)} 个角色')
    print('  角色赋权迁移完成')


def step4b_assign_new_module_permissions():
    print('步骤4b: 为 admin 角色分配新模块权限（role/permission）...')
    admin_role = execute_query(
        "SELECT RoleID FROM Role WHERE RoleCode = N'admin'",
        fetch_type='one'
    )
    if not admin_role:
        print('  admin 角色不存在，跳过')
        return
    admin_role_id = admin_role.RoleID
    new_module_perms = [
        'role_view', 'role_create', 'role_edit', 'role_delete',
        'permission_view', 'permission_create', 'permission_edit', 'permission_delete'
    ]
    added = 0
    for code in new_module_perms:
        perm = execute_query(
            "SELECT PermissionID FROM Permission WHERE PermissionCode = ? AND IsActive = 1",
            (code,), fetch_type='one'
        )
        if not perm:
            continue
        exists = execute_query(
            "SELECT RolePermissionID FROM RolePermission WHERE RoleID = ? AND PermissionID = ?",
            (admin_role_id, perm.PermissionID), fetch_type='one'
        )
        if not exists:
            execute_update(
                "INSERT INTO RolePermission (RoleID, PermissionID, CreateTime) VALUES (?, ?, GETDATE())",
                (admin_role_id, perm.PermissionID)
            )
            added += 1
    print(f'  已为 admin 角色添加 {added} 个新模块权限')


def step5_deactivate_old_permissions():
    print('步骤5: 停用旧权限（IsActive = 0）...')
    old_codes = list(MANAGE_TO_CRUD.keys())
    placeholders = ','.join(['?'] * len(old_codes))
    execute_update(
        f"UPDATE Permission SET IsActive = 0 WHERE PermissionCode IN ({placeholders})",
        tuple(old_codes)
    )
    print(f'  已停用 {len(old_codes)} 个旧权限')


def main():
    print('=== CRUD 权限迁移开始 ===')
    step1_add_columns()
    step2_mark_old_permissions()
    step3_insert_new_permissions()
    step4_migrate_role_permissions()
    step4b_assign_new_module_permissions()
    step5_deactivate_old_permissions()
    print('=== CRUD 权限迁移完成 ===')


if __name__ == '__main__':
    with app.app_context():
        main()
