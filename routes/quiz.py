from fastapi import APIRouter, HTTPException
from config import groq_client
from database import db
from pydantic import BaseModel
from bson import ObjectId
import logging
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

router = APIRouter()
users_collection = db["users"]
user_quizzes = {}

# ✅ Use a smaller & faster model
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# ✅ Load the Hugging Face Model once during startup
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

# ✅ Enable Logging
logging.basicConfig(level=logging.INFO)

class AnswerRequest(BaseModel):
    user_id: str
    answer: str

class UserIDRequest(BaseModel):
    user_id: str

@router.post("/start_quiz/")
def start_quiz(request: UserIDRequest):
    """Start a new quiz and return the first question."""
    user = users_collection.find_one({"_id": ObjectId(request.user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    quiz_response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": f"Generate a 10-question multiple-choice quiz on prerequisites for {user['specialization']}. Format: \nQuestion: <text>\nA) <option 1>\nB) <option 2>\nC) <option 3>\nD) <option 4>\nCorrect Answer: <A/B/C/D>"}],
        model="llama-3.3-70b-versatile",
    )

    quiz_text = quiz_response.choices[0].message.content.strip().split("\n\n")
    questions, correct_answers = [], []

    for q in quiz_text:
        if "Correct Answer:" in q:
            question_part, correct_part = q.rsplit("\nCorrect Answer:", 1)
            questions.append(question_part.strip())
            correct_answers.append(correct_part.strip().upper())

    if not questions:
        raise HTTPException(status_code=500, detail="Quiz generation failed.")

    user_quizzes[request.user_id] = {
        "questions": questions,
        "correct_answers": correct_answers,
        "current_question": 0,
        "score": 0,
        "total_questions": len(questions),
    }

    return {
        "question": user_quizzes[request.user_id]["questions"][0],
        "question_number": 1,
    }

@router.post("/answer_question/")
def answer_question(request: AnswerRequest):
    """Process user's answer and return the next question or final score."""
    user_id = request.user_id
    answer = request.answer.strip().upper()  # ✅ Ensure uppercase for consistency

    if user_id not in user_quizzes:
        raise HTTPException(status_code=400, detail="Quiz not started. Call /quiz/start_quiz/ first.")

    quiz = user_quizzes[user_id]
    current_question = quiz["current_question"]

    if current_question >= quiz["total_questions"]:
        raise HTTPException(status_code=400, detail="Quiz already completed.")

    correct_answer = quiz["correct_answers"][current_question].strip().upper()

    logging.info(f"Q{current_question + 1}: User answered {answer}, Correct answer: {correct_answer}")

    # ✅ Check if the answer is correct
    if answer == correct_answer:
        quiz["score"] += 1

    quiz["current_question"] += 1

    # ✅ If quiz is completed, return final score
    if quiz["current_question"] >= quiz["total_questions"]:
        final_score = quiz["score"]
        total_questions = quiz["total_questions"]
        correct_percentage = round((final_score / total_questions) * 100, 2)

        # ✅ Store final score in MongoDB
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"quiz_score": final_score, "quiz_percentage": correct_percentage}}
        )

        logging.info(f"✅ Quiz Completed for {user_id}: Final Score = {final_score}/{total_questions} ({correct_percentage:.2f}%)")

        # ✅ Remove quiz session to prevent stale data
        del user_quizzes[user_id]

        return {
            "message": "Quiz completed!",
            "final_score": final_score,
            "total_questions": total_questions,
            "correct_percentage": correct_percentage
        }

    return {
        "question": quiz["questions"][quiz["current_question"]],
        "question_number": quiz["current_question"] + 1,
        "current_score": quiz["score"]
    }


def generate_hf_embedding(text):
    """Generate embeddings using the smaller MiniLM model."""
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().tolist()

def update_embeddings(user_id: str, quiz_score: int):
    """Generate or update embeddings using Hugging Face MiniLM model."""
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        logging.error(f"User {user_id} not found, skipping embedding update.")
        return

    specialization = user.get("specialization", "General Knowledge")
    current_embedding = user.get("generated_embedding")

    # ✅ Generate new embedding from MiniLM model
    new_embedding = generate_hf_embedding(f"Embedding for {specialization} with quiz score {quiz_score}/10.")

    if current_embedding:
        # ✅ Blend old and new embeddings for incremental learning
        updated_embedding = np.array(current_embedding) * 0.7 + np.array(new_embedding) * 0.3
    else:
        updated_embedding = new_embedding

    # ✅ Store updated embedding in the database
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"generated_embedding": updated_embedding.tolist()}}
    )

    logging.info(f"✅ Updated embeddings for {user_id} based on quiz performance.")
