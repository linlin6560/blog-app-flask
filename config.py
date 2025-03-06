import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')  # 注意这里改为 instance 目录
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 硅基流动API配置
    SILICONFLOW_API_KEY = os.environ.get('SILICONFLOW_API_KEY') or "sk-lfqrjuvlcjlibudqjknvjhjzhqaobphpfquokxbqcsvadjmo"
    SILICONFLOW_API_URL = os.environ.get('SILICONFLOW_API_URL') or "https://api.siliconflow.cn/v1/chat/completions"
    SILICONFLOW_MODEL = os.environ.get('SILICONFLOW_MODEL') or "deepseek-ai/DeepSeek-V3"
    
    # 日志配置
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
    # 其他配置... 