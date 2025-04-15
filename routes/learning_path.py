from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from config import groq_client
from utils.email_service import send_email
import json
import logging
import re

router = APIRouter()
logging.basicConfig(level=logging.INFO)

# ✅ Request Model
class LearningPathRequest(BaseModel):
    user_id: Optional[str] = None  # Made user_id optional
    goal: str
    send_email: bool = False
    user_email: Optional[EmailStr] = None  # Made user_email optional
    email_content: Optional[str] = None  # Added field for manual email content

# ✅ Response Model
class LearningPathResponse(BaseModel):
    goal: str
    required_skills: List[str]
    learning_path: List[str]
    email_status: str

def extract_json_from_text(response_content: str):
    """✅ Extracts valid JSON from AI response, removing extra AI-generated text."""
    try:
        parsed_data = json.loads(response_content.strip())
        return parsed_data
    except json.JSONDecodeError:
        pass  # ✅ Continue to regex extraction if direct parsing fails

    json_matches = re.findall(r"```json\n(.*?)\n```", response_content, re.DOTALL)

    if json_matches:
        try:
            extracted_json = json.loads(json_matches[0])
            return extracted_json
        except json.JSONDecodeError as e:
            logging.error(f"❌ Failed to parse extracted JSON: {e}")
            raise HTTPException(status_code=500, detail="AI returned malformed JSON.")

    try:
        json_start = response_content.find("[")
        json_end = response_content.rfind("]")
        if json_start != -1 and json_end != -1:
            extracted_json = json.loads(response_content[json_start : json_end + 1])
            return extracted_json
    except json.JSONDecodeError as e:
        logging.error(f"❌ No valid JSON found in AI response: {response_content}")
        raise HTTPException(status_code=500, detail=f"AI response was not valid JSON. Error: {e}")

    logging.error(f"❌ No valid JSON found. Raw response: {response_content}")
    raise HTTPException(status_code=500, detail="AI response did not contain valid JSON.")

def parse_json_response(response_content: str, label: str):
    """✅ Parses AI responses and logs errors if JSON parsing fails."""
    try:
        extracted_json = extract_json_from_text(response_content)
        logging.info(f"✅ Parsed {label}: {extracted_json}")
        return extracted_json
    except json.JSONDecodeError as e:
        logging.error(f"❌ Failed to parse {label}. Raw response: {response_content} Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI response for {label} was not valid JSON.")

@router.post("/generate_learning_path/", response_model=LearningPathResponse)
def generate_learning_path(request: LearningPathRequest):
    """Generates a structured learning path based on a user's goal."""

    # ✅ 1. Identify Required Skills
    logging.info(f"🔍 Identifying skills for goal: {request.goal}...")

    skills_prompt = f"""
    List essential skills needed to achieve this goal: {request.goal}.
    Strict JSON format: ["Skill 1", "Skill 2", "Skill 3"]
    """

    skills_response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": skills_prompt}],
        model="llama-3.3-70b-versatile",
    )
    required_skills = parse_json_response(skills_response.choices[0].message.content, "Required Skills")

    # ✅ 3. Recommend Learning Path
    logging.info(f"📚 Structuring learning path for {request.goal}...")

    learning_path_prompt = f"""
    Suggest a structured learning path for achieving {request.goal} using: {', '.join(required_skills)}.
    Strict JSON format: ["Step 1", "Step 2", "Step 3"]
    """

    learning_path_response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": learning_path_prompt}],
        model="llama-3.3-70b-versatile",
    )
    learning_path = parse_json_response(learning_path_response.choices[0].message.content, "Learning Path")

    # ✅ 4. Email Learning Path (if requested)
    email_status = "Email not requested."
    if request.send_email and request.user_email:
        logging.info(f"📩 Sending learning path to {request.user_email}...")
        
        # ✅ Create email content with learning path details in HTML format
        if request.email_content:
            email_content = request.email_content  # Use provided email content if available
        else:
            email_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Learning Path</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f4;
                        margin: 0;
                        padding: 20px;
                    }}
                    .container {{
                        background-color: #ffffff;
                        border-radius: 8px;
                        padding: 20px;
                        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    }}
                    h1 {{
                        color: #333;
                    }}
                    h2 {{
                        color: #555;
                    }}
                    p {{
                        line-height: 1.6;
                    }}
                    .skills, .learning-path {{
                        margin: 20px 0;
                        padding: 10px;
                        background-color: #e9ecef;
                        border-radius: 5px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Your Learning Path</h1>
                    <h2>Goal: {request.goal}</h2>
                    
                    <div class="skills">
                        <h3>Required Skills:</h3>
                        <p>{', '.join(required_skills)}</p>
                    </div>
                    
                    <div class="learning-path">
                        <h3>Learning Path:</h3>
                        <ol>
                            {''.join(f'<li>{step}</li>' for step in learning_path)}
                        </ol>
                    </div>
                </div>
            </body>
            </html>
            """

        email_sent = send_email(request.user_email, f"Learning Path for {request.goal}", email_content)
        email_status = "✅ Email sent!" if email_sent else "❌ Email failed."

    return {
        "goal": request.goal,
        "required_skills": required_skills,
        "learning_path": learning_path,
        "email_status": email_status
    }
