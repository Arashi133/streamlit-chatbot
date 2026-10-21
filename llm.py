"""Gemini client: retries, conversation conversion, greeting and chat replies."""
import asyncio
import time
from dataclasses import dataclass
from typing import Optional

from google import genai
from google.genai import errors, types

from . import config
from .prompts import GREETING_SYSTEM_PROMPT, build_agent_prompt, fallback_greeting

gemini = genai.Client(api_key=config.GEMINI_API_KEY)

# Gemini sometimes returns transient server errors; these are worth retrying.
RETRYABLE_CODES = {429, 500, 502, 503, 504}


def gemini_generate(retries: int = 3, **kwargs):
    """generate_content with exponential backoff on transient errors."""
    for attempt in range(retries):
        try:
            return gemini.models.generate_content(**kwargs)
        except errors.APIError as e:
            if e.code in RETRYABLE_CODES and attempt < retries - 1:
                wait = 2 ** attempt  # 1s, 2s, ...
                print(f"Gemini {e.code} ({e.status}), retrying in {wait}s")
                time.sleep(wait)
                continue
            raise


async def a_gemini_generate(retries: int = 3, **kwargs):
    """Async version of gemini_generate (used by the DeepEval judge)."""
    for attempt in range(retries):
        try:
            return await gemini.aio.models.generate_content(**kwargs)
        except errors.APIError as e:
            if e.code in RETRYABLE_CODES and attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            raise


def to_gemini_contents(messages):
    """Convert [{'role','content'}, ...] to Gemini Content objects."""
    contents = []
    for m in messages:
        if not contents and m["role"] == "assistant":
            continue  # Gemini history should start with a user turn; skip the greeting
        role = "user" if m["role"] == "user" else "model"
        if contents and contents[-1].role == role:
            # e.g. an earlier message whose reply failed: merge instead of two turns in a row
            contents[-1].parts.append(types.Part(text=m["content"]))
        else:
            contents.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))
    return contents


def generate_greeting(name: str) -> str:
    """Ask Gemini for a fresh, natural opening line that greets the user by name."""
    try:
        response = gemini_generate(
            model=config.CHAT_MODEL,
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


@dataclass
class Reply:
    content: str
    reasoning: Optional[str]
    model: str
    completion_id: Optional[str]
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


def _split_thoughts(response):
    """Separate thought summaries from the actual answer text."""
    content, reasoning = "", ""
    if response.candidates and response.candidates[0].content:
        for part in response.candidates[0].content.parts or []:
            if not part.text:
                continue
            if part.thought:
                reasoning += part.text
            else:
                content += part.text
    return content, reasoning


def generate_reply(messages, user_name: str) -> Reply:
    """Answer the conversation so far. Raises on failure or an empty/blocked response."""
    contents = to_gemini_contents(messages)
    system_prompt = build_agent_prompt(user_name)

    try:
        response = gemini_generate(
            model=config.CHAT_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                thinking_config=types.ThinkingConfig(include_thoughts=True),
            ),
        )
    except errors.APIError as e:
        # Still failing after retries (or the model rejects thinking): try once without it
        print(f"Chat call failed with thinking ({e.code}); retrying without it")
        response = gemini_generate(
            model=config.CHAT_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )

    content, reasoning = _split_thoughts(response)
    if not content:
        raise ValueError("Empty response (possibly blocked by safety filters).")

    usage = response.usage_metadata
    return Reply(
        content=content,
        reasoning=reasoning or None,
        model=response.model_version or config.CHAT_MODEL,
        completion_id=response.response_id,
        prompt_tokens=(usage.prompt_token_count or 0) if usage else 0,
        completion_tokens=(usage.candidates_token_count or 0) if usage else 0,
        total_tokens=(usage.total_token_count or 0) if usage else 0,
    )
