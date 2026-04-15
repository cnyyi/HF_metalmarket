from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.services.dict_service import DictService

dict_bp = Blueprint('dict', __name__)


def check_permission(permission_code):
    def decorator(f):
        @login_required
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(current_user, 'has_permission') or not current_user.has_permission(permission_code):
                return jsonify({'success': False, 'message': '您没有权限执行此操作'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@dict_bp.route('/list')
@login_required
def dict_list():
    return render_template('dict/list.html')


@dict_bp.route('/api/list', methods=['GET'])
@login_required
def api_list():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 15, type=int)
        dict_type = request.args.get('dict_type', '')
        keyword = request.args.get('keyword', '')
        is_active = request.args.get('is_active', '')

        is_active_val = None
        if is_active == '1':
            is_active_val = True
        elif is_active == '0':
            is_active_val = False

        items, total_count, total_pages = DictService.get_dict_list(
            page=page,
            per_page=per_page,
            dict_type=dict_type if dict_type else None,
            keyword=keyword if keyword else None,
            is_active=is_active_val
        )

        return jsonify({
            'success': True,
            'data': {
                'items': items,
                'total_count': total_count,
                'total_pages': total_pages,
                'page': page,
                'per_page': per_page
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@dict_bp.route('/api/types', methods=['GET'])
@login_required
def api_types():
    try:
        types = DictService.get_dict_types()
        return jsonify({'success': True, 'data': types})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@dict_bp.route('/api/detail/<int:dict_id>', methods=['GET'])
@login_required
def api_detail(dict_id):
    try:
        item = DictService.get_dict_by_id(dict_id)
        if not item:
            return jsonify({'success': False, 'message': '字典项不存在'}), 404
        return jsonify({'success': True, 'data': item})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@dict_bp.route('/api/add', methods=['POST'])
@check_permission('dict_manage')
def api_add():
    try:
        data = request.json

        dict_type = data.get('dict_type', '').strip()
        dict_code = data.get('dict_code', '').strip()
        dict_name = data.get('dict_name', '').strip()

        if not dict_type or not dict_code or not dict_name:
            return jsonify({'success': False, 'message': '字典类型、编码和名称不能为空'}), 400

        description = data.get('description', '').strip() or None
        sort_order = data.get('sort_order', 0)
        is_active = data.get('is_active', True)
        unit_price = data.get('unit_price')
        if unit_price is not None:
            unit_price = float(unit_price)

        new_id = DictService.create_dict(
            dict_type=dict_type,
            dict_code=dict_code,
            dict_name=dict_name,
            description=description,
            sort_order=sort_order,
            is_active=is_active,
            unit_price=unit_price
        )

        if new_id is None:
            return jsonify({'success': False, 'message': '该字典类型下编码已存在'}), 400

        return jsonify({'success': True, 'message': '新增成功', 'data': {'dict_id': new_id}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@dict_bp.route('/api/update/<int:dict_id>', methods=['POST'])
@check_permission('dict_manage')
def api_update(dict_id):
    try:
        data = request.json

        dict_type = data.get('dict_type', '').strip()
        dict_code = data.get('dict_code', '').strip()
        dict_name = data.get('dict_name', '').strip()

        if not dict_type or not dict_code or not dict_name:
            return jsonify({'success': False, 'message': '字典类型、编码和名称不能为空'}), 400

        description = data.get('description', '').strip() or None
        sort_order = data.get('sort_order', 0)
        is_active = data.get('is_active', True)
        unit_price = data.get('unit_price')
        if unit_price is not None:
            unit_price = float(unit_price)

        result = DictService.update_dict(
            dict_id=dict_id,
            dict_type=dict_type,
            dict_code=dict_code,
            dict_name=dict_name,
            description=description,
            sort_order=sort_order,
            is_active=is_active,
            unit_price=unit_price
        )

        if result:
            return jsonify({'success': True, 'message': '更新成功'})
        else:
            return jsonify({'success': False, 'message': '该字典类型下编码已存在'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@dict_bp.route('/api/delete/<int:dict_id>', methods=['POST'])
@check_permission('dict_manage')
def api_delete(dict_id):
    try:
        result = DictService.delete_dict(dict_id)
        if result:
            return jsonify({'success': True, 'message': '删除成功'})
        else:
            return jsonify({'success': False, 'message': '删除失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@dict_bp.route('/api/batch_status', methods=['POST'])
@check_permission('dict_manage')
def api_batch_status():
    try:
        data = request.json
        dict_ids = data.get('ids', [])
        is_active = data.get('is_active', True)

        if not dict_ids:
            return jsonify({'success': False, 'message': '请选择要操作的记录'}), 400

        rows = DictService.batch_update_status(dict_ids, is_active)
        status_text = '启用' if is_active else '禁用'
        return jsonify({'success': True, 'message': f'成功{status_text}{rows}条记录'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@dict_bp.route('/api/batch_delete', methods=['POST'])
@check_permission('dict_manage')
def api_batch_delete():
    try:
        data = request.json
        dict_ids = data.get('ids', [])

        if not dict_ids:
            return jsonify({'success': False, 'message': '请选择要删除的记录'}), 400

        rows = DictService.batch_delete(dict_ids)
        return jsonify({'success': True, 'message': f'成功删除{rows}条记录'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
