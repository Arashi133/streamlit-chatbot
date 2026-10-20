import streamlit as st
from config import supabase

def current_user_key() -> str:
    """Normalized name used to separate each user's conversations in Supabase."""
    return " ".join(st.session_state.user_name.split()).casefold()


def save_message(role: str, content: str, **extra):
    """Insert one message row into Supabase, tagged with the current user."""
    row = {
        "conversation_id": st.session_state.conversation_id,
        "user_key": current_user_key(),
        "role": role,
        "content": content,
        "model": None,
        "completion_id": None,
        "reasoning": None,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    row.update(extra)
    supabase.table("conversation_messages").insert(row).execute()


def load_conversation_messages(conversation_id: str):
    """Fetch messages for a specific conversation and user."""
    try:
        msg_res = (
            supabase.table("conversation_messages")
            .select("role, content, reasoning, score")
            .eq("conversation_id", conversation_id)
            .eq("user_key", current_user_key())
            .order("created_at", desc=False)
            .order("id", desc=False)
            .execute()
        )
        return msg_res.data or []
    except Exception as e:
        print(f"Load error: {e}")
        return []


def fetch_user_conversations():
    """Fetch all unique conversations and their titles for the sidebar history."""
    try:
        response = (
            supabase.table("conversation_messages")
            .select("conversation_id, role, content, created_at")
            .eq("user_key", current_user_key())
            .order("created_at", desc=True)
            .execute()
        )

        conversations = {}
        for row in response.data or []:
            cid = row["conversation_id"]
            conversations.setdefault(cid, None)
            if row["role"] == "user":
                text = row["content"]
                conversations[cid] = text[:25] + "..." if len(text) > 25 else text
        return conversations
    except Exception as e:
        print(f"History error: {e}")
        return {}