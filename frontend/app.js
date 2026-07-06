/* frontend/app.js - Voice Dashboard Controller */
console.log("APP VERSION 12345");
// API Base URL (FastAPI backend port 8000)
const API_BASE_URL = 'http://127.0.0.1:8000';
const WS_BASE_URL = 'ws://127.0.0.1:8000';

// Global variables for active caller state
let activePatient = null;
let isCallActive = false;
let wsConnection = null;
let elevenConversation = null;

// Speech Recognition & Synthesis Web API (Free Browser Fallback)
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let synthesis = window.speechSynthesis;

// UI Elements
const connectionIndicator = document.getElementById('connectionIndicator');
const connectionText = document.getElementById('connectionText');
const patientVerified = document.getElementById('patientVerified');
const patientName = document.getElementById('patientName');
const patientPolicy = document.getElementById('patientPolicy');
const patientProvider = document.getElementById('patientProvider');
const billingBalance = document.getElementById('billingBalance');
const claimCount = document.getElementById('claimCount');
const claimsList = document.getElementById('claimsList');
const appointmentsList = document.getElementById('appointmentsList');
const modeToggle = document.getElementById('modeToggle');
const callStatusBar = document.getElementById('callStatusBar');
const callStatusText = document.getElementById('callStatusText');
const transcriptContainer = document.getElementById('transcriptContainer');
const micButton = document.getElementById('micButton');
const audioWave = document.getElementById('audioWave');
const helpText = document.getElementById('helpText');
const keyboardInput = document.getElementById('keyboardInput');
const sendBtn = document.getElementById('sendBtn');

// Initialize Web Speech Recognition
let speechRecognized = false;

function RecognitionWrapper() {
    const rec = new SpeechRecognition();
    rec.continuous = false; // Stop listening when user stops talking
    rec.lang = 'en-US';
    rec.interimResults = false;

    // Handle Speech Recognition Events
    rec.onstart = () => {
        speechRecognized = false;
        setCallStatus('Listening...', 'active');
        audioWave.classList.add('active');
        console.log("Speech recognition started.");
    };

    rec.onerror = (e) => {
        console.error('Speech recognition error:', e.error);
        if (e.error === 'no-speech') {
            setCallStatus('No speech detected. Listening...', 'active');
        }
        audioWave.classList.remove('active');
    };

    rec.onend = () => {
        audioWave.classList.remove('active');
        // If the call is still active, we can reset to "Ready" or process
        if (isCallActive && modeToggle.value === 'browser') {
            if (speechRecognized) {
                setCallStatus('Processing speech...', 'active');
            } else {
                console.log("No speech recognized. Restarting loop...");
                try {
                    rec.start();
                } catch (err) {
                    console.error("Failed to restart speech recognition:", err);
                }
            }
        }
    };

    rec.onresult = async (event) => {
        speechRecognized = true;
        const transcript = event.results[0][0].transcript;
        addTranscriptBubble(transcript, 'user');

        // Process text using our local mock rule processor
        // speakText() will restart recognition after speaking finishes
        await processUserMessage(transcript);
    };

    return rec;
}

if (SpeechRecognition) {
    recognition = new RecognitionWrapper();
} else {
    console.warn("Speech recognition is not supported in this browser. Falling back to keyboard input only.");
    helpText.innerText = "Mic not supported. Please type your message below.";
    micButton.style.opacity = 0.5;
    micButton.disabled = true;
}

// --- CALL STATE HANDLERS ---

function setCallStatus(text, className = '') {
    callStatusText.innerText = text;
    callStatusBar.className = 'call-status-bar ' + className;
}

function addTranscriptBubble(text, sender) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;

    const content = document.createElement('div');
    content.className = 'bubble-content';
    content.innerText = text;

    bubble.appendChild(content);
    transcriptContainer.appendChild(bubble);
    transcriptContainer.scrollTop = transcriptContainer.scrollHeight;
}

// Speak text out loud using browser Speech Synthesis API
// NOTE: Chrome/Windows has a known bug where speechSynthesis.onend sometimes
// never fires, breaking the conversation loop. We use a polling watchdog fix.
function speakText(text) {
    if (!synthesis) return;

    // Stop any speech currently playing
    synthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    // Find a good English voice if available
    const voices = synthesis.getVoices();
    const englishVoice = voices.find(voice => voice.lang.includes('en-US')) || voices[0];
    if (englishVoice) {
        utterance.voice = englishVoice;
    }

    let hasEnded = false;
    let watchdogInterval = null;

    function onSpeechEnd() {
        if (hasEnded) return;
        hasEnded = true;
        if (watchdogInterval) { clearInterval(watchdogInterval); watchdogInterval = null; }
        audioWave.classList.remove('active');
        if (isCallActive && modeToggle.value === 'browser') {
            setCallStatus('Listening...', 'active');
            if (recognition) {
                try { recognition.start(); } catch(e) { console.warn('mic restart:', e); }
            }
        } else if (!isCallActive) {
            setCallStatus('Ready to start call');
        }
    }

    utterance.onstart = () => {
        setCallStatus('Speaking...', 'active');
        audioWave.classList.add('active');
        // Watchdog: Chrome/Windows onend bug — poll until speaking stops
        watchdogInterval = setInterval(() => {
            if (!synthesis.speaking) { onSpeechEnd(); }
        }, 250);
    };

    utterance.onend = onSpeechEnd;
    utterance.onerror = onSpeechEnd;

    synthesis.speak(utterance);
}

// Check if Backend is running on startup
async function checkBackendConnection() {
    try {
        const res = await fetch(`${API_BASE_URL}/`);
        if (res.ok) {
            connectionIndicator.classList.add('online');
            connectionText.innerText = 'Connected to API';
            console.log("Successfully connected to FastAPI Backend.");
        }
    } catch (e) {
        connectionIndicator.classList.remove('online');
        connectionText.innerText = 'Server Offline';
        console.warn("FastAPI backend is offline. Run 'uvicorn backend.app.main:app' to test database APIs.");
    }
}

// Trigger connection check on window load
window.addEventListener('load', () => {
    checkBackendConnection();
    // Some browsers need a user interaction before voices are loaded
    if (synthesis) synthesis.getVoices();
});


// --- MOCK NLP INTELLIGENCE ENGINE (NO API KEYS FALLBACK) ---

async function processUserMessage(text) {
    const textLower = text.toLowerCase();

    // 1. Identity Verification Request check
    // Looks for name keywords or DOB keywords or policy keywords
    if (!activePatient && (textLower.includes("verify") || textLower.includes("doe") || textLower.includes("smith") || textLower.includes("policy"))) {

        let targetPatient = null;
        let dob = null;
        let policy = null;

        // Mock simple extraction logic for our seed patients
        if (textLower.includes("john") || textLower.includes("doe") || textLower.includes("pol12345")) {
            targetPatient = { first_name: "John", last_name: "Doe", dob: "1985-05-15", policy: "POL12345" };
        } else if (textLower.includes("jane") || textLower.includes("smith") || textLower.includes("pol67890")) {
            targetPatient = { first_name: "Jane", last_name: "Smith", dob: "1990-08-22", policy: "POL67890" };
        }

        if (targetPatient) {
            try {
                setCallStatus('Querying database...', 'active');
                const response = await fetch(`${API_BASE_URL}/api/verify-patient`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        first_name: targetPatient.first_name,
                        last_name: targetPatient.last_name,
                        date_of_birth: targetPatient.dob,
                        policy_number: targetPatient.policy
                    })
                });

                if (response.ok) {
                    activePatient = await response.json();
                    updatePatientUI(activePatient);

                    const reply = `Thank you, I have verified your profile for ${activePatient.first_name} ${activePatient.last_name}. How can I assist you with your blue cross blue shield insurance claims or balances today?`;
                    addTranscriptBubble(reply, 'assistant');
                    speakText(reply);
                    return;
                }
            } catch (error) {
                console.error("Verification database fetch failed:", error);
            }
        }

        const failReply = "I was unable to verify your identity. Please state your full name, date of birth, and policy number clearly.";
        addTranscriptBubble(failReply, 'assistant');
        speakText(failReply);
        return;
    }

    // 2. Check outstanding bill balance
    if (textLower.includes("balance") || textLower.includes("bill") || textLower.includes("invoice") || textLower.includes("pay")) {
        if (!activePatient) {
            const reply = "I would be happy to check your balance, but I need to verify your identity first. What is your name and policy number?";
            addTranscriptBubble(reply, 'assistant');
            speakText(reply);
            return;
        }

        try {
            const res = await fetch(`${API_BASE_URL}/api/patients/${activePatient.policy_number}/invoices`);
            if (res.ok) {
                const invoices = await res.json();
                renderInvoices(invoices);
                const unpaid = invoices.filter(i => i.payment_status === "Unpaid");
                if (unpaid.length > 0) {
                    const totalBalance = unpaid.reduce((sum, inv) => sum + inv.outstanding_balance, 0);
                    const reply = `Your outstanding copay balance is $${totalBalance.toFixed(2)}, due on ${unpaid[0].due_date}. We offer flexible payment plans of three or six months.`;
                    addTranscriptBubble(reply, 'assistant');
                    speakText(reply);
                } else {
                    const reply = "Great news! You do not have any outstanding balances at this time.";
                    addTranscriptBubble(reply, 'assistant');
                    speakText(reply);
                }
                return;
            }
        } catch (err) {
            console.error(err);
        }
    }

    // 3. Check claims status
    if (textLower.includes("claim") || textLower.includes("clm")) {
        if (!activePatient) {
            const reply = "I can look up your claim status, but I must verify your identity first. Please provide your name, date of birth, and policy number.";
            addTranscriptBubble(reply, 'assistant');
            speakText(reply);
            return;
        }

        // If checking a specific claim number (e.g. CLM10002)
        const claimMatch = textLower.match(/clm\d{5}/);
        if (claimMatch) {
            const claimNum = claimMatch[0].toUpperCase();
            try {
                const res = await fetch(`${API_BASE_URL}/api/claims/${claimNum}`);
                if (res.ok) {
                    const claim = await res.json();
                    let reply = `Claim ${claim.claim_number} is currently ${claim.status}.`;
                    if (claim.status === "Denied") {
                        reply += ` It was denied because: ${claim.denial_reason}.`;
                    } else if (claim.status === "Paid") {
                        reply += ` Insurance paid $${claim.amount_paid}.`;
                    }
                    addTranscriptBubble(reply, 'assistant');
                    speakText(reply);

                    // Refresh claims UI list
                    fetchClaimsList();
                    return;
                }
            } catch (err) {
                console.error(err);
            }
        }

        // Otherwise, list all claims for the patient
        try {
            const res = await fetch(`${API_BASE_URL}/api/patients/${activePatient.policy_number}/claims`);
            if (res.ok) {
                const claims = await res.json();
                renderClaims(claims);
                const deniedCount = claims.filter(c => c.status === "Denied").length;
                let reply = `I found ${claims.length} claims on file for your policy. `;
                if (deniedCount > 0) {
                    reply += `You have ${deniedCount} denied claim. Would you like me to explain the denial reason?`;
                } else {
                    reply += "They are all paid or pending processing. How can I help you further?";
                }
                addTranscriptBubble(reply, 'assistant');
                speakText(reply);
                return;
            }
        } catch (err) {
            console.error(err);
        }
    }

    // 4. Check CPT Codes or general FAQs (Local RAG keyword-mock simulation)
    if (textLower.includes("cpt") || textLower.includes("code") || textLower.includes("mri") || textLower.includes("appeal") || textLower.includes("denial reason")) {
        let answer = "Our billing team processes claims daily. Standard codes like 99213 are for office visits. What code are you inquiring about?";

        if (textLower.includes("72148")) {
            answer = "CPT Code 72148 is an MRI scan of the lumbar spine (your lower back) without contrast. It is commonly used for persistent lower back pain.";
        } else if (textLower.includes("99213")) {
            answer = "CPT Code 99213 represents a standard mid level outpatient office visit with a doctor, lasting between 15 to 29 minutes.";
        } else if (textLower.includes("appeal") || textLower.includes("how to appeal")) {
            answer = "You have the right to appeal any claim denial in writing within 180 days. I can transfer you to a billing supervisor if you need assistance filing it.";
        }

        addTranscriptBubble(answer, 'assistant');
        speakText(answer);
        return;
    }

    // 5. Transfer to human representative
    if (textLower.includes("human") || textLower.includes("agent") || textLower.includes("representative") || textLower.includes("supervisor") || textLower.includes("person") || textLower.includes("talk to someone")) {
        const reply = "Of course. I am transferring your call to a billing supervisor now. Please remain on the line.";
        addTranscriptBubble(reply, 'assistant');
        addTranscriptBubble("[SYSTEM] Call transferred to human billing representative. Call ended.", 'system');
        speakText(reply);

        setTimeout(() => {
            endCall();
            setCallStatus("Transferred to Supervisor", "transferred");
        }, 3000);
        return;
    }

    // Default conversational reply
    const defaultReply = "I understand. Can you please tell me more details about your claim, bill balance, or appointments?";
    addTranscriptBubble(defaultReply, 'assistant');
    speakText(defaultReply);
}

// --- DYNAMIC UI RENDERING ---

function updatePatientUI(patient) {
    patientVerified.innerText = "Verified";
    patientVerified.className = "value badge status-verified";
    patientName.innerText = `${patient.first_name} ${patient.last_name}`;
    patientPolicy.innerText = patient.policy_number;
    patientProvider.innerText = patient.insurance_provider;

    // Fetch and render claims and appointments automatically
    fetchClaimsList();
    fetchAppointmentsList();
}

async function fetchClaimsList() {
    if (!activePatient) return;
    try {
        const res = await fetch(`${API_BASE_URL}/api/patients/${activePatient.policy_number}/claims`);
        if (res.ok) {
            const claims = await res.json();
            renderClaims(claims);
        }
    } catch (e) { console.error(e); }
}

function renderClaims(claims) {
    claimCount.innerText = `${claims.length} Claims`;
    claimsList.innerHTML = "";

    if (claims.length === 0) {
        claimsList.innerHTML = `<p class="placeholder-text">No claims found.</p>`;
        return;
    }

    claims.forEach(c => {
        const item = document.createElement('div');
        item.className = `claim-item ${c.status.toLowerCase()}`;
        item.innerHTML = `
            <div>
                <strong>${c.claim_number}</strong> (${c.date_of_service})
                <br><span style="color:var(--text-secondary)">CPT: ${c.cpt_codes}</span>
            </div>
            <div>
                <strong>$${c.total_amount.toFixed(2)}</strong>
                <br><span class="badge ${c.status === 'Paid' ? 'status-verified' : c.status === 'Denied' ? 'status-unverified' : ''}" style="padding: 2px 6px;">${c.status}</span>
            </div>
        `;
        claimsList.appendChild(item);
    });
}

async function fetchAppointmentsList() {
    if (!activePatient) return;
    try {
        const res = await fetch(`${API_BASE_URL}/api/patients/${activePatient.policy_number}/appointments`);
        if (res.ok) {
            const appts = await res.json();
            renderAppointments(appts);
        }
    } catch (e) { console.error(e); }
}

function renderAppointments(appts) {
    appointmentsList.innerHTML = "";

    if (appts.length === 0) {
        appointmentsList.innerHTML = `<p class="placeholder-text">No upcoming appointments.</p>`;
        return;
    }

    appts.forEach(a => {
        const item = document.createElement('div');
        item.className = `appt-item`;
        item.innerHTML = `
            <div>
                <strong>${a.provider_name}</strong>
                <br><span style="color:var(--text-secondary)">${a.reason_for_visit}</span>
            </div>
            <div style="text-align:right">
                <strong>${a.appointment_date}</strong>
                <br><span style="font-size:0.75rem; color:var(--success-green); font-weight:bold;">${a.status}</span>
            </div>
        `;
        appointmentsList.appendChild(item);
    });
}

function renderInvoices(invoices) {
    const unpaid = invoices.filter(i => i.payment_status === "Unpaid");
    const totalBalance = unpaid.reduce((sum, inv) => sum + inv.outstanding_balance, 0);
    billingBalance.innerText = `$${totalBalance.toFixed(2)}`;
}

// Reset UI on disconnect/call ending
function resetPatientUI() {
    activePatient = null;
    patientVerified.innerText = "Unverified";
    patientVerified.className = "value badge status-unverified";
    patientName.innerText = "--";
    patientPolicy.innerText = "--";
    patientProvider.innerText = "--";
    billingBalance.innerText = "$0.00";
    claimCount.innerText = "0 Claims";
    claimsList.innerHTML = `<p class="placeholder-text">Verify patient to display claims</p>`;
    appointmentsList.innerHTML = `<p class="placeholder-text">Verify patient to display appointments</p>`;
}


// --- INTERACTION CONTROLS ---

function toggleCall() {
    if (isCallActive) {
        endCall();
    } else {
        startCall();
    }
}

function startCall() {
    isCallActive = true;
    micButton.classList.add('active');
    helpText.innerText = "Call active. Click microphone to end call.";

    // Clear old transcripts and reset profile data
    transcriptContainer.innerHTML = "";
    resetPatientUI();

    if (modeToggle.value === 'browser') {
        setCallStatus('Listening...', 'active');
        const welcome = "Hello! Thank you for calling AlphaMed Clinic. I am your billing assistant. How can I help you today?";
        addTranscriptBubble(welcome, 'assistant');
        speakText(welcome);
    } else {
        // AI Server Mode – use ElevenLabs SDK via backend proxy
        setCallStatus('Connecting to ElevenLabs...', 'active');
        startElevenConversation();
    }
}

function endCall() {
    isCallActive = false;
    micButton.classList.remove('active');
    audioWave.classList.remove('active');
    helpText.innerText = "Click microphone to start talking";
    setCallStatus('Call ended');

    if (recognition) {
        recognition.stop();
    }

    if (synthesis) {
        synthesis.cancel();
    }

    if (wsConnection) {
        wsConnection.close();
        wsConnection = null;
    }

    if (elevenConversation) {
        elevenConversation.endSession();
        elevenConversation = null;
    }
}
    // --- ElevenLabs Browser Integration Functions ---

    async function startElevenConversation() {
        try {
            // Request mic permission first
            await navigator.mediaDevices.getUserMedia({ audio: true });

            const startRes = await fetch(`${API_BASE_URL}/elevenlabs/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!startRes.ok) throw new Error('Failed to start ElevenLabs session');
            const data = await startRes.json();
            
            setCallStatus('Connecting to ElevenLabs...', 'active');

            elevenConversation = await ElevenLabs.Conversation.startSession({
                signedUrl: data.signed_url,
                onConnect: () => {
                    setCallStatus('Call Active (ElevenLabs AI Receptionist)', 'active');
                    audioWave.classList.add('active');
                    console.log("ElevenLabs session connected successfully.");
                },
                onDisconnect: () => {
                    setCallStatus('Call ended');
                    audioWave.classList.remove('active');
                    isCallActive = false;
                    micButton.classList.remove('active');
                    console.log("ElevenLabs session disconnected.");
                },
                onError: (error) => {
                    console.error('ElevenLabs error:', error);
                    setCallStatus('Error connecting to ElevenLabs', 'error');
                    fetch('/api/log-error', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            message: 'ElevenLabs client error: ' + String(error) + (error && error.message ? ' - ' + error.message : ''),
                            stack: error && error.stack ? String(error.stack) : null
                        })
                    }).catch(e => console.error(e));
                },
                onMessage: (msg) => {
                    console.log('ElevenLabs message:', msg);
                    // Differentiate between user transcript and assistant response
                    if (msg.source === 'user') {
                        addTranscriptBubble(msg.message, 'user');
                    } else if (msg.source === 'ai') {
                        addTranscriptBubble(msg.message, 'assistant');
                    }
                },
                clientTools: {
                    verify_patient: async (args) => {
                        console.log("Tool verify_patient invoked with args:", args);
                        try {
                            const res = await fetch(`${API_BASE_URL}/api/verify-patient`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(args)
                            });
                            if (res.ok) {
                                activePatient = await res.json();
                                updatePatientUI(activePatient);
                                
                                // Fetch claims, appointments and invoices for the verified patient automatically
                                const claimsRes = await fetch(`${API_BASE_URL}/api/patients/${activePatient.policy_number}/claims`);
                                if (claimsRes.ok) {
                                    renderClaims(await claimsRes.json());
                                }
                                const apptsRes = await fetch(`${API_BASE_URL}/api/patients/${activePatient.policy_number}/appointments`);
                                if (apptsRes.ok) {
                                    renderAppointments(await apptsRes.json());
                                }
                                const invoicesRes = await fetch(`${API_BASE_URL}/api/patients/${activePatient.policy_number}/invoices`);
                                if (invoicesRes.ok) {
                                    renderInvoices(await invoicesRes.json());
                                }

                                return JSON.stringify({
                                    verified: true,
                                    patient_id: activePatient.id,
                                    first_name: activePatient.first_name,
                                    last_name: activePatient.last_name,
                                    insurance_provider: activePatient.insurance_provider
                                });
                            }
                        } catch (e) {
                            console.error(e);
                        }
                        return JSON.stringify({ verified: false, error: "Patient records not found." });
                    },
                    get_patient_claims: async (args) => {
                        console.log("Tool get_patient_claims invoked with args:", args);
                        try {
                            const res = await fetch(`${API_BASE_URL}/api/patients/${args.policy_number}/claims`);
                            if (res.ok) {
                                const claims = await res.json();
                                renderClaims(claims);
                                return JSON.stringify(claims.map(c => ({
                                    claim_number: c.claim_number,
                                    date_of_service: c.date_of_service,
                                    status: c.status,
                                    total_amount: c.total_amount,
                                    amount_paid: c.amount_paid
                                })));
                            }
                        } catch (e) {
                            console.error(e);
                        }
                        return JSON.stringify({ error: "Failed to fetch claims." });
                    },
                    get_claim_details: async (args) => {
                        console.log("Tool get_claim_details invoked with args:", args);
                        try {
                            const res = await fetch(`${API_BASE_URL}/api/claims/${args.claim_number}`);
                            if (res.ok) {
                                const claim = await res.json();
                                return JSON.stringify(claim);
                            }
                        } catch (e) {
                            console.error(e);
                        }
                        return JSON.stringify({ error: "Claim not found." });
                    },
                    get_patient_invoices: async (args) => {
                        console.log("Tool get_patient_invoices invoked with args:", args);
                        try {
                            const res = await fetch(`${API_BASE_URL}/api/patients/${args.policy_number}/invoices`);
                            if (res.ok) {
                                const invoices = await res.json();
                                renderInvoices(invoices);
                                return JSON.stringify(invoices.map(i => ({
                                    invoice_number: i.invoice_number,
                                    due_date: i.due_date,
                                    outstanding_balance: i.outstanding_balance,
                                    payment_status: i.payment_status
                                })));
                            }
                        } catch (e) {
                            console.error(e);
                        }
                        return JSON.stringify({ error: "Failed to fetch invoices." });
                    },
                    get_patient_appointments: async (args) => {
                        console.log("Tool get_patient_appointments invoked with args:", args);
                        try {
                            const res = await fetch(`${API_BASE_URL}/api/patients/${args.policy_number}/appointments`);
                            if (res.ok) {
                                const appts = await res.json();
                                renderAppointments(appts);
                                return JSON.stringify(appts.map(a => ({
                                    appointment_date: a.appointment_date,
                                    provider_name: a.provider_name,
                                    reason_for_visit: a.reason_for_visit,
                                    status: a.status
                                })));
                            }
                        } catch (e) {
                            console.error(e);
                        }
                        return JSON.stringify({ error: "Failed to fetch appointments." });
                    },
                    schedule_new_appointment: async (args) => {
                        console.log("Tool schedule_new_appointment invoked with args:", args);
                        try {
                            const res = await fetch(`${API_BASE_URL}/api/appointments`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(args)
                            });
                            if (res.ok) {
                                const appt = await res.json();
                                const apptsRes = await fetch(`${API_BASE_URL}/api/patients/${args.policy_number}/appointments`);
                                if (apptsRes.ok) {
                                    renderAppointments(await apptsRes.json());
                                }
                                return JSON.stringify({
                                    status: "Scheduled",
                                    appointment_id: appt.id,
                                    appointment_date: appt.appointment_date,
                                    provider_name: appt.provider_name
                                });
                            }
                        } catch (e) {
                            console.error(e);
                        }
                        return JSON.stringify({ error: "Failed to schedule appointment." });
                    },
                    transfer_to_human: async (args) => {
                        console.log("Tool transfer_to_human invoked with args:", args);
                        setCallStatus('Transferred to Human', 'transferred');
                        addTranscriptBubble(`[SYSTEM] Call transferred to human supervisor. Reason: ${args.reason}`, 'system');
                        return JSON.stringify({ status: "Transferring call to human agent..." });
                    }
                }
            });

        } catch (err) {
            console.error(err);
            setCallStatus('Error connecting to ElevenLabs', 'error');
        }
    }

    // Establish real-time WebSocket connection to backend voice agent
    function connectWebSocket() {
        const wsUrl = `${WS_BASE_URL}/api/voice`;
        console.log(`Connecting to voice agent WebSocket: ${wsUrl}`);

        wsConnection = new WebSocket(wsUrl);

        wsConnection.onopen = () => {
            setCallStatus('Call Active (Streaming Audio)', 'active');
            console.log("WebSocket connected successfully.");
            // Prompt greeting
            const greeting = "Hello, you are connected to the premium medical billing agent. How can I help you?";
            addTranscriptBubble(greeting, 'assistant');
            speakText(greeting);
        };

        wsConnection.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.transcript) {
                    addTranscriptBubble(data.transcript, 'user');
                }
                if (data.response) {
                    addTranscriptBubble(data.response, 'assistant');
                    speakText(data.response);
                }
                if (data.patient_update) {
                    updatePatientUI(data.patient_update);
                }
            } catch (e) {
                console.error("Error parsing websocket JSON message:", e);
            }
        };

        wsConnection.onclose = () => {
            console.log("WebSocket connection closed.");
            if (isCallActive) {
                endCall();
            }
        };

        wsConnection.onerror = (error) => {
            console.error("WebSocket error:", error);
            setCallStatus('Connection Error. Reverting to Browser Mode.', 'transferred');
            setTimeout(() => {
                modeToggle.value = 'browser';
                startCall();
            }, 1500);
        };
    }

// Bind event listeners
micButton.addEventListener('click', toggleCall);

// Send message via keyboard
async function handleSend() {
    const messageText = keyboardInput.value.trim();
    if (!messageText) return;

    addTranscriptBubble(messageText, 'user');
    keyboardInput.value = "";

    if (isCallActive && modeToggle.value === 'browser') {
        if (recognition) recognition.stop(); // Stop mic temporarily while typing
        await processUserMessage(messageText);
    } else if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        // Send plain text message over the premium web socket stream
        wsConnection.send(JSON.stringify({ text: messageText }));
    } else {
        // Start call if inactive
        isCallActive = true;
        micButton.classList.add('active');
        setCallStatus('Active Call', 'active');
        await processUserMessage(messageText);
    }
}

sendBtn.addEventListener('click', handleSend);
keyboardInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleSend();
    }
});

modeToggle.addEventListener('change', () => {
    if (isCallActive) {
        endCall();
        startCall();
    }
});

