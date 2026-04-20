import datetime
import logging
from utils.database import execute_query, execute_update
from app.models.merchant_binding import MerchantBinding

logger = logging.getLogger(__name__)


class WxBindService:

    @staticmethod
    def apply_binding(user_id, merchant_id, bind_role, remark=None):
        existing = execute_query("""
            SELECT BindingID FROM MerchantBinding
            WHERE UserID = ? AND MerchantID = ? AND Status = N'Pending' AND IsActive = 1
        """, (user_id, merchant_id), fetch_type='one')
        if existing:
            return {'success': False, 'message': '您已提交过该商户的绑定申请，请等待审批'}

        approved = execute_query("""
            SELECT BindingID FROM MerchantBinding
            WHERE UserID = ? AND MerchantID = ? AND Status = N'Approved' AND IsActive = 1
        """, (user_id, merchant_id), fetch_type='one')
        if approved:
            return {'success': False, 'message': '您已绑定该商户'}

        insert_query = """
            INSERT INTO MerchantBinding (UserID, MerchantID, BindRole, Status, ApplyTime, Remark, IsActive)
            VALUES (?, ?, ?, N'Pending', ?, ?, 1)
        """
        execute_update(insert_query, (user_id, merchant_id, bind_role, datetime.datetime.now(), remark or ''))

        return {'success': True, 'message': '绑定申请已提交，请等待管理员审批'}

    @staticmethod
    def cancel_binding(binding_id, user_id):
        binding = execute_query(
            "SELECT BindingID, Status FROM MerchantBinding WHERE BindingID = ? AND UserID = ?",
            (binding_id, user_id), fetch_type='one',
        )
        if not binding:
            return {'success': False, 'message': '绑定记录不存在'}
        if binding.Status != 'Pending':
            return {'success': False, 'message': '只能取消待审批的申请'}

        execute_update("""
            UPDATE MerchantBinding SET Status = N'Cancelled', IsActive = 0 WHERE BindingID = ?
        """, (binding_id,))
        return {'success': True, 'message': '已取消绑定申请'}

    @staticmethod
    def get_user_bindings(user_id):
        query = """
            SELECT mb.BindingID, mb.UserID, mb.MerchantID, mb.BindRole, mb.Status,
                   mb.ApplyTime, mb.ApproveTime, mb.RejectReason, mb.Remark,
                   m.MerchantName
            FROM MerchantBinding mb
            LEFT JOIN Merchant m ON mb.MerchantID = m.MerchantID
            WHERE mb.UserID = ? AND mb.IsActive = 1
            ORDER BY mb.ApplyTime DESC
        """
        results = execute_query(query, (user_id,), fetch_type='all')
        bindings = []
        for r in results:
            bindings.append(MerchantBinding(
                binding_id=r.BindingID,
                user_id=r.UserID,
                merchant_id=r.MerchantID,
                bind_role=r.BindRole,
                status=r.Status,
                apply_time=r.ApplyTime,
                approve_time=r.ApproveTime,
                reject_reason=r.RejectReason,
                remark=r.Remark,
                merchant_name=r.MerchantName,
            ))
        return bindings

    @staticmethod
    def get_approved_bindings(user_id):
        query = """
            SELECT mb.BindingID, mb.UserID, mb.MerchantID, mb.BindRole, mb.Status,
                   m.MerchantName
            FROM MerchantBinding mb
            LEFT JOIN Merchant m ON mb.MerchantID = m.MerchantID
            WHERE mb.UserID = ? AND mb.Status = N'Approved' AND mb.IsActive = 1
            ORDER BY mb.ApplyTime DESC
        """
        results = execute_query(query, (user_id,), fetch_type='all')
        bindings = []
        for r in results:
            bindings.append(MerchantBinding(
                binding_id=r.BindingID,
                user_id=r.UserID,
                merchant_id=r.MerchantID,
                bind_role=r.BindRole,
                status=r.Status,
                merchant_name=r.MerchantName,
            ))
        return bindings

    @staticmethod
    def get_pending_requests(merchant_id=None):
        conditions = ["mb.Status = N'Pending'", "mb.IsActive = 1"]
        params = []
        if merchant_id:
            conditions.append("mb.MerchantID = ?")
            params.append(merchant_id)

        where = " AND ".join(conditions)
        query = f"""
            SELECT mb.BindingID, mb.UserID, mb.MerchantID, mb.BindRole, mb.Status,
                   mb.ApplyTime, mb.Remark,
                   m.MerchantName, u.RealName AS UserRealName, u.Phone
            FROM MerchantBinding mb
            LEFT JOIN Merchant m ON mb.MerchantID = m.MerchantID
            LEFT JOIN [User] u ON mb.UserID = u.UserID
            WHERE {where}
            ORDER BY mb.ApplyTime DESC
        """
        results = execute_query(query, tuple(params), fetch_type='all')
        items = []
        for r in results:
            items.append({
                'binding_id': r.BindingID,
                'user_id': r.UserID,
                'merchant_id': r.MerchantID,
                'bind_role': r.BindRole,
                'status': r.Status,
                'apply_time': r.ApplyTime.strftime('%Y-%m-%d %H:%M') if r.ApplyTime else '',
                'remark': r.Remark or '',
                'merchant_name': r.MerchantName or '',
                'user_real_name': r.UserRealName or '',
                'phone': r.Phone or '',
            })
        return items

    @staticmethod
    def approve_binding(binding_id, approver_id):
        binding = execute_query(
            "SELECT BindingID, UserID, MerchantID, BindRole FROM MerchantBinding WHERE BindingID = ? AND Status = N'Pending'",
            (binding_id,), fetch_type='one',
        )
        if not binding:
            return {'success': False, 'message': '绑定申请不存在或已处理'}

        execute_update("""
            UPDATE MerchantBinding
            SET Status = N'Approved', ApproveTime = ?, ApproverID = ?
            WHERE BindingID = ?
        """, (datetime.datetime.now(), approver_id, binding_id))

        user_approved = execute_query("""
            SELECT BindingID FROM MerchantBinding
            WHERE UserID = ? AND MerchantID = ? AND Status = N'Approved' AND IsActive = 1
        """, (binding.UserID, binding.MerchantID), fetch_type='one')

        if not user_approved or user_approved.BindingID == binding_id:
            execute_update("""
                UPDATE [User] SET MerchantID = ? WHERE UserID = ? AND (MerchantID IS NULL OR MerchantID = 0)
            """, (binding.MerchantID, binding.UserID))

        wx_user = execute_query(
            "SELECT WxUserID FROM WxUser WHERE UserID = ?", (binding.UserID,), fetch_type='one',
        )
        if wx_user:
            execute_update("""
                UPDATE WxUser SET CurrentMerchantID = ? WHERE WxUserID = ? AND (CurrentMerchantID IS NULL OR CurrentMerchantID = 0)
            """, (binding.MerchantID, wx_user.WxUserID))

        merchant = execute_query(
            "SELECT MerchantName FROM Merchant WHERE MerchantID = ?",
            (binding.MerchantID,), fetch_type='one',
        )
        merchant_name = merchant.MerchantName if merchant else ''

        wx_user_openid = execute_query(
            "SELECT OpenID FROM WxUser WHERE UserID = ?", (binding.UserID,), fetch_type='one',
        )
        openid = wx_user_openid.OpenID if wx_user_openid else ''

        return {'success': True, 'message': f'已通过 {merchant_name} 的绑定申请', 'openid': openid, 'merchant_name': merchant_name, 'bind_role': binding.BindRole}

    @staticmethod
    def reject_binding(binding_id, approver_id, reason):
        binding = execute_query(
            "SELECT BindingID, UserID, MerchantID FROM MerchantBinding WHERE BindingID = ? AND Status = N'Pending'",
            (binding_id,), fetch_type='one',
        )
        if not binding:
            return {'success': False, 'message': '绑定申请不存在或已处理'}

        execute_update("""
            UPDATE MerchantBinding
            SET Status = N'Rejected', ApproveTime = ?, ApproverID = ?, RejectReason = ?
            WHERE BindingID = ?
        """, (datetime.datetime.now(), approver_id, reason or '', binding_id))

        merchant = execute_query(
            "SELECT MerchantName FROM Merchant WHERE MerchantID = ?",
            (binding.MerchantID,), fetch_type='one',
        )
        merchant_name = merchant.MerchantName if merchant else ''

        wx_user_openid = execute_query(
            "SELECT OpenID FROM WxUser WHERE UserID = ?", (binding.UserID,), fetch_type='one',
        )
        openid = wx_user_openid.OpenID if wx_user_openid else ''

        return {'success': True, 'message': f'已驳回 {merchant_name} 的绑定申请', 'openid': openid, 'merchant_name': merchant_name, 'reason': reason or ''}

    @staticmethod
    def get_user_current_merchant(user_id):
        wx_user = execute_query(
            "SELECT CurrentMerchantID FROM WxUser WHERE UserID = ?",
            (user_id,), fetch_type='one',
        )
        merchant_id = None
        if wx_user and wx_user.CurrentMerchantID:
            merchant_id = wx_user.CurrentMerchantID
        else:
            user = execute_query(
                "SELECT MerchantID FROM [User] WHERE UserID = ?",
                (user_id,), fetch_type='one',
            )
            if user and user.MerchantID:
                merchant_id = user.MerchantID

        if not merchant_id:
            return None

        merchant = execute_query(
            "SELECT MerchantID, MerchantName FROM Merchant WHERE MerchantID = ?",
            (merchant_id,), fetch_type='one',
        )
        if not merchant:
            return None
        return {'merchant_id': merchant.MerchantID, 'merchant_name': merchant.MerchantName}

    @staticmethod
    def get_user_bind_role(user_id, merchant_id):
        binding = execute_query("""
            SELECT BindRole FROM MerchantBinding
            WHERE UserID = ? AND MerchantID = ? AND Status = N'Approved' AND IsActive = 1
        """, (user_id, merchant_id), fetch_type='one')
        if binding:
            return binding.BindRole
        return None

    @staticmethod
    def switch_merchant(user_id, merchant_id):
        approved = execute_query("""
            SELECT BindingID FROM MerchantBinding
            WHERE UserID = ? AND MerchantID = ? AND Status = N'Approved' AND IsActive = 1
        """, (user_id, merchant_id), fetch_type='one')
        if not approved:
            return {'success': False, 'message': '您未绑定该商户'}

        execute_update("""
            UPDATE WxUser SET CurrentMerchantID = ?, UpdateTime = ? WHERE UserID = ?
        """, (merchant_id, datetime.datetime.now(), user_id))

        execute_update("""
            UPDATE [User] SET MerchantID = ? WHERE UserID = ?
        """, (merchant_id, user_id))

        return {'success': True, 'message': '已切换商户'}

    @staticmethod
    def search_merchants(search=''):
        query = """
            SELECT TOP 20 MerchantID, MerchantName, ContactPerson, Phone
            FROM Merchant WHERE Status = N'正常'
        """
        params = []
        if search:
            query += " AND MerchantName LIKE ?"
            params.append(f'%{search}%')
        query += " ORDER BY MerchantName"
        results = execute_query(query, tuple(params), fetch_type='all') if params else execute_query(query, fetch_type='all')
        items = [{'merchant_id': r.MerchantID, 'merchant_name': r.MerchantName, 'contact_person': r.ContactPerson or '', 'phone': r.Phone or ''} for r in results]
        return items
