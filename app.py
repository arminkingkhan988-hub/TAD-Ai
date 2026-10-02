import os
import json
import time
import base64
import mimetypes
import urllib.request
import urllib.error

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# =========================================================
# CONFIG
# =========================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash").strip()

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    + GEMINI_MODEL
    + ":generateContent"
)

MAX_MESSAGE_LENGTH = 12000
MAX_HISTORY = 16
MAX_FILE_BYTES = 12 * 1024 * 1024


# =========================================================
# MEDICAL SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are MedAI, a multilingual medical information assistant.

IMPORTANT SAFETY RULES:
- You provide general medical information, not a medical diagnosis.
- Never claim certainty about a diagnosis.
- Do not replace a doctor, nurse, pharmacist, or emergency service.
- Never invent laboratory values, medical records, medications, or sources.
- Do not give dangerous instructions.
- If a user describes a possible emergency, clearly recommend immediate
  emergency medical care.
- If a medication is discussed, explain general uses, common precautions,
  and advise checking the official label or a pharmacist/doctor.
- Do not tell users to stop or change prescribed treatment without
  professional medical advice.
- For children, pregnancy, severe symptoms, allergies, or serious
  conditions, recommend professional medical evaluation.

RESPONSE STYLE:
- Answer in the same language as the user when possible.
- Support Pashto, Dari, English, and mixed-language questions.
- Use clear headings and bullet points.
- Keep normal answers concise but useful.
- For symptoms use:
  Possible explanations
  Warning signs
  What to do now
  When to see a doctor
- For medicine questions use:
  What it is
  Common uses
  Important precautions
  When to contact a professional
- For lab reports:
  Explain each provided result in simple language.
  Do not diagnose from one number alone.
  Mention that reference ranges differ by laboratory.
- For uploaded images/documents:
  Only describe what can actually be read or observed.
  If the image is unclear, say so.
"""


# =========================================================
# HELPERS
# =========================================================

def clean_history(history):
    """Keep only safe, small conversation history."""
    if not isinstance(history, list):
        return []

    result = []

    for item in history[-MAX_HISTORY:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        text = str(item.get("text", "")).strip()

        if role not in ("user", "assistant"):
            continue

        if not text:
            continue

        result.append({
            "role": role,
            "text": text[:6000]
        })

    return result


def make_text_contents(message, history):
    contents = []

    for item in clean_history(history):
        contents.append({
            "role": "user" if item["role"] == "user" else "model",
            "parts": [
                {
                    "text": item["text"]
                }
            ]
        })

    contents.append({
        "role": "user",
        "parts": [
            {
                "text": message
            }
        ]
    })

    return contents


def extract_gemini_text(data):
    candidates = data.get("candidates") or []

    if not candidates:
        return ""

    candidate = candidates[0] or {}
    content = candidate.get("content") or {}
    parts = content.get("parts") or []

    text_parts = []

    for part in parts:
        if isinstance(part, dict) and part.get("text"):
            text_parts.append(str(part["text"]))

    return "\n".join(text_parts).strip()


def gemini_request(payload, retries=3):
    """Gemini REST request with retry for temporary errors."""

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing in Vercel Environment Variables."
        )

    body = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY,
    }

    last_error = "Unknown Gemini error"

    for attempt in range(retries):

        req = urllib.request.Request(
            GEMINI_URL,
            data=body,
            headers=headers,
            method="POST",
        )

        try:

            with urllib.request.urlopen(req, timeout=60) as response:
                raw = response.read().decode("utf-8")

            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                raise RuntimeError(
                    "Gemini returned invalid JSON."
                )

        except urllib.error.HTTPError as error:

            try:
                detail = error.read().decode("utf-8")
            except Exception:
                detail = ""

            last_error = (
                f"Gemini API HTTP {error.code}"
                + (f": {detail[:700]}" if detail else "")
            )

            # Temporary server/rate-limit errors.
            if error.code in (429, 500, 502, 503, 504):
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue

            if error.code == 400:
                raise RuntimeError(
                    "Gemini rejected the request. "
                    + detail[:500]
                )

            if error.code == 401 or error.code == 403:
                raise RuntimeError(
                    "Gemini API key is invalid or does not have access."
                )

            raise RuntimeError(last_error)

        except urllib.error.URLError as error:

            last_error = f"Gemini connection error: {error}"

            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue

            raise RuntimeError(last_error)

        except TimeoutError:

            last_error = "Gemini request timed out."

            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue

            raise RuntimeError(last_error)

    raise RuntimeError(last_error)


# =========================================================
# TEXT CHAT
# =========================================================

def ask_gemini(message, history=None):

    payload = {
        "system_instruction": {
            "parts": [
                {
                    "text": SYSTEM_PROMPT
                }
            ]
        },

        "contents": make_text_contents(
            message,
            history or []
        ),

        "generationConfig": {
            "maxOutputTokens": 1800,
            "thinkingConfig": {
                "thinkingLevel": "medium"
            }
        }
    }

    data = gemini_request(payload)

    answer = extract_gemini_text(data)

    if not answer:
        raise RuntimeError(
            "Gemini returned an empty answer."
        )

    return answer


# =========================================================
# MULTIMODAL CHAT
# IMAGE / PDF
# =========================================================

def ask_gemini_with_file(message, file_bytes, filename, mimetype):

    if not file_bytes:
        raise RuntimeError("Uploaded file is empty.")

    if len(file_bytes) > MAX_FILE_BYTES:
        raise RuntimeError(
            "File is too large. Maximum allowed size is 12 MB."
        )

    if not mimetype:
        mimetype = (
            mimetypes.guess_type(filename)[0]
            or "application/octet-stream"
        )

    allowed = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
        "image/heif",
        "application/pdf",
    }

    if mimetype not in allowed:
        raise RuntimeError(
            "Supported files: JPG, PNG, WEBP, HEIC, HEIF and PDF."
        )

    encoded = base64.b64encode(file_bytes).decode("utf-8")

    prompt = f"""
{SYSTEM_PROMPT}

The user uploaded this file:
{filename}

User request:
{message}

Analyze the uploaded file only as far as the visible/readable content allows.
Clearly mention uncertainty if something cannot be read.
"""

    payload = {
        "system_instruction": {
            "parts": [
                {
                    "text": SYSTEM_PROMPT
                }
            ]
        },

        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    },
                    {
                        "inline_data": {
                            "mime_type": mimetype,
                            "data": encoded
                        }
                    }
                ]
            }
        ],

        "generationConfig": {
            "maxOutputTokens": 2000,
            "thinkingConfig": {
                "thinkingLevel": "medium"
            }
        }
    }

    data = gemini_request(payload)

    answer = extract_gemini_text(data)

    if not answer:
        raise RuntimeError(
            "Gemini could not analyze this file."
        )

    return answer


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template_string(HTML)


# =========================================================
# HEALTH
# =========================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "service": "MedAI",
        "gemini_configured": bool(GEMINI_API_KEY),
        "model": GEMINI_MODEL
    })


# =========================================================
# CHAT API
# =========================================================

@app.route("/api/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json(silent=True) or {}

        message = str(
            data.get("message", "")
        ).strip()

        history = data.get("history", [])

        if not message:
            return jsonify({
                "error": "Please enter a message."
            }), 400

        if len(message) > MAX_MESSAGE_LENGTH:
            return jsonify({
                "error": "Message is too long."
            }), 400

        answer = ask_gemini(
            message,
            history
        )

        return jsonify({
            "answer": answer,
            "model": GEMINI_MODEL
        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


# =========================================================
# FILE CHAT API
# =========================================================

@app.route("/api/analyze", methods=["POST"])
def analyze_file():

    try:

        message = (
            request.form.get("message")
            or "Please explain this medical document."
        ).strip()

        if len(message) > 6000:
            return jsonify({
                "error": "Request is too long."
            }), 400

        uploaded = request.files.get("file")

        if not uploaded:
            return jsonify({
                "error": "No file was uploaded."
            }), 400

        filename = uploaded.filename or "uploaded-file"

        file_bytes = uploaded.read()

        answer = ask_gemini_with_file(
            message,
            file_bytes,
            filename,
            uploaded.mimetype
        )

        return jsonify({
            "answer": answer,
            "filename": filename,
            "model": GEMINI_MODEL
        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


# =========================================================
# FRONTEND
# =========================================================

HTML = r"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>MedAI</title>

<style>

:root {
    --bg: #ffffff;
    --panel: #f7f7f8;
    --card: #ffffff;
    --text: #171717;
    --muted: #6b7280;
    --border: #e5e7eb;
    --primary: #10a37f;
    --primary-dark: #087f63;
    --user: #f0f2f5;
    --danger: #dc2626;
}

body.dark {
    --bg: #212121;
    --panel: #171717;
    --card: #212121;
    --text: #f5f5f5;
    --muted: #a1a1aa;
    --border: #3f3f46;
    --user: #303030;
}

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    width: 100%;
    height: 100%;
}

body {
    font-family:
        Inter,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    background: var(--bg);
    color: var(--text);
    overflow: hidden;
}

button,
textarea,
input {
    font: inherit;
}

button {
    cursor: pointer;
}


/* =====================================================
   APP
===================================================== */

.app {
    display: flex;
    height: 100vh;
}


/* =====================================================
   SIDEBAR
===================================================== */

.sidebar {
    width: 270px;
    background: var(--panel);
    border-right: 1px solid var(--border);
    padding: 15px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    flex-shrink: 0;
}

.logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px;
    font-size: 21px;
    font-weight: 800;
}

.logo-icon {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    background: var(--primary);
    color: white;
    display: grid;
    place-items: center;
    font-size: 21px;
}

.new-chat {
    width: 100%;
    border: 1px solid var(--border);
    background: var(--card);
    color: var(--text);
    padding: 12px;
    border-radius: 10px;
}

.new-chat:hover {
    background: var(--user);
}

.history-title {
    color: var(--muted);
    font-size: 11px;
    padding: 8px;
    text-transform: uppercase;
}

.history {
    flex: 1;
    overflow-y: auto;
}

.history-item {
    padding: 10px;
    border-radius: 9px;
    font-size: 13px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.history-item:hover {
    background: var(--user);
}

.side-actions {
    display: grid;
    gap: 5px;
}

.side-button {
    border: 0;
    background: transparent;
    color: var(--text);
    text-align: left;
    padding: 10px;
    border-radius: 8px;
}

.side-button:hover {
    background: var(--user);
}


/* =====================================================
   MAIN
===================================================== */

.main {
    min-width: 0;
    flex: 1;
    display: flex;
    flex-direction: column;
}

.topbar {
    height: 62px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 18px;
}

.top-title {
    font-weight: 700;
}

.top-status {
    color: var(--muted);
    font-size: 12px;
    display: flex;
    align-items: center;
    gap: 7px;
}

.dot {
    width: 8px;
    height: 8px;
    background: #22c55e;
    border-radius: 50%;
}


/* =====================================================
   CHAT
===================================================== */

.chat {
    flex: 1;
    overflow-y: auto;
    padding: 30px 15px 180px;
}

.chat-inner {
    max-width: 900px;
    margin: auto;
}

.welcome {
    text-align: center;
    padding-top: 50px;
}

.welcome-logo {
    width: 75px;
    height: 75px;
    border-radius: 24px;
    background: var(--primary);
    color: white;
    display: grid;
    place-items: center;
    font-size: 35px;
    margin: auto auto 18px;
}

.welcome h1 {
    font-size: 32px;
    margin: 0 0 10px;
}

.welcome p {
    color: var(--muted);
    line-height: 1.6;
    margin: auto;
    max-width: 620px;
}


/* =====================================================
   QUICK ACTIONS
===================================================== */

.quick {
    display: grid;
    grid-template-columns:
        repeat(4, 1fr);

    gap: 10px;
    margin: 28px auto;
}

.quick button {
    border: 1px solid var(--border);
    background: var(--card);
    color: var(--text);
    border-radius: 14px;
    padding: 15px 10px;
}

.quick button:hover {
    border-color: var(--primary);
}

.quick-icon {
    font-size: 23px;
    margin-bottom: 6px;
}

.quick-text {
    font-size: 12px;
}


/* =====================================================
   MESSAGE
===================================================== */

.message {
    display: flex;
    gap: 13px;
    padding: 23px 8px;
    border-bottom: 1px solid var(--border);
}

.avatar {
    min-width: 35px;
    height: 35px;
    border-radius: 10px;
    display: grid;
    place-items: center;
}

.avatar.ai {
    background: var(--primary);
    color: white;
}

.avatar.user {
    background: #64748b;
    color: white;
}

.message-body {
    flex: 1;
    min-width: 0;
}

.message-name {
    font-weight: 700;
    margin-bottom: 6px;
}

.message-text {
    white-space: pre-wrap;
    line-height: 1.7;
    overflow-wrap: anywhere;
}

.message-actions {
    display: flex;
    gap: 5px;
    margin-top: 9px;
}

.message-actions button {
    border: 0;
    background: transparent;
    color: var(--muted);
    padding: 5px 8px;
    border-radius: 6px;
}

.message-actions button:hover {
    background: var(--user);
}


/* =====================================================
   INPUT
===================================================== */

.input-area {
    position: fixed;
    bottom: 0;
    left: 270px;
    right: 0;
    padding: 28px 15px 15px;
    background:
        linear-gradient(
            transparent,
            var(--bg) 30%
        );
}

.input-inner {
    max-width: 900px;
    margin: auto;
}

.input-box {
    display: flex;
    align-items: flex-end;
    gap: 5px;
    padding: 8px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 18px;
    box-shadow: 0 7px 30px rgba(0,0,0,.08);
}

textarea {
    flex: 1;
    resize: none;
    border: 0;
    outline: 0;
    background: transparent;
    color: var(--text);
    min-height: 45px;
    max-height: 160px;
    padding: 12px;
}

.input-button {
    width: 42px;
    height: 42px;
    border: 0;
    background: transparent;
    color: var(--muted);
    border-radius: 10px;
}

.input-button:hover {
    background: var(--user);
}

.send {
    background: var(--primary);
    color: white;
}

.send:hover {
    background: var(--primary-dark);
}

.disclaimer {
    text-align: center;
    color: var(--muted);
    font-size: 10px;
    margin-top: 8px;
}


/* =====================================================
   FILE
===================================================== */

.file-name {
    display: none;
    background: var(--user);
    padding: 8px 12px;
    border-radius: 9px;
    font-size: 12px;
    margin-bottom: 8px;
}

.file-name.show {
    display: block;
}


/* =====================================================
   EMERGENCY
===================================================== */

.emergency {
    margin: 20px auto;
    padding: 13px;
    border: 1px solid #fecaca;
    background: #fef2f2;
    color: #991b1b;
    border-radius: 12px;
    line-height: 1.5;
    max-width: 900px;
    font-size: 13px;
}

body.dark .emergency {
    background: #351c1c;
    color: #fecaca;
    border-color: #6b3030;
}


/* =====================================================
   MOBILE
===================================================== */

.mobile-menu {
    display: none;
    border: 0;
    background: transparent;
    color: var(--text);
    font-size: 22px;
}

@media (max-width: 800px) {

    .sidebar {
        position: fixed;
        z-index: 100;
        top: 0;
        bottom: 0;
        left: -280px;
        transition: .25s;
    }

    .sidebar.open {
        left: 0;
    }

    .mobile-menu {
        display: block;
    }

    .input-area {
        left: 0;
        padding: 20px 9px 10px;
    }

    .quick {
        grid-template-columns: repeat(2, 1fr);
    }

    .welcome {
        padding-top: 20px;
    }

    .welcome h1 {
        font-size: 26px;
    }

}

</style>

</head>

<body>

<div class="app">

<!-- ===================================================
     SIDEBAR
=================================================== -->

<aside class="sidebar" id="sidebar">

    <div class="logo">
        <div class="logo-icon">✚</div>
        MedAI
    </div>

    <button
        class="new-chat"
        onclick="newChat()">
        ＋ New chat
    </button>

    <div class="history-title">
        Recent chats
    </div>

    <div
        class="history"
        id="history">
    </div>

    <div class="side-actions">

        <button
            class="side-button"
            onclick="toggleDark()">
            🌙 Dark / Light
        </button>

        <button
            class="side-button"
            onclick="exportChat()">
            📥 Export chat
        </button>

        <button
            class="side-button"
            onclick="clearChat()">
            🗑 Clear chat
        </button>

    </div>

</aside>


<!-- ===================================================
     MAIN
=================================================== -->

<main class="main">

<header class="topbar">

    <button
        class="mobile-menu"
        onclick="toggleSidebar()">
        ☰
    </button>

    <div class="top-title">
        MedAI
    </div>

    <div class="top-status">
        <span class="dot"></span>
        Medical AI
    </div>

</header>


<section
    class="chat"
    id="chat">

<div class="chat-inner">

<!-- WELCOME -->

<div id="welcome">

    <div class="welcome">

        <div class="welcome-logo">
            ✚
        </div>

        <h1>
            How can MedAI help?
        </h1>

        <p>
            Ask about symptoms, medicines, laboratory
            reports, health information, or upload
            a medical image/PDF for explanation.
        </p>

    </div>


    <div class="quick">

        <button onclick="quickAsk(
            'Please help me understand my symptoms.'
        )">

            <div class="quick-icon">🩺</div>

            <div class="quick-text">
                Symptoms
            </div>

        </button>


        <button onclick="quickAsk(
            'Please explain this medicine, its common uses, precautions, and when to contact a professional.'
        )">

            <div class="quick-icon">💊</div>

            <div class="quick-text">
                Medicine
            </div>

        </button>


        <button onclick="quickAsk(
            'Please help me understand my laboratory report and explain the results in simple language.'
        )">

            <div class="quick-icon">🧪</div>

            <div class="quick-text">
                Lab Report
            </div>

        </button>


        <button onclick="quickAsk(
            'What symptoms can be signs of a medical emergency and require immediate care?'
        )">

            <div class="quick-icon">🚨</div>

            <div class="quick-text">
                Emergency
            </div>

        </button>

    </div>


    <div class="emergency">

        <strong>Medical notice:</strong>

        MedAI provides general medical information.
        It does not replace a qualified healthcare
        professional. If you have a medical emergency,
        seek immediate medical care.

    </div>

</div>


<!-- MESSAGES -->

<div id="messages"></div>

</div>

</section>


<!-- ===================================================
     INPUT
=================================================== -->

<div class="input-area">

<div class="input-inner">

<div
    id="fileName"
    class="file-name">
</div>

<div class="input-box">

<textarea
    id="input"
    rows="1"
    placeholder="Message MedAI..."
    onkeydown="keyDown(event)">
</textarea>


<button
    class="input-button"
    onclick="document.getElementById('file').click()"
    title="Upload image or PDF">
    📎
</button>

<input
    id="file"
    type="file"
    hidden
    accept=".jpg,.jpeg,.png,.webp,.heic,.heif,.pdf"
    onchange="fileSelected(this)"
>


<button
    class="input-button"
    onclick="voiceInput()"
    title="Voice input">
    🎙️
</button>


<button
    class="input-button"
    onclick="speakLast()"
    title="Read answer">
    🔊
</button>


<button
    class="input-button send"
    onclick="send()"
    title="Send">
    ➤
</button>

</div>


<div class="disclaimer">
    MedAI can make mistakes. Important medical decisions
    should be discussed with a qualified healthcare professional.
</div>

</div>

</div>

</main>

</div>


<script>

/* ======================================================
   STATE
====================================================== */

const STORAGE = "medai_messages_v3";
const DARK = "medai_dark_v3";

let messages = [];

const input =
    document.getElementById("input");

const messagesBox =
    document.getElementById("messages");

const welcome =
    document.getElementById("welcome");

const chat =
    document.getElementById("chat");

const fileInput =
    document.getElementById("file");

const fileName =
    document.getElementById("fileName");


/* ======================================================
   LOAD
====================================================== */

function load() {

    try {

        const saved =
            localStorage.getItem(STORAGE);

        if (saved) {
            messages = JSON.parse(saved);
        }

    } catch {

        messages = [];

    }

    if (
        localStorage.getItem(DARK)
        === "true"
    ) {
        document.body.classList.add("dark");
    }

    render();

}


/* ======================================================
   SAVE
====================================================== */

function save() {

    localStorage.setItem(
        STORAGE,
        JSON.stringify(messages.slice(-100))
    );

}


/* ======================================================
   RENDER
====================================================== */

function render() {

    messagesBox.innerHTML = "";

    welcome.style.display =
        messages.length
            ? "none"
            : "block";


    messages.forEach(
        (message, index) => {

            const row =
                document.createElement("div");

            row.className =
                "message";


            const avatar =
                document.createElement("div");

            avatar.className =
                "avatar " +
                (
                    message.role === "user"
                    ? "user"
                    : "ai"
                );

            avatar.textContent =
                message.role === "user"
                ? "👤"
                : "✚";


            const body =
                document.createElement("div");

            body.className =
                "message-body";


            const name =
                document.createElement("div");

            name.className =
                "message-name";

            name.textContent =
                message.role === "user"
                ? "You"
                : "MedAI";


            const text =
                document.createElement("div");

            text.className =
                "message-text";

            text.textContent =
                message.text;


            body.appendChild(name);
            body.appendChild(text);


            if (
                message.role === "assistant"
            ) {

                const actions =
                    document.createElement("div");

                actions.className =
                    "message-actions";


                const copy =
                    document.createElement("button");

                copy.textContent =
                    "📋 Copy";

                copy.onclick =
                    () => copyText(
                        message.text
                    );


                const speak =
                    document.createElement("button");

                speak.textContent =
                    "🔊 Read";

                speak.onclick =
                    () => speakText(
                        message.text
                    );


                actions.appendChild(copy);
                actions.appendChild(speak);

                body.appendChild(actions);

            }


            row.appendChild(avatar);
            row.appendChild(body);

            messagesBox.appendChild(row);

        }
    );


    renderHistory();

    scrollBottom();

}


/* ======================================================
   HISTORY
====================================================== */

function renderHistory() {

    const history =
        document.getElementById("history");

    history.innerHTML = "";

    messages
        .filter(
            m => m.role === "user"
        )
        .slice(-15)
        .reverse()
        .forEach(
            message => {

                const item =
                    document.createElement("div");

                item.className =
                    "history-item";

                item.textContent =
                    message.text
                        .replace(/\s+/g, " ")
                        .slice(0, 45);

                history.appendChild(item);

            }
        );

}


/* ======================================================
   SEND
====================================================== */

async function send() {

    const text =
        input.value.trim();

    const file =
        fileInput.files[0];


    if (!text && !file) {
        return;
    }


    const history =
        messages.slice(-16);


    if (text) {

        messages.push({
            role: "user",
            text: text
        });

    }


    if (file) {

        messages.push({
            role: "user",
            text:
                "📎 Uploaded: "
                + file.name
        });

    }


    input.value = "";

    resetFile();

    save();

    render();

    typing(true);


    try {

        let response;


        /* FILE */

        if (file) {

            const form =
                new FormData();

            form.append(
                "message",
                text ||
                "Please analyze this medical file."
            );

            form.append(
                "file",
                file
            );


            response =
                await fetch(
                    "/api/analyze",
                    {
                        method: "POST",
                        body: form
                    }
                );

        }

        /* NORMAL CHAT */

        else {

            response =
                await fetch(
                    "/api/chat",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            message: text,
                            history: history
                        })
                    }
                );

        }


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error
                || "Server error"
            );

        }


        messages.push({
            role: "assistant",
            text: data.answer
        });


        save();

        render();

    }

    catch (error) {

        messages.push({
            role: "assistant",
            text:
                "⚠️ MedAI could not complete the request.\n\n"
                + error.message
                + "\n\nPlease try again."
        });

        save();

        render();

    }

    finally {

        typing(false);

    }

}


/* ======================================================
   QUICK
====================================================== */

function quickAsk(text) {

    input.value = text;

    send();

}


/* ======================================================
   TYPING
====================================================== */

function typing(show) {

    const old =
        document.getElementById(
            "typing"
        );

    if (old) {
        old.remove();
    }


    if (!show) {
        return;
    }


    const row =
        document.createElement("div");

    row.id =
        "typing";

    row.className =
        "message";


    row.innerHTML = `
        <div class="avatar ai">✚</div>
        <div class="message-body">
            <div class="message-name">MedAI</div>
            <div class="message-text">
                Thinking...
            </div>
        </div>
    `;


    messagesBox.appendChild(row);

    scrollBottom();

}


/* ======================================================
   COPY
====================================================== */

async function copyText(text) {

    try {

        await navigator.clipboard.writeText(
            text
        );

    } catch {

        alert(
            "Copy is not supported by this browser."
        );

    }

}


/* ======================================================
   SPEECH
====================================================== */

function speakText(text) {

    if (
        !("speechSynthesis" in window)
    ) {

        alert(
            "Text-to-speech is not supported."
        );

        return;

    }


    speechSynthesis.cancel();

    const voice =
        new SpeechSynthesisUtterance(text);

    voice.rate = 0.95;

    speechSynthesis.speak(
        voice
    );

}


function speakLast() {

    const answers =
        messages.filter(
            m => m.role === "assistant"
        );

    if (!answers.length) {
        return;
    }

    speakText(
        answers[answers.length - 1].text
    );

}


/* ======================================================
   VOICE INPUT
====================================================== */

function voiceInput() {

    const Recognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;


    if (!Recognition) {

        alert(
            "Voice input is not supported in this browser."
        );

        return;

    }


    const recognition =
        new Recognition();


    recognition.lang =
        navigator.language || "en-US";

    recognition.interimResults =
        false;


    recognition.onresult =
        event => {

            input.value =
                event.results[0][0]
                    .transcript;

            resizeInput();

        };


    recognition.onerror =
        () => {

            input.placeholder =
                "Voice input failed.";

            setTimeout(
                () => {
                    input.placeholder =
                        "Message MedAI...";
                },
                1500
            );

        };


    recognition.start();

}


/* ======================================================
   FILE
====================================================== */

function fileSelected(element) {

    const file =
        element.files[0];

    if (!file) {
        return;
    }


    const max =
        12 * 1024 * 1024;


    if (file.size > max) {

        alert(
            "File is too large. Maximum size is 12 MB."
        );

        resetFile();

        return;

    }


    fileName.textContent =
        "📎 " + file.name;

    fileName.classList.add(
        "show"
    );

}


function resetFile() {

    fileInput.value = "";

    fileName.textContent = "";

    fileName.classList.remove(
        "show"
    );

}


/* ======================================================
   NEW CHAT
====================================================== */

function newChat() {

    messages = [];

    save();

    render();

    input.focus();

}


/* ======================================================
   CLEAR
====================================================== */

function clearChat() {

    if (
        confirm(
            "Clear all MedAI chat history?"
        )
    ) {

        newChat();

    }

}


/* ======================================================
   EXPORT
====================================================== */

function exportChat() {

    if (!messages.length) {

        alert(
            "There is no chat to export."
        );

        return;

    }


    let content =
        "MedAI Chat Export\n"
        + "=================\n\n";


    messages.forEach(
        message => {

            content +=
                (
                    message.role === "user"
                    ? "You"
                    : "MedAI"
                )
                + ":\n"
                + message.text
                + "\n\n";

        }
    );


    const blob =
        new Blob(
            [content],
            {
                type:
                    "text/plain;charset=utf-8"
            }
        );


    const url =
        URL.createObjectURL(blob);


    const link =
        document.createElement("a");

    link.href = url;

    link.download =
        "medai-chat.txt";

    link.click();

    URL.revokeObjectURL(url);

}


/* ======================================================
   DARK MODE
====================================================== */

function toggleDark() {

    document.body.classList.toggle(
        "dark"
    );


    localStorage.setItem(
        DARK,
        document.body.classList.contains(
            "dark"
        )
    );

}


/* ======================================================
   MOBILE
====================================================== */

function toggleSidebar() {

    document
        .getElementById("sidebar")
        .classList.toggle(
            "open"
        );

}


/* ======================================================
   KEYBOARD
====================================================== */

function keyDown(event) {

    if (
        event.key === "Enter"
        && !event.shiftKey
    ) {

        event.preventDefault();

        send();

    }

}


/* ======================================================
   RESIZE INPUT
====================================================== */

function resizeInput() {

    input.style.height =
        "auto";

    input.style.height =
        Math.min(
            input.scrollHeight,
            160
        ) + "px";

}


input.addEventListener(
    "input",
    resizeInput
);


/* ======================================================
   SCROLL
====================================================== */

function scrollBottom() {

    setTimeout(
        () => {

            chat.scrollTop =
                chat.scrollHeight;

        },
        40
    );

}


/* ======================================================
   START
====================================================== */

load();

</script>

</body>

</html>
"""


# =========================================================
# LOCAL DEVELOPMENT
# =========================================================

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
