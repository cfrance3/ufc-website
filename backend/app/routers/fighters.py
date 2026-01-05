from fastapi import APIRouter
from backend.app.crud.fighters import get_all_fighters

router = APIRouter(prefix="/fighters", tags=["fighters"])

@router.get("/")
def list_fighters():
    return get_all_fighters()