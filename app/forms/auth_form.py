# 认证相关表单
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo


class LoginForm(FlaskForm):
    """
    用户登录表单
    """
    username = StringField('用户名', validators=[DataRequired('用户名不能为空'), Length(min=2, max=50, message='用户名长度必须在2到50个字符之间')])
    password = PasswordField('密码', validators=[DataRequired('密码不能为空')])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class RegisterForm(FlaskForm):
    """
    用户注册表单
    """
    username = StringField('用户名', validators=[DataRequired('用户名不能为空'), Length(min=2, max=50, message='用户名长度必须在2到50个字符之间')])
    password = PasswordField('密码', validators=[DataRequired('密码不能为空'), Length(min=8, max=100, message='密码长度必须在8到100个字符之间')])
    confirm_password = PasswordField('确认密码', validators=[DataRequired('请确认密码'), EqualTo('password', message='两次输入的密码不一致')])
    real_name = StringField('真实姓名', validators=[DataRequired('真实姓名不能为空'), Length(min=2, max=50, message='真实姓名长度必须在2到50个字符之间')])
    phone = StringField('手机号码', validators=[DataRequired('手机号码不能为空'), Length(min=11, max=11, message='手机号码必须是11位')])
    email = StringField('邮箱地址', validators=[Email('请输入有效的邮箱地址')])
    submit = SubmitField('注册')
