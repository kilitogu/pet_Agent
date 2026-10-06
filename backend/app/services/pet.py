from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.models.pet import Pet
from app.schemas.pet import PetCreateRequest, PetResponse, PetUpdateRequest


def get_pet_page_list(
    db: Session, page: int, page_size: int, keywords: str | None = None
):
    query = db.query(Pet)
    if keywords:
        query = query.filter(
            or_(Pet.name.ilike(f"%{keywords}%"), Pet.species.ilike(f"%{keywords}%"))
        )
    total = query.count()
    items = (
        query.order_by(Pet.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PageResponse(
        list=[PetResponse.model_validate(item) for item in items],
        total=total,
    )


def create_pet(db: Session, data: PetCreateRequest):
    exists = db.query(Pet).filter(Pet.name == data.name).first()
    if exists:
        raise BusinessException(message="宠物名称已存在")

    pet = Pet(**data.model_dump())
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return PetResponse.model_validate(pet)


def update_pet(db: Session, pet_id: int, data: PetUpdateRequest):
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise BusinessException(message="宠物不存在")

    payload = data.model_dump(exclude_none=True)
    if "name" in payload:
        exists = (
            db.query(Pet).filter(Pet.name == payload["name"], Pet.id != pet_id).first()
        )
        if exists:
            raise BusinessException(message="宠物名称已存在")

    for field, value in payload.items():
        setattr(pet, field, value)
    db.commit()
    db.refresh(pet)
    return PetResponse.model_validate(pet)


def delete_pet(db: Session, pet_id: int):
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise BusinessException(message="宠物不存在")
    db.delete(pet)
    db.commit()
