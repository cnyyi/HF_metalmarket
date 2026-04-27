"""客户管理路由"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.services.customer_service import CustomerService
from app.routes.user import check_permission, check_api_permission
from app.api_response import handle_exception

customer_bp = Blueprint('customer', __name__)
customer_svc = CustomerService()


@customer_bp.route('/list')
@check_permission('customer_view')
def customer_list():
    """客户列表页面"""
    return render_template('customer/list.html')


@customer_bp.route('/api/list', methods=['GET'])
@check_api_permission('customer_view')
def api_list():
    """客户列表API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()

        result = customer_svc.get_customers(
            page=page, per_page=per_page,
            search=search or None, status=status or None
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@customer_bp.route('/api/add', methods=['POST'])
@check_api_permission('customer_create')
def api_add():
    """新增客户"""
    try:
        data = request.json
        new_id = customer_svc.create_customer(data)
        return jsonify({'success': True, 'message': '添加成功', 'id': new_id})
    except Exception as e:
        return handle_exception(e)


@customer_bp.route('/api/edit/<int:customer_id>', methods=['POST'])
@check_api_permission('customer_edit')
def api_edit(customer_id):
    """编辑客户"""
    try:
        data = request.json
        result = customer_svc.update_customer(customer_id, data)
        if result:
            return jsonify({'success': True, 'message': '更新成功'})
        else:
            return jsonify({'success': False, 'message': '客户不存在'}), 404
    except Exception as e:
        return handle_exception(e)


@customer_bp.route('/api/delete/<int:customer_id>', methods=['POST'])
@check_api_permission('customer_delete')
def api_delete(customer_id):
    """删除客户"""
    try:
        result = customer_svc.delete_customer(customer_id)
        if result:
            return jsonify({'success': True, 'message': '删除成功'})
        else:
            return jsonify({'success': False, 'message': '客户不存在'}), 404
    except Exception as e:
        return handle_exception(e)


@customer_bp.route('/api/search', methods=['GET'])
@check_api_permission('customer_view')
def api_search():
    """搜索客户（用于应收/应付下拉选择）"""
    try:
        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return jsonify({'success': True, 'data': []})
        result = customer_svc.search_customers(keyword)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@customer_bp.route('/api/detail/<int:customer_id>', methods=['GET'])
@check_api_permission('customer_view')
def api_detail(customer_id):
    """获取客户详情"""
    try:
        result = customer_svc.get_customer_by_id(customer_id)
        if result:
            return jsonify({'success': True, 'data': result})
        else:
            return jsonify({'success': False, 'message': '客户不存在'}), 404
    except Exception as e:
        return handle_exception(e)
