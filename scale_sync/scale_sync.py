"""
宏发金属交易市场 - 过磅数据同步服务
从 Access 过磅软件数据库同步数据到 SQL Server

功能：
  1. 增量同步：按流水号上传最新记录
  2. 变更检测：对比毛重、皮重、净重、毛重时间、皮重时间、过磅费，
     任意不一致则以 Access 为准直接更新 SQL Server 记录

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
    "access_db_path": r"D:\BaiduSyncdisk\HF_metalmarket\Database.mdb",
    "access_password": "",

    "sql_server": "",
    "sql_database": "hf_metalmarket",
    "sql_user": "",
    "sql_password": "",

    "default_scale_id": 1,
    "sync_interval": 60,
    "only_finished": True,
    "change_detection_days": 3,
    "log_level": "INFO"
}

ENV_MAPPING = {
    "access_password": "SYNC_ACCESS_PASSWORD",
    "sql_server": "SYNC_SQL_SERVER",
    "sql_database": "SYNC_SQL_DATABASE",
    "sql_user": "SYNC_SQL_USER",
    "sql_password": "SYNC_SQL_PASSWORD",
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        print(f"已生成默认配置文件: {CONFIG_FILE}")
        print("请根据实际情况修改配置后重新运行。")
        config = dict(DEFAULT_CONFIG)
    else:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)

    for config_key, env_key in ENV_MAPPING.items():
        env_val = os.environ.get(env_key)
        if env_val:
            config[config_key] = env_val

    return config


# ============================================================
# 日志
# ============================================================

def setup_logger(config):
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger('ScaleSync')
    logger.setLevel(getattr(logging, config.get('log_level', 'INFO')))

    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(ch)

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
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        f'DBQ={config["access_db_path"]};'
        f'PWD={config["access_password"]}'
    )
    return pyodbc.connect(conn_str)


def get_sql_connection(config):
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


def row_to_params(data, columns, config):
    scale_id = config.get('default_scale_id', 1)
    now = datetime.now()

    serial_no = data.get('流水号', '')
    weigh_type = WEIGH_TYPE_MAP.get(data.get('过磅类型', ''), data.get('过磅类型', ''))
    scale_time = data.get('二次过磅时间') or data.get('一次过磅时间') or data.get('更新时间') or now
    product_name = data.get('货名', '') or data.get('规格', '')
    memo = data.get('备注', '') or ''
    source_update_time = data.get('更新时间')

    params = (
        scale_id,
        None,
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
        source_update_time,
        0,
        None,
    )
    return serial_no, params


# ============================================================
# 同步逻辑 - 阶段1: 增量上传新记录
# ============================================================

def get_last_synced_serial(sql_conn):
    cursor = sql_conn.cursor()
    cursor.execute("""
        SELECT MAX(SourceSerialNo) FROM ScaleRecord
        WHERE SourceSerialNo IS NOT NULL
    """)
    row = cursor.fetchone()
    return row[0] if row and row[0] else None


def fetch_new_records(access_conn, last_serial, only_finished=True):
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
        sql += " AND 流水号 > ?"

    if only_finished:
        sql += " AND RecordFinish = 1"

    sql += " ORDER BY 流水号 ASC"

    if last_serial:
        cursor.execute(sql, (last_serial,))
    else:
        cursor.execute(sql)

    return cursor.fetchall(), [desc[0] for desc in cursor.description]


def insert_new_records(sql_conn, records, columns, config, logger):
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

        if len(batch_params) >= batch_size:
            inserted, skipped = _execute_batch(
                sql_conn, insert_sql, batch_params, inserted, skipped, logger
            )
            batch_params = []

    if batch_params:
        inserted, skipped = _execute_batch(
            sql_conn, insert_sql, batch_params, inserted, skipped, logger
        )

    logger.info(f"新增同步完成: 插入 {inserted} 条，跳过 {skipped} 条")
    return inserted


def _execute_batch(sql_conn, insert_sql, batch_params, inserted, skipped, logger):
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


# ============================================================
# 同步逻辑 - 阶段2: 变更检测与更新
# ============================================================

CHANGE_FIELDS = [
    ('毛重', 'GrossWeight'),
    ('皮重', 'TareWeight'),
    ('净重', 'NetWeight'),
    ('毛重时间', 'GrossTime'),
    ('皮重时间', 'TareTime'),
    ('过磅费', 'ScaleFee'),
]


def _values_equal(v1, v2):
    if v1 is None and v2 is None:
        return True
    if v1 is None or v2 is None:
        return False
    if isinstance(v1, float) or isinstance(v2, float):
        return abs(float(v1) - float(v2)) < 0.001
    return v1 == v2


def fetch_access_recent_records(access_conn, detection_days, only_finished=True):
    cursor = access_conn.cursor()
    cutoff = datetime.now() - timedelta(days=detection_days)

    sql = """
        SELECT
            流水号, 车号, 过磅类型, 发货单位, 收货单位, 货名, 规格,
            毛重, 皮重, 净重, 扣重, 实重, 单价, 金额, 过磅费,
            毛重司磅员, 皮重司磅员, 毛重磅号, 皮重磅号,
            毛重时间, 皮重时间,
            一次过磅时间, 二次过磅时间,
            更新人, 更新时间, 备注, RecordFinish
        FROM 称重信息
        WHERE 更新时间 >= ?
    """

    if only_finished:
        sql += " AND RecordFinish = 1"

    cursor.execute(sql, (cutoff,))
    columns = [desc[0] for desc in cursor.description]

    result = {}
    for row in cursor.fetchall():
        data = dict(zip(columns, row))
        serial = data.get('流水号', '')
        if serial:
            result[serial] = data
    return result


def fetch_sql_records_for_comparison(sql_conn, serial_nos):
    if not serial_nos:
        return {}

    cursor = sql_conn.cursor()
    placeholders = ','.join(['?'] * len(serial_nos))

    cursor.execute(f"""
        SELECT
            ScaleRecordID, SourceSerialNo,
            GrossWeight, TareWeight, NetWeight,
            GrossTime, TareTime, ScaleFee
        FROM ScaleRecord
        WHERE SourceSerialNo IN ({placeholders})
          AND IsModified = 0
    """, list(serial_nos))

    result = {}
    for row in cursor.fetchall():
        record_id = row[0]
        serial = row[1]
        sql_values = {
            'GrossWeight': row[2],
            'TareWeight': row[3],
            'NetWeight': row[4],
            'GrossTime': row[5],
            'TareTime': row[6],
            'ScaleFee': row[7],
        }
        if serial not in result:
            result[serial] = (record_id, sql_values)
    return result


def detect_and_update_changes(sql_conn, access_conn, config, logger):
    detection_days = config.get('change_detection_days', 3)

    access_data = fetch_access_recent_records(
        access_conn, detection_days,
        only_finished=config.get('only_finished', True)
    )
    if not access_data:
        logger.debug("变更检测: Access 端无最近更新的记录")
        return 0

    logger.debug(f"变更检测: Access 端最近 {detection_days} 天有 {len(access_data)} 条记录")

    serial_nos = list(access_data.keys())
    sql_records = fetch_sql_records_for_comparison(sql_conn, serial_nos)
    if not sql_records:
        logger.debug("变更检测: 这些记录尚未同步到 SQL Server，无需变更检测")
        return 0

    logger.debug(f"变更检测: 其中 {len(sql_records)} 条已在 SQL Server 中")

    updated_count = 0
    cursor = sql_conn.cursor()

    for serial_no, (record_id, sql_values) in sql_records.items():
        access_row = access_data.get(serial_no)
        if not access_row:
            continue

        changed_fields = []
        for access_field, sql_field in CHANGE_FIELDS:
            access_val = access_row.get(access_field)
            sql_val = sql_values.get(sql_field)
            if not _values_equal(access_val, sql_val):
                changed_fields.append(access_field)

        if not changed_fields:
            continue

        logger.info(
            f"发现变更: 流水号 {serial_no}, 变更字段: {', '.join(changed_fields)}"
        )

        try:
            cursor.execute("""
                UPDATE ScaleRecord SET
                    GrossWeight = ?,
                    TareWeight = ?,
                    NetWeight = ?,
                    GrossTime = ?,
                    TareTime = ?,
                    ScaleFee = ?,
                    DeductWeight = ?,
                    ActualWeight = ?,
                    UnitPrice = ?,
                    TotalAmount = ?,
                    LicensePlate = ?,
                    ProductName = ?,
                    SenderName = ?,
                    ReceiverName = ?,
                    ScaleTime = ?,
                    GrossOperator = ?,
                    TareOperator = ?,
                    Operator = ?,
                    Description = ?,
                    SourceUpdateTime = ?
                WHERE ScaleRecordID = ?
            """, (
                access_row.get('毛重', 0) or 0,
                access_row.get('皮重', 0) or 0,
                access_row.get('净重', 0) or 0,
                access_row.get('毛重时间'),
                access_row.get('皮重时间'),
                access_row.get('过磅费', 0) or 0,
                access_row.get('扣重', 0) or 0,
                access_row.get('实重', 0) or 0,
                access_row.get('单价', 0) or 0,
                access_row.get('金额', 0) or 0,
                access_row.get('车号', ''),
                access_row.get('货名', '') or access_row.get('规格', ''),
                access_row.get('发货单位', ''),
                access_row.get('收货单位', ''),
                access_row.get('二次过磅时间') or access_row.get('一次过磅时间') or access_row.get('更新时间'),
                access_row.get('毛重司磅员', ''),
                access_row.get('皮重司磅员', ''),
                access_row.get('更新人', '') or '系统同步',
                access_row.get('备注', '') or '',
                access_row.get('更新时间'),
                record_id,
            ))
            updated_count += 1
        except Exception as e:
            logger.error(f"更新记录失败 [流水号 {serial_no}]: {e}")

    if updated_count > 0:
        try:
            sql_conn.commit()
            logger.info(f"变更检测完成: 更新 {updated_count} 条记录")
        except Exception as e:
            logger.error(f"变更检测提交失败: {e}")
            sql_conn.rollback()

    return updated_count


# ============================================================
# 同步逻辑 - 阶段3: 补漏（检测已遗漏的已完成记录）
# ============================================================

def fetch_missing_records(access_conn, sql_conn, detection_days, config, logger):
    """
    对比 Access 中已完成的记录与 SQL Server 已同步记录，
    找出缺失的流水号并补录。
    
    解决场景：跨天过磅（皮重录入时 RecordFinish=0 被跳过，
    毛重录入后 RecordFinish=1 但流水号已小于 last_serial）
    """
    cutoff = datetime.now() - timedelta(days=detection_days)

    # 1) 从 Access 取最近 N 天 RecordFinish=1 的流水号
    access_cursor = access_conn.cursor()
    access_cursor.execute("""
        SELECT 流水号
        FROM 称重信息
        WHERE 更新时间 >= ?
          AND RecordFinish = 1
          AND 流水号 IS NOT NULL
          AND 流水号 <> ''
        ORDER BY 流水号 ASC
    """, (cutoff,))
    access_serials = set(row[0] for row in access_cursor.fetchall())

    if not access_serials:
        logger.debug("补漏检测: Access 端无符合条件的记录")
        return 0

    # 2) 从 SQL Server 取同期已同步的流水号（分批查询避免 IN 列表过长）
    sql_serials = set()
    serial_list = list(access_serials)
    batch_size = 500
    sql_cursor = sql_conn.cursor()

    for i in range(0, len(serial_list), batch_size):
        batch = serial_list[i:i + batch_size]
        placeholders = ','.join(['?'] * len(batch))
        sql_cursor.execute(f"""
            SELECT SourceSerialNo
            FROM ScaleRecord
            WHERE SourceSerialNo IN ({placeholders})
        """, batch)
        for row in sql_cursor.fetchall():
            sql_serials.add(row[0])

    # 3) 差集 = 缺失的流水号
    missing_serials = access_serials - sql_serials

    if not missing_serials:
        logger.debug("补漏检测: 无缺失记录")
        return 0

    logger.info(f"补漏检测: 发现 {len(missing_serials)} 条缺失记录")

    # 4) 从 Access 取缺失记录的完整数据（分批查询避免 IN 列表过长）
    columns = None
    missing_rows = []
    missing_list_sorted = sorted(missing_serials)

    for i in range(0, len(missing_list_sorted), batch_size):
        batch = missing_list_sorted[i:i + batch_size]
        placeholders = ','.join(['?'] * len(batch))
        access_cursor.execute(f"""
            SELECT
                流水号, 车号, 过磅类型, 发货单位, 收货单位, 货名, 规格,
                毛重, 皮重, 净重, 扣重, 实重, 单价, 金额, 过磅费,
                毛重司磅员, 皮重司磅员, 毛重磅号, 皮重磅号,
                毛重时间, 皮重时间,
                一次过磅时间, 二次过磅时间,
                更新人, 更新时间, 备注, RecordFinish
            FROM 称重信息
            WHERE 流水号 IN ({placeholders})
            ORDER BY 流水号 ASC
        """, batch)

        if columns is None:
            columns = [desc[0] for desc in access_cursor.description]
        missing_rows.extend(access_cursor.fetchall())

    # 5) 插入 SQL Server
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
    cursor = sql_conn.cursor()

    for row in missing_rows:
        data = dict(zip(columns, row))
        serial_no, params = row_to_params(data, columns, config)

        if not serial_no:
            skipped += 1
            continue

        try:
            cursor.execute(insert_sql, params)
            inserted += 1
        except pyodbc.IntegrityError:
            skipped += 1
            logger.debug(f"补漏跳过重复流水号: {serial_no}")
        except Exception as e:
            logger.error(f"补漏插入失败 [{serial_no}]: {e}")
            skipped += 1

    if inserted > 0:
        try:
            sql_conn.commit()
            logger.info(f"补漏同步完成: 插入 {inserted} 条，跳过 {skipped} 条")
        except Exception as e:
            logger.error(f"补漏提交失败: {e}")
            sql_conn.rollback()

    return inserted

def do_sync(config, logger):
    try:
        access_conn = get_access_connection(config)
        sql_conn = get_sql_connection(config)
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return

    try:
        # ---- 阶段1: 增量上传新记录 ----
        last_serial = get_last_synced_serial(sql_conn)
        logger.debug(f"最后已同步流水号: {last_serial or '无'}")

        records, columns = fetch_new_records(
            access_conn, last_serial,
            only_finished=config.get('only_finished', True)
        )

        inserted = 0
        if records:
            logger.info(f"发现 {len(records)} 条新记录，开始同步...")
            inserted = insert_new_records(sql_conn, records, columns, config, logger)

        # ---- 阶段2: 变更检测与更新 ----
        updated = detect_and_update_changes(sql_conn, access_conn, config, logger)

        # ---- 阶段3: 补漏检测 ----
        missing_days = config.get('missing_detection_days', 7)
        missing = fetch_missing_records(
            access_conn, sql_conn, missing_days, config, logger
        )

        # ---- 汇总 ----
        if inserted == 0 and updated == 0 and missing == 0:
            logger.debug("无新记录，无变更，无遗漏")
        else:
            logger.info(f"本次同步: 新增 {inserted} 条，变更更新 {updated} 条，补漏 {missing} 条")

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
    interval = config.get('sync_interval', 60)
    logger.info(f"过磅数据同步服务启动，同步间隔 {interval} 秒")
    logger.info(f"Access 数据库: {config['access_db_path']}")
    logger.info(f"SQL Server: {config['sql_server']}/{config['sql_database']}")
    logger.info(f"变更检测回查天数: {config.get('change_detection_days', 3)}")
    logger.info(f"补漏检测回查天数: {config.get('missing_detection_days', 7)}")

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
    import subprocess

    script_path = os.path.abspath(__file__)
    python_path = sys.executable

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
        subprocess.run([
            'schtasks', '/create', '/tn', task_name, '/tr',
            f'"{python_path}" "{script_path}"',
            '/sc', 'minute', '/mo', '1', '/ru', 'SYSTEM',
            '/f'
        ], check=True)
        print(f"任务计划 {task_name} 已创建（每分钟运行一次）")


def uninstall_service():
    import subprocess

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
