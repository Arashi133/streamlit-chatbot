import uuid
import streamlit as st
from google.genai import types

from config import CHAT_MODEL, gemini
from database import (
    save_message,
    load_conversation_messages,
    fetch_user_conversations,
)
from agent import (
    build_agent_prompt,
    generate_greeting,
    to_gemini_contents,
    score_chatbot_response,
)

# ---------------------------------------------------------------------------
# Session state & Authentication setup
# ---------------------------------------------------------------------------
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

if "loaded_cid" not in st.session_state:
    st.session_state.loaded_cid = None

if "user_name" not in st.session_state:
    st.session_state.user_name = st.query_params.get("name", "").strip()

# Ask for the name first if missing
if not st.session_state.user_name:
    st.title("Chatbot")
    with st.form("name_form"):
        name_input = st.text_input("Before we start, what should I call you?")
        submitted = st.form_submit_button("Start chatting")
    if submitted:
        if name_input.strip():
            st.session_state.user_name = name_input.strip()
            st.query_params["name"] = st.session_state.user_name
            st.session_state.conversation_id = str(uuid.uuid4())
            st.session_state.loaded_cid = None
            st.rerun()
        else:
            st.warning("Please enter a name.")
    st.stop()

# Auto-loader for messages
if st.session_state.conversation_id != st.session_state.loaded_cid:
    messages = load_conversation_messages(st.session_state.conversation_id)

    if not messages:
        with st.spinner("Starting a new chat..."):
            greeting = generate_greeting(st.session_state.user_name)
        messages = [{"role": "assistant", "content": greeting, "reasoning": None, "score": None}]
        try:
            save_message("assistant", greeting, model=CHAT_MODEL)
        except Exception as e:
            print(f"Greeting save error: {e}")

    st.session_state.messages = messages
    st.session_state.loaded_cid = st.session_state.conversation_id

# ---------------------------------------------------------------------------
# Sidebar UI
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("My Conversations")
    st.caption(f"Chatting as **{st.session_state.user_name}**")
    
    if st.button("✏️ Change name", use_container_width=True):
        st.session_state.user_name = ""
        st.session_state.conversation_id = str(uuid.uuid4())
        st.session_state.loaded_cid = None
        if "name" in st.query_params:
            del st.query_params["name"]
        st.rerun()

    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.conversation_id = str(uuid.uuid4())
        st.rerun()

    st.divider()
    st.subheader("Chat History")
    
    conversations = fetch_user_conversations()
    for cid, title in conversations.items():
        if title is None:
            continue
        is_active = cid == st.session_state.conversation_id
        if st.button(
            title,
            key=f"hist_btn_{cid}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            st.session_state.conversation_id = cid
            st.rerun()

# ---------------------------------------------------------------------------
# Main Chat UI
# ---------------------------------------------------------------------------
st.title("Chatbot")
st.caption("A Streamlit chatbot")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("reasoning"):
            with st.expander("Thought Process"):
                st.write(msg["reasoning"])
        st.write(msg["content"])
        if msg["role"] == "assistant" and msg.get("score") is not None:
            st.caption(f"Judge score: {msg['score']}/10")

# ---------------------------------------------------------------------------
# User Input Handling
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    try:
        save_message("user", prompt)

        with st.chat_message("assistant"):
            with st.spinner("Typing..."):
                response = gemini.models.generate_content(
                    model=CHAT_MODEL,
                    contents=to_gemini_contents(st.session_state.messages),
                    config=types.GenerateContentConfig(
                        system_instruction=build_agent_prompt(st.session_state.user_name),
                        thinking_config=types.ThinkingConfig(include_thoughts=True),
                    ),
                )

                assistant_content, reasoning_content = "", ""
                if response.candidates and response.candidates[0].content:
                    for part in response.candidates[0].content.parts or []:
                        if not part.text:
                            continue
                        if part.thought:
                            reasoning_content += part.text
                        else:
                            assistant_content += part.text

                if not assistant_content:
                    raise ValueError("Empty response (possibly blocked by safety filters).")

                response_score = score_chatbot_response(prompt, assistant_content)

        usage = response.usage_metadata
        reasoning_content = reasoning_content or None

        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_content,
            "reasoning": reasoning_content,
            "score": response_score,
        })

        save_message(
            "assistant",
            assistant_content,
            model=response.model_version or CHAT_MODEL,
            completion_id=response.response_id,
            reasoning=reasoning_content,
            prompt_tokens=(usage.prompt_token_count or 0) if usage else 0,
            completion_tokens=(usage.candidates_token_count or 0) if usage else 0,
            total_tokens=(usage.total_token_count or 0) if usage else 0,
            score=response_score,
        )

        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")