"""Streamlit UI pieces and session-state handling."""
import uuid

import streamlit as st

from . import config
from .database import list_conversations, load_messages, normalize_name, save_message
from .llm import generate_greeting


def current_user_key() -> str:
    return normalize_name(st.session_state.user_name)


def new_conversation() -> None:
    st.session_state.conversation_id = str(uuid.uuid4())
    st.session_state.loaded_cid = None


def init_session() -> None:
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
    if "loaded_cid" not in st.session_state:
        st.session_state.loaded_cid = None
    if "user_name" not in st.session_state:
        # restore from the URL (?name=...) so a browser refresh doesn't ask again
        st.session_state.user_name = st.query_params.get("name", "").strip()


def require_user_name() -> None:
    """Show the name form and stop the script until a name is given."""
    if st.session_state.user_name:
        return
    st.title("Chatbot")
    with st.form("name_form"):
        name_input = st.text_input("Before we start, what should I call you?")
        submitted = st.form_submit_button("Start chatting")
    if submitted:
        if name_input.strip():
            st.session_state.user_name = name_input.strip()
            st.query_params["name"] = st.session_state.user_name
            new_conversation()  # never reuse another user's chat
            st.rerun()
        else:
            st.warning("Please enter a name.")
    st.stop()


def load_active_conversation() -> None:
    """When the active conversation changes, load it, or create an AI-written greeting."""
    if st.session_state.conversation_id == st.session_state.loaded_cid:
        return

    cid, user_key = st.session_state.conversation_id, current_user_key()
    messages = []
    try:
        messages = load_messages(cid, user_key)
    except Exception as e:
        print(f"Load error: {e}")

    if not messages:
        with st.spinner("Starting a new chat..."):
            greeting = generate_greeting(st.session_state.user_name)
        messages = [{"role": "assistant", "content": greeting,
                     "reasoning": None, "score": None, "score_reason": None}]
        try:
            save_message(cid, user_key, "assistant", greeting, model=config.CHAT_MODEL)
        except Exception as e:
            print(f"Greeting save error: {e}")

    st.session_state.messages = messages
    st.session_state.loaded_cid = cid


def render_sidebar() -> None:
    with st.sidebar:
        st.title("My Conversations")
        st.caption(f"Chatting as **{st.session_state.user_name}**")

        if st.button("✏️ Change name", use_container_width=True):
            st.session_state.user_name = ""
            new_conversation()
            if "name" in st.query_params:
                del st.query_params["name"]
            st.rerun()

        if st.button("➕ New Chat", use_container_width=True):
            new_conversation()
            st.rerun()

        st.divider()
        st.subheader("Chat History")
        try:
            for cid, title in list_conversations(current_user_key()):
                is_active = cid == st.session_state.conversation_id
                if st.button(
                    title,
                    key=f"hist_btn_{cid}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.conversation_id = cid  # the loader handles the rest
                    st.rerun()
        except Exception as e:
            print(f"History error: {e}")
            st.sidebar.error("Could not load chat history.")


def render_messages() -> None:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("reasoning"):
                with st.expander("Thought Process"):
                    st.write(msg["reasoning"])
            st.write(msg["content"])
            if msg["role"] == "assistant" and msg.get("score") is not None:
                st.caption(f"Judge score: {msg['score']}/10")
                if msg.get("score_reason"):
                    st.caption(f"↳ {msg['score_reason']}")
