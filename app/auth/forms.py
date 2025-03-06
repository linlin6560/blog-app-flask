from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models.user import User
# Add this if it's not already there
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class ProfileForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    bio = TextAreaField('个人简介', validators=[Length(0, 200)])
    avatar = FileField('头像', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], '只允许上传图片!')])
    submit = SubmitField('保存修改')
class LoginForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册')