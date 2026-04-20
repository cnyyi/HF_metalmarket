import pyodbc
from datetime import datetime

# Access
access_conn = pyodbc.connect(
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    r'DBQ=D:\BaiduSyncdisk\HF_metalmarket\Database.mdb;'
    r'PWD=www.fzatw.com'
)
access_cur = access_conn.cursor()

# 查 A202604190029
access_cur.execute(
    "SELECT 流水号, 车号, 过磅类型, 发货单位, 收货单位, 货名, 规格,"
    "毛重, 皮重, 净重, 扣重, 实重, 单价, 金额, 过磅费,"
    "毛重司磅员, 皮重司磅员, 毛重磅号, 皮重磅号,"
    "毛重时间, 皮重时间, 一次过磅时间, 二次过磅时间,"
    "更新人, 更新时间, 备注, RecordFinish "
    "FROM 称重信息 WHERE 流水号='A202604190029'"
)
cols = [d[0] for d in access_cur.description]
row = access_cur.fetchone()
data = dict(zip(cols, row))
access_conn.close()

WEIGH_TYPE_MAP = {'PO': '皮毛重', 'SO': '毛重', 'OO': '皮重', 'IO': '入口'}

now = datetime.now()
serial = data['流水号']
scale_time = data['二次过磅时间'] or data['一次过磅时间'] or data['更新时间'] or now

params = (
    1,  # ScaleID
    None,  # MerchantID
    serial,
    WEIGH_TYPE_MAP.get(data['过磅类型'], data['过磅类型']),
    data['毛重'] or 0,
    data['皮重'] or 0,
    data['净重'] or 0,
    data['扣重'] or 0,
    data['实重'] or 0,
    data['单价'] or 0,
    data['金额'] or 0,
    data['过磅费'] or 0,
    data['车号'],
    data['货名'] or data['规格'],
    data['发货单位'],
    data['收货单位'],
    data['毛重时间'],
    data['皮重时间'],
    scale_time,
    data['毛重司磅员'],
    data['皮重司磅员'],
    data['更新人'] or '系统同步',
    data['备注'] or '',
    now,
    data['更新时间'],
    0,  # IsModified
    None,  # ModifiedFromRecordID
)

# 写入 SQL Server
sql_conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=yyi.myds.me;'
    'DATABASE=hf_metalmarket;'
    'UID=sa;'
    'PWD=yyI.123212'
)
sql_cur = sql_conn.cursor()

try:
    sql_cur.execute("""
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
    sql_conn.commit()
    print(f"OK 已手动插入: {serial}")
except Exception as e:
    print(f"插入失败: {e}")
    sql_conn.rollback()

sql_conn.close()
