import re
from google.genai import types
from config import gemini, CHAT_MODEL, JUDGE_MODEL

AGENT_SYSTEM_PROMPT = """You are a friendly, attentive assistant whose job is to genuinely
understand what the user needs before you answer.

How to behave:
- If the request is clear and you have enough detail, just answer it directly and well.
- If the request is vague or missing details that would change your answer (goal, context,
  audience, constraints, preferences, level of experience, deadline, budget, etc.), ask for them
  first. Ask at most 2-3 short, specific questions, in a single message, and explain briefly
  why you are asking when it is not obvious.
- Never interrogate. Do not ask for things you can reasonably assume or that do not matter.
  Do not ask questions the user has already answered earlier in the conversation.
- Once the user has given you enough, stop asking and deliver the answer. If they say they
  don't know or don't care about a detail, pick sensible defaults and say what you assumed.
- Be honest: if you are unsure about a fact, say so instead of guessing.
- Sound like a warm, natural person, not a form. Keep replies concise, and reply in the same
  language the user writes in."""

GREETING_SYSTEM_PROMPT = """You are a friendly assistant opening a brand-new chat.
You will be told the user's name. Write a short, warm, natural opening message (1-2 sentences)
that greets them by name and invites them to share what they are working on or what they need
help with. Use the name exactly once, and only the name as given (do not add a surname or a
title). Sound like a real person, not a corporate bot. Do not list your features, do not use
more than one emoji, and do not repeat the same stock phrasing every time. Output only the
message itself."""


def fallback_greeting(name: str) -> str:
    return f"Hey {name}! What's on your mind today?"


def build_agent_prompt(name: str) -> str:
    return (
        AGENT_SYSTEM_PROMPT
        + f"\n\nThe user's name is {name}. Use it occasionally and naturally "
        "(for example when greeting or wrapping up), not in every message."
    )


def to_gemini_contents(messages):
    """Convert [{'role','content'}, ...] to Gemini Content objects."""
    contents = []
    for m in messages:
        if not contents and m["role"] == "assistant":
            continue  # Skip initial greeting
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))
    return contents


def generate_greeting(name: str) -> str:
    try:
        response = gemini.models.generate_content(
            model=CHAT_MODEL,
            contents=f"The user's name is {name}. Start the conversation.",
            config=types.GenerateContentConfig(
                system_instruction=GREETING_SYSTEM_PROMPT,
                temperature=1.0,
            ),
        )
        text = (response.text or "").strip()
        return text or fallback_greeting(name)
    except Exception as e:
        print(f"Greeting error: {e}")
        return fallback_greeting(name)


def score_chatbot_response(user_query: str, chatbot_response: str):
    eval_prompt = f"""You are a strict AI evaluator. Grade the chatbot response below on
truth, accuracy and helpfulness. If the chatbot is asking the user a reasonable clarifying
question because the request was vague, judge how appropriate and useful that question is.
Return ONLY a single integer from 0 to 10. No extra text, explanation, or punctuation.

[User Query]: {user_query}
[Chatbot Response]: {chatbot_response}

Score:"""

    try:
        response = gemini.models.generate_content(
            model=JUDGE_MODEL,
            contents=eval_prompt,
            config=types.GenerateContentConfig(temperature=0.1),
        )
        score_text = (response.text or "").strip()
        match = re.search(r"\b(10|[0-9])\b", score_text)
        return int(match.group(1)) if match else None
    except Exception as e:
        print(f"Scoring error: {e}")
        return None