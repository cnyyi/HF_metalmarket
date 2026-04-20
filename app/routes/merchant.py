# 商户管理相关路由
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.forms.merchant_form import MerchantAddForm, MerchantEditForm
from app.services.merchant_service import MerchantService
from app.routes.user import check_permission

# 创建蓝图
merchant_bp = Blueprint('merchant', __name__)


@merchant_bp.route('/list')
@login_required
def merchant_list():
    """
    商户列表页面
    """
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取搜索参数
    search = request.args.get('search', '')
    
    # 获取商户列表
    merchants, total_count, total_pages = MerchantService.get_merchants(page=page, per_page=per_page, search=search)
    
    return render_template('merchant/list.html', 
                         merchants=merchants, 
                         page=page, 
                         per_page=per_page, 
                         total_count=total_count, 
                         total_pages=total_pages, 
                         search=search)


@merchant_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """
    添加商户页面
    """
    form = MerchantAddForm()
    
    # 获取商户类型和业务类型
    merchant_types = MerchantService.get_merchant_types()
    form.merchant_type.choices = merchant_types
    
    business_types = MerchantService.get_business_types()
    form.business_type.choices = [('', '--请选择--')] + business_types
    
    if form.validate_on_submit():
        # 创建商户
        merchant = MerchantService.create_merchant(
            merchant_name=form.merchant_name.data,
            legal_person=form.legal_person.data,
            contact_person=form.contact_person.data,
            phone=form.phone.data,
            merchant_type=form.merchant_type.data,
            business_license=form.business_license.data,
            address=form.address.data,
            description=form.description.data,
            tax_registration=form.tax_registration.data,
            business_type=form.business_type.data if form.business_type.data else None
        )
        
        if merchant:
            flash('商户添加成功', 'success')
            return redirect(url_for('merchant.merchant_list'))
        else:
            flash('商户添加失败', 'danger')
    
    return render_template('merchant/add.html', form=form)


@merchant_bp.route('/edit/<int:merchant_id>', methods=['GET', 'POST'])
@login_required
def edit(merchant_id):
    """
    编辑商户页面
    """
    merchant = MerchantService.get_merchant_by_id(merchant_id)
    if not merchant:
        flash('商户不存在', 'danger')
        return redirect(url_for('merchant.merchant_list'))
    
    form = MerchantEditForm()
    
    # 获取商户类型和业务类型
    merchant_types = MerchantService.get_merchant_types()
    form.merchant_type.choices = merchant_types
    
    business_types = MerchantService.get_business_types()
    form.business_type.choices = [('', '--请选择--')] + business_types
    
    if request.method == 'GET':
        form.merchant_name.data = merchant.merchant_name
        form.legal_person.data = merchant.legal_person
        form.contact_person.data = merchant.contact_person
        form.phone.data = merchant.phone
        form.merchant_type.data = merchant.merchant_type
        form.business_type.data = merchant.business_type
        form.business_license.data = merchant.business_license
        form.tax_registration.data = merchant.tax_registration
        form.address.data = merchant.address
        form.description.data = merchant.description
        form.status.data = merchant.status == '正常'
    
    if form.validate_on_submit():
        updated_merchant = MerchantService.update_merchant(
            merchant_id=merchant_id,
            merchant_name=form.merchant_name.data,
            legal_person=form.legal_person.data,
            contact_person=form.contact_person.data,
            phone=form.phone.data,
            merchant_type=form.merchant_type.data,
            business_license=form.business_license.data,
            address=form.address.data,
            description=form.description.data,
            status=form.status.data,
            tax_registration=form.tax_registration.data,
            business_type=form.business_type.data if form.business_type.data else None
        )
        
        if updated_merchant:
            flash('商户更新成功', 'success')
            return redirect(url_for('merchant.merchant_list'))
        else:
            flash('商户更新失败', 'danger')
    
    return render_template('merchant/edit.html', form=form, merchant=merchant)


# ==================== 商户门户管理 ====================

@merchant_bp.route('/api/portal_status/<int:merchant_id>', methods=['GET'])
@login_required
def portal_status(merchant_id):
    """获取商户门户状态"""
    status = MerchantService.get_portal_status(merchant_id)
    return jsonify({'success': True, 'data': status})


@merchant_bp.route('/api/open_portal/<int:merchant_id>', methods=['POST'])
@login_required
def open_portal(merchant_id):
    """为商户开通门户"""
    data = request.get_json(silent=True) or {}
    result = MerchantService.open_portal(
        merchant_id=merchant_id,
        username=data.get('username'),
        password=data.get('password')
    )
    if result['success']:
        return jsonify(result)
    return jsonify(result), 400


@merchant_bp.route('/api/reset_portal_password/<int:merchant_id>', methods=['POST'])
@login_required
def reset_portal_password(merchant_id):
    """重置商户门户密码"""
    result = MerchantService.reset_portal_password(merchant_id)
    if result['success']:
        return jsonify(result)
    return jsonify(result), 400


# ==================== 商户绑定审批 ====================

@merchant_bp.route('/bind-requests')
@login_required
@check_permission('merchant_manage')
def bind_requests():
    return render_template('merchant/bind_requests.html')


@merchant_bp.route('/api/bind-requests')
@login_required
@check_permission('merchant_manage')
def api_bind_requests():
    from app.services.wx_bind_service import WxBindService
    try:
        items = WxBindService.get_pending_requests()
        return jsonify({'success': True, 'data': items})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@merchant_bp.route('/api/bind-approve/<int:binding_id>', methods=['POST'])
@login_required
@check_permission('merchant_manage')
def api_bind_approve(binding_id):
    from app.services.wx_bind_service import WxBindService
    from app.services.wx_notify_service import WxNotifyService
    try:
        result = WxBindService.approve_binding(binding_id, current_user.user_id)
        if result.get('success') and result.get('openid'):
            WxNotifyService.send_bind_approved(result['openid'], result['merchant_name'], result['bind_role'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@merchant_bp.route('/api/bind-reject/<int:binding_id>', methods=['POST'])
@login_required
@check_permission('merchant_manage')
def api_bind_reject(binding_id):
    from app.services.wx_bind_service import WxBindService
    from app.services.wx_notify_service import WxNotifyService
    data = request.get_json() or {}
    reason = data.get('reason', '').strip()
    try:
        result = WxBindService.reject_binding(binding_id, current_user.user_id, reason)
        if result.get('success') and result.get('openid'):
            WxNotifyService.send_bind_rejected(result['openid'], result['merchant_name'], result.get('reason', ''))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
