from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFError
from app import db
from app.main import main
from app.models.post import Post, Category  # Added Category import here
from app.main.forms import PostForm
from app.services.ai_service import AIService

@main.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category_id', type=int)
    
    query = Post.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    return render_template('main/index.html', posts=posts)

@main.route('/post/<int:post_id>')
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

@main.route('/create', methods=['GET', 'POST'])
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
        return redirect(url_for('main.post', post_id=post.id))
        
    return render_template('main/create_post.html', form=form)

@main.route('/chat')
def chat():
    return render_template('chat.html')

@main.errorhandler(CSRFError)
def handle_csrf_error(e):
    current_app.logger.error(f"CSRF错误: {str(e)}")
    return jsonify({'error': 'CSRF验证失败'}), 400

@main.route('/api/chat', methods=['POST'])
def chat_api():
    try:
        # 记录请求头信息
        current_app.logger.info(f"请求头: {dict(request.headers)}")
        
        # 记录原始请求数据
        current_app.logger.info(f"原始请求数据: {request.data}")
        
        # 尝试解析JSON
        try:
            data = request.get_json()
            current_app.logger.info(f"解析后的JSON数据: {data}")
        except Exception as e:
            current_app.logger.error(f"JSON解析错误: {str(e)}")
            return jsonify({'error': 'JSON格式错误'}), 400
        
        if not data:
            current_app.logger.error("请求数据为空")
            return jsonify({'error': '无效的请求数据'}), 400
            
        if not isinstance(data, dict):
            current_app.logger.error(f"请求数据不是字典类型: {type(data)}")
            return jsonify({'error': '无效的数据格式'}), 400
            
        if 'message' not in data:
            current_app.logger.error(f"请求数据中缺少message字段，现有字段: {data.keys()}")
            return jsonify({'error': '请求数据中缺少message字段'}), 400
            
        if not isinstance(data['message'], str):
            current_app.logger.error(f"message字段不是字符串类型: {type(data['message'])}")
            return jsonify({'error': 'message必须是字符串'}), 400

        messages = [
            {"role": "system", "content": "你是一个友好、专业的AI助手，可以帮助用户解答各种问题。"},
            {"role": "user", "content": data['message']}
        ]

        current_app.logger.info(f"发送到AI服务的消息: {messages}")
        
        ai_service = AIService()
        response = ai_service.get_chat_response(messages)
        
        current_app.logger.info(f"AI服务返回的响应: {response}")
        
        return jsonify({'response': response})
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"处理请求时发生错误: {str(e)}")
        current_app.logger.error(f"错误堆栈: {traceback.format_exc()}")
        return jsonify({'error': '服务器内部错误'}), 500
# 添加删除文章的路由
@main.route('/post/<int:post_id>/delete')
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # 检查当前用户是否是文章作者
    if post.user_id != current_user.id:
        flash('您没有权限删除这篇文章！', 'danger')
        return redirect(url_for('main.post', post_id=post_id))
    
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
    return redirect(url_for('main.index'))