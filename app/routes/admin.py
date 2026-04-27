"""
后台管理首页蓝图
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from datetime import datetime

from app.services.admin_service import AdminService
from app.api_response import handle_exception

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
admin_svc = AdminService()


@admin_bp.route('/')
@login_required
def index():
    """后台管理首页"""
    current_time = datetime.now()
    return render_template('admin/index.html', current_time=current_time)


@admin_bp.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    """仪表盘统计数据API"""
    try:
        return jsonify({
            'success': True,
            'data': admin_svc.get_dashboard_stats()
        })
    except Exception as e:
        return handle_exception(e)
