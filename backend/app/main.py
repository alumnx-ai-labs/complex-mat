from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.azure_devops import router as azure_devops_router
from app.api.comments import router as comments_router
from app.api.meetings import router as meetings_router
from app.api.tasks import router as tasks_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers

settings = get_settings()

app = FastAPI(title="Meeting Action Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(meetings_router)
app.include_router(tasks_router)
app.include_router(users_router)
app.include_router(comments_router)
app.include_router(azure_devops_router)
