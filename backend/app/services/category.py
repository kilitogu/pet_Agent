from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.models.category import PetCategory
from app.schemas.category import (
    PetCategoryCreateRequest,
    PetCategoryResponse,
    PetCategoryUpdateRequest,
)


def get_category_page_list(
    db: Session, page: int, page_size: int, keywords: str | None = None
):
    query = db.query(PetCategory)
    if keywords:
        query = query.filter(
            or_(
                PetCategory.name.ilike(f"%{keywords}%"),
                PetCategory.description.ilike(f"%{keywords}%"),
            )
        )
    total = query.count()
    items = (
        query.order_by(PetCategory.sort.asc(), PetCategory.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PageResponse(
        list=[PetCategoryResponse.model_validate(item) for item in items],
        total=total,
    )


def create_category(db: Session, data: PetCategoryCreateRequest):
    exists = db.query(PetCategory).filter(PetCategory.name == data.name).first()
    if exists:
        raise BusinessException(message="分类名称已存在")

    category = PetCategory(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return PetCategoryResponse.model_validate(category)


def update_category(db: Session, category_id: int, data: PetCategoryUpdateRequest):
    category = db.query(PetCategory).filter(PetCategory.id == category_id).first()
    if not category:
        raise BusinessException(message="分类不存在")

    payload = data.model_dump(exclude_none=True)
    if "name" in payload:
        exists = (
            db.query(PetCategory)
            .filter(PetCategory.name == payload["name"], PetCategory.id != category_id)
            .first()
        )
        if exists:
            raise BusinessException(message="分类名称已存在")

    for field, value in payload.items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return PetCategoryResponse.model_validate(category)


def delete_category(db: Session, category_id: int):
    category = db.query(PetCategory).filter(PetCategory.id == category_id).first()
    if not category:
        raise BusinessException(message="分类不存在")
    db.delete(category)
    db.commit()
