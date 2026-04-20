# -*- coding: utf-8 -*-
"""
微信OAuth认证服务
处理微信OAuth2.0授权登录和手机号绑定功能
"""

import datetime
import logging
import uuid
from flask import current_app
from wechatpy import WeChatOAuth
from wechatpy.exceptions import WeChatClientException
from utils.database import execute_query, execute_update, DBConnection
from app.models.wx_user import WxUser
from app.models.user import User
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class WxAuthService:

    @staticmethod
    def get_oauth_client():
        return WeChatOAuth(
            app_id=current_app.config.get('WX_APP_ID', ''),
            secret=current_app.config.get('WX_APP_SECRET', ''),
            redirect_uri='',
            scope='snsapi_userinfo',
        )

    @staticmethod
    def get_auth_url(redirect_uri, state=None):
        oauth = WxAuthService.get_oauth_client()
        oauth.redirect_uri = redirect_uri
        if not state:
            state = uuid.uuid4().hex[:16]
        return oauth.authorize_url(state=state), state

    @staticmethod
    def handle_callback(code):
        oauth = WxAuthService.get_oauth_client()
        try:
            token_data = oauth.fetch_access_token(code)
            openid = token_data.get('openid', '')
            access_token = token_data.get('access_token', '')
            unionid = token_data.get('unionid', '')
        except WeChatClientException as e:
            logger.error(f'微信OAuth回调失败: {e}')
            return None

        if not openid:
            return None

        wx_user = WxAuthService.get_wx_user(openid)
        if wx_user:
            user = AuthService.get_user_by_id(wx_user.user_id) if wx_user.user_id else None
            if user and user.is_active:
                return user
            return None

        nickname = ''
        head_img_url = ''
        try:
            user_info = oauth.get_user_info(access_token, openid)
            nickname = user_info.get('nickname', '')
            head_img_url = user_info.get('headimgurl', '')
        except WeChatClientException:
            pass

        user, wx_user = WxAuthService.create_wx_user(openid, unionid, nickname, head_img_url)
        return user

    @staticmethod
    def get_wx_user(openid):
        query = """
            SELECT WxUserID, OpenID, UnionID, UserID, Nickname, HeadImgUrl,
                   PhoneNumber, CurrentMerchantID, CreateTime, UpdateTime
            FROM WxUser WHERE OpenID = ?
        """
        result = execute_query(query, (openid,), fetch_type='one')
        if not result:
            return None
        return WxUser(
            wx_user_id=result.WxUserID,
            openid=result.OpenID,
            unionid=result.UnionID,
            user_id=result.UserID,
            nickname=result.Nickname,
            head_img_url=result.HeadImgUrl,
            phone_number=result.PhoneNumber,
            current_merchant_id=result.CurrentMerchantID,
            create_time=result.CreateTime,
            update_time=result.UpdateTime,
        )

    @staticmethod
    def get_wx_user_by_user_id(user_id):
        query = """
            SELECT WxUserID, OpenID, UnionID, UserID, Nickname, HeadImgUrl,
                   PhoneNumber, CurrentMerchantID, CreateTime, UpdateTime
            FROM WxUser WHERE UserID = ?
        """
        result = execute_query(query, (user_id,), fetch_type='one')
        if not result:
            return None
        return WxUser(
            wx_user_id=result.WxUserID,
            openid=result.OpenID,
            unionid=result.UnionID,
            user_id=result.UserID,
            nickname=result.Nickname,
            head_img_url=result.HeadImgUrl,
            phone_number=result.PhoneNumber,
            current_merchant_id=result.CurrentMerchantID,
            create_time=result.CreateTime,
            update_time=result.UpdateTime,
        )

    @staticmethod
    def create_wx_user(openid, unionid, nickname, head_img_url):
        username = f'wx_{uuid.uuid4().hex[:12]}'
        hashed_password = AuthService.hash_password(uuid.uuid4().hex)

        new_user_id = None
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO [User] (Username, Password, RealName, Phone, Email, IsActive, CreateTime, UserType)
                VALUES (?, ?, ?, '', '', 1, ?, N'WeChatUser')
            """, (username, hashed_password, nickname or '微信用户', datetime.datetime.now()))
            cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
            row = cursor.fetchone()
            new_user_id = row[0] if row else None
            conn.commit()

        if not new_user_id:
            return None, None

        role = execute_query("SELECT RoleID FROM Role WHERE RoleCode = 'merchant'", fetch_type='one')
        if role:
            execute_update(
                "INSERT INTO UserRole (UserID, RoleID, CreateTime) VALUES (?, ?, ?)",
                (new_user_id, role.RoleID, datetime.datetime.now()),
            )

        insert_wx_query = """
            INSERT INTO WxUser (OpenID, UnionID, UserID, Nickname, HeadImgUrl, CreateTime)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        execute_update(insert_wx_query, (openid, unionid or '', new_user_id, nickname, head_img_url, datetime.datetime.now()))

        user = AuthService.get_user_by_id(new_user_id)
        wx_user = WxAuthService.get_wx_user(openid)
        return user, wx_user

    @staticmethod
    def bind_phone(wx_user_id, phone, sms_code):
        stored_code = WxAuthService._get_sms_code(phone)
        if not stored_code or stored_code != sms_code:
            return {'success': False, 'message': '验证码错误或已过期'}

        execute_update("""
            UPDATE WxUser SET PhoneNumber = ?, UpdateTime = ? WHERE WxUserID = ?
        """, (phone, datetime.datetime.now(), wx_user_id))

        wx_user = execute_query(
            "SELECT UserID FROM WxUser WHERE WxUserID = ?", (wx_user_id,), fetch_type='one',
        )
        if wx_user and wx_user.UserID:
            execute_update("""
                UPDATE [User] SET Phone = ? WHERE UserID = ?
            """, (phone, wx_user.UserID))

        existing_user = execute_query(
            "SELECT UserID, Username FROM [User] WHERE Phone = ? AND UserType != N'WeChatUser'",
            (phone,), fetch_type='one',
        )
        if existing_user:
            return {'success': True, 'message': '手机号绑定成功', 'has_existing_account': True, 'existing_user_id': existing_user.UserID}

        return {'success': True, 'message': '手机号绑定成功', 'has_existing_account': False}

    @staticmethod
    def send_sms_code(phone):
        import random
        code = str(random.randint(100000, 999999))
        WxAuthService._store_sms_code(phone, code)
        logger.info(f'短信验证码已生成: phone={phone}, code={code}')
        return {'success': True, 'message': '验证码已发送'}

    @staticmethod
    def _store_sms_code(phone, code):
        from flask import session as flask_session
        session_key = f'sms_code_{phone}'
        session_data = {'code': code, 'expire': (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat()}
        flask_session[session_key] = session_data

    @staticmethod
    def _get_sms_code(phone):
        from flask import session as flask_session
        session_key = f'sms_code_{phone}'
        data = flask_session.get(session_key)
        if not data:
            return None
        expire_str = data.get('expire', '')
        if not expire_str:
            return None
        expire_time = datetime.datetime.fromisoformat(expire_str)
        if datetime.datetime.now() > expire_time:
            flask_session.pop(session_key, None)
            return None
        return data.get('code')
