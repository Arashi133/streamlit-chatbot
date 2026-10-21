import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_secret(name: str, default=None):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass  # no secrets.toml available (for example when running only with .env)
    return os.getenv(name, default)


SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_SECRET_KEY = get_secret("SUPABASE_SECRET_KEY")
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")

CHAT_MODEL = get_secret("GEMINI_CHAT_MODEL")    # the chatbot
JUDGE_MODEL = get_secret("GEMINI_JUDGE_MODEL")   # the evaluator

MESSAGES_TABLE = "conversation_messages"
