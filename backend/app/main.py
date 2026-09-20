from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth import router as auth_router
from app.routes.access_requests import router as access_requests_router
from app.routes.users import router as users_router
from app.routes.resources import router as resources_router
from app.core.config import settings

app = FastAPI(title="GRC Access Governance System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(access_requests_router)
app.include_router(users_router)
app.include_router(resources_router)