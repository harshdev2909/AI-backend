from fastapi import APIRouter
from services.course_service import fetch_courses

router = APIRouter()

@router.get("/fetch_courses/")
def get_courses(topic: str):
    return fetch_courses(topic)
