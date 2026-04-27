# 认证服务
import datetime
from passlib.hash import pbkdf2_sha256
from utils.database import execute_query, execute_update
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission


class AuthService:
    """
    认证服务类，用于处理用户登录、注册和权限验证等功能
    """
    
    @staticmethod
    def verify_password(plain_password, hashed_password):
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            布尔值，表示密码是否匹配
        """
        return pbkdf2_sha256.verify(plain_password, hashed_password)
    
    @staticmethod
    def hash_password(password):
        """
        对密码进行哈希处理
        
        Args:
            password: 明文密码
            
        Returns:
            哈希密码
        """
        return pbkdf2_sha256.hash(password)
    
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
            SELECT UserID, Username, Password, RealName, Phone, Email, IsActive, 
                   CreateTime, UpdateTime, LastLoginTime, WeChatOpenID, MerchantID, UserType
            FROM [User]
            WHERE Username = ?
        """
        result = execute_query(query, (username,), fetch_type='one')
        
        if not result:
            return None
        
        # 获取商户名称（如果是商户用户）
        merchant_name = None
        if result.MerchantID:
            m_query = "SELECT MerchantName FROM Merchant WHERE MerchantID = ?"
            m_result = execute_query(m_query, (result.MerchantID,), fetch_type='one')
            if m_result:
                merchant_name = m_result.MerchantName
        
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
            merchant_id=result.MerchantID,
            merchant_name=merchant_name,
            user_type=getattr(result, 'UserType', 'Admin') or 'Admin'
        )
        
        # 获取用户角色
        user.roles = AuthService.get_user_roles(user.user_id)
        
        # 获取用户权限
        user.permissions = AuthService.get_user_permissions(user.user_id)
        
        return user
    
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
            SELECT UserID, Username, Password, RealName, Phone, Email, IsActive,
                   CreateTime, UpdateTime, LastLoginTime, WeChatOpenID, MerchantID, UserType
            FROM [User]
            WHERE UserID = ?
        """
        result = execute_query(query, (user_id,), fetch_type='one')
        
        if not result:
            return None
        
        # 获取商户名称（如果是商户用户）
        merchant_name = None
        if result.MerchantID:
            m_query = "SELECT MerchantName FROM Merchant WHERE MerchantID = ?"
            m_result = execute_query(m_query, (result.MerchantID,), fetch_type='one')
            if m_result:
                merchant_name = m_result.MerchantName
        
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
            merchant_id=result.MerchantID,
            merchant_name=merchant_name,
            user_type=getattr(result, 'UserType', 'Admin') or 'Admin'
        )
        
        # 获取用户角色
        user.roles = AuthService.get_user_roles(user.user_id)
        
        # 获取用户权限
        user.permissions = AuthService.get_user_permissions(user.user_id)
        
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
            SELECT DISTINCT p.PermissionID, p.PermissionName, p.PermissionCode, p.Description, p.ModuleName, p.OperationCode, p.SortOrder, p.IsActive, p.CreateTime, p.UpdateTime
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
                operation_code=getattr(result, 'OperationCode', None),
                sort_order=getattr(result, 'SortOrder', 0),
                is_active=result.IsActive,
                create_time=result.CreateTime,
                update_time=result.UpdateTime
            )
            permissions.append(permission)
        
        return permissions
    
    @staticmethod
    def login(username, password):
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            如果登录成功，返回User对象；否则返回None
        """
        # 获取用户信息
        user = AuthService.get_user_by_username(username)
        
        # 检查用户是否存在且密码是否正确
        if not user or not user.is_active or not AuthService.verify_password(password, user.password):
            return None
        
        # 更新用户最后登录时间
        update_query = """
            UPDATE [User]
            SET LastLoginTime = ?
            WHERE UserID = ?
        """
        execute_update(update_query, (datetime.datetime.now(), user.user_id))
        
        return user
    
    @staticmethod
    def register(username, password, real_name, phone, email, roles=None):
        """
        用户注册
        
        Args:
            username: 用户名
            password: 密码
            real_name: 真实姓名
            phone: 电话号码
            email: 电子邮箱
            roles: 角色列表（可选）
            
        Returns:
            如果注册成功，返回User对象；否则返回None
        """
        # 检查用户名是否已存在
        existing_user = AuthService.get_user_by_username(username)
        if existing_user:
            return None
        
        # 对密码进行哈希处理
        hashed_password = AuthService.hash_password(password)
        
        # 插入用户信息
        insert_query = """
            INSERT INTO [User] (Username, Password, RealName, Phone, Email, IsActive, CreateTime)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """
        execute_update(insert_query, (username, hashed_password, real_name, phone, email, datetime.datetime.now()))
        
        # 获取新创建的用户信息
        user = AuthService.get_user_by_username(username)
        
        # 如果指定了角色，为用户分配角色
        if roles and user:
            for role_code in roles:
                # 获取角色ID
                role_query = """
                    SELECT RoleID
                    FROM Role
                    WHERE RoleCode = ?
                """
                role_result = execute_query(role_query, (role_code,), fetch_type='one')
                
                if role_result:
                    # 为用户分配角色
                    assign_role_query = """
                        INSERT INTO UserRole (UserID, RoleID, CreateTime)
                        VALUES (?, ?, ?)
                    """
                    execute_update(assign_role_query, (user.user_id, role_result.RoleID, datetime.datetime.now()))
            
            # 重新获取用户信息，包括角色和权限
            user = AuthService.get_user_by_username(username)
        
        return user
    
    @staticmethod
    def has_permission(user_id, permission_code):
        """
        检查用户是否拥有指定权限
        
        Args:
            user_id: 用户ID
            permission_code: 权限编码
            
        Returns:
            布尔值，表示用户是否拥有该权限
        """
        query = """
            SELECT COUNT(*) as count
            FROM Permission p
            INNER JOIN RolePermission rp ON p.PermissionID = rp.PermissionID
            INNER JOIN UserRole ur ON rp.RoleID = ur.RoleID
            WHERE ur.UserID = ? AND p.PermissionCode = ? AND p.IsActive = 1
        """
        result = execute_query(query, (user_id, permission_code), fetch_type='one')
        
        return result.count > 0
