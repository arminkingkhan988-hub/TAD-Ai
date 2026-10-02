from flask import Flask

app = Flask(__name__)
import os
import json
import urllib.request
import urllib.error

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
).strip()

MAX_MESSAGE_LENGTH = 12000
MAX_HISTORY_ITEMS = 20


# ============================================================
# MEDICAL SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are MedAI, a medical information assistant.

Your job is to provide clear, useful, cautious medical information.

IMPORTANT SAFETY RULES:

1. You are not a doctor and you are not a replacement for a doctor,
   pharmacist, emergency service, or hospital.

2. Never claim that you can make a certain diagnosis from symptoms alone.

3. Explain possible causes as possibilities, not certainties.

4. If symptoms could indicate a medical emergency, clearly tell the user
   to contact local emergency medical services or go to the nearest
   emergency department.

5. Do not provide dangerous instructions.

6. For medicines:
   - Explain common uses.
   - Explain common side effects.
   - Explain important precautions.
   - Mention important interactions when relevant.
   - Do not invent a prescription.
   - Encourage confirmation of dosing with a doctor or pharmacist.

7. For laboratory reports:
   - Explain what the test generally measures.
   - Explain whether a value is commonly considered low/high only when
     enough information is available.
   - Mention that reference ranges vary by laboratory.
   - Do not diagnose solely from a laboratory value.

8. For pregnancy, children, elderly people, severe symptoms, or major
   chronic diseases, recommend professional medical evaluation when
   appropriate.

9. Ask relevant follow-up questions when necessary.

10. Answer in the language used by the user.
    If the user writes Pashto, answer in Pashto.
    If the user writes Dari, answer in Dari.
    If the user writes English, answer in English.

11. Keep answers understandable and organized.

12. For emergencies, prioritize urgent medical care over lengthy
    explanations.

13. Do not pretend to have examined the patient.

14. If information is uncertain or incomplete, say so clearly.
"""


# ============================================================
# GEMINI API
# ============================================================

def ask_gemini(message, history):
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured on the server."
        )

    contents = []

    if isinstance(history, list):
        for item in history[-MAX_HISTORY_ITEMS:]:
            if not isinstance(item, dict):
                continue

            role = item.get("role")
            text = item.get("text")

            if role not in ("user", "model"):
                continue

            if not isinstance(text, str):
                continue

            text = text.strip()

            if not text:
                continue

            contents.append({
                "role": role,
                "parts": [
                    {
                        "text": text[:MAX_MESSAGE_LENGTH]
                    }
                ]
            })

    # Prevent duplicate current message.
    already_added = False

    if contents:
        last = contents[-1]

        if last.get("role") == "user":
            parts = last.get("parts") or []

            if (
                parts
                and isinstance(parts[0], dict)
                and parts[0].get("text") == message
            ):
                already_added = True

    if not already_added:
        contents.append({
            "role": "user",
            "parts": [
                {
                    "text": message[:MAX_MESSAGE_LENGTH]
                }
            ]
        })

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{GEMINI_MODEL}:generateContent"
    )

    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": SYSTEM_PROMPT
                }
            ]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048
        }
    }

    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(
            req,
            timeout=55
        ) as response:

            raw = response.read().decode("utf-8")
            data = json.loads(raw)

    except urllib.error.HTTPError as exc:

        error_body = exc.read().decode(
            "utf-8",
            errors="replace"
        )

        try:
            error_data = json.loads(error_body)

            error_message = (
                error_data
                .get("error", {})
                .get("message")
                or error_body
            )

        except Exception:
            error_message = error_body

        raise RuntimeError(
            f"Gemini API error ({exc.code}): "
            f"{error_message[:500]}"
        )

    except urllib.error.URLError as exc:

        raise RuntimeError(
            "Network error while contacting Gemini: "
            f"{exc.reason}"
        )

    except json.JSONDecodeError:
        raise RuntimeError(
            "Gemini returned invalid JSON."
        )

    candidates = data.get("candidates") or []

    if not candidates:
        raise RuntimeError(
            "Gemini returned no answer."
        )

    content = candidates[0].get("content") or {}

    parts = content.get("parts") or []

    answer = ""

    for part in parts:

        if isinstance(part, dict):

            text = part.get("text", "")

            if isinstance(text, str):
                answer += text

    answer = answer.strip()

    if not answer:
        raise RuntimeError(
            "Gemini returned an empty answer."
        )

    return answer


# ============================================================
# HTML
# ============================================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>MedAI - Medical AI Assistant</title>

<style>

* {
    box-sizing: border-box;
}

:root {
    --bg: #f4f7fb;
    --card: #ffffff;
    --text: #172033;
    --muted: #64748b;
    --border: #dbe3ee;
    --primary: #2563eb;
    --primary-hover: #1d4ed8;
    --user: #e7efff;
    --ai: #f1f5f9;
    --danger: #dc2626;
    --success: #16a34a;
}

body.dark {
    --bg: #0f172a;
    --card: #111827;
    --text: #f8fafc;
    --muted: #94a3b8;
    --border: #263244;
    --primary: #3b82f6;
    --primary-hover: #60a5fa;
    --user: #172554;
    --ai: #1e293b;
}

body {
    margin: 0;
    font-family:
        Arial,
        "Noto Sans",
        sans-serif;

    background: var(--bg);
    color: var(--text);

    transition:
        background 0.2s,
        color 0.2s;
}

button,
textarea,
select {
    font: inherit;
}

.app {
    width: 100%;
    max-width: 1100px;
    margin: auto;
    padding: 20px;
}

.header {
    display: flex;
    align-items: center;
    justify-content: space-between;

    gap: 15px;

    background: var(--card);

    padding: 20px;

    border-radius: 20px;

    border: 1px solid var(--border);

    box-shadow:
        0 8px 30px rgba(0,0,0,.06);

    margin-bottom: 15px;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.logo {
    width: 50px;
    height: 50px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 15px;

    background: var(--primary);

    color: white;

    font-size: 25px;
}

.header h1 {
    margin: 0;
    font-size: 27px;
}

.header p {
    margin: 3px 0 0;
    color: var(--muted);
}

.header-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.btn {
    border: 0;

    border-radius: 10px;

    padding: 10px 13px;

    cursor: pointer;

    background: var(--primary);

    color: white;
}

.btn:hover {
    background: var(--primary-hover);
}

.btn.secondary {
    background: var(--ai);
    color: var(--text);
}

.btn.danger {
    background: var(--danger);
    color: white;
}

.btn:disabled {
    opacity: .5;
    cursor: not-allowed;
}

.notice {
    background: #fff7ed;

    border: 1px solid #fed7aa;

    color: #9a3412;

    padding: 12px 15px;

    border-radius: 12px;

    margin-bottom: 15px;

    line-height: 1.5;
}

body.dark .notice {
    background: #431407;
    color: #fed7aa;
    border-color: #7c2d12;
}

.main {
    display: grid;

    grid-template-columns: 250px 1fr;

    gap: 15px;
}

.sidebar,
.chat {
    background: var(--card);

    border: 1px solid var(--border);

    border-radius: 20px;

    box-shadow:
        0 8px 30px rgba(0,0,0,.06);
}

.sidebar {
    padding: 15px;

    height: fit-content;
}

.sidebar h3 {
    margin-top: 5px;
}

.quick {
    width: 100%;

    text-align: left;

    border: 0;

    background: var(--ai);

    color: var(--text);

    padding: 11px;

    margin: 5px 0;

    border-radius: 10px;

    cursor: pointer;
}

.quick:hover {
    opacity: .8;
}

.chat {
    padding: 15px;

    min-width: 0;
}

.messages {
    height: 58vh;

    min-height: 400px;

    overflow-y: auto;

    padding: 5px;
}

.message {
    padding: 13px 15px;

    border-radius: 15px;

    margin: 12px 0;

    line-height: 1.6;

    white-space: pre-wrap;

    word-break: break-word;
}

.message.user {
    background: var(--user);

    margin-left: 12%;
}

.message.ai {
    background: var(--ai);

    margin-right: 8%;
}

.message.system {
    background: #ecfdf5;

    color: #166534;

    border: 1px solid #bbf7d0;
}

body.dark .message.system {
    background: #052e16;

    color: #bbf7d0;

    border-color: #166534;
}

.message-head {
    font-size: 12px;

    color: var(--muted);

    margin-bottom: 5px;
}

.composer {
    margin-top: 10px;
}

textarea {
    width: 100%;

    resize: vertical;

    min-height: 70px;

    max-height: 200px;

    border: 1px solid var(--border);

    border-radius: 14px;

    background: var(--card);

    color: var(--text);

    padding: 14px;

    outline: none;
}

textarea:focus {
    border-color: var(--primary);
}

.composer-actions {
    display: flex;

    justify-content: space-between;

    align-items: center;

    gap: 10px;

    margin-top: 10px;
}

.left-actions,
.right-actions {
    display: flex;

    gap: 8px;

    flex-wrap: wrap;
}

.status {
    min-height: 20px;

    margin-top: 8px;

    color: var(--muted);

    font-size: 14px;
}

.typing {
    display: inline-flex;

    gap: 4px;
}

.dot {
    width: 6px;
    height: 6px;

    border-radius: 50%;

    background: var(--muted);

    animation: blink 1s infinite;
}

.dot:nth-child(2) {
    animation-delay: .15s;
}

.dot:nth-child(3) {
    animation-delay: .3s;
}

@keyframes blink {
    0%, 100% {
        opacity: .2;
    }

    50% {
        opacity: 1;
    }
}

.modal {
    display: none;

    position: fixed;

    inset: 0;

    background: rgba(0,0,0,.55);

    align-items: center;

    justify-content: center;

    padding: 15px;

    z-index: 100;
}

.modal.show {
    display: flex;
}

.modal-box {
    width: 100%;

    max-width: 600px;

    max-height: 90vh;

    overflow-y: auto;

    background: var(--card);

    color: var(--text);

    border-radius: 18px;

    padding: 20px;
}

.modal-header {
    display: flex;

    justify-content: space-between;

    align-items: center;
}

.modal-header h2 {
    margin: 0;
}

.close {
    border: 0;

    background: transparent;

    color: var(--text);

    font-size: 25px;

    cursor: pointer;
}

.form-group {
    margin: 12px 0;
}

.form-group label {
    display: block;

    margin-bottom: 5px;

    font-size: 14px;
}

.form-group input,
.form-group select {
    width: 100%;

    padding: 11px;

    border-radius: 10px;

    border: 1px solid var(--border);

    background: var(--card);

    color: var(--text);
}

.emergency {
    background: #fef2f2;

    border: 1px solid #fecaca;

    color: #991b1b;

    padding: 13px;

    border-radius: 12px;

    margin-bottom: 10px;
}

body.dark .emergency {
    background: #450a0a;

    border-color: #7f1d1d;

    color: #fecaca;
}

.footer {
    text-align: center;

    color: var(--muted);

    font-size: 13px;

    padding: 20px;
}

@media (max-width: 800px) {

    .main {
        grid-template-columns: 1fr;
    }

    .sidebar {
        order: 2;
    }

    .chat {
        order: 1;
    }

    .messages {
        height: 55vh;
    }

}

@media (max-width: 600px) {

    .app {
        padding: 8px;
    }

    .header {
        align-items: flex-start;

        flex-direction: column;
    }

    .header-actions {
        width: 100%;
    }

    .header-actions .btn {
        flex: 1;
    }

    .message.user {
        margin-left: 3%;
    }

    .message.ai {
        margin-right: 3%;
    }

    .composer-actions {
        flex-direction: column;

        align-items: stretch;
    }

    .left-actions,
    .right-actions {
        width: 100%;
    }

    .left-actions .btn,
    .right-actions .btn {
        flex: 1;
    }

}

</style>

</head>

<body>

<div class="app">

    <header class="header">

        <div class="brand">

            <div class="logo">
                🩺
            </div>

            <div>
                <h1>MedAI</h1>

                <p>
                    AI Medical Information Assistant
                </p>
            </div>

        </div>

        <div class="header-actions">

            <button
                class="btn secondary"
                onclick="toggleLanguage()"
            >
                🌐 <span id="languageText">EN</span>
            </button>

            <button
                class="btn secondary"
                onclick="toggleDark()"
            >
                🌙
            </button>

            <button
                class="btn secondary"
                onclick="openProfile()"
            >
                👤 Profile
            </button>

        </div>

    </header>


    <div class="notice">

        ⚠️ <strong>Medical safety:</strong>
        MedAI provides general medical information and is not a
        replacement for a doctor. If you have a medical emergency,
        contact local emergency medical services or go to the nearest
        emergency department.

    </div>


    <main class="main">

        <aside class="sidebar">

            <button
                class="btn"
                style="width:100%; margin-bottom:10px"
                onclick="newChat()"
            >
                ➕ New Chat
            </button>

            <h3>Quick Tools</h3>

            <button
                class="quick"
                onclick="quickAsk(
                    'Explain my symptoms and possible causes.'
                )"
            >
                🩺 Symptoms
            </button>

            <button
                class="quick"
                onclick="quickAsk(
                    'Explain this medicine, its common uses, side effects, precautions, and important interactions.'
                )"
            >
                💊 Medicine
            </button>

            <button
                class="quick"
                onclick="quickAsk(
                    'Help me understand my laboratory report. Explain what the tests generally measure and what abnormal results can mean.'
                )"
            >
                🧪 Lab Report
            </button>

            <button
                class="quick"
                onclick="quickAsk(
                    'What symptoms require emergency medical attention?'
                )"
            >
                🚨 Emergency
            </button>

            <button
                class="quick"
                onclick="quickAsk(
                    'Give me general healthy lifestyle advice.'
                )"
            >
                ❤️ Healthy Living
            </button>

            <button
                class="quick"
                onclick="quickAsk(
                    'What questions should I ask my doctor about my symptoms?'
                )"
            >
                👨‍⚕️ Doctor Questions
            </button>

            <hr>

            <button
                class="quick"
                onclick="exportChat()"
            >
                📥 Export Chat
            </button>

            <button
                class="quick"
                onclick="clearChat()"
            >
                🗑️ Clear Chat
            </button>

        </aside>


        <section class="chat">

            <div
                id="messages"
                class="messages"
            >

                <div class="message ai">

                    <div class="message-head">
                        MedAI
                    </div>

                    Hello! 👋

                    I am MedAI, an AI medical information assistant.

                    You can ask me about symptoms, medicines,
                    laboratory tests, health questions, or emergency
                    warning signs.

                    Please remember that I cannot replace a doctor.

                </div>

            </div>


            <div class="composer">

                <textarea
                    id="input"
                    placeholder="Write your medical question..."
                    onkeydown="handleKey(event)"
                ></textarea>


                <div class="composer-actions">

                    <div class="left-actions">

                        <button
                            class="btn secondary"
                            onclick="startVoice()"
                        >
                            🎤 Voice
                        </button>

                        <button
                            class="btn secondary"
                            onclick="toggleSpeech()"
                            id="speechButton"
                        >
                            🔊 Voice ON
                        </button>

                    </div>


                    <div class="right-actions">

                        <button
                            class="btn"
                            id="send"
                            onclick="sendMessage()"
                        >
                            Send ➤
                        </button>

                    </div>

                </div>


                <div
                    id="status"
                    class="status"
                ></div>

            </div>

        </section>

    </main>


    <div class="footer">

        MedAI provides general information only.
        Always consult an appropriately qualified healthcare professional
        for diagnosis and treatment.

    </div>

</div>


<!-- PROFILE MODAL -->

<div
    id="profileModal"
    class="modal"
    onclick="closeModalOutside(event)"
>

    <div class="modal-box">

        <div class="modal-header">

            <h2>Patient Profile</h2>

            <button
                class="close"
                onclick="closeProfile()"
            >
                ×
            </button>

        </div>


        <div class="form-group">

            <label>Name</label>

            <input
                id="profileName"
                placeholder="Your name"
            >

        </div>


        <div class="form-group">

            <label>Age</label>

            <input
                id="profileAge"
                type="number"
                min="0"
                max="120"
                placeholder="Age"
            >

        </div>


        <div class="form-group">

            <label>Sex</label>

            <select id="profileSex">

                <option value="">
                    Prefer not to say
                </option>

                <option value="male">
                    Male
                </option>

                <option value="female">
                    Female
                </option>

                <option value="other">
                    Other
                </option>

            </select>

        </div>


        <div class="form-group">

            <label>Important medical information</label>

            <textarea
                id="profileMedical"
                placeholder="Optional: allergies, medications, conditions..."
            ></textarea>

        </div>


        <button
            class="btn"
            onclick="saveProfile()"
            style="width:100%"
        >
            Save Profile
        </button>

    </div>

</div>


<script>

let history = [];

let speakingEnabled = true;

let currentLanguage = "en";


// ============================================================
// LOCAL STORAGE
// ============================================================

function loadData() {

    try {

        const savedHistory =
            localStorage.getItem("medai_history");

        const savedProfile =
            localStorage.getItem("medai_profile");

        const savedDark =
            localStorage.getItem("medai_dark");

        if (savedHistory) {

            history =
                JSON.parse(savedHistory);

        }

        if (savedDark === "1") {

            document.body.classList.add("dark");

        }

        if (savedProfile) {

            const profile =
                JSON.parse(savedProfile);

            document.getElementById("profileName").value =
                profile.name || "";

            document.getElementById("profileAge").value =
                profile.age || "";

            document.getElementById("profileSex").value =
                profile.sex || "";

            document.getElementById("profileMedical").value =
                profile.medical || "";

        }

    } catch (error) {

        console.error(error);

    }

}


function saveHistory() {

    try {

        localStorage.setItem(
            "medai_history",
            JSON.stringify(history.slice(-40))
        );

    } catch (error) {

        console.error(error);

    }

}


// ============================================================
// MESSAGE UI
// ============================================================

function addMessage(role, text) {

    const messages =
        document.getElementById("messages");

    const div =
        document.createElement("div");

    div.className =
        "message " +
        (role === "user"
            ? "user"
            : "ai");

    const head =
        document.createElement("div");

    head.className =
        "message-head";

    head.textContent =
        role === "user"
            ? "You"
            : "MedAI";

    const content =
        document.createElement("div");

    content.textContent = text;

    div.appendChild(head);

    div.appendChild(content);

    messages.appendChild(div);

    messages.scrollTop =
        messages.scrollHeight;

}


function renderHistory() {

    const messages =
        document.getElementById("messages");

    messages.innerHTML = "";

    if (!history.length) {

        addMessage(
            "model",
            "Hello! 👋 I am MedAI. How can I help you today?"
        );

        return;

    }

    history.forEach(item => {

        if (
            item &&
            (
                item.role === "user" ||
                item.role === "model"
            )
        ) {

            addMessage(
                item.role,
                item.text
            );

        }

    });

}


// ============================================================
// CHAT
// ============================================================

function handleKey(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();

    }

}


function quickAsk(text) {

    document.getElementById("input").value =
        text;

    sendMessage();

}


async function sendMessage() {

    const input =
        document.getElementById("input");

    const send =
        document.getElementById("send");

    const status =
        document.getElementById("status");

    const message =
        input.value.trim();

    if (!message) {

        return;

    }


    addMessage(
        "user",
        message
    );


    input.value = "";

    send.disabled = true;


    status.innerHTML = `
        <span class="typing">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
        </span>
        MedAI is thinking...
    `;


    const oldHistory =
        history.slice(-20);


    try {

        const response =
            await fetch(
                "/api/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        message: message,
                        history: oldHistory
                    })
                }
            );


        let data;

        try {

            data =
                await response.json();

        } catch (error) {

            throw new Error(
                "Server returned invalid response."
            );

        }


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Server error."
            );

        }


        const answer =
            data.answer ||
            "No answer received.";


        addMessage(
            "model",
            answer
        );


        history.push({
            role: "user",
            text: message
        });


        history.push({
            role: "model",
            text: answer
        });


        history =
            history.slice(-40);


        saveHistory();


        if (speakingEnabled) {

            speak(answer);

        }


        status.textContent = "";

    } catch (error) {

        addMessage(
            "model",
            "Error: " + error.message
        );

        status.textContent = "";

    }


    send.disabled = false;

    input.focus();

}


// ============================================================
// NEW / CLEAR CHAT
// ============================================================

function newChat() {

    if (
        history.length &&
        !confirm("Start a new chat?")
    ) {

        return;

    }

    history = [];

    saveHistory();

    renderHistory();

}


function clearChat() {

    if (
        !confirm(
            "Are you sure you want to delete the chat history?"
        )
    ) {

        return;

    }

    history = [];

    saveHistory();

    renderHistory();

}


// ============================================================
// VOICE INPUT
// ============================================================

function startVoice() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;


    if (!SpeechRecognition) {

        alert(
            "Voice input is not supported by this browser."
        );

        return;

    }


    const recognition =
        new SpeechRecognition();


    if (currentLanguage === "ps") {

        recognition.lang = "ps-AF";

    } else if (currentLanguage === "fa") {

        recognition.lang = "fa-AF";

    } else {

        recognition.lang = "en-US";

    }


    recognition.interimResults =
        false;

    recognition.maxAlternatives =
        1;


    recognition.onstart = function() {

        document.getElementById(
            "status"
        ).textContent =
            "🎤 Listening...";

    };


    recognition.onresult =
        function(event) {

            const text =
                event.results[0][0]
                .transcript;

            document.getElementById(
                "input"
            ).value = text;

            document.getElementById(
                "status"
            ).textContent =
                "Voice captured.";

        };


    recognition.onerror =
        function(event) {

            document.getElementById(
                "status"
            ).textContent =
                "Voice error: " +
                event.error;

        };


    recognition.onend =
        function() {

            setTimeout(
                function() {

                    document.getElementById(
                        "status"
                    ).textContent = "";

                },
                1500
            );

        };


    recognition.start();

}


// ============================================================
// VOICE OUTPUT
// ============================================================

function speak(text) {

    if (
        !("speechSynthesis" in window)
    ) {

        return;

    }


    window.speechSynthesis.cancel();


    const utterance =
        new SpeechSynthesisUtterance(text);


    if (currentLanguage === "ps") {

        utterance.lang = "ps-AF";

    } else if (currentLanguage === "fa") {

        utterance.lang = "fa-AF";

    } else {

        utterance.lang = "en-US";

    }


    utterance.rate = 0.95;

    utterance.pitch = 1;


    window.speechSynthesis.speak(
        utterance
    );

}


function toggleSpeech() {

    speakingEnabled =
        !speakingEnabled;


    const button =
        document.getElementById(
            "speechButton"
        );


    button.textContent =
        speakingEnabled
            ? "🔊 Voice ON"
            : "🔇 Voice OFF";


    if (!speakingEnabled) {

        if (
            "speechSynthesis"
            in window
        ) {

            window.speechSynthesis.cancel();

        }

    }

}


// ============================================================
// DARK MODE
// ============================================================

function toggleDark() {

    document.body.classList.toggle(
        "dark"
    );


    localStorage.setItem(
        "medai_dark",
        document.body.classList.contains("dark")
            ? "1"
            : "0"
    );

}


// ============================================================
// LANGUAGE
// ============================================================

function toggleLanguage() {

    if (currentLanguage === "en") {

        currentLanguage = "ps";

        document.getElementById(
            "languageText"
        ).textContent = "PS";

        document.getElementById(
            "input"
        ).placeholder =
            "خپله طبي پوښتنه ولیکئ...";

    } else if (currentLanguage === "ps") {

        currentLanguage = "fa";

        document.getElementById(
            "languageText"
        ).textContent = "FA";

        document.getElementById(
            "input"
        ).placeholder =
            "سوال طبی خود را بنویسید...";

    } else {

        currentLanguage = "en";

        document.getElementById(
            "languageText"
        ).textContent = "EN";

        document.getElementById(
            "input"
        ).placeholder =
            "Write your medical question...";

    }

}


// ============================================================
// PROFILE
// ============================================================

function openProfile() {

    document.getElementById(
        "profileModal"
    ).classList.add("show");

}


function closeProfile() {

    document.getElementById(
        "profileModal"
    ).classList.remove("show");

}


function closeModalOutside(event) {

    if (
        event.target.id ===
        "profileModal"
    ) {

        closeProfile();

    }

}


function saveProfile() {

    const profile = {

        name:
            document.getElementById(
                "profileName"
            ).value.trim(),

        age:
            document.getElementById(
                "profileAge"
            ).value,

        sex:
            document.getElementById(
                "profileSex"
            ).value,

        medical:
            document.getElementById(
                "profileMedical"
            ).value.trim()

    };


    localStorage.setItem(
        "medai_profile",
        JSON.stringify(profile)
    );


    closeProfile();


    document.getElementById(
        "status"
    ).textContent =
        "Profile saved.";


    setTimeout(
        function() {

            document.getElementById(
                "status"
            ).textContent = "";

        },
        1500
    );

}


// ============================================================
// EXPORT CHAT
// ============================================================

function exportChat() {

    if (!history.length) {

        alert(
            "There is no chat to export."
        );

        return;

    }


    let output =
        "MedAI Chat\n" +
        "====================\n\n";


    history.forEach(item => {

        output +=
            (
                item.role === "user"
                    ? "You"
                    : "MedAI"
            ) +
            ":\n" +
            item.text +
            "\n\n";

    });


    const blob =
        new Blob(
            [output],
            {
                type: "text/plain;charset=utf-8"
            }
        );


    const url =
        URL.createObjectURL(blob);


    const a =
        document.createElement("a");


    a.href = url;

    a.download =
        "medai-chat.txt";


    document.body.appendChild(a);

    a.click();

    a.remove();

    URL.revokeObjectURL(url);

}


// ============================================================
// START
// ============================================================

loadData();

renderHistory();

</script>

</body>

</html>
"""


# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def home():

    return render_template_string(
        HTML
    )


@app.get("/health")
def health():

    return jsonify({
        "status": "ok",
        "service": "MedAI",
        "gemini_configured": bool(
            GEMINI_API_KEY
        )
    })


@app.post("/api/chat")
def chat():

    try:

        data =
            request.get_json(
                silent=True
            ) or {}

        message =
            data.get(
                "message",
                ""
            )

        history =
            data.get(
                "history",
                []
            )


        if not isinstance(
            message,
            str
        ):

            return jsonify({
                "error":
                    "Message must be text."
            }), 400


        message =
            message.strip()


        if not message:

            return jsonify({
                "error":
                    "Please enter a message."
            }), 400


        if len(message) >
            MAX_MESSAGE_LENGTH:

            return jsonify({
                "error":
                    "Message is too long."
            }), 400


        if not isinstance(
            history,
            list
        ):

            history = []


        # Limit incoming history.
        history =
            history[
                -MAX_HISTORY_ITEMS:
            ]


        answer =
            ask_gemini(
                message,
                history
            )


        return jsonify({
            "answer": answer
        })


    except RuntimeError as exc:

        return jsonify({
            "error": str(exc)
        }), 500


    except Exception as exc:

        return jsonify({
            "error":
                "Unexpected server error: " +
                str(exc)
        }), 500


# ============================================================
# LOCAL SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
