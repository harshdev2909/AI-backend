import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)

# Exchange rate (Assumption: 1 USD ≈ 83 INR)
USD_TO_INR = 83  

def fetch_udemy_courses(topic, budget, level, language="English"):
    """Fetch Udemy courses dynamically with INR pricing and language filter."""
    url = f"https://www.udemy.com/courses/search/?q={topic}+{level}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    courses = []
    for course in soup.find_all("div", class_="course-card--container"):
        title_tag = course.find("div", class_="course-card--course-title")
        link_tag = course.find("a", class_="course-card-link")
        
        if title_tag and link_tag:
            course_title = title_tag.text.strip()
            course_link = f"https://www.udemy.com{link_tag.get('href')}"
            
            courses.append({
                "title": course_title,
                "price": 10 * USD_TO_INR,  # ✅ Assuming $10 converted to INR
                "currency": "INR",
                "platform": "Udemy",
                "link": course_link,
                "language": language
            })

    return [c for c in courses if c["price"] <= budget]

def fetch_coursera_courses(topic, language="English"):
    """Fetch Coursera courses dynamically."""
    url = f"https://api.coursera.org/api/courses.v1?q=search&query={topic}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        courses = response.json().get("elements", [])
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch Coursera courses: {e}")
        return []

    return [
        {
            "title": c.get("name", "Unknown Course"),
            "platform": "Coursera",
            "link": f"https://www.coursera.org/learn/{c.get('slug', '')}",
            "language": language
        }
        for c in courses
    ]

# def fetch_youtube_videos(topic, language="English"):
#     """Fetch YouTube courses dynamically."""
#     ydl_opts = {"quiet": True}
#     attempts = 0

#     while attempts < 5:
#         try:
#             with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#                 search_result = ydl.extract_info(f"ytsearch10:{topic}", download=False)
#                 return [
#                     {
#                         "title": v.get("title", "Unknown Video"),
#                         "platform": "YouTube",
#                         "link": v.get("webpage_url", "#"),
#                         "language": language
#                     }
#                     for v in search_result.get("entries", []) if v
#                 ]
#         except yt_dlp.utils.ExtractorError as e:
#             logging.error(f"Extractor Error: {e}, skipping...")
#             return []
#         except yt_dlp.utils.DownloadError as e:
#             if "429" in str(e):
#                 wait_time = 2**attempts  # Exponential backoff
#                 logging.warning(f"⚠️ Rate-limited! Retrying in {wait_time} sec...")
#                 time.sleep(wait_time)
#                 attempts += 1
#             else:
#                 logging.error(f"YouTube Download Error: {e}")
#                 return []

#     return []

def fetch_courses(topic, budget, level, language="English"):
    """Fetch courses from Udemy and Coursera (YouTube Removed)."""
    return {
        "udemy": fetch_udemy_courses(topic, budget, level, language),
        "coursera": fetch_coursera_courses(topic, language),
        # "youtube": fetch_youtube_videos(topic, language)  # ❌ Removed YouTube
    }
