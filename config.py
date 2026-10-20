import os
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai

load_dotenv()

# Clients
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SECRET_KEY"))
gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Models
CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL")
JUDGE_MODEL = os.getenv("GEMINI_JUDGE_MODEL")