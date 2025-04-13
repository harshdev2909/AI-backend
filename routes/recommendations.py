from fastapi import APIRouter, Query
from pydantic import BaseModel, EmailStr
from services.course_service import fetch_courses
from services.agent_service import run_agents
from utils.email_service import send_course_recommendation_email
import logging

router = APIRouter()

# Enable logging for debugging
logging.basicConfig(level=logging.INFO)

# Exchange rate (Assumption: 1 USD ≈ 83 INR)
USD_TO_INR = 83

# ✅ Request Body Model
class CourseRequest(BaseModel):
    user_email: EmailStr
    specialization: str
    language: str = "English"
    quiz_score: int = 5
    budget_usd: float = 50
    preferred_difficulty: str = "Beginner"
    send_email: bool = False
    generated_embedding: list[float] = []  # or any default/fake value
    limit: int = Query(5, ge=1, le=10)

# ✅ Response Models
class Course(BaseModel):
    title: str
    platform: str
    rating: float
    price: float
    currency: str = "INR"
    link: str

class RecommendationResponse(BaseModel):
    final_recommendations: list[Course]
    scraped_courses: dict

# ✅ API Endpoint
@router.post("/recommend_courses/", response_model=RecommendationResponse)
def recommend_courses(request: CourseRequest):
    """Recommend courses based on inputs without database usage."""

    budget_inr = request.budget_usd * USD_TO_INR

    logging.info(f"📌 Generating recommendations for {request.specialization} (Level: {request.preferred_difficulty}, Budget: ₹{budget_inr})")

    # Run AI Agents to generate internal recommendations
    agent_recommendations = run_agents(
        request.specialization,
        request.quiz_score,
        request.preferred_difficulty,
        request.language,
        request.generated_embedding
    )

    # Scrape from external platforms
    scraped_courses = fetch_courses(
        request.specialization,
        budget_inr,
        request.preferred_difficulty,
        request.language
    )

    # Combine results
    final_courses = (
        agent_recommendations[:request.limit] +
        scraped_courses["udemy"][:request.limit] +
        scraped_courses["coursera"][:request.limit]
    )

    # Ensure valid course objects
    validated_courses = []
    for course in final_courses:
        validated_courses.append(Course(
            title=course.get("title", "Unknown Course"),
            platform=course.get("platform", "Unknown"),
            rating=float(course.get("rating", 0.0)),
            price=float(course.get("price", 0.0)),
            link=course.get("link", "#")
        ))

    # Optional email
    if request.send_email:
        logging.info(f"📩 Sending course recommendations to {request.user_email}...")
        success = send_course_recommendation_email(request.user_email, validated_courses)
        if success:
            logging.info("✅ Email sent successfully!")
        else:
            logging.error("❌ Email sending failed!")

    return {
        "final_recommendations": validated_courses,
        "scraped_courses": scraped_courses
    }
