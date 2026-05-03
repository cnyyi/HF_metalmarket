from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.api_response import success_response, error_response, handle_exception
from app.services.agent_service import AgentService

agent_bp = Blueprint('agent', __name__)
agent_svc = AgentService()


@agent_bp.route('/chat')
@login_required
def chat():
    return render_template('agent/chat.html')


@agent_bp.route('/chat/send', methods=['POST'])
@login_required
def chat_send():
    try:
        data = request.json
        conversation_id = data.get('conversation_id')
        message = data.get('message', '').strip()

        if not message:
            return error_response('消息不能为空')

        result = agent_svc.chat(
            user_id=current_user.user_id,
            conversation_id=conversation_id,
            message=message,
            source='admin'
        )
        return success_response(result)
    except Exception as e:
        return handle_exception(e)


@agent_bp.route('/conversations', methods=['GET'])
@login_required
def conversations():
    try:
        result = agent_svc.get_conversations(current_user.user_id, source='admin')
        return success_response(result)
    except Exception as e:
        return handle_exception(e)


@agent_bp.route('/conversation/create', methods=['POST'])
@login_required
def conversation_create():
    try:
        conversation_id = agent_svc.create_conversation(current_user.user_id, source='admin')
        return success_response({'conversation_id': conversation_id})
    except Exception as e:
        return handle_exception(e)


@agent_bp.route('/conversation/delete/<int:conversation_id>', methods=['POST'])
@login_required
def conversation_delete(conversation_id):
    try:
        result = agent_svc.delete_conversation(conversation_id, current_user.user_id)
        if result:
            return success_response(message='删除成功')
        return error_response('会话不存在或无权删除')
    except Exception as e:
        return handle_exception(e)


@agent_bp.route('/history/<int:conversation_id>', methods=['GET'])
@login_required
def history(conversation_id):
    try:
        result = agent_svc.get_history(conversation_id, current_user.user_id)
        return success_response(result)
    except Exception as e:
        return handle_exception(e)


@agent_bp.route('/wx/chat')
def wx_chat():
    from flask import session
    wx_user_id = session.get('wx_user_id')
    if not wx_user_id:
        from flask import redirect, url_for
        return redirect(url_for('wx.index'))
    return render_template('agent/wx_chat.html')


@agent_bp.route('/wx/chat/send', methods=['POST'])
def wx_chat_send():
    from flask import session
    wx_user_id = session.get('wx_user_id')
    if not wx_user_id:
        return error_response('请先登录', status=401)

    try:
        data = request.json
        conversation_id = data.get('conversation_id')
        message = data.get('message', '').strip()

        if not message:
            return error_response('消息不能为空')

        from app.services.wx_bind_service import WxBindService
        bind_svc = WxBindService()
        binding = bind_svc.get_active_binding(wx_user_id)
        merchant_id = binding.get('merchant_id') if binding else None
        merchant_name = binding.get('merchant_name') if binding else None

        result = agent_svc.chat(
            user_id=wx_user_id,
            conversation_id=conversation_id,
            message=message,
            source='wx',
            merchant_id=merchant_id,
            merchant_name=merchant_name
        )
        return success_response(result)
    except Exception as e:
        return handle_exception(e)


@agent_bp.route('/wx/history/<int:conversation_id>', methods=['GET'])
def wx_history(conversation_id):
    from flask import session
    wx_user_id = session.get('wx_user_id')
    if not wx_user_id:
        return error_response('请先登录', status=401)

    try:
        result = agent_svc.get_history(conversation_id, wx_user_id)
        return success_response(result)
    except Exception as e:
        return handle_exception(e)
