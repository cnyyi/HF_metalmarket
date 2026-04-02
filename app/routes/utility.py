# 水电计费相关路由
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.services.utility_service import UtilityService

# 创建蓝图
utility_bp = Blueprint('utility', __name__)

# 初始化服务
utility_service = UtilityService()


@utility_bp.route('/list')
@login_required
def utility_list():
    """
    水电表列表页面
    """
    return render_template('utility/list.html')


@utility_bp.route('/list_data', methods=['GET'])
@login_required
def list_data():
    """
    获取水电表列表数据（带分页和筛选）
    """
    try:
        meter_type = request.args.get('type', 'all').strip()
        merchant_id = request.args.get('merchant_id', '').strip()
        
        if merchant_id:
            merchant_id = int(merchant_id)
        else:
            merchant_id = None
        
        result = utility_service.get_meter_list(meter_type=meter_type, merchant_id=merchant_id)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取数据失败：{str(e)}'
        }), 500


@utility_bp.route('/detail/<int:meter_id>', methods=['GET'])
@login_required
def detail(meter_id):
    """
    查看水电表明细
    """
    try:
        meter_type = request.args.get('type', 'water').strip()
        result = utility_service.get_meter_detail(meter_id, meter_type)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取详情失败：{str(e)}'
        }), 500


@utility_bp.route('/create', methods=['POST'])
@login_required
def create():
    """
    新增水电表
    """
    try:
        data = request.get_json()
        meter_type = data.get('meter_type', '').strip()

        if not meter_type or meter_type not in ['water', 'electricity']:
            return jsonify({
                'success': False,
                'message': '表类型参数错误'
            }), 400

        required_fields = ['meter_number', 'meter_type', 'installation_date']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段：{field}'
                }), 400

        result = utility_service.create_meter(meter_type, data)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建失败：{str(e)}'
        }), 500


@utility_bp.route('/edit/<int:meter_id>', methods=['POST'])
@login_required
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
        return jsonify({
            'success': False,
            'message': f'编辑失败：{str(e)}'
        }), 500


@utility_bp.route('/delete/<int:meter_id>', methods=['POST'])
@login_required
def delete(meter_id):
    """
    删除水电表
    """
    try:
        meter_type = request.form.get('meter_type', 'water').strip()
        result = utility_service.delete_meter(meter_id, meter_type)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除失败：{str(e)}'
        }), 500


@utility_bp.route('/unlink/<int:meter_id>', methods=['POST'])
@login_required
def unlink(meter_id):
    """
    解除水电表与合同的关联
    """
    try:
        meter_type = request.form.get('meter_type', 'water').strip()
        result = utility_service.unlink_meter(meter_id, meter_type)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'解除关联失败：{str(e)}'
        }), 500


@utility_bp.route('/water_meter')
@login_required
def water_meter():
    """
    水表抄表页面
    """
    return render_template('utility/water_meter.html')


@utility_bp.route('/water_meter_data', methods=['GET'])
@login_required
def water_meter_data():
    """
    获取待抄水表列表
    """
    try:
        result = utility_service.get_meters_to_read('water')
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取数据失败：{str(e)}'
        }), 500


@utility_bp.route('/water_meter_submit', methods=['POST'])
@login_required
def water_meter_submit():
    """
    提交水表抄表数据
    """
    try:
        data = request.get_json()
        readings = data.get('readings', [])
        
        if not readings:
            return jsonify({
                'success': False,
                'message': '未提供抄表数据'
            }), 400
        
        result = utility_service.submit_meter_readings('water', readings)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'提交失败：{str(e)}'
        }), 500


@utility_bp.route('/electricity_meter')
@login_required
def electricity_meter():
    """
    电表抄表页面
    """
    return render_template('utility/electricity_meter.html')


@utility_bp.route('/electricity_meter_data', methods=['GET'])
@login_required
def electricity_meter_data():
    """
    获取待抄电表列表
    """
    try:
        result = utility_service.get_meters_to_read('electricity')
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取数据失败：{str(e)}'
        }), 500


@utility_bp.route('/electricity_meter_submit', methods=['POST'])
@login_required
def electricity_meter_submit():
    """
    提交电表抄表数据
    """
    try:
        data = request.get_json()
        readings = data.get('readings', [])
        
        if not readings:
            return jsonify({
                'success': False,
                'message': '未提供抄表数据'
            }), 400
        
        result = utility_service.submit_meter_readings('electricity', readings)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'提交失败：{str(e)}'
        }), 500


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
        return jsonify({
            'success': False,
            'message': f'获取商户列表失败：{str(e)}'
        }), 500


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
        return jsonify({
            'success': False,
            'message': f'获取合同列表失败：{str(e)}'
        }), 500


@utility_bp.route('/debug_contracts')
@login_required
def debug_contracts():
    """
    调试合同接口页面
    """
    return render_template('utility/debug_contracts.html')

@utility_bp.route('/test_contracts')
@login_required
def test_contracts():
    """
    测试合同接口
    """
    try:
        result = utility_service.get_contracts_list()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'测试失败：{str(e)}'
        }), 500
