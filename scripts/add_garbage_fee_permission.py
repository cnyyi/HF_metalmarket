import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from config import Config
from utils.database import execute_query, execute_update
import datetime

app = Flask(__name__)
app.config.from_object(Config)

PERMISSIONS = [
    ('garbage_fee_view', '垃圾费查看', '市场管理', 'view', 901),
    ('garbage_fee_create', '垃圾费新增', '市场管理', 'create', 902),
    ('garbage_fee_edit', '垃圾费编辑', '市场管理', 'edit', 903),
    ('garbage_fee_delete', '垃圾费删除', '市场管理', 'delete', 904),
]

MANAGE_CODE = 'garbage_fee_manage'
MANAGE_NAME = '垃圾费管理'

with app.app_context():
    for code, name, module, action, sort_order in PERMISSIONS:
        existing = execute_query("SELECT PermissionID FROM Permission WHERE PermissionCode = N'" + code + "'", fetch_type='one')
        if existing:
            print(f'{code} already exists, ID: {existing.PermissionID}')
        else:
            execute_update("""INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, Action, SortOrder, IsActive, CreateTime)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)""", (name, code, name, module, action, sort_order, datetime.datetime.now()))
            print(f'{code} added successfully')

    existing_manage = execute_query("SELECT PermissionID FROM Permission WHERE PermissionCode = N'" + MANAGE_CODE + "'", fetch_type='one')
    if not existing_manage:
        execute_update("""INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, Action, SortOrder, IsActive, CreateTime)
            VALUES (?, ?, ?, ?, 'manage', 900, 1, ?)""", (MANAGE_NAME, MANAGE_CODE, MANAGE_NAME, '市场管理', datetime.datetime.now()))
        print(f'{MANAGE_CODE} added successfully')
    else:
        print(f'{MANAGE_CODE} already exists')

    for role_code in ['admin', 'staff']:
        role = execute_query("SELECT RoleID FROM Role WHERE RoleCode = N'" + role_code + "'", fetch_type='one')
        if not role:
            print(f'Role {role_code} not found, skipping')
            continue

        for code, name, module, action, sort_order in PERMISSIONS:
            perm = execute_query("SELECT PermissionID FROM Permission WHERE PermissionCode = N'" + code + "'", fetch_type='one')
            if not perm:
                continue
            existing_rp = execute_query("SELECT * FROM RolePermission WHERE RoleID = ? AND PermissionID = ?", (role.RoleID, perm.PermissionID), fetch_type='one')
            if not existing_rp:
                execute_update("INSERT INTO RolePermission (RoleID, PermissionID, CreateTime) VALUES (?, ?, ?)", (role.RoleID, perm.PermissionID, datetime.datetime.now()))
                print(f'Assigned {code} to {role_code}')

        manage_perm = execute_query("SELECT PermissionID FROM Permission WHERE PermissionCode = N'" + MANAGE_CODE + "'", fetch_type='one')
        if manage_perm:
            existing_rp = execute_query("SELECT * FROM RolePermission WHERE RoleID = ? AND PermissionID = ?", (role.RoleID, manage_perm.PermissionID), fetch_type='one')
            if not existing_rp:
                execute_update("INSERT INTO RolePermission (RoleID, PermissionID, CreateTime) VALUES (?, ?, ?)", (role.RoleID, manage_perm.PermissionID, datetime.datetime.now()))
                print(f'Assigned {MANAGE_CODE} to {role_code}')

    print('Done!')
