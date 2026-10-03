import os
import base64
import requests
from flask import Flask, request, jsonify, render_template_string

# =========================================================
# MedAI - Flask + Gemini
# =========================================================

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    + GEMINI_MODEL
    + ":generateContent"
)


SYSTEM_PROMPT = """
You are MedAI, a helpful multilingual AI assistant.

IMPORTANT:
- Answer in the same language as the user's latest message.
- Support Pashto, Dari, and English.
- You can help with general questions, education, science, mathematics,
  programming, writing, history, business, technology, and medicine.
- Give clear, useful, structured answers.
- Do not pretend to be a doctor.
- For medical questions, provide general educational information, not a diagnosis.
- If symptoms may indicate an emergency, clearly recommend contacting local
  emergency medical services or going to an emergency department.
- Never claim certainty when information is incomplete.
- If an image is provided, carefully describe what can be observed and explain
  uncertainty. For medical images, do not provide a definitive diagnosis.
- Do not invent sources, test results, medications, or facts.
- When the user asks for code, provide complete and runnable code when practical.
- Be concise but helpful.
"""


# =========================================================
# Basic pages
# =========================================================

@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "MedAI"
    })


# =========================================================
# Gemini API
# =========================================================

@app.route("/api/chat", methods=["POST"])
def chat():
    if not GEMINI_API_KEY:
        return jsonify({
            "ok": False,
            "error": "GEMINI_API_KEY is not configured in Vercel."
        }), 500

    try:
        data = request.get_json(silent=True) or {}

        message = str(data.get("message", "")).strip()
        history = data.get("history", [])
        image_data = data.get("image")

        if not message and not image_data:
            return jsonify({
                "ok": False,
                "error": "Please enter a message or select an image."
            }), 400

        contents = []

        # Conversation context
        if isinstance(history, list):
            for item in history[-12:]:
                if not isinstance(item, dict):
                    continue

                role = item.get("role", "user")
                text = str(item.get("text", "")).strip()

                if not text:
                    continue

                gemini_role = "model" if role == "assistant" else "user"

                contents.append({
                    "role": gemini_role,
                    "parts": [
                        {
                            "text": text
                        }
                    ]
                })

        # Current message
        parts = []

        if message:
            parts.append({
                "text": message
            })

        # Optional image
        if image_data:
            try:
                if "," in image_data:
                    header, encoded = image_data.split(",", 1)
                    mime_type = "image/jpeg"

                    if "image/png" in header:
                        mime_type = "image/png"
                    elif "image/webp" in header:
                        mime_type = "image/webp"
                    elif "image/gif" in header:
                        mime_type = "image/gif"

                    # Validate base64
                    base64.b64decode(encoded, validate=True)

                    parts.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": encoded
                        }
                    })

            except Exception:
                return jsonify({
                    "ok": False,
                    "error": "The uploaded image could not be processed."
                }), 400

        contents.append({
            "role": "user",
            "parts": parts
        })

        payload = {
            "system_instruction": {
                "parts": [
                    {
                        "text": SYSTEM_PROMPT
                    }
                ]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.95,
                "maxOutputTokens": 2048
            }
        }

        response = requests.post(
            GEMINI_URL,
            params={
                "key": GEMINI_API_KEY
            },
            json=payload,
            timeout=55
        )

        if response.status_code != 200:
            try:
                error_data = response.json()
            except Exception:
                error_data = {
                    "message": response.text[:500]
                }

            return jsonify({
                "ok": False,
                "error": "Gemini API error.",
                "details": error_data
            }), response.status_code

        result = response.json()

        answer = ""

        candidates = result.get("candidates", [])

        if candidates:
            candidate = candidates[0]
            candidate_content = candidate.get("content", {})
            candidate_parts = candidate_content.get("parts", [])

            for part in candidate_parts:
                if isinstance(part, dict) and part.get("text"):
                    answer += part["text"]

        answer = answer.strip()

        if not answer:
            return jsonify({
                "ok": False,
                "error": "Gemini returned an empty response."
            }), 502

        return jsonify({
            "ok": True,
            "answer": answer,
            "model": GEMINI_MODEL
        })

    except requests.Timeout:
        return jsonify({
            "ok": False,
            "error": "The AI request timed out. Please try again."
        }), 504

    except requests.RequestException as exc:
        return jsonify({
            "ok": False,
            "error": "Network error while contacting Gemini.",
            "details": str(exc)
        }), 502

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": "Server error.",
            "details": str(exc)
        }), 500


# =========================================================
# Frontend
# =========================================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>MedAI</title>

<style>
* {
    box-sizing: border-box;
}

:root {
    --bg: #f5f7fb;
    --panel: #ffffff;
    --panel2: #eef2f7;
    --text: #172033;
    --muted: #6b7280;
    --border: #dfe4ec;
    --primary: #2563eb;
    --primary2: #1d4ed8;
    --user: #2563eb;
    --assistant: #ffffff;
    --danger: #dc2626;
    --shadow: 0 8px 30px rgba(0,0,0,.08);
}

body.dark {
    --bg: #0b1220;
    --panel: #111827;
    --panel2: #1f2937;
    --text: #f3f4f6;
    --muted: #9ca3af;
    --border: #374151;
    --primary: #3b82f6;
    --primary2: #2563eb;
    --assistant: #111827;
    --shadow: 0 8px 30px rgba(0,0,0,.30);
}

html,
body {
    margin: 0;
    padding: 0;
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

/* APP */

.app {
    display: flex;
    width: 100%;
    height: 100vh;
}

/* SIDEBAR */

.sidebar {
    width: 280px;
    min-width: 280px;
    height: 100vh;
    background: var(--panel);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    padding: 16px;
    z-index: 20;
}

.logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 800;
    font-size: 21px;
    margin-bottom: 18px;
}

.logo-icon {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    background: linear-gradient(135deg, #2563eb, #06b6d4);
    color: white;
    display: grid;
    place-items: center;
    font-size: 20px;
}

.new-chat {
    border: 1px solid var(--border);
    background: var(--panel2);
    color: var(--text);
    padding: 12px 14px;
    border-radius: 12px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 15px;
}

.new-chat:hover {
    border-color: var(--primary);
}

.sidebar-title {
    color: var(--muted);
    font-size: 12px;
    font-weight: 700;
    margin: 8px 4px;
    text-transform: uppercase;
}

.history {
    flex: 1;
    overflow-y: auto;
}

.history-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 10px;
    border-radius: 10px;
    cursor: pointer;
    margin-bottom: 4px;
    font-size: 13px;
}

.history-item:hover {
    background: var(--panel2);
}

.history-text {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.delete-history {
    border: 0;
    background: transparent;
    color: var(--muted);
    cursor: pointer;
}

.sidebar-bottom {
    border-top: 1px solid var(--border);
    padding-top: 12px;
}

.side-button {
    width: 100%;
    text-align: left;
    padding: 10px;
    border: 0;
    background: transparent;
    color: var(--text);
    border-radius: 9px;
    cursor: pointer;
}

.side-button:hover {
    background: var(--panel2);
}

/* MAIN */

.main {
    flex: 1;
    min-width: 0;
    height: 100vh;
    display: flex;
    flex-direction: column;
}

/* TOP BAR */

.topbar {
    height: 62px;
    min-height: 62px;
    border-bottom: 1px solid var(--border);
    background: var(--panel);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 18px;
}

.top-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.mobile-menu {
    display: none;
    border: 0;
    background: transparent;
    color: var(--text);
    font-size: 23px;
    cursor: pointer;
}

.status {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 13px;
    color: var(--muted);
}

.status-dot {
    width: 8px;
    height: 8px;
    background: #22c55e;
    border-radius: 50%;
}

.top-actions {
    display: flex;
    align-items: center;
    gap: 7px;
}

.icon-button {
    width: 38px;
    height: 38px;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--panel);
    color: var(--text);
    cursor: pointer;
}

/* CHAT */

.chat {
    flex: 1;
    overflow-y: auto;
    padding: 25px 18px 130px;
}

.chat-inner {
    width: min(900px, 100%);
    margin: auto;
}

.welcome {
    text-align: center;
    padding: 60px 10px 30px;
}

.welcome-icon {
    width: 72px;
    height: 72px;
    margin: auto;
    border-radius: 22px;
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, #2563eb, #06b6d4);
    color: white;
    font-size: 35px;
    box-shadow: var(--shadow);
}

.welcome h1 {
    margin: 18px 0 8px;
    font-size: 30px;
}

.welcome p {
    color: var(--muted);
    margin: 0 auto;
    max-width: 620px;
}

.quick-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    max-width: 700px;
    margin: 25px auto;
}

.quick {
    text-align: left;
    padding: 14px;
    background: var(--panel);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 13px;
    cursor: pointer;
}

.quick:hover {
    border-color: var(--primary);
}

.quick strong {
    display: block;
    margin-bottom: 5px;
}

.quick span {
    color: var(--muted);
    font-size: 12px;
}

/* MESSAGES */

.message {
    display: flex;
    margin-bottom: 20px;
    gap: 10px;
}

.message.user {
    justify-content: flex-end;
}

.avatar {
    width: 34px;
    height: 34px;
    min-width: 34px;
    border-radius: 10px;
    display: grid;
    place-items: center;
    background: var(--panel2);
    font-size: 16px;
}

.user .avatar {
    order: 2;
    background: var(--primary);
    color: white;
}

.bubble {
    max-width: 80%;
    padding: 13px 15px;
    border-radius: 15px;
    line-height: 1.6;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}

.user .bubble {
    background: var(--user);
    color: white;
    border-bottom-right-radius: 4px;
}

.assistant .bubble {
    background: var(--assistant);
    border: 1px solid var(--border);
    border-bottom-left-radius: 4px;
}

.message-actions {
    display: flex;
    gap: 5px;
    margin-top: 6px;
}

.small-button {
    border: 0;
    background: transparent;
    color: var(--muted);
    cursor: pointer;
    font-size: 12px;
}

.small-button:hover {
    color: var(--primary);
}

/* THINKING */

.typing {
    display: flex;
    gap: 5px;
    padding: 7px 2px;
}

.typing span {
    width: 7px;
    height: 7px;
    background: var(--muted);
    border-radius: 50%;
    animation: blink 1.2s infinite;
}

.typing span:nth-child(2) {
    animation-delay: .15s;
}

.typing span:nth-child(3) {
    animation-delay: .30s;
}

@keyframes blink {
    0%, 80%, 100% {
        opacity: .3;
        transform: translateY(0);
    }
    40% {
        opacity: 1;
        transform: translateY(-4px);
    }
}

/* IMAGE PREVIEW */

.preview {
    display: none;
    width: min(900px, 100%);
    margin: 0 auto 8px;
    padding: 8px;
}

.preview-box {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 6px;
}

.preview img {
    width: 60px;
    height: 60px;
    object-fit: cover;
    border-radius: 7px;
}

.remove-image {
    border: 0;
    background: transparent;
    color: var(--danger);
    cursor: pointer;
}

/* COMPOSER */

.composer-area {
    position: fixed;
    bottom: 0;
    right: 0;
    left: 280px;
    background: linear-gradient(
        to top,
        var(--bg) 72%,
        transparent
    );
    padding: 15px 18px 17px;
}

.composer {
    width: min(900px, 100%);
    margin: auto;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 17px;
    box-shadow: var(--shadow);
    padding: 9px;
}

.input-row {
    display: flex;
    align-items: flex-end;
    gap: 7px;
}

#messageInput {
    flex: 1;
    resize: none;
    border: 0;
    outline: 0;
    background: transparent;
    color: var(--text);
    padding: 11px;
    font-family: inherit;
    font-size: 15px;
    max-height: 150px;
}

#messageInput::placeholder {
    color: var(--muted);
}

.send-button {
    width: 43px;
    height: 43px;
    border: 0;
    border-radius: 12px;
    background: var(--primary);
    color: white;
    cursor: pointer;
    font-size: 17px;
}

.send-button:hover {
    background: var(--primary2);
}

.send-button:disabled {
    opacity: .5;
    cursor: not-allowed;
}

.composer-tools {
    display: flex;
    gap: 5px;
    padding-top: 4px;
}

.tool-button {
    border: 0;
    background: transparent;
    color: var(--muted);
    cursor: pointer;
    padding: 7px;
    border-radius: 8px;
}

.tool-button:hover {
    background: var(--panel2);
    color: var(--text);
}

.disclaimer {
    text-align: center;
    color: var(--muted);
    font-size: 10px;
    margin-top: 7px;
}

/* MODAL */

.modal {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.55);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 100;
    padding: 20px;
}

.modal.show {
    display: flex;
}

.modal-box {
    width: min(520px, 100%);
    max-height: 85vh;
    overflow-y: auto;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 17px;
    padding: 20px;
    box-shadow: var(--shadow);
}

.modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.modal-header h2 {
    margin: 0;
}

.close {
    border: 0;
    background: transparent;
    color: var(--muted);
    font-size: 22px;
    cursor: pointer;
}

.reminder-form {
    display: grid;
    gap: 10px;
    margin-top: 15px;
}

.reminder-form input {
    width: 100%;
    padding: 11px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text);
}

.primary-button {
    border: 0;
    background: var(--primary);
    color: white;
    padding: 11px;
    border-radius: 10px;
    cursor: pointer;
}

.reminder-item {
    margin-top: 10px;
    padding: 10px;
    background: var(--panel2);
    border-radius: 10px;
    display: flex;
    justify-content: space-between;
    gap: 8px;
}

/* MOBILE */

@media (max-width: 760px) {
    .sidebar {
        position: fixed;
        left: -290px;
        top: 0;
        transition: left .2s ease;
        box-shadow: var(--shadow);
    }

    .sidebar.open {
        left: 0;
    }

    .mobile-menu {
        display: block;
    }

    .composer-area {
        left: 0;
        padding: 9px;
    }

    .chat {
        padding: 18px 10px 125px;
    }

    .bubble {
        max-width: 88%;
    }

    .quick-grid {
        grid-template-columns: 1fr;
    }

    .welcome {
        padding-top: 35px;
    }

    .welcome h1 {
        font-size: 25px;
    }
}
</style>
</head>

<body>

<div class="app">

    <!-- SIDEBAR -->
    <aside class="sidebar" id="sidebar">

        <div class="logo">
            <div class="logo-icon">⚕</div>
            <span>MedAI</span>
        </div>

        <button class="new-chat" onclick="newChat()">
            ＋ New Chat
        </button>

        <div class="sidebar-title">
            Chat History
        </div>

        <div class="history" id="historyList"></div>

        <div class="sidebar-bottom">

            <button class="side-button" onclick="openReminders()">
                ⏰ Reminders
            </button>

            <button class="side-button" onclick="exportChat()">
                📤 Export Chat
            </button>

            <button class="side-button" onclick="clearAllChats()">
                🗑️ Clear History
            </button>

        </div>
    </aside>

    <!-- MAIN -->
    <main class="main">

        <header class="topbar">

            <div class="top-left">

                <button
                    class="mobile-menu"
                    onclick="toggleSidebar()"
                >
                    ☰
                </button>

                <div class="status">
                    <span class="status-dot"></span>
                    MedAI Online
                </div>

            </div>

            <div class="top-actions">

                <button
                    class="icon-button"
                    title="Dark / Light"
                    onclick="toggleTheme()"
                >
                    🌙
                </button>

                <button
                    class="icon-button"
                    title="New Chat"
                    onclick="newChat()"
                >
                    ＋
                </button>

            </div>

        </header>

        <section class="chat" id="chat">

            <div class="chat-inner" id="chatInner">

                <div class="welcome" id="welcome">

                    <div class="welcome-icon">
                        ⚕
                    </div>

                    <h1>How can I help you?</h1>

                    <p>
                        MedAI can help with medicine, education,
                        science, coding, mathematics, writing and
                        general questions.
                    </p>

                    <div class="quick-grid">

                        <button
                            class="quick"
                            onclick="quickPrompt('Explain this medical topic in simple language.')"
                        >
                            <strong>🩺 Medical</strong>
                            <span>General health information</span>
                        </button>

                        <button
                            class="quick"
                            onclick="quickPrompt('Teach me this topic step by step.')"
                        >
                            <strong>📚 Education</strong>
                            <span>Learn difficult topics</span>
                        </button>

                        <button
                            class="quick"
                            onclick="quickPrompt('Help me write clean and working code.')"
                        >
                            <strong>💻 Coding</strong>
                            <span>Programming assistance</span>
                        </button>

                        <button
                            class="quick"
                            onclick="quickPrompt('Solve this math problem and explain every step.')"
                        >
                            <strong>🧮 Mathematics</strong>
                            <span>Step-by-step solutions</span>
                        </button>

                    </div>

                </div>

            </div>

        </section>

        <!-- IMAGE PREVIEW -->
        <div class="preview" id="imagePreview">

            <div class="preview-box">

                <img id="previewImage" alt="Selected image">

                <button
                    class="remove-image"
                    onclick="removeImage()"
                >
                    ✕
                </button>

            </div>

        </div>

        <!-- COMPOSER -->
        <div class="composer-area">

            <div class="composer">

                <div class="input-row">

                    <textarea
                        id="messageInput"
                        rows="1"
                        placeholder="Message MedAI..."
                        onkeydown="handleKey(event)"
                        oninput="autoResize(this)"
                    ></textarea>

                    <button
                        class="send-button"
                        id="sendButton"
                        onclick="sendMessage()"
                    >
                        ➤
                    </button>

                </div>

                <div class="composer-tools">

                    <button
                        class="tool-button"
                        title="Upload image"
                        onclick="document.getElementById('imageInput').click()"
                    >
                        🖼️
                    </button>

                    <button
                        class="tool-button"
                        title="Voice input"
                        onclick="startVoice()"
                    >
                        🎤
                    </button>

                    <button
                        class="tool-button"
                        title="Reminders"
                        onclick="openReminders()"
                    >
                        ⏰
                    </button>

                </div>

            </div>

            <div class="disclaimer">
                MedAI provides general information and is not a substitute
                for professional medical care.
            </div>

        </div>

    </main>

</div>


<input
    type="file"
    id="imageInput"
    accept="image/*"
    style="display:none"
    onchange="handleImage(event)"
>


<!-- REMINDERS MODAL -->

<div class="modal" id="reminderModal">

    <div class="modal-box">

        <div class="modal-header">

            <h2>⏰ Reminders</h2>

            <button
                class="close"
                onclick="closeReminders()"
            >
                ✕
            </button>

        </div>

        <div class="reminder-form">

            <input
                id="reminderText"
                placeholder="Reminder text"
            >

            <input
                id="reminderDate"
                type="datetime-local"
            >

            <button
                class="primary-button"
                onclick="addReminder()"
            >
                Add Reminder
            </button>

        </div>

        <div id="reminderList"></div>

    </div>

</div>


<script>
/* =========================================================
   STATE
   ========================================================= */

let messages = [];
let selectedImage = null;
let isSending = false;
let currentChatId = null;


/* =========================================================
   STORAGE
   ========================================================= */

const CHAT_KEY = "medai_chats_v1";
const THEME_KEY = "medai_theme_v1";
const REMINDER_KEY = "medai_reminders_v1";


function getChats() {
    try {
        return JSON.parse(localStorage.getItem(CHAT_KEY) || "[]");
    } catch (error) {
        return [];
    }
}


function saveChats(chats) {
    localStorage.setItem(CHAT_KEY, JSON.stringify(chats));
}


function getReminders() {
    try {
        return JSON.parse(
            localStorage.getItem(REMINDER_KEY) || "[]"
        );
    } catch (error) {
        return [];
    }
}


function saveReminders(items) {
    localStorage.setItem(
        REMINDER_KEY,
        JSON.stringify(items)
    );
}


/* =========================================================
   INIT
   ========================================================= */

document.addEventListener("DOMContentLoaded", function() {

    loadTheme();
    renderHistory();
    renderReminders();

    const saved = sessionStorage.getItem("medai_current_chat");

    if (saved) {
        try {
            messages = JSON.parse(saved);
            renderMessages();
        } catch (error) {
            messages = [];
        }
    }

});


/* =========================================================
   THEME
   ========================================================= */

function loadTheme() {

    const theme = localStorage.getItem(THEME_KEY);

    if (theme === "dark") {
        document.body.classList.add("dark");
    }
}


function toggleTheme() {

    document.body.classList.toggle("dark");

    const dark = document.body.classList.contains("dark");

    localStorage.setItem(
        THEME_KEY,
        dark ? "dark" : "light"
    );
}


/* =========================================================
   SIDEBAR
   ========================================================= */

function toggleSidebar() {
    document
        .getElementById("sidebar")
        .classList.toggle("open");
}


/* =========================================================
   NEW CHAT
   ========================================================= */

function newChat() {

    messages = [];
    selectedImage = null;
    currentChatId = null;

    sessionStorage.removeItem("medai_current_chat");

    removeImage();
    renderMessages();

    document
        .getElementById("messageInput")
        .focus();

    document
        .getElementById("sidebar")
        .classList.remove("open");
}


/* =========================================================
   MESSAGE RENDER
   ========================================================= */

function renderMessages() {

    const container = document.getElementById("chatInner");

    container.innerHTML = "";

    if (messages.length === 0) {

        container.innerHTML = `
            <div class="welcome" id="welcome">

                <div class="welcome-icon">⚕</div>

                <h1>How can I help you?</h1>

                <p>
                    Ask MedAI anything about medicine, education,
                    science, coding, mathematics, writing and more.
                </p>

                <div class="quick-grid">

                    <button
                        class="quick"
                        onclick="quickPrompt('Explain this medical topic in simple language.')"
                    >
                        <strong>🩺 Medical</strong>
                        <span>General health information</span>
                    </button>

                    <button
                        class="quick"
                        onclick="quickPrompt('Teach me this topic step by step.')"
                    >
                        <strong>📚 Education</strong>
                        <span>Learn difficult topics</span>
                    </button>

                    <button
                        class="quick"
                        onclick="quickPrompt('Help me write clean and working code.')"
                    >
                        <strong>💻 Coding</strong>
                        <span>Programming assistance</span>
                    </button>

                    <button
                        class="quick"
                        onclick="quickPrompt('Solve this math problem and explain every step.')"
                    >
                        <strong>🧮 Mathematics</strong>
                        <span>Step-by-step solutions</span>
                    </button>

                </div>

            </div>
        `;

        return;
    }

    messages.forEach(function(message, index) {

        addMessageElement(
            message.role,
            message.text,
            index
        );

    });

    scrollToBottom();
}


function addMessageElement(role, text, index) {

    const container = document.getElementById("chatInner");

    const wrapper = document.createElement("div");

    wrapper.className =
        "message " +
        (role === "user" ? "user" : "assistant");

    const avatar = document.createElement("div");

    avatar.className = "avatar";
    avatar.textContent =
        role === "user" ? "👤" : "⚕";

    const content = document.createElement("div");

    const bubble = document.createElement("div");

    bubble.className = "bubble";
    bubble.textContent = text;

    content.appendChild(bubble);

    if (role === "assistant") {

        const actions = document.createElement("div");

        actions.className = "message-actions";

        const copyButton = document.createElement("button");

        copyButton.className = "small-button";
        copyButton.textContent = "Copy";

        copyButton.onclick = function() {
            copyText(text);
        };

        const speakButton = document.createElement("button");

        speakButton.className = "small-button";
        speakButton.textContent = "🔊 Speak";

        speakButton.onclick = function() {
            speak(text);
        };

        const favoriteButton = document.createElement("button");

        favoriteButton.className = "small-button";
        favoriteButton.textContent = "⭐ Save";

        favoriteButton.onclick = function() {
            favoriteAnswer(text);
        };

        actions.appendChild(copyButton);
        actions.appendChild(speakButton);
        actions.appendChild(favoriteButton);

        content.appendChild(actions);
    }

    wrapper.appendChild(avatar);
    wrapper.appendChild(content);

    container.appendChild(wrapper);
}


/* =========================================================
   SEND
   ========================================================= */

async function sendMessage() {

    if (isSending) {
        return;
    }

    const input = document.getElementById("messageInput");
    const text = input.value.trim();

    if (!text && !selectedImage) {
        return;
    }

    isSending = true;

    document.getElementById("sendButton").disabled = true;

    const historyForApi = messages.slice(-12).map(function(item) {
        return {
            role: item.role,
            text: item.text
        };
    });

    const userText = text || "Please analyze this image.";

    messages.push({
        role: "user",
        text: userText
    });

    input.value = "";
    autoResize(input);

    renderMessages();

    showTyping();

    const imageToSend = selectedImage;

    removeImage();

    try {

        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: userText,
                history: historyForApi,
                image: imageToSend
            })
        });

        const data = await response.json();

        removeTyping();

        if (!response.ok || !data.ok) {

            const errorMessage =
                data.error ||
                "Something went wrong. Please try again.";

            messages.push({
                role: "assistant",
                text: "⚠️ " + errorMessage
            });

        } else {

            messages.push({
                role: "assistant",
                text: data.answer
            });

            saveCurrentChat();

        }

    } catch (error) {

        removeTyping();

        messages.push({
            role: "assistant",
            text:
                "⚠️ Connection error. Please check your internet connection and try again."
        });

    }

    isSending = false;

    document.getElementById("sendButton").disabled = false;

    saveCurrentChat();
    renderMessages();
}


/* =========================================================
   TYPING
   ========================================================= */

function showTyping() {

    const container = document.getElementById("chatInner");

    const wrapper = document.createElement("div");

    wrapper.id = "typingMessage";
    wrapper.className = "message assistant";

    wrapper.innerHTML = `
        <div class="avatar">⚕</div>
        <div class="bubble">
            <div class="typing">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    container.appendChild(wrapper);

    scrollToBottom();
}


function removeTyping() {

    const typing =
        document.getElementById("typingMessage");

    if (typing) {
        typing.remove();
    }
}


/* =========================================================
   CHAT STORAGE
   ========================================================= */

function saveCurrentChat() {

    if (messages.length === 0) {
        return;
    }

    sessionStorage.setItem(
        "medai_current_chat",
        JSON.stringify(messages)
    );

    const chats = getChats();

    let chatId = currentChatId;

    if (!chatId) {
        chatId =
            Date.now().toString();

        currentChatId = chatId;
    }

    const firstUser =
        messages.find(function(item) {
            return item.role === "user";
        });

    const title =
        firstUser
            ? firstUser.text.substring(0, 60)
            : "New Chat";

    const existingIndex =
        chats.findIndex(function(item) {
            return item.id === chatId;
        });

    const chatObject = {
        id: chatId,
        title: title,
        messages: messages,
        updated: Date.now()
    };

    if (existingIndex >= 0) {
        chats[existingIndex] = chatObject;
    } else {
        chats.unshift(chatObject);
    }

    saveChats(chats.slice(0, 50));

    renderHistory();
}


function renderHistory() {

    const container =
        document.getElementById("historyList");

    const chats = getChats();

    container.innerHTML = "";

    chats.forEach(function(chat) {

        const item =
            document.createElement("div");

        item.className = "history-item";

        const text =
            document.createElement("div");

        text.className = "history-text";
        text.textContent = chat.title;

        text.onclick = function() {
            loadChat(chat.id);
        };

        const deleteButton =
            document.createElement("button");

        deleteButton.className =
            "delete-history";

        deleteButton.textContent = "✕";

        deleteButton.onclick = function(event) {

            event.stopPropagation();

            deleteChat(chat.id);
        };

        item.appendChild(text);
        item.appendChild(deleteButton);

        container.appendChild(item);
    });
}


function loadChat(id) {

    const chats = getChats();

    const chat =
        chats.find(function(item) {
            return item.id === id;
        });

    if (!chat) {
        return;
    }

    currentChatId = id;

    messages =
        Array.isArray(chat.messages)
            ? chat.messages
            : [];

    sessionStorage.setItem(
        "medai_current_chat",
        JSON.stringify(messages)
    );

    renderMessages();

    document
        .getElementById("sidebar")
        .classList.remove("open");
}


function deleteChat(id) {

    const chats =
        getChats().filter(function(item) {
            return item.id !== id;
        });

    saveChats(chats);

    if (currentChatId === id) {
        newChat();
    }

    renderHistory();
}


function clearAllChats() {

    const confirmed =
        confirm(
            "Delete all saved chat history?"
        );

    if (!confirmed) {
        return;
    }

    localStorage.removeItem(CHAT_KEY);

    newChat();

    renderHistory();
}


/* =========================================================
   IMAGE
   ========================================================= */

function handleImage(event) {

    const file =
        event.target.files[0];

    if (!file) {
        return;
    }

    if (!file.type.startsWith("image/")) {
        alert("Please select an image file.");
        return;
    }

    if (file.size > 8 * 1024 * 1024) {
        alert("Please select an image smaller than 8 MB.");
        return;
    }

    const reader =
        new FileReader();

    reader.onload = function(e) {

        selectedImage =
            e.target.result;

        document.getElementById(
            "previewImage"
        ).src = selectedImage;

        document.getElementById(
            "imagePreview"
        ).style.display = "block";
    };

    reader.readAsDataURL(file);

    event.target.value = "";
}


function removeImage() {

    selectedImage = null;

    document.getElementById(
        "imagePreview"
    ).style.display = "none";

    document.getElementById(
        "previewImage"
    ).src = "";
}


/* =========================================================
   VOICE INPUT
   ========================================================= */

function startVoice() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {

        alert(
            "Voice input is not supported by this browser. Try Chrome or Edge."
        );

        return;
    }

    const recognition =
        new SpeechRecognition();

    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.continuous = false;

    recognition.onstart = function() {
        alert("Listening... Speak now.");
    };

    recognition.onresult = function(event) {

        const transcript =
            event.results[0][0].transcript;

        const input =
            document.getElementById("messageInput");

        input.value =
            transcript;

        autoResize(input);
    };

    recognition.onerror = function() {
        alert("Voice input could not be started.");
    };

    recognition.start();
}


/* =========================================================
   VOICE OUTPUT
   ========================================================= */

function speak(text) {

    if (!("speechSynthesis" in window)) {

        alert(
            "Voice output is not supported by this browser."
        );

        return;
    }

    window.speechSynthesis.cancel();

    const utterance =
        new SpeechSynthesisUtterance(text);

    utterance.rate = 1;
    utterance.pitch = 1;

    window.speechSynthesis.speak(
        utterance
    );
}


/* =========================================================
   COPY
   ========================================================= */

async function copyText(text) {

    try {

        await navigator.clipboard.writeText(text);

        alert("Copied.");

    } catch (error) {

        alert("Could not copy the text.");
    }
}


/* =========================================================
   FAVORITES
   ========================================================= */

function favoriteAnswer(text) {

    const key =
        "medai_favorites_v1";

    let favorites = [];

    try {
        favorites =
            JSON.parse(
                localStorage.getItem(key) || "[]"
            );
    } catch (error) {
        favorites = [];
    }

    if (!favorites.includes(text)) {
        favorites.push(text);
    }

    localStorage.setItem(
        key,
        JSON.stringify(favorites)
    );

    alert("Saved to favorites.");
}


/* =========================================================
   EXPORT
   ========================================================= */

function exportChat() {

    if (messages.length === 0) {
        alert("There is no chat to export.");
        return;
    }

    let output =
        "MedAI Conversation\n";
    output +=
        "===================\n\n";

    messages.forEach(function(item) {

        output +=
            (item.role === "user"
                ? "You"
                : "MedAI") +
            ":\n";

        output +=
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

    const link =
        document.createElement("a");

    link.href = url;
    link.download =
        "medai-chat.txt";

    document.body.appendChild(link);

    link.click();

    link.remove();

    URL.revokeObjectURL(url);
}


/* =========================================================
   REMINDERS
   ========================================================= */

function openReminders() {

    document
        .getElementById("reminderModal")
        .classList.add("show");

    renderReminders();
}


function closeReminders() {

    document
        .getElementById("reminderModal")
        .classList.remove("show");
}


function addReminder() {

    const text =
        document
            .getElementById("reminderText")
            .value
            .trim();

    const date =
        document
            .getElementById("reminderDate")
            .value;

    if (!text || !date) {
        alert("Please enter reminder text and date.");
        return;
    }

    const reminders =
        getReminders();

    reminders.push({
        id: Date.now(),
        text: text,
        date: date,
        done: false
    });

    saveReminders(reminders);

    document.getElementById(
        "reminderText"
    ).value = "";

    document.getElementById(
        "reminderDate"
    ).value = "";

    renderReminders();
}


function renderReminders() {

    const container =
        document.getElementById("reminderList");

    if (!container) {
        return;
    }

    const reminders =
        getReminders();

    container.innerHTML = "";

    reminders
        .sort(function(a, b) {
            return new Date(a.date) - new Date(b.date);
        })
        .forEach(function(item) {

            const div =
                document.createElement("div");

            div.className =
                "reminder-item";

            const date =
                new Date(item.date);

            div.innerHTML =
                "<div>" +
                "<strong>" +
                escapeHtml(item.text) +
                "</strong><br>" +
                "<small>" +
                date.toLocaleString() +
                "</small>" +
                "</div>";

            const button =
                document.createElement("button");

            button.className =
                "small-button";

            button.textContent =
                "Delete";

            button.onclick = function() {
                deleteReminder(item.id);
            };

            div.appendChild(button);

            container.appendChild(div);
        });
}


function deleteReminder(id) {

    const reminders =
        getReminders().filter(function(item) {
            return item.id !== id;
        });

    saveReminders(reminders);

    renderReminders();
}


/* =========================================================
   REMINDER CHECK
   ========================================================= */

setInterval(function() {

    const reminders =
        getReminders();

    const now =
        new Date();

    let changed = false;

    reminders.forEach(function(item) {

        if (
            !item.done &&
            new Date(item.date) <= now
        ) {

            item.done = true;
            changed = true;

            alert(
                "⏰ Reminder: " +
                item.text
            );
        }
    });

    if (changed) {
        saveReminders(reminders);
        renderReminders();
    }

}, 30000);


/* =========================================================
   QUICK PROMPTS
   ========================================================= */

function quickPrompt(text) {

    const input =
        document.getElementById("messageInput");

    input.value = text;

    autoResize(input);

    input.focus();
}


/* =========================================================
   INPUT
   ========================================================= */

function handleKey(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();
    }
}


function autoResize(element) {

    element.style.height = "auto";

    element.style.height =
        Math.min(
            element.scrollHeight,
            150
        ) + "px";
}


/* =========================================================
   UTILITIES
   ========================================================= */

function scrollToBottom() {

    const chat =
        document.getElementById("chat");

    setTimeout(function() {

        chat.scrollTop =
            chat.scrollHeight;

    }, 30);
}


function escapeHtml(text) {

    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

</script>

</body>
</html>
"""


# =========================================================
# Local development
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
