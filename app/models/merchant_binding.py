# -*- coding: utf-8 -*-
"""
商户绑定模型
对应数据库 MerchantBinding 表
"""

import datetime


class MerchantBinding:
    """
    商户绑定模型类，用于表示数据库中的 MerchantBinding 表
    管理用户与商户的绑定关系及审批流程
    """

    # 状态常量
    STATUS_PENDING = 'Pending'
    STATUS_APPROVED = 'Approved'
    STATUS_REJECTED = 'Rejected'
    STATUS_CANCELLED = 'Cancelled'

    # 角色常量
    ROLE_BOSS = 'Boss'
    ROLE_STAFF = 'Staff'
    ROLE_FINANCE = 'Finance'

    ROLE_CHOICES = [
        (ROLE_BOSS, '老板'),
        (ROLE_STAFF, '员工'),
        (ROLE_FINANCE, '财务'),
    ]

    def __init__(self, binding_id=None, user_id=None, merchant_id=None,
                 bind_role=None, status=None, apply_time=None,
                 approve_time=None, approver_id=None, reject_reason=None,
                 remark=None, is_active=True,
                 merchant_name=None, user_real_name=None):
        self.binding_id = binding_id
        self.user_id = user_id
        self.merchant_id = merchant_id
        self.bind_role = bind_role
        self.status = status or self.STATUS_PENDING
        self.apply_time = apply_time or datetime.datetime.now()
        self.approve_time = approve_time
        self.approver_id = approver_id
        self.reject_reason = reject_reason
        self.remark = remark
        self.is_active = is_active
        self.merchant_name = merchant_name
        self.user_real_name = user_real_name

    @property
    def bind_role_display(self):
        """绑定角色的中文显示名"""
        role_map = {self.ROLE_BOSS: '老板', self.ROLE_STAFF: '员工', self.ROLE_FINANCE: '财务'}
        return role_map.get(self.bind_role, self.bind_role)

    @property
    def status_display(self):
        """状态的中文显示名"""
        status_map = {
            self.STATUS_PENDING: '待审批',
            self.STATUS_APPROVED: '已通过',
            self.STATUS_REJECTED: '已驳回',
            self.STATUS_CANCELLED: '已取消',
        }
        return status_map.get(self.status, self.status)

    def __repr__(self):
        return f"<MerchantBinding(binding_id={self.binding_id}, user_id={self.user_id}, merchant_id={self.merchant_id}, status='{self.status}')>"
