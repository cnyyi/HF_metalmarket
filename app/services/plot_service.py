# -*- coding: utf-8 -*-
"""
地块管理服务
"""
import logging
from utils.database import DBConnection
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
from config.base import Config

logger = logging.getLogger(__name__)

class PlotService:
    @staticmethod
    def get_plot_types():
        """
        获取地块类型列表
        """
        with DBConnection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DictName, UnitPrice
                FROM Sys_Dictionary
                WHERE DictType = N'plot_type'
                ORDER BY SortOrder
            """)
            
            types = [(r.DictName, r.DictName, float(r.UnitPrice) if r.UnitPrice else 0) for r in cursor.fetchall()]
        
        return types

    @staticmethod
    def get_plot_types_json():
        """
        获取地块类型列表（JSON格式）
        """
        with DBConnection() as conn:
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
        
        return types

    @staticmethod
    def save_uploaded_file(file):
        """
        保存上传的文件
        """
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
        
        def allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
        
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

    @staticmethod
    def safe_delete_image(image_path_relative):
        """
        安全删除上传的图片（带路径遍历防护）
        
        Args:
            image_path_relative: 相对路径，如 /uploads/plot/xxx.png
        """
        if not image_path_relative:
            return
        
        # 安全校验：确保路径在 uploads 目录内，防止路径遍历攻击
        safe_prefix = '/uploads/'
        if not image_path_relative.startswith(safe_prefix):
            logger.warning(f"尝试删除非uploads目录的文件: {image_path_relative}")
            return

        full_path = os.path.join(Config.UPLOAD_FOLDER, image_path_relative[len(safe_prefix):])

        # 二次验证：规范化后仍在 uploads 目录内
        resolved_path = os.path.realpath(full_path)
        upload_real = os.path.realpath(Config.UPLOAD_FOLDER)
        if not resolved_path.startswith(upload_real):
            logger.warning(f"路径遍历尝试被拦截: {image_path_relative} -> {resolved_path}")
            return

        if os.path.exists(resolved_path):
            try:
                os.remove(resolved_path)
            except OSError as e:
                logger.warning(f"删除图片失败: {e}")

    @staticmethod
    def calculate_rent(area, unit_price):
        """
        计算租金
        """
        monthly_rent = area * unit_price
        yearly_rent = monthly_rent * 12
        return monthly_rent, yearly_rent

    @staticmethod
    def add_plot(plot_number, plot_name, plot_type, area, unit_price, location, status, description, image_path):
        """
        添加地块
        """
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                # 检查地块编号是否已存在
                cursor.execute("SELECT COUNT(*) FROM Plot WHERE PlotNumber = ?", (plot_number,))
                if cursor.fetchone()[0] > 0:
                    return False, '地块编号已存在'
                
                # 计算租金
                monthly_rent, yearly_rent = PlotService.calculate_rent(area, unit_price)
                total_price = area * unit_price
                
                # 插入数据
                cursor.execute("""
                    INSERT INTO Plot (PlotNumber, PlotName, PlotType, Area, UnitPrice, TotalPrice, MonthlyRent, YearlyRent, Location, Status, Description, ImagePath, CreateTime)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (plot_number, plot_name, plot_type, area, unit_price, total_price, monthly_rent, yearly_rent, location, status, description, image_path))

                cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
                plot_id = cursor.fetchone()[0]
                conn.commit()
            
            return True, plot_id
        except Exception as e:
            logger.error(f"添加地块失败: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def update_plot(plot_id, plot_number, plot_name, plot_type, area, unit_price, location, status, description, image_path):
        """
        更新地块
        """
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                # 检查地块编号是否被其他地块使用
                cursor.execute("SELECT COUNT(*) FROM Plot WHERE PlotNumber = ? AND PlotID != ?", (plot_number, plot_id))
                if cursor.fetchone()[0] > 0:
                    return False, '地块编号已被其他地块使用'
                
                # 计算租金
                monthly_rent, yearly_rent = PlotService.calculate_rent(area, unit_price)
                
                # 更新数据
                cursor.execute("""
                    UPDATE Plot SET 
                        PlotNumber = ?, PlotName = ?, PlotType = ?, Area = ?, UnitPrice = ?, 
                        MonthlyRent = ?, YearlyRent = ?, Location = ?, 
                        Status = ?, Description = ?, ImagePath = ?, UpdateTime = GETDATE()
                    WHERE PlotID = ?
                """, (plot_number, plot_name, plot_type, area, unit_price, monthly_rent, yearly_rent, location, status, description, image_path, plot_id))
                
                conn.commit()
            
            return True, '更新成功'
        except Exception as e:
            logger.error(f"更新地块失败: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def upload_image(plot_id, image_path):
        """
        上传图片
        """
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                # 获取旧图片路径
                cursor.execute("SELECT ImagePath FROM Plot WHERE PlotID = ?", (plot_id,))
                row = cursor.fetchone()
                old_image_path = row.ImagePath if row else None
                
                # 安全删除旧图片
                if old_image_path:
                    PlotService.safe_delete_image(old_image_path)
                
                # 更新图片路径
                cursor.execute("UPDATE Plot SET ImagePath = ?, UpdateTime = GETDATE() WHERE PlotID = ?", (image_path, plot_id))
                conn.commit()
            
            return True, '图片上传成功'
        except Exception as e:
            logger.error(f"上传图片失败: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def delete_plot(plot_id):
        """
        删除地块
        """
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                # 获取图片路径
                cursor.execute("SELECT ImagePath FROM Plot WHERE PlotID = ?", (plot_id,))
                row = cursor.fetchone()
                image_path = row.ImagePath if row else None
                
                # 安全删除图片
                if image_path:
                    PlotService.safe_delete_image(image_path)
                
                # 删除地块
                cursor.execute("DELETE FROM Plot WHERE PlotID = ?", (plot_id,))
                
                conn.commit()
            
            return True, '删除成功'
        except Exception as e:
            logger.error(f"删除地块失败: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def get_plot_detail(plot_id):
        """
        获取地块详情
        """
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT PlotID, PlotNumber, PlotName, PlotType, Area, UnitPrice, MonthlyRent, YearlyRent, Location, Status, Description, ImagePath, CreateTime, UpdateTime
                    FROM Plot WHERE PlotID = ?
                """, (plot_id,))
                
                row = cursor.fetchone()
                if not row:
                    return False, '地块不存在'
                
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
            
            return True, plot
        except Exception as e:
            logger.error(f"获取地块详情失败: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def get_plot_list(page, per_page, search, status, plot_type, rent_status, sort_by, sort_dir):
        """
        获取地块列表
        """
        try:
            with DBConnection() as conn:
                cursor = conn.cursor()
                
                allowed_sort = {
                    'plot_code': 'p.PlotNumber',
                    'plot_type': 'p.PlotType',
                    'rent_status': 'RentStatus',
                    'area': 'p.Area'
                }
                order_clause = 'p.CreateTime DESC'
                if sort_by in allowed_sort:
                    col = allowed_sort[sort_by]
                    direction = 'DESC' if sort_dir == 'desc' else 'ASC'
                    order_clause = f'{col} {direction}'
                
                offset = (page - 1) * per_page
                
                where_clause = "WHERE 1=1"
                params = []
                
                if search:
                    where_clause += " AND (p.PlotNumber LIKE ? OR p.PlotName LIKE ? OR p.Location LIKE ?)"
                    search_param = f"%{search}%"
                    params.extend([search_param, search_param, search_param])
                
                if status:
                    where_clause += " AND p.Status = ?"
                    params.append(status)
                
                if plot_type:
                    where_clause += " AND p.PlotType = ?"
                    params.append(plot_type)
                
                # 租赁状态筛选
                if rent_status == '租赁中':
                    where_clause += " AND EXISTS (SELECT 1 FROM ContractPlot cp INNER JOIN Contract c ON cp.ContractID = c.ContractID WHERE cp.PlotID = p.PlotID AND c.StartDate <= CAST(GETDATE() AS DATE) AND c.EndDate >= CAST(GETDATE() AS DATE) AND c.Status <> N'已终止')"
                elif rent_status == '空闲':
                    where_clause += " AND NOT EXISTS (SELECT 1 FROM ContractPlot cp INNER JOIN Contract c ON cp.ContractID = c.ContractID WHERE cp.PlotID = p.PlotID AND c.StartDate <= CAST(GETDATE() AS DATE) AND c.EndDate >= CAST(GETDATE() AS DATE) AND c.Status <> N'已终止')"
                
                # 获取总数
                cursor.execute(f"""
                    SELECT COUNT(*) FROM Plot p {where_clause}
                """, params)
                total = cursor.fetchone()[0]
                
                # 获取数据
                cursor.execute(f"""
                    SELECT p.PlotID, p.PlotNumber, p.PlotName, p.PlotType, p.Area, p.UnitPrice, 
                           p.MonthlyRent, p.YearlyRent, p.Location, p.Status, p.ImagePath, p.CreateTime,
                           CASE WHEN EXISTS (
                               SELECT 1 FROM ContractPlot cp 
                               INNER JOIN Contract c ON cp.ContractID = c.ContractID 
                               WHERE cp.PlotID = p.PlotID 
                                 AND c.StartDate <= CAST(GETDATE() AS DATE) 
                                 AND c.EndDate >= CAST(GETDATE() AS DATE) 
                                 AND c.Status <> N'已终止'
                           ) THEN N'租赁中' ELSE N'空闲' END AS RentStatus
                    FROM Plot p {where_clause}
                    ORDER BY {order_clause}
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
                    'rent_status': r.RentStatus,
                    'image_path': r.ImagePath,
                    'create_time': r.CreateTime.strftime('%Y-%m-%d %H:%M:%S') if r.CreateTime else None
                } for r in cursor.fetchall()]
            
            return True, {
                'plots': plots,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        except Exception as e:
            logger.error(f"获取地块列表失败: {e}", exc_info=True)
            return False, str(e)