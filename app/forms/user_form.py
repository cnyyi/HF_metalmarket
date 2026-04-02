# 用户管理表单
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email, Regexp, Optional


class UserAddForm(FlaskForm):
    """
    添加用户表单
    """
    username = StringField('用户名', validators=[
        DataRequired('用户名不能为空'),
        Length(min=3, max=50, message='用户名长度必须在3到50个字符之间'),
        Regexp(r'^[a-zA-Z0-9_]+$', message='用户名只能包含字母、数字和下划线')
    ])
    password = PasswordField('密码', validators=[
        DataRequired('密码不能为空'),
        Length(min=6, max=20, message='密码长度必须在6到20个字符之间'),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{6,20}$', 
               message='密码必须包含大小写字母和数字')
    ])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired('确认密码不能为空'),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{6,20}$', 
               message='密码必须包含大小写字母和数字')
    ])
    real_name = StringField('真实姓名', validators=[
        DataRequired('真实姓名不能为空'),
        Length(min=2, max=50, message='真实姓名长度必须在2到50个字符之间')
    ])
    phone = StringField('电话号码', validators=[
        DataRequired('电话号码不能为空'),
        Regexp(r'^1[3-9]\d{9}$|^\d{3,4}-\d{7,8}$', message='请输入有效的手机号或固定电话')
    ])
    email = StringField('电子邮箱', validators=[
        DataRequired('电子邮箱不能为空'),
        Email(message='请输入有效的电子邮箱地址')
    ])
    roles = SelectMultipleField('角色', coerce=int, validators=[
        DataRequired('请至少选择一个角色')
    ])
    merchant_id = SelectField('关联商户', coerce=int, validators=[
        Optional()
    ])
    submit = SubmitField('添加用户')


class UserEditForm(FlaskForm):
    """
    编辑用户表单
    """
    real_name = StringField('真实姓名', validators=[
        DataRequired('真实姓名不能为空'),
        Length(min=2, max=50, message='真实姓名长度必须在2到50个字符之间')
    ])
    phone = StringField('电话号码', validators=[
        DataRequired('电话号码不能为空'),
        Regexp(r'^1[3-9]\d{9}$|^\d{3,4}-\d{7,8}$', message='请输入有效的手机号或固定电话')
    ])
    email = StringField('电子邮箱', validators=[
        DataRequired('电子邮箱不能为空'),
        Email(message='请输入有效的电子邮箱地址')
    ])
    roles = SelectMultipleField('角色', coerce=int, validators=[
        DataRequired('请至少选择一个角色')
    ])
    is_active = BooleanField('是否有效')
    merchant_id = SelectField('关联商户', coerce=int, validators=[
        Optional()
    ])
    submit = SubmitField('保存修改')


class PasswordChangeForm(FlaskForm):
    """
    密码修改表单
    """
    current_password = PasswordField('当前密码', validators=[
        DataRequired('当前密码不能为空')
    ])
    new_password = PasswordField('新密码', validators=[
        DataRequired('新密码不能为空'),
        Length(min=6, max=20, message='新密码长度必须在6到20个字符之间'),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{6,20}$', 
               message='新密码必须包含大小写字母和数字')
    ])
    confirm_new_password = PasswordField('确认新密码', validators=[
        DataRequired('确认新密码不能为空'),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{6,20}$', 
               message='新密码必须包含大小写字母和数字')
    ])
    submit = SubmitField('修改密码')
