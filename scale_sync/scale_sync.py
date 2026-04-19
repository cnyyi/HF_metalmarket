"""
宏发金属交易市场 - 过磅数据同步服务
从 Access 过磅软件数据库同步数据到 SQL Server

功能：
  1. 增量同步：按流水号插入新记录
  2. 变更检测：对比已同步记录的更新时间，发现修改后标记原记录并插入新版本

运行方式：
  python scale_sync.py                # 前台运行
  python scale_sync.py --install      # 安装为 Windows 服务
  python scale_sync.py --uninstall    # 卸载 Windows 服务

配置文件：sync_config.json（同目录下，自动生成默认配置）
"""

import os
import sys
import json
import time
import logging
import pyodbc
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

# ============================================================
# 配置
# ============================================================

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sync_config.json')

DEFAULT_CONFIG = {
    # Access 过磅数据库（本地）
    "access_db_path": r"D:\BaiduSyncdisk\HF_metalmarket\Database.mdb",
    "access_password": "www.fzatw.com",

    # SQL Server 目标数据库（远程）
    "sql_server": "yyi.myds.me",
    "sql_database": "hf_metalmarket",
    "sql_user": "sa",
    "sql_password": "yyI.123212",

    # 默认磅秤ID（对应 Scale 表的 ScaleID）
    "default_scale_id": 1,

    # 同步间隔（秒）
    "sync_interval": 60,

    # 只同步 RecordFinish=1 的已完成过磅记录
    "only_finished": True,

    # 变更检测回查天数（检查最近N天内已同步记录是否被修改）
    "change_detection_days": 3,

    # 日志级别
    "log_level": "INFO"
}


def load_config():
    """加载配置，不存在则生成默认配置"""
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        print(f"已生成默认配置文件: {CONFIG_FILE}")
        print("请根据实际情况修改配置后重新运行。")
        return DEFAULT_CONFIG

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    # 补全缺失的配置项
    for key, value in DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = value
            # 回写到配置文件
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
    return config


# ============================================================
# 日志
# ============================================================

def setup_logger(config):
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger('ScaleSync')
    logger.setLevel(getattr(logging, config.get('log_level', 'INFO')))

    # 控制台输出
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(ch)

    # 文件输出（按天滚动，保留30天）
    fh = RotatingFileHandler(
        os.path.join(log_dir, 'scale_sync.log'),
        maxBytes=5*1024*1024, backupCount=30, encoding='utf-8'
    )
    fh.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(fh)

    return logger


# ============================================================
# 数据库连接
# ============================================================

def get_access_connection(config):
    """连接 Access 过磅数据库"""
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        f'DBQ={config["access_db_path"]};'
        f'PWD={config["access_password"]}'
    )
    return pyodbc.connect(conn_str)


def get_sql_connection(config):
    """连接 SQL Server"""
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={config["sql_server"]};'
        f'DATABASE={config["sql_database"]};'
        f'UID={config["sql_user"]};'
        f'PWD={config["sql_password"]}'
    )
    return pyodbc.connect(conn_str)


# ============================================================
# 数据转换工具
# ============================================================

WEIGH_TYPE_MAP = {
    'PO': '皮毛重',
    'SO': '毛重',
    'OO': '皮重',
    'IO': '入口',
}


def row_to_params(data, columns, config, modified_from_id=None):
    """将 Access 一行数据转换为 SQL Server INSERT 参数"""
    scale_id = config.get('default_scale_id', 1)
    now = datetime.now()

    serial_no = data.get('流水号', '')
    weigh_type = WEIGH_TYPE_MAP.get(data.get('过磅类型', ''), data.get('过磅类型', ''))
    scale_time = data.get('二次过磅时间') or data.get('一次过磅时间') or data.get('更新时间') or now
    product_name = data.get('货名', '') or data.get('规格', '')
    memo = data.get('备注', '') or ''
    source_update_time = data.get('更新时间')  # Access 端更新时间

    params = (
        scale_id,
        None,                               # MerchantID = NULL
        serial_no,
        weigh_type,
        data.get('毛重', 0) or 0,
        data.get('皮重', 0) or 0,
        data.get('净重', 0) or 0,
        data.get('扣重', 0) or 0,
        data.get('实重', 0) or 0,
        data.get('单价', 0) or 0,
        data.get('金额', 0) or 0,
        data.get('过磅费', 0) or 0,
        data.get('车号', ''),
        product_name,
        data.get('发货单位', ''),
        data.get('收货单位', ''),
        data.get('毛重时间'),
        data.get('皮重时间'),
        scale_time,
        data.get('毛重司磅员', ''),
        data.get('皮重司磅员', ''),
        data.get('更新人', '') or '系统同步',
        memo,
        now,
        source_update_time,                 # SourceUpdateTime
        0,                                  # IsModified = 0（新记录）
        modified_from_id,                   # ModifiedFromRecordID
    )
    return serial_no, params


# ============================================================
# 同步逻辑
# ============================================================

def get_last_synced_serial(sql_conn):
    """获取 SQL Server 中已同步的最大流水号"""
    cursor = sql_conn.cursor()
    cursor.execute("""
        SELECT MAX(SourceSerialNo) FROM ScaleRecord 
        WHERE SourceSerialNo IS NOT NULL
    """)
    row = cursor.fetchone()
    return row[0] if row and row[0] else None


def fetch_new_records(access_conn, last_serial, only_finished=True):
    """从 Access 查询新记录（流水号 > last_serial）"""
    cursor = access_conn.cursor()

    sql = """
        SELECT 
            流水号, 车号, 过磅类型, 发货单位, 收货单位, 货名, 规格,
            毛重, 皮重, 净重, 扣重, 实重, 单价, 金额, 过磅费,
            毛重司磅员, 皮重司磅员, 毛重磅号, 皮重磅号,
            毛重时间, 皮重时间,
            一次过磅时间, 二次过磅时间,
            更新人, 更新时间, 备注, RecordFinish
        FROM 称重信息
        WHERE 1=1
    """

    if last_serial:
        sql += f" AND 流水号 > '{last_serial}'"

    if only_finished:
        sql += " AND RecordFinish = 1"

    sql += " ORDER BY 流水号 ASC"

    cursor.execute(sql)
    return cursor.fetchall(), [desc[0] for desc in cursor.description]


def fetch_recent_source_records(sql_conn, detection_days):
    """
    查询 SQL Server 中最近 N 天已同步、且未被修改标记的记录
    返回 dict: {SourceSerialNo: (ScaleRecordID, SourceUpdateTime)}
    """
    cursor = sql_conn.cursor()
    cutoff = datetime.now() - timedelta(days=detection_days)

    cursor.execute("""
        SELECT SourceSerialNo, ScaleRecordID, SourceUpdateTime
        FROM ScaleRecord
        WHERE SourceSerialNo IS NOT NULL
          AND IsModified = 0
          AND CreateTime >= ?
    """, (cutoff,))

    result = {}
    for row in cursor.fetchall():
        serial = row[0]
        # 如果同一流水号有多条未修改记录，取最新的那条
        if serial not in result or (row[2] and result[serial][1] and row[2] > result[serial][1]):
            result[serial] = (row[1], row[2])  # (ScaleRecordID, SourceUpdateTime)
    return result


def fetch_access_updated_records(access_conn, serial_nos, only_finished=True):
    """
    从 Access 查询指定流水号的记录（用于变更检测）
    返回 dict: {流水号: row_dict}
    """
    if not serial_nos:
        return {}

    cursor = access_conn.cursor()

    # 构建 IN 子句
    placeholders = ','.join(f"'{s}'" for s in serial_nos)
    sql = f"""
        SELECT 
            流水号, 车号, 过磅类型, 发货单位, 收货单位, 货名, 规格,
            毛重, 皮重, 净重, 扣重, 实重, 单价, 金额, 过磅费,
            毛重司磅员, 皮重司磅员, 毛重磅号, 皮重磅号,
            毛重时间, 皮重时间,
            一次过磅时间, 二次过磅时间,
            更新人, 更新时间, 备注, RecordFinish
        FROM 称重信息
        WHERE 流水号 IN ({placeholders})
    """

    if only_finished:
        sql += " AND RecordFinish = 1"

    cursor.execute(sql)
    columns = [desc[0] for desc in cursor.description]

    result = {}
    for row in cursor.fetchall():
        data = dict(zip(columns, row))
        serial = data.get('流水号', '')
        if serial:
            result[serial] = data
    return result


def detect_changes(sql_conn, access_conn, config, logger):
    """
    变更检测：对比最近已同步记录与 Access 端数据
    发现修改后：标记原记录 IsModified=1，插入新版本记录
    返回修改的记录数
    """
    detection_days = config.get('change_detection_days', 3)

    # 1. 从 SQL Server 获取最近 N 天已同步的记录
    source_records = fetch_recent_source_records(sql_conn, detection_days)
    if not source_records:
        logger.debug("变更检测: 无最近记录需要检查")
        return 0

    logger.debug(f"变更检测: 检查 {len(source_records)} 条最近记录")

    # 2. 从 Access 查询这些流水号的当前数据
    serial_nos = list(source_records.keys())
    access_data = fetch_access_updated_records(
        access_conn, serial_nos,
        only_finished=config.get('only_finished', True)
    )

    # 3. 逐一对比更新时间
    modified_count = 0
    cursor = sql_conn.cursor()

    for serial_no, (record_id, stored_update_time) in source_records.items():
        access_row = access_data.get(serial_no)
        if not access_row:
            continue  # Access 中已无此记录，跳过

        access_update_time = access_row.get('更新时间')
        if not access_update_time or not stored_update_time:
            continue

        # 对比更新时间：如果 Access 的更新时间比存储的更新时间更新，则认为被修改
        if access_update_time > stored_update_time:
            logger.info(f"发现修改: 流水号 {serial_no}, 原更新时间={stored_update_time}, 新更新时间={access_update_time}")

            # 标记原记录为已修改
            cursor.execute("""
                UPDATE ScaleRecord SET IsModified = 1
                WHERE ScaleRecordID = ?
            """, (record_id,))

            # 插入新版本记录，ModifiedFromRecordID 指向原记录
            _, params = row_to_params(access_row, list(access_row.keys()), config, modified_from_id=record_id)
            try:
                cursor.execute("""
                    INSERT INTO ScaleRecord (
                        ScaleID, MerchantID, SourceSerialNo, WeighType,
                        GrossWeight, TareWeight, NetWeight, DeductWeight, ActualWeight,
                        UnitPrice, TotalAmount, ScaleFee,
                        LicensePlate, ProductName,
                        SenderName, ReceiverName,
                        GrossTime, TareTime, ScaleTime,
                        GrossOperator, TareOperator, Operator,
                        Description, CreateTime,
                        SourceUpdateTime, IsModified, ModifiedFromRecordID
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, params)
                modified_count += 1
            except pyodbc.IntegrityError:
                logger.warning(f"修改记录插入冲突: 流水号 {serial_no}")
            except Exception as e:
                logger.error(f"修改记录插入失败 [{serial_no}]: {e}")

    if modified_count > 0:
        try:
            sql_conn.commit()
            logger.info(f"变更检测完成: 处理 {modified_count} 条修改记录")
        except Exception as e:
            logger.error(f"变更检测提交失败: {e}")
            sql_conn.rollback()

    return modified_count


def insert_new_records(sql_conn, records, columns, config, logger):
    """批量插入新记录到 SQL Server"""
    if not records:
        return 0

    insert_sql = """
        INSERT INTO ScaleRecord (
            ScaleID, MerchantID, SourceSerialNo, WeighType,
            GrossWeight, TareWeight, NetWeight, DeductWeight, ActualWeight,
            UnitPrice, TotalAmount, ScaleFee,
            LicensePlate, ProductName,
            SenderName, ReceiverName,
            GrossTime, TareTime, ScaleTime,
            GrossOperator, TareOperator, Operator,
            Description, CreateTime,
            SourceUpdateTime, IsModified, ModifiedFromRecordID
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    inserted = 0
    skipped = 0
    batch_size = 100
    batch_params = []

    for row in records:
        data = dict(zip(columns, row))
        serial_no, params = row_to_params(data, columns, config)

        if not serial_no:
            skipped += 1
            continue

        batch_params.append((serial_no, params))

        # 批量提交
        if len(batch_params) >= batch_size:
            inserted, skipped = _execute_batch(
                sql_conn, insert_sql, batch_params, inserted, skipped, logger
            )
            batch_params = []

    # 剩余记录
    if batch_params:
        inserted, skipped = _execute_batch(
            sql_conn, insert_sql, batch_params, inserted, skipped, logger
        )

    logger.info(f"新增同步完成: 插入 {inserted} 条，跳过 {skipped} 条")
    return inserted


def _execute_batch(sql_conn, insert_sql, batch_params, inserted, skipped, logger):
    """执行一批插入"""
    cursor = sql_conn.cursor()
    for serial_no, params in batch_params:
        try:
            cursor.execute(insert_sql, params)
            inserted += 1
        except pyodbc.IntegrityError:
            skipped += 1
            logger.debug(f"跳过重复流水号: {serial_no}")
        except Exception as e:
            logger.error(f"插入失败 [{serial_no}]: {e}")
            skipped += 1
    try:
        sql_conn.commit()
    except Exception as e:
        logger.error(f"批量提交失败: {e}")
        sql_conn.rollback()
    return inserted, skipped


def do_sync(config, logger):
    """执行一次同步"""
    try:
        access_conn = get_access_connection(config)
        sql_conn = get_sql_connection(config)
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return

    try:
        # ---- 阶段1: 变更检测 ----
        modified = detect_changes(sql_conn, access_conn, config, logger)

        # ---- 阶段2: 增量插入新记录 ----
        last_serial = get_last_synced_serial(sql_conn)
        logger.debug(f"最后已同步流水号: {last_serial or '无'}")

        records, columns = fetch_new_records(
            access_conn, last_serial,
            only_finished=config.get('only_finished', True)
        )

        if not records and modified == 0:
            logger.debug("无新记录，无修改")
            return

        if records:
            logger.info(f"发现 {len(records)} 条新记录，开始同步...")
            inserted = insert_new_records(sql_conn, records, columns, config, logger)
            logger.info(f"本次同步: 新增 {inserted} 条，修改 {modified} 条")
        else:
            logger.info(f"本次同步: 新增 0 条，修改 {modified} 条")

    except Exception as e:
        logger.error(f"同步异常: {e}")
        try:
            sql_conn.rollback()
        except:
            pass
    finally:
        try:
            access_conn.close()
        except:
            pass
        try:
            sql_conn.close()
        except:
            pass


# ============================================================
# 主循环
# ============================================================

def run_loop(config, logger):
    """主循环：每分钟执行一次同步"""
    interval = config.get('sync_interval', 60)
    logger.info(f"过磅数据同步服务启动，同步间隔 {interval} 秒")
    logger.info(f"Access 数据库: {config['access_db_path']}")
    logger.info(f"SQL Server: {config['sql_server']}/{config['sql_database']}")
    logger.info(f"变更检测回查天数: {config.get('change_detection_days', 3)}")

    while True:
        try:
            do_sync(config, logger)
        except Exception as e:
            logger.error(f"同步循环异常: {e}")

        time.sleep(interval)


# ============================================================
# Windows 服务支持
# ============================================================

def install_as_service(config, logger):
    """安装为 Windows 服务（使用 nssm 或 pythoncom）"""
    import subprocess

    script_path = os.path.abspath(__file__)
    python_path = sys.executable

    # 检查 nssm
    nssm_check = subprocess.run(['where', 'nssm'], capture_output=True, text=True)
    if nssm_check.returncode == 0:
        print("检测到 nssm，使用 nssm 安装服务...")
        service_name = "HF_ScaleSync"
        subprocess.run(['nssm', 'install', service_name, python_path, script_path], check=True)
        subprocess.run(['nssm', 'set', service_name, 'Description', '宏发金属交易市场-过磅数据同步服务'], check=True)
        subprocess.run(['nssm', 'set', service_name, 'AppDirectory', os.path.dirname(script_path)], check=True)
        subprocess.run(['nssm', 'set', service_name, 'Start', 'SERVICE_AUTO_START'], check=True)
        subprocess.run(['nssm', 'start', service_name], check=True)
        print(f"服务 {service_name} 已安装并启动")
    else:
        print("未检测到 nssm，使用任务计划程序替代...")
        task_name = "HF_ScaleSync"
        # 创建开机自启任务，每分钟执行
        subprocess.run([
            'schtasks', '/create', '/tn', task_name, '/tr',
            f'"{python_path}" "{script_path}"',
            '/sc', 'minute', '/mo', '1', '/ru', 'SYSTEM',
            '/f'
        ], check=True)
        print(f"任务计划 {task_name} 已创建（每分钟运行一次）")


def uninstall_service():
    """卸载 Windows 服务"""
    import subprocess

    # 尝试 nssm 卸载
    nssm_check = subprocess.run(['where', 'nssm'], capture_output=True, text=True)
    if nssm_check.returncode == 0:
        subprocess.run(['nssm', 'stop', 'HF_ScaleSync'], capture_output=True)
        subprocess.run(['nssm', 'remove', 'HF_ScaleSync', 'confirm'], capture_output=True)
        print("nssm 服务已卸载")
    else:
        subprocess.run(['schtasks', '/delete', '/tn', 'HF_ScaleSync', '/f'], capture_output=True)
        print("任务计划已删除")


# ============================================================
# 入口
# ============================================================

if __name__ == '__main__':
    config = load_config()
    logger = setup_logger(config)

    if len(sys.argv) > 1:
        if sys.argv[1] == '--install':
            install_as_service(config, logger)
        elif sys.argv[1] == '--uninstall':
            uninstall_service()
        elif sys.argv[1] == '--once':
            # 单次同步（调试用）
            do_sync(config, logger)
        else:
            print(f"未知参数: {sys.argv[1]}")
            print("用法:")
            print("  python scale_sync.py          # 前台运行")
            print("  python scale_sync.py --once   # 单次同步")
            print("  python scale_sync.py --install   # 安装为服务")
            print("  python scale_sync.py --uninstall # 卸载服务")
    else:
        run_loop(config, logger)
