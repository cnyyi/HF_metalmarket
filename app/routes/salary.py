# -*- coding: utf-8 -*-
"""工资管理路由"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.salary_service import SalaryService
from app.routes.user import check_permission, check_api_permission
from app.api_response import handle_exception

salary_bp = Blueprint('salary', __name__)
salary_svc = SalaryService()


# ==================== 工资档案 ====================

@salary_bp.route('/profile')
@check_permission('salary_view')
def profile():
    """工资档案管理页面"""
    return render_template('salary/profile.html')


@salary_bp.route('/profile/list', methods=['GET'])
@check_api_permission('salary_view')
def profile_list():
    """工资档案列表数据"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()

        result = salary_svc.get_profiles(
            page=page, per_page=per_page,
            search=search or None, status=status or None
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@salary_bp.route('/profile/add', methods=['POST'])
@check_api_permission('salary_create')
def profile_add():
    """新增工资档案"""
    try:
        data = request.json
        new_id = salary_svc.create_profile(
            user_id=data.get('user_id'),
            base_salary=data.get('base_salary', 0),
            post_salary=data.get('post_salary', 0),
            subsidy=data.get('subsidy', 0),
            insurance=data.get('insurance', 0),
            housing_fund=data.get('housing_fund', 0),
            effective_date=data.get('effective_date'),
            description=data.get('description', '')
        )
        return jsonify({'success': True, 'message': '添加成功', 'id': new_id})
    except Exception as e:
        return handle_exception(e)


@salary_bp.route('/profile/edit/<int:profile_id>', methods=['POST'])
@check_api_permission('salary_edit')
def profile_edit(profile_id):
    """编辑工资档案"""
    try:
        data = request.json
        salary_svc.update_profile(
            profile_id=profile_id,
            base_salary=data.get('base_salary'),
            post_salary=data.get('post_salary'),
            subsidy=data.get('subsidy'),
            insurance=data.get('insurance'),
            housing_fund=data.get('housing_fund'),
            status=data.get('status'),
            description=data.get('description')
        )
        return jsonify({'success': True, 'message': '更新成功'})
    except Exception as e:
        return handle_exception(e)


@salary_bp.route('/profile/delete/<int:profile_id>', methods=['POST'])
@check_api_permission('salary_delete')
def profile_delete(profile_id):
    """删除工资档案"""
    try:
        salary_svc.delete_profile(profile_id)
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return handle_exception(e)


@salary_bp.route('/profile/available_users', methods=['GET'])
@check_api_permission('salary_view')
def available_users():
    """获取没有工资档案的员工列表"""
    try:
        result = salary_svc.get_users_without_profile()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


# ==================== 月度工资 ====================

@salary_bp.route('/monthly')
@check_permission('salary_view')
def monthly():
    """月度工资核算页面"""
    return render_template('salary/monthly.html')


@salary_bp.route('/monthly/list', methods=['GET'])
@check_api_permission('salary_view')
def monthly_list():
    """月度工资列表数据"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        year_month = request.args.get('year_month', '').strip()
        status = request.args.get('status', '').strip()
        search = request.args.get('search', '').strip()

        result = salary_svc.get_salary_records(
            page=page, per_page=per_page,
            year_month=year_month or None,
            status=status or None,
            search=search or None
        )

        # 如果指定了月份，附加汇总
        summary = None
        if year_month:
            summary = salary_svc.get_monthly_summary(year_month)

        return jsonify({'success': True, 'data': result, 'summary': summary})
    except Exception as e:
        return handle_exception(e)


@salary_bp.route('/monthly/generate', methods=['POST'])
@check_api_permission('salary_create')
def monthly_generate():
    """批量生成月度工资单"""
    try:
        data = request.json
        year_month = data.get('year_month', '').strip()
        user_ids = data.get('user_ids')  # None = 全部

        result = salary_svc.generate_monthly_salary(year_month, user_ids)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return handle_exception(e)


@salary_bp.route('/monthly/edit/<int:record_id>', methods=['POST'])
@check_api_permission('salary_edit')
def monthly_edit(record_id):
    """编辑工资单"""
    try:
        data = request.json
        result = salary_svc.update_salary_record(record_id, data)
        return jsonify(result)
    except Exception as e:
        return handle_exception(e)


@salary_bp.route('/monthly/delete/<int:record_id>', methods=['POST'])
@check_api_permission('salary_delete')
def monthly_delete(record_id):
    """删除工资单"""
    try:
        salary_svc.delete_salary_record(record_id)
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return handle_exception(e)


@salary_bp.route('/monthly/detail/<int:record_id>', methods=['GET'])
@check_api_permission('salary_view')
def monthly_detail(record_id):
    """获取工资单详情"""
    try:
        row = salary_svc.get_salary_record_by_id(record_id)
        if not row:
            return jsonify({'success': False, 'message': '记录不存在'}), 404

        data = {
            'record_id': row.RecordID,
            'user_id': row.UserID,
            'real_name': row.RealName or '',
            'username': row.Username or '',
            'phone': row.Phone or '',
            'year_month': row.YearMonth or '',
            'base_salary': float(row.BaseSalary),
            'post_salary': float(row.PostSalary),
            'subsidy': float(row.Subsidy),
            'overtime_pay': float(row.OvertimePay),
            'bonus': float(row.Bonus),
            'other_income': float(row.OtherIncome),
            'gross_pay': float(row.GrossPay),
            'insurance': float(row.Insurance),
            'housing_fund': float(row.HousingFund),
            'tax': float(row.Tax),
            'deduction': float(row.Deduction),
            'total_deduction': float(row.TotalDeduction),
            'net_pay': float(row.NetPay),
            'work_days': row.WorkDays or 0,
            'actual_days': row.ActualDays or 0,
            'status': row.Status,
            'payable_id': row.PayableID,
            'description': row.Description or '',
            'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
        }
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return handle_exception(e)


# ==================== 审核与发放 ====================

@salary_bp.route('/monthly/approve/<int:record_id>', methods=['POST'])
@check_api_permission('salary_edit')
def monthly_approve(record_id):
    """审核单条工资单"""
    try:
        salary_svc.approve_salary(record_id, current_user.user_id)
        return jsonify({'success': True, 'message': '审核成功'})
    except Exception as e:
        return handle_exception(e)


@salary_bp.route('/monthly/batch_approve', methods=['POST'])
@check_api_permission('salary_edit')
def monthly_batch_approve():
    """批量审核工资单"""
    try:
        data = request.json
        record_ids = data.get('record_ids', [])
        result = salary_svc.batch_approve_salary(record_ids, current_user.user_id)
        return jsonify(result)
    except Exception as e:
        return handle_exception(e)


@salary_bp.route('/monthly/pay/<int:record_id>', methods=['POST'])
@check_api_permission('salary_create')
def monthly_pay(record_id):
    """发放工资（联动财务）"""
    try:
        data = request.json
        result = salary_svc.pay_salary(
            record_id=record_id,
            created_by=current_user.user_id,
            payment_method=data.get('payment_method', '转账'),
            transaction_date=data.get('transaction_date')
        )
        return jsonify(result)
    except Exception as e:
        return handle_exception(e)


# ==================== 工资条（员工自助） ====================

@salary_bp.route('/payslip')
@login_required
def payslip():
    """我的工资条页面"""
    return render_template('salary/payslip.html')


@salary_bp.route('/payslip/list', methods=['GET'])
@login_required
def payslip_list():
    """获取当前用户的工资条"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)

        result = salary_svc.get_my_salary_records(
            user_id=current_user.user_id,
            page=page, per_page=per_page
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


# ==================== 辅助接口 ====================

@salary_bp.route('/available_months', methods=['GET'])
@login_required
def available_months():
    """获取已有工资记录的月份列表"""
    try:
        months = salary_svc.get_available_months()
        return jsonify({'success': True, 'data': months})
    except Exception as e:
        return handle_exception(e)
