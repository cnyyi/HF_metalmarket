# 生产环境配置
import os
from config.base import Config


class ProductionConfig(Config):
    """
    应用生产环境配置类
    """
    # 调试模式（生产环境关闭）
    DEBUG = False
    TESTING = False
    
    # 密钥配置（生产环境使用环境变量）
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # 数据库配置（生产环境）
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # 直接使用pyodbc的数据库连接字符串（生产环境）
    ODBC_CONNECTION_STRING = os.environ.get('ODBC_CONNECTION_STRING')
    
    # 日志配置（生产环境）
    LOG_LEVEL = 'WARNING'
    
    # 上传配置（生产环境）
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or Config.UPLOAD_FOLDER
    PLOT_IMAGE_FOLDER = os.environ.get('PLOT_IMAGE_FOLDER') or Config.PLOT_IMAGE_FOLDER
    LOGO_IMAGE_FOLDER = os.environ.get('LOGO_IMAGE_FOLDER') or Config.LOGO_IMAGE_FOLDER
    
    # 安全配置（生产环境）
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SECURE = True
