# 水电计费相关路由
import logging

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.utility_service import UtilityService
from app.api_response import handle_exception
from app.routes.user import check_permission, check_api_permission

# 创建蓝图
utility_bp = Blueprint('utility', __name__)

# 初始化服务
utility_service = UtilityService()
logger = logging.getLogger(__name__)


@utility_bp.route('/list')
@login_required
@check_permission('utility_view')
def utility_list():
    """
    水电表列表页面
    """
    return render_template('utility/list.html')


@utility_bp.route('/list_data', methods=['GET'])
@login_required
@check_api_permission('utility_view')
def list_data():
    """
    获取水电表列表数据（带分页和筛选）
    """
    try:
        meter_number = request.args.get('meter_number', '').strip()
        meter_type = request.args.get('meter_type', 'all')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        result = utility_service.get_meter_list_paginated(
            meter_number=meter_number,
            meter_type=meter_type,
            page=page,
            page_size=page_size
        )
        return jsonify(result)
    
    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/detail/<int:meter_id>', methods=['GET'])
@login_required
@check_api_permission('utility_view')
def detail(meter_id):
    """
    查看水电表明细
    """
    try:
        meter_type = request.args.get('meter_type', request.args.get('type', 'water')).strip()
        result = utility_service.get_meter_detail(meter_id, meter_type)
        return jsonify(result)
    
    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/create', methods=['POST'])
@login_required
@check_api_permission('utility_create')
def create():
    """
    新增水电表
    """
    try:
        data = request.get_json()
        logger.debug("进入 /utility/create 路由，接收到数据: %s", data)

        if not data:
            logger.warning("/utility/create 未接收到 JSON 数据")
            return jsonify({
                'success': False,
                'message': '[CREATE_V3] 请求数据格式错误，需要JSON格式'
            }), 400

        meter_type = data.get('meter_type', '').strip()
        logger.debug("/utility/create 表类型: %s", meter_type)

        if not meter_type or meter_type not in ['water', 'electricity']:
            return jsonify({
                'success': False,
                'message': '[CREATE_V3] 表类型参数错误，必须为 water 或 electricity'
            }), 400

        required_fields = ['meter_number', 'meter_type']
        logger.debug("/utility/create 必填字段: %s", required_fields)

        for field in required_fields:
            field_value = data.get(field)
            logger.debug("/utility/create 检查字段 %s: %s", field, field_value)
            if field not in data or not str(data[field]).strip():
                logger.warning("/utility/create 验证失败，字段为空: %s", field)
                return jsonify({
                    'success': False,
                    'message': f'[CREATE_V3] 缺少必填字段：{field}'
                }), 400

        logger.debug("/utility/create 参数校验通过，开始调用 utility_service.create_meter")
        result = utility_service.create_meter(meter_type, data)
        logger.debug("/utility/create service 返回结果: %s", result)
        return jsonify(result)

    except Exception as e:
        logger.exception("/utility/create 创建失败: %s", e)
        return jsonify({
            'success': False,
            'message': ''
        }), 500


@utility_bp.route('/edit/<int:meter_id>', methods=['POST'])
@login_required
@check_api_permission('utility_edit')
def edit(meter_id):
    """
    编辑水电表
    """
    try:
        data = request.get_json()
        meter_type = data.get('meter_type', '').strip()
        
        if not meter_type or meter_type not in ['water', 'electricity']:
            return jsonify({
                'success': False,
                'message': '表类型参数错误'
            }), 400
        
        result = utility_service.update_meter(meter_id, meter_type, data)
        return jsonify(result)
    
    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/delete/<int:meter_id>', methods=['POST'])
@login_required
@check_api_permission('utility_delete')
def delete(meter_id):
    """
    删除水电表
    """
    try:
        meter_type = request.form.get('meter_type', 'water').strip()
        result = utility_service.delete_meter(meter_id, meter_type)
        return jsonify(result)
    
    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/unlink/<int:meter_id>', methods=['POST'])
@login_required
@check_api_permission('utility_edit')
def unlink(meter_id):
    """
    解除水电表与合同的关联
    """
    try:
        meter_type = request.form.get('meter_type', 'water').strip()
        result = utility_service.unlink_meter(meter_id, meter_type)
        return jsonify(result)
    
    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/water_meter')
@login_required
@check_permission('utility_reading')
def water_meter():
    """
    水表抄表页面
    支持URL参数传递日期，格式：?date=2026-01-01
    """
    from datetime import datetime, date
    from dateutil.relativedelta import relativedelta
    from flask import request
    
    reading_date = request.args.get('date')
    
    if reading_date:
        try:
            parsed_date = datetime.strptime(reading_date, '%Y-%m-%d').date()
        except ValueError:
            parsed_date = date.today().replace(day=1)
    else:
        parsed_date = date.today().replace(day=1)
    
    # 生成所属月份选项：前6个月 + 当月 + 后5个月，格式"YYYY年MM月"
    today = date.today()
    month_options = []
    for i in range(-6, 6):
        m = today + relativedelta(months=i)
        label = f"{m.year}年{m.month:02d}月"
        value = f"{m.year}-{m.month:02d}"
        month_options.append({'label': label, 'value': value})
    
    # 默认选择上一个月
    last_month = today + relativedelta(months=-1)
    default_belong_month = f"{last_month.year}-{last_month.month:02d}"
    
    return render_template('utility/water_meter.html', 
                         default_reading_date=parsed_date.strftime('%Y-%m-%d'),
                         month_options=month_options,
                         default_belong_month=default_belong_month)


@utility_bp.route('/water_meter_data', methods=['GET'])
@login_required
@check_api_permission('utility_reading')
def water_meter_data():
    """
    获取待抄水表列表（按所属月份过滤已抄表记录）
    """
    try:
        belong_month = request.args.get('belong_month', '').strip()
        result = utility_service.get_meters_to_read('water', belong_month=belong_month or None)
        return jsonify(result)
    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/water_meter_submit', methods=['POST'])
@login_required
@check_api_permission('utility_reading')
def water_meter_submit():
    """
    提交水表抄表数据
    """
    try:
        data = request.get_json()
        readings = data.get('readings', [])
        reading_date = data.get('reading_date')
        belong_month = data.get('belong_month')
        
        if not readings:
            return jsonify({
                'success': False,
                'message': '未提供抄表数据'
            }), 400
        
        # 注入当前操作用户ID
        for r in readings:
            r['created_by'] = current_user.user_id
        result = utility_service.submit_meter_readings('water', readings, reading_date, belong_month)
        return jsonify(result)
    
    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/electricity_meter')
@login_required
@check_permission('utility_reading')
def electricity_meter():
    """
    电表抄表页面
    支持URL参数传递日期，格式：?date=2026-01-01
    """
    from datetime import datetime, date
    from dateutil.relativedelta import relativedelta
    from flask import request
    
    reading_date = request.args.get('date')
    
    if reading_date:
        try:
            parsed_date = datetime.strptime(reading_date, '%Y-%m-%d').date()
        except ValueError:
            parsed_date = date.today().replace(day=1)
    else:
        parsed_date = date.today().replace(day=1)
    
    # 生成所属月份选项：前6个月 + 当月 + 后5个月，格式"YYYY年MM月"
    today = date.today()
    month_options = []
    for i in range(-6, 6):
        m = today + relativedelta(months=i)
        label = f"{m.year}年{m.month:02d}月"
        value = f"{m.year}-{m.month:02d}"
        month_options.append({'label': label, 'value': value})
    
    # 默认选择上一个月
    last_month = today + relativedelta(months=-1)
    default_belong_month = f"{last_month.year}-{last_month.month:02d}"
    
    return render_template('utility/electricity_meter.html', 
                         default_reading_date=parsed_date.strftime('%Y-%m-%d'),
                         month_options=month_options,
                         default_belong_month=default_belong_month)


@utility_bp.route('/electricity_meter_data', methods=['GET'])
@login_required
@check_api_permission('utility_reading')
def electricity_meter_data():
    """
    获取待抄电表列表（按所属月份过滤已抄表记录）
    """
    try:
        belong_month = request.args.get('belong_month', '').strip()
        result = utility_service.get_meters_to_read('electricity', belong_month=belong_month or None)
        return jsonify(result)
    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/electricity_meter_submit', methods=['POST'])
@login_required
@check_api_permission('utility_reading')
def electricity_meter_submit():
    """
    提交电表抄表数据
    """
    try:
        data = request.get_json()
        readings = data.get('readings', [])
        reading_date = data.get('reading_date')
        belong_month = data.get('belong_month')
        
        if not readings:
            return jsonify({
                'success': False,
                'message': '未提供抄表数据'
            }), 400
        
        # 注入当前操作用户ID
        for r in readings:
            r['created_by'] = current_user.user_id
        result = utility_service.submit_meter_readings('electricity', readings, reading_date, belong_month)
        return jsonify(result)
    
    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/merchants', methods=['GET'])
@login_required
def merchants():
    """
    获取商户列表（用于筛选）
    """
    try:
        result = utility_service.get_merchants_list()
        return jsonify(result)
    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/contracts', methods=['GET'])
@login_required
def contracts():
    """
    获取可关联的合同列表
    """
    try:
        result = utility_service.get_contracts_list()
        return jsonify(result)
    except Exception as e:
        return handle_exception(e)


# [已移除] debug_contracts 和 test_contracts 路由 — 生产环境不需要调试页面


@utility_bp.route('/valid_contracts', methods=['GET'])
@login_required
def valid_contracts():
    """
    获取有效合同列表
    有效期：起始日期 ≤ 今天 ≤ 结束日期+3个月
    """
    try:
        result = utility_service.get_valid_contracts()
        return jsonify(result)
    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/bind', methods=['POST'])
@login_required
@check_api_permission('utility_edit')
def bind():
    """
    绑定水电表到合同
    """
    try:
        data = request.get_json()
        meter_id = data.get('meter_id')
        meter_type = data.get('meter_type')
        contract_id = data.get('contract_id')
        unit_price = data.get('unit_price', 0)
        
        if not meter_id or not meter_type or not contract_id:
            return jsonify({
                'success': False,
                'message': '参数不完整'
            }), 400
        
        if meter_type not in ['water', 'electricity']:
            return jsonify({
                'success': False,
                'message': '表类型参数错误'
            }), 400
        
        if unit_price <= 0:
            return jsonify({
                'success': False,
                'message': '单价必须大于0'
            }), 400
        
        result = utility_service.bind_meter_to_contract(meter_id, meter_type, contract_id, unit_price)
        return jsonify(result)
    
    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/unbind', methods=['POST'])
@login_required
@check_api_permission('utility_edit')
def unbind():
    """
    解绑水电表
    """
    try:
        data = request.get_json()
        meter_id = data.get('meter_id')
        meter_type = data.get('meter_type')
        
        if not meter_id or not meter_type:
            return jsonify({
                'success': False,
                'message': '参数不完整'
            }), 400
        
        if meter_type not in ['water', 'electricity']:
            return jsonify({
                'success': False,
                'message': '表类型参数错误'
            }), 400
        
        result = utility_service.unbind_meter_from_contract(meter_id, meter_type)
        return jsonify(result)
    
    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/toggle_meter_status', methods=['POST'])
@login_required
@check_api_permission('utility_edit')
def toggle_meter_status():
    """
    切换水电表绑定的启用/停用状态
    """
    try:
        data = request.get_json()
        meter_id = data.get('meter_id')
        meter_type = data.get('meter_type')
        contract_id = data.get('contract_id')
        
        if not meter_id or not meter_type:
            return jsonify({
                'success': False,
                'message': '参数不完整'
            }), 400
        
        if meter_type not in ['water', 'electricity']:
            return jsonify({
                'success': False,
                'message': '表类型参数错误'
            }), 400
        
        result = utility_service.toggle_meter_binding_status(meter_id, meter_type, contract_id)
        return jsonify(result)
    
    except Exception as e:
        return handle_exception(e)


# [已移除] diagnose_electricity 和 diagnose_electricity_page 路由 — 生产环境不需要调试页面


@utility_bp.route('/reading_data')
@login_required
@check_permission('utility_reading')
def reading_data():
    from datetime import date
    from dateutil.relativedelta import relativedelta

    today = date.today()
    month_options = []
    for i in range(-12, 1):
        m = today + relativedelta(months=i)
        label = f"{m.year}年{m.month:02d}月"
        value = f"{m.year}-{m.month:02d}"
        month_options.append({'label': label, 'value': value})

    default_belong_month = f"{today.year}-{today.month:02d}"

    return render_template('utility/reading_data.html',
                         month_options=month_options,
                         default_belong_month=default_belong_month)


@utility_bp.route('/reading_data_list', methods=['GET'])
@login_required
@check_api_permission('utility_reading')
def reading_data_list():
    try:
        belong_month = request.args.get('belong_month', '').strip()
        meter_type = request.args.get('meter_type', '').strip()

        if not belong_month:
            return jsonify({'success': False, 'message': '请选择月份'}), 400

        result = utility_service.get_reading_data(belong_month, meter_type or None)
        return jsonify(result)

    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/reading_data/pay', methods=['POST'])
@login_required
@check_api_permission('utility_pay')
def pay_reading():
    """
    抄表数据快捷收费
    """
    try:
        data = request.get_json()
        merchant_id = data.get('merchant_id')
        belong_month = data.get('belong_month')  # 格式 "YYYY年MM月"
        meter_type = data.get('meter_type', 'electricity')
        account_id = data.get('account_id')
        amount = float(data.get('amount', 0))

        logger.info(f"收费请求: merchant_id={merchant_id}, belong_month={belong_month}, meter_type={meter_type}, account_id={account_id}, amount={amount}")

        if not merchant_id:
            return jsonify({'success': False, 'message': '缺少商户ID'}), 400

        result = utility_service.pay_reading(
            merchant_id, belong_month, meter_type, account_id, amount,
            created_by=current_user.id
        )
        return jsonify(result)
    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/reading_data/delete/<int:reading_id>', methods=['POST'])
@login_required
@check_api_permission('utility_reading')
def delete_reading(reading_id):
    """
    删除单条抄表记录
    """
    try:
        result = utility_service.delete_reading(reading_id)
        return jsonify(result)
    except Exception as e:
        return handle_exception(e)


@utility_bp.route('/reading_data/delete_batch', methods=['POST'])
@login_required
@check_api_permission('utility_reading')
def delete_readings_batch():
    """
    批量删除抄表记录
    """
    try:
        data = request.get_json()
        reading_ids = data.get('reading_ids', [])
        
        if not reading_ids or not isinstance(reading_ids, list):
            return jsonify({
                'success': False,
                'message': '请提供有效的抄表记录ID列表'
            }), 400
        
        result = utility_service.delete_readings_batch(reading_ids)
        return jsonify(result)
    except Exception as e:
        return handle_exception(e)
