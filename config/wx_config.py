# -*- coding: utf-8 -*-
"""
微信配置类
所有微信相关的配置项，通过环境变量传入
"""

import os


class WxConfig:
    # 微信公众号 AppID
    WX_APP_ID = os.environ.get('WX_APP_ID', '')
    # 微信公众号 AppSecret
    WX_APP_SECRET = os.environ.get('WX_APP_SECRET', '')
    # 微信公众号 Token（用于消息校验）
    WX_TOKEN = os.environ.get('WX_TOKEN', '')
    # 微信公众号 EncodingAESKey（用于消息加解密）
    WX_ENCODING_AES_KEY = os.environ.get('WX_ENCODING_AES_KEY', '')
    # 绑定结果通知模板消息 ID
    WX_TEMPLATE_BIND_RESULT = os.environ.get('WX_TEMPLATE_BIND_RESULT', '')
