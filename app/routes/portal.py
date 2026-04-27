# -*- coding: utf-8 -*-
"""商户门户路由 — 商户登录后的首页及数据查看"""
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, abort
from flask_login import login_required, current_user
from app.services.portal_service import PortalService
from app.api_response import handle_exception

portal_bp = Blueprint('portal', __name__, url_prefix='/portal')
portal_svc = PortalService()


def merchant_required(f):
    """确保是商户用户且已关联商户"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if getattr(current_user, 'user_type', 'Admin') != 'Merchant':
            return redirect(url_for('admin.index'))
        if not current_user.merchant_id:
            abort(403, description='未关联商户，请联系管理员')
        return f(*args, **kwargs)
    return decorated


@portal_bp.route('/')
@login_required
@merchant_required
def index():
    """商户首页"""
    return render_template('portal/index.html')


@portal_bp.route('/api/dashboard')
@login_required
@merchant_required
def api_dashboard():
    """首页统计数据"""
    try:
        stats = PortalService.get_dashboard(current_user.merchant_id)
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return handle_exception(e)


@portal_bp.route('/contracts')
@login_required
@merchant_required
def contracts():
    """我的合同"""
    return render_template('portal/contracts.html')


@portal_bp.route('/api/contracts')
@login_required
@merchant_required
def api_contracts():
    """合同列表数据"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        result = PortalService.get_contracts(current_user.merchant_id, page=page, per_page=per_page)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@portal_bp.route('/receivables')
@login_required
@merchant_required
def receivables():
    """缴费记录"""
    return render_template('portal/receivables.html')


@portal_bp.route('/api/receivables')
@login_required
@merchant_required
def api_receivables():
    """应收/缴费数据"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', '').strip()
        result = PortalService.get_receivables(
            current_user.merchant_id, page=page, per_page=per_page,
            status=status or None
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@portal_bp.route('/scale-records')
@login_required
@merchant_required
def scale_records():
    """过磅记录"""
    return render_template('portal/scale_records.html')


@portal_bp.route('/api/scale-records')
@login_required
@merchant_required
def api_scale_records():
    """过磅记录数据"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        result = PortalService.get_scale_records(current_user.merchant_id, page=page, per_page=per_page)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@portal_bp.route('/utility-readings')
@login_required
@merchant_required
def utility_readings():
    """水电抄表"""
    return render_template('portal/utility_readings.html')


@portal_bp.route('/api/utility-readings')
@login_required
@merchant_required
def api_utility_readings():
    """水电抄表数据"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        result = PortalService.get_utility_readings(current_user.merchant_id, page=page, per_page=per_page)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@portal_bp.route('/profile')
@login_required
@merchant_required
def profile():
    """商户信息"""
    return render_template('portal/profile.html')
