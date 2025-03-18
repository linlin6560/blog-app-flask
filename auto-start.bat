@echo off
cd /d D:\source\python\enrollment
docker-compose down
docker-compose build --no-cache
docker-compose up -d
timeout 10  # 等待10秒确保容器启动
start http://localhost:8080  # 自动打开浏览器
