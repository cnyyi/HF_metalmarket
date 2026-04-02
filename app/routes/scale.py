# 磅秤管理相关路由
from flask import Blueprint, render_template
from flask_login import login_required

# 创建蓝图
scale_bp = Blueprint('scale', __name__)


@scale_bp.route('/list')
@login_required
def scale_list():
    """
    磅秤列表页面
    """
    return render_template('scale/list.html')


@scale_bp.route('/records')
@login_required
def records():
    """
    过磅记录页面
    """
    return render_template('scale/records.html')
