from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.auth import auth
from app.auth.forms import LoginForm, RegistrationForm
from app.models.user import User

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('邮箱或密码错误', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='登录', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('注册成功！请登录', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='注册', form=form)

# 在文件顶部添加必要的导入
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.auth.forms import ProfileForm
from app.auth.utils import save_avatar

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        if form.avatar.data:
            avatar_file = save_avatar(form.avatar.data)
            current_user.avatar = avatar_file
        
        current_user.username = form.username.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('个人资料已更新!', 'success')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.bio.data = current_user.bio
    
    return render_template('auth/profile.html', form=form)