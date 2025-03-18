from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFError
from app import db
from app.main import bp
from app.models.post import Post, Category
from app.main.forms import PostForm
from app.services.ai_service import AIService
from flask import Response, stream_with_context
from app.decorators import role_required
from datetime import datetime
from app.models.seller import Seller
from app.models import User
from app.models import Team  # 添加这行导入

# 在文件顶部添加这些导入（如果尚未存在）
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.main import bp
from app.models.seller import Seller
from app.models.seller_assignment import SellerAssignment
from datetime import datetime

@bp.route('/')  # 修改所有的 @main 为 @bp
@bp.route('/index')
def index():
    # 如果用户已登录，重定向到人员管理页面
    if current_user.is_authenticated:
        return redirect(url_for('main.employees'))
    # 否则显示登录页面
    return redirect(url_for('auth.login'))
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category_id', type=int)
    
    query = Post.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    # 添加首页需要的变量
    now = datetime.now()
    
    # 这些是示例数据，实际应用中应该从数据库获取
    pending_tasks = 5
    completed_tasks = 12
    total_sellers = 150
    recent_activities_count = 8
    
    # 示例待办事项列表
    todo_list = [
        {
            'id': 1,
            'type': 'approval',
            'title': '新卖家审批',
            'seller_id': 'S12345',
            'seller_name': '北京科技有限公司',
            'created_at': '2025-03-10',
            'due_date': '2025-03-15',
            'priority': 'high'
        },
        {
            'id': 2,
            'type': 'assignment',
            'title': 'AM分配任务',
            'seller_id': 'S12346',
            'seller_name': '上海贸易有限公司',
            'created_at': '2025-03-11',
            'due_date': '2025-03-16',
            'priority': 'medium'
        }
    ]
    
    # 示例最近活动列表
    recent_activities_list = [
        {
            'title': '完成卖家审批',
            'description': '已审批通过 S12340 上海电子科技',
            'time': '1小时前',
            'user': '管理员'
        },
        {
            'title': '分配AM',
            'description': '将 S12338 分配给 张经理',
            'time': '3小时前',
            'user': '系统'
        }
    ]
    
    return render_template('main/index.html', 
                          posts=posts,
                          now=now,
                          pending_tasks=pending_tasks,
                          completed_tasks=completed_tasks,
                          total_sellers=total_sellers,
                          recent_activities=recent_activities_count,
                          todo_list=todo_list,
                          recent_activities_list=recent_activities_list)

@bp.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('main/post.html', post=post)

# 添加图片上传处理函数
import os
import secrets
from PIL import Image
from flask import current_app

def save_image(file, folder='post_images', size=(800, 600)):
    """保存上传的图片并返回文件名"""
    if not file:
        return None
        
    # 创建随机文件名，避免文件名冲突
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(file.filename)
    file_name = random_hex + file_ext
    
    # 确保目标文件夹存在
    upload_folder = os.path.join(current_app.root_path, 'static', folder)
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    file_path = os.path.join(upload_folder, file_name)
    
    # 使用Pillow调整图片大小并保存
    i = Image.open(file)
    i.thumbnail(size)
    i.save(file_path)
    
    # 返回相对路径，确保使用正斜杠
    return folder + '/' + file_name

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    form.category.choices = [(0, '无分类')]
    # 添加数据库中的分类选项
    categories = Category.query.all()
    for category in categories:
        form.category.choices.append((category.id, category.name))
    
    if form.validate_on_submit():
        # 处理图片上传
        image_file = None
        if form.image.data:
            current_app.logger.info(f"正在处理图片上传: {form.image.data.filename}")
            image_file = save_image(form.image.data)
            current_app.logger.info(f"图片已保存，路径为: {image_file}")
            
        # Create the post object after handling the image
        post = Post(
            title=form.title.data,
            content=form.content.data,
            summary=form.summary.data,
            author=current_user,
            image=image_file  # 保存图片路径
        )
        
        if form.category.data > 0:
            post.category_id = form.category.data
            
        db.session.add(post)
        db.session.commit()
        flash('文章发布成功!', 'success')
        return redirect(url_for('main.post', post_id=post.id))  # 使用 'main.post' 而不是 'bp.post'
        
    return render_template('main/create_post.html', form=form)

@bp.route('/chat')
def chat():
    return render_template('chat.html')

@bp.errorhandler(CSRFError)
def handle_csrf_error(e):
    current_app.logger.error(f"CSRF错误: {str(e)}")
    return jsonify({'error': 'CSRF验证失败'}), 400

@bp.route('/api/chat', methods=['POST'])
@bp.route('/chat_api', methods=['POST'])
def chat_api():
    try:
        data = request.get_json()
        current_app.logger.info(f"解析后的JSON数据: {data}")
        
        if not data or 'message' not in data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        message = data['message']
        
        messages = [
            {"role": "system", "content": "你是一个友好、专业的AI助手，可以帮助用户解答各种问题。"},
            {"role": "user", "content": message}
        ]

        current_app.logger.info(f"发送到AI服务的消息: {messages}")
        
        # 不使用流式响应，改为普通响应
        ai_service = AIService()
        response = ai_service.get_chat_response(messages)
        
        return jsonify({'response': response})
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"处理请求时发生错误: {str(e)}")
        current_app.logger.error(f"错误堆栈: {traceback.format_exc()}")
        return jsonify({'error': '服务器内部错误'}), 500

@bp.route('/stream_chat')
def stream_chat():
    message = request.args.get('message', '')
    if not message:
        return "数据不能为空", 400
    
    # 创建应用上下文
    from app import create_app
    app = create_app()
    
    def generate():
        with app.app_context():
            messages = [
                {"role": "system", "content": "你是一个友好、专业的AI助手，可以帮助用户解答各种问题。"},
                {"role": "user", "content": message}
            ]
            
            ai_service = AIService()
            
            yield "data: 正在思考...\n\n"
            
            try:
                for chunk in ai_service.get_chat_response_stream(messages):
                    if chunk:
                        yield f"data: {chunk}\n\n"
                
                yield "data: [DONE]\n\n"
            except Exception as e:
                current_app.logger.error(f"生成响应时出错: {str(e)}")
                yield f"data: 抱歉，生成回复时出错: {str(e)}\n\n"
                yield "data: [DONE]\n\n"
    
    return Response(generate(), mimetype='text/event-stream')
# 添加删除文章的路由
@bp.route('/post/<int:post_id>/delete')
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # 检查当前用户是否是文章作者
    if post.user_id != current_user.id:
        flash('您没有权限删除这篇文章！', 'danger')
        return redirect(url_for('main.post', post_id=post_id))  # 使用 'main.post' 而不是 'bp.post'
    
    # 删除文章关联的图片文件
    if post.image:
        try:
            image_path = os.path.join(current_app.root_path, 'static', post.image)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            current_app.logger.error(f"删除图片文件失败: {str(e)}")
    
    # 删除文章
    db.session.delete(post)
    db.session.commit()
    
    flash('文章已成功删除！', 'success')
    return redirect(url_for('main.index'))  # 使用 'main.index' 而不是 'bp.index'


@bp.route('/approval_poc')
@login_required
def approval_poc():
    # 检查用户是否有权限访问此页面
    if not current_user.has_role('from_team_approve_poc'):
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 这里添加处理逻辑
    return render_template('main/approval_poc.html', title='From AM Approval POC')

@bp.route('/assignment-poc')
@login_required
@role_required('assignment_poc')
def assignment_poc():
    """分配管理页面"""
    return render_template('main/assignment_poc.html')

# 删除 ApplicationForm 类和 create_application 路由
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

class ApplicationForm(FlaskForm):
    seller_id = StringField('卖家记号', validators=[DataRequired()])
    shop_name = StringField('签约账户店铺名称', validators=[DataRequired()])
    gms_tag = StringField('GMS tag')
    rejoin_tag = StringField('Rejoin tag')
    primary_category = StringField('Primary Category')
    key_contact = StringField('关键联系人')
    leads_source = StringField('Leads/Opp Source')
    bd = StringField('BD')
    am_team = StringField('AM Team')

@bp.route('/create-application', methods=['GET', 'POST'])
@login_required
def create_application():
    """创建新申请"""
    form = ApplicationForm()
    if form.validate_on_submit():
        # TODO: 处理表单提交
        flash('申请已提交', 'success')
        return redirect(url_for('main.index'))
    return render_template('main/create_application.html', form=form)

@bp.route('/from_team_assignment')
@login_required
@role_required('from_team_assignment_poc')
def from_team_assignment():
    """From-team AM Assignment POC 页面"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    # 构建查询
    query = Seller.query
    
    # 应用状态筛选
    if status:
        query = query.filter(Seller.status == status)
    
    # 应用搜索条件
    if search:
        query = query.filter(
            (Seller.seller_id.like(f'%{search}%')) | 
            (Seller.seller_name.like(f'%{search}%'))
        )
    
    # 获取分页数据
    sellers = query.order_by(Seller.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # 获取团队和AM用户列表（用于分配表单）
    teams = Team.query.all()
    am_users = User.query.filter(User.team_id.isnot(None)).all()
    
    # 统计数据
    stats = {
        'pending_count': Seller.query.filter_by(status='待分配').count(),
        'assigned_count': Seller.query.filter_by(status='已分配').count(),
        'rejected_count': Seller.query.filter_by(status='已拒绝').count()
    }
    
    return render_template(
        'main/from_team_assignment.html',
        sellers=sellers,
        teams=teams,
        am_users=am_users,
        stats=stats
    )

@bp.route('/assign_seller/<string:seller_id>', methods=['POST'])
@login_required
@role_required('from_team_assignment_poc')
def assign_seller(seller_id):
    """分配卖家给AM"""
    seller = Seller.query.filter_by(seller_id=seller_id).first_or_404()
    am_id = request.form.get('am_id', type=int)
    note = request.form.get('note', '')
    
    if not am_id:
        flash('请选择AM', 'danger')
        return redirect(url_for('main.from_team_assignment'))
    
    # 创建分配记录
    assignment = SellerAssignment(
        seller_id=seller_id,
        am_user_id=am_id,
        assigned_at=datetime.now(),
        assigned_by=current_user.id
    )
    
    # 更新卖家状态
    seller.status = '已分配'
    seller.updated_at = datetime.now()
    
    db.session.add(assignment)
    db.session.commit()
    
    flash(f'卖家 {seller.seller_name} 已成功分配', 'success')
    return redirect(url_for('main.from_team_assignment'))

@bp.route('/reject_seller/<string:seller_id>', methods=['POST'])
@login_required
@role_required('from_team_assignment_poc')
def reject_seller(seller_id):
    """拒绝分配卖家"""
    seller = Seller.query.filter_by(seller_id=seller_id).first_or_404()
    team_id = request.form.get('team_id', type=int)
    note = request.form.get('note', '')
    
    # 获取选择的团队
    team = Team.query.get(team_id)
    
    # 创建审批记录
    from app.models.approval import Approval  # 确保导入Approval模型
    
    approval = Approval(
        seller_id=seller_id,
        approval_type='Cross team special approval',
        applicant_id=current_user.id,
        status='已拒绝',
        reason=note,  # 直接使用备注作为拒绝原因
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # 更新卖家状态
    seller.status = '已拒绝'
    seller.updated_at = datetime.now()
    
    db.session.add(approval)
    db.session.commit()
    
    flash(f'卖家 {seller.seller_name} 已拒绝分配并转交给团队 {team.name if team else "未知团队"}', 'success')
    return redirect(url_for('main.from_team_assignment'))

@bp.route('/from-am-approval-poc')
@role_required('from_team_approve_poc')
def from_am_approval_poc():
    return render_template('main/from_am_approval_poc.html', title='From AM Approval POC')


@bp.route('/accept_seller/<int:seller_id>', methods=['POST'])
@login_required
def accept_seller(seller_id):
    seller = Seller.query.get_or_404(seller_id)
    am_id = request.form.get('am_id', type=int)
    # 移除notes变量，因为表中没有对应字段
    
    # 验证AM选择
    if not am_id:
        flash('请选择AM', 'danger')
        return redirect(url_for('main.from_team_assignment'))
    
    # 获取选择的AM用户
    am_user = User.query.get(am_id)
    if not am_user:
        flash('选择的AM不存在', 'danger')
        return redirect(url_for('main.from_team_assignment'))
    
    # 更新卖家状态
    seller.status = '已分配'
    
    # 创建分配记录 - 移除notes参数
    assignment = SellerAssignment(
        seller_id=seller.seller_id,
        am_user_id=am_id,  # 使用选择的AM ID
        assigned_at=datetime.utcnow(),
        assigned_by=current_user.id  # 当前用户作为分配者
    )
    
    db.session.add(assignment)
    db.session.commit()
    
    flash(f'已成功将卖家 {seller.seller_name} 分配给 {am_user.username}', 'success')
    return redirect(url_for('main.from_team_assignment'))

# 员工管理 - 列表页面
@bp.route('/employees')
@login_required
def employees():
    search = request.args.get('search', '')
    department = request.args.get('department', '')
    employee_type = request.args.get('employee_type', '')
    
    # 构建查询
    query = Employee.query
    
    # 应用搜索条件
    if search:
        query = query.filter(
            (Employee.name.like(f'%{search}%')) | 
            (Employee.yida_id.like(f'%{search}%')) |
            (Employee.gid.like(f'%{search}%')) |
            (Employee.email.like(f'%{search}%')) |
            (Employee.phone.like(f'%{search}%'))
        )
    
    if department:
        query = query.filter(Employee.department == department)
    
    if employee_type:
        query = query.filter(Employee.employee_type == employee_type)
    
    # 获取所有数据（不分页）
    employees = query.order_by(Employee.id.desc()).all()
    
    # 获取所有部门（用于筛选）
    departments = [(d.department, d.department) for d in db.session.query(Employee.department).distinct()]
    departments.insert(0, ('', '所有部门'))
    
    # 创建搜索表单
    form = EmployeeSearchForm()
    form.department.choices = departments
    
    # 创建导入表单
    import_form = ImportEmployeeForm()
    
    return render_template(
        'main/employees.html',
        title='人员管理',
        employees=employees,
        form=form,
        import_form=import_form,
        search=search,
        department=department,
        employee_type=employee_type
    )

# 员工管理 - 添加员工
@bp.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    form = EmployeeForm()
    if form.validate_on_submit():
        employee = Employee(
            name=form.name.data,
            yida_id=form.yida_id.data,
            gid=form.gid.data,
            email=form.email.data,
            work_calendar=form.work_calendar.data,
            department=form.department.data,
            gender=form.gender.data,
            project=form.project.data,
            employee_type=form.employee_type.data,
            phone=form.phone.data
        )
        db.session.add(employee)
        db.session.commit()
        flash('员工信息已成功添加！', 'success')
        return redirect(url_for('main.employees'))
    return render_template('main/employee_form.html', title='添加员工', form=form)

# 员工管理 - 编辑员工
@bp.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee)
    if form.validate_on_submit():
        employee.name = form.name.data
        employee.yida_id = form.yida_id.data
        employee.gid = form.gid.data
        employee.email = form.email.data
        employee.work_calendar = form.work_calendar.data
        employee.department = form.department.data
        employee.gender = form.gender.data
        employee.project = form.project.data
        employee.employee_type = form.employee_type.data
        employee.phone = form.phone.data
        employee.updated_at = datetime.utcnow()
        db.session.commit()
        flash('员工信息已成功更新！', 'success')
        return redirect(url_for('main.employees'))
    return render_template('main/employee_form.html', title='编辑员工', form=form)

# 员工管理 - 删除员工
@bp.route('/employees/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    db.session.delete(employee)
    db.session.commit()
    flash('员工信息已成功删除！', 'success')
    return redirect(url_for('main.employees'))

# 员工管理 - 导出Excel
@bp.route('/employees/export')
@login_required
def export_employees():
    # 获取所有员工数据
    employees = Employee.query.all()
    
    # 创建DataFrame
    data = []
    for emp in employees:
        data.append({
            'ID': emp.id,
            '姓名': emp.name,
            'YIDA员工ID': emp.yida_id,
            'GID': emp.gid,
            '电子邮箱': emp.email,
            '工作日历': emp.work_calendar,
            '所属部门': emp.department,
            '性别': emp.gender,
            '项目名称': emp.project,
            '社员区分': emp.employee_type,
            '联系电话': emp.phone
        })
    
    df = pd.DataFrame(data)
    
    # 创建一个BytesIO对象
    output = io.BytesIO()
    
    # 使用ExcelWriter写入Excel，使用xlsxwriter引擎
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='员工信息', index=False)
        
        # 获取xlsxwriter工作簿和工作表对象
        workbook = writer.book
        worksheet = writer.sheets['员工信息']
        
        # 设置列宽
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
    
    # 设置文件指针到开始
    output.seek(0)
    
    # 生成下载文件名
    filename = f"员工信息_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    # 返回Excel文件
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# 员工管理 - 导入Excel
@bp.route('/employees/import', methods=['POST'])
@login_required
def import_employees():
    form = ImportEmployeeForm()
    if form.validate_on_submit():
        try:
            # 获取上传的文件
            file = form.file.data
            
            # 读取Excel文件
            df = pd.read_excel(file)
            
            # 验证Excel文件格式
            required_columns = ['姓名', 'YIDA员工ID', 'GID', '电子邮箱', 
                              '工作日历', '所属部门', '性别', '项目名称', 
                              '社员区分', '联系电话']
            
            # 检查是否包含所有必需的列
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f'Excel文件缺少以下列: {", ".join(missing_columns)}', 'danger')
                return redirect(url_for('main.employees'))
            
            # 处理每一行数据
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    # 如果有ID列，尝试更新现有记录
                    if 'ID' in df.columns and not pd.isna(row['ID']):
                        employee = Employee.query.get(int(row['ID']))
                        if employee:
                            # 更新现有员工
                            employee.name = row['姓名']
                            employee.yida_id = str(row['YIDA员工ID'])
                            employee.gid = str(row['GID'])
                            employee.email = row['电子邮箱']
                            employee.work_calendar = row['工作日历']
                            employee.department = row['所属部门']
                            employee.gender = row['性别']
                            employee.project = row['项目名称']
                            employee.employee_type = row['社员区分']
                            employee.phone = str(row['联系电话'])
                            employee.updated_at = datetime.utcnow()
                        else:
                            # ID不存在，创建新员工
                            employee = Employee(
                                name=row['姓名'],
                                yida_id=str(row['YIDA员工ID']),
                                gid=str(row['GID']),
                                email=row['电子邮箱'],
                                work_calendar=row['工作日历'],
                                department=row['所属部门'],
                                gender=row['性别'],
                                project=row['项目名称'],
                                employee_type=row['社员区分'],
                                phone=str(row['联系电话'])
                            )
                            db.session.add(employee)
                    else:
                        # 没有ID列，创建新员工
                        employee = Employee(
                            name=row['姓名'],
                            yida_id=str(row['YIDA员工ID']),
                            gid=str(row['GID']),
                            email=row['电子邮箱'],
                            work_calendar=row['工作日历'],
                            department=row['所属部门'],
                            gender=row['性别'],
                            project=row['项目名称'],
                            employee_type=row['社员区分'],
                            phone=str(row['联系电话'])
                        )
                        db.session.add(employee)
                    
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    current_app.logger.error(f"导入第{index+1}行时出错: {str(e)}")
            
            db.session.commit()
            flash(f'导入完成！成功导入{success_count}条记录，失败{error_count}条记录', 'success')
            return redirect(url_for('main.employees'))
            
        except Exception as e:
            flash(f'导入失败: {str(e)}', 'danger')
            current_app.logger.error(f"Excel导入失败: {str(e)}")
            return redirect(url_for('main.employees'))
    
    flash('请选择有效的Excel文件', 'warning')
    return redirect(url_for('main.employees'))

# 员工管理 - 批量删除
@bp.route('/employees/batch_delete', methods=['POST'])
@login_required
def batch_delete_employees():
    employee_ids = request.form.getlist('employee_ids')
    
    if not employee_ids:
        flash('请选择要删除的员工', 'warning')
        return redirect(url_for('main.employees'))
    
    try:
        # 批量删除选中的员工
        deleted_count = 0
        for employee_id in employee_ids:
            employee = Employee.query.get(int(employee_id))
            if employee:
                db.session.delete(employee)
                deleted_count += 1
        
        db.session.commit()
        flash(f'成功删除{deleted_count}名员工', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')
        current_app.logger.error(f"批量删除员工失败: {str(e)}")
    
    return redirect(url_for('main.employees'))

# 员工管理 - 查看员工详情
@bp.route('/employees/view/<int:id>')
@login_required
def view_employee(id):
    employee = Employee.query.get_or_404(id)
    return render_template('main/employee_view.html', title='员工详情', employee=employee)

# 员工管理 - 搜索员工
@bp.route('/employees/search')
@login_required
def search_employees():
    search_term = request.args.get('search', '')
    if not search_term:
        return redirect(url_for('main.employees'))
    
    # 构建查询
    query = Employee.query.filter(
        (Employee.name.like(f'%{search_term}%')) | 
        (Employee.yida_id.like(f'%{search_term}%')) |
        (Employee.gid.like(f'%{search_term}%')) |
        (Employee.email.like(f'%{search_term}%')) |
        (Employee.phone.like(f'%{search_term}%'))
    )
    
    # 获取分页数据
    page = request.args.get('page', 1, type=int)
    employees = query.order_by(Employee.id.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # 获取所有部门（用于筛选）
    departments = [(d.department, d.department) for d in db.session.query(Employee.department).distinct()]
    departments.insert(0, ('', '所有部门'))
    
    # 创建搜索表单
    form = EmployeeSearchForm()
    form.department.choices = departments
    
    # 创建导入表单
    import_form = ImportEmployeeForm()
    
    return render_template(
        'main/employees.html',
        title='搜索结果',
        employees=employees,
        form=form,
        import_form=import_form,
        search=search_term
    )

# 员工管理 - 下载导入模板
@bp.route('/employees/download_template')
@login_required
def download_template():
    # 创建示例数据
    data = {
        '姓名': ['张三', '李四'],
        'YIDA员工ID': ['60000001', '60000002'],
        'GID': ['510000001', '510000002'],
        '电子邮箱': ['zhangsan@example.com', 'lisi@example.com'],
        '工作日历': ['SN_CN', 'SN_CN'],
        '所属部门': ['SG-dalian', 'SG-dalian'],
        '性别': ['男', '女'],
        '项目名称': ['Palt', 'Palt'],
        '社员区分': ['正社员', '契约社员'],
        '联系电话': ['13000000001', '13000000002']
    }
    
    df = pd.DataFrame(data)
    
    # 创建一个BytesIO对象
    output = io.BytesIO()
    
    # 使用ExcelWriter写入Excel
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='员工信息模板', index=False)
        
        # 获取xlsxwriter工作簿和工作表对象
        workbook = writer.book
        worksheet = writer.sheets['员工信息模板']
        
        # 设置列宽
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
    
    # 设置文件指针到开始
    output.seek(0)
    
    # 返回Excel文件
    return send_file(
        output,
        as_attachment=True,
        download_name='员工信息导入模板.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# 员工管理 - 统计报表
@bp.route('/employees/statistics')
@login_required
def employee_statistics():
    # 按部门统计
    department_stats = db.session.query(
        Employee.department, 
        db.func.count(Employee.id)
    ).group_by(Employee.department).all()
    
    # 按员工类型统计
    type_stats = db.session.query(
        Employee.employee_type, 
        db.func.count(Employee.id)
    ).group_by(Employee.employee_type).all()
    
    # 按性别统计
    gender_stats = db.session.query(
        Employee.gender, 
        db.func.count(Employee.id)
    ).group_by(Employee.gender).all()
    
    # 按项目统计
    project_stats = db.session.query(
        Employee.project, 
        db.func.count(Employee.id)
    ).group_by(Employee.project).all()
    
    # 准备图表数据
    department_labels = [item[0] for item in department_stats]
    department_values = [item[1] for item in department_stats]
    
    type_labels = [item[0] for item in type_stats]
    type_values = [item[1] for item in type_stats]
    
    gender_labels = [item[0] for item in gender_stats]
    gender_values = [item[1] for item in gender_stats]
    
    project_labels = [item[0] for item in project_stats]
    project_values = [item[1] for item in project_stats]
    
    return render_template(
        'main/employee_statistics.html',
        title='员工统计',
        department_labels=department_labels,
        department_values=department_values,
        type_labels=type_labels,
        type_values=type_values,
        gender_labels=gender_labels,
        gender_values=gender_values,
        project_labels=project_labels,
        project_values=project_values
    )

# 确保在文件顶部添加必要的导入
from flask import send_file, current_app
from app.forms.employee import EmployeeForm, EmployeeSearchForm, ImportEmployeeForm
from app.models.employee import Employee
import pandas as pd
import io
