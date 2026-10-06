from aiogram import Router
from handlers.admin import router as admin_router
from handlers.user import router as user_router

main_router = Router()
main_router.include_router(admin_router)
main_router.include_router(user_router)

__all__ = ["main_router", "admin_router", "user_router"]
