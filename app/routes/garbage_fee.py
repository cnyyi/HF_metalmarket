# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from app.routes.user import check_permission
from app.services.garbage_fee_service import GarbageFeeService
from app.api_response import handle_exception

garbage_fee_bp = Blueprint('garbage_fee', __name__)
garbage_fee_svc = GarbageFeeService()


@garbage_fee_bp.route('/')
@login_required
@check_permission('garbage_fee_view')
def index():
    return render_template('garbage_fee/list.html')


@garbage_fee_bp.route('/list')
@login_required
@check_permission('garbage_fee_view')
def fee_list():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        year = request.args.get('year', '').strip()
        business_type = request.args.get('business_type', '').strip()
        status = request.args.get('status', '').strip()
        search = request.args.get('search', '').strip()

        result = garbage_fee_svc.get_list(
            page=page, per_page=per_page,
            year=year or None,
            business_type=business_type or None,
            status=status or None,
            search=search or None,
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/generate')
@login_required
@check_permission('garbage_fee_create')
def generate_page():
    return render_template('garbage_fee/generate.html')


@garbage_fee_bp.route('/generate', methods=['POST'])
@login_required
@check_permission('garbage_fee_create')
def generate():
    try:
        data = request.json
        year = data.get('year')
        if not year:
            raise ValueError("请选择年度")
        result = garbage_fee_svc.batch_generate(
            year=int(year),
            created_by=current_user.user_id,
        )
        return jsonify({'success': True, 'message': f"生成完成：成功{result['success_count']}条，跳过{result['skip_count']}条", 'data': result})
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/preview')
@login_required
@check_permission('garbage_fee_create')
def preview():
    try:
        year = request.args.get('year', '').strip()
        if not year:
            raise ValueError("请选择年度")
        result = garbage_fee_svc.get_preview(year=int(year))
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/edit/<int:garbage_fee_id>', methods=['POST'])
@login_required
@check_permission('garbage_fee_edit')
def update_fee(garbage_fee_id):
    try:
        data = request.json
        result = garbage_fee_svc.update_fee(
            garbage_fee_id=garbage_fee_id,
            rental_area=data.get('rental_area'),
            unit_price=data.get('unit_price'),
            min_amount=data.get('min_amount'),
            final_fee=data.get('final_fee'),
            status=data.get('status'),
            description=data.get('description', '').strip() or None,
            updated_by=current_user.user_id,
        )
        return jsonify({'success': True, 'message': '更新成功', 'data': result})
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/detail/<int:garbage_fee_id>')
@login_required
@check_permission('garbage_fee_view')
def detail(garbage_fee_id):
    return render_template('garbage_fee/detail.html', garbage_fee_id=garbage_fee_id)


@garbage_fee_bp.route('/detail/<int:garbage_fee_id>/data')
@login_required
@check_permission('garbage_fee_view')
def detail_data(garbage_fee_id):
    try:
        data = garbage_fee_svc.get_detail(garbage_fee_id)
        if not data:
            return jsonify({'success': False, 'message': '垃圾费记录不存在'}), 404
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/delete/<int:garbage_fee_id>', methods=['POST'])
@login_required
@check_permission('garbage_fee_delete')
def delete(garbage_fee_id):
    try:
        garbage_fee_svc.delete_fee(garbage_fee_id)
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/export')
@login_required
@check_permission('garbage_fee_view')
def export():
    try:
        year = request.args.get('year', '').strip()
        business_type = request.args.get('business_type', '').strip()
        status = request.args.get('status', '').strip()
        search = request.args.get('search', '').strip()

        output, filename = garbage_fee_svc.export_fees(
            year=year or None,
            business_type=business_type or None,
            status=status or None,
            search=search or None,
        )
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/business-types')
@login_required
@check_permission('garbage_fee_view')
def business_types():
    try:
        result = garbage_fee_svc.get_business_types()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)


@garbage_fee_bp.route('/status-options')
@login_required
@check_permission('garbage_fee_view')
def status_options():
    try:
        result = garbage_fee_svc.get_status_options()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return handle_exception(e)
