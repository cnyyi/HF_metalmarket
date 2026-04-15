import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from app import create_app
from utils.database import execute_query, execute_update
import datetime

app = create_app()

with app.app_context():
    existing = execute_query("SELECT PermissionID FROM Permission WHERE PermissionCode = N'dict_manage'", fetch_type='one')
    if existing:
        print('dict_manage permission already exists, ID:', existing.PermissionID)
    else:
        now = datetime.datetime.now()
        execute_update("""INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, IsActive, CreateTime)
            VALUES (N'字典管理', N'dict_manage', N'管理字典数据', N'系统管理', 1, ?)""", (now,))
        print('dict_manage permission added successfully')

    perm = execute_query("SELECT PermissionID FROM Permission WHERE PermissionCode = N'dict_manage'", fetch_type='one')
    perm_id = perm.PermissionID

    admin_role = execute_query("SELECT RoleID FROM Role WHERE RoleCode = N'admin'", fetch_type='one')
    if admin_role:
        existing_rp = execute_query("SELECT * FROM RolePermission WHERE RoleID = ? AND PermissionID = ?", (admin_role.RoleID, perm_id), fetch_type='one')
        if not existing_rp:
            execute_update("INSERT INTO RolePermission (RoleID, PermissionID, CreateTime) VALUES (?, ?, ?)", (admin_role.RoleID, perm_id, datetime.datetime.now()))
            print('Assigned dict_manage to admin role')
        else:
            print('admin already has dict_manage')

    staff_role = execute_query("SELECT RoleID FROM Role WHERE RoleCode = N'staff'", fetch_type='one')
    if staff_role:
        existing_rp = execute_query("SELECT * FROM RolePermission WHERE RoleID = ? AND PermissionID = ?", (staff_role.RoleID, perm_id), fetch_type='one')
        if not existing_rp:
            execute_update("INSERT INTO RolePermission (RoleID, PermissionID, CreateTime) VALUES (?, ?, ?)", (staff_role.RoleID, perm_id, datetime.datetime.now()))
            print('Assigned dict_manage to staff role')
        else:
            print('staff already has dict_manage')

    print('Done!')
