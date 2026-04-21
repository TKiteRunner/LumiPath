"""API v1 路由聚合。"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.interviews import router as interviews_router
from app.api.v1.okr import router as okr_router
from app.api.v1.notes import router as notes_router
from app.api.v1.agent import router as agent_router, ws_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(interviews_router)
api_router.include_router(okr_router)
api_router.include_router(notes_router)
api_router.include_router(agent_router)
api_router.include_router(ws_router)
