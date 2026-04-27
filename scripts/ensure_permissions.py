"""确保所有权限码存在于数据库中，并分配给 admin/staff 角色。
运行方式: python scripts/ensure_permissions.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from app import create_app
from utils.database import execute_query, execute_update
import datetime

PERMISSIONS = [
    # (PermissionName, PermissionCode, Description, ModuleName)
    ('合同管理', 'contract_manage', '管理合同信息', '运营管理'),
    ('用户管理', 'user_manage', '管理用户账号', '系统管理'),
    ('商户管理', 'merchant_manage', '管理商户信息及门户', '运营管理'),
    ('客户管理', 'customer_manage', '管理往来客户', '运营管理'),
    ('铺位管理', 'plot_manage', '管理铺位信息', '运营管理'),
    ('财务管理', 'finance_manage', '管理应收应付账款', '财务管理'),
    ('账户管理', 'account_manage', '管理收付款账户', '财务管理'),
    ('直接记账', 'direct_entry', '直接收入/支出记账', '财务管理'),
    ('预收预付管理', 'prepayment_manage', '管理预收/预付款', '财务管理'),
    ('押金管理', 'deposit_manage', '管理押金收退', '财务管理'),
    ('水电管理', 'utility_manage', '管理水电表及抄表', '水电管理'),
    ('水电抄表', 'utility_reading', '水电表抄表及查询', '水电管理'),
    ('磅秤管理', 'scale_manage', '管理磅秤记录', '运营管理'),
    ('字典管理', 'dict_manage', '管理字典数据', '系统管理'),
    ('工资管理', 'salary_manage', '管理工资数据', '人事管理'),
    ('垃圾清运管理', 'garbage_manage', '管理垃圾清运记录', '运营管理'),
    ('宿舍管理', 'dorm_manage', '管理宿舍信息', '运营管理'),
    ('费用管理', 'expense_manage', '管理费用报销', '财务管理'),
]

ROLES_TO_ASSIGN = ['admin', 'staff']

app = create_app()

with app.app_context():
    for perm_name, perm_code, desc, module in PERMISSIONS:
        existing = execute_query(
            "SELECT PermissionID FROM Permission WHERE PermissionCode = ?",
            (perm_code,), fetch_type='one'
        )
        if existing:
            print(f'  [OK] {perm_code} (ID={existing.PermissionID})')
        else:
            now = datetime.datetime.now()
            execute_update("""
                INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, IsActive, CreateTime)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (perm_name, perm_code, desc, module, now))
            print(f'  [NEW] {perm_code} added')

        perm = execute_query(
            "SELECT PermissionID FROM Permission WHERE PermissionCode = ?",
            (perm_code,), fetch_type='one'
        )
        perm_id = perm.PermissionID

        for role_code in ROLES_TO_ASSIGN:
            role = execute_query(
                "SELECT RoleID FROM Role WHERE RoleCode = ?",
                (role_code,), fetch_type='one'
            )
            if not role:
                continue
            existing_rp = execute_query(
                "SELECT * FROM RolePermission WHERE RoleID = ? AND PermissionID = ?",
                (role.RoleID, perm_id), fetch_type='one'
            )
            if not existing_rp:
                execute_update(
                    "INSERT INTO RolePermission (RoleID, PermissionID, CreateTime) VALUES (?, ?, ?)",
                    (role.RoleID, perm_id, datetime.datetime.now())
                )
                print(f'  [ASSIGN] {perm_code} -> {role_code}')

    print('Done!')
