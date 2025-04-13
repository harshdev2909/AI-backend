import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
from groq import Groq
from deep_translator import GoogleTranslator

# Set your Groq API Key (Ensure this is set in environment variables)
client = Groq(api_key="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")

# List of Indian regional languages
LANGUAGES = {
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "pa": "Punjabi",
    "gu": "Gujarati",
    "ur": "Urdu"
}

def get_video_id(youtube_url):
    """
    Extracts video ID from a YouTube URL.
    """
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", youtube_url)
    return match.group(1) if match else None

def fetch_transcript(video_id):
    """
    Fetches the transcript of a YouTube video.
    """
    try:
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([entry["text"] for entry in transcript_data])
        return transcript_text
    except Exception as e:
        return f"Error fetching transcript: {e}"

def summarize_transcript(transcript_text):
    """
    Summarizes the transcript using Groq's Llama 3.3-70B.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": f"Summarize the following transcript in detail:\n\n{transcript_text}"}
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error generating summary: {e}"

def translate_summary(summary, language_code):
    """
    Translates the summary into a selected regional language using Deep Translator.
    """
    try:
        translated_text = GoogleTranslator(source="auto", target=language_code).translate(summary)
        return translated_text
    except Exception as e:
        return f"Error translating summary: {e}"

def main():
    youtube_url = input("Enter YouTube URL: ").strip()
    video_id = get_video_id(youtube_url)

    if not video_id:
        print("Invalid YouTube URL. Please enter a valid link.")
        return

    print("\nFetching transcript...")
    transcript = fetch_transcript(video_id)

    if transcript.startswith("Error"):
        print(transcript)
        return

    print("\nGenerating summary...")
    summary = summarize_transcript(transcript)
    
    print("\nDetailed Summary (English):\n")
    print(summary)

    # Ask user if they want translation
    choice = input("\nDo you want the summary in a regional language? (yes/no): ").strip().lower()
    
    if choice == "yes":
        print("\nSelect a regional language for translation:")
        for code, lang in LANGUAGES.items():
            print(f"{code}: {lang}")

        language_code = input("\nEnter the language code: ").strip()

        if language_code in LANGUAGES:
            print(f"\nTranslating summary to {LANGUAGES[language_code]}...")
            translated_summary = translate_summary(summary, language_code)
            print(f"\nTranslated Summary in {LANGUAGES[language_code]}:\n")
            print(translated_summary)
        else:
            print("\nInvalid language code. Showing summary in English only.")
    else:
        print("\nSummary provided in English only. Exiting.")

if __name__ == "__main__":
    main()
