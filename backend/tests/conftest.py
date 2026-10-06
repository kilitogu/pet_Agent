"""共享 fixture：内存 SQLite（不依赖 MySQL，可离线运行）。"""

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 让 `app` 包在测试中可导入（backend/ 加入 sys.path）
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import Base
from app.models.category import PetCategory  # noqa: F401  注册到 metadata
from app.models.conversation import Conversation, Message  # noqa: F401
from app.models.pet import Pet
from app.models.user import User


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def user(db):
    u = User(username="tester", password="x", name="测试用户", role="user", status=1)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def admin(db):
    u = User(username="boss", password="x", name="管理员", role="admin", status=1)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def pets(db):
    rows = [
        Pet(name="咪咪", species="猫", breed="橘猫", age=8, gender="母", status=1),
        Pet(name="旺财", species="狗", breed="中华田园犬", age=14, gender="公", status=1),
        Pet(name="雪球", species="猫", breed="布偶", age=5, gender="母", status=0),
    ]
    db.add_all(rows)
    db.commit()
    return rows
