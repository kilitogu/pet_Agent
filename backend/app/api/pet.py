from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin
from app.models.user import User
from app.schemas.pet import PetCreateRequest, PetUpdateRequest
from app.services import pet

router = APIRouter(prefix="/pet", tags=["宠物管理"])


@router.get("/list")
def get_pet_list(
    page: int = 1,
    page_size: int = 10,
    keywords: str | None = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = pet.get_pet_page_list(db, page, page_size, keywords)
    return Response.success(data=res)


@router.post("")
def create_pet(
    data: PetCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = pet.create_pet(db, data)
    return Response.success(data=res)


@router.put("/{pet_id}")
def update_pet(
    pet_id: int,
    data: PetUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = pet.update_pet(db, pet_id, data)
    return Response.success(data=res)


@router.delete("/{pet_id}")
def delete_pet(
    pet_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    pet.delete_pet(db, pet_id)
    return Response.success(message="删除成功")
