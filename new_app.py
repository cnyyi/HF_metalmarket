from flask import Flask, redirect, url_for
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config

# 初始化登录管理器
login_manager = LoginManager()

# 初始化CSRF保护
csrf = CSRFProtect()

app = Flask(__name__)
app.config.from_object(Config)

# 初始化扩展
login_manager.init_app(app)
csrf.init_app(app)

# 导入蓝图
from app.routes.auth import auth_bp

# 注册蓝图
app.register_blueprint(auth_bp, url_prefix='/auth')

# 用户加载函数
@login_manager.user_loader
def load_user(user_id):
    return None

# 未登录重定向
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'warning'

@app.route('/')
def hello():
    return redirect(url_for('auth.index'))

@app.route('/test')
def test():
    return 'Hello, Test!'

if __name__ == '__main__':
    app.run(debug=True, port=5000)