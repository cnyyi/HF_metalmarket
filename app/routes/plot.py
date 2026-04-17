# -*- coding: utf-8 -*-
"""
地块管理相关路由
"""
import logging
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from utils.database import DBConnection
from config.base import Config

logger = logging.getLogger(__name__)

plot_bp = Blueprint('plot', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def calculate_rent(area, unit_price):
    monthly_rent = area * unit_price
    yearly_rent = monthly_rent * 12
    return monthly_rent, yearly_rent


def get_plot_types():
    with DBConnection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DictName, UnitPrice
            FROM Sys_Dictionary
            WHERE DictType = N'plot_type'
            ORDER BY SortOrder
        """)
        
        types = [(r.DictName, r.DictName, float(r.UnitPrice) if r.UnitPrice else 0) for r in cursor.fetchall()]
    
    return types


def get_plot_types_json():
    with DBConnection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DictName, UnitPrice
            FROM Sys_Dictionary
            WHERE DictType = N'plot_type'
            ORDER BY SortOrder
        """)
        
        types = [{
            'dict_name': r.DictName,
            'unit_price': float(r.UnitPrice) if r.UnitPrice else 0
        } for r in cursor.fetchall()]
    
    return types


def save_uploaded_file(file):
    if not file or not allowed_file(file.filename):
        return None
    
    original_name = secure_filename(file.filename)
    ext = original_name.rsplit('.', 1)[1].lower()
    new_filename = f"{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}.{ext}"
    
    upload_folder = os.path.join(Config.UPLOAD_FOLDER, 'plot')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    file_path = os.path.join(upload_folder, new_filename)
    file.save(file_path)
    
    relative_path = f"/uploads/plot/{new_filename}"
    return relative_path


def _safe_delete_image(image_path_relative):
    """
    安全删除上传的图片（带路径遍历防护）
    
    Args:
        image_path_relative: 相对路径，如 /uploads/plot/xxx.png
    """
    if not image_path_relative:
        return
    
    # 安全校验：确保路径在 uploads 目录内，防止路径遍历攻击
    # 只允许 uploads/ 目录下的文件被删除
    safe_prefix = '/uploads/'
    if not image_path_relative.startswith(safe_prefix):
        logger.warning(f"尝试删除非uploads目录的文件: {image_path_relative}")
        return

    full_path = os.path.join(Config.UPLOAD_FOLDER, image_path_relative[len(safe_prefix):])

    # 二次验证：规范化后仍在 uploads 目录内
    resolved_path = os.path.realpath(full_path)
    upload_real = os.path.realpath(Config.UPLOAD_FOLDER)
    if not resolved_path.startswith(upload_real):
        logger.warning(f"路径遍历尝试被拦截: {image_path_relative} -> {resolved_path}")
        return

    if os.path.exists(resolved_path):
        try:
            os.remove(resolved_path)
        except OSError as e:
            logger.warning(f"删除图片失败: {e}")


@plot_bp.route('/list')
@login_required
def plot_list():
    plot_types = get_plot_types()
    return render_template('plot/list.html', plot_types=plot_types)


@plot_bp.route('/types', methods=['GET'])
@login_required
def types():
    try:
        types = get_plot_types_json()
        return jsonify({'success': True, 'data': types})
    except Exception as e:
        logger.error(f"获取地块类型失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': '获取地块类型失败，请稍后重试'})


@plot_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'GET':
        plot_types = get_plot_types()
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
            plot_types = get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        if not plot_name:
            flash('地块名称不能为空', 'danger')
            plot_types = get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        if not plot_type:
            flash('地块类型不能为空', 'danger')
            plot_types = get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        if not area:
            flash('面积不能为空', 'danger')
            plot_types = get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        if not unit_price:
            flash('单价不能为空', 'danger')
            plot_types = get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        
        area = float(area)
        unit_price = float(unit_price)
        
        if area <= 0:
            flash('面积必须大于0', 'danger')
            plot_types = get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        
        if unit_price <= 0:
            flash('单价必须大于0', 'danger')
            plot_types = get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        
        total_price = area * unit_price
        monthly_rent, yearly_rent = calculate_rent(area, unit_price)
        
        image_path = None
        file = request.files.get('image')
        if file and file.filename != '':
            image_path = save_uploaded_file(file)
        
        with DBConnection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM Plot WHERE PlotNumber = ?", (plot_number,))
            if cursor.fetchone()[0] > 0:
                flash('地块编号已存在', 'danger')
                plot_types = get_plot_types()
                return render_template('plot/add.html', plot_types=plot_types)
            
            cursor.execute("""
                INSERT INTO Plot (PlotNumber, PlotName, PlotType, Area, UnitPrice, TotalPrice, MonthlyRent, YearlyRent, Location, Status, Description, ImagePath, CreateTime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (plot_number, plot_name, plot_type, area, unit_price, total_price, monthly_rent, yearly_rent, location, status, description, image_path))

            cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
            plot_id = cursor.fetchone()[0]
            conn.commit()
        
        flash('地块添加成功', 'success')
        return redirect(url_for('plot.plot_list'))
        
    except Exception as e:
        logger.error(f"添加地块失败: {e}", exc_info=True)
        flash('添加失败，请稍后重试', 'danger')
        plot_types = get_plot_types()
        return render_template('plot/add.html', plot_types=plot_types)


@plot_bp.route('/edit/<int:plot_id>', methods=['GET', 'POST'])
@login_required
def edit(plot_id):
    if request.method == 'GET':
        plot_types = get_plot_types()
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
            return jsonify({'success': False, 'message': '地块编号不能为空'})
        if not plot_name:
            return jsonify({'success': False, 'message': '地块名称不能为空'})
        if not plot_type:
            return jsonify({'success': False, 'message': '地块类型不能为空'})
        if not area:
            return jsonify({'success': False, 'message': '面积不能为空'})
        if not unit_price:
            return jsonify({'success': False, 'message': '单价不能为空'})
        
        area = float(area)
        unit_price = float(unit_price)
        monthly_rent, yearly_rent = calculate_rent(area, unit_price)
        
        with DBConnection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM Plot WHERE PlotNumber = ? AND PlotID != ?", (plot_number, plot_id))
            if cursor.fetchone()[0] > 0:
                return jsonify({'success': False, 'message': '地块编号已被其他地块使用'})
            
            cursor.execute("""
                UPDATE Plot SET 
                    PlotNumber = ?, PlotName = ?, PlotType = ?, Area = ?, UnitPrice = ?, 
                    MonthlyRent = ?, YearlyRent = ?, Location = ?, 
                    Status = ?, Description = ?, ImagePath = ?, UpdateTime = GETDATE()
                WHERE PlotID = ?
            """, (plot_number, plot_name, plot_type, area, unit_price, monthly_rent, yearly_rent, location, status, description, image_path, plot_id))
            
            conn.commit()
        
        return jsonify({'success': True, 'message': '更新成功'})
        
    except Exception as e:
        logger.error(f"更新地块失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': '更新失败，请稍后重试'})


@plot_bp.route('/upload_image/<int:plot_id>', methods=['POST'])
@login_required
def upload_image(plot_id):
    try:
        file = request.files.get('image')
        if not file or file.filename == '':
            return jsonify({'success': False, 'message': '请选择图片文件'})
        
        image_path = save_uploaded_file(file)
        if not image_path:
            return jsonify({'success': False, 'message': '图片上传失败'})
        
        with DBConnection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT ImagePath FROM Plot WHERE PlotID = ?", (plot_id,))
            row = cursor.fetchone()
            if row and row.ImagePath:
                _safe_delete_image(row.ImagePath)
            
            cursor.execute("UPDATE Plot SET ImagePath = ?, UpdateTime = GETDATE() WHERE PlotID = ?", (image_path, plot_id))
            conn.commit()
        
        return jsonify({'success': True, 'message': '图片上传成功', 'image_path': image_path})
        
    except Exception as e:
        logger.error(f"上传图片失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': '上传失败，请稍后重试'})


@plot_bp.route('/delete/<int:plot_id>', methods=['POST'])
@login_required
def delete(plot_id):
    try:
        with DBConnection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT ImagePath FROM Plot WHERE PlotID = ?", (plot_id,))
            row = cursor.fetchone()
            
            if row and row.ImagePath:
                _safe_delete_image(row.ImagePath)
            
            cursor.execute("DELETE FROM Plot WHERE PlotID = ?", (plot_id,))
            
            conn.commit()
        
        return jsonify({'success': True, 'message': '删除成功'})
        
    except Exception as e:
        logger.error(f"删除地块失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': '删除失败，请稍后重试'})


@plot_bp.route('/detail/<int:plot_id>', methods=['GET'])
@login_required
def detail(plot_id):
    try:
        with DBConnection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT PlotID, PlotNumber, PlotName, PlotType, Area, UnitPrice, MonthlyRent, YearlyRent, Location, Status, Description, ImagePath, CreateTime, UpdateTime
                FROM Plot WHERE PlotID = ?
            """, (plot_id,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({'success': False, 'message': '地块不存在'})
            
            plot = {
                'plot_id': row.PlotID,
                'plot_code': row.PlotNumber,
                'plot_name': row.PlotName,
                'plot_type': row.PlotType,
                'area': float(row.Area) if row.Area else 0,
                'price': float(row.UnitPrice) if row.UnitPrice else 0,
                'monthly_rent': float(row.MonthlyRent) if row.MonthlyRent else 0,
                'yearly_rent': float(row.YearlyRent) if row.YearlyRent else 0,
                'location': row.Location,
                'status': row.Status,
                'description': row.Description,
                'image_path': row.ImagePath,
                'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M:%S') if row.CreateTime else None,
                'update_time': row.UpdateTime.strftime('%Y-%m-%d %H:%M:%S') if row.UpdateTime else None
            }
            
            images = []
            if row.ImagePath:
                images.append({
                    'file_path': row.ImagePath,
                    'original_name': row.ImagePath.split('/')[-1]
                })
            plot['images'] = images
        
        return jsonify({'success': True, 'data': plot})
        
    except Exception as e:
        logger.error(f"获取地块详情失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': '获取失败，请稍后重试'})


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
        
        allowed_sort = {
            'plot_code': 'p.PlotNumber',
            'plot_type': 'p.PlotType',
            'rent_status': 'RentStatus',
            'area': 'p.Area'
        }
        order_clause = 'p.CreateTime DESC'
        if sort_by in allowed_sort:
            col = allowed_sort[sort_by]
            direction = 'DESC' if sort_dir == 'desc' else 'ASC'
            order_clause = f'{col} {direction}'
        
        offset = (page - 1) * per_page
        
        with DBConnection() as conn:
            cursor = conn.cursor()
            
            where_clause = "WHERE 1=1"
            params = []
            
            if search:
                where_clause += " AND (p.PlotNumber LIKE ? OR p.PlotName LIKE ? OR p.Location LIKE ?)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])
            
            if status:
                where_clause += " AND p.Status = ?"
                params.append(status)
            
            if plot_type:
                where_clause += " AND p.PlotType = ?"
                params.append(plot_type)
            
            # 租赁状态筛选（注意：StartDate/EndDate 是 DATE 类型，需用 CAST(GETDATE() AS DATE) 比较）
            if rent_status == '租赁中':
                where_clause += " AND EXISTS (SELECT 1 FROM ContractPlot cp INNER JOIN Contract c ON cp.ContractID = c.ContractID WHERE cp.PlotID = p.PlotID AND c.StartDate <= CAST(GETDATE() AS DATE) AND c.EndDate >= CAST(GETDATE() AS DATE) AND c.Status <> N'已终止')"
            elif rent_status == '空闲':
                where_clause += " AND NOT EXISTS (SELECT 1 FROM ContractPlot cp INNER JOIN Contract c ON cp.ContractID = c.ContractID WHERE cp.PlotID = p.PlotID AND c.StartDate <= CAST(GETDATE() AS DATE) AND c.EndDate >= CAST(GETDATE() AS DATE) AND c.Status <> N'已终止')"
            
            cursor.execute(f"""
                SELECT COUNT(*) FROM Plot p {where_clause}
            """, params)
            total = cursor.fetchone()[0]
            
            cursor.execute(f"""
                SELECT p.PlotID, p.PlotNumber, p.PlotName, p.PlotType, p.Area, p.UnitPrice, 
                       p.MonthlyRent, p.YearlyRent, p.Location, p.Status, p.ImagePath, p.CreateTime,
                       CASE WHEN EXISTS (
                           SELECT 1 FROM ContractPlot cp 
                           INNER JOIN Contract c ON cp.ContractID = c.ContractID 
                           WHERE cp.PlotID = p.PlotID 
                             AND c.StartDate <= CAST(GETDATE() AS DATE) 
                             AND c.EndDate >= CAST(GETDATE() AS DATE) 
                             AND c.Status <> N'已终止'
                       ) THEN N'租赁中' ELSE N'空闲' END AS RentStatus
                FROM Plot p {where_clause}
                ORDER BY {order_clause}
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, params + [offset, per_page])
            
            plots = [{
                'plot_id': r.PlotID,
                'plot_code': r.PlotNumber,
                'plot_name': r.PlotName,
                'plot_type': r.PlotType,
                'area': float(r.Area) if r.Area else 0,
                'price': float(r.UnitPrice) if r.UnitPrice else 0,
                'monthly_rent': float(r.MonthlyRent) if r.MonthlyRent else 0,
                'yearly_rent': float(r.YearlyRent) if r.YearlyRent else 0,
                'location': r.Location,
                'status': r.Status,
                'rent_status': r.RentStatus,
                'image_path': r.ImagePath,
                'create_time': r.CreateTime.strftime('%Y-%m-%d %H:%M:%S') if r.CreateTime else None
            } for r in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'data': {
                'plots': plots,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"获取地块列表失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': '获取失败，请稍后重试'})
