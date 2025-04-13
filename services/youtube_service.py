from googleapiclient.discovery import build
import os

# 🔹 Replace with your YouTube API key
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "AIzaSyBhz43LzgW_tqRhSurArDC0AEXq31pKZSw")

def fetch_youtube_courses(query: str, max_results: int = 5):
    """Fetch courses from YouTube based on a search query."""
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    search_response = youtube.search().list(
        q=query, part="snippet", maxResults=max_results, type="video"
    ).execute()

    courses = []
    for item in search_response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        description = item["snippet"]["description"]
        thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
        link = f"https://www.youtube.com/watch?v={video_id}"

        courses.append({
            "title": title,
            "description": description,
            "thumbnail": thumbnail,
            "link": link
        })

    return courses
