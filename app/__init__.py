import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_moment import Moment
from flask_ckeditor import CKEditor
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
moment = Moment()
ckeditor = CKEditor()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 配置日志
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/blog.log',
                                         maxBytes=10240,
                                         backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('博客启动')
    else:
        # 在调试模式下也启用文件日志
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/blog.log',
                                         maxBytes=10240,
                                         backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)
    ckeditor.init_app(app)
    csrf.init_app(app)
    
    # 设置登录视图
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    
    # 注册蓝图
    from app.auth import auth as auth_blueprint
    from app.main import main as main_blueprint
    
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)
    
    return app 