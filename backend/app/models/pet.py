from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer
from app.database import Base


class Pet(Base):
    __tablename__ = "pets"
    __table_args__ = {"comment": "宠物信息表"}

    name: Mapped[str] = mapped_column(String(50), comment="宠物名字", nullable=False)
    species: Mapped[str | None] = mapped_column(String(50), comment="物种，如猫/狗/兔")
    breed: Mapped[str | None] = mapped_column(String(50), comment="品种")
    age: Mapped[int] = mapped_column(Integer, comment="年龄（月）", default=0)
    gender: Mapped[str | None] = mapped_column(String(10), comment="性别：公/母")
    color: Mapped[str | None] = mapped_column(String(30), comment="毛色")
    health: Mapped[str | None] = mapped_column(String(50), comment="健康状况")
    description: Mapped[str | None] = mapped_column(String(500), comment="简介")
    img: Mapped[str | None] = mapped_column(String(200), comment="封面图")
    status: Mapped[int] = mapped_column(default=1, comment="状态：0-已领养，1-待领养")
