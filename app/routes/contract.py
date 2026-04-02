# -*- coding: utf-8 -*-
"""
合同管理相关路由
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
import pyodbc
import re
from datetime import datetime
from config import Config

contract_bp = Blueprint('contract', __name__)


def get_connection():
    return pyodbc.connect(Config.ODBC_CONNECTION_STRING)


def get_contract_periods():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DictName
        FROM Sys_Dictionary
        WHERE DictType = N'contract_period'
        ORDER BY SortOrder
    """)
    
    periods = [r.DictName for r in cursor.fetchall()]
    conn.close()
    return periods


def get_available_merchants(period):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.MerchantID, m.MerchantName
        FROM Merchant m
        WHERE m.MerchantID NOT IN (
            SELECT MerchantID FROM Contract
            WHERE ContractPeriod = ?
        )
        ORDER BY m.MerchantName
    """, (period,))
    
    merchants = [{
        'merchant_id': r.MerchantID,
        'merchant_name': r.MerchantName
    } for r in cursor.fetchall()]
    conn.close()
    return merchants


def get_available_plots(period):
    conn = get_connection()
    cursor = conn.cursor()
    
    # 查询可用地块，排除已被占用（结束日期 > 当前日期 -1 个月）的地块
    cursor.execute("""
        SELECT p.PlotID, p.PlotNumber, p.PlotName, p.Area, p.UnitPrice, p.MonthlyRent, p.YearlyRent, p.ImagePath
        FROM Plot p
        WHERE p.PlotID NOT IN (
            SELECT cp.PlotID 
            FROM ContractPlot cp
            INNER JOIN Contract c ON cp.ContractID = c.ContractID
            WHERE c.EndDate > DATEADD(MONTH, -1, GETDATE())
        )
        ORDER BY p.PlotNumber
    """)
    
    plots = [{
        'plot_id': r.PlotID,
        'plot_number': r.PlotNumber,
        'plot_name': r.PlotName,
        'area': float(r.Area) if r.Area else 0,
        'unit_price': float(r.UnitPrice) if r.UnitPrice else 0,
        'monthly_rent': float(r.MonthlyRent) if r.MonthlyRent else 0,
        'yearly_rent': float(r.YearlyRent) if r.YearlyRent else 0,
        'image_path': r.ImagePath
    } for r in cursor.fetchall()]
    conn.close()
    return plots


def generate_contract_number(period, merchant_id):
    match = re.search(r'第(\d+)期第(\d+)年', period)
    if match:
        period_code = match.group(1) + match.group(2)
    else:
        return None
    
    date_str = datetime.now().strftime('%Y%m%d')
    merchant_id_padded = str(merchant_id).zfill(3)
    return f"ZTHYHT{period_code}{date_str}{merchant_id_padded}"


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
        
        offset = (page - 1) * per_page
        
        conn = get_connection()
        cursor = conn.cursor()
        
        where_clause = "WHERE 1=1"
        params = []
        
        if search:
            where_clause += " AND (c.ContractNumber LIKE ? OR m.MerchantName LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param])
        
        cursor.execute(f"SELECT COUNT(*) FROM Contract c LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID {where_clause}", params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT c.ContractID, c.ContractNumber, c.ActualAmount as ActualAmount, m.MerchantName, m.ContactPerson,
                   c.StartDate, c.EndDate, c.Status, c.CreateTime,
                   (SELECT COUNT(*) FROM ContractPlot cp WHERE cp.ContractID = c.ContractID) as PlotCount
            FROM Contract c
            LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
            {where_clause}
            ORDER BY c.CreateTime DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, params + [offset, per_page])
        
        contracts = []
        for r in cursor.fetchall():
            actual_amount_val = r.ActualAmount if hasattr(r, 'ActualAmount') else (r[2] if len(r) > 2 else 0)
            contracts.append({
                'contract_id': r.ContractID,
                'contract_number': r.ContractNumber,
                'actual_amount': float(actual_amount_val) if actual_amount_val is not None else 0,
                'merchant_name': r.MerchantName or '-',
                'contact_person': r.ContactPerson or '-',
                'plot_count': r.PlotCount,
                'start_date': r.StartDate.strftime('%Y-%m-%d') if r.StartDate else None,
                'end_date': r.EndDate.strftime('%Y-%m-%d') if r.EndDate else None,
                'status': r.Status or '有效',
                'create_time': r.CreateTime.strftime('%Y-%m-%d %H:%M:%S') if r.CreateTime else None
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'contracts': contracts,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
        
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
        from flask import send_file
        
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
        period_list = get_contract_periods()
        return jsonify({'success': True, 'data': period_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@contract_bp.route('/merchants/<period>', methods=['GET'])
@login_required
def merchants(period):
    try:
        merchant_list = get_available_merchants(period)
        return jsonify({'success': True, 'data': merchant_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@contract_bp.route('/plots/<period>', methods=['GET'])
@login_required
def plots(period):
    try:
        plot_list = get_available_plots(period)
        return jsonify({'success': True, 'data': plot_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@contract_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'GET':
        period_list = get_contract_periods()
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
            return jsonify({'success': False, 'message': '请选择合同期年'})
        if not merchant_id:
            return jsonify({'success': False, 'message': '请选择商户'})
        if not plot_ids:
            return jsonify({'success': False, 'message': '请选择地块'})
        if not start_date:
            return jsonify({'success': False, 'message': '请选择开始日期'})
        if not end_date:
            return jsonify({'success': False, 'message': '请选择结束日期'})
        
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        if end_date_obj <= start_date_obj:
            return jsonify({'success': False, 'message': '结束日期必须晚于开始日期'})
        
        contract_number = generate_contract_number(period, merchant_id)
        if not contract_number:
            return jsonify({'success': False, 'message': f'合同编号生成失败，period格式错误： {period}'})
        
        contract_name = f"{period}-{merchant_id}号合同"
        
        total_rent = 0
        conn = get_connection()
        cursor = conn.cursor()
        
        for plot_id in plot_ids:
            cursor.execute("SELECT YearlyRent, UnitPrice, Area FROM Plot WHERE PlotID = ?", (int(plot_id),))
            result = cursor.fetchone()
            if result and result.YearlyRent:
                total_rent += float(result.YearlyRent)
        
        try:
            cursor.execute("""
                INSERT INTO Contract (
                    ContractNumber, ContractName, MerchantID, ContractPeriod, StartDate, EndDate,
                    ContractAmount, AmountReduction, ActualAmount, PaymentMethod, ContractPeriodYear, BusinessType, Status, Description, CreateTime
                ) OUTPUT INSERTED.ContractID
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                contract_number,
                contract_name,
                merchant_id,
                period,
                start_date_obj,
                end_date_obj,
                total_rent,
                rent_adjust,
                total_rent + rent_adjust,
                '银行转账',
                1,
                '租赁',
                '有效',
                description
            ))
            
            result = cursor.fetchone()
            contract_id = result[0] if result else None
            
            if contract_id:
                for plot_id in plot_ids:
                    cursor.execute("SELECT UnitPrice, Area FROM Plot WHERE PlotID = ?", (int(plot_id),))
                    plot_result = cursor.fetchone()
                    unit_price = float(plot_result.UnitPrice) if plot_result and plot_result.UnitPrice else 0
                    area = float(plot_result.Area) if plot_result and plot_result.Area else 0
                    monthly_price = unit_price * area
                    
                    cursor.execute("""
                        INSERT INTO ContractPlot (ContractID, PlotID, UnitPrice, Area, MonthlyPrice)
                        VALUES (?, ?, ?, ?, ?)
                    """, (contract_id, int(plot_id), unit_price, area, monthly_price))
            
            conn.commit()
            return jsonify({'success': True, 'message': '合同添加成功', 'contract_number': contract_number})
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': str(e)})
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@contract_bp.route('/detail/<int:contract_id>', methods=['GET'])
@login_required
def detail(contract_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.ContractID, c.ContractNumber, c.ContractName, c.MerchantID, m.MerchantName, m.ContactPerson,
                   c.ContractPeriod, c.StartDate, c.EndDate, c.ContractAmount, c.AmountReduction,
                   c.ActualAmount, c.Status, c.Description, c.CreateTime
            FROM Contract c
            LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
            WHERE c.ContractID = ?
        """, (contract_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'success': False, 'message': '合同不存在'})
        
        contract = {
            'contract_id': row.ContractID,
            'contract_number': row.ContractNumber,
            'contract_name': row.ContractName,
            'merchant_id': row.MerchantID,
            'merchant_name': row.MerchantName or '-',
            'contact_person': row.ContactPerson or '-',
            'contract_period': row.ContractPeriod,
            'start_date': row.StartDate.strftime('%Y-%m-%d') if row.StartDate else None,
            'end_date': row.EndDate.strftime('%Y-%m-%d') if row.EndDate else None,
            'contract_amount': float(row.ContractAmount) if row.ContractAmount else 0,
            'amount_reduction': float(row.AmountReduction) if row.AmountReduction else 0,
            'actual_amount': float(row.ActualAmount) if row.ActualAmount else 0,
            'status': row.Status or '有效',
            'description': row.Description or '',
            'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M:%S') if row.CreateTime else None
        }
        
        cursor.execute("""
            SELECT cp.PlotID, cp.UnitPrice, cp.Area, cp.MonthlyPrice, p.PlotNumber, p.PlotName, p.YearlyRent, p.ImagePath
            FROM ContractPlot cp
            LEFT JOIN Plot p ON cp.PlotID = p.PlotID
            WHERE cp.ContractID = ?
        """, (contract_id,))
        
        plots = []
        for p in cursor.fetchall():
            plots.append({
                'plot_id': p.PlotID,
                'plot_number': p.PlotNumber,
                'plot_name': p.PlotName,
                'area': float(p.Area) if p.Area else 0,
                'unit_price': float(p.UnitPrice) if p.UnitPrice else 0,
                'monthly_rent': float(p.MonthlyPrice) if p.MonthlyPrice else 0,
                'yearly_rent': float(p.YearlyRent) if p.YearlyRent else 0,
                'image_path': p.ImagePath
            })
        
        contract['plots'] = plots
        
        conn.close()
        
        return jsonify({'success': True, 'data': contract})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@contract_bp.route('/edit/<int:contract_id>', methods=['GET', 'POST'])
@login_required
def edit(contract_id):
    if request.method == 'GET':
        period_list = get_contract_periods()
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
            return jsonify({'success': False, 'message': '请选择开始日期'})
        if not end_date:
            return jsonify({'success': False, 'message': '请选择结束日期'})
        
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        if end_date_obj <= start_date_obj:
            return jsonify({'success': False, 'message': '结束日期必须晚于开始日期'})
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT ContractPeriod FROM Contract WHERE ContractID = ?", (contract_id,))
        contract_row = cursor.fetchone()
        if not contract_row:
            conn.close()
            return jsonify({'success': False, 'message': '合同不存在'})
        
        total_rent = 0
        for plot_id in plot_ids:
            cursor.execute("SELECT YearlyRent FROM Plot WHERE PlotID = ?", (int(plot_id),))
            result = cursor.fetchone()
            if result and result.YearlyRent:
                total_rent += float(result.YearlyRent)
        
        try:
            cursor.execute("""
                UPDATE Contract
                SET StartDate = ?, EndDate = ?, ContractAmount = ?, AmountReduction = ?,
                    ActualAmount = ?, Description = ?, Status = ?, UpdateTime = GETDATE()
                WHERE ContractID = ?
            """, (
                start_date_obj,
                end_date_obj,
                total_rent,
                rent_adjust,
                total_rent + rent_adjust,
                description,
                status,
                contract_id
            ))
            
            cursor.execute("DELETE FROM ContractPlot WHERE ContractID = ?", (contract_id,))
            
            for plot_id in plot_ids:
                cursor.execute("SELECT UnitPrice, Area FROM Plot WHERE PlotID = ?", (int(plot_id),))
                plot_result = cursor.fetchone()
                unit_price = float(plot_result.UnitPrice) if plot_result and plot_result.UnitPrice else 0
                area = float(plot_result.Area) if plot_result and plot_result.Area else 0
                monthly_price = unit_price * area
                
                cursor.execute("""
                    INSERT INTO ContractPlot (ContractID, PlotID, UnitPrice, Area, MonthlyPrice)
                    VALUES (?, ?, ?, ?, ?)
                """, (contract_id, int(plot_id), unit_price, area, monthly_price))
            
            conn.commit()
            return jsonify({'success': True, 'message': '合同更新成功'})
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': str(e)})
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@contract_bp.route('/delete/<int:contract_id>', methods=['POST'])
@login_required
def delete(contract_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM ContractPlot WHERE ContractID = ?", (contract_id,))
        cursor.execute("DELETE FROM Contract WHERE ContractID = ?", (contract_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '删除成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
