from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services import dashboard

router = APIRouter(prefix="/dashboard", tags=["首页统计"])


@router.get("/stats")
def get_dashboard_stats(
    # 只要求登录，不要求管理员：
    # 总览页对所有登录用户可见，且 AI 助手的 get_system_stats 工具也面向普通用户，
    # 这里若限制为管理员会出现「页面能进、数据报无权限」的不一致。
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = dashboard.get_dashboard_stats(db)
    return Response.success(data=data)
