from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length
from flask_wtf.file import FileField, FileAllowed

class EmployeeForm(FlaskForm):
    name = StringField('姓名', validators=[DataRequired()])
    yida_id = StringField('YIDA员工ID', validators=[DataRequired()])
    gid = StringField('GID', validators=[DataRequired()])
    email = StringField('电子邮箱', validators=[DataRequired(), Email()])
    work_calendar = StringField('工作日历', validators=[DataRequired()])
    department = StringField('所属部门', validators=[DataRequired()])
    # 将性别从SelectField改为StringField
    gender = StringField('性别', validators=[DataRequired()])
    project = StringField('项目名称', validators=[DataRequired()])
    # 将社员区分从SelectField改为StringField
    employee_type = StringField('社员区分', validators=[DataRequired()])
    phone = StringField('联系电话', validators=[DataRequired()])
    submit = SubmitField('提交')

class EmployeeSearchForm(FlaskForm):
    search = StringField('搜索')
    department = SelectField('部门', choices=[('', '所有部门')], validators=[])
    employee_type = SelectField('社员区分', choices=[
        ('', '所有类型'),
        ('正社员', '正社员'), 
        ('契约社员', '契约社员'),
        ('派遣社员', '派遣社员'),
        ('实习生', '实习生')
    ], validators=[])
    submit = SubmitField('搜索')

class ImportEmployeeForm(FlaskForm):
    file = FileField('选择Excel文件', validators=[
        FileAllowed(['xls', 'xlsx'], message='只允许上传Excel文件(.xls或.xlsx)')
    ])
    submit = SubmitField('导入')