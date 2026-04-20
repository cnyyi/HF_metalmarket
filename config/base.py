# -*- coding: utf-8 -*-
"""
基础配置类
所有环境配置的基类

安全说明：
- 所有敏感信息必须通过环境变量传入，禁止硬编码
- 启动前请设置以下环境变量（或创建 .env 文件）：
    set DB_SERVER=your_server_address
    set DB_DATABASE=hf_metalmarket
    set DB_UID=your_db_user
    set DB_PWD=your_db_password
    set SECRET_KEY=your_random_secret_key_at_least_32_chars
"""

import os
import secrets


def _get_required_env(key, default=None, warn=True):
    """
    安全获取环境变量
    - 如果设置了环境变量，使用环境变量的值
    - 否则使用默认值（仅在开发环境）
    生产环境应始终设置所有必要的环境变量
    """
    value = os.environ.get(key)
    if value is not None:
        return value
    if default is not None and warn:
        import sys
        print(f"[⚠️ 配置警告] 环境变量 {key} 未设置，使用默认值。生产环境请务必设置此变量！", file=sys.stderr)
    return default


def _build_odbc_connection_string():
    """
    构建 ODBC 连接字符串。

    优先使用 ODBC_CONNECTION_STRING；如果未提供，则回退到拆分环境变量。
    这样可以兼容现有脚本，也避免在仓库中硬编码真实连接信息。
    """
    raw_connection_string = os.environ.get('ODBC_CONNECTION_STRING')
    if raw_connection_string:
        return raw_connection_string

    db_driver = _get_required_env('DB_DRIVER', '{ODBC Driver 17 for SQL Server}', warn=False)
    db_server = _get_required_env('DB_SERVER', 'localhost')
    db_database = _get_required_env('DB_DATABASE', 'hf_metalmarket')
    db_uid = _get_required_env('DB_UID', 'sa')
    db_pwd = _get_required_env('DB_PWD', '')

    return (
        f'DRIVER={db_driver};'
        f'SERVER={db_server};'
        f'DATABASE={db_database};'
        f'UID={db_uid};'
        f'PWD={db_pwd};'
    )


class Config:
    """
    应用基础配置类
    
    包含所有环境共用的配置项
    """
    
    # 密钥配置（用于会话和CSRF保护）
    # 生产环境必须设置强随机密钥，可通过 python -c "import secrets; print(secrets.token_hex(32))" 生成
    SECRET_KEY = _get_required_env('SECRET_KEY', secrets.token_hex(32))
    
    # 数据库基础配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # 上传文件配置
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    PLOT_IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, 'plot')
    LOGO_IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, 'logo')
    
    # ODBC 数据库连接字符串 - 统一从环境变量读取
    DB_SERVER = _get_required_env('DB_SERVER', 'localhost')
    DB_DATABASE = _get_required_env('DB_DATABASE', 'hf_metalmarket')
    DB_UID = _get_required_env('DB_UID', 'sa')
    DB_PWD = _get_required_env('DB_PWD', '')
    ODBC_CONNECTION_STRING = _build_odbc_connection_string()
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    
    # 会话配置
    SESSION_COOKIE_NAME = 'hf_metalmarket_session'
    PERMANENT_SESSION_LIFETIME = 86400  # 24小时
    
    # CSRF保护配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # 不限制CSRF token的有效时间
    
    # 分页配置
    ITEMS_PER_PAGE = 10
    
    # 时间格式
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    DATE_FORMAT = '%Y-%m-%d'

    # 微信公众号配置
    WX_APP_ID = os.environ.get('WX_APP_ID', '')
    WX_APP_SECRET = os.environ.get('WX_APP_SECRET', '')
    WX_TOKEN = os.environ.get('WX_TOKEN', '')
    WX_ENCODING_AES_KEY = os.environ.get('WX_ENCODING_AES_KEY', '')
    WX_TEMPLATE_BIND_RESULT = os.environ.get('WX_TEMPLATE_BIND_RESULT', '')
