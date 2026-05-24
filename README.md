# Skysecure Intelligent MSP - Zoho AI Assistant

Demo Video: https://drive.google.com/file/d/1sxPoV5_uqiTiHBpDirQItUV7st1U7ghq/view?usp=sharing](https://drive.google.com/file/d/1BifJSCO6RseEQ6gG47RMJv58OH-Q-RQZ/view?usp=sharing

A production-grade, multi-agent conversational interface built to securely interact with the Zoho Projects API. Engineered with a focus on state predictability, Human-in-the-Loop (HIL) operational security, and seamless UI telemetry, specifically tailored for managed services environments.

## 🏗️ Architecture Overview

This application utilizes a stateful multi-agent graph architecture to strictly separate read and write operations, ensuring enterprise-grade security and zero unintended infrastructure mutations.

* **Backend Framework:** FastAPI providing asynchronous endpoint handling, CORS middleware, and static UI serving.
* **Orchestration:** LangGraph implementing a deterministic `IntentSupervisor` that routes inputs to either a `QueryAgent` (pure functions) or an `ActionAgent` (mutations).
* **Intelligence:** Powered by a General AI API via `langchain-mistralai` for intent classification and semantic response generation.
* **State & Memory:** Utilizes LangGraph's `MemorySaver` for short-term thread context (e.g., remembering active project IDs) and a serverless SQLite database for long-term OAuth token persistence.
* **Frontend Interface:** A zero-build React application featuring dynamic Markdown rendering, real-time LangGraph execution tracing, native Web Speech APIs, and PDF/Email report generation.

---

## ⚙️ Setup Steps

**1. Clone the repository:**
`bash
git clone https://github.com/NEEL-DHAYGUDE/Neel_skysecure_zoholangchainchatbot.git
cd Neel_skysecure_zoholangchainchatbot
`

**2. Initialize a virtual environment:**
`bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate 
`

**3. Install backend dependencies:**
`bash
pip install fastapi uvicorn sqlalchemy httpx langchain-mistralai langgraph pydantic python-dotenv
`

**4. Boot the application:**
`bash
uvicorn main:app --reload --port 8000
`

**5. Access the UI:**
Navigate to `http://localhost:8000/` in your browser.

---

## 🔐 OAuth Configuration Guide

To connect this application to live Zoho infrastructure, you must provision an API client:

1. Navigate to the [Zoho API Console](https://api-console.zoho.in/).
2. Click **Add Client** and select **Server-based Applications**.
3. Provide a name and set the **Authorized Redirect URI** to your local or ngrok address: 
   `http://localhost:8000/auth/callback`
4. Copy your generated **Client ID** and **Client Secret**.
5. Create a `.env` file in the root directory of this project (matching the provided `.env.example` file) and populate it with your credentials:

`env
ZOHO_CLIENT_ID=your_zoho_client_id_here
ZOHO_CLIENT_SECRET=your_zoho_client_secret_here
ZOHO_REDIRECT_URI=http://localhost:8000/auth/callback
MISTRAL_API_KEY=your_mistral_key_here

# Required for automated report dispatch:
SMTP_EMAIL=your.email@gmail.com
SMTP_PASSWORD=your_16_digit_google_app_password
`

---

## ⚠️ Known Limitations

* **Strict Message Sequencing:** To comply with the LLM API's strict role-alternating requirements (`HumanMessage` -> `AIMessage` -> `ToolMessage`), certain direct tool invocations during specific demo flows utilize injected structural fallbacks to prevent `400 Bad Request` HTTP exceptions.
* **Web Speech API Support:** The voice-to-text dashboard feature relies on the native browser `webkitSpeechRecognition` API, which is highly optimized for Chromium-based browsers (Chrome/Edge) but may lack support or require manual permission toggling in Firefox/Safari.
* **Graph State Persistence:** The system is currently utilizing an in-memory checkpointer (`MemorySaver`) for rapid iteration and stable UI reloading. In a production cloud deployment, this layer would be swapped to `AsyncPostgresSaver` to maintain thread states across horizontal worker reboots.
