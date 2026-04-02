# 认证相关路由
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app.forms.auth_form import LoginForm, RegisterForm
from app.services.auth_service import AuthService

# 创建蓝图
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    用户登录页面
    """
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # 验证用户
        user = AuthService.login(username, password)
        
        if user:
            # 登录用户
            login_user(user)
            flash('登录成功', 'success')
            
            # 重定向到首页
            return redirect(url_for('auth.index'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    用户注册页面
    """
    form = RegisterForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        real_name = form.real_name.data
        phone = form.phone.data
        email = form.email.data
        
        # 注册用户
        user = AuthService.register(username, password, real_name, phone, email, roles=['staff'])
        
        if user:
            flash('注册成功', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('用户名已存在', 'danger')
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """
    用户登出
    """
    logout_user()
    flash('您已成功登出', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/')
def index():
    """
    系统首页
    """
    from datetime import datetime
    current_time = datetime.now()
    return render_template('index.html', current_time=current_time)
