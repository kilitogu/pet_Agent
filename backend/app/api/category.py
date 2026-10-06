from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin
from app.models.user import User
from app.schemas.category import (
    PetCategoryCreateRequest,
    PetCategoryUpdateRequest,
)
from app.services import category

router = APIRouter(prefix="/pet-category", tags=["宠物分类管理"])


@router.get("/list")
def get_category_list(
    page: int = 1,
    page_size: int = 10,
    keywords: str | None = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = category.get_category_page_list(db, page, page_size, keywords)
    return Response.success(data=res)


@router.post("")
def create_category(
    data: PetCategoryCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = category.create_category(db, data)
    return Response.success(data=res)


@router.put("/{category_id}")
def update_category(
    category_id: int,
    data: PetCategoryUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = category.update_category(db, category_id, data)
    return Response.success(data=res)


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    category.delete_category(db, category_id)
    return Response.success(message="删除成功")
