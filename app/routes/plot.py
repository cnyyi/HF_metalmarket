# -*- coding: utf-8 -*-
"""
地块管理相关路由
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pyodbc
import os
import uuid
from datetime import datetime
from config import Config

plot_bp = Blueprint('plot', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_connection():
    return pyodbc.connect(Config.ODBC_CONNECTION_STRING)


def calculate_rent(area, unit_price):
    monthly_rent = area * unit_price
    yearly_rent = monthly_rent * 12
    return monthly_rent, yearly_rent


def get_plot_types():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DictName, UnitPrice
        FROM Sys_Dictionary
        WHERE DictType = N'plot_type'
        ORDER BY SortOrder
    """)
    
    types = [(r.DictName, r.DictName, float(r.UnitPrice) if r.UnitPrice else 0) for r in cursor.fetchall()]
    conn.close()
    return types


def get_plot_types_json():
    conn = get_connection()
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
    conn.close()
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
        return jsonify({'success': False, 'message': f'获取地块类型失败: {str(e)}'})


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
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM Plot WHERE PlotNumber = ?", (plot_number,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            flash('地块编号已存在', 'danger')
            plot_types = get_plot_types()
            return render_template('plot/add.html', plot_types=plot_types)
        
        cursor.execute("""
            INSERT INTO Plot (PlotNumber, PlotName, PlotType, Area, UnitPrice, TotalPrice, MonthlyRent, YearlyRent, Location, Status, Description, ImagePath, CreateTime)
            OUTPUT INSERTED.PlotID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """, (plot_number, plot_name, plot_type, area, unit_price, total_price, monthly_rent, yearly_rent, location, status, description, image_path))
        
        plot_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        flash('地块添加成功', 'success')
        return redirect(url_for('plot.plot_list'))
        
    except Exception as e:
        flash(f'添加失败: {str(e)}', 'danger')
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
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM Plot WHERE PlotNumber = ? AND PlotID != ?", (plot_number, plot_id))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'success': False, 'message': '地块编号已被其他地块使用'})
        
        cursor.execute("""
            UPDATE Plot SET 
                PlotNumber = ?, PlotName = ?, PlotType = ?, Area = ?, UnitPrice = ?, 
                MonthlyRent = ?, YearlyRent = ?, Location = ?, 
                Status = ?, Description = ?, ImagePath = ?, UpdateTime = GETDATE()
            WHERE PlotID = ?
        """, (plot_number, plot_name, plot_type, area, unit_price, monthly_rent, yearly_rent, location, status, description, image_path, plot_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '更新成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})


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
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT ImagePath FROM Plot WHERE PlotID = ?", (plot_id,))
        row = cursor.fetchone()
        if row and row.ImagePath:
            old_path = os.path.join(os.getcwd(), row.ImagePath.lstrip('/'))
            if os.path.exists(old_path):
                os.remove(old_path)
        
        cursor.execute("UPDATE Plot SET ImagePath = ?, UpdateTime = GETDATE() WHERE PlotID = ?", (image_path, plot_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '图片上传成功', 'image_path': image_path})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'上传失败: {str(e)}'})


@plot_bp.route('/delete/<int:plot_id>', methods=['POST'])
@login_required
def delete(plot_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT ImagePath FROM Plot WHERE PlotID = ?", (plot_id,))
        row = cursor.fetchone()
        
        if row and row.ImagePath:
            full_path = os.path.join(os.getcwd(), row.ImagePath.lstrip('/'))
            if os.path.exists(full_path):
                os.remove(full_path)
        
        cursor.execute("DELETE FROM Plot WHERE PlotID = ?", (plot_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '删除成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})


@plot_bp.route('/detail/<int:plot_id>', methods=['GET'])
@login_required
def detail(plot_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT PlotID, PlotNumber, PlotName, PlotType, Area, UnitPrice, MonthlyRent, YearlyRent, Location, Status, Description, ImagePath, CreateTime, UpdateTime
            FROM Plot WHERE PlotID = ?
        """, (plot_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
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
        
        conn.close()
        return jsonify({'success': True, 'data': plot})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'})


@plot_bp.route('/list_data', methods=['GET'])
@login_required
def list_data():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        plot_type = request.args.get('plot_type', '').strip()
        
        offset = (page - 1) * per_page
        
        conn = get_connection()
        cursor = conn.cursor()
        
        where_clause = "WHERE 1=1"
        params = []
        
        if search:
            where_clause += " AND (PlotNumber LIKE ? OR PlotName LIKE ? OR Location LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        if status:
            where_clause += " AND Status = ?"
            params.append(status)
        
        if plot_type:
            where_clause += " AND PlotType = ?"
            params.append(plot_type)
        
        cursor.execute(f"SELECT COUNT(*) FROM Plot {where_clause}", params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT PlotID, PlotNumber, PlotName, PlotType, Area, UnitPrice, MonthlyRent, YearlyRent, Location, Status, ImagePath, CreateTime
            FROM Plot {where_clause}
            ORDER BY CreateTime DESC
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
            'image_path': r.ImagePath,
            'create_time': r.CreateTime.strftime('%Y-%m-%d %H:%M:%S') if r.CreateTime else None
        } for r in cursor.fetchall()]
        
        conn.close()
        
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
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'})
