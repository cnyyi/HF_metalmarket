"""客户管理服务"""
import logging
from utils.database import DBConnection

logger = logging.getLogger(__name__)


class CustomerService:
    """客户管理服务类"""

    @staticmethod
    def get_customers(page=1, per_page=10, search=None, status=None):
        """获取客户列表，支持分页和搜索"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = """
                SELECT CustomerID, CustomerName, ShortName, ContactPerson, Phone,
                       Address, CustomerType, BusinessScope, TaxNumber,
                       Description, Status, CreateTime, UpdateTime
                FROM Customer
            """
            count_query = "SELECT COUNT(*) FROM Customer"

            conditions = []
            params = []

            if search:
                conditions.append("(CustomerName LIKE ? OR ShortName LIKE ? OR ContactPerson LIKE ? OR Phone LIKE ?)")
                p = f'%{search}%'
                params.extend([p, p, p, p])

            if status:
                conditions.append("Status = ?")
                params.append(status)

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
            base_query += " ORDER BY CustomerID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, tuple(params))
            rows = cursor.fetchall()

            items = []
            for row in rows:
                items.append({
                    'customer_id': row.CustomerID,
                    'customer_name': row.CustomerName,
                    'short_name': row.ShortName or '',
                    'contact_person': row.ContactPerson or '',
                    'phone': row.Phone or '',
                    'address': row.Address or '',
                    'customer_type': row.CustomerType or '',
                    'business_scope': row.BusinessScope or '',
                    'tax_number': row.TaxNumber or '',
                    'description': row.Description or '',
                    'status': row.Status,
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
                    'update_time': row.UpdateTime.strftime('%Y-%m-%d %H:%M') if row.UpdateTime else '',
                })

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

            return {
                'items': items,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page
            }

    @staticmethod
    def get_customer_by_id(customer_id):
        """根据ID获取客户信息"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT CustomerID, CustomerName, ShortName, ContactPerson, Phone,
                       Address, CustomerType, BusinessScope, TaxNumber,
                       Description, Status, CreateTime, UpdateTime
                FROM Customer
                WHERE CustomerID = ?
            """, customer_id)
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'customer_id': row.CustomerID,
                'customer_name': row.CustomerName,
                'short_name': row.ShortName or '',
                'contact_person': row.ContactPerson or '',
                'phone': row.Phone or '',
                'address': row.Address or '',
                'customer_type': row.CustomerType or '',
                'business_scope': row.BusinessScope or '',
                'tax_number': row.TaxNumber or '',
                'description': row.Description or '',
                'status': row.Status,
                'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
                'update_time': row.UpdateTime.strftime('%Y-%m-%d %H:%M') if row.UpdateTime else '',
            }

    @staticmethod
    def create_customer(data):
        """创建客户"""
        customer_name = data.get('customer_name', '').strip()
        if not customer_name:
            raise ValueError("客户名称不能为空")

        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Customer (CustomerName, ShortName, ContactPerson, Phone,
                                      Address, CustomerType, BusinessScope, TaxNumber,
                                      Description, Status)
                OUTPUT INSERTED.CustomerID
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, N'正常')
            """,
                customer_name,
                data.get('short_name', '').strip() or None,
                data.get('contact_person', '').strip() or None,
                data.get('phone', '').strip() or None,
                data.get('address', '').strip() or None,
                data.get('customer_type', '').strip() or None,
                data.get('business_scope', '').strip() or None,
                data.get('tax_number', '').strip() or None,
                data.get('description', '').strip() or None,
            )
            row = cursor.fetchone()
            new_id = row[0] if row else None
            conn.commit()
            return new_id

    @staticmethod
    def update_customer(customer_id, data):
        """更新客户信息"""
        customer_name = data.get('customer_name', '').strip()
        if not customer_name:
            raise ValueError("客户名称不能为空")

        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Customer
                SET CustomerName = ?, ShortName = ?, ContactPerson = ?, Phone = ?,
                    Address = ?, CustomerType = ?, BusinessScope = ?, TaxNumber = ?,
                    Description = ?, Status = ?, UpdateTime = GETDATE()
                WHERE CustomerID = ?
            """,
                customer_name,
                data.get('short_name', '').strip() or None,
                data.get('contact_person', '').strip() or None,
                data.get('phone', '').strip() or None,
                data.get('address', '').strip() or None,
                data.get('customer_type', '').strip() or None,
                data.get('business_scope', '').strip() or None,
                data.get('tax_number', '').strip() or None,
                data.get('description', '').strip() or None,
                data.get('status', '正常'),
                customer_id,
            )
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def delete_customer(customer_id):
        """删除客户（检查是否有关联数据）"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            # 检查应收/应付是否关联
            cursor.execute("SELECT COUNT(*) FROM Receivable WHERE CustomerType='Customer' AND CustomerID=? AND IsActive=1", customer_id)
            recv_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM Payable WHERE CustomerType='Customer' AND CustomerID=?", customer_id)
            pay_count = cursor.fetchone()[0]
            if recv_count > 0 or pay_count > 0:
                raise ValueError(f"该客户关联了 {recv_count} 条应收、{pay_count} 条应付记录，无法删除")

            cursor.execute("DELETE FROM Customer WHERE CustomerID = ?", customer_id)
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def search_customers(keyword):
        """搜索客户（用于下拉选择）"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT CustomerID, CustomerName, ContactPerson, Phone
                FROM Customer
                WHERE (CustomerName LIKE ? OR ShortName LIKE ? OR ContactPerson LIKE ?)
                  AND Status = N'正常'
                ORDER BY CustomerName
            """, f'%{keyword}%', f'%{keyword}%', f'%{keyword}%')
            rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append({
                    'customer_id': row.CustomerID,
                    'customer_name': row.CustomerName,
                    'contact_person': row.ContactPerson or '',
                    'phone': row.Phone or '',
                })
            return result
