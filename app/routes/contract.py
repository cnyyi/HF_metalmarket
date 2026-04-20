# -*- coding: utf-8 -*-
"""
合同管理相关路由
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import login_required
from app.api_response import success_response, error_response
from app.services.contract_service import ContractService

contract_bp = Blueprint('contract', __name__)


@contract_bp.route('/list')
@login_required
def contract_list():
    return render_template('contract/list.html')


@contract_bp.route('/list_data', methods=['GET'])
@login_required
def list_data():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '').strip()
        
        success, result = ContractService.get_contract_list(page, per_page, search)
        if not success:
            return error_response(result)
        
        return success_response(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@contract_bp.route('/generate/<int:contract_id>', methods=['POST'])
@login_required
def generate_doc(contract_id):
    """生成合同文档"""
    try:
        from app.services.contract_doc_service import contract_doc_service
        
        # 生成合同
        result = contract_doc_service.generate_contract_doc(contract_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'file_name': result['file_name']
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@contract_bp.route('/download/<path:file_name>', methods=['GET'])
@login_required
def download_doc(file_name):
    """下载合同文档"""
    try:
        from app.services.contract_doc_service import contract_doc_service
        
        # 获取文件
        file_info = contract_doc_service.download_contract(file_name)
        
        if not file_info:
            return jsonify({'success': False, 'message': '文件不存在'}), 404
        
        file_path, safe_file_name = file_info
        
        # 发送文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=safe_file_name,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@contract_bp.route('/periods', methods=['GET'])
@login_required
def periods():
    try:
        period_list = ContractService.get_contract_periods()
        return jsonify({'success': True, 'data': period_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@contract_bp.route('/merchants/<period>', methods=['GET'])
@login_required
def merchants(period):
    try:
        merchant_list = ContractService.get_available_merchants(period)
        return jsonify({'success': True, 'data': merchant_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@contract_bp.route('/plots/<period>', methods=['GET'])
@login_required
def plots(period):
    try:
        plot_list = ContractService.get_available_plots(period)
        return jsonify({'success': True, 'data': plot_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@contract_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'GET':
        period_list = ContractService.get_contract_periods()
        return render_template('contract/add.html', periods=period_list)
    
    try:
        data = request.get_json()
        
        period = data.get('period')
        merchant_id = data.get('merchant_id')
        plot_ids = data.get('plot_ids', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        rent_adjust = data.get('rent_adjust', 0)
        description = data.get('description', '')
        
        if not period:
            return error_response('请选择合同期年')
        if not merchant_id:
            return error_response('请选择商户')
        if not plot_ids:
            return error_response('请选择地块')
        if not start_date:
            return error_response('请选择开始日期')
        if not end_date:
            return error_response('请选择结束日期')
        
        success, result = ContractService.add_contract(
            period, merchant_id, plot_ids, start_date, end_date, rent_adjust, description
        )
        
        if not success:
            return error_response(result)
        
        return success_response(
            {'contract_number': result},
            message='合同添加成功',
            contract_number=result
        )
            
    except Exception as e:
        return error_response(str(e), status=500)


@contract_bp.route('/detail/<int:contract_id>', methods=['GET'])
@login_required
def detail(contract_id):
    try:
        success, result = ContractService.get_contract_detail(contract_id)
        if not success:
            return error_response(result)
        
        return success_response(result)
        
    except Exception as e:
        return error_response(str(e), status=500)


@contract_bp.route('/edit/<int:contract_id>', methods=['GET', 'POST'])
@login_required
def edit(contract_id):
    if request.method == 'GET':
        period_list = ContractService.get_contract_periods()
        return render_template('contract/edit.html', contract_id=contract_id, periods=period_list)
    
    try:
        data = request.get_json()
        
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        rent_adjust = data.get('rent_adjust', 0)
        description = data.get('description', '')
        status = data.get('status', '有效')
        plot_ids = data.get('plot_ids', [])
        
        if not start_date:
            return error_response('请选择开始日期')
        if not end_date:
            return error_response('请选择结束日期')
        
        success, message = ContractService.update_contract(
            contract_id, start_date, end_date, rent_adjust, description, status, plot_ids
        )
        
        if not success:
            return error_response(message)
        
        return success_response(message=message)
            
    except Exception as e:
        return error_response(str(e), status=500)


@contract_bp.route('/delete/<int:contract_id>', methods=['POST'])
@login_required
def delete(contract_id):
    try:
        success, message = ContractService.delete_contract(contract_id)
        if not success:
            return error_response(message)
        
        return success_response(message=message)
        
    except Exception as e:
        return error_response(str(e), status=500)
