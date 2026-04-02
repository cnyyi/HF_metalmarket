# 检查和修复权限问题
from app import create_app
from config import DevelopmentConfig
from utils.database import execute_query, execute_update
import datetime

app = create_app(DevelopmentConfig)

with app.app_context():
    print("=== 检查权限配置 ===\n")
    
    # 1. 检查权限表
    print("1. 检查权限表:")
    permissions = execute_query("SELECT * FROM Permission", fetch_type='all')
    if permissions:
        for p in permissions:
            print(f"  - {p.PermissionCode}: {p.PermissionName}")
    else:
        print("  权限表为空，需要创建权限")
    
    print()
    
    # 2. 检查角色表
    print("2. 检查角色表:")
    roles = execute_query("SELECT * FROM Role", fetch_type='all')
    if roles:
        for r in roles:
            print(f"  - {r.RoleCode}: {r.RoleName}")
    else:
        print("  角色表为空，需要创建角色")
    
    print()
    
    # 3. 检查admin用户
    print("3. 检查admin用户:")
    admin = execute_query("SELECT * FROM [User] WHERE Username = 'admin'", fetch_type='one')
    if admin:
        print(f"  用户ID: {admin.UserID}")
        print(f"  用户名: {admin.Username}")
        print(f"  真实姓名: {admin.RealName}")
        print(f"  是否激活: {admin.IsActive}")
        
        # 检查admin的角色
        admin_roles = execute_query("""
            SELECT r.RoleID, r.RoleName, r.RoleCode 
            FROM Role r 
            INNER JOIN UserRole ur ON r.RoleID = ur.RoleID 
            WHERE ur.UserID = ?
        """, (admin.UserID,), fetch_type='all')
        
        if admin_roles:
            print("  角色:")
            for r in admin_roles:
                print(f"    - {r.RoleName} ({r.RoleCode})")
        else:
            print("  用户没有分配角色!")
    else:
        print("  admin用户不存在!")
    
    print()
    
    # 4. 如果权限表为空，创建基础权限
    if not permissions:
        print("4. 创建基础权限...")
        permissions_data = [
            ('用户管理', 'user_manage', '用户管理权限', '系统管理'),
            ('角色管理', 'role_manage', '角色管理权限', '系统管理'),
            ('权限管理', 'permission_manage', '权限管理权限', '系统管理'),
            ('商户管理', 'merchant_manage', '商户管理权限', '商户管理'),
            ('地块管理', 'plot_manage', '地块管理权限', '地块管理'),
            ('合同管理', 'contract_manage', '合同管理权限', '合同管理'),
            ('水电管理', 'utility_manage', '水电管理权限', '水电管理'),
            ('财务管理', 'finance_manage', '财务管理权限', '财务管理'),
            ('磅秤管理', 'scale_manage', '磅秤管理权限', '磅秤管理'),
        ]
        
        for perm_name, perm_code, desc, module in permissions_data:
            execute_update("""
                INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, IsActive, CreateTime)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (perm_name, perm_code, desc, module, datetime.datetime.now()))
        
        print("  基础权限创建完成!")
    else:
        print("4. 权限表已有数据，跳过创建")
    
    print()
    
    # 5. 如果角色表为空，创建基础角色
    if not roles:
        print("5. 创建基础角色...")
        roles_data = [
            ('超级管理员', 'super_admin', '拥有所有权限'),
            ('管理员', 'admin', '拥有大部分管理权限'),
            ('普通用户', 'user', '普通用户权限'),
        ]
        
        for role_name, role_code, desc in roles_data:
            execute_update("""
                INSERT INTO Role (RoleName, RoleCode, Description, IsActive, CreateTime)
                VALUES (?, ?, ?, 1, ?)
            """, (role_name, role_code, desc, datetime.datetime.now()))
        
        print("  基础角色创建完成!")
    else:
        print("5. 角色表已有数据，跳过创建")
    
    print()
    
    # 6. 为超级管理员角色分配所有权限
    print("6. 为超级管理员角色分配权限...")
    super_admin_role = execute_query("SELECT RoleID FROM Role WHERE RoleCode = 'super_admin'", fetch_type='one')
    all_permissions = execute_query("SELECT PermissionID FROM Permission", fetch_type='all')
    
    if super_admin_role and all_permissions:
        # 先删除旧的权限分配
        execute_update("DELETE FROM RolePermission WHERE RoleID = ?", (super_admin_role.RoleID,))
        
        # 分配所有权限
        for perm in all_permissions:
            execute_update("""
                INSERT INTO RolePermission (RoleID, PermissionID, CreateTime)
                VALUES (?, ?, ?)
            """, (super_admin_role.RoleID, perm.PermissionID, datetime.datetime.now()))
        
        print("  超级管理员权限分配完成!")
    else:
        if not super_admin_role:
            print("  超级管理员角色不存在!")
        if not all_permissions:
            print("  没有找到权限!")
    
    print()
    
    # 7. 为admin用户分配超级管理员角色
    print("7. 为admin用户分配超级管理员角色...")
    if admin and super_admin_role:
        # 检查是否已分配
        existing = execute_query("""
            SELECT * FROM UserRole WHERE UserID = ? AND RoleID = ?
        """, (admin.UserID, super_admin_role.RoleID), fetch_type='one')
        
        if not existing:
            execute_update("""
                INSERT INTO UserRole (UserID, RoleID, CreateTime)
                VALUES (?, ?, ?)
            """, (admin.UserID, super_admin_role.RoleID, datetime.datetime.now()))
            print("  角色分配完成!")
        else:
            print("  用户已拥有超级管理员角色")
    
    print()
    print("=== 权限检查和修复完成 ===")
