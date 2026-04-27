from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.services.role_service import RoleService
from functools import wraps

role_bp = Blueprint('role', __name__)


def check_permission(permission_code):
    def decorator(f):
        @login_required
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(current_user, 'has_permission') or not current_user.has_permission(permission_code):
                flash('您没有权限执行此操作', 'danger')
                return redirect(url_for('auth.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_api_permission(permission_code):
    def decorator(f):
        @login_required
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(current_user, 'has_permission') or not current_user.has_permission(permission_code):
                return jsonify({'success': False, 'message': '您没有权限执行此操作'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@role_bp.route('/list')
@login_required
@check_permission('role_view')
def role_list():
    roles = RoleService.get_all_roles()
    return render_template('role/list.html', roles=roles)


@role_bp.route('/add', methods=['GET', 'POST'])
@login_required
@check_permission('role_create')
def role_add():
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
        role_name = data.get('role_name', '').strip() if isinstance(data.get('role_name'), str) else str(data.get('role_name', '')).strip()
        role_code = data.get('role_code', '').strip() if isinstance(data.get('role_code'), str) else str(data.get('role_code', '')).strip()
        description = data.get('description', '').strip() if isinstance(data.get('description'), str) else str(data.get('description', '')).strip()
        if not role_name or not role_code:
            return jsonify({'success': False, 'message': '角色名称和编码不能为空'}), 400
        result = RoleService.create_role(role_name, role_code, description)
        if result is None:
            return jsonify({'success': False, 'message': '角色编码已存在'}), 400
        return jsonify({'success': True, 'message': '角色创建成功'})
    return render_template('role/add.html')


@role_bp.route('/edit/<int:role_id>', methods=['GET', 'POST'])
@login_required
@check_permission('role_edit')
def role_edit(role_id):
    role = RoleService.get_role_by_id(role_id)
    if not role:
        flash('角色不存在', 'danger')
        return redirect(url_for('role.role_list'))
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
        role_name = data.get('role_name', '').strip() if isinstance(data.get('role_name'), str) else str(data.get('role_name', '')).strip()
        description = data.get('description', '').strip() if isinstance(data.get('description'), str) else str(data.get('description', '')).strip()
        permission_ids = data.getlist('permission_ids', type=int) if hasattr(data, 'getlist') else [int(x) for x in data.get('permission_ids', []) if str(x).isdigit()]
        if not role_name:
            return jsonify({'success': False, 'message': '角色名称不能为空'}), 400
        RoleService.update_role(role_id, role_name, description)
        RoleService.update_role_permissions(role_id, permission_ids)
        return jsonify({'success': True, 'message': '角色更新成功'})
    permissions_grouped = RoleService.get_all_permissions_grouped()
    role_permission_ids = RoleService.get_role_permissions(role_id)
    return render_template('role/edit.html', role=role, permissions_grouped=permissions_grouped, role_permission_ids=role_permission_ids)


@role_bp.route('/delete/<int:role_id>', methods=['POST'])
@login_required
@check_api_permission('role_delete')
def role_delete(role_id):
    if role_id <= 3:
        return jsonify({'success': False, 'message': '系统内置角色不允许删除'})
    result = RoleService.delete_role(role_id)
    if result:
        return jsonify({'success': True, 'message': '删除成功'})
    return jsonify({'success': False, 'message': '删除失败'})


@role_bp.route('/permissions')
@login_required
@check_permission('permission_view')
def permission_list():
    permissions = RoleService.get_all_permissions()
    return render_template('role/permissions.html', permissions=permissions)
