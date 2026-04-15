# 应用入口文件
import os
from app import create_app
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)

if __name__ == '__main__':
    app.run(
        debug=True, 
        port=5000,
        use_reloader=False
    )