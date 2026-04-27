# 用户管理相关路由
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.forms.user_form import UserAddForm, UserEditForm, PasswordChangeForm
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.api_response import handle_exception

# 创建蓝图
user_bp = Blueprint('user', __name__)


from functools import wraps

def check_permission(permission_code):
    """
    检查用户是否拥有指定权限的装饰器
    """
    def decorator(f):
        @login_required
        @wraps(f)  # 使用wraps保留原函数的名称和属性
        def decorated_function(*args, **kwargs):
            # 检查current_user是否有has_permission方法
            if not hasattr(current_user, 'has_permission') or not current_user.has_permission(permission_code):
                flash('您没有权限执行此操作', 'danger')
                return redirect(url_for('auth.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_api_permission(permission_code):
    """检查用户是否拥有指定权限的装饰器（API路由专用，返回JSON 403）"""
    def decorator(f):
        @login_required
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(current_user, 'has_permission') or not current_user.has_permission(permission_code):
                return jsonify({'success': False, 'message': '您没有权限执行此操作'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@user_bp.route('/list')
@login_required
@check_permission('user_view')
def user_list():
    """
    用户列表页面
    """
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    users, total_count, total_pages = UserService.get_users(page=page, per_page=10, search=search if search else None)
    
    return render_template('user/list.html', users=users, page=page, total_pages=total_pages, total_count=total_count, search=search)


@user_bp.route('/add', methods=['GET', 'POST'])
@check_permission('user_create')
def add():
    """
    添加用户页面
    """
    form = UserAddForm()
    
    # 获取所有角色
    roles = UserService.get_all_roles()
    form.roles.choices = [(role.role_id, role.role_name) for role in roles]
    
    # 获取所有商户（暂未实现，后续补充）
    form.merchant_id.choices = [(0, '无')]  # 占位符，后续补充
    
    if form.validate_on_submit():
        # 检查密码和确认密码是否一致
        if form.password.data != form.confirm_password.data:
            flash('两次输入的密码不一致', 'danger')
            return render_template('user/add.html', form=form)
        
        # 创建用户
        user = UserService.create_user(
            username=form.username.data,
            password=form.password.data,
            real_name=form.real_name.data,
            phone=form.phone.data,
            email=form.email.data,
            role_ids=form.roles.data,
            merchant_id=form.merchant_id.data if form.merchant_id.data != 0 else None
        )
        
        if user:
            flash('用户添加成功', 'success')
            return redirect(url_for('user.user_list'))
        else:
            flash('用户名已存在', 'danger')
    
    return render_template('user/add.html', form=form)


@user_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@check_permission('user_edit')
def edit(user_id):
    """
    编辑用户页面
    """
    # 获取用户信息
    user = UserService.get_user_by_id(user_id)
    if not user:
        flash('用户不存在', 'danger')
        return redirect(url_for('user.user_list'))
    
    form = UserEditForm(obj=user)
    
    # 获取所有角色
    roles = UserService.get_all_roles()
    form.roles.choices = [(role.role_id, role.role_name) for role in roles]
    
    # 获取所有商户（暂未实现，后续补充）
    form.merchant_id.choices = [(0, '无')]  # 占位符，后续补充
    
    # 设置当前角色
    current_role_ids = [role.role_id for role in user.roles]
    form.roles.data = current_role_ids
    
    # 设置当前商户
    form.merchant_id.data = user.merchant_id or 0
    
    if form.validate_on_submit():
        # 更新用户
        updated_user = UserService.update_user(
            user_id=user_id,
            real_name=form.real_name.data,
            phone=form.phone.data,
            email=form.email.data,
            role_ids=form.roles.data,
            is_active=form.is_active.data,
            merchant_id=form.merchant_id.data if form.merchant_id.data != 0 else None
        )
        
        if updated_user:
            flash('用户更新成功', 'success')
            return redirect(url_for('user.user_list'))
        else:
            flash('用户更新失败', 'danger')
    
    return render_template('user/edit.html', form=form, user=user)


@user_bp.route('/delete/<int:user_id>')
@check_permission('user_delete')
def delete(user_id):
    """
    删除用户
    """
    # 不能删除自己
    if current_user.user_id == user_id:
        flash('不能删除当前登录用户', 'danger')
        return redirect(url_for('user.user_list'))
    
    # 删除用户
    if UserService.delete_user(user_id):
        flash('用户删除成功', 'success')
    else:
        flash('用户删除失败', 'danger')
    
    return redirect(url_for('user.user_list'))


@user_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = PasswordChangeForm()

    if form.validate_on_submit():
        if not AuthService.verify_password(form.current_password.data, current_user.password):
            flash('当前密码错误', 'danger')
            return render_template('user/change_password.html', form=form)

        if form.new_password.data != form.confirm_new_password.data:
            flash('两次输入的新密码不一致', 'danger')
            return render_template('user/change_password.html', form=form)

        if UserService.update_user_password(current_user.user_id, form.new_password.data):
            flash('密码修改成功，请重新登录', 'success')
            return redirect(url_for('auth.logout'))
        else:
            flash('密码修改失败', 'danger')

    return render_template('user/change_password.html', form=form)


@user_bp.route('/api/detail/<int:user_id>', methods=['GET'])
@login_required
@check_api_permission('user_view')
def api_user_detail(user_id):
    try:
        user = UserService.get_user_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404

        role_ids = [role.role_id for role in user.roles]
        role_names = [role.role_name for role in user.roles]

        return jsonify({
            'success': True,
            'data': {
                'user_id': user.user_id,
                'username': user.username,
                'real_name': user.real_name or '',
                'phone': user.phone or '',
                'email': user.email or '',
                'is_active': user.is_active,
                'merchant_id': user.merchant_id,
                'role_ids': role_ids,
                'role_names': role_names
            }
        })
    except Exception as e:
        return handle_exception(e)


@user_bp.route('/api/update/<int:user_id>', methods=['POST'])
@login_required
@check_api_permission('user_edit')
def api_user_update(user_id):
    try:
        data = request.json
        updated = UserService.update_user(
            user_id=user_id,
            real_name=data.get('real_name'),
            phone=data.get('phone'),
            email=data.get('email'),
            role_ids=data.get('role_ids', []),
            is_active=data.get('is_active', True),
            merchant_id=data.get('merchant_id') if data.get('merchant_id') else None
        )

        if updated:
            return jsonify({'success': True, 'message': '更新成功'})
        else:
            return jsonify({'success': False, 'message': '更新失败'}), 400
    except Exception as e:
        return handle_exception(e)


@user_bp.route('/api/merchants', methods=['GET'])
@login_required
def api_merchants():
    try:
        from utils.database import execute_query
        results = execute_query("""
            SELECT MerchantID, MerchantName FROM Merchant ORDER BY MerchantID
        """, fetch_type='all')

        merchants = [{'merchant_id': r.MerchantID, 'merchant_name': r.MerchantName} for r in results]
        return jsonify({'success': True, 'data': merchants})
    except Exception as e:
        return handle_exception(e)


@user_bp.route('/api/roles', methods=['GET'])
@login_required
def api_roles():
    try:
        roles = UserService.get_all_roles()
        data = [{'role_id': r.role_id, 'role_name': r.role_name} for r in roles]
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return handle_exception(e)
