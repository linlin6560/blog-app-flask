from flask import Blueprint

main = Blueprint('main', __name__)

from . import routes  # 这行必须在创建蓝图之后 