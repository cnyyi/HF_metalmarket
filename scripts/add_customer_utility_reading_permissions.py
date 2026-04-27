import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from app import create_app
from utils.database import execute_query, execute_update
import datetime

app = create_app()

NEW_PERMISSIONS = [
    ('客户管理', 'customer_manage', '管理客户信息', '客户管理'),
    ('水电抄表', 'utility_reading', '水电表抄表及查询', '水电管理'),
]

ROLES_TO_ASSIGN = ['admin', 'staff']

with app.app_context():
    for perm_name, perm_code, desc, module in NEW_PERMISSIONS:
        existing = execute_query(
            "SELECT PermissionID FROM Permission WHERE PermissionCode = ?",
            (perm_code,), fetch_type='one'
        )
        if existing:
            print(f'{perm_code} already exists, ID: {existing.PermissionID}')
        else:
            now = datetime.datetime.now()
            execute_update("""
                INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, IsActive, CreateTime)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (perm_name, perm_code, desc, module, now))
            print(f'{perm_code} added successfully')

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
            if role:
                existing_rp = execute_query(
                    "SELECT * FROM RolePermission WHERE RoleID = ? AND PermissionID = ?",
                    (role.RoleID, perm_id), fetch_type='one'
                )
                if not existing_rp:
                    execute_update(
                        "INSERT INTO RolePermission (RoleID, PermissionID, CreateTime) VALUES (?, ?, ?)",
                        (role.RoleID, perm_id, datetime.datetime.now())
                    )
                    print(f'Assigned {perm_code} to {role_code} role')
                else:
                    print(f'{role_code} already has {perm_code}')

    print('Done!')
