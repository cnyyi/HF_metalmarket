# 开发环境配置
from config.base import Config


class DevelopmentConfig(Config):
    """
    应用开发环境配置类
    """
    # 调试模式
    DEBUG = True

    # 数据库配置统一继承 Config，通过环境变量注入
    SQLALCHEMY_DATABASE_URI = None

    # 日志配置（开发环境）
    LOG_LEVEL = 'DEBUG'

    # 启用详细的错误信息
    PROPAGATE_EXCEPTIONS = True
    TRAP_HTTP_EXCEPTIONS = True
    TRAP_BAD_REQUEST_ERRORS = True

    # 上传配置（开发环境）
    UPLOAD_FOLDER = Config.UPLOAD_FOLDER
    PLOT_IMAGE_FOLDER = Config.PLOT_IMAGE_FOLDER
    LOGO_IMAGE_FOLDER = Config.LOGO_IMAGE_FOLDER
