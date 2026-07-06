# AlphaMed Voice AI — Demo Script

Use these questions in order to demo all features of the voice agent. Works in both **Browser Mode** (free) and **Premium Mode** (ElevenLabs + Gemini).

---

## 🔗 Open the App

1. Run `run_server.bat` or: `uvicorn backend.app.main:app --reload`
2. Open: **http://127.0.0.1:8000**
3. Click the **microphone button** to start a call

---

## 🎤 Demo with Patient: John Doe

### Step 1 — Try accessing data without verification (HIPAA guardrail)

> **Say:** *"What is my balance?"*

**Expected Response:** The agent refuses and asks you to verify your identity first — demonstrating the HIPAA compliance guardrail.

---

### Step 2 — Verify patient identity

> **Say:** *"Verify John Doe, date of birth May 15th 1985, policy POL12345"*

**Expected Response:** *"Thank you, I have verified your profile for John Doe."*
**Dashboard Update:** Verification badge turns green, patient name/policy/provider load, claims and appointments populate automatically.

---

### Step 3 — Check outstanding balance

> **Say:** *"What is my outstanding balance?"*

**Expected Response:** *"Your outstanding copay balance is $45.00, due on 2026-07-20. We offer flexible payment plans of three or six months."*

---

### Step 4 — List all claims

> **Say:** *"Show me my claims"*

**Expected Response:** Lists 2 claims:
- CLM10001 — **Paid** ($450.00, office visit + blood draw)
- CLM10002 — **Denied** ($1,200.00, MRI lumbar spine)

---

### Step 5 — Ask about denied claim

> **Say:** *"Why was claim CLM10002 denied?"*

**Expected Response:** *"Claim CLM10002 is currently Denied. It was denied because: Prior Authorization Required."*

---

### Step 6 — CPT code lookup

> **Say:** *"What is CPT code 72148?"*

**Expected Response:** *"CPT Code 72148 is an MRI scan of the lumbar spine (your lower back) without contrast. It is commonly used for persistent lower back pain."*

---

### Step 7 — Ask about the appeals process

> **Say:** *"How do I appeal a denied claim?"*

**Expected Response:** *"You have the right to appeal any claim denial in writing within 180 days. I can transfer you to a billing supervisor if you need assistance filing it."*

---

### Step 8 — Check appointments

> **Say:** *"When is my next appointment?"*

**Expected Response:** Shows appointment with **Dr. Sarah Johnson** on **2026-07-10 at 10:00 AM** for "Follow-up on MRI results."

---

### Step 9 — Ask about another CPT code

> **Say:** *"What is CPT code 99213?"*

**Expected Response:** *"CPT Code 99213 represents a standard mid-level outpatient office visit with a doctor, lasting between 15 to 29 minutes."*

---

### Step 10 — Request transfer to human

> **Say:** *"I want to talk to a real person"*

**Expected Response:** *"Of course. I am transferring your call to a billing supervisor now. Please remain on the line."*
**Dashboard Update:** Status changes to "Transferred to Supervisor", call ends.

---

## 🎤 Demo with Patient: Jane Smith

Start a new call and repeat the flow with Jane's credentials.

### Verify Jane

> **Say:** *"Verify Jane Smith, date of birth August 22nd 1990, policy POL67890"*

**Expected Response:** Verification succeeds. Dashboard loads Jane's profile with Aetna insurance.

---

### Check Jane's balance

> **Say:** *"What is my outstanding balance?"*

**Expected Response:** *"Your outstanding copay balance is $30.00, due on 2026-07-15."*

---

### Check Jane's claims

> **Say:** *"What are my claims?"*

**Expected Response:** Lists 2 claims:
- CLM20001 — **Paid** ($150.00, brief office visit)
- CLM20002 — **Pending** ($350.00, medium office visit + inhalation treatment)

---

### Check Jane's appointments

> **Say:** *"When is my next appointment?"*

**Expected Response:** Shows appointment with **Dr. Robert Lee** on **2026-07-12 at 2:30 PM** for "Annual physical checkup."

---

### Ask about payment plans

> **Say:** *"Do you offer payment plans?"*

**Expected Response:** Explains flexible payment plans (3, 6, or 12 months with 0% interest) and 15% discount for paying within 10 days.

---

## ⌨️ Keyboard Alternatives

If microphone is unavailable, type these into the text input box at the bottom:

| Type This | What It Tests |
|-----------|--------------|
| `Verify John Doe, May 15th 1985, policy POL12345` | Patient verification |
| `What is my balance?` | Invoice/billing lookup |
| `Show me my claims` | Claims listing |
| `Why was claim CLM10002 denied?` | Specific claim details |
| `What is CPT code 72148?` | Knowledge base / CPT lookup |
| `How do I appeal?` | FAQ / policy search |
| `Schedule an appointment` | Appointment booking |
| `Transfer me to a human` | Human escalation |

---

## 📝 Summary of Features Demonstrated

| # | Feature | Demonstrated By |
|---|---------|----------------|
| 1 | HIPAA identity verification guardrail | Step 1 (blocked) → Step 2 (verified) |
| 2 | Real-time dashboard updates | Steps 2–4 |
| 3 | Insurance claim status lookup | Steps 4–5 |
| 4 | Claim denial explanation | Step 5 |
| 5 | CPT medical code explanation | Steps 6, 9 |
| 6 | Billing balance inquiry | Step 3 |
| 7 | Knowledge base / FAQ search (RAG) | Step 7 |
| 8 | Appointment lookup | Step 8 |
| 9 | Human agent transfer | Step 10 |
| 10 | Voice STT + TTS | All steps |
| 11 | Keyboard text fallback | Keyboard table |
| 12 | Multiple patient support | Jane Smith section |
