from flask import jsonify


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
