import faiss
import numpy as np
from database import db

courses_collection = db["courses"]
DIMENSION = 512
index = faiss.IndexFlatL2(DIMENSION)

def load_embeddings():
    courses = list(courses_collection.find({}, {"_id": 1, "embedding": 1, "difficulty_level": 1}))
    valid_courses = [c for c in courses if "embedding" in c]
    if valid_courses:
        embeddings = np.array([c["embedding"] for c in valid_courses], dtype=np.float32)
        index.add(embeddings)

def match_courses(user_embedding, difficulty_level):
    if index.ntotal == 0:
        return []

    query_vector = np.array(user_embedding, dtype=np.float32).reshape(1, -1)
    _, indices = index.search(query_vector, 5)
    matched_courses = [courses_collection.find_one({"_id": idx}) for idx in indices[0]]
    
    return sorted(matched_courses, key=lambda x: x.get("difficulty_level", "Beginner") == difficulty_level, reverse=True)[:3]
