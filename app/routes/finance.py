# 财务管理相关路由
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.api_response import success_response, error_response
from app.services.receivable_service import ReceivableService
from app.services.finance_service import FinanceService
from app.services.customer_service import CustomerService
from app.services.dict_service import DictService
from app.services.account_service import AccountService
from app.services.prepayment_service import PrepaymentService
from app.services.deposit_service import DepositService
from app.routes.user import check_permission

finance_bp = Blueprint('finance', __name__)
receivable_svc = ReceivableService()
finance_svc = FinanceService()
customer_svc = CustomerService()
account_svc = AccountService()
prepayment_svc = PrepaymentService()
deposit_svc = DepositService()


# ==================== 应收账款 ====================

@finance_bp.route('/receivable')
@login_required
def receivable():
    return render_template('finance/receivable.html')


@finance_bp.route('/receivable/list', methods=['GET'])
@login_required
def receivable_list():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        expense_type_id = request.args.get('expense_type_id', type=int)

        result = receivable_svc.get_receivables(
            page=page, per_page=per_page,
            search=search or None, status=status or None,
            expense_type_id=expense_type_id
        )

        return success_response(result)
    except Exception as e:
        return error_response(f'获取数据失败：{str(e)}', status=500)


@finance_bp.route('/receivable/create', methods=['POST'])
@login_required
def receivable_create():
    try:
        data = request.json

        new_id = receivable_svc.create_receivable(
            merchant_id=data.get('merchant_id'),
            expense_type_id=data.get('expense_type_id'),
            amount=data.get('amount'),
            due_date=data.get('due_date'),
            description=data.get('description'),
            reference_id=data.get('reference_id'),
            reference_type=data.get('reference_type'),
            customer_type=data.get('customer_type', 'Merchant'),
            customer_id=data.get('customer_id'),
            product_name=data.get('product_name'),
            specification=data.get('specification'),
            quantity=data.get('quantity'),
            unit_id=data.get('unit_id'),
            unit_price=data.get('unit_price')
        )

        return success_response({'id': new_id}, message='添加成功', id=new_id)
    except ValueError as e:
        return error_response(str(e))
    except Exception as e:
        return error_response(f'添加失败：{str(e)}', status=500)


@finance_bp.route('/receivable/delete/<int:receivable_id>', methods=['POST'])
@login_required
@check_permission('finance_manage')
def receivable_delete(receivable_id):
    """软删除应收账款"""
    try:
        data = request.get_json() if request.is_json else {}
        delete_reason = data.get('delete_reason', '').strip() if data else ''

        if not delete_reason:
            return error_response('请填写删除原因')

        result = receivable_svc.soft_delete(
            receivable_id=receivable_id,
            deleted_by=current_user.user_id,
            delete_reason=delete_reason
        )

        if result['success']:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return success_response(result_data or None, message=result.get('message', '操作成功'), **result_data)
        else:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return error_response(result.get('message', '操作失败'), data=result_data or None, status=400, **result_data)

    except Exception as e:
        return error_response(f'删除失败：{str(e)}', status=500)


@finance_bp.route('/receivable/expense_types', methods=['GET'])
@login_required
def receivable_expense_types():
    """获取收入方向费用类型（从字典表获取）"""
    try:
        items = DictService.get_expense_items('expense_item_income')
        result = [{
            'expense_type_id': item['dict_id'],
            'expense_type_name': item['dict_name'],
            'expense_type_code': item['dict_code'],
            'expense_direction': '收入',
            'description': ''
        } for item in items]
        return success_response(result)
    except Exception as e:
        return error_response(f'获取费用类型失败：{str(e)}', status=500)


@finance_bp.route('/receivable/unit_types', methods=['GET'])
@login_required
def receivable_unit_types():
    """获取单位类型（从字典表获取）"""
    try:
        items = DictService.get_expense_items('unit_type')
        result = [{
            'unit_id': item['dict_id'],
            'unit_name': item['dict_name'],
            'unit_code': item['dict_code'],
        } for item in items]
        return success_response(result)
    except Exception as e:
        return error_response(f'获取单位类型失败：{str(e)}', status=500)


@finance_bp.route('/receivable/search_merchants', methods=['GET'])
@login_required
def receivable_search_merchants():
    try:
        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return success_response([])

        result = ReceivableService.search_merchants(keyword)
        return success_response(result)
    except Exception as e:
        return error_response(f'搜索商户失败：{str(e)}', status=500)


@finance_bp.route('/receivable/search_customers', methods=['GET'])
@login_required
def receivable_search_customers():
    """搜索往来客户（用于应收/应付下拉选择）"""
    try:
        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return success_response([])

        result = customer_svc.search_customers(keyword)
        return success_response(result)
    except Exception as e:
        return error_response(f'搜索客户失败：{str(e)}', status=500)


@finance_bp.route('/receivable/collect/<int:receivable_id>', methods=['POST'])
@login_required
def receivable_collect(receivable_id):
    """收款核销"""
    try:
        data = request.json
        result = finance_svc.collect_receivable(
            receivable_id=receivable_id,
            amount=float(data.get('amount', 0)),
            payment_method=data.get('payment_method', ''),
            transaction_date=data.get('transaction_date', ''),
            description=data.get('description', ''),
            created_by=current_user.user_id,
            account_id=data.get('account_id')
        )
        if result['success']:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return success_response(result_data or None, message=result.get('message', '操作成功'), **result_data)
        else:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return error_response(result.get('message', '操作失败'), data=result_data or None, status=400, **result_data)
    except Exception as e:
        return error_response(f'收款失败：{str(e)}', status=500)


@finance_bp.route('/receivable/detail/<int:receivable_id>', methods=['GET'])
@login_required
def receivable_detail(receivable_id):
    """应收详情（含收款历史、关联合同/抄表数据）"""
    try:
        detail = finance_svc.get_receivable_detail(receivable_id)
        if not detail:
            return error_response('记录不存在', status=404)
        return success_response(detail)
    except Exception as e:
        return error_response(f'获取详情失败：{str(e)}', status=500)


# ==================== 应付账款 ====================

@finance_bp.route('/payable')
@login_required
def payable():
    return render_template('finance/payable.html')


@finance_bp.route('/payable/list', methods=['GET'])
@login_required
def payable_list():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()

        result = finance_svc.get_payables(
            page=page, per_page=per_page,
            search=search or None, status=status or None
        )

        return success_response(result)
    except Exception as e:
        return error_response(f'获取数据失败：{str(e)}', status=500)


@finance_bp.route('/payable/list_by_customer', methods=['GET'])
@login_required
def payable_list_by_customer():
    """按客户汇总应付账款列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()

        result = finance_svc.get_payables_by_customer(
            page=page, per_page=per_page,
            search=search or None, status=status or None
        )

        return success_response(result)
    except Exception as e:
        return error_response(f'获取数据失败：{str(e)}', status=500)


@finance_bp.route('/payable/batch_pay', methods=['POST'])
@login_required
def payable_batch_pay():
    """按客户批量付款核销"""
    try:
        data = request.json
        result = finance_svc.batch_pay_by_customer(
            customer_type=data.get('customer_type', 'Merchant'),
            customer_id=int(data.get('customer_id', 0)),
            total_amount=float(data.get('amount', 0)),
            payment_method=data.get('payment_method', ''),
            transaction_date=data.get('transaction_date', ''),
            description=data.get('description', ''),
            created_by=current_user.user_id,
            account_id=data.get('account_id')
        )
        if result['success']:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return success_response(result_data or None, message=result.get('message', '批量付款成功'))
        else:
            return error_response(result.get('message', '批量付款失败'), status=400)
    except Exception as e:
        return error_response(f'批量付款失败：{str(e)}', status=500)


@finance_bp.route('/payable/delete/<int:payable_id>', methods=['POST'])
@login_required
def payable_delete(payable_id):
    """软删除应付账款"""
    try:
        data = request.get_json() if request.is_json else {}
        delete_reason = data.get('delete_reason', '').strip() if data else ''

        if not delete_reason:
            return error_response('请填写删除原因')

        result = finance_svc.soft_delete_payable(
            payable_id=payable_id,
            deleted_by=current_user.user_id,
            delete_reason=delete_reason
        )

        if result['success']:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return success_response(result_data or None, message=result.get('message', '删除成功'))
        else:
            return error_response(result.get('message', '删除失败'), status=400)
    except Exception as e:
        return error_response(f'删除失败：{str(e)}', status=500)


@finance_bp.route('/payable/add', methods=['POST'])
@login_required
def payable_add():
    try:
        data = request.json

        new_id = finance_svc.create_payable(
            vendor_name=data.get('vendor_name', '').strip(),
            expense_type_id=data.get('expense_type_id'),
            amount=data.get('amount'),
            due_date=data.get('due_date'),
            description=data.get('description'),
            created_by=current_user.user_id,
            customer_type=data.get('customer_type', 'Merchant'),
            customer_id=data.get('customer_id')
        )

        return success_response({'id': new_id}, message='添加成功', id=new_id)
    except ValueError as e:
        return error_response(str(e))
    except Exception as e:
        return error_response(f'添加失败：{str(e)}', status=500)


@finance_bp.route('/payable/pay/<int:payable_id>', methods=['POST'])
@login_required
def payable_pay(payable_id):
    """付款核销"""
    try:
        data = request.json
        result = finance_svc.pay_payable(
            payable_id=payable_id,
            amount=float(data.get('amount', 0)),
            payment_method=data.get('payment_method', ''),
            transaction_date=data.get('transaction_date', ''),
            description=data.get('description', ''),
            created_by=current_user.user_id,
            account_id=data.get('account_id')
        )
        if result['success']:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return success_response(result_data or None, message=result.get('message', '操作成功'), **result_data)
        else:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return error_response(result.get('message', '操作失败'), data=result_data or None, status=400, **result_data)
    except Exception as e:
        return error_response(f'付款失败：{str(e)}', status=500)


@finance_bp.route('/payable/detail/<int:payable_id>', methods=['GET'])
@login_required
def payable_detail(payable_id):
    """应付详情（含付款历史）"""
    try:
        payable = finance_svc._get_payable_by_id(payable_id)
        if not payable:
            return error_response('记录不存在', status=404)

        payment_records = finance_svc.get_payment_records(payable_id)

        data = {
            'payable_id': payable.PayableID,
            'vendor_name': payable.VendorName,
            'customer_type': getattr(payable, 'CustomerType', None) or 'Merchant',
            'customer_id': getattr(payable, 'CustomerID', None),
            'customer_name': getattr(payable, 'CustomerName', None) or payable.VendorName,
            'expense_type_id': payable.ExpenseTypeID,
            'expense_type_name': payable.ExpenseTypeName,
            'amount': float(payable.Amount),
            'paid_amount': float(payable.PaidAmount),
            'remaining_amount': float(payable.RemainingAmount),
            'due_date': payable.DueDate.strftime('%Y-%m-%d') if payable.DueDate else '',
            'status': payable.Status,
            'description': payable.Description or '',
            'create_time': payable.CreateTime.strftime('%Y-%m-%d %H:%M') if payable.CreateTime else '',
            'payment_records': payment_records
        }

        return success_response(data)
    except Exception as e:
        return error_response(f'获取详情失败：{str(e)}', status=500)


@finance_bp.route('/payable/expense_types', methods=['GET'])
@login_required
def payable_expense_types():
    """获取支出方向费用类型（从字典表获取）"""
    try:
        items = DictService.get_expense_items('expense_item_expend')
        result = [{
            'expense_type_id': item['dict_id'],
            'expense_type_name': item['dict_name'],
            'expense_type_code': item['dict_code'],
            'expense_direction': '支出',
            'description': ''
        } for item in items]
        return success_response(result)
    except Exception as e:
        return error_response(f'获取费用类型失败：{str(e)}', status=500)


# ==================== 现金流水 ====================

@finance_bp.route('/cash_flow')
@login_required
def cash_flow():
    return render_template('finance/cash_flow.html')


@finance_bp.route('/cash_flow/list', methods=['GET'])
@login_required
def cash_flow_list():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        direction = request.args.get('direction', '').strip()
        expense_type_id = request.args.get('expense_type_id', type=int)
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        account_id = request.args.get('account_id', type=int)

        result = finance_svc.get_cash_flows(
            page=page, per_page=per_page,
            direction=direction or None,
            expense_type_id=expense_type_id,
            start_date=start_date or None,
            end_date=end_date or None,
            account_id=account_id
        )

        # 附加汇总数据
        summary = finance_svc.get_cash_flow_summary(
            start_date=start_date or None,
            end_date=end_date or None
        )

        return success_response(result, summary=summary)
    except Exception as e:
        return error_response(f'获取数据失败：{str(e)}', status=500)


@finance_bp.route('/cash_flow/expense_types', methods=['GET'])
@login_required
def cash_flow_expense_types():
    """获取所有费用类型（从字典表获取，合并收入+支出）"""
    try:
        income_items = DictService.get_expense_items('expense_item_income')
        expend_items = DictService.get_expense_items('expense_item_expend')
        result = []
        for item in income_items:
            result.append({
                'expense_type_id': item['dict_id'],
                'expense_type_name': item['dict_name'],
                'expense_type_code': item['dict_code'],
                'expense_direction': '收入',
                'description': ''
            })
        for item in expend_items:
            result.append({
                'expense_type_id': item['dict_id'],
                'expense_type_name': item['dict_name'],
                'expense_type_code': item['dict_code'],
                'expense_direction': '支出',
                'description': ''
            })
        return success_response(result)
    except Exception as e:
        return error_response(f'获取费用类型失败：{str(e)}', status=500)


# ==================== 其他 ====================

@finance_bp.route('/list')
@login_required
def finance_list():
    from flask import redirect, url_for
    return redirect(url_for('finance.receivable'))


# ==================== 账户管理 ====================

@finance_bp.route('/account')
@login_required
@check_permission('account_manage')
def account():
    return render_template('finance/account.html')


@finance_bp.route('/account/list', methods=['GET'])
@login_required
@check_permission('account_manage')
def account_list():
    try:
        status = request.args.get('status', '').strip()
        result = account_svc.get_accounts(status=status or None)
        return success_response(result)
    except Exception as e:
        return error_response(f'获取数据失败：{str(e)}', status=500)


@finance_bp.route('/account/create', methods=['POST'])
@login_required
@check_permission('account_manage')
def account_create():
    try:
        data = request.json
        new_id = account_svc.create_account(
            account_name=data.get('account_name', '').strip(),
            account_type=data.get('account_type', '').strip(),
            bank_name=data.get('bank_name', '').strip() or None,
            bank_account=data.get('bank_account', '').strip() or None,
            is_default=data.get('is_default', False),
            remark=data.get('remark', '').strip() or None
        )
        return success_response({'id': new_id}, message='创建成功', id=new_id)
    except ValueError as e:
        return error_response(str(e))
    except Exception as e:
        return error_response(f'创建失败：{str(e)}', status=500)


@finance_bp.route('/account/update/<int:account_id>', methods=['POST'])
@login_required
@check_permission('account_manage')
def account_update(account_id):
    try:
        data = request.json
        account_svc.update_account(
            account_id=account_id,
            account_name=data.get('account_name'),
            account_type=data.get('account_type'),
            bank_name=data.get('bank_name'),
            bank_account=data.get('bank_account'),
            is_default=data.get('is_default'),
            remark=data.get('remark')
        )
        return success_response(message='更新成功')
    except ValueError as e:
        return error_response(str(e))
    except Exception as e:
        return error_response(f'更新失败：{str(e)}', status=500)


@finance_bp.route('/account/toggle_status/<int:account_id>', methods=['POST'])
@login_required
@check_permission('account_manage')
def account_toggle_status(account_id):
    try:
        new_status = account_svc.toggle_account_status(account_id)
        return success_response({'new_status': new_status}, message=f'账户已{new_status}', new_status=new_status)
    except ValueError as e:
        return error_response(str(e))
    except Exception as e:
        return error_response(f'操作失败：{str(e)}', status=500)


@finance_bp.route('/account/summary', methods=['GET'])
@login_required
@check_permission('account_manage')
def account_summary():
    try:
        result = account_svc.get_balance_summary()
        return success_response(result)
    except Exception as e:
        return error_response(f'获取汇总失败：{str(e)}', status=500)


# ==================== 直接记账 ====================

@finance_bp.route('/direct_entry')
@login_required
@check_permission('direct_entry')
def direct_entry():
    return render_template('finance/direct_entry.html')


@finance_bp.route('/direct_entry/submit', methods=['POST'])
@login_required
@check_permission('direct_entry')
def direct_entry_submit():
    try:
        data = request.json
        result = finance_svc.direct_entry(
            direction=data.get('direction', ''),
            amount=data.get('amount', 0),
            account_id=data.get('account_id'),
            expense_type_id=data.get('expense_type_id'),
            transaction_date=data.get('transaction_date', ''),
            description=data.get('description', ''),
            created_by=current_user.user_id
        )
        if result['success']:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return success_response(result_data or None, message=result.get('message', '操作成功'), **result_data)
        else:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return error_response(result.get('message', '操作失败'), data=result_data or None, status=400, **result_data)
    except Exception as e:
        return error_response(f'记账失败：{str(e)}', status=500)


@finance_bp.route('/account/active_list', methods=['GET'])
@login_required
def account_active_list():
    """获取所有有效账户（供下拉选择用，不需要 account_manage 权限）"""
    try:
        result = account_svc.get_accounts(status='有效')
        return success_response(result)
    except Exception as e:
        return error_response(f'获取账户失败：{str(e)}', status=500)


# ==================== 预收/预付管理 ====================

@finance_bp.route('/prepayment')
@login_required
@check_permission('prepayment_manage')
def prepayment():
    return render_template('finance/prepayment.html')


@finance_bp.route('/prepayment/list', methods=['GET'])
@login_required
@check_permission('prepayment_manage')
def prepayment_list():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        direction = request.args.get('direction', '').strip()
        customer_type = request.args.get('customer_type', '').strip()
        status = request.args.get('status', '').strip()
        search = request.args.get('search', '').strip()

        result = prepayment_svc.get_prepayments(
            page=page, per_page=per_page,
            direction=direction or None,
            customer_type=customer_type or None,
            status=status or None,
            search=search or None
        )
        return success_response(result)
    except Exception as e:
        return error_response(f'获取数据失败：{str(e)}', status=500)


@finance_bp.route('/prepayment/create', methods=['POST'])
@login_required
@check_permission('prepayment_manage')
def prepayment_create():
    try:
        data = request.json
        new_id = prepayment_svc.create_prepayment(
            direction=data.get('direction', ''),
            customer_type=data.get('customer_type', 'Merchant'),
            customer_id=data.get('customer_id'),
            customer_name=data.get('customer_name', '').strip(),
            total_amount=data.get('amount', 0),
            account_id=data.get('account_id'),
            expense_type_id=data.get('expense_type_id'),
            description=data.get('description', '').strip() or None,
            created_by=current_user.user_id
        )
        return success_response({'id': new_id}, message='创建成功', id=new_id)
    except ValueError as e:
        return error_response(str(e))
    except Exception as e:
        return error_response(f'创建失败：{str(e)}', status=500)


@finance_bp.route('/prepayment/detail/<int:prepayment_id>', methods=['GET'])
@login_required
@check_permission('prepayment_manage')
def prepayment_detail(prepayment_id):
    try:
        detail = prepayment_svc.get_prepayment_by_id(prepayment_id)
        if not detail:
            return error_response('记录不存在', status=404)

        apply_records = prepayment_svc.get_apply_records(prepayment_id)
        detail['apply_records'] = apply_records

        return success_response(detail)
    except Exception as e:
        return error_response(f'获取详情失败：{str(e)}', status=500)


@finance_bp.route('/prepayment/apply', methods=['POST'])
@login_required
@check_permission('prepayment_manage')
def prepayment_apply():
    """预收冲抵应收 / 预付冲抵应付"""
    try:
        data = request.json
        result = prepayment_svc.apply_prepayment(
            prepayment_id=data.get('prepayment_id'),
            target_items=data.get('target_items', []),
            created_by=current_user.user_id
        )
        if result['success']:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return success_response(result_data or None, message=result.get('message', '操作成功'), **result_data)
        else:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return error_response(result.get('message', '操作失败'), data=result_data or None, status=400, **result_data)
    except Exception as e:
        return error_response(f'冲抵失败：{str(e)}', status=500)


@finance_bp.route('/prepayment/available', methods=['GET'])
@login_required
def prepayment_available():
    """获取可用于冲抵的预收/预付列表（供收款弹窗使用）"""
    try:
        direction = request.args.get('direction', 'income')
        customer_type = request.args.get('customer_type', 'Merchant')
        customer_id = request.args.get('customer_id', type=int)
        if not customer_id:
            return success_response([])

        result = prepayment_svc.get_available_prepayments(direction, customer_type, customer_id)
        return success_response(result)
    except Exception as e:
        return error_response(f'获取数据失败：{str(e)}', status=500)


@finance_bp.route('/prepayment/summary', methods=['GET'])
@login_required
@check_permission('prepayment_manage')
def prepayment_summary():
    try:
        direction = request.args.get('direction', '').strip()
        result = prepayment_svc.get_summary(direction=direction or None)
        return success_response(result)
    except Exception as e:
        return error_response(f'获取汇总失败：{str(e)}', status=500)


# ==================== 押金管理 ====================

@finance_bp.route('/deposit')
@login_required
@check_permission('deposit_manage')
def deposit():
    return render_template('finance/deposit.html')


@finance_bp.route('/deposit/list', methods=['GET'])
@login_required
@check_permission('deposit_manage')
def deposit_list():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        customer_type = request.args.get('customer_type', '').strip()
        deposit_type = request.args.get('deposit_type', '').strip()
        status = request.args.get('status', '').strip()
        search = request.args.get('search', '').strip()

        result = deposit_svc.get_deposits(
            page=page, per_page=per_page,
            customer_type=customer_type or None,
            deposit_type=deposit_type or None,
            status=status or None,
            search=search or None
        )
        return success_response(result)
    except Exception as e:
        return error_response(f'获取数据失败：{str(e)}', status=500)


@finance_bp.route('/deposit/create', methods=['POST'])
@login_required
@check_permission('deposit_manage')
def deposit_create():
    try:
        data = request.json
        new_id = deposit_svc.create_deposit(
            customer_type=data.get('customer_type', 'Merchant'),
            customer_id=data.get('customer_id'),
            customer_name=data.get('customer_name', '').strip(),
            deposit_type=data.get('deposit_type', ''),
            amount=data.get('amount', 0),
            account_id=data.get('account_id'),
            related_contract_id=data.get('related_contract_id'),
            description=data.get('description', '').strip() or None,
            created_by=current_user.user_id
        )
        return success_response({'id': new_id}, message='收取成功', id=new_id)
    except ValueError as e:
        return error_response(str(e))
    except Exception as e:
        return error_response(f'收取失败：{str(e)}', status=500)


@finance_bp.route('/deposit/detail/<int:deposit_id>', methods=['GET'])
@login_required
@check_permission('deposit_manage')
def deposit_detail(deposit_id):
    try:
        detail = deposit_svc.get_deposit_by_id(deposit_id)
        if not detail:
            return error_response('记录不存在', status=404)

        operations = deposit_svc.get_operations(deposit_id)
        detail['operations'] = operations

        return success_response(detail)
    except Exception as e:
        return error_response(f'获取详情失败：{str(e)}', status=500)


@finance_bp.route('/deposit/refund', methods=['POST'])
@login_required
@check_permission('deposit_manage')
def deposit_refund():
    """退还押金"""
    try:
        data = request.json
        result = deposit_svc.refund_deposit(
            deposit_id=data.get('deposit_id'),
            amount=data.get('amount', 0),
            account_id=data.get('account_id'),
            description=data.get('description', '').strip() or None,
            created_by=current_user.user_id
        )
        if result['success']:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return success_response(result_data or None, message=result.get('message', '操作成功'), **result_data)
        else:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return error_response(result.get('message', '操作失败'), data=result_data or None, status=400, **result_data)
    except Exception as e:
        return error_response(f'退还失败：{str(e)}', status=500)


@finance_bp.route('/deposit/deduct', methods=['POST'])
@login_required
@check_permission('deposit_manage')
def deposit_deduct():
    """扣除押金"""
    try:
        data = request.json
        result = deposit_svc.deduct_deposit(
            deposit_id=data.get('deposit_id'),
            amount=data.get('amount', 0),
            expense_type_id=data.get('expense_type_id'),
            description=data.get('description', '').strip() or None,
            created_by=current_user.user_id
        )
        if result['success']:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return success_response(result_data or None, message=result.get('message', '操作成功'), **result_data)
        else:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return error_response(result.get('message', '操作失败'), data=result_data or None, status=400, **result_data)
    except Exception as e:
        return error_response(f'扣除失败：{str(e)}', status=500)


@finance_bp.route('/deposit/transfer', methods=['POST'])
@login_required
@check_permission('deposit_manage')
def deposit_transfer():
    """押金转抵应收"""
    try:
        data = request.json
        result = deposit_svc.transfer_deposit(
            deposit_id=data.get('deposit_id'),
            receivable_id=data.get('receivable_id'),
            amount=data.get('amount', 0),
            description=data.get('description', '').strip() or None,
            created_by=current_user.user_id
        )
        if result['success']:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return success_response(result_data or None, message=result.get('message', '操作成功'), **result_data)
        else:
            result_data = {k: v for k, v in result.items() if k not in ('success', 'message')}
            return error_response(result.get('message', '操作失败'), data=result_data or None, status=400, **result_data)
    except Exception as e:
        return error_response(f'转抵失败：{str(e)}', status=500)


@finance_bp.route('/deposit/summary', methods=['GET'])
@login_required
@check_permission('deposit_manage')
def deposit_summary():
    try:
        result = deposit_svc.get_summary()
        return success_response(result)
    except Exception as e:
        return error_response(f'获取汇总失败：{str(e)}', status=500)
