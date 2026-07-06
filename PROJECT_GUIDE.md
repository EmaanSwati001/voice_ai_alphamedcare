# AlphaMed Voice AI — Project Description & Q&A Guide

---

## 🔗 How to Open & Run

1. **Double-click** `run_server.bat` in the project root, OR run manually:
   ```powershell
   cd c:\Users\ek139\OneDrive\Desktop\voice_ai_alphamedcare
   .venv\Scripts\activate
   pip install -r backend\requirements.txt
   uvicorn backend.app.main:app --reload
   ```

2. **Open in browser:** [http://127.0.0.1:8000](http://127.0.0.1:8000)

3. **GitHub Repo:** [https://github.com/EmaanSwati001/voice_ai_alphamedcare](https://github.com/EmaanSwati001/voice_ai_alphamedcare)

---

## 📋 Project Description

**AlphaMed Voice AI** is an AI-powered voice assistant for a medical billing clinic called "AlphaMed Clinic." It acts as a virtual receptionist that patients can talk to — by speaking into their microphone or typing — to handle administrative tasks related to their healthcare billing.

### What Problem Does It Solve?

Medical clinics receive hundreds of repetitive phone calls daily from patients asking the same questions:
- *"What's my outstanding balance?"*
- *"Why was my claim denied?"*
- *"When is my next appointment?"*

These calls take up valuable staff time and make patients wait on hold. **AlphaMed Voice AI automates this entire process** by providing an intelligent voice agent that can:

1. **Verify patient identity** (HIPAA-compliant) before revealing any protected health information
2. **Look up insurance claims** and explain their status (Paid, Pending, Denied) along with denial reasons
3. **Check outstanding billing balances** and co-pay invoices
4. **View and schedule doctor appointments**
5. **Explain medical billing codes** (CPT codes like 99213, 72148, etc.)
6. **Answer policy questions** like how to file an appeal or set up a payment plan
7. **Transfer to a human supervisor** if the patient requests one or has a complex issue

### Two Operating Modes

| Mode | How It Works | Cost |
|------|-------------|------|
| **🆓 Browser Mode** | Uses the browser's built-in Speech Recognition (STT) and Speech Synthesis (TTS) APIs. Intent matching is done locally via keyword rules in JavaScript. | Free — No API keys needed |
| **💎 Premium Mode** | Uses **ElevenLabs Conversational AI** with a **Gemini** LLM backend. ElevenLabs handles natural voice STT/TTS, and Gemini provides intelligent conversation and tool-calling. | Requires ElevenLabs API key |

### How It Works (Step-by-Step)

1. Patient clicks the glowing microphone button on the dashboard
2. They speak: *"Verify John Doe, date of birth May 15th 1985, policy POL12345"*
3. The system captures speech → converts to text → extracts patient details
4. It calls the FastAPI backend → queries the SQLite database → verifies the patient
5. The dashboard updates in real-time: verification badge turns green, patient profile loads, claims and appointments populate
6. The AI speaks back: *"Thank you John Doe, I have verified your profile. How can I assist you today?"*
7. The patient can then ask about claims, balances, appointments, etc. — all via voice

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | HTML, CSS (dark glassmorphic design), Vanilla JavaScript |
| **Backend** | Python, FastAPI, Uvicorn |
| **Database** | SQLite with SQLAlchemy ORM |
| **AI Voice (Premium)** | ElevenLabs Conversational AI SDK + Gemini LLM |
| **AI Voice (Free)** | Browser Web Speech API (webkitSpeechRecognition + speechSynthesis) |
| **Knowledge Base** | Markdown files with RAG (Retrieval-Augmented Generation) search |
| **Fonts** | Google Fonts (Outfit + Plus Jakarta Sans) |

### Key Features

- 🎙️ **Real-time voice interaction** — speak naturally, hear responses out loud
- 🔒 **HIPAA-compliant identity verification** — must verify before accessing patient data
- 📊 **Live dashboard** — patient profile, claims, invoices, and appointments update in real-time
- 🏥 **Medical billing intelligence** — CPT code lookups, claim denial explanations, payment plan info
- ⌨️ **Keyboard fallback** — type messages if microphone is unavailable
- 🔄 **Dual mode** — works without any API keys (browser mode) or with premium ElevenLabs voice
- 📡 **Error forwarding** — browser errors are logged to the server console for debugging
- 🌙 **Premium dark-mode UI** — glassmorphism, gradient effects, animated mic orb

---

## ❓ Questions & Answers

### General / Overview Questions

**Q1: What is AlphaMed Voice AI?**
> It's an AI-powered voice assistant for a medical billing clinic. Patients can call in through their browser and speak naturally to check their insurance claims, outstanding balances, appointments, and get answers to common billing questions — all without waiting on hold for a human representative.

**Q2: What problem does this project solve?**
> Medical clinics receive hundreds of repetitive phone calls daily. Patients call to ask about claim statuses, billing balances, and appointments. This wastes staff time and creates long hold times. Our voice AI automates these routine inquiries, freeing up staff for complex cases and giving patients instant answers 24/7.

**Q3: Who is the target user?**
> The primary users are patients of AlphaMed Clinic who need to check billing information. The secondary user is the clinic's administrative team, who benefit from reduced call volume. The dashboard also serves as a monitoring tool for supervisors to see live call transcripts.

**Q4: What are the two modes and why do you have both?**
> **Browser Mode** is a free fallback that works without any API keys — it uses the browser's built-in speech recognition and synthesis. It's great for demos and testing. **Premium Mode** uses ElevenLabs Conversational AI with Gemini LLM for natural-sounding voice, intelligent conversation, and tool-calling capabilities. Having both modes means the app always works, even without paid API keys.

---

### Technical / Architecture Questions

**Q5: What is your tech stack?**
> Frontend is vanilla HTML/CSS/JavaScript with a premium glassmorphic dark-mode design. Backend is Python with FastAPI serving REST endpoints. Database is SQLite managed through SQLAlchemy ORM. For premium voice, we use ElevenLabs Conversational AI SDK with Gemini as the underlying LLM. For free mode, we use the browser's Web Speech API.

**Q6: Why did you choose FastAPI over Flask or Django?**
> FastAPI is built on modern Python async capabilities, has automatic API documentation (Swagger UI), built-in Pydantic data validation, and is significantly faster than Flask. It's also lightweight compared to Django, which would be overkill for a REST API backend. Plus, FastAPI has native WebSocket support which we need for real-time voice communication.

**Q7: Why SQLite instead of PostgreSQL or MySQL?**
> SQLite is a file-based database that requires zero setup — no database server installation needed. For a demo/prototype with a small patient dataset, it's perfect. The entire database is a single 49KB file (`medical_billing.db`). In production, we would migrate to PostgreSQL, and since we use SQLAlchemy ORM, the migration would only require changing the connection string.

**Q8: How does the database schema work?**
> We have 4 tables: **Patients** (identity info, policy number), **Claims** (insurance claim records with status and denial reasons), **BillingInvoices** (outstanding co-pay balances), and **Appointments** (scheduled doctor visits). They're related through foreign keys — each patient has multiple claims, invoices, and appointments. The database auto-seeds with 2 test patients (John Doe and Jane Smith) on startup.

**Q9: What are your API endpoints?**
> We have 7 main endpoints:
> - `POST /api/verify-patient` — HIPAA identity verification
> - `GET /api/patients/{policy}/claims` — list all claims for a patient
> - `GET /api/claims/{claim_number}` — details of a specific claim
> - `GET /api/patients/{policy}/invoices` — outstanding balances
> - `GET /api/patients/{policy}/appointments` — scheduled appointments
> - `POST /api/appointments` — schedule a new appointment
> - `POST /elevenlabs/start` — get signed WebSocket URL for ElevenLabs

**Q10: How does the frontend communicate with the backend?**
> In browser mode, the frontend makes standard HTTP `fetch()` requests to the FastAPI REST endpoints. In premium mode, the frontend first calls `/elevenlabs/start` to get a signed WebSocket URL, then opens a direct WebSocket connection to ElevenLabs' servers. When ElevenLabs' Gemini agent needs database data, it triggers `clientTools` defined in the browser, which then make HTTP requests to our FastAPI backend.

---

### AI / Voice Questions

**Q11: How does the ElevenLabs integration work?**
> When the user starts a call in premium mode:
> 1. Frontend calls our backend's `/elevenlabs/start` endpoint
> 2. Backend uses the ElevenLabs Python SDK with our API key to request a secure signed WebSocket URL
> 3. Frontend receives this URL and opens a direct WebSocket connection to ElevenLabs
> 4. ElevenLabs handles speech-to-text, sends the text to Gemini LLM for processing, and streams natural-sounding voice back
> 5. When Gemini needs patient data, it calls our `clientTools` (defined in `app.js`), which query our local database via FastAPI

**Q12: What is the role of Gemini in this project?**
> Gemini is the Large Language Model (LLM) configured on the ElevenLabs Conversational AI platform. It acts as the "brain" of the voice agent — it understands patient requests in natural language, decides which tools to call (verify patient, look up claims, etc.), processes the database results, and generates conversational spoken responses. We chose Gemini when configuring the ElevenLabs agent.

**Q13: What are client tools and why are they important?**
> Client tools are JavaScript functions registered in the ElevenLabs SDK session (`clientTools` in `app.js`). When the AI agent (Gemini) decides it needs to verify a patient or look up a claim, it sends a tool-call request over the WebSocket. The browser intercepts this, runs the corresponding JavaScript function (which calls our FastAPI backend), and sends the database result back to the AI. This is crucial because it lets the AI agent interact with our local database in real-time.

**Q14: How does the Browser Mode (free) speech recognition work?**
> It uses the `webkitSpeechRecognition` Web API built into Chrome and Edge. When the user speaks, the browser converts speech to text for free (no API key needed). The text is then processed by a local keyword-based intent router in JavaScript that detects phrases like "verify", "balance", "claim", "CPT code", "human agent" and routes them to the appropriate API call. Response text is spoken back using the browser's `speechSynthesis` API.

**Q15: What is RAG and how do you use it?**
> RAG stands for Retrieval-Augmented Generation. Instead of relying solely on the LLM's training data, we provide it with our own knowledge documents (clinic FAQ, CPT code reference guide, billing policies). When a patient asks a policy question, the system searches these documents for the most relevant paragraphs and feeds them to the AI as context. We support both semantic search (using OpenAI embeddings with cosine similarity) and a keyword fallback when no API key is available.

---

### Security / Compliance Questions

**Q16: How do you handle HIPAA compliance?**
> We enforce identity verification before any protected health information (PHI) is revealed. The patient must provide their full name, date of birth, and policy number. These are verified against our database. The AI's system prompt explicitly instructs it to never reveal claim details, balances, or appointments until verification succeeds. This is a mandatory guardrail built into both the prompt and the API logic.

**Q17: How is the ElevenLabs API key secured?**
> The API key is stored in a `.env` file on the server, never exposed to the frontend. The frontend only receives a temporary signed URL (which expires after use) from our backend. The actual API key never leaves the server. The `.env` file is listed in `.gitignore` so it's never committed to version control.

**Q18: What happens when verification fails?**
> The API returns a `401 Unauthorized` HTTP response, and the AI politely tells the patient: "I was unable to verify your identity. Please state your full name, date of birth, and policy number clearly." The dashboard remains in the "Unverified" state and no patient data is displayed.

---

### Frontend / UI Questions

**Q19: Describe the UI design approach.**
> We use a premium dark-mode glassmorphic design with CSS backdrop-filter blur effects. The color palette uses deep navy backgrounds with cyan/blue accent gradients. The layout is a two-panel dashboard: left panel shows the patient database (verification status, claims, invoices, appointments) and right panel shows the live call console with transcription, audio wave visualization, and the glowing microphone button. We use Google Fonts (Outfit for headings, Plus Jakarta Sans for body text) for a modern look.

**Q20: How does the real-time dashboard update work?**
> When a patient is verified, JavaScript immediately calls the claims, appointments, and invoices API endpoints. The responses are dynamically rendered into the DOM — claim cards show status badges (green for Paid, red for Denied), the billing balance updates, and appointments populate with doctor names and dates. All of this happens without page reload using DOM manipulation.

**Q21: What is the audio wave visualization?**
> It's a CSS-only animated equalizer made of 8 span bars that animate with staggered delays using `@keyframes`. When the mic is active or the AI is speaking, the `.active` class is added and the bars bounce at different speeds, creating a realistic audio waveform effect. It provides visual feedback that the system is listening or speaking.

---

### Database / Data Questions

**Q22: What seed data do you have?**
> Two patients:
> - **John Doe** (Policy: POL12345) — has 2 claims (one Paid, one Denied for "Prior Authorization Required"), 1 unpaid invoice ($45.00), and an appointment with Dr. Sarah Johnson
> - **Jane Smith** (Policy: POL67890) — has 2 claims (one Paid, one Pending), 1 unpaid invoice ($30.00), and an appointment with Dr. Robert Lee

**Q23: What CPT codes does the system know about?**
> Six codes: 99212 (brief office visit), 99213 (standard office visit), 99214 (comprehensive visit), 36415 (blood draw), 72148 (MRI lumbar spine), and 94640 (inhalation/nebulizer treatment). These are stored in the knowledge base markdown files.

**Q24: How is the database seeded?**
> The `seed_database()` function in `crud.py` runs automatically on server startup. It first checks if any patients exist — if the database is already populated, it skips seeding. Otherwise, it creates 2 patients, 4 claims, 2 invoices, and 2 appointments using SQLAlchemy ORM objects and commits them in a single transaction.

---

### Demo / Testing Questions

**Q25: How can I test it without any API keys?**
> Start the server and open `http://127.0.0.1:8000`. Select "Free Browser Mode" and click the microphone. Say: *"Verify John Doe, May 15th 1985, policy POL12345"* — the system will verify the patient, load their profile, and you can then ask about claims, balances, or CPT codes. Everything works locally.

**Q26: What voice commands can I use for the demo?**
> - *"Verify John Doe, May 15th 1985, policy POL12345"* — verifies patient
> - *"What is my outstanding balance?"* — shows billing info
> - *"What is CPT code 72148?"* — explains the MRI code
> - *"Why was claim CLM10002 denied?"* — shows denial reason
> - *"What are my claims?"* — lists all claims
> - *"Transfer me to a human"* — simulates call transfer
> - *"When is my next appointment?"* — shows scheduled visits

**Q27: What test scripts are available?**
> Four test scripts in the `backend/` folder:
> - `test_db.py` — tests raw database CRUD operations
> - `test_api.py` — tests FastAPI endpoint responses
> - `test_rag.py` — tests knowledge base search functionality
> - `test_agent_cli.py` — runs an interactive terminal chat agent (mock demo or real OpenAI chat)

---

### Future Scope / Improvement Questions

**Q28: What would you improve for production?**
> - Switch SQLite to PostgreSQL for concurrent access
> - Add proper user authentication (JWT tokens)
> - Restrict CORS to specific domains
> - Add responsive CSS for mobile/tablet
> - Implement rate limiting on API endpoints
> - Add call recording and analytics
> - Deploy on cloud (AWS/GCP) with HTTPS

**Q29: Could this work for a real medical clinic?**
> Yes, with modifications. The core architecture (voice → AI → database → response) is production-ready. We'd need to integrate with real EHR/EMR systems (like Epic or Cerner) instead of SQLite, add proper HIPAA-compliant security (encryption at rest, audit logging, BAA with cloud providers), and pass a security review. The ElevenLabs voice quality is already production-grade.

**Q30: How would you add multi-language support?**
> The Web Speech API already supports multiple languages by changing the `rec.lang` property. For premium mode, ElevenLabs supports multilingual voice synthesis. We'd also need to translate the system prompts and knowledge base documents, and potentially use a translation API for dynamic content from the database.
