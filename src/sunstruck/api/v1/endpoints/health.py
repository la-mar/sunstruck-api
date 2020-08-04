from typing import Dict

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", response_model=Dict)
def health():
    return {"status": "ok"}
