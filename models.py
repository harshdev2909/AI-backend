from pydantic import BaseModel
from typing import List, Optional

class UserProfile(BaseModel):
    name: str
    email: str
    education_level: str
    specialization: str
    preferred_difficulty: str = "Beginner"
    learning_style: str = "Video-based"
    budget: float = 0.0
    quiz_score: Optional[int] = None
    generated_embedding: Optional[List[float]] = None
    language: str = "english"
