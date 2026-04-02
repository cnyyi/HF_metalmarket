# 应用初始化文件
from flask import Flask, redirect, url_for, render_template
from flask_login import LoginManager, login_required
from flask_wtf.csrf import CSRFProtect
from config import Config

# 初始化登录管理器
login_manager = LoginManager()

# 初始化CSRF保护
csrf = CSRFProtect()


def create_app(config_class=Config):
    """
    创建Flask应用实例
    """
    import os
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates'))
    app.config.from_object(config_class)
    
    # 导入蓝图
    print("Importing blueprints...")
    from .routes.auth import auth_bp
    print(f"Imported auth_bp: {auth_bp}")
    from .routes.user import user_bp
    print(f"Imported user_bp: {user_bp}")
    from .routes.merchant import merchant_bp
    print(f"Imported merchant_bp: {merchant_bp}")
    from .routes.contract import contract_bp
    print(f"Imported contract_bp: {contract_bp}")
    from .routes.finance import finance_bp
    print(f"Imported finance_bp: {finance_bp}")
    from .routes.plot import plot_bp
    print(f"Imported plot_bp: {plot_bp}")
    from .routes.scale import scale_bp
    print(f"Imported scale_bp: {scale_bp}")
    from .routes.utility import utility_bp
    print(f"Imported utility_bp: {utility_bp}")
    
    # 注册蓝图
    print("Registering blueprints...")
    app.register_blueprint(auth_bp, url_prefix='/auth')
    print(f"Registered auth_bp with prefix /auth")
    app.register_blueprint(user_bp, url_prefix='/user')
    print(f"Registered user_bp with prefix /user")
    app.register_blueprint(merchant_bp, url_prefix='/merchant')
    print(f"Registered merchant_bp with prefix /merchant")
    app.register_blueprint(contract_bp, url_prefix='/contract')
    print(f"Registered contract_bp with prefix /contract")
    app.register_blueprint(finance_bp, url_prefix='/finance')
    print(f"Registered finance_bp with prefix /finance")
    app.register_blueprint(plot_bp, url_prefix='/plot')
    print(f"Registered plot_bp with prefix /plot")
    app.register_blueprint(scale_bp, url_prefix='/scale')
    print(f"Registered scale_bp with prefix /scale")
    app.register_blueprint(utility_bp, url_prefix='/utility')
    print(f"Registered utility_bp with prefix /utility")
    
    # 初始化扩展
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # 初始化合同文档服务
    from app.services.contract_doc_service import contract_doc_service
    contract_doc_service.init_app(app)
    
    # 打印所有路由
    print("\n===== ALL ROUTES =====")
    for rule in app.url_map.iter_rules():
        print(f"{rule.rule} -> {rule.endpoint}")
    print("=====================\n")
    
    # 未登录重定向
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'warning'
    
    # 添加user_loader回调函数
    @login_manager.user_loader
    def load_user(user_id):
        # 从数据库加载用户
        from app.services.auth_service import AuthService
        return AuthService.get_user_by_id(int(user_id))
    
    # 添加测试路由
    @app.route('/test')
    def test():
        return 'Hello, Test!'
    
    # 添加测试上传页面路由
    @app.route('/test_upload_page')
    @login_required
    def test_upload_page():
        return render_template('test_upload.html')
    
    # 添加测试用户路由
    @app.route('/test_user')
    def test_user():
        return 'Hello, Test User!'
    
    # 添加测试用户列表路由
    @app.route('/test_user_list')
    def test_user_list():
        return 'Hello, Test User List!'
    
    # 添加测试 /user/list 路由
    @app.route('/user/list')
    def direct_user_list():
        return 'Hello, Direct User List!'
    
    # 根路径
    @app.route('/')
    def root():
        return redirect(url_for('auth.index'))
    
    # 静态文件服务 - 上传的文件
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        import os
        upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
        return send_from_directory(upload_folder, filename)
    
    return app
