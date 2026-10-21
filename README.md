# Modular Gemini & Supabase Streamlit Chatbot

A Streamlit chatbot application powered by **Google Gemini** models and **Supabase** for message persistence, chat history management, and automated LLM-as-a-judge scoring.

---

## Features

* **Modular Architecture**: Cleanly separated concerns into configuration, database operations, agent logic, and the Streamlit UI.
* **Persistent Chat History**: Automatically saves conversations to Supabase, isolating chats per user using a normalized identifier.
* **Smart Agent Persona**: Uses Gemini system instructions to ensure the bot asks clarifying questions when prompts are vague, avoiding unnecessary interrogation.
* **Thinking Process Support**: Captures and renders internal reasoning/thought blocks using Streamlit expanders.
* **Session & Name Management**: Seamlessly remembers user identity across page refreshes via URL parameters.
* **LLM-as-a-judge scoring**: every reply is scored 0-10 with a short explanation, using DeepEval with Gemini as the judge.
* **Thought summaries**: Gemini's reasoning summary is shown in a "Thought Process" expander.
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
```

## Prerequisites

- **Python 3.10+** installed on your system.
- A **Supabase** project account.
- A **Google Gemini API Key** from [Google AI Studio](https://aistudio.google.com/).
- (Optional) A virtual environment for Python.

---
## Configure Supabase Database

In the Supabase project, create a table named `conversation_messages` with the following columns:

* `id` (Primary Key, e.g., bigint or uuid)
* `conversation_id` (Text / UUID)
* `user_key` (Text)
* `role` (Text)
* `content` (Text)
* `model` (Text, nullable)
* `completion_id` (Text, nullable)
* `reasoning` (Text, nullable)
* `prompt_tokens` (Integer, default 0)
* `completion_tokens` (Integer, default 0)
* `total_tokens` (Integer, default 0)
* `score` (Integer, nullable)
* `created_at` (Timestamp with time zone, default now())

---

## Set Up Environment Variables

Create a file named `.env` in the root directory of your project and populate it with your credentials:

```env
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_SECRET_KEY=your_supabase_secret_or_service_role_key_here
GEMINI_API_KEY=your_google_gemini_api_key_here

GEMINI_CHAT_MODEL=google_gemini_model_here
GEMINI_JUDGE_MODEL=google_gemini_model_here
```

---
## Run it locally 
```bash
pip install -r requirements.txt
streamlit run Chatbot.py

