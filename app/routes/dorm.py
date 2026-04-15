# -*- coding: utf-8 -*-
"""宿舍管理路由"""
import os
import uuid
from datetime import date
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.routes.user import check_permission
from app.services.dorm_service import DormService

dorm_bp = Blueprint('dorm', __name__)
dorm_svc = DormService()


# ==================== 房间管理 ====================

@dorm_bp.route('/rooms')
@login_required
@check_permission('dorm_manage')
def rooms():
    """房间管理页面"""
    return render_template('dorm/rooms.html')


@dorm_bp.route('/rooms/list', methods=['GET'])
@login_required
@check_permission('dorm_manage')
def rooms_list():
    """房间列表数据"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        room_type = request.args.get('room_type', '').strip()

        result = dorm_svc.get_rooms(
            page=page, per_page=per_page,
            search=search or None, status=status or None,
            room_type=room_type or None
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


@dorm_bp.route('/rooms/add', methods=['POST'])
@login_required
@check_permission('dorm_manage')
def rooms_add():
    """新增房间"""
    try:
        data = request.json
        new_id = dorm_svc.create_room(
            room_number=data.get('room_number', '').strip(),
            room_type=data.get('room_type', '单间'),
            area=data.get('area'),
            monthly_rent=data.get('monthly_rent', 0),
            water_quota=data.get('water_quota', 0),
            electricity_unit_price=data.get('electricity_unit_price', 1.0),
            meter_number=data.get('meter_number', '').strip() or None,
            description=data.get('description', '').strip() or None,
        )
        return jsonify({'success': True, 'message': '添加成功', 'id': new_id})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'添加失败：{str(e)}'}), 500


@dorm_bp.route('/rooms/edit/<int:room_id>', methods=['POST'])
@login_required
@check_permission('dorm_manage')
def rooms_edit(room_id):
    """编辑房间"""
    try:
        data = request.json
        dorm_svc.update_room(room_id, **data)
        return jsonify({'success': True, 'message': '更新成功'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新失败：{str(e)}'}), 500


@dorm_bp.route('/rooms/delete/<int:room_id>', methods=['POST'])
@login_required
@check_permission('dorm_manage')
def rooms_delete(room_id):
    """删除房间"""
    try:
        dorm_svc.delete_room(room_id)
        return jsonify({'success': True, 'message': '删除成功'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败：{str(e)}'}), 500


# ==================== 入住管理 ====================

@dorm_bp.route('/occupancy')
@login_required
@check_permission('dorm_manage')
def occupancy():
    """入住管理页面"""
    return render_template('dorm/occupancy.html')


@dorm_bp.route('/occupancy/list', methods=['GET'])
@login_required
@check_permission('dorm_manage')
def occupancy_list():
    """入住记录列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', '').strip()
        search = request.args.get('search', '').strip()

        result = dorm_svc.get_occupancies(
            page=page, per_page=per_page,
            status=status or None, search=search or None
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


@dorm_bp.route('/occupancy/check_in', methods=['POST'])
@login_required
@check_permission('dorm_manage')
def occupancy_check_in():
    """办理入住"""
    try:
        data = request.json
        new_id = dorm_svc.check_in(
            room_id=data.get('room_id'),
            tenant_type=data.get('tenant_type', '个人'),
            merchant_id=data.get('merchant_id'),
            tenant_name=data.get('tenant_name', '').strip(),
            tenant_phone=data.get('tenant_phone', '').strip() or None,
            id_card_number=data.get('id_card_number', '').strip() or None,
            id_card_front_photo=data.get('id_card_front_photo', '').strip() or None,
            id_card_back_photo=data.get('id_card_back_photo', '').strip() or None,
            move_in_date=data.get('move_in_date', date.today().strftime('%Y-%m-%d')),
            description=data.get('description', '').strip() or None,
        )
        return jsonify({'success': True, 'message': '入住办理成功', 'id': new_id})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'入住办理失败：{str(e)}'}), 500


@dorm_bp.route('/occupancy/check_out/<int:occupancy_id>', methods=['POST'])
@login_required
@check_permission('dorm_manage')
def occupancy_check_out(occupancy_id):
    """办理退房"""
    try:
        data = request.json or {}
        move_out_date = data.get('move_out_date', date.today().strftime('%Y-%m-%d'))
        dorm_svc.check_out(occupancy_id, move_out_date)
        return jsonify({'success': True, 'message': '退房办理成功'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'退房办理失败：{str(e)}'}), 500


# ==================== 身份证照片上传 ====================

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@dorm_bp.route('/upload_idcard', methods=['POST'])
@login_required
@check_permission('dorm_manage')
def upload_idcard():
    """上传身份证照片"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '未找到文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '未选择文件'}), 400

        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': '仅支持 JPG/PNG 格式'}), 400

        # 检查文件大小（5MB）
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > 5 * 1024 * 1024:
            return jsonify({'success': False, 'message': '文件大小不能超过5MB'}), 400

        # 生成唯一文件名
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"

        # 保存路径
        upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'dorm_idcard')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # 返回相对路径
        relative_path = f"dorm_idcard/{filename}"
        return jsonify({'success': True, 'path': relative_path})

    except Exception as e:
        return jsonify({'success': False, 'message': f'上传失败：{str(e)}'}), 500


# ==================== 电表抄表 ====================

@dorm_bp.route('/reading')
@login_required
@check_permission('dorm_manage')
def reading():
    """电表抄表页面"""
    return render_template('dorm/reading.html')


@dorm_bp.route('/reading/list', methods=['GET'])
@login_required
@check_permission('dorm_manage')
def reading_list():
    """电表读数列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        year_month = request.args.get('year_month', '').strip()
        room_id = request.args.get('room_id', type=int)

        result = dorm_svc.get_readings(
            page=page, per_page=per_page,
            year_month=year_month or None,
            room_id=room_id
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


@dorm_bp.route('/reading/rooms_for_reading', methods=['GET'])
@login_required
@check_permission('dorm_manage')
def reading_rooms():
    """获取需要抄表的在住房间列表"""
    try:
        year_month = request.args.get('year_month', '').strip()
        if not year_month:
            return jsonify({'success': False, 'message': '请选择抄表月份'}), 400

        result = dorm_svc.get_rooms_for_reading(year_month)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


@dorm_bp.route('/reading/save', methods=['POST'])
@login_required
@check_permission('dorm_manage')
def reading_save():
    """保存电表读数"""
    try:
        data = request.json
        result = dorm_svc.save_reading(
            room_id=data.get('room_id'),
            year_month=data.get('year_month', '').strip(),
            current_reading=data.get('current_reading'),
            reading_date=data.get('reading_date'),
        )
        return jsonify({'success': True, 'message': '保存成功', 'data': result})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存失败：{str(e)}'}), 500


# ==================== 月度账单 ====================

@dorm_bp.route('/bill')
@login_required
@check_permission('dorm_manage')
def bill():
    """月度账单页面"""
    return render_template('dorm/bill.html')


@dorm_bp.route('/bill/list', methods=['GET'])
@login_required
@check_permission('dorm_manage')
def bill_list():
    """月度账单列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        year_month = request.args.get('year_month', '').strip()
        status = request.args.get('status', '').strip()

        result = dorm_svc.get_bills(
            page=page, per_page=per_page,
            year_month=year_month or None,
            status=status or None
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败：{str(e)}'}), 500


@dorm_bp.route('/bill/generate', methods=['POST'])
@login_required
@check_permission('dorm_manage')
def bill_generate():
    """按月批量生成账单"""
    try:
        data = request.json
        year_month = data.get('year_month', '').strip()
        result = dorm_svc.generate_bills(year_month)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成失败：{str(e)}'}), 500


@dorm_bp.route('/bill/confirm/<int:bill_id>', methods=['POST'])
@login_required
@check_permission('dorm_manage')
def bill_confirm(bill_id):
    """确认单条账单"""
    try:
        dorm_svc.confirm_bill(bill_id)
        return jsonify({'success': True, 'message': '确认成功'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'确认失败：{str(e)}'}), 500


@dorm_bp.route('/bill/batch_confirm', methods=['POST'])
@login_required
@check_permission('dorm_manage')
def bill_batch_confirm():
    """批量确认账单"""
    try:
        data = request.json
        bill_ids = data.get('bill_ids', [])
        result = dorm_svc.batch_confirm_bills(bill_ids)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': f'批量确认失败：{str(e)}'}), 500


@dorm_bp.route('/bill/create_receivable/<int:bill_id>', methods=['POST'])
@login_required
@check_permission('dorm_manage')
def bill_create_receivable(bill_id):
    """开账→联动应收"""
    try:
        result = dorm_svc.create_receivable(bill_id, created_by=current_user.user_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'开账失败：{str(e)}'}), 500


# ==================== 统计概览 ====================

@dorm_bp.route('/stats', methods=['GET'])
@login_required
@check_permission('dorm_manage')
def stats():
    """宿舍概览统计"""
    try:
        result = dorm_svc.get_dashboard_stats()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取统计失败：{str(e)}'}), 500
