# 扩展模块初始化
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# 初始化登录管理器
login_manager = LoginManager()

# 初始化CSRF保护
csrf = CSRFProtect()
