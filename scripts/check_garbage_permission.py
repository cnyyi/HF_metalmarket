import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from app import create_app
from utils.database import execute_query

app = create_app()

with app.app_context():
    # 检查权限是否存在
    permission = execute_query("SELECT * FROM Permission WHERE PermissionCode = N'garbage_manage'", fetch_type='one')
    print('Garbage manage permission exists:', permission is not None)
    if permission:
        print('Permission ID:', permission.PermissionID)
        print('Permission Name:', permission.PermissionName)
        print('Permission Code:', permission.PermissionCode)
    else:
        print('Garbage manage permission does not exist!')
    
    # 检查admin角色是否有该权限
    if permission:
        admin_role = execute_query("SELECT RoleID FROM Role WHERE RoleCode = N'admin'", fetch_type='one')
        if admin_role:
            role_permission = execute_query(
                "SELECT * FROM RolePermission WHERE RoleID = ? AND PermissionID = ?",
                (admin_role.RoleID, permission.PermissionID),
                fetch_type='one'
            )
            print('Admin role has garbage_manage permission:', role_permission is not None)

print('Done!')
