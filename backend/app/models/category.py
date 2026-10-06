from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer

from app.database import Base


class PetCategory(Base):
    __tablename__ = "pet_categories"
    __table_args__ = {"comment": "宠物分类表"}

    name: Mapped[str] = mapped_column(String(50), comment="分类名称", nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), comment="分类描述")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序，越小越靠前")
    status: Mapped[int] = mapped_column(
        Integer, default=1, comment="状态：0-禁用，1-启用"
    )
