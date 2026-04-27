# -*- coding: utf-8 -*-
"""
垃圾清运管理路由
"""
from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from app.routes.user import check_permission
from app.services.garbage_service import GarbageService
from app.api_response import handle_exception

# 创建蓝图
garbage_bp = Blueprint('garbage', __name__)
# 初始化服务
garbage_svc = GarbageService()


# ==================== 列表页 ====================

@garbage_bp.route('/')
@login_required
@check_permission('garbage_view')
def index():
    """垃圾清运记录列表页"""
    return render_template('garbage/list.html')


@garbage_bp.route('/list')
@login_required
@check_permission('garbage_view')
def garbage_list():
    """垃圾清运记录分页列表数据"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        vendor_id = request.args.get('vendor_id', '').strip()
        show_all = request.args.get('show_all', '').strip().lower() == 'true'

        result = garbage_svc.get_collections(
            page=page, per_page=per_page,
            search=search or None,
            date_from=date_from or None,
            date_to=date_to or None,
            vendor_id=vendor_id or None,
            show_all=show_all,
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


# ==================== 新增 ====================

@garbage_bp.route('/create')
@login_required
@check_permission('garbage_create')
def create():
    """新增垃圾清运记录页面"""
    return render_template('garbage/add.html')


@garbage_bp.route('/create', methods=['POST'])
@login_required
@check_permission('garbage_create')
def create_collection():
    """创建垃圾清运记录（联动创建 Payable）"""
    try:
        data = request.json
        result = garbage_svc.create_collection(
            collection_date=data.get('collection_date', ''),
            customer_id=data.get('customer_id', ''),
            garbage_type=data.get('garbage_type', ''),
            amount=data.get('amount', 0),
            unit=data.get('unit', ''),
            unit_price=data.get('unit_price', 0),
            total_amount=data.get('total_amount', 0),
            description=data.get('description', '').strip() or None,
            created_by=current_user.user_id,
        )
        return jsonify({'success': True, 'message': '垃圾清运记录创建成功，已同步生成应付账款', 'data': result})
    except Exception as e:
        return handle_exception(e)


# ==================== 编辑 ====================

@garbage_bp.route('/edit/<int:collection_id>')
@login_required
@check_permission('garbage_edit')
def edit(collection_id):
    """编辑垃圾清运记录页面"""
    return render_template('garbage/edit.html', collection_id=collection_id)


@garbage_bp.route('/edit/<int:collection_id>', methods=['POST'])
@login_required
@check_permission('garbage_edit')
def update_collection(collection_id):
    """更新垃圾清运记录"""
    try:
        data = request.json
        result = garbage_svc.update_collection(
            collection_id=collection_id,
            collection_date=data.get('collection_date', ''),
            customer_id=data.get('customer_id', ''),
            garbage_type=data.get('garbage_type', ''),
            amount=data.get('amount', 0),
            unit=data.get('unit', ''),
            unit_price=data.get('unit_price', 0),
            total_amount=data.get('total_amount', 0),
            description=data.get('description', '').strip() or None,
            status=data.get('status', ''),
            updated_by=current_user.user_id,
        )
        return jsonify({'success': True, 'message': '垃圾清运记录更新成功', 'data': result})
    except Exception as e:
        return handle_exception(e)


# ==================== 详情 ====================

@garbage_bp.route('/detail/<int:collection_id>')
@login_required
@check_permission('garbage_view')
def detail(collection_id):
    """垃圾清运记录详情页"""
    return render_template('garbage/detail.html', collection_id=collection_id)


@garbage_bp.route('/detail/<int:collection_id>/data')
@login_required
@check_permission('garbage_view')
def detail_data(collection_id):
    """垃圾清运记录详情数据"""
    try:
        collection = garbage_svc.get_collection_detail(collection_id)
        if not collection:
            return jsonify({'success': False, 'message': '垃圾清运记录不存在'}), 404
        return jsonify({'success': True, 'data': collection})
    except Exception as e:
        return handle_exception(e)


# ==================== 删除 ====================

@garbage_bp.route('/delete/<int:collection_id>', methods=['POST'])
@login_required
@check_permission('garbage_delete')
def delete(collection_id):
    """删除垃圾清运记录"""
    try:
        result = garbage_svc.delete_collection(collection_id)
        return jsonify({'success': True, 'message': '垃圾清运记录删除成功'})
    except Exception as e:
        return handle_exception(e)


# ==================== 导出 ====================

@garbage_bp.route('/export')
@login_required
@check_permission('garbage_view')
def export():
    """导出垃圾清运记录为 Excel"""
    try:
        search = request.args.get('search', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        vendor_id = request.args.get('vendor_id', '').strip()

        output, filename = garbage_svc.export_collections(
            search=search or None,
            date_from=date_from or None,
            date_to=date_to or None,
            vendor_id=vendor_id or None,
        )
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        return handle_exception(e)


# ==================== 字典接口 ====================

@garbage_bp.route('/merchants')
@login_required
@check_permission('garbage_view')
def merchants():
    """获取商户列表"""
    try:
        result = garbage_svc.get_merchants()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@garbage_bp.route('/vendors')
@login_required
@check_permission('garbage_view')
def vendors():
    """获取供应商列表"""
    try:
        result = garbage_svc.get_vendors()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@garbage_bp.route('/garbage-types')
@login_required
@check_permission('garbage_view')
def garbage_types():
    """获取垃圾类型列表"""
    try:
        result = garbage_svc.get_garbage_types()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@garbage_bp.route('/status-options')
@login_required
@check_permission('garbage_view')
def status_options():
    """获取状态选项列表"""
    try:
        result = garbage_svc.get_status_options()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)
