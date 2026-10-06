from datetime import datetime
from sqlalchemy import DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from app.config import setting

engine = create_engine(setting.DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, active_history=True, comment="主键ID",sort_order=-1)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间", sort_order=1)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间", sort_order=2)