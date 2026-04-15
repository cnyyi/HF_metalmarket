"""模拟登录流程，看错误信息"""
import sys
sys.path.insert(0, '.')

from app import create_app
from config import DevelopmentConfig
app = create_app(DevelopmentConfig)

with app.app_context():
    from app.forms.auth_form import LoginForm
    
    # 测试表单验证
    with app.test_request_context('/auth/login', method='POST', data={
        'username': 'yyi',
        'password': '123456',
    }):
        form = LoginForm()
        valid = form.validate()
        print(f"表单验证结果: {valid}")
        if not valid:
            print(f"表单错误: {form.errors}")
        
    # 测试 AuthService.login
    from app.services.auth_service import AuthService
    result = AuthService.login('yyi', '123456')
    print(f"AuthService.login('yyi', '123456') = {result}")
    
    # 试试 admin 用户
    result2 = AuthService.login('admin', 'admin123')
    print(f"AuthService.login('admin', 'admin123') = {result2}")
