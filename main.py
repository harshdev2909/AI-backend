from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import user, quiz, recommendations, youtube_summary, learning_path, daily_content
from database import db
import logging

# ✅ Initialize FastAPI app
app = FastAPI(title="AI Course Recommendation API", version="1.0")

# ✅ Enable CORS (Required for frontend integrations)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production to restrict allowed domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register API routes
app.include_router(user.router, prefix="/user", tags=["User Management"])
app.include_router(quiz.router, prefix="/quiz", tags=["Quiz System"])
app.include_router(daily_content.router, prefix="/daily-content", tags=["Daily"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Course Recommendations"])
app.include_router(youtube_summary.router, prefix="/youtube", tags=["YouTube Summarization"])  # ✅ Added YouTube Summary API
app.include_router(learning_path.router, prefix="/learning", tags=["Learning Path Generator"])

# ✅ Root Endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the AI-Powered Course Recommendation System 🚀"}

# ✅ Verify MongoDB connection on startup
@app.on_event("startup")
def startup_event():
    try:
        db.list_collection_names()  # Test MongoDB connection
        logging.info("✅ Connected to MongoDB Successfully!")
    except Exception as e:
        logging.error(f"❌ MongoDB Connection Failed: {e}")



# ✅ Run Uvicorn (if running standalone)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
