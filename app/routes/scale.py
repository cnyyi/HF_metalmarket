# -*- coding: utf-8 -*-
"""磅秤管理相关路由"""
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.api_response import handle_exception, success_response, error_response
from app.routes.user import check_permission, check_api_permission
from app.services.scale_service import ScaleService

scale_bp = Blueprint('scale', __name__)


@scale_bp.route('/list')
@login_required
@check_permission('scale_view')
def scale_list():
    return render_template('scale/list.html')


@scale_bp.route('/records')
@login_required
@check_permission('scale_view')
def records():
    return render_template('scale/records.html')


@scale_bp.route('/api/list')
@login_required
@check_api_permission('scale_view')
def api_scale_list():
    try:
        items = ScaleService.get_scale_list()
        return success_response({'items': items})
    except Exception as e:
        return handle_exception(e)


@scale_bp.route('/api/records')
@login_required
@check_api_permission('scale_view')
def api_records():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        keyword = request.args.get('keyword', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        result = ScaleService.get_scale_records(
            page=page, per_page=per_page,
            keyword=keyword or None,
            start_date=start_date or None,
            end_date=end_date or None
        )
        return success_response(result)
    except Exception as e:
        return handle_exception(e)


@scale_bp.route('/api/records/<int:record_id>')
@login_required
@check_api_permission('scale_view')
def api_record_detail(record_id):
    try:
        record = ScaleService.get_scale_record_detail(record_id)
        if not record:
            return error_response('记录不存在', status=404)
        return success_response(record)
    except Exception as e:
        return handle_exception(e)


@scale_bp.route('/api/dashboard/overview')
@login_required
@check_api_permission('scale_view')
def api_dashboard_overview():
    try:
        data = ScaleService.get_dashboard_overview()
        return success_response(data)
    except Exception as e:
        return handle_exception(e)


@scale_bp.route('/api/dashboard/trend')
@login_required
@check_api_permission('scale_view')
def api_dashboard_trend():
    try:
        now = datetime.now()
        year = request.args.get('year', now.year, type=int)
        month = request.args.get('month', now.month, type=int)
        data = ScaleService.get_monthly_trend(year, month)
        return success_response(data)
    except Exception as e:
        return handle_exception(e)


@scale_bp.route('/api/dashboard/today')
@login_required
@check_api_permission('scale_view')
def api_dashboard_today():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 15, type=int)
        keyword = request.args.get('keyword', '').strip()
        result = ScaleService.get_today_records(
            page=page, per_page=per_page,
            keyword=keyword or None
        )
        return success_response(result)
    except Exception as e:
        return handle_exception(e)
