# 用户管理服务
import datetime
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from utils.database import execute_query, execute_update
from app.services.auth_service import AuthService


class UserService:
    """
    用户管理服务类，用于处理用户管理相关的业务逻辑
    """
    
    @staticmethod
    def get_users(page=1, per_page=10, search=None):
        """
        获取用户列表，支持分页和搜索
        
        Args:
            page: 当前页码
            per_page: 每页数量
            search: 搜索关键词
            
        Returns:
            用户列表和总页数
        """
        # 构建查询语句
        base_query = """
            SELECT u.UserID, u.Username, u.RealName, u.Phone, u.Email, u.IsActive, u.CreateTime, u.UpdateTime, u.LastLoginTime, u.WeChatOpenID, u.MerchantID
            FROM [User] u
        """
        
        count_query = """
            SELECT COUNT(*) as count
            FROM [User] u
        """
        
        params = []
        
        # 添加搜索条件
        if search:
            search_condition = " WHERE u.Username LIKE ? OR u.RealName LIKE ? OR u.Phone LIKE ? OR u.Email LIKE ?"
            base_query += search_condition
            count_query += search_condition
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param, search_param])
        
        # 添加分页条件
        offset = (page - 1) * per_page
        base_query += " ORDER BY u.UserID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, per_page])
        
        # 执行查询
        users = []
        results = execute_query(base_query, tuple(params), fetch_type='all')
        
        for result in results:
            user = User(
                user_id=result.UserID,
                username=result.Username,
                real_name=result.RealName,
                phone=result.Phone,
                email=result.Email,
                is_active=result.IsActive,
                create_time=result.CreateTime,
                update_time=result.UpdateTime,
                last_login_time=result.LastLoginTime,
                wechat_openid=result.WeChatOpenID,
                merchant_id=result.MerchantID
            )
            
            # 获取用户角色
            user.roles = UserService.get_user_roles(user.user_id)
            
            users.append(user)
        
        # 获取总页数
        count_result = execute_query(count_query, tuple(params[:-2]) if search else tuple(), fetch_type='one')
        total_count = count_result.count
        total_pages = (total_count + per_page - 1) // per_page
        
        return users, total_count, total_pages
    
    @staticmethod
    def get_user_by_id(user_id):
        """
        根据用户ID获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            User对象，如果用户不存在则返回None
        """
        query = """
            SELECT UserID, Username, Password, RealName, Phone, Email, IsActive, CreateTime, UpdateTime, LastLoginTime, WeChatOpenID, MerchantID
            FROM [User]
            WHERE UserID = ?
        """
        result = execute_query(query, (user_id,), fetch_type='one')
        
        if not result:
            return None
        
        user = User(
            user_id=result.UserID,
            username=result.Username,
            password=result.Password,
            real_name=result.RealName,
            phone=result.Phone,
            email=result.Email,
            is_active=result.IsActive,
            create_time=result.CreateTime,
            update_time=result.UpdateTime,
            last_login_time=result.LastLoginTime,
            wechat_openid=result.WeChatOpenID,
            merchant_id=result.MerchantID
        )
        
        # 获取用户角色
        user.roles = UserService.get_user_roles(user.user_id)
        
        # 获取用户权限
        user.permissions = UserService.get_user_permissions(user.user_id)
        
        return user
    
    @staticmethod
    def get_user_by_username(username):
        """
        根据用户名获取用户信息
        
        Args:
            username: 用户名
            
        Returns:
            User对象，如果用户不存在则返回None
        """
        query = """
            SELECT UserID, Username, Password, RealName, Phone, Email, IsActive, CreateTime, UpdateTime, LastLoginTime, WeChatOpenID, MerchantID
            FROM [User]
            WHERE Username = ?
        """
        result = execute_query(query, (username,), fetch_type='one')
        
        if not result:
            return None
        
        user = User(
            user_id=result.UserID,
            username=result.Username,
            password=result.Password,
            real_name=result.RealName,
            phone=result.Phone,
            email=result.Email,
            is_active=result.IsActive,
            create_time=result.CreateTime,
            update_time=result.UpdateTime,
            last_login_time=result.LastLoginTime,
            wechat_openid=result.WeChatOpenID,
            merchant_id=result.MerchantID
        )
        
        # 获取用户角色
        user.roles = UserService.get_user_roles(user.user_id)
        
        # 获取用户权限
        user.permissions = UserService.get_user_permissions(user.user_id)
        
        return user
    
    @staticmethod
    def get_user_roles(user_id):
        """
        获取用户的角色列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            角色列表
        """
        query = """
            SELECT r.RoleID, r.RoleName, r.RoleCode, r.Description, r.IsActive, r.CreateTime, r.UpdateTime
            FROM Role r
            INNER JOIN UserRole ur ON r.RoleID = ur.RoleID
            WHERE ur.UserID = ? AND r.IsActive = 1
        """
        results = execute_query(query, (user_id,), fetch_type='all')
        
        roles = []
        for result in results:
            role = Role(
                role_id=result.RoleID,
                role_name=result.RoleName,
                role_code=result.RoleCode,
                description=result.Description,
                is_active=result.IsActive,
                create_time=result.CreateTime,
                update_time=result.UpdateTime
            )
            roles.append(role)
        
        return roles
    
    @staticmethod
    def get_user_permissions(user_id):
        """
        获取用户的权限列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            权限列表
        """
        query = """
            SELECT DISTINCT p.PermissionID, p.PermissionName, p.PermissionCode, p.Description, p.ModuleName, p.IsActive, p.CreateTime, p.UpdateTime
            FROM Permission p
            INNER JOIN RolePermission rp ON p.PermissionID = rp.PermissionID
            INNER JOIN UserRole ur ON rp.RoleID = ur.RoleID
            WHERE ur.UserID = ? AND p.IsActive = 1
        """
        results = execute_query(query, (user_id,), fetch_type='all')
        
        permissions = []
        for result in results:
            permission = Permission(
                permission_id=result.PermissionID,
                permission_name=result.PermissionName,
                permission_code=result.PermissionCode,
                description=result.Description,
                module_name=result.ModuleName,
                is_active=result.IsActive,
                create_time=result.CreateTime,
                update_time=result.UpdateTime
            )
            permissions.append(permission)
        
        return permissions
    
    @staticmethod
    def get_all_roles():
        """
        获取所有角色
        
        Returns:
            角色列表
        """
        query = """
            SELECT RoleID, RoleName, RoleCode, Description, IsActive, CreateTime, UpdateTime
            FROM Role
            WHERE IsActive = 1
            ORDER BY RoleID
        """
        results = execute_query(query, fetch_type='all')
        
        roles = []
        for result in results:
            role = Role(
                role_id=result.RoleID,
                role_name=result.RoleName,
                role_code=result.RoleCode,
                description=result.Description,
                is_active=result.IsActive,
                create_time=result.CreateTime,
                update_time=result.UpdateTime
            )
            roles.append(role)
        
        return roles
    
    @staticmethod
    def create_user(username, password, real_name, phone, email, role_ids, merchant_id=None):
        """
        创建新用户
        
        Args:
            username: 用户名
            password: 密码
            real_name: 真实姓名
            phone: 电话号码
            email: 电子邮箱
            role_ids: 角色ID列表
            merchant_id: 关联商户ID（可选）
            
        Returns:
            如果创建成功，返回User对象；否则返回None
        """
        # 检查用户名是否已存在
        existing_user = UserService.get_user_by_username(username)
        if existing_user:
            return None
        
        # 对密码进行哈希处理
        hashed_password = AuthService.hash_password(password)
        
        # 插入用户信息
        insert_query = """
            INSERT INTO [User] (Username, Password, RealName, Phone, Email, MerchantID, IsActive, CreateTime)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """
        execute_update(insert_query, (username, hashed_password, real_name, phone, email, merchant_id, datetime.datetime.now()))
        
        # 获取新创建的用户信息
        user = UserService.get_user_by_username(username)
        
        # 为用户分配角色
        if user and role_ids:
            for role_id in role_ids:
                assign_role_query = """
                    INSERT INTO UserRole (UserID, RoleID, CreateTime)
                    VALUES (?, ?, ?)
                """
                execute_update(assign_role_query, (user.user_id, role_id, datetime.datetime.now()))
            
            # 重新获取用户信息，包括角色和权限
            user = UserService.get_user_by_username(username)
        
        return user
    
    @staticmethod
    def update_user(user_id, real_name, phone, email, role_ids, is_active, merchant_id=None):
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            real_name: 真实姓名
            phone: 电话号码
            email: 电子邮箱
            role_ids: 角色ID列表
            is_active: 是否有效
            merchant_id: 关联商户ID（可选）
            
        Returns:
            如果更新成功，返回User对象；否则返回None
        """
        # 更新用户基本信息
        update_query = """
            UPDATE [User]
            SET RealName = ?, Phone = ?, Email = ?, MerchantID = ?, IsActive = ?, UpdateTime = ?
            WHERE UserID = ?
        """
        execute_update(update_query, (real_name, phone, email, merchant_id, is_active, datetime.datetime.now(), user_id))
        
        # 删除用户现有的角色
        delete_roles_query = "DELETE FROM UserRole WHERE UserID = ?"
        execute_update(delete_roles_query, (user_id,))
        
        # 为用户重新分配角色
        if role_ids:
            for role_id in role_ids:
                assign_role_query = """
                    INSERT INTO UserRole (UserID, RoleID, CreateTime)
                    VALUES (?, ?, ?)
                """
                execute_update(assign_role_query, (user_id, role_id, datetime.datetime.now()))
        
        # 获取更新后的用户信息
        return UserService.get_user_by_id(user_id)
    
    @staticmethod
    def update_user_password(user_id, new_password):
        """
        更新用户密码
        
        Args:
            user_id: 用户ID
            new_password: 新密码
            
        Returns:
            布尔值，表示是否更新成功
        """
        # 对密码进行哈希处理
        hashed_password = AuthService.hash_password(new_password)
        
        # 更新密码
        update_query = """
            UPDATE [User]
            SET Password = ?, UpdateTime = ?
            WHERE UserID = ?
        """
        result = execute_update(update_query, (hashed_password, datetime.datetime.now(), user_id))
        
        return result > 0
    
    @staticmethod
    def delete_user(user_id):
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            布尔值，表示是否删除成功
        """
        # 删除用户的角色关联
        delete_roles_query = "DELETE FROM UserRole WHERE UserID = ?"
        execute_update(delete_roles_query, (user_id,))
        
        # 删除用户
        delete_query = "DELETE FROM [User] WHERE UserID = ?"
        result = execute_update(delete_query, (user_id,))
        
        return result > 0
