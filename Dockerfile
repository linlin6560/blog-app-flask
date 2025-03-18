FROM python:3.11-slim

WORKDIR /app

# 安装编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 先安装固定版本的numpy
RUN pip install --no-cache-dir numpy==1.24.3

# 安装除pandas和numpy外的所有依赖
RUN pip install --no-cache-dir \
    Flask==2.3.3 \
    Flask-SQLAlchemy==3.1.1 \
    Flask-Migrate==4.0.5 \
    Flask-Login==0.6.3 \
    Flask-WTF==1.2.1 \
    Flask-Mail==0.9.1 \
    Flask-Bcrypt==1.0.1 \
    Flask-Moment==1.0.5 \
    Flask-CKEditor==0.4.6 \
    email-validator==2.1.0 \
    SQLAlchemy==2.0.23 \
    psycopg2-binary==2.9.9 \
    pymysql==1.1.0 \
    python-dotenv==1.0.0 \
    Werkzeug==2.3.7 \
    Jinja2==3.1.2 \
    itsdangerous==2.1.2 \
    gunicorn==21.2.0 \
    pytz==2023.3 \
    WTForms==3.1.1 \
    Pillow==10.1.0 \
    python-slugify==8.0.1 \
    alembic==1.12.1 \
    requests==2.31.0 \
    xlsxwriter==3.1.2 \
    openpyxl==3.1.2

# 最后安装pandas
RUN pip install --no-cache-dir pandas==2.0.3

COPY . .

ENV FLASK_APP=run.py
ENV FLASK_ENV=development

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]