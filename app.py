# 应用入口文件
import os
from dotenv import load_dotenv

# 加载 .env 环境变量（必须在导入配置之前）
load_dotenv()

from app import create_app
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)

if __name__ == '__main__':
    app.run(
        debug=True, 
        port=5000,
        use_reloader=False
    )