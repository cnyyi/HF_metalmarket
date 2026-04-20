# 测试环境配置
from config.base import Config


class TestingConfig(Config):
    """
    应用测试环境配置类
    """
    # 测试模式
    TESTING = True
    DEBUG = True

    # 数据库配置统一继承 Config，通过环境变量注入或测试时 mock
    SQLALCHEMY_DATABASE_URI = None

    # 禁用CSRF保护（测试环境）
    WTF_CSRF_ENABLED = False

    # 日志配置（测试环境）
    LOG_LEVEL = 'DEBUG'

    # 上传配置（测试环境）
    UPLOAD_FOLDER = Config.UPLOAD_FOLDER
    PLOT_IMAGE_FOLDER = Config.PLOT_IMAGE_FOLDER
    LOGO_IMAGE_FOLDER = Config.LOGO_IMAGE_FOLDER
