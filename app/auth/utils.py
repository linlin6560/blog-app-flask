import os
import secrets
from PIL import Image
from flask import current_app

def save_avatar(file, size=(150, 150)):
    """保存用户头像并返回文件名"""
    if not file:
        return None
        
    # 创建随机文件名，避免文件名冲突
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(file.filename)
    file_name = random_hex + file_ext
    
    # 确保目标文件夹存在
    upload_folder = os.path.join(current_app.root_path, 'static', 'avatars')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    file_path = os.path.join(upload_folder, file_name)
    
    # 使用Pillow调整图片大小并保存
    i = Image.open(file)
    i.thumbnail(size)
    i.save(file_path)
    
    # 返回相对路径，使用正斜杠
    return 'avatars/' + file_name