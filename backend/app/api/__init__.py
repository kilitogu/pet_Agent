from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.user import router as user_router
from app.api.file import router as file_router
from app.api.pet import router as pet_router
from app.api.dashboard import router as dashboard_router
from app.api.category import router as pet_category_router
from app.api.ai import router as ai_router

api = APIRouter(prefix="/api")

api.include_router(auth_router)
api.include_router(user_router)
api.include_router(file_router)
api.include_router(pet_router)
api.include_router(dashboard_router)
api.include_router(pet_category_router)
api.include_router(ai_router)
