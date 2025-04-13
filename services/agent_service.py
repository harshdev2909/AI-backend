from config import groq_client
import logging
import json

logging.basicConfig(level=logging.INFO)

def run_agents(specialization, quiz_score, required_level, language, embeddings):
    """AI Agent refines recommendations based on user's level, learning style, and budget."""
    logging.info(f"🤖 Running AI Agents for {specialization} (Level: {required_level})")

    prompt = f"""
    Act as an AI education expert. Recommend exactly 5 online courses for a student who wants to specialize in {specialization} in {language} language.
    - The student has a quiz score of {quiz_score}/10.
    - The required difficulty level is {required_level}.
    - The user's learning performance (embedding): {embeddings}.
    - Courses should include Udemy, Coursera, and YouTube.
    - Ensure each course has a valid link.
    - **Return the response as a strict JSON array**, without any extra text or explanations.

    Example format:
    [
        {{"title": "Course 1", "platform": "Udemy", "link": "https://udemy.com/..."}},
        {{"title": "Course 2", "platform": "Coursera", "link": "https://coursera.org/..."}}
    ]
    """

    try:
        ai_response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )

        response_text = ai_response.choices[0].message.content.strip()
        logging.info(f"🔍 AI Response: {response_text}")

        # Attempt to parse the response as JSON
        recommendations = json.loads(response_text)

        if isinstance(recommendations, list):
            return recommendations
        else:
            logging.error("❌ AI Agent Error: Response is not a valid JSON list.")
            return []

    except json.JSONDecodeError as e:
        logging.error(f"❌ JSON Parsing Error: {e}")
        return []
    except Exception as e:
        logging.error(f"❌ AI Agent Error: {e}")
        return []
