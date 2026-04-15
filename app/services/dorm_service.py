# -*- coding: utf-8 -*-
"""
宿舍管理服务层
负责房间管理、入住/退房、电表抄表、月度账单等业务逻辑
"""
import logging
import os
from datetime import datetime, date
from utils.database import DBConnection

logger = logging.getLogger(__name__)


class DormService:
    """宿舍管理服务"""

    # ========== 房间管理 ==========

    def get_rooms(self, page=1, per_page=10, search=None, status=None, room_type=None):
        """获取房间列表"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = """
                SELECT dr.RoomID, dr.RoomNumber, dr.RoomType, dr.Area,
                       dr.MonthlyRent, dr.WaterQuota, dr.ElectricityUnitPrice,
                       dr.MeterNumber, dr.LastReading, dr.Status, dr.Description,
                       dr.CreateTime,
                       o.TenantName, o.TenantPhone, o.TenantType, o.OccupancyID
                FROM DormRoom dr
                LEFT JOIN DormOccupancy o ON dr.RoomID = o.RoomID AND o.Status = N'在住'
            """
            count_query = "SELECT COUNT(*) FROM DormRoom dr"

            conditions = []
            params = []

            if search:
                conditions.append("(dr.RoomNumber LIKE ? OR dr.MeterNumber LIKE ?)")
                p = f'%{search}%'
                params.extend([p, p])

            if status:
                conditions.append("dr.Status = ?")
                params.append(status)

            if room_type:
                conditions.append("dr.RoomType = ?")
                params.append(room_type)

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause

            # 总数
            cursor.execute(count_query, tuple(params))
            total_count = cursor.fetchone()[0]

            # 分页
            offset = (page - 1) * per_page
            base_query += " ORDER BY dr.RoomNumber OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, tuple(params))
            rows = cursor.fetchall()

            items = []
            for row in rows:
                items.append({
                    'room_id': row.RoomID,
                    'room_number': row.RoomNumber,
                    'room_type': row.RoomType,
                    'area': float(row.Area) if row.Area else None,
                    'monthly_rent': float(row.MonthlyRent),
                    'water_quota': float(row.WaterQuota),
                    'electricity_unit_price': float(row.ElectricityUnitPrice),
                    'meter_number': row.MeterNumber or '',
                    'last_reading': float(row.LastReading) if row.LastReading else 0,
                    'status': row.Status,
                    'description': row.Description or '',
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
                    'tenant_name': row.TenantName or '',
                    'tenant_phone': row.TenantPhone or '',
                    'tenant_type': row.TenantType or '',
                    'occupancy_id': row.OccupancyID,
                })

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

            return {
                'items': items,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page
            }

    def get_room_by_id(self, room_id):
        """获取房间详情"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT RoomID, RoomNumber, RoomType, Area,
                       MonthlyRent, WaterQuota, ElectricityUnitPrice,
                       MeterNumber, LastReading, Status, Description,
                       CreateTime, UpdateTime
                FROM DormRoom WHERE RoomID = ?
            """, room_id)
            return cursor.fetchone()

    def create_room(self, room_number, room_type='单间', area=None,
                    monthly_rent=0, water_quota=0, electricity_unit_price=1.0,
                    meter_number=None, description=None):
        """新增房间"""
        if not room_number:
            raise ValueError("房间编号不能为空")

        with DBConnection() as conn:
            cursor = conn.cursor()
            # 检查编号唯一性
            cursor.execute("SELECT 1 FROM DormRoom WHERE RoomNumber = ?", room_number)
            if cursor.fetchone():
                raise ValueError(f"房间编号 {room_number} 已存在")

            cursor.execute("""
                INSERT INTO DormRoom (RoomNumber, RoomType, Area, MonthlyRent, WaterQuota,
                                      ElectricityUnitPrice, MeterNumber, Description)
                OUTPUT INSERTED.RoomID
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, room_number, room_type, area, monthly_rent, water_quota,
                 electricity_unit_price, meter_number, description)

            row = cursor.fetchone()
            new_id = row[0] if row else None
            conn.commit()
            return new_id

    def update_room(self, room_id, **kwargs):
        """更新房间信息"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            # 检查房间状态——已住人的房间不允许改租金等关键字段
            cursor.execute("SELECT Status FROM DormRoom WHERE RoomID = ?", room_id)
            row = cursor.fetchone()
            if not row:
                raise ValueError("房间不存在")

            updates = []
            params = []

            allowed_fields = ['room_type', 'area', 'monthly_rent', 'water_quota',
                              'electricity_unit_price', 'meter_number', 'status', 'description']
            for field in allowed_fields:
                if field in kwargs and kwargs[field] is not None:
                    db_field = ''.join(word.capitalize() for word in field.split('_'))
                    updates.append(f"{db_field} = ?")
                    params.append(kwargs[field])

            if not updates:
                return

            updates.append("UpdateTime = GETDATE()")
            params.append(room_id)

            sql = f"UPDATE DormRoom SET {', '.join(updates)} WHERE RoomID = ?"
            cursor.execute(sql, tuple(params))
            conn.commit()

    def delete_room(self, room_id):
        """删除房间（仅空闲可删）"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Status FROM DormRoom WHERE RoomID = ?", room_id)
            row = cursor.fetchone()
            if not row:
                raise ValueError("房间不存在")
            if row.Status != '空闲':
                raise ValueError("只能删除空闲状态的房间")

            # 检查有无入住历史
            cursor.execute("SELECT COUNT(*) FROM DormOccupancy WHERE RoomID = ?", room_id)
            if cursor.fetchone()[0] > 0:
                raise ValueError("该房间有入住历史记录，无法删除，建议改为维修中状态")

            cursor.execute("DELETE FROM DormRoom WHERE RoomID = ?", room_id)
            conn.commit()

    # ========== 入住管理 ==========

    def get_occupancies(self, page=1, per_page=10, status=None, search=None):
        """获取入住记录列表"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = """
                SELECT o.OccupancyID, o.RoomID, dr.RoomNumber, dr.RoomType,
                       o.TenantType, o.MerchantID, o.TenantName, o.TenantPhone,
                       o.IDCardNumber, o.IDCardFrontPhoto, o.IDCardBackPhoto,
                       o.MoveInDate, o.MoveOutDate, o.Status, o.Description,
                       o.CreateTime,
                       m.MerchantName
                FROM DormOccupancy o
                INNER JOIN DormRoom dr ON o.RoomID = dr.RoomID
                LEFT JOIN Merchant m ON o.MerchantID = m.MerchantID
            """
            count_query = """
                SELECT COUNT(*) FROM DormOccupancy o
                INNER JOIN DormRoom dr ON o.RoomID = dr.RoomID
                LEFT JOIN Merchant m ON o.MerchantID = m.MerchantID
            """

            conditions = []
            params = []

            if status:
                conditions.append("o.Status = ?")
                params.append(status)

            if search:
                conditions.append("(o.TenantName LIKE ? OR o.TenantPhone LIKE ? OR dr.RoomNumber LIKE ? OR m.MerchantName LIKE ?)")
                p = f'%{search}%'
                params.extend([p, p, p, p])

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause

            cursor.execute(count_query, tuple(params))
            total_count = cursor.fetchone()[0]

            offset = (page - 1) * per_page
            base_query += " ORDER BY o.OccupancyID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, tuple(params))
            rows = cursor.fetchall()

            items = []
            for row in rows:
                items.append({
                    'occupancy_id': row.OccupancyID,
                    'room_id': row.RoomID,
                    'room_number': row.RoomNumber,
                    'room_type': row.RoomType,
                    'tenant_type': row.TenantType,
                    'merchant_id': row.MerchantID,
                    'merchant_name': row.MerchantName or '',
                    'tenant_name': row.TenantName,
                    'tenant_phone': row.TenantPhone or '',
                    'id_card_number': row.IDCardNumber or '',
                    'id_card_front_photo': row.IDCardFrontPhoto or '',
                    'id_card_back_photo': row.IDCardBackPhoto or '',
                    'move_in_date': row.MoveInDate.strftime('%Y-%m-%d') if row.MoveInDate else '',
                    'move_out_date': row.MoveOutDate.strftime('%Y-%m-%d') if row.MoveOutDate else '',
                    'status': row.Status,
                    'description': row.Description or '',
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
                })

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

            return {
                'items': items,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page
            }

    def check_in(self, room_id, tenant_type='个人', merchant_id=None,
                 tenant_name=None, tenant_phone=None,
                 id_card_number=None, id_card_front_photo=None, id_card_back_photo=None,
                 move_in_date=None, description=None):
        """办理入住"""
        if not tenant_name:
            raise ValueError("租户姓名不能为空")
        if not move_in_date:
            raise ValueError("入住日期不能为空")
        if tenant_type == '商户' and not merchant_id:
            raise ValueError("商户类型租户必须选择商户")

        with DBConnection() as conn:
            cursor = conn.cursor()

            # 检查房间状态
            cursor.execute("SELECT Status FROM DormRoom WHERE RoomID = ?", room_id)
            room = cursor.fetchone()
            if not room:
                raise ValueError("房间不存在")
            if room.Status == '已住':
                raise ValueError("该房间已有在住人员，请先办理退房")

            # 创建入住记录
            cursor.execute("""
                INSERT INTO DormOccupancy (RoomID, TenantType, MerchantID, TenantName, TenantPhone,
                                           IDCardNumber, IDCardFrontPhoto, IDCardBackPhoto,
                                           MoveInDate, Status, Description)
                OUTPUT INSERTED.OccupancyID
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, N'在住', ?)
            """, room_id, tenant_type, merchant_id, tenant_name, tenant_phone,
                 id_card_number, id_card_front_photo, id_card_back_photo,
                 move_in_date, description)

            row = cursor.fetchone()
            occupancy_id = row[0] if row else None

            # 更新房间状态
            cursor.execute("UPDATE DormRoom SET Status = N'已住', UpdateTime = GETDATE() WHERE RoomID = ?", room_id)

            conn.commit()
            return occupancy_id

    def check_out(self, occupancy_id, move_out_date=None):
        """办理退房"""
        if not move_out_date:
            move_out_date = date.today().strftime('%Y-%m-%d')

        with DBConnection() as conn:
            cursor = conn.cursor()

            # 获取入住记录
            cursor.execute("""
                SELECT OccupancyID, RoomID, Status FROM DormOccupancy WHERE OccupancyID = ?
            """, occupancy_id)
            row = cursor.fetchone()
            if not row:
                raise ValueError("入住记录不存在")
            if row.Status == '已退房':
                raise ValueError("该记录已退房")

            room_id = row.RoomID

            # 更新入住记录
            cursor.execute("""
                UPDATE DormOccupancy SET Status = N'已退房', MoveOutDate = ?, UpdateTime = GETDATE()
                WHERE OccupancyID = ?
            """, move_out_date, occupancy_id)

            # 更新房间状态
            cursor.execute("UPDATE DormRoom SET Status = N'空闲', UpdateTime = GETDATE() WHERE RoomID = ?", room_id)

            conn.commit()

    def get_occupancy_by_id(self, occupancy_id):
        """获取入住记录详情"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.OccupancyID, o.RoomID, dr.RoomNumber,
                       o.TenantType, o.MerchantID, o.TenantName, o.TenantPhone,
                       o.IDCardNumber, o.IDCardFrontPhoto, o.IDCardBackPhoto,
                       o.MoveInDate, o.MoveOutDate, o.Status, o.Description,
                       o.CreateTime, o.UpdateTime,
                       m.MerchantName
                FROM DormOccupancy o
                INNER JOIN DormRoom dr ON o.RoomID = dr.RoomID
                LEFT JOIN Merchant m ON o.MerchantID = m.MerchantID
                WHERE o.OccupancyID = ?
            """, occupancy_id)
            return cursor.fetchone()

    # ========== 电表抄表 ==========

    def get_readings(self, page=1, per_page=50, year_month=None, room_id=None):
        """获取电表读数列表"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = """
                SELECT r.ReadingID, r.RoomID, dr.RoomNumber, r.YearMonth,
                       r.PreviousReading, r.CurrentReading, r.Consumption,
                       r.UnitPrice, r.Amount, r.ReadingDate, r.OccupancyID,
                       r.CreateTime,
                       o.TenantName
                FROM DormReading r
                INNER JOIN DormRoom dr ON r.RoomID = dr.RoomID
                LEFT JOIN DormOccupancy o ON r.OccupancyID = o.OccupancyID
            """
            count_query = "SELECT COUNT(*) FROM DormReading r"

            conditions = []
            params = []

            if year_month:
                conditions.append("r.YearMonth = ?")
                params.append(year_month)

            if room_id:
                conditions.append("r.RoomID = ?")
                params.append(room_id)

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause

            cursor.execute(count_query, tuple(params))
            total_count = cursor.fetchone()[0]

            offset = (page - 1) * per_page
            base_query += " ORDER BY dr.RoomNumber OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, tuple(params))
            rows = cursor.fetchall()

            items = []
            for row in rows:
                items.append({
                    'reading_id': row.ReadingID,
                    'room_id': row.RoomID,
                    'room_number': row.RoomNumber,
                    'year_month': row.YearMonth,
                    'previous_reading': float(row.PreviousReading),
                    'current_reading': float(row.CurrentReading),
                    'consumption': float(row.Consumption),
                    'unit_price': float(row.UnitPrice),
                    'amount': float(row.Amount),
                    'reading_date': row.ReadingDate.strftime('%Y-%m-%d') if row.ReadingDate else '',
                    'occupancy_id': row.OccupancyID,
                    'tenant_name': row.TenantName or '',
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
                })

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

            return {
                'items': items,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page
            }

    def save_reading(self, room_id, year_month, current_reading, reading_date=None):
        """保存电表读数（新增或更新）"""
        if not year_month:
            raise ValueError("抄表月份不能为空")

        if not reading_date:
            reading_date = date.today().strftime('%Y-%m-%d')

        with DBConnection() as conn:
            cursor = conn.cursor()

            # 获取房间信息
            cursor.execute("""
                SELECT RoomID, LastReading, ElectricityUnitPrice, Status
                FROM DormRoom WHERE RoomID = ?
            """, room_id)
            room = cursor.fetchone()
            if not room:
                raise ValueError("房间不存在")

            previous_reading = float(room.LastReading) if room.LastReading else 0
            unit_price = float(room.ElectricityUnitPrice)

            current_reading = float(current_reading)
            if current_reading < previous_reading:
                raise ValueError(f"读数不能小于上次读数 {previous_reading}")

            consumption = current_reading - previous_reading
            amount = round(consumption * unit_price, 2)

            # 获取当前在住的OccupancyID
            cursor.execute("""
                SELECT TOP 1 OccupancyID FROM DormOccupancy
                WHERE RoomID = ? AND Status = N'在住'
            """, room_id)
            occ_row = cursor.fetchone()
            occupancy_id = occ_row.OccupancyID if occ_row else None

            # 检查是否已有该月读数
            cursor.execute("""
                SELECT ReadingID FROM DormReading WHERE RoomID = ? AND YearMonth = ?
            """, room_id, year_month)
            existing = cursor.fetchone()

            if existing:
                # 更新
                cursor.execute("""
                    UPDATE DormReading SET
                        PreviousReading = ?, CurrentReading = ?, Consumption = ?,
                        UnitPrice = ?, Amount = ?, ReadingDate = ?, OccupancyID = ?
                    WHERE ReadingID = ?
                """, previous_reading, current_reading, consumption,
                     unit_price, amount, reading_date, occupancy_id, existing.ReadingID)
            else:
                # 新增
                cursor.execute("""
                    INSERT INTO DormReading (RoomID, YearMonth, PreviousReading, CurrentReading,
                                             Consumption, UnitPrice, Amount, ReadingDate, OccupancyID)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, room_id, year_month, previous_reading, current_reading,
                     consumption, unit_price, amount, reading_date, occupancy_id)

            # 更新房间的 LastReading
            cursor.execute("""
                UPDATE DormRoom SET LastReading = ?, UpdateTime = GETDATE() WHERE RoomID = ?
            """, current_reading, room_id)

            conn.commit()

            return {
                'consumption': consumption,
                'amount': amount,
                'unit_price': unit_price
            }

    def get_rooms_for_reading(self, year_month):
        """获取需要抄表的在住房间列表（含上次读数，排除已有该月读数的房间）"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT dr.RoomID, dr.RoomNumber, dr.LastReading, dr.ElectricityUnitPrice,
                       dr.MeterNumber, o.TenantName
                FROM DormRoom dr
                LEFT JOIN DormOccupancy o ON dr.RoomID = o.RoomID AND o.Status = N'在住'
                WHERE dr.Status = N'已住'
                  AND NOT EXISTS (SELECT 1 FROM DormReading r WHERE r.RoomID = dr.RoomID AND r.YearMonth = ?)
                ORDER BY dr.RoomNumber
            """, year_month)
            rows = cursor.fetchall()

            items = []
            for row in rows:
                items.append({
                    'room_id': row.RoomID,
                    'room_number': row.RoomNumber,
                    'last_reading': float(row.LastReading) if row.LastReading else 0,
                    'electricity_unit_price': float(row.ElectricityUnitPrice),
                    'meter_number': row.MeterNumber or '',
                    'tenant_name': row.TenantName or '',
                })
            return items

    # ========== 月度账单 ==========

    def get_bills(self, page=1, per_page=20, year_month=None, status=None):
        """获取月度账单列表"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = """
                SELECT b.BillID, b.RoomID, b.OccupancyID, b.YearMonth,
                       b.RentAmount, b.WaterAmount, b.ElectricityAmount, b.TotalAmount,
                       b.ReadingID, b.ReceivableID, b.Status, b.CreateTime,
                       dr.RoomNumber, dr.RoomType,
                       o.TenantName, o.TenantType, o.TenantPhone, o.MerchantID,
                       m.MerchantName
                FROM DormBill b
                INNER JOIN DormRoom dr ON b.RoomID = dr.RoomID
                INNER JOIN DormOccupancy o ON b.OccupancyID = o.OccupancyID
                LEFT JOIN Merchant m ON o.MerchantID = m.MerchantID
            """
            count_query = "SELECT COUNT(*) FROM DormBill b"

            conditions = []
            params = []

            if year_month:
                conditions.append("b.YearMonth = ?")
                params.append(year_month)

            if status:
                conditions.append("b.Status = ?")
                params.append(status)

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause

            cursor.execute(count_query, tuple(params))
            total_count = cursor.fetchone()[0]

            offset = (page - 1) * per_page
            base_query += " ORDER BY dr.RoomNumber OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, tuple(params))
            rows = cursor.fetchall()

            items = []
            for row in rows:
                items.append({
                    'bill_id': row.BillID,
                    'room_id': row.RoomID,
                    'occupancy_id': row.OccupancyID,
                    'year_month': row.YearMonth,
                    'rent_amount': float(row.RentAmount),
                    'water_amount': float(row.WaterAmount),
                    'electricity_amount': float(row.ElectricityAmount),
                    'total_amount': float(row.TotalAmount),
                    'reading_id': row.ReadingID,
                    'receivable_id': row.ReceivableID,
                    'status': row.Status,
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
                    'room_number': row.RoomNumber,
                    'room_type': row.RoomType,
                    'tenant_name': row.TenantName,
                    'tenant_type': row.TenantType,
                    'tenant_phone': row.TenantPhone or '',
                    'merchant_id': row.MerchantID,
                    'merchant_name': row.MerchantName or '',
                })

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

            # 汇总
            summary = None
            if year_month:
                summary_query = """
                    SELECT COUNT(*) AS BillCount,
                           SUM(RentAmount) AS TotalRent,
                           SUM(WaterAmount) AS TotalWater,
                           SUM(ElectricityAmount) AS TotalElec,
                           SUM(TotalAmount) AS TotalAmount
                    FROM DormBill WHERE YearMonth = ?
                """
                cursor.execute(summary_query, year_month)
                s = cursor.fetchone()
                if s and s.BillCount > 0:
                    summary = {
                        'bill_count': s.BillCount,
                        'total_rent': float(s.TotalRent),
                        'total_water': float(s.TotalWater),
                        'total_elec': float(s.TotalElec),
                        'total_amount': float(s.TotalAmount),
                    }

            return {
                'items': items,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page,
                'summary': summary
            }

    def generate_bills(self, year_month):
        """按月批量生成账单（租金+水费+电费）"""
        if not year_month:
            raise ValueError("请选择账单月份")

        with DBConnection() as conn:
            cursor = conn.cursor()

            # 获取所有在住房间
            cursor.execute("""
                SELECT dr.RoomID, dr.MonthlyRent, dr.WaterQuota, dr.ElectricityUnitPrice,
                       o.OccupancyID, o.TenantType, o.MerchantID, o.TenantName
                FROM DormRoom dr
                INNER JOIN DormOccupancy o ON dr.RoomID = o.RoomID AND o.Status = N'在住'
                WHERE dr.Status = N'已住'
            """)
            rooms = cursor.fetchall()

            if not rooms:
                return {'success': False, 'message': '没有在住房间，无需生成账单'}

            created = 0
            skipped = 0

            for room in rooms:
                # 检查是否已有账单
                cursor.execute("""
                    SELECT 1 FROM DormBill WHERE RoomID = ? AND YearMonth = ?
                """, room.RoomID, year_month)
                if cursor.fetchone():
                    skipped += 1
                    continue

                # 获取电费读数
                electricity_amount = 0
                reading_id = None
                cursor.execute("""
                    SELECT ReadingID, Amount FROM DormReading
                    WHERE RoomID = ? AND YearMonth = ?
                """, room.RoomID, year_month)
                reading = cursor.fetchone()
                if reading:
                    electricity_amount = float(reading.Amount)
                    reading_id = reading.ReadingID

                rent_amount = float(room.MonthlyRent)
                water_amount = float(room.WaterQuota)
                total_amount = rent_amount + water_amount + electricity_amount

                cursor.execute("""
                    INSERT INTO DormBill (RoomID, OccupancyID, YearMonth,
                                          RentAmount, WaterAmount, ElectricityAmount, TotalAmount,
                                          ReadingID, Status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, N'待确认')
                """, room.RoomID, room.OccupancyID, year_month,
                     rent_amount, water_amount, electricity_amount, total_amount,
                     reading_id)

                created += 1

            conn.commit()

            return {
                'success': True,
                'message': f'生成完成：新建 {created} 条，跳过 {skipped} 条（已存在）'
            }

    def confirm_bill(self, bill_id):
        """确认单条账单"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Status FROM DormBill WHERE BillID = ?", bill_id)
            bill = cursor.fetchone()
            if not bill:
                raise ValueError("账单不存在")
            if bill.Status != '待确认':
                raise ValueError("只能确认待确认状态的账单")

            cursor.execute("""
                UPDATE DormBill SET Status = N'已确认' WHERE BillID = ?
            """, bill_id)
            conn.commit()

    def batch_confirm_bills(self, bill_ids):
        """批量确认账单"""
        success_count = 0
        fail_count = 0
        errors = []

        for bid in bill_ids:
            try:
                self.confirm_bill(bid)
                success_count += 1
            except Exception as e:
                fail_count += 1
                errors.append(str(e))

        return {
            'success': True,
            'message': f'确认完成：成功 {success_count} 条，失败 {fail_count} 条',
            'errors': errors
        }

    def create_receivable(self, bill_id, created_by=None):
        """确认后开账→联动应收模块"""
        from app.services.receivable_service import ReceivableService
        from app.services.dict_service import DictService
        from app.services.customer_service import CustomerService

        with DBConnection() as conn:
            cursor = conn.cursor()

            # 获取账单详情
            cursor.execute("""
                SELECT b.BillID, b.RoomID, b.OccupancyID, b.YearMonth,
                       b.RentAmount, b.WaterAmount, b.ElectricityAmount, b.TotalAmount,
                       b.Status, b.ReceivableID,
                       dr.RoomNumber, dr.MonthlyRent, dr.WaterQuota,
                       o.TenantType, o.MerchantID, o.TenantName, o.TenantPhone,
                       m.MerchantName
                FROM DormBill b
                INNER JOIN DormRoom dr ON b.RoomID = dr.RoomID
                INNER JOIN DormOccupancy o ON b.OccupancyID = o.OccupancyID
                LEFT JOIN Merchant m ON o.MerchantID = m.MerchantID
                WHERE b.BillID = ?
            """, bill_id)
            bill = cursor.fetchone()

            if not bill:
                raise ValueError("账单不存在")
            if bill.Status != '已确认':
                raise ValueError("只能对已确认的账单开账")
            if bill.ReceivableID:
                raise ValueError("该账单已开账")

            # 确定客户类型和ID
            if bill.TenantType == '商户' and bill.MerchantID:
                customer_type = 'Merchant'
                customer_id = bill.MerchantID
                customer_name = bill.MerchantName or bill.TenantName
            else:
                # 个人租户→在Customer表查找或创建
                customer_type = 'Customer'
                customer_id = self._ensure_customer(cursor, bill.TenantName, bill.TenantPhone)
                customer_name = bill.TenantName

            # 获取费用项DictID
            income_items = DictService.get_expense_items('expense_item_income')
            expense_map = {item['dict_code']: item['dict_id'] for item in income_items}

            rent_expense_id = expense_map.get('dorm_rent')
            water_expense_id = expense_map.get('dorm_water')
            elec_expense_id = expense_map.get('dorm_elec')

            # 到期日：当月最后一天
            year, month = bill.YearMonth.split('-')
            import calendar
            last_day = calendar.monthrange(int(year), int(month))[1]
            due_date = f"{bill.YearMonth}-{last_day:02d}"

            receivable_svc = ReceivableService()
            receivable_ids = []

            # 创建3条应收
            items_to_create = [
                (bill.RentAmount, rent_expense_id, f"宿舍租金-{bill.RoomNumber}-{bill.YearMonth}", 'dorm_rent'),
                (bill.WaterAmount, water_expense_id, f"宿舍水费-{bill.RoomNumber}-{bill.YearMonth}", 'dorm_water'),
                (bill.ElectricityAmount, elec_expense_id, f"宿舍电费-{bill.RoomNumber}-{bill.YearMonth}", 'dorm_elec'),
            ]

            for amount, expense_id, description, ref_type in items_to_create:
                if float(amount) > 0 and expense_id:
                    ref_id = f"dorm_{bill.BillID}_{ref_type}"
                    rid = receivable_svc.create_receivable(
                        merchant_id=bill.MerchantID if customer_type == 'Merchant' else None,
                        expense_type_id=expense_id,
                        amount=float(amount),
                        due_date=due_date,
                        description=description,
                        reference_id=ref_id,
                        reference_type=f'dorm_bill_{ref_type}',
                        customer_type=customer_type,
                        customer_id=customer_id
                    )
                    receivable_ids.append(rid)

            # 回写第一个ReceivableID到账单（标识已开账）
            first_rid = receivable_ids[0] if receivable_ids else None
            cursor.execute("""
                UPDATE DormBill SET ReceivableID = ?, Status = N'已开账' WHERE BillID = ?
            """, first_rid, bill_id)

            conn.commit()

            return {
                'success': True,
                'message': f'开账成功，已创建 {len(receivable_ids)} 条应收',
                'receivable_ids': receivable_ids
            }

    def _ensure_customer(self, cursor, name, phone=None):
        """确保个人租户在Customer表中存在，不存在则创建，返回CustomerID"""
        # 查找
        if phone:
            cursor.execute("""
                SELECT CustomerID FROM Customer
                WHERE CustomerName = ? AND Phone = ? AND CustomerType = N'宿舍个人'
            """, name, phone)
        else:
            cursor.execute("""
                SELECT CustomerID FROM Customer
                WHERE CustomerName = ? AND CustomerType = N'宿舍个人'
            """, name)

        row = cursor.fetchone()
        if row:
            return row.CustomerID

        # 创建
        cursor.execute("""
            INSERT INTO Customer (CustomerName, ContactPerson, Phone, CustomerType, Status)
            OUTPUT INSERTED.CustomerID
            VALUES (?, ?, ?, N'宿舍个人', N'正常')
        """, name, name, phone)

        new_row = cursor.fetchone()
        return new_row[0] if new_row else None

    # ========== 统计 ==========

    def get_dashboard_stats(self):
        """获取宿舍概览统计"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            # 房间统计
            cursor.execute("""
                SELECT
                    COUNT(*) AS Total,
                    SUM(CASE WHEN Status = N'空闲' THEN 1 ELSE 0 END) AS Vacant,
                    SUM(CASE WHEN Status = N'已住' THEN 1 ELSE 0 END) AS Occupied,
                    SUM(CASE WHEN Status = N'维修中' THEN 1 ELSE 0 END) AS Maintenance
                FROM DormRoom
            """)
            row = cursor.fetchone()

            return {
                'total_rooms': row.Total,
                'vacant_rooms': row.Vacant,
                'occupied_rooms': row.Occupied,
                'maintenance_rooms': row.Maintenance,
            }
