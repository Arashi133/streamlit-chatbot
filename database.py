from supabase import Client, create_client

import config

supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_SECRET_KEY)
TABLE = config.MESSAGES_TABLE


def normalize_name(name: str) -> str:
    """'Anna', 'anna' and ' ANNA ' all map to the same key."""
    return " ".join(name.split()).casefold()


def save_message(conversation_id: str, user_key: str, role: str, content: str, **extra) -> None:
    row = {
        "conversation_id": conversation_id,
        "user_key": user_key,
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
    supabase.table(TABLE).insert(row).execute()


def load_messages(conversation_id: str, user_key: str) -> list:
    res = (
        supabase.table(TABLE)
        .select("role, content, reasoning, score, score_reason")
        .eq("conversation_id", conversation_id)
        .eq("user_key", user_key)
        .order("created_at", desc=False)
        .order("id", desc=False)
        .execute()
    )
    return res.data or []


def list_conversations(user_key: str) -> list:
    """Return [(conversation_id, title)], most recently active first.

    The title is the earliest USER message. Chats that only contain the greeting are skipped.
    """
    res = (
        supabase.table(TABLE)
        .select("conversation_id, role, content, created_at")
        .eq("user_key", user_key)
        .order("created_at", desc=True)
        .limit(1000)
        .execute()
    )
    titles = {}
    for row in res.data or []:
        cid = row["conversation_id"]
        titles.setdefault(cid, None)  # newest-first, so dict order = latest activity
        if row["role"] == "user":
            text = row["content"]  # walking back in time, so the earliest one wins
            titles[cid] = text[:25] + "..." if len(text) > 25 else text
    return [(cid, title) for cid, title in titles.items() if title is not None]
