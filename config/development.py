# 开发环境配置
from config.base import Config


class DevelopmentConfig(Config):
    """
    应用开发环境配置类
    """
    # 调试模式
    DEBUG = True
    
    # 数据库配置（开发环境）
    SQLALCHEMY_DATABASE_URI = 'mssql+pymssql://sa:yyI.123212@yyi.myds.me:1433/hf_metalmarket'
    
    # 直接使用pyodbc的数据库连接字符串（开发环境）
    ODBC_CONNECTION_STRING = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=yyi.myds.me;'
        'DATABASE=hf_metalmarket;'
        'UID=sa;'
        'PWD=yyI.123212;'
        'Encrypt=no;'
        'TrustServerCertificate=yes;'
        'charset=utf-8;'
    )
    
    # 日志配置（开发环境）
    LOG_LEVEL = 'DEBUG'
    
    # 启用详细的错误信息
    PROPAGATE_EXCEPTIONS = True
    DEBUG = True
    TRAP_HTTP_EXCEPTIONS = True
    TRAP_BAD_REQUEST_ERRORS = True
    
    # 上传配置（开发环境）
    UPLOAD_FOLDER = Config.UPLOAD_FOLDER
    PLOT_IMAGE_FOLDER = Config.PLOT_IMAGE_FOLDER
    LOGO_IMAGE_FOLDER = Config.LOGO_IMAGE_FOLDER
