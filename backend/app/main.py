from fastapi import FastAPI
from app.database import Base, engine
from app.models.user import User
from app.models.pet import Pet
from app.models.category import PetCategory
from app.models.conversation import Conversation, Message
from app.api import api
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from app.common.exceptions import (
    BusinessException,
    bussiness_excpetion_hadler,
    http_excpetion_hadler,
    validation_excpetion_hadler,
    global_excpetion_hadler,
)
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.common.logger import get_logger, setup_logging
from app.config import UPLOAD_DIR, setting

setup_logging()
log = get_logger(__name__)

try:
    Base.metadata.create_all(bind=engine)
except Exception as exc:  # noqa: BLE001
    # 数据库不可用时不要直接崩在 import 阶段，给出可诊断的提示
    log.error("建表失败，请检查 DATABASE_URL 与数据库服务是否可用：%s", exc)

app = FastAPI()


# 挂载静态资源：/uploads/xxx.jpg → uploads/xxx.jpg
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(api)

# 注册异常处理器
app.add_exception_handler(BusinessException, bussiness_excpetion_hadler)
app.add_exception_handler(HTTPException, http_excpetion_hadler)
app.add_exception_handler(RequestValidationError, validation_excpetion_hadler)
# 全局的异常兜底，必须放在最后注册！！
app.add_exception_handler(Exception, global_excpetion_hadler)

origins = [o.strip() for o in setting.CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的前端源，不要直接写 ["*"]
    allow_credentials=True,  # ✅ 关键：允许前端携带 Authorization token
    allow_methods=["*"],  # 允许所有请求方法 GET POST PUT DELETE OPTIONS
    allow_headers=["*"],  # 允许所有请求头（包含Authorization）
)
