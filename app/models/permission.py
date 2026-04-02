# 权限模型
import datetime


class Permission:
    """
    权限模型类，用于表示数据库中的Permission表
    """
    def __init__(self, permission_id=None, permission_name=None, permission_code=None, 
                 description=None, module_name=None, is_active=True, create_time=None, update_time=None):
        self.permission_id = permission_id
        self.permission_name = permission_name
        self.permission_code = permission_code
        self.description = description
        self.module_name = module_name
        self.is_active = is_active
        self.create_time = create_time or datetime.datetime.now()
        self.update_time = update_time
    
    def __repr__(self):
        return f"<Permission(permission_id={self.permission_id}, permission_name='{self.permission_name}', permission_code='{self.permission_code}')>"
