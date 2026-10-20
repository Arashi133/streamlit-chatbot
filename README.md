# Modular Gemini & Supabase Streamlit Chatbot

A Streamlit chatbot application powered by **Google Gemini** models and **Supabase** for message persistence, chat history management, and automated LLM-as-a-judge scoring.

---

## Features

* **Modular Architecture**: Cleanly separated concerns into configuration, database operations, agent logic, and the Streamlit UI.
* **Persistent Chat History**: Automatically saves conversations to Supabase, isolating chats per user using a normalized identifier.
* **Smart Agent Persona**: Uses Gemini system instructions to ensure the bot asks clarifying questions when prompts are vague, avoiding unnecessary interrogation.
* **Thinking Process Support**: Captures and renders internal reasoning/thought blocks using Streamlit expanders.
* **Automated AI Evaluation**: Grades each chatbot turn on truthfulness, accuracy, and helpfulness using a judge model.
* **Session & Name Management**: Seamlessly remembers user identity across page refreshes via URL parameters (`?name=...`).

---

## Project Structure

```text
main/
│
├── .env                    # Environment variables & API keys
├── requirements.txt        # Python packages
├── app.py                  # Main entry point (Streamlit UI, flow, and event handlers)
├── config.py               # Client initializations (Supabase & Gemini) and model configs
├── database.py             # Supabase data access layer (saving and loading messages)
└── agent.py                # Gemini integration (prompts, greetings, content conversion, evaluation)
