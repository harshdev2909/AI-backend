from config import groq_client

def generate_quiz(user):
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Generate a skill assessment quiz for a student with {user['education_level']} education level specializing in {user['specialization']}."
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def recommend_courses_based_on_quiz(user, quiz_score):
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Based on a skill level of {quiz_score}/100, suggest 5 best courses for a {user['education_level']} student specializing in {user['specialization']}."
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content
