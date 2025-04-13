from fastapi import APIRouter
from config import groq_client
from database import db
from bson import ObjectId
import logging

router = APIRouter()
users_collection = db["users"]
user_quizzes = {}

# Enable Logging
logging.basicConfig(level=logging.INFO)

@router.post("/start_quiz/")
def start_quiz(user_id: str):
    """Start a new quiz and get the first question."""
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return {"error": "User not found"}

    # AI Generates Quiz in a Proper Format
    quiz_response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": f"Generate a 10-question multiple-choice quiz on {user['specialization']}. Format: \nQuestion: <text>\nA) <option 1>\nB) <option 2>\nC) <option 3>\nD) <option 4>\nCorrect Answer: <A/B/C/D>"}],
        model="llama-3.3-70b-versatile",
    )

    quiz_text = quiz_response.choices[0].message.content.strip().split("\n\n")

    # Extract Questions & Answers
    questions = []
    correct_answers = []
    for q in quiz_text:
        if "Correct Answer:" in q:
            question_part, correct_part = q.rsplit("\nCorrect Answer:", 1)
            questions.append(question_part.strip())
            correct_answers.append(correct_part.strip())

    user_quizzes[user_id] = {
        "questions": questions,
        "correct_answers": correct_answers,
        "current_question": 0,
        "score": 0,
        "total_questions": len(questions)
    }

    logging.info(f"Quiz started for {user_id}: {len(questions)} questions generated.")

    return {
        "question": user_quizzes[user_id]["questions"][0],
        "question_number": 1
    }

@router.post("/answer_question/")
def answer_question(user_id: str, answer: str):
    """Process user's answer and return the next question."""
    if user_id not in user_quizzes:
        return {"error": "Quiz not started. Call /start_quiz/ first."}

    quiz = user_quizzes[user_id]
    current_question = quiz["current_question"]

    # ✅ Compare user answer with correct answer directly (No AI Validation Needed)
    correct_answer = quiz["correct_answers"][current_question]
    logging.info(f"Q{current_question + 1}: User answered {answer}, Correct answer: {correct_answer}")

    if answer.strip().upper() == correct_answer.upper():
        quiz["score"] += 1  # ✅ Increment score only if correct

    # Move to Next Question
    quiz["current_question"] += 1

    if quiz["current_question"] >= quiz["total_questions"]:
        final_score = quiz["score"]
        users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"quiz_score": final_score}})
        del user_quizzes[user_id]  # ✅ Cleanup
        logging.info(f"Quiz completed for {user_id}: Final Score = {final_score}/10")

        return {"message": "Quiz completed!", "final_score": final_score}

    return {
        "question": quiz["questions"][quiz["current_question"]],
        "question_number": quiz["current_question"] + 1
    }
