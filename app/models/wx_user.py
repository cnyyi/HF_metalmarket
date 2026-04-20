# -*- coding: utf-8 -*-
"""
微信用户模型
对应数据库 WxUser 表
"""

import datetime


class WxUser:
    """
    微信用户模型类，用于表示数据库中的 WxUser 表
    """
    def __init__(self, wx_user_id=None, openid=None, unionid=None,
                 user_id=None, nickname=None, head_img_url=None,
                 phone_number=None, current_merchant_id=None,
                 create_time=None, update_time=None):
        self.wx_user_id = wx_user_id
        self.openid = openid
        self.unionid = unionid
        self.user_id = user_id
        self.nickname = nickname
        self.head_img_url = head_img_url
        self.phone_number = phone_number
        self.current_merchant_id = current_merchant_id
        self.create_time = create_time or datetime.datetime.now()
        self.update_time = update_time

    def __repr__(self):
        return f"<WxUser(wx_user_id={self.wx_user_id}, openid='{self.openid}', nickname='{self.nickname}')>"
