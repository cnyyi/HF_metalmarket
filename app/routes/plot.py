# -*- coding: utf-8 -*-
"""
地块管理相关路由
"""
import logging
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from app.api_response import success_response, error_response
from app.services.plot_service import PlotService

logger = logging.getLogger(__name__)

plot_bp = Blueprint('plot', __name__)


@plot_bp.route('/list')
@login_required
def plot_list():
    plot_types = PlotService.get_plot_types()
    return render_template('plot/list.html', plot_types=plot_types)


@plot_bp.route('/types', methods=['GET'])
@login_required
def types():
    try:
        types = PlotService.get_plot_types_json()
        return jsonify({'success': True, 'data': types})
    except Exception as e:
        logger.error(f"获取地块类型失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': '获取地块类型失败，请稍后重试'})


@plot_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'GET':
        plot_types = PlotService.get_plot_types()
        return render_template('plot/add.html', plot_types=plot_types)
    
    try:
        plot_number = request.form.get('plot_code', '').strip()
        plot_name = request.form.get('plot_name', '').strip()
        plot_type = request.form.get('plot_type', '').strip()
        area = request.form.get('area')
        unit_price = request.form.get('price')
        location = request.form.get('location', '').strip() if request.form.get('location') else None
        status = request.form.get('status', '空闲')
        description = request.form.get('description', '').strip() if request.form.get('description') else None
        
        if not plot_number:
            flash('地块编号不能为空', 'danger')
            plot_types = PlotService.get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        if not plot_name:
            flash('地块名称不能为空', 'danger')
            plot_types = PlotService.get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        if not plot_type:
            flash('地块类型不能为空', 'danger')
            plot_types = PlotService.get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        if not area:
            flash('面积不能为空', 'danger')
            plot_types = PlotService.get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        if not unit_price:
            flash('单价不能为空', 'danger')
            plot_types = PlotService.get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        
        area = float(area)
        unit_price = float(unit_price)
        
        if area <= 0:
            flash('面积必须大于0', 'danger')
            plot_types = PlotService.get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        
        if unit_price <= 0:
            flash('单价必须大于0', 'danger')
            plot_types = PlotService.get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        
        image_path = None
        file = request.files.get('image')
        if file and file.filename != '':
            image_path = PlotService.save_uploaded_file(file)
        
        success, result = PlotService.add_plot(
            plot_number, plot_name, plot_type, area, unit_price, 
            location, status, description, image_path
        )
        
        if not success:
            flash(result, 'danger')
            plot_types = PlotService.get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        
        flash('地块添加成功', 'success')
        return redirect(url_for('plot.plot_list'))
        
    except Exception as e:
        logger.error(f"添加地块失败: {e}", exc_info=True)
        flash('添加失败，请稍后重试', 'danger')
        plot_types = PlotService.get_plot_types()
        return render_template('plot/add.html', plot_types=plot_types)


@plot_bp.route('/edit/<int:plot_id>', methods=['GET', 'POST'])
@login_required
def edit(plot_id):
    if request.method == 'GET':
        plot_types = PlotService.get_plot_types()
        return render_template('plot/edit.html', plot_types=plot_types, plot_id=plot_id)
    
    try:
        data = request.get_json()
        
        plot_number = data.get('plot_code', '').strip()
        plot_name = data.get('plot_name', '').strip()
        plot_type = data.get('plot_type', '').strip()
        area = data.get('area')
        unit_price = data.get('price')
        location = data.get('location', '').strip() if data.get('location') else None
        status = data.get('status', '空闲')
        description = data.get('description', '').strip() if data.get('description') else None
        image_path = data.get('image_path', '').strip() if data.get('image_path') else None
        
        if not plot_number:
            return error_response('地块编号不能为空')
        if not plot_name:
            return error_response('地块名称不能为空')
        if not plot_type:
            return error_response('地块类型不能为空')
        if not area:
            return error_response('面积不能为空')
        if not unit_price:
            return error_response('单价不能为空')
        
        area = float(area)
        unit_price = float(unit_price)
        
        success, message = PlotService.update_plot(
            plot_id, plot_number, plot_name, plot_type, area, unit_price, 
            location, status, description, image_path
        )
        
        if not success:
            return error_response(message)
        
        return success_response(message=message)
        
    except Exception as e:
        logger.error(f"更新地块失败: {e}", exc_info=True)
        return error_response('更新失败，请稍后重试', status=500)


@plot_bp.route('/upload_image/<int:plot_id>', methods=['POST'])
@login_required
def upload_image(plot_id):
    try:
        file = request.files.get('image')
        if not file or file.filename == '':
            return error_response('请选择图片文件')
        
        image_path = PlotService.save_uploaded_file(file)
        if not image_path:
            return error_response('图片上传失败')
        
        success, message = PlotService.upload_image(plot_id, image_path)
        if not success:
            return error_response(message)
        
        return success_response(
            {'image_path': image_path},
            message=message,
            image_path=image_path
        )
        
    except Exception as e:
        logger.error(f"上传图片失败: {e}", exc_info=True)
        return error_response('上传失败，请稍后重试', status=500)


@plot_bp.route('/delete/<int:plot_id>', methods=['POST'])
@login_required
def delete(plot_id):
    try:
        success, message = PlotService.delete_plot(plot_id)
        if not success:
            return error_response(message)
        
        return success_response(message=message)
        
    except Exception as e:
        logger.error(f"删除地块失败: {e}", exc_info=True)
        return error_response('删除失败，请稍后重试', status=500)


@plot_bp.route('/detail/<int:plot_id>', methods=['GET'])
@login_required
def detail(plot_id):
    try:
        success, result = PlotService.get_plot_detail(plot_id)
        if not success:
            return error_response(result)
        
        return success_response(result)
        
    except Exception as e:
        logger.error(f"获取地块详情失败: {e}", exc_info=True)
        return error_response('获取失败，请稍后重试', status=500)


@plot_bp.route('/list_data', methods=['GET'])
@login_required
def list_data():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        plot_type = request.args.get('plot_type', '').strip()
        rent_status = request.args.get('rent_status', '').strip()
        sort_by = request.args.get('sort_by', '').strip()
        sort_dir = request.args.get('sort_dir', 'asc').strip().lower()
        
        success, result = PlotService.get_plot_list(
            page, per_page, search, status, plot_type, rent_status, sort_by, sort_dir
        )
        
        if not success:
            return error_response(result)
        
        return success_response(result)
        
    except Exception as e:
        logger.error(f"获取地块列表失败: {e}", exc_info=True)
        return error_response('获取失败，请稍后重试', status=500)
