from fastapi import APIRouter, Query, HTTPException
from config import groq_client
from youtube_transcript_api import YouTubeTranscriptApi
from deep_translator import GoogleTranslator
from utils.email_service import send_email
import re
import logging
from pydantic import BaseModel

router = APIRouter()
logging.basicConfig(level=logging.INFO)

# Supported Languages
LANGUAGES = {
    "hi": "Hindi", "bn": "Bengali", "ta": "Tamil", "te": "Telugu", 
    "kn": "Kannada", "ml": "Malayalam", "mr": "Marathi", "pa": "Punjabi", 
    "gu": "Gujarati", "ur": "Urdu"
}

# Define a Pydantic model for the request body
class YouTubeSummaryRequest(BaseModel):
    youtube_url: str
    language_code: str = "en"
    send_email: bool = False
    user_email: str = None

def get_video_id(youtube_url: str):
    """Extracts video ID from a YouTube URL."""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", youtube_url)
    return match.group(1) if match else None

def fetch_transcript(video_id: str):
    """Fetches transcript from a YouTube video."""
    try:
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript_data])
    except Exception as e:
        logging.error(f"❌ Transcript Error: {e}")
        return None

def summarize_transcript(transcript_text: str):
    """Summarizes the transcript using Groq Llama 3.3-70B."""
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": f"Summarize the following transcript in detail:\n\n{transcript_text}"}],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logging.error(f"❌ Summarization Error: {e}")
        return None

def translate_summary(summary: str, language_code: str):
    """Translates the summary into a selected regional language."""
    try:
        return GoogleTranslator(source="auto", target=language_code).translate(summary)
    except Exception as e:
        logging.error(f"❌ Translation Error: {e}")
        return None

def send_summary_email(to_email, video_url, summary, language):
    """Send an email with the YouTube summary."""
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

    return send_email(to_email, subject, html_content)

@router.post("/youtube_summary/")
def youtube_summary(request: YouTubeSummaryRequest):
    """Extracts, summarizes, translates YouTube video transcripts & optionally emails the summary."""
    
    if request.send_email and not request.user_email:
        return {"error": "Email is required if 'send_email' is true."}

    video_id = get_video_id(request.youtube_url)
    if not video_id:
        return {"error": "Invalid YouTube URL. Please enter a valid link."}

    logging.info(f"📹 Fetching transcript for {request.youtube_url}...")
    transcript = fetch_transcript(video_id)
    if not transcript:
        return {"error": "Transcript not available for this video."}

    logging.info("📝 Generating summary...")
    summary = summarize_transcript(transcript)
    if not summary:
        return {"error": "Failed to generate summary."}

    if request.language_code != "en" and request.language_code in LANGUAGES:
        logging.info(f"🌍 Translating summary to {LANGUAGES[request.language_code]}...")
        translated_summary = translate_summary(summary, request.language_code)
        if not translated_summary:
            return {"error": f"Failed to translate to {LANGUAGES[request.language_code]}"}
    else:
        translated_summary = summary

    response_data = {
        "video_url": request.youtube_url,
        "summary": translated_summary,
        "language": LANGUAGES.get(request.language_code, "English")
    }

    if request.send_email and request.user_email:
        logging.info(f"📩 Sending summary to {request.user_email}...")
        email_sent = send_summary_email(request.user_email, request.youtube_url, translated_summary, LANGUAGES.get(request.language_code, "English"))
        response_data["email_status"] = "Summary emailed successfully!" if email_sent else "Failed to send email."

    return response_data
