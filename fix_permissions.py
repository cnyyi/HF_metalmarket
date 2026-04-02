# 修复权限问题 - 添加 user_manage 权限
from app import create_app
from config import DevelopmentConfig
from utils.database import execute_query, execute_update
import datetime

app = create_app(DevelopmentConfig)

with app.app_context():
    print("=== 修复权限问题 ===\n")
    
    # 1. 检查 user_manage 权限是否存在
    print("1. 检查 user_manage 权限:")
    user_manage_perm = execute_query("""
        SELECT * FROM Permission WHERE PermissionCode = 'user_manage'
    """, fetch_type='one')
    
    if not user_manage_perm:
        print("  user_manage 权限不存在，正在创建...")
        execute_update("""
            INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, IsActive, CreateTime)
            VALUES (N'用户管理', 'user_manage', N'用户管理权限', N'系统管理', 1, ?)
        """, (datetime.datetime.now(),))
        print("  user_manage 权限创建成功!")
        
        # 重新获取
        user_manage_perm = execute_query("""
            SELECT * FROM Permission WHERE PermissionCode = 'user_manage'
        """, fetch_type='one')
    else:
        print(f"  user_manage 权限已存在，ID: {user_manage_perm.PermissionID}")
    
    print()
    
    # 2. 为 admin 角色分配 user_manage 权限
    print("2. 为 admin 角色分配权限:")
    admin_role = execute_query("""
        SELECT * FROM Role WHERE RoleCode = 'admin'
    """, fetch_type='one')
    
    if admin_role and user_manage_perm:
        # 检查是否已分配
        existing = execute_query("""
            SELECT * FROM RolePermission 
            WHERE RoleID = ? AND PermissionID = ?
        """, (admin_role.RoleID, user_manage_perm.PermissionID), fetch_type='one')
        
        if not existing:
            execute_update("""
                INSERT INTO RolePermission (RoleID, PermissionID, CreateTime)
                VALUES (?, ?, ?)
            """, (admin_role.RoleID, user_manage_perm.PermissionID, datetime.datetime.now()))
            print(f"  已为 admin 角色分配 user_manage 权限")
        else:
            print("  admin 角色已拥有 user_manage 权限")
    else:
        if not admin_role:
            print("  admin 角色不存在!")
        if not user_manage_perm:
            print("  user_manage 权限不存在!")
    
    print()
    
    # 3. 添加其他管理权限
    print("3. 添加其他管理权限:")
    manage_permissions = [
        ('角色管理', 'role_manage', '角色管理权限', '系统管理'),
        ('权限管理', 'permission_manage', '权限管理权限', '系统管理'),
        ('商户管理', 'merchant_manage', '商户管理权限', '商户管理'),
        ('地块管理', 'plot_manage', '地块管理权限', '地块管理'),
        ('合同管理', 'contract_manage', '合同管理权限', '合同管理'),
        ('水电管理', 'utility_manage', '水电管理权限', '水电管理'),
        ('财务管理', 'finance_manage', '财务管理权限', '财务管理'),
        ('磅秤管理', 'scale_manage', '磅秤管理权限', '磅秤管理'),
    ]
    
    for perm_name, perm_code, desc, module in manage_permissions:
        perm = execute_query("""
            SELECT * FROM Permission WHERE PermissionCode = ?
        """, (perm_code,), fetch_type='one')
        
        if not perm:
            execute_update("""
                INSERT INTO Permission (PermissionName, PermissionCode, Description, ModuleName, IsActive, CreateTime)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (perm_name, perm_code, desc, module, datetime.datetime.now()))
            print(f"  创建权限: {perm_name} ({perm_code})")
            
            # 为 admin 角色分配权限
            new_perm = execute_query("""
                SELECT * FROM Permission WHERE PermissionCode = ?
            """, (perm_code,), fetch_type='one')
            
            if admin_role and new_perm:
                execute_update("""
                    INSERT INTO RolePermission (RoleID, PermissionID, CreateTime)
                    VALUES (?, ?, ?)
                """, (admin_role.RoleID, new_perm.PermissionID, datetime.datetime.now()))
        else:
            # 检查 admin 角色是否有此权限
            existing = execute_query("""
                SELECT * FROM RolePermission 
                WHERE RoleID = ? AND PermissionID = ?
            """, (admin_role.RoleID, perm.PermissionID), fetch_type='one')
            
            if not existing:
                execute_update("""
                    INSERT INTO RolePermission (RoleID, PermissionID, CreateTime)
                    VALUES (?, ?, ?)
                """, (admin_role.RoleID, perm.PermissionID, datetime.datetime.now()))
                print(f"  为 admin 角色分配权限: {perm_name}")
    
    print()
    
    # 4. 验证 admin 用户的权限
    print("4. 验证 admin 用户的权限:")
    admin_user = execute_query("""
        SELECT * FROM [User] WHERE Username = 'admin'
    """, fetch_type='one')
    
    if admin_user:
        user_perms = execute_query("""
            SELECT DISTINCT p.PermissionCode, p.PermissionName
            FROM Permission p
            INNER JOIN RolePermission rp ON p.PermissionID = rp.PermissionID
            INNER JOIN UserRole ur ON rp.RoleID = ur.RoleID
            WHERE ur.UserID = ?
            ORDER BY p.PermissionCode
        """, (admin_user.UserID,), fetch_type='all')
        
        print(f"  admin 用户拥有的权限:")
        for p in user_perms:
            print(f"    - {p.PermissionCode}: {p.PermissionName}")
    
    print()
    print("=== 权限修复完成 ===")
