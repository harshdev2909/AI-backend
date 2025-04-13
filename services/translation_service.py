import requests
from deep_translator import GoogleTranslator
from sentence_transformers import SentenceTransformer, util
from config import groq_client

# Load Hugging Face Transformer for Embeddings
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Generate contextual embeddings
def get_embedding(text):
    return model.encode(text, convert_to_tensor=True)

# Step 1: Context-based Translation using Groq AI
def translate_with_groq(text, target_language):
    response = groq_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Translate this into {target_language} with accurate context: {text}"
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    return response.choices[0].message.content

# Step 2: Improve Translation Accuracy with Deep Translator
def refine_translation(text, target_language):
    return GoogleTranslator(source="auto", target=target_language).translate(text)

# Step 3: Final Context Matching with Embeddings
def ensure_contextual_translation(original, translated, target_language):
    original_emb = get_embedding(original)
    translated_emb = get_embedding(translated)

    similarity = util.pytorch_cos_sim(original_emb, translated_emb).item()
    if similarity < 0.85:  # If similarity is too low, refine further
        return translate_with_groq(original, target_language)
    return translated

# Full Translation Pipeline
def advanced_translate(text, target_language):
    step1 = translate_with_groq(text, target_language)
    step2 = refine_translation(step1, target_language)
    final_translation = ensure_contextual_translation(text, step2, target_language)
    return final_translation
