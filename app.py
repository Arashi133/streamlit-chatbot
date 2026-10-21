import streamlit as st
import database, evaluation, llm, ui

ui.init_session()
ui.require_user_name()          # shows the name form and stops until a name is entered
ui.load_active_conversation()   # loads history, or writes a fresh greeting
ui.render_sidebar()

st.title("Chatbot")
st.caption("A Streamlit chatbot")
ui.render_messages()


def handle_prompt(prompt: str) -> None:
    cid = st.session_state.conversation_id
    user_key = ui.current_user_key()

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    try:
        database.save_message(cid, user_key, "user", prompt)

        with st.chat_message("assistant"):
            with st.spinner("Typing..."):
                reply = llm.generate_reply(st.session_state.messages, st.session_state.user_name)
                score, score_reason = evaluation.score_chatbot_response(prompt, reply.content)

        st.session_state.messages.append({
            "role": "assistant",
            "content": reply.content,
            "reasoning": reply.reasoning,
            "score": score,
            "score_reason": score_reason,
        })
        database.save_message(
            cid, user_key, "assistant", reply.content,
            model=reply.model,
            completion_id=reply.completion_id,
            reasoning=reply.reasoning,
            prompt_tokens=reply.prompt_tokens,
            completion_tokens=reply.completion_tokens,
            total_tokens=reply.total_tokens,
            score=score,
            score_reason=score_reason,
        )
        st.rerun()  # refresh the sidebar titles and render the message from state

    except Exception as e:
        st.error(f"Error: {e}")


if prompt := st.chat_input("Type your message..."):
    handle_prompt(prompt)
