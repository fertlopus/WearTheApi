from fastapi import APIRouter
from app.api.v1 import endpoints

router = APIRouter()
router.include_router(endpoints.router, tags=["recommendations"])
