from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, session, current_app
from flask_login import login_required, current_user, login_user
from app.services.wx_auth_service import WxAuthService
from app.services.wx_bind_service import WxBindService
from app.services.portal_service import PortalService
from app.api_response import handle_exception

wx_bp = Blueprint('wx', __name__, url_prefix='/wx')


def wx_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('wx.login'))
        return f(*args, **kwargs)
    return decorated


def wx_bound_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('wx.login'))
        merchant = WxBindService.get_user_current_merchant(current_user.user_id)
        if not merchant:
            return redirect(url_for('wx.bind_apply'))
        return f(*args, **kwargs)
    return decorated


def wx_role_allowed(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('wx.login'))
            merchant = WxBindService.get_user_current_merchant(current_user.user_id)
            if not merchant:
                return redirect(url_for('wx.bind_apply'))
            bind_role = WxBindService.get_user_bind_role(current_user.user_id, merchant['merchant_id'])
            if bind_role not in allowed_roles and bind_role != 'Boss':
                if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                    return jsonify({'success': False, 'message': '您没有权限查看此数据'}), 403
                wx_flash_msg = '您没有权限查看此页面'
                return render_template('wx/index.html', role_error=wx_flash_msg)
            return f(*args, **kwargs)
        return decorated
    return decorator


def _safe_page_params():
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = min(max(request.args.get('per_page', 10, type=int), 1), 50)
    return page, per_page


def _get_current_merchant_id():
    merchant = WxBindService.get_user_current_merchant(current_user.user_id)
    return merchant['merchant_id'] if merchant else None


def _get_current_bind_role():
    merchant_id = _get_current_merchant_id()
    if not merchant_id:
        return None
    return WxBindService.get_user_bind_role(current_user.user_id, merchant_id)


@wx_bp.route('/auth/login')
def login():
    redirect_uri = request.host_url.rstrip('/') + url_for('wx.callback')
    auth_url, state = WxAuthService.get_auth_url(redirect_uri, state=None)
    session['wx_oauth_state'] = state
    return redirect(auth_url)


@wx_bp.route('/auth/callback')
def callback():
    code = request.args.get('code', '')
    state = request.args.get('state', '')
    if not code:
        return redirect(url_for('wx.login'))

    expected_state = session.pop('wx_oauth_state', '')
    if not expected_state or state != expected_state:
        return render_template('wx/auth/login.html', error='授权验证失败，请重新登录')

    user = WxAuthService.handle_callback(code)
    if not user:
        return render_template('wx/auth/login.html', error='微信授权登录失败，请重试')

    login_user(user)
    merchant = WxBindService.get_user_current_merchant(user.user_id)
    if merchant:
        return redirect(url_for('wx.index'))
    return redirect(url_for('wx.bind_apply'))


@wx_bp.route('/auth/phone', methods=['GET'])
@wx_login_required
def phone_page():
    return render_template('wx/auth/phone.html')


@wx_bp.route('/auth/phone', methods=['POST'])
@wx_login_required
def phone_bind():
    data = request.get_json() or {}
    phone = data.get('phone', '').strip()
    sms_code = data.get('code', '').strip()
    if not phone or not sms_code:
        return jsonify({'success': False, 'message': '请输入手机号和验证码'})

    wx_user = WxAuthService.get_wx_user_by_user_id(current_user.user_id)
    if not wx_user:
        return jsonify({'success': False, 'message': '微信用户信息不存在'})

    result = WxAuthService.bind_phone(wx_user.wx_user_id, phone, sms_code)
    return jsonify(result)


@wx_bp.route('/auth/send-sms', methods=['POST'])
@wx_login_required
def send_sms():
    data = request.get_json() or {}
    phone = data.get('phone', '').strip()
    if not phone or len(phone) != 11 or not phone.startswith('1'):
        return jsonify({'success': False, 'message': '请输入正确的手机号'})
    result = WxAuthService.send_sms_code(phone)
    return jsonify(result)


@wx_bp.route('/bind/apply', methods=['GET'])
@wx_login_required
def bind_apply():
    return render_template('wx/bind/apply.html')


@wx_bp.route('/bind/status', methods=['GET'])
@wx_login_required
def bind_status():
    return render_template('wx/bind/status.html')


@wx_bp.route('/api/bind/apply', methods=['POST'])
@wx_login_required
def api_bind_apply():
    data = request.get_json() or {}
    merchant_id = data.get('merchant_id')
    bind_role = data.get('bind_role', '').strip()
    remark = data.get('remark', '').strip()
    if not merchant_id or not bind_role:
        return jsonify({'success': False, 'message': '请选择商户和身份'})
    if bind_role not in ('Boss', 'Staff', 'Finance'):
        return jsonify({'success': False, 'message': '无效的身份类型'})

    result = WxBindService.apply_binding(current_user.user_id, merchant_id, bind_role, remark)
    return jsonify(result)


@wx_bp.route('/api/bind/cancel', methods=['POST'])
@wx_login_required
def api_bind_cancel():
    data = request.get_json() or {}
    binding_id = data.get('binding_id')
    if not binding_id:
        return jsonify({'success': False, 'message': '参数错误'})
    result = WxBindService.cancel_binding(binding_id, current_user.user_id)
    return jsonify(result)


@wx_bp.route('/api/bindings', methods=['GET'])
@wx_login_required
def api_bindings():
    bindings = WxBindService.get_user_bindings(current_user.user_id)
    items = []
    for b in bindings:
        items.append({
            'binding_id': b.binding_id,
            'merchant_id': b.merchant_id,
            'merchant_name': b.merchant_name or '',
            'bind_role': b.bind_role,
            'bind_role_display': b.bind_role_display,
            'status': b.status,
            'status_display': b.status_display,
            'apply_time': b.apply_time.strftime('%Y-%m-%d %H:%M') if b.apply_time else '',
            'reject_reason': b.reject_reason or '',
        })
    return jsonify({'success': True, 'data': items})


@wx_bp.route('/api/merchants', methods=['GET'])
@wx_login_required
def api_merchants():
    search = request.args.get('search', '').strip()
    items = WxBindService.search_merchants(search)
    return jsonify({'success': True, 'data': items})


@wx_bp.route('')
@wx_login_required
@wx_bound_required
def index():
    return render_template('wx/index.html')


@wx_bp.route('/api/dashboard')
@wx_login_required
@wx_bound_required
def api_dashboard():
    merchant_id = _get_current_merchant_id()
    if not merchant_id:
        return jsonify({'success': False, 'message': '未绑定商户'}), 403
    try:
        stats = PortalService.get_dashboard(merchant_id)
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return handle_exception(e)


@wx_bp.route('/contracts')
@wx_login_required
@wx_role_allowed('Staff')
def contracts():
    return render_template('wx/contracts.html')


@wx_bp.route('/api/contracts')
@wx_login_required
@wx_role_allowed('Staff')
def api_contracts():
    merchant_id = _get_current_merchant_id()
    if not merchant_id:
        return jsonify({'success': False, 'message': '未绑定商户'}), 403
    page, per_page = _safe_page_params()
    try:
        result = PortalService.get_contracts(merchant_id, page=page, per_page=per_page)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@wx_bp.route('/utility')
@wx_login_required
@wx_role_allowed('Finance')
def utility():
    return render_template('wx/utility.html')


@wx_bp.route('/api/utility')
@wx_login_required
@wx_role_allowed('Finance')
def api_utility():
    merchant_id = _get_current_merchant_id()
    if not merchant_id:
        return jsonify({'success': False, 'message': '未绑定商户'}), 403
    page, per_page = _safe_page_params()
    try:
        result = PortalService.get_utility_readings(merchant_id, page=page, per_page=per_page)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@wx_bp.route('/scale')
@wx_login_required
@wx_role_allowed('Staff')
def scale():
    return render_template('wx/scale.html')


@wx_bp.route('/api/scale-records')
@wx_login_required
@wx_role_allowed('Staff')
def api_scale_records():
    merchant_id = _get_current_merchant_id()
    if not merchant_id:
        return jsonify({'success': False, 'message': '未绑定商户'}), 403
    page, per_page = _safe_page_params()
    try:
        result = PortalService.get_scale_records(merchant_id, page=page, per_page=per_page)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@wx_bp.route('/finance')
@wx_login_required
@wx_role_allowed('Finance')
def finance():
    return render_template('wx/finance.html')


@wx_bp.route('/api/receivables')
@wx_login_required
@wx_role_allowed('Finance')
def api_receivables():
    merchant_id = _get_current_merchant_id()
    if not merchant_id:
        return jsonify({'success': False, 'message': '未绑定商户'}), 403
    page, per_page = _safe_page_params()
    status = request.args.get('status', '').strip()
    try:
        result = PortalService.get_receivables(merchant_id, page=page, per_page=per_page, status=status or None)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@wx_bp.route('/profile')
@wx_login_required
def profile():
    return render_template('wx/profile.html')


@wx_bp.route('/switch')
@wx_login_required
@wx_bound_required
def switch():
    return render_template('wx/switch.html')


@wx_bp.route('/api/switch', methods=['POST'])
@wx_login_required
@wx_bound_required
def api_switch():
    data = request.get_json() or {}
    merchant_id = data.get('merchant_id')
    if not merchant_id:
        return jsonify({'success': False, 'message': '请选择商户'})
    result = WxBindService.switch_merchant(current_user.user_id, merchant_id)
    return jsonify(result)


@wx_bp.route('/api/current-merchant')
@wx_login_required
def api_current_merchant():
    merchant = WxBindService.get_user_current_merchant(current_user.user_id)
    if not merchant:
        return jsonify({'success': True, 'data': None})
    bind_role = WxBindService.get_user_bind_role(current_user.user_id, merchant['merchant_id'])
    return jsonify({'success': True, 'data': {'merchant_id': merchant['merchant_id'], 'merchant_name': merchant['merchant_name'], 'bind_role': bind_role}})


@wx_bp.route('/debug/login')
@login_required
def debug_login():
    if not current_app.debug:
        return redirect(url_for('wx.login'))
    merchant = WxBindService.get_user_current_merchant(current_user.user_id)
    if not merchant:
        return redirect(url_for('wx.bind_apply'))
    return redirect(url_for('wx.index'))
