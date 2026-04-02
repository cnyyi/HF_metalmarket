# 商户管理表单
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Regexp, Optional


class MerchantAddForm(FlaskForm):
    """
    添加商户表单
    """
    merchant_name = StringField('商户名称', validators=[
        DataRequired('商户名称不能为空'),
        Length(min=2, max=100, message='商户名称长度必须在2到100个字符之间')
    ])
    legal_person = StringField('法人代表', validators=[
        DataRequired('法人代表不能为空'),
        Length(min=2, max=50, message='法人代表长度必须在2到50个字符之间')
    ])
    contact_person = StringField('联系人', validators=[
        DataRequired('联系人不能为空'),
        Length(min=2, max=50, message='联系人长度必须在2到50个字符之间')
    ])
    phone = StringField('联系电话', validators=[
        DataRequired('联系电话不能为空'),
        Regexp(r'^1[3-9]\d{9}$|^\d{3,4}-\d{7,8}$', message='请输入有效的手机号或固定电话')
    ])
    merchant_type = SelectField('商户类型', coerce=str, validators=[
        DataRequired('请选择商户类型')
    ])
    business_type = SelectField('业务类型', coerce=str, validators=[
        Optional()
    ])
    business_license = StringField('营业执照号', validators=[
        Optional(),
        Length(min=15, max=30, message='营业执照号长度必须在15到30个字符之间')
    ])
    tax_registration = StringField('税务登记证号', validators=[
        Length(max=50, message='税务登记证号长度不能超过50个字符')
    ])
    address = StringField('地址', validators=[
        Optional(),
        Length(max=200, message='地址长度不能超过200个字符')
    ])
    description = TextAreaField('商户描述', validators=[
        Length(max=500, message='商户描述长度不能超过500个字符')
    ])
    submit = SubmitField('添加商户')


class MerchantEditForm(FlaskForm):
    """
    编辑商户表单
    """
    merchant_name = StringField('商户名称', validators=[
        DataRequired('商户名称不能为空'),
        Length(min=2, max=100, message='商户名称长度必须在2到100个字符之间')
    ])
    legal_person = StringField('法人代表', validators=[
        DataRequired('法人代表不能为空'),
        Length(min=2, max=50, message='法人代表长度必须在2到50个字符之间')
    ])
    contact_person = StringField('联系人', validators=[
        DataRequired('联系人不能为空'),
        Length(min=2, max=50, message='联系人长度必须在2到50个字符之间')
    ])
    phone = StringField('联系电话', validators=[
        DataRequired('联系电话不能为空'),
        Regexp(r'^1[3-9]\d{9}$|^\d{3,4}-\d{7,8}$', message='请输入有效的手机号或固定电话')
    ])
    merchant_type = SelectField('商户类型', coerce=str, validators=[
        DataRequired('请选择商户类型')
    ])
    business_type = SelectField('业务类型', coerce=str, validators=[
        Optional()
    ])
    business_license = StringField('营业执照号', validators=[
        Optional(),
        Length(min=15, max=30, message='营业执照号长度必须在15到30个字符之间')
    ])
    tax_registration = StringField('税务登记证号', validators=[
        Length(max=50, message='税务登记证号长度不能超过50个字符')
    ])
    address = StringField('地址', validators=[
        Optional(),
        Length(max=200, message='地址长度不能超过200个字符')
    ])
    description = TextAreaField('商户描述', validators=[
        Length(max=500, message='商户描述长度不能超过500个字符')
    ])
    status = BooleanField('是否正常')
    submit = SubmitField('保存修改')
