from fastapi import APIRouter, HTTPException, Query
import requests
from bs4 import BeautifulSoup
import json
import logging
from config import groq_client
from utils.email_service import send_email
from database import db
from bson import ObjectId
from transformers import AutoTokenizer, AutoModel
from models import UserProfile

router = APIRouter()
users_collection = db["users"]

# ✅ Load MiniLM model once for embeddings
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

logging.basicConfig(level=logging.INFO)

# ✅ Fetch user from MongoDB
def get_user_from_db(user_id: str):
    logging.info(f"📢 Incoming request to fetch user: {user_id}")

    try:
        # ✅ Check if user ID is valid
        if not ObjectId.is_valid(user_id):
            logging.error(f"❌ Invalid User ID format: {user_id}")
            raise HTTPException(status_code=400, detail="Invalid User ID format.")

        user = users_collection.find_one({"_id": ObjectId(user_id)})

        if not user:
            logging.error(f"❌ User ID {user_id} not found in MongoDB.")
            raise HTTPException(status_code=404, detail="User not found in the database.")

        # ✅ Convert MongoDB ObjectId to string
        user["_id"] = str(user["_id"])

        logging.info(f"✅ User Found: {user['name']} | Specialization: {user.get('specialization', 'Unknown')}")
        return user

    except Exception as e:
        logging.error(f"❌ Unexpected Error in get_user_from_db: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

# ✅ Fetch news articles dynamically
def fetch_news_articles(query):
    logging.info(f"📰 Fetching news articles for topic: {query}")
    
    sources = {
        "Medium": f"https://medium.com/search?q={query}",
        "Google News": f"https://news.google.com/search?q={query}",
        "TechCrunch": f"https://techcrunch.com/search/{query}/",
    }

    articles = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for source, url in sources.items():
        logging.info(f"🌍 Fetching from {source} - URL: {url}")

        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logging.warning(f"⚠️ Failed to fetch articles from {source}, Status Code: {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            found_articles = soup.find_all("h3")[:3]

            for article in found_articles:
                link_tag = article.find("a", href=True)
                if link_tag:
                    articles.append({
                        "source": source,
                        "title": article.text.strip(),
                        "url": link_tag["href"].split("?")[0]
                    })

        except Exception as e:
            logging.error(f"❌ Error fetching from {source}: {e}")

    logging.info(f"✅ Found {len(articles)} articles")
    return articles[:5] if articles else None

# ✅ AI-generated article summary
def generate_ai_summary(article_title, article_url):
    logging.info(f"🤖 Generating AI summary for: {article_title} - {article_url}")

    summary_prompt = f"""
    Summarize this article in 3 sentences:
    Title: {article_title}
    Link: {article_url}
    """

    try:
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": summary_prompt}],
            model="llama-3.3-70b-versatile",
        )
        summary = json.loads(response.choices[0].message.content.strip())

        logging.info(f"✅ AI Summary Generated: {summary}")
        return summary

    except json.JSONDecodeError:
        logging.error(f"❌ AI Summary failed for {article_title}")
        return {"summary": "Could not generate summary.", "key_takeaway": "Read the full article for details."}

# ✅ AI-generated Problem of the Day
def generate_ai_problem(user):
    logging.info(f"🧩 Generating Problem of the Day for user: {user['name']}")

    problem_prompt = f"""
    Create a challenging problem in {user['specialization']}.
    Difficulty: {user.get('preferred_difficulty', 'Beginner')}.
    Quiz Score: {user.get('quiz_score', 'N/A')}.
    """

    try:
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": problem_prompt}],
            model="llama-3.3-70b-versatile",
        )
        problem = json.loads(response.choices[0].message.content.strip())

        logging.info(f"✅ Problem Generated: {problem}")
        return problem

    except json.JSONDecodeError:
        logging.error("❌ AI Problem generation failed")
        return {"problem": "An interesting problem to test your skills.", "hint": "Think logically!"}

# ✅ AI-Powered Daily Content API (Logs Everything)
@router.get("/daily-content/")
def get_daily_content(user_id: str):
    logging.info(f"📢 Received request for daily content for User ID: {user_id}")

    # ✅ Fetch user
    user = get_user_from_db(user_id)

    # ✅ Fetch articles
    articles = fetch_news_articles(user["specialization"])
    if not articles:
        logging.error("❌ No news articles found")
        raise HTTPException(status_code=404, detail="No articles found.")

    # ✅ Summarize articles
    summarized_articles = []
    for article in articles:
        summary = generate_ai_summary(article["title"], article["url"])
        summarized_articles.append({**article, **summary})

    # ✅ Generate problem of the day
    problem_of_the_day = generate_ai_problem(user)

    # ✅ Build final response
    daily_content = {
        "user": user["name"],
        "problem_of_the_day": problem_of_the_day,
        "news_articles": summarized_articles
    }

    logging.info(f"✅ Successfully generated daily content for {user['name']}")
    return daily_content
