# 角色模型
import datetime


class Role:
    """
    角色模型类，用于表示数据库中的Role表
    """
    def __init__(self, role_id=None, role_name=None, role_code=None, description=None,
                 is_active=True, create_time=None, update_time=None):
        self.role_id = role_id
        self.role_name = role_name
        self.role_code = role_code
        self.description = description
        self.is_active = is_active
        self.create_time = create_time or datetime.datetime.now()
        self.update_time = update_time
    
    def __repr__(self):
        return f"<Role(role_id={self.role_id}, role_name='{self.role_name}', role_code='{self.role_code}')>"
