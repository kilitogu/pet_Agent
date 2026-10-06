from fastapi import APIRouter, Depends
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.user import UserUpdateRequest, PasswordUpdateRequest, UserCreateRequest
from app.common.response import Response
from app.services import user
from app.database import get_db
from sqlalchemy.orm import Session
from app.dependencies.auth import get_current_admin

router = APIRouter(prefix="/user", tags=["用户信息接口"])

@router.get("/info")
def get_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return Response.success(data=user.get_user_info(current_user))


@router.put("/update")
def update_user_info(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新当前用户信息"""
    res = user.update_user_info(db, current_user, data)
    return Response.success(data=res)


@router.put("/password")
def update_password(
    data: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改当前用户密码"""
    user.update_password(db, current_user, data)
    return Response.success(message="密码修改成功")

@router.get("/list")
def get_user_list(
    page: int = 1,
    page_size: int = 10,
    keywords: str | None = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user.get_user_page_list(db, page, page_size, keywords)
    return Response.success(data=res)


@router.post("")
def create_user(
    data: UserCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user.create_user(db, data)
    return Response.success(data=res)


@router.put("/{user_id}")
def create_user(
    user_id: int,
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user.update_user(db, user_id, data)
    return Response.success(data=res)


@router.delete("/{user_id}")
def create_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user.delete_user(db, user_id, current_user)
    return Response.success()
