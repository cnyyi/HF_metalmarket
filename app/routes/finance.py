# 财务管理相关路由
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
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

        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


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

        return jsonify({'success': True, 'message': '添加成功', 'id': new_id})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'添加失败：{str(e)}'}), 500


@finance_bp.route('/receivable/delete/<int:receivable_id>', methods=['POST'])
@login_required
@check_permission('finance_manage')
def receivable_delete(receivable_id):
    """软删除应收账款"""
    try:
        data = request.get_json() if request.is_json else {}
        delete_reason = data.get('delete_reason', '').strip() if data else ''

        if not delete_reason:
            return jsonify({'success': False, 'message': '请填写删除原因'}), 400

        result = receivable_svc.soft_delete(
            receivable_id=receivable_id,
            deleted_by=current_user.user_id,
            delete_reason=delete_reason
        )

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败：{str(e)}'}), 500


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
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取费用类型失败：{str(e)}'}), 500


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
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取单位类型失败：{str(e)}'}), 500


@finance_bp.route('/receivable/search_merchants', methods=['GET'])
@login_required
def receivable_search_merchants():
    try:
        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return jsonify({'success': True, 'data': []})

        result = ReceivableService.search_merchants(keyword)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'搜索商户失败：{str(e)}'}), 500


@finance_bp.route('/receivable/search_customers', methods=['GET'])
@login_required
def receivable_search_customers():
    """搜索往来客户（用于应收/应付下拉选择）"""
    try:
        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return jsonify({'success': True, 'data': []})

        result = customer_svc.search_customers(keyword)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'搜索客户失败：{str(e)}'}), 500


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
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'收款失败：{str(e)}'}), 500


@finance_bp.route('/receivable/detail/<int:receivable_id>', methods=['GET'])
@login_required
def receivable_detail(receivable_id):
    """应收详情（含收款历史、关联合同/抄表数据）"""
    try:
        receivable = receivable_svc.repo.get_by_id(receivable_id)
        if not receivable:
            return jsonify({'success': False, 'message': '记录不存在'}), 404

        # 收款历史
        records = finance_svc.collection_repo.get_by_receivable_id(receivable_id)
        collection_list = []
        for r in records:
            collection_list.append({
                'collection_record_id': r.CollectionRecordID,
                'amount': float(r.Amount),
                'payment_method': r.PaymentMethod,
                'transaction_date': r.TransactionDate.strftime('%Y-%m-%d') if r.TransactionDate else '',
                'description': r.Description or '',
                'operator_name': r.OperatorName or '',
                'create_time': r.CreateTime.strftime('%Y-%m-%d %H:%M') if r.CreateTime else '',
            })

        data = {
            'receivable_id': receivable.ReceivableID,
            'merchant_id': receivable.MerchantID,
            'merchant_name': receivable.CustomerName or '',
            'customer_type': receivable.CustomerType or 'Merchant',
            'customer_id': receivable.CustomerID or receivable.MerchantID,
            'expense_type_id': receivable.ExpenseTypeID,
            'expense_type_name': receivable.ExpenseTypeName,
            'amount': float(receivable.Amount),
            'paid_amount': float(receivable.PaidAmount),
            'remaining_amount': float(receivable.RemainingAmount),
            'product_name': receivable.ProductName or '',
            'specification': receivable.Specification or '',
            'quantity': float(receivable.Quantity) if receivable.Quantity else None,
            'unit_id': receivable.UnitID,
            'unit_name': receivable.UnitName or '',
            'unit_price': float(receivable.UnitPrice) if receivable.UnitPrice else None,
            'due_date': receivable.DueDate.strftime('%Y-%m-%d') if receivable.DueDate else '',
            'status': receivable.Status,
            'description': receivable.Description or '',
            'reference_id': receivable.ReferenceID,
            'reference_type': receivable.ReferenceType or '',
            'create_time': receivable.CreateTime.strftime('%Y-%m-%d %H:%M') if receivable.CreateTime else '',
            'is_active': bool(receivable.IsActive) if hasattr(receivable, 'IsActive') else True,
            'deleted_at': receivable.DeletedAt.strftime('%Y-%m-%d %H:%M') if hasattr(receivable, 'DeletedAt') and receivable.DeletedAt else '',
            'delete_reason': receivable.DeleteReason or '' if hasattr(receivable, 'DeleteReason') else '',
            'collection_records': collection_list
        }

        # 关联数据：租金→合同，电费/水费→抄表
        expense_name = receivable.ExpenseTypeName or ''
        ref_type = receivable.ReferenceType or ''

        # 租金：通过 ReferenceID=ContractID 查关联合同
        if (expense_name == '租金' or ref_type == 'contract') and receivable.ReferenceID:
            contract_data = _get_contract_summary(receivable.ReferenceID)
            if contract_data:
                data['contract_info'] = contract_data

        # 电费/水费：通过多种策略查关联抄表
        if expense_name in ('电费', '水费') or ref_type == 'utility_reading_merged' or ref_type == 'utility_reading':
            reading_data = _get_utility_readings(receivable_id)
            if reading_data:
                data['utility_readings'] = reading_data

        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取详情失败：{str(e)}'}), 500


def _get_contract_summary(contract_id):
    """获取合同摘要信息（含关联合同地块）"""
    try:
        from utils.database import DBConnection
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.ContractID, c.ContractNumber, c.ContractName,
                       c.MerchantID, m.MerchantName,
                       c.StartDate, c.EndDate,
                       c.ContractAmount, c.AmountReduction, c.ActualAmount,
                       c.Status, c.PaymentMethod, c.ContractPeriod
                FROM Contract c
                LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
                WHERE c.ContractID = ?
            """, contract_id)
            row = cursor.fetchone()
            if not row:
                return None

            # 查关联合同地块
            cursor.execute("""
                SELECT cp.PlotID, cp.UnitPrice, cp.Area, cp.MonthlyPrice,
                       p.PlotNumber, p.PlotName
                FROM ContractPlot cp
                LEFT JOIN Plot p ON cp.PlotID = p.PlotID
                WHERE cp.ContractID = ?
            """, contract_id)
            plots = []
            for p in cursor.fetchall():
                plots.append({
                    'plot_number': p.PlotNumber or '',
                    'plot_name': p.PlotName or '',
                    'area': float(p.Area) if p.Area else 0,
                    'monthly_price': float(p.MonthlyPrice) if p.MonthlyPrice else 0,
                })
            plot_numbers = ', '.join([pl['plot_number'] for pl in plots if pl['plot_number']])

            return {
                'contract_id': row.ContractID,
                'contract_number': row.ContractNumber or '',
                'contract_name': row.ContractName or '',
                'merchant_name': row.MerchantName or '',
                'plot_numbers': plot_numbers,
                'plots': plots,
                'start_date': row.StartDate.strftime('%Y-%m-%d') if row.StartDate else '',
                'end_date': row.EndDate.strftime('%Y-%m-%d') if row.EndDate else '',
                'contract_amount': float(row.ContractAmount) if row.ContractAmount else 0,
                'amount_reduction': float(row.AmountReduction) if row.AmountReduction else 0,
                'actual_amount': float(row.ActualAmount) if row.ActualAmount else 0,
                'status': row.Status or '',
                'payment_method': row.PaymentMethod or '',
                'contract_period': row.ContractPeriod or '',
            }
    except Exception:
        return None


def _get_utility_readings(receivable_id):
    """获取关联的抄表数据列表

    查询策略（按优先级）：
    1. 通过 ReceivableDetail 关联查
    2. 通过 ReferenceID 直接查（旧版 utility_reading 类型）
    3. 通过 MerchantID + BelongMonth + MeterType 关联查（兜底）
    """
    try:
        import re
        from utils.database import DBConnection

        # 公共 SQL 片段：抄表记录 + 电表/水表关联
        UTILITY_SELECT = """
            SELECT ur.ReadingID, ur.MeterID, ur.MeterType,
                   ur.LastReading, ur.CurrentReading, ur.Usage, ur.UnitPrice, ur.TotalAmount,
                   ur.BelongMonth, ur.ReadingDate, ur.ReadingMonth,
                   CASE
                       WHEN ur.MeterType = N'electricity' THEN ISNULL(em.MeterMultiplier, 1)
                       WHEN ur.MeterType = N'water' THEN ISNULL(wm.MeterMultiplier, 1)
                       ELSE 1
                   END AS MeterMultiplier,
                   CASE
                       WHEN ur.MeterType = N'electricity' THEN em.MeterNumber
                       WHEN ur.MeterType = N'water' THEN wm.MeterNumber
                       ELSE ''
                   END AS MeterNumber,
                   CASE
                       WHEN ur.MeterType = N'electricity' THEN ISNULL(em.InstallationLocation, '')
                       WHEN ur.MeterType = N'water' THEN ISNULL(wm.InstallationLocation, '')
                       ELSE ''
                   END AS InstallationLocation
        """
        UTILITY_JOINS = """
            LEFT JOIN ElectricityMeter em ON ur.MeterType = N'electricity' AND ur.MeterID = em.MeterID
            LEFT JOIN WaterMeter wm ON ur.MeterType = N'water' AND ur.MeterID = wm.MeterID
        """

        with DBConnection() as conn:
            cursor = conn.cursor()
            rows = []

            # ---- 策略1：通过 ReceivableDetail 关联 ----
            cursor.execute(f"""
                {UTILITY_SELECT}
                FROM ReceivableDetail rd
                INNER JOIN UtilityReading ur ON rd.ReadingID = ur.ReadingID
                {UTILITY_JOINS}
                WHERE rd.ReceivableID = ?
                ORDER BY ur.MeterType, ur.MeterID
            """, receivable_id)
            rows = cursor.fetchall()

            # ---- 策略2：通过 ReferenceID 直接查（旧版 utility_reading） ----
            if not rows:
                cursor.execute(f"""
                    {UTILITY_SELECT}
                    FROM UtilityReading ur
                    {UTILITY_JOINS}
                    WHERE ur.ReadingID IN (
                        SELECT ReferenceID FROM Receivable
                        WHERE ReceivableID = ? AND ReferenceType = N'utility_reading'
                    )
                    ORDER BY ur.MeterType, ur.MeterID
                """, receivable_id)
                rows = cursor.fetchall()

            # ---- 策略3：通过 MerchantID + BelongMonth + MeterType 兜底查 ----
            if not rows:
                # 先获取该应收的 MerchantID 和 Description
                cursor.execute("""
                    SELECT MerchantID, Description, ExpenseTypeID
                    FROM Receivable WHERE ReceivableID = ?
                """, receivable_id)
                recv = cursor.fetchone()
                if recv and recv.MerchantID and recv.Description:
                    # 从 Description 解析月份，格式如 "2026年01月电费（3块表）"
                    month_match = re.search(r'(\d{4}年\d{2}月)', recv.Description)
                    belong_month = month_match.group(1) if month_match else ''

                    # 判断 MeterType：Description 包含"水费"→ water，否则→ electricity
                    meter_type = 'water' if '水费' in (recv.Description or '') else 'electricity'

                    if belong_month:
                        cursor.execute(f"""
                            {UTILITY_SELECT}
                            FROM UtilityReading ur
                            {UTILITY_JOINS}
                            WHERE ur.MerchantID = ? AND ur.BelongMonth = ? AND ur.MeterType = ?
                            ORDER BY ur.MeterID
                        """, recv.MerchantID, belong_month, meter_type)
                        rows = cursor.fetchall()

            if not rows:
                return []

            result = []
            total_amount = 0
            for row in rows:
                subtotal = float(row.TotalAmount) if row.TotalAmount else 0
                total_amount += subtotal
                result.append({
                    'reading_id': row.ReadingID,
                    'meter_number': row.MeterNumber or '',
                    'meter_type': row.MeterType or '',
                    'installation_location': row.InstallationLocation or '',
                    'belong_month': row.BelongMonth or row.ReadingMonth or '',
                    'last_reading': float(row.LastReading) if row.LastReading else 0,
                    'current_reading': float(row.CurrentReading) if row.CurrentReading else 0,
                    'meter_multiplier': float(row.MeterMultiplier) if row.MeterMultiplier else 1,
                    'usage': float(row.Usage) if row.Usage else 0,
                    'unit_price': float(row.UnitPrice) if row.UnitPrice else 0,
                    'subtotal': subtotal,
                })
            # 返回列表+合计
            return {
                'items': result,
                'total_amount': total_amount
            }
    except Exception:
        return []


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
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()

        result = finance_svc.get_payables(
            page=page, per_page=per_page,
            search=search or None, status=status or None
        )

        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


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

        return jsonify({'success': True, 'message': '添加成功', 'id': new_id})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'添加失败：{str(e)}'}), 500


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
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'付款失败：{str(e)}'}), 500


@finance_bp.route('/payable/detail/<int:payable_id>', methods=['GET'])
@login_required
def payable_detail(payable_id):
    """应付详情（含付款历史）"""
    try:
        payable = finance_svc._get_payable_by_id(payable_id)
        if not payable:
            return jsonify({'success': False, 'message': '记录不存在'}), 404

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

        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取详情失败：{str(e)}'}), 500


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
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取费用类型失败：{str(e)}'}), 500


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

        return jsonify({
            'success': True,
            'data': result,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


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
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取费用类型失败：{str(e)}'}), 500


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
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


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
        return jsonify({'success': True, 'message': '创建成功', 'id': new_id})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建失败：{str(e)}'}), 500


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
        return jsonify({'success': True, 'message': '更新成功'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新失败：{str(e)}'}), 500


@finance_bp.route('/account/toggle_status/<int:account_id>', methods=['POST'])
@login_required
@check_permission('account_manage')
def account_toggle_status(account_id):
    try:
        new_status = account_svc.toggle_account_status(account_id)
        return jsonify({'success': True, 'message': f'账户已{new_status}', 'new_status': new_status})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'操作失败：{str(e)}'}), 500


@finance_bp.route('/account/summary', methods=['GET'])
@login_required
@check_permission('account_manage')
def account_summary():
    try:
        result = account_svc.get_balance_summary()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取汇总失败：{str(e)}'}), 500


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
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'记账失败：{str(e)}'}), 500


@finance_bp.route('/account/active_list', methods=['GET'])
@login_required
def account_active_list():
    """获取所有有效账户（供下拉选择用，不需要 account_manage 权限）"""
    try:
        result = account_svc.get_accounts(status='有效')
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取账户失败：{str(e)}'}), 500


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
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


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
        return jsonify({'success': True, 'message': '创建成功', 'id': new_id})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建失败：{str(e)}'}), 500


@finance_bp.route('/prepayment/detail/<int:prepayment_id>', methods=['GET'])
@login_required
@check_permission('prepayment_manage')
def prepayment_detail(prepayment_id):
    try:
        detail = prepayment_svc.get_prepayment_by_id(prepayment_id)
        if not detail:
            return jsonify({'success': False, 'message': '记录不存在'}), 404

        apply_records = prepayment_svc.get_apply_records(prepayment_id)
        detail['apply_records'] = apply_records

        return jsonify({'success': True, 'data': detail})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取详情失败：{str(e)}'}), 500


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
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'冲抵失败：{str(e)}'}), 500


@finance_bp.route('/prepayment/available', methods=['GET'])
@login_required
def prepayment_available():
    """获取可用于冲抵的预收/预付列表（供收款弹窗使用）"""
    try:
        direction = request.args.get('direction', 'income')
        customer_type = request.args.get('customer_type', 'Merchant')
        customer_id = request.args.get('customer_id', type=int)
        if not customer_id:
            return jsonify({'success': True, 'data': []})

        result = prepayment_svc.get_available_prepayments(direction, customer_type, customer_id)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


@finance_bp.route('/prepayment/summary', methods=['GET'])
@login_required
@check_permission('prepayment_manage')
def prepayment_summary():
    try:
        direction = request.args.get('direction', '').strip()
        result = prepayment_svc.get_summary(direction=direction or None)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取汇总失败：{str(e)}'}), 500


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
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


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
        return jsonify({'success': True, 'message': '收取成功', 'id': new_id})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'收取失败：{str(e)}'}), 500


@finance_bp.route('/deposit/detail/<int:deposit_id>', methods=['GET'])
@login_required
@check_permission('deposit_manage')
def deposit_detail(deposit_id):
    try:
        detail = deposit_svc.get_deposit_by_id(deposit_id)
        if not detail:
            return jsonify({'success': False, 'message': '记录不存在'}), 404

        operations = deposit_svc.get_operations(deposit_id)
        detail['operations'] = operations

        return jsonify({'success': True, 'data': detail})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取详情失败：{str(e)}'}), 500


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
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'退还失败：{str(e)}'}), 500


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
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'扣除失败：{str(e)}'}), 500


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
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'转抵失败：{str(e)}'}), 500


@finance_bp.route('/deposit/summary', methods=['GET'])
@login_required
@check_permission('deposit_manage')
def deposit_summary():
    try:
        result = deposit_svc.get_summary()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取汇总失败：{str(e)}'}), 500
