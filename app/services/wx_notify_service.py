import logging
from flask import current_app

logger = logging.getLogger(__name__)


class WxNotifyService:

    @staticmethod
    def _get_wechat_client():
        from wechatpy import WeChatClient
        app_id = current_app.config.get('WX_APP_ID', '')
        secret = current_app.config.get('WX_APP_SECRET', '')
        return WeChatClient(app_id, secret)

    @staticmethod
    def send_bind_approved(openid, merchant_name, bind_role):
        template_id = current_app.config.get('WX_TEMPLATE_BIND_RESULT', '')
        if not template_id or not openid:
            logger.warning('微信模板消息配置缺失或openid为空，跳过通知')
            return False

        role_map = {'Boss': '老板', 'Staff': '员工', 'Finance': '财务'}
        try:
            client = WxNotifyService._get_wechat_client()
            client.message.send_template(
                user_id=openid,
                template_id=template_id,
                data={
                    'first': {'value': '您的商户绑定申请已通过'},
                    'keyword1': {'value': merchant_name},
                    'keyword2': {'value': role_map.get(bind_role, bind_role)},
                    'keyword3': {'value': '已通过'},
                    'remark': {'value': '您现在可以登录查看商户数据了'},
                },
            )
            logger.info(f'绑定通过通知已发送: openid={openid}, merchant={merchant_name}')
            return True
        except Exception as e:
            logger.error(f'发送微信模板消息失败: {e}')
            return False

    @staticmethod
    def send_bind_rejected(openid, merchant_name, reason):
        template_id = current_app.config.get('WX_TEMPLATE_BIND_RESULT', '')
        if not template_id or not openid:
            logger.warning('微信模板消息配置缺失或openid为空，跳过通知')
            return False

        try:
            client = WxNotifyService._get_wechat_client()
            client.message.send_template(
                user_id=openid,
                template_id=template_id,
                data={
                    'first': {'value': '您的商户绑定申请已被驳回'},
                    'keyword1': {'value': merchant_name},
                    'keyword2': {'value': '-'},
                    'keyword3': {'value': '已驳回'},
                    'remark': {'value': f'驳回原因：{reason or "无"}'},
                },
            )
            logger.info(f'绑定驳回通知已发送: openid={openid}, merchant={merchant_name}')
            return True
        except Exception as e:
            logger.error(f'发送微信模板消息失败: {e}')
            return False

    @staticmethod
    def send_new_bind_request(admin_openids, merchant_name, user_name):
        template_id = current_app.config.get('WX_TEMPLATE_BIND_RESULT', '')
        if not template_id:
            logger.warning('微信模板消息配置缺失，跳过管理员通知')
            return False

        for openid in admin_openids:
            if not openid:
                continue
            try:
                client = WxNotifyService._get_wechat_client()
                client.message.send_template(
                    user_id=openid,
                    template_id=template_id,
                    data={
                        'first': {'value': '收到新的商户绑定申请'},
                        'keyword1': {'value': merchant_name},
                        'keyword2': {'value': user_name},
                        'keyword3': {'value': '待审批'},
                        'remark': {'value': '请登录管理后台进行审批'},
                    },
                )
            except Exception as e:
                logger.error(f'发送管理员通知失败: openid={openid}, error={e}')
        return True
