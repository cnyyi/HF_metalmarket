import datetime
from utils.database import DBConnection


def _format_date(val, fmt='%Y-%m-%d'):
    """安全格式化日期：兼容 datetime 对象和字符串"""
    if not val:
        return ''
    if isinstance(val, str):
        return val[:10] if len(val) >= 10 else val
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.strftime(fmt)
    return str(val)


def _format_datetime(val):
    """安全格式化日期时间：兼容 datetime 对象和字符串"""
    if not val:
        return ''
    if isinstance(val, str):
        return val[:19] if len(val) >= 19 else val
    if isinstance(val, datetime.datetime):
        return val.strftime('%Y-%m-%d %H:%M:%S')
    return str(val)


class WaterMeter:

    @staticmethod
    def get_all(filter_type='all', merchant_id=None, page=1, page_size=10):
        with DBConnection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    wm.MeterID,
                    wm.MeterNumber,
                    wm.MeterType,
                    wm.InstallationLocation,
                    wm.MeterMultiplier,
                    wm.InstallationDate,
                    wm.InitReading,
                    wm.Status,
                    wm.CreateTime,
                    wm.UpdateTime,
                    cwm.ContractID,
                    m.MerchantName,
                    m.MerchantID
                FROM WaterMeter wm
                LEFT JOIN ContractWaterMeter cwm ON wm.MeterID = cwm.MeterID
                LEFT JOIN Contract c ON cwm.ContractID = c.ContractID
                LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
                WHERE 1=1
            """

            if merchant_id:
                query += " AND m.MerchantID = ?"
                params = (merchant_id,)
            else:
                params = ()

            cursor.execute(query, params)
            rows = cursor.fetchall()

        data = []
        for r in rows:
            data.append({
                'meter_id': r.MeterID,
                'meter_number': r.MeterNumber,
                'meter_type': r.MeterType,
                'installation_location': r.InstallationLocation or '',
                'meter_multiplier': float(r.MeterMultiplier) if r.MeterMultiplier else 1,
                'installation_date': _format_date(r.InstallationDate),
                'init_reading': float(r.InitReading) if r.InitReading else 0,
                'status': r.Status or '正常',
                'create_time': _format_datetime(r.CreateTime),
                'update_time': _format_datetime(r.UpdateTime),
                'contract_id': r.ContractID,
                'merchant_name': r.MerchantName or '',
                'merchant_id': r.MerchantID
            })

        return {
            'success': True,
            'data': data,
            'total': len(data),
            'page': page,
            'page_size': page_size
        }

    @staticmethod
    def get_by_id(meter_id):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    wm.MeterID,
                    wm.MeterNumber,
                    wm.MeterType,
                    wm.InstallationLocation,
                    wm.MeterMultiplier,
                    wm.InstallationDate,
                    wm.InitReading,
                    wm.Status,
                    wm.CreateTime,
                    wm.UpdateTime,
                    cwm.ContractID,
                    m.MerchantName,
                    m.MerchantID
                FROM WaterMeter wm
                LEFT JOIN ContractWaterMeter cwm ON wm.MeterID = cwm.MeterID
                LEFT JOIN Contract c ON cwm.ContractID = c.ContractID
                LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
                WHERE wm.MeterID = ?
            """, (meter_id,))

            row = cursor.fetchone()

            if row:
                return {
                    'meter_id': row.MeterID,
                    'meter_number': row.MeterNumber,
                    'meter_type': row.MeterType,
                    'installation_location': row.InstallationLocation or '',
                    'meter_multiplier': float(row.MeterMultiplier) if row.MeterMultiplier else 1,
                    'installation_date': _format_date(row.InstallationDate),
                    'init_reading': float(row.InitReading) if row.InitReading else 0,
                    'status': row.Status or '正常',
                    'contract_id': row.ContractID,
                    'merchant_name': row.MerchantName or '',
                    'merchant_id': row.MerchantID
                }
        return None

    @staticmethod
    def create(data):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO WaterMeter (
                    MeterNumber, MeterType,
                    InstallationLocation, MeterMultiplier, InstallationDate,
                    InitReading, Status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data['meter_number'],
                data['meter_type'],
                data.get('installation_location', ''),
                data.get('meter_multiplier', 1),
                data.get('installation_date', None),
                data.get('init_reading', 0),
                data.get('status', '正常')
            ))

            cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
            meter_id = cursor.fetchone()[0]
            conn.commit()

        return meter_id

    @staticmethod
    def update(meter_id, data):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE WaterMeter SET
                    MeterNumber = ?,
                    MeterType = ?,
                    MeterMultiplier = ?,
                    InstallationDate = ?,
                    InitReading = ?,
                    Status = ?,
                    UpdateTime = GETDATE()
                WHERE MeterID = ?
            """, (
                data.get('meter_number', ''),
                data.get('meter_type', 'water'),
                data.get('meter_multiplier', 1),
                data.get('installation_date', None),
                data.get('init_reading', 0),
                data.get('status', '正常'),
                meter_id
            ))

            conn.commit()

        return True

    @staticmethod
    def delete(meter_id):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM ContractWaterMeter WHERE MeterID = ?", (meter_id,))
            cursor.execute("DELETE FROM WaterMeter WHERE MeterID = ?", (meter_id,))

            conn.commit()

        return True

    @staticmethod
    def link_to_contract(meter_id, contract_id, start_reading=0):
        with DBConnection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT COUNT(*) FROM ContractWaterMeter WHERE MeterID = ?", (meter_id,))
                if cursor.fetchone()[0] > 0:
                    cursor.execute("""
                        UPDATE ContractWaterMeter SET
                            ContractID = ?,
                            StartReading = ?
                        WHERE MeterID = ?
                    """, (contract_id, start_reading, meter_id))
                else:
                    cursor.execute("""
                        INSERT INTO ContractWaterMeter (MeterID, ContractID, StartReading)
                        VALUES (?, ?, ?)
                    """, (meter_id, contract_id, start_reading))

                cursor.execute("""
                    UPDATE WaterMeter SET
                        InitReading = ?,
                        UpdateTime = GETDATE()
                    WHERE MeterID = ?
                """, (start_reading, meter_id))

                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                raise e

    @staticmethod
    def check_contract_link(meter_id):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM ContractWaterMeter cwm
                INNER JOIN Contract c ON cwm.ContractID = c.ContractID
                WHERE cwm.MeterID = ?
                  AND c.StartDate <= GETDATE()
                  AND DATEADD(MONTH, 3, c.EndDate) >= GETDATE()
            """, (meter_id,))

            count = cursor.fetchone()[0]

        return count > 0

    @staticmethod
    def unlink_from_contract(meter_id):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM ContractWaterMeter WHERE MeterID = ?", (meter_id,))
            conn.commit()

        return True


class ElectricityMeter:

    @staticmethod
    def get_all(filter_type='all', merchant_id=None, page=1, page_size=10):
        with DBConnection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    em.MeterID,
                    em.MeterNumber,
                    em.MeterType,
                    em.InstallationLocation,
                    em.MeterMultiplier,
                    em.InstallationDate,
                    em.InitReading,
                    em.Status,
                    em.CreateTime,
                    em.UpdateTime,
                    cem.ContractID,
                    m.MerchantName,
                    m.MerchantID
                FROM ElectricityMeter em
                LEFT JOIN ContractElectricityMeter cem ON em.MeterID = cem.MeterID
                LEFT JOIN Contract c ON cem.ContractID = c.ContractID
                LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
                WHERE 1=1
            """

            if merchant_id:
                query += " AND m.MerchantID = ?"
                params = (merchant_id,)
            else:
                params = ()

            cursor.execute(query, params)
            rows = cursor.fetchall()

        data = []
        for r in rows:
            data.append({
                'meter_id': r.MeterID,
                'meter_number': r.MeterNumber,
                'meter_type': r.MeterType,
                'installation_location': r.InstallationLocation or '',
                'meter_multiplier': float(r.MeterMultiplier) if r.MeterMultiplier else 1,
                'installation_date': _format_date(r.InstallationDate),
                'init_reading': float(r.InitReading) if r.InitReading else 0,
                'status': r.Status or '正常',
                'create_time': _format_datetime(r.CreateTime),
                'update_time': _format_datetime(r.UpdateTime),
                'contract_id': r.ContractID,
                'merchant_name': r.MerchantName or '',
                'merchant_id': r.MerchantID
            })

        return {
            'success': True,
            'data': data,
            'total': len(data),
            'page': page,
            'page_size': page_size
        }

    @staticmethod
    def get_by_id(meter_id):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    em.MeterID,
                    em.MeterNumber,
                    em.MeterType,
                    em.InstallationLocation,
                    em.MeterMultiplier,
                    em.InstallationDate,
                    em.InitReading,
                    em.Status,
                    em.CreateTime,
                    em.UpdateTime,
                    cem.ContractID,
                    m.MerchantName,
                    m.MerchantID
                FROM ElectricityMeter em
                LEFT JOIN ContractElectricityMeter cem ON em.MeterID = cem.MeterID
                LEFT JOIN Contract c ON cem.ContractID = c.ContractID
                LEFT JOIN Merchant m ON c.MerchantID = m.MerchantID
                WHERE em.MeterID = ?
            """, (meter_id,))

            row = cursor.fetchone()

            if row:
                return {
                    'meter_id': row.MeterID,
                    'meter_number': row.MeterNumber,
                    'meter_type': row.MeterType,
                    'installation_location': row.InstallationLocation or '',
                    'meter_multiplier': float(row.MeterMultiplier) if row.MeterMultiplier else 1,
                    'installation_date': _format_date(row.InstallationDate),
                    'init_reading': float(row.InitReading) if row.InitReading else 0,
                    'status': row.Status or '正常',
                    'contract_id': row.ContractID,
                    'merchant_name': row.MerchantName or '',
                    'merchant_id': row.MerchantID
                }
        return None

    @staticmethod
    def create(data):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO ElectricityMeter (
                    MeterNumber, MeterType,
                    InstallationLocation, MeterMultiplier, InstallationDate,
                    InitReading, Status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data['meter_number'],
                data['meter_type'],
                data.get('installation_location', ''),
                data.get('meter_multiplier', 1),
                data.get('installation_date', None),
                data.get('init_reading', 0),
                data.get('status', '正常')
            ))

            cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
            meter_id = cursor.fetchone()[0]
            conn.commit()

        return meter_id

    @staticmethod
    def update(meter_id, data):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE ElectricityMeter SET
                    MeterNumber = ?,
                    MeterType = ?,
                    MeterMultiplier = ?,
                    InstallationDate = ?,
                    InitReading = ?,
                    Status = ?,
                    UpdateTime = GETDATE()
                WHERE MeterID = ?
            """, (
                data.get('meter_number', ''),
                data.get('meter_type', 'electricity'),
                data.get('meter_multiplier', 1),
                data.get('installation_date', None),
                data.get('init_reading', 0),
                data.get('status', '正常'),
                meter_id
            ))

            conn.commit()

        return True

    @staticmethod
    def delete(meter_id):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM ContractElectricityMeter WHERE MeterID = ?", (meter_id,))
            cursor.execute("DELETE FROM ElectricityMeter WHERE MeterID = ?", (meter_id,))

            conn.commit()

        return True

    @staticmethod
    def link_to_contract(meter_id, contract_id, start_reading=0):
        with DBConnection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT COUNT(*) FROM ContractElectricityMeter WHERE MeterID = ?", (meter_id,))
                if cursor.fetchone()[0] > 0:
                    cursor.execute("""
                        UPDATE ContractElectricityMeter SET
                            ContractID = ?,
                            StartReading = ?
                        WHERE MeterID = ?
                    """, (contract_id, start_reading, meter_id))
                else:
                    cursor.execute("""
                        INSERT INTO ContractElectricityMeter (MeterID, ContractID, StartReading)
                        VALUES (?, ?, ?)
                    """, (meter_id, contract_id, start_reading))

                cursor.execute("""
                    UPDATE ElectricityMeter SET
                        InitReading = ?,
                        UpdateTime = GETDATE()
                    WHERE MeterID = ?
                """, (start_reading, meter_id))

                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                raise e

    @staticmethod
    def check_contract_link(meter_id):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM ContractElectricityMeter cem
                INNER JOIN Contract c ON cem.ContractID = c.ContractID
                WHERE cem.MeterID = ?
                  AND c.StartDate <= GETDATE()
                  AND DATEADD(MONTH, 3, c.EndDate) >= GETDATE()
            """, (meter_id,))

            count = cursor.fetchone()[0]

        return count > 0

    @staticmethod
    def unlink_from_contract(meter_id):
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM ContractElectricityMeter WHERE MeterID = ?", (meter_id,))
            conn.commit()

        return True
