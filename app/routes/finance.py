# 财务管理相关路由
from flask import Blueprint, render_template
from flask_login import login_required

# 创建蓝图
finance_bp = Blueprint('finance', __name__)


@finance_bp.route('/receivable')
@login_required
def receivable():
    """
    应收账款页面
    """
    return render_template('finance/receivable.html')


@finance_bp.route('/payable')
@login_required
def payable():
    """
    应付账款页面
    """
    return render_template('finance/payable.html')


@finance_bp.route('/cash_flow')
@login_required
def cash_flow():
    """
    现金流水页面
    """
    return render_template('finance/cash_flow.html')


@finance_bp.route('/list')
@login_required
def finance_list():
    """
    财务管理首页
    """
    # 重定向到应收账款页面
    from flask import redirect, url_for
    return redirect(url_for('finance.receivable'))
