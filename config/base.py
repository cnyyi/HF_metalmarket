# 基础配置
import os
from datetime import timedelta


class Config:
    """
    应用基础配置类
    """
    # 密钥配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 数据库配置
    # 注意：由于需求中明确要求使用pyodbc直接连接SQL Server，避免SQLAlchemy兼容性问题，
    # 这里仅配置SQLAlchemy的连接字符串，但实际使用时会通过pyodbc直接操作数据库
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        'mssql+pymssql://sa:yyI.123212@yyi.myds.me:1433/hf_metalmarket'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 直接使用pyodbc的数据库连接字符串
    ODBC_CONNECTION_STRING = os.environ.get('ODBC_CONNECTION_STRING') or (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=yyi.myds.me;' 
        'DATABASE=hf_metalmarket;' 
        'UID=sa;' 
        'PWD=yyI.123212;' 
        'Encrypt=no;' 
        'TrustServerCertificate=yes;' 
        'charset=utf-8;' 
    )
    
    # 会话配置
    SESSION_PERMANENT = True
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    
    # 图片上传配置
    PLOT_IMAGE_FOLDER = os.path.join(os.getcwd(), 'static', 'images', 'plots')
    LOGO_IMAGE_FOLDER = os.path.join(os.getcwd(), 'static', 'images', 'logos')
    
    # 模板配置
    TEMPLATES_AUTO_RELOAD = True
    
    # 微信配置
    WECHAT_APPID = os.environ.get('WECHAT_APPID') or ''
    WECHAT_SECRET = os.environ.get('WECHAT_SECRET') or ''
    
    # 磅秤配置
    SCALE_DEVICE_PORT = os.environ.get('SCALE_DEVICE_PORT') or 'COM3'
    SCALE_BAUD_RATE = int(os.environ.get('SCALE_BAUD_RATE') or '9600')
    
    # 日志配置
    LOG_FOLDER = os.path.join(os.getcwd(), 'logs')
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
    # 分页配置
    PER_PAGE = 10
    
    # 权限配置
    PERMISSIONS = {
        'user_manage': '用户管理',
        'merchant_manage': '商户管理',
        'plot_manage': '地块管理',
        'contract_manage': '合同管理',
        'utility_manage': '水电计费',
        'finance_manage': '财务管理',
        'scale_manage': '磅秤管理',
    }
    
    # 角色配置
    ROLES = {
        'admin': '管理员',
        'staff': '工作人员',
        'merchant': '商户',
    }
