# 用户模型
import datetime
from flask_login import UserMixin
from app.models.role import Role


class User(UserMixin):
    """
    用户模型类，用于表示数据库中的User表，继承自UserMixin以支持Flask-Login
    """
    def __init__(self, user_id=None, username=None, password=None, real_name=None,
                 phone=None, email=None, is_active=True, create_time=None, update_time=None,
                 last_login_time=None, wechat_openid=None, merchant_id=None, merchant_name=None,
                 user_type='Admin'):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.real_name = real_name
        self.phone = phone
        self.email = email
        self._is_active = is_active
        self.create_time = create_time or datetime.datetime.now()
        self.update_time = update_time
        self.last_login_time = last_login_time
        self.wechat_openid = wechat_openid
        self.merchant_id = merchant_id
        self.merchant_name = merchant_name
        self.user_type = user_type or 'Admin'
        
        # 角色和权限列表
        self.roles = []
        self.permissions = []
    
    @property
    def is_merchant(self):
        """判断是否为商户用户"""
        return self.user_type == 'Merchant'
    
    @property
    def is_active(self):
        """
        获取用户激活状态
        """
        return self._is_active
    
    @is_active.setter
    def is_active(self, value):
        """
        设置用户激活状态
        """
        self._is_active = value
    
    def get_id(self):
        """
        Flask-Login要求的方法，返回用户的唯一标识符
        """
        return str(self.user_id)
    
    def has_role(self, role_code):
        """
        检查用户是否拥有指定角色
        """
        for role in self.roles:
            if role.role_code == role_code:
                return True
        return False
    
    def has_permission(self, permission_code):
        """
        检查用户是否拥有指定权限
        """
        for permission in self.permissions:
            if permission.permission_code == permission_code:
                return True
        return False
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}', real_name='{self.real_name}')>"
