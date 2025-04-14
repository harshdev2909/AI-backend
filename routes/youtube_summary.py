from fastapi import APIRouter, HTTPException
from config import groq_client
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from deep_translator import GoogleTranslator
from utils.email_service import send_email
import re
import logging
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supported Languages
LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr)": "Marathi",
    "pa": "Punjabi",
    "gu": "Gujarati",
    "ur": "Urdu",
}

# Pydantic model for request validation
class YouTubeSummaryRequest(BaseModel):
    youtube_url: HttpUrl
    language_code: str = "en"
    send_email: bool = False
    user_email: Optional[EmailStr] = None

def get_video_id(youtube_url: str) -> Optional[str]:
    """Extracts video ID from a YouTube URL."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, str(youtube_url))
        if match:
            return match.group(1)
    return None

def fetch_transcript(video_id: str, retries: int = 3, delay: float = 5.0) -> Optional[str]:
    """Fetches transcript from a YouTube video with retry logic and proxy support."""
    # Configure proxies from environment variables
    proxies = {
        "http": os.getenv("PROXY_HTTP"),
        "https": os.getenv("PROXY_HTTPS"),
    } if os.getenv("PROXY_HTTP") and os.getenv("PROXY_HTTPS") else None

    for attempt in range(retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{retries} to fetch transcript for video ID: {video_id}")
            transcript_data = YouTubeTranscriptApi.get_transcript(
                video_id,
                proxies=proxies,
                languages=['en', 'hi', 'bn', 'ta', 'te', 'kn', 'ml', 'mr', 'pa', 'gu', 'ur']
            )
            return " ".join(entry["text"] for entry in transcript_data)
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            logger.error(f"❌ Transcript unavailable: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Transcript fetch attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            continue
    logger.error(f"❌ Failed to fetch transcript after {retries} attempts for video ID: {video_id}")
    return None

def summarize_transcript(transcript_text: str) -> Optional[str]:
    """Summarizes the transcript using Groq Llama 3.3-70B."""
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Summarize the following transcript in a concise and detailed manner, "
                        "capturing key points and main ideas in 3-5 sentences:\n\n"
                        f"{transcript_text[:4000]}"
                    ),
                }
            ],
            model="llama-3.3-70b-versatile",
            max_tokens=500,
            temperature=0.7,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"❌ Summarization Error: {e}")
        return None

def translate_summary(summary: str, language_code: str) -> Optional[str]:
    """Translates the summary into the selected language."""
    if language_code == "en":
        return summary
    try:
        translator = GoogleTranslator(source="auto", target=language_code)
        return translator.translate(summary)
    except Exception as e:
        logger.error(f"❌ Translation Error to {LANGUAGES.get(language_code, language_code)}: {e}")
        return None

def send_summary_email(to_email: str, video_url: str, summary: str, language: str) -> bool:
    """Sends an email with the YouTube summary."""
    subject = "📺 Apurv.AI - Your YouTube Video Summary"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9;">
        <h2 style="color: #007bff; text-align: center;">Your YouTube Video Summary 🎥</h2>
        <p style="text-align: center;"><b>Video URL:</b> <a href="{video_url}" style="color: #007bff;">Watch Video</a></p>
        <p><b>Summary ({language}):</b></p>
        <p style="border-left: 4px solid #007bff; padding-left: 10px;">{summary}</p>
        <hr style="border: 0; height: 1px; background: #ddd;">
        <p style="text-align: center;">Happy Learning! 🚀</p>
        <p style="text-align: center;"><b>Best Regards,<br>Apurv Inc.</b></p>
    </div>
    """
    try:
        return send_email(to_email, subject, html_content)
    except Exception as e:
        logger.error(f"❌ Email Sending Error: {e}")
        return False

@router.post("/youtube_summary/", response_model=dict)
async def youtube_summary(request: YouTubeSummaryRequest):
    """Extracts, summarizes, translates YouTube video transcripts & optionally emails the summary."""
    # Validate email if send_email is True
    if request.send_email and not request.user_email:
        raise HTTPException(status_code=400, detail="Email is required when 'send_email' is true.")

    # Validate language code
    if request.language_code not in LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language code. Supported codes: {list(LANGUAGES.keys())}")

    # Extract video ID
    video_id = get_video_id(request.youtube_url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL. Please provide a valid link.")

    # Fetch transcript
    logger.info(f"📹 Fetching transcript for {request.youtube_url} (video ID: {video_id})...")
    transcript = fetch_transcript(video_id)
    if not transcript:
        raise HTTPException(status_code=422, detail="Transcript not available for this video. Subtitles may be disabled or the video is inaccessible.")

    # Generate summary
    logger.info("📝 Generating summary...")
    summary = summarize_transcript(transcript)
    if not summary:
        raise HTTPException(status_code=500, detail="Failed to generate summary due to an internal error.")

    # Translate summary if needed
    logger.info(f"🌍 Translating summary to {LANGUAGES[request.language_code]}...")
    translated_summary = translate_summary(summary, request.language_code)
    if not translated_summary:
        raise HTTPException(status_code=500, detail=f"Failed to translate summary to {LANGUAGES[request.language_code]}.")

    # Prepare response
    response_data = {
        "video_url": str(request.youtube_url),
        "summary": translated_summary,
        "language": LANGUAGES[request.language_code],
    }

    # Send email if requested
    if request.send_email and request.user_email:
        logger.info(f"📩 Sending summary to {request.user_email}...")
        email_sent = send_summary_email(
            request.user_email,
            str(request.youtube_url),
            translated_summary,
            LANGUAGES[request.language_code]
        )
        response_data["email_status"] = (
            "Summary emailed successfully!" if email_sent else "Failed to send email."
        )

    return response_data