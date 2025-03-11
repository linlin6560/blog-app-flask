# 使用官方 Python 3.11 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# 暴露端口（Gunicorn 默认使用 8000）
EXPOSE 8000

# 启动 Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]