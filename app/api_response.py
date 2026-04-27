from flask import jsonify
import logging


def success_response(data=None, message='操作成功', status=200, **extra):
    payload = {
        'success': True,
        'message': message,
        'data': data
    }
    payload.update(extra)
    return jsonify(payload), status


def error_response(message, status=400, data=None, **extra):
    payload = {
        'success': False,
        'message': message,
        'data': data
    }
    payload.update(extra)
    return jsonify(payload), status


def handle_exception(e, user_message='操作失败，请稍后重试'):
    """路由层安全异常处理。

    - ValueError: 开发者主动抛出的校验消息，原样返回（400）
    - 其他 Exception: 记录完整堆栈到日志，返回通用消息（500）
    """
    if isinstance(e, ValueError):
        return error_response(str(e))
    logging.getLogger(__name__).exception('Route exception')
    return error_response(user_message, status=500)
