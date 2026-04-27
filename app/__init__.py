# 应用初始化文件
import logging
from flask import Flask, redirect, url_for, send_from_directory, request

from config import Config
from app.extensions import login_manager, csrf

# 配置日志（替代 print 调试语句）
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """
    创建Flask应用实例
    """
    import os
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates'))
    app.config.from_object(config_class)

    # 配置日志
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )
    logger.info(f"日志级别: {log_level}")

    # 导入并注册蓝图（带异常处理，非核心蓝图导入失败不阻止应用启动）
    blueprints = [
        ('app.routes.auth', 'auth_bp', '/auth', True),
        ('app.routes.user', 'user_bp', '/user', False),
        ('app.routes.merchant', 'merchant_bp', '/merchant', False),
        ('app.routes.contract', 'contract_bp', '/contract', False),
        ('app.routes.finance', 'finance_bp', '/finance', False),
        ('app.routes.plot', 'plot_bp', '/plot', False),
        ('app.routes.scale', 'scale_bp', '/scale', False),
        ('app.routes.utility', 'utility_bp', '/utility', False),
        ('app.routes.customer', 'customer_bp', '/customer', False),
        ('app.routes.dict', 'dict_bp', '/dict', False),
        ('app.routes.portal', 'portal_bp', None, False),
        ('app.routes.wx', 'wx_bp', '/wx', False),
        ('app.routes.salary', 'salary_bp', '/salary', False),
        ('app.routes.dorm', 'dorm_bp', '/dorm', False),
        ('app.routes.expense', 'expense_bp', '/expense', False),
        ('app.routes.garbage', 'garbage_bp', '/garbage', False),
        ('app.routes.garbage_fee', 'garbage_fee_bp', '/garbage_fee', False),
        ('app.routes.role', 'role_bp', '/role', False),
        ('app.routes.admin', 'admin_bp', None, False),
    ]

    failed_blueprints = []
    for module_path, bp_name, url_prefix, is_critical in blueprints:
        try:
            import importlib
            module = importlib.import_module(module_path)
            bp = getattr(module, bp_name)
            if url_prefix:
                app.register_blueprint(bp, url_prefix=url_prefix)
            else:
                app.register_blueprint(bp)
            logger.info(f"蓝图 {bp_name} 注册成功 (prefix={url_prefix or '无'})")
        except Exception as e:
            msg = f"蓝图 {module_path}.{bp_name} 注册失败：{e}"
            if is_critical:
                logger.critical(msg)
                raise
            else:
                logger.error(msg)
                failed_blueprints.append(bp_name)

    if failed_blueprints:
        logger.warning(f"以下蓝图注册失败（应用仍可运行）：{', '.join(failed_blueprints)}")
    logger.info("蓝图注册流程完毕")
    
    # 初始化扩展
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # 初始化合同文档服务
    logger.info("开始初始化合同文档服务...")
    try:
        from app.services.contract_doc_service import contract_doc_service
        contract_doc_service.init_app(app)
        logger.info("合同文档服务初始化成功")
    except Exception as e:
        logger.exception(f"合同文档服务初始化失败：{e}")
    
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
    
    # favicon — 避免未登录时 500
    @app.route('/favicon.ico')
    def favicon():
        import os
        favicon_path = os.path.join(app.root_path, '..', 'static', 'favicon.ico')
        if os.path.exists(favicon_path):
            return send_from_directory(os.path.dirname(favicon_path), 'favicon.ico',
                                       mimetype='image/vnd.microsoft.icon')
        return '', 204

    # 根路径 → 后台首页
    @app.route('/')
    def root():
        return redirect(url_for('admin.index'))
    
    # 静态文件服务 - 上传的文件（带路径遍历防护）
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory, abort
        import os

        # 安全校验：防止路径遍历攻击（如 ../../etc/passwd）
        # send_from_directory 本身会做基础防护，但显式检查更安全
        if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
            abort(404)

        upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
        return send_from_directory(upload_folder, filename)

    # 全局异常处理器 — 兜底未捕获的异常
    from app.api_response import error_response

    @app.errorhandler(Exception)
    def handle_unhandled_exception(e):
        logger.exception('Unhandled exception')
        if request.is_json or request.accept_mimetypes.best == 'application/json':
            return error_response('服务器内部错误，请稍后重试', status=500)
        return '服务器内部错误', 500

    return app
