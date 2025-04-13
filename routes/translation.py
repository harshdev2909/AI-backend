from fastapi import APIRouter
from services.translation_service import advanced_translate

router = APIRouter()

@router.post("/translate/")
def translate_text(text: str, target_language: str):
    translated_text = advanced_translate(text, target_language)
    return {"translated_text": translated_text}
