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
    
    # ODBC数据库连接字符串 - 从环境变量读取，不再硬编码密码
    DB_SERVER = _get_required_env('DB_SERVER', 'localhost')
    DB_DATABASE = _get_required_env('DB_DATABASE', 'hf_metalmarket')
    DB_UID = _get_required_env('DB_UID', 'sa')
    DB_PWD = _get_required_env('DB_PWD', '')  # 密码无默认值，强制要求设置
    
    ODBC_CONNECTION_STRING = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={DB_SERVER};'
        f'DATABASE={DB_DATABASE};'
        f'UID={DB_UID};'
        f'PWD={DB_PWD};'
        'Encrypt=no;'
        'TrustServerCertificate=yes;'
        'charset=utf-8;'
    )
    
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
