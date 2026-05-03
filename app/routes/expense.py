# -*- coding: utf-8 -*-
"""
费用单管理路由
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.routes.user import check_permission
from app.services.expense_service import ExpenseService
from app.services.dict_service import DictService
from app.api_response import handle_exception

expense_bp = Blueprint('expense', __name__)
expense_svc = ExpenseService()


# ==================== 列表页 ====================

@expense_bp.route('/')
@login_required
@check_permission('expense_view')
def index():
    """费用单列表页"""
    return render_template('expense/list.html')


@expense_bp.route('/list')
@login_required
@check_permission('expense_view')
def order_list():
    """费用单分页列表数据"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()

        result = expense_svc.get_orders(
            page=page, per_page=per_page,
            search=search or None,
            category=category or None,
            date_from=date_from or None,
            date_to=date_to or None,
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


# ==================== 新增 ====================

@expense_bp.route('/create')
@login_required
@check_permission('expense_create')
def create():
    """新增费用单页面"""
    return render_template('expense/create.html')


@expense_bp.route('/create', methods=['POST'])
@login_required
@check_permission('expense_create')
def create_order():
    """创建费用单"""
    try:
        data = request.json
        result = expense_svc.create_order(
            expense_category=data.get('expense_category', '').strip(),
            vendor_name=data.get('vendor_name', '').strip(),
            order_date=data.get('order_date', ''),
            items=data.get('items', []),
            description=data.get('description', '').strip() or None,
            created_by=current_user.user_id,
        )
        return jsonify({'success': True, 'message': f'费用单创建成功，已生成{result["payable_count"]}笔应付', 'data': result})
    except Exception as e:
        return handle_exception(e)


# ==================== 详情 ====================

@expense_bp.route('/detail/<int:order_id>')
@login_required
@check_permission('expense_view')
def detail(order_id):
    """费用单详情页"""
    return render_template('expense/detail.html', order_id=order_id)


@expense_bp.route('/detail/<int:order_id>/data')
@login_required
@check_permission('expense_view')
def detail_data(order_id):
    """费用单详情数据"""
    try:
        order = expense_svc.get_order_detail(order_id)
        if not order:
            return jsonify({'success': False, 'message': '费用单不存在'}), 404
        return jsonify({'success': True, 'data': order})
    except Exception as e:
        return handle_exception(e)


# ==================== 字典接口 ====================

@expense_bp.route('/categories')
@login_required
@check_permission('expense_view')
def categories():
    """获取费用大类"""
    try:
        items = DictService.get_expense_items('expense_category')
        return jsonify({'success': True, 'data': items})
    except Exception as e:
        return handle_exception(e)


@expense_bp.route('/expense-items')
@login_required
@check_permission('expense_view')
def expense_items():
    """获取支出费用项"""
    try:
        items = DictService.get_expense_items('expense_item_expend')
        return jsonify({'success': True, 'data': items})
    except Exception as e:
        return handle_exception(e)
