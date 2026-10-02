import os
import time
import logging
from collections import defaultdict, deque

import requests
from flask import Flask, request, jsonify, render_template_string, make_response

# =========================================================
# MedAI - Complete Single File Medical AI Assistant
# Developer: Toyebullah Dawoodzay
# =========================================================

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 512 * 1024

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medai")

# =========================================================
# CONFIG
# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Official GenerateContent model
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/"
    f"v1beta/models/{GEMINI_MODEL}:generateContent"
)

MAX_TEXT = 12000
MAX_HISTORY = 20

RATE_WINDOW = 60
RATE_LIMIT = 30

request_log = defaultdict(deque)


# =========================================================
# SECURITY
# =========================================================

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "microphone=(self), camera=(self), geolocation=()"
    )
    response.headers["Cache-Control"] = "no-store"

    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://generativelanguage.googleapis.com; "
        "media-src 'self' blob: data:; "
        "font-src 'self' data:;"
    )

    return response


def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.remote_addr or "unknown"


def rate_limit():
    ip = get_client_ip()
    now = time.time()

    bucket = request_log[ip]

    while bucket and now - bucket[0] > RATE_WINDOW:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT:
        return False

    bucket.append(now)
    return True


@app.before_request
def protect_api():
    if request.path.startswith("/api/"):
        if not rate_limit():
            return jsonify({
                "ok": False,
                "error": "Too many requests. Please wait a little."
            }), 429


# =========================================================
# HELPERS
# =========================================================

def clean_text(value, max_len=MAX_TEXT):
    if value is None:
        return ""

    value = str(value)
    value = value.replace("\x00", "")
    value = value.strip()

    return value[:max_len]


def json_body():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {}

    return data


# =========================================================
# MEDICAL SYSTEM PROMPT
# =========================================================

def medical_system_prompt():
    return """
You are MedAI, an educational medical AI assistant.

Developer: Toyebullah Dawoodzay
Year: 2026

LANGUAGE:
- Answer in the same language as the user.
- If the user writes Pashto, answer in Pashto.
- If the user writes English, answer in English.
- You can understand Pashto, Dari, Urdu and English.

MEDICAL SAFETY:
- You are an educational assistant, not a human doctor.
- Do not claim certainty about a diagnosis from symptoms alone.
- Do not invent medical facts, test results, medicines, citations or sources.
- Clearly state uncertainty when information is insufficient.
- Do not prescribe personalized prescription doses.
- Do not tell users to start, stop or change prescription medicines.
- Explain general medication uses, common risks, interactions and precautions.
- Explain lab results carefully and mention that reference ranges and clinical context matter.
- For children, pregnancy, elderly people or serious chronic illness, recommend professional medical evaluation when appropriate.
- If the user describes a possible emergency, prioritize urgent/emergency medical care.
- Important emergency warning signs include severe difficulty breathing, severe chest pain,
  stroke-like symptoms, severe allergic reaction, uncontrolled bleeding, seizure,
  loss of consciousness, severe poisoning, or another potentially life-threatening condition.
- Do not unnecessarily frighten the user.
- Use simple language.
- Do not pretend to have examined the patient.
- Do not pretend to see medical images unless an image was actually supplied.
- For medical decisions, encourage consultation with a qualified healthcare professional.

ANSWER STYLE:
- Be clear and practical.
- Use short sections and bullet points when helpful.
- If the user asks about symptoms, explain:
  1. Possible causes
  2. Important warning signs
  3. What information would help
  4. When to seek medical care
- If the user asks about medicines, explain:
  1. General purpose
  2. Common side effects
  3. Important precautions
  4. Common interaction considerations
  5. When professional advice is needed
- If the user asks about lab results, explain:
  1. What the test measures
  2. General interpretation
  3. Why reference ranges differ
  4. When follow-up may be appropriate
"""


# =========================================================
# GEMINI API
# =========================================================

def gemini_request(message, history=None):
    if not GEMINI_API_KEY:
        return {
            "ok": False,
            "error": (
                "GEMINI_API_KEY په server کې نه ده تنظیم شوې. "
                "په Vercel Environment Variables کې یې اضافه کړئ."
            )
        }

    message = clean_text(message)

    if not message:
        return {
            "ok": False,
            "error": "پیغام خالي دی."
        }

    history = history or []

    contents = []

    for item in history[-MAX_HISTORY:]:
        role = item.get("role")

        if role not in ("user", "model"):
            continue

        text = clean_text(item.get("text"))

        if not text:
            continue

        contents.append({
            "role": role,
            "parts": [
                {
                    "text": text
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

    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": medical_system_prompt()
                }
            ]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.25,
            "maxOutputTokens": 2048
        }
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    try:
        response = requests.post(
            GEMINI_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code >= 400:
            try:
                error_data = response.json()
                logger.error(
                    "Gemini API %s: %s",
                    response.status_code,
                    error_data
                )
            except Exception:
                logger.error(
                    "Gemini API %s: %s",
                    response.status_code,
                    response.text[:2000]
                )

            return {
                "ok": False,
                "error": (
                    f"AI service error ({response.status_code}). "
                    "GEMINI_MODEL او GEMINI_API_KEY وګورئ."
                )
            }

        data = response.json()

        candidates = data.get("candidates", [])

        if not candidates:
            logger.error("Gemini returned no candidates: %s", data)

            return {
                "ok": False,
                "error": "AI ځواب ورنه کړ."
            }

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )

        texts = []

        for part in parts:
            text = part.get("text")

            if text:
                texts.append(text)

        output = "\n".join(texts).strip()

        if not output:
            return {
                "ok": False,
                "error": "AI خالي ځواب ورکړ."
            }

        return {
            "ok": True,
            "text": output
        }

    except requests.Timeout:
        return {
            "ok": False,
            "error": "AI request timeout شو. بیا هڅه وکړئ."
        }

    except requests.RequestException as exc:
        logger.error("Gemini connection error: %s", exc)

        return {
            "ok": False,
            "error": "AI service سره اړیکه ونه شوه."
        }

    except Exception as exc:
        logger.exception("Unexpected Gemini error: %s", exc)

        return {
            "ok": False,
            "error": "د server یوه ناڅرګنده ستونزه رامنځته شوه."
        }


# =========================================================
# HTML
# =========================================================

PAGE = r"""
<!DOCTYPE html>
<html lang="ps" dir="rtl">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<meta name="theme-color"
      content="#087f8c">

<meta name="description"
      content="MedAI Medical AI Assistant">

<title>MedAI - Medical AI</title>

<style>

* {
    box-sizing: border-box;
}

:root {
    --bg: #f5f7fa;
    --panel: #ffffff;
    --panel2: #eef3f5;
    --text: #17212b;
    --muted: #687580;
    --primary: #087f8c;
    --primary2: #0b7285;
    --border: #dce4e8;
    --danger: #c92a2a;
    --success: #2b8a3e;
    --shadow: 0 10px 30px rgba(0,0,0,.08);
}

body.dark {
    --bg: #101417;
    --panel: #171d21;
    --panel2: #20282d;
    --text: #f2f5f7;
    --muted: #aeb9c1;
    --primary: #38b8c6;
    --primary2: #2ca8b7;
    --border: #303a40;
    --shadow: 0 10px 30px rgba(0,0,0,.35);
}

body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
    min-height: 100vh;
}

button,
textarea,
input,
select {
    font: inherit;
}

button {
    cursor: pointer;
}

.app {
    min-height: 100vh;
    display: flex;
}

.sidebar {
    width: 280px;
    background: var(--panel);
    border-left: 1px solid var(--border);
    padding: 16px;
    position: fixed;
    right: 0;
    top: 0;
    bottom: 0;
    overflow-y: auto;
    z-index: 100;
    transition: transform .25s ease;
}

.logo {
    display: flex;
    align-items: center;
    gap: 11px;
    padding: 8px 4px 20px;
}

.logo-icon {
    width: 46px;
    height: 46px;
    border-radius: 15px;
    display: grid;
    place-items: center;
    color: white;
    font-size: 24px;
    background: linear-gradient(135deg,#087f8c,#20a4b2);
}

.logo h1 {
    margin: 0;
    font-size: 21px;
}

.logo small {
    color: var(--muted);
}

.menu-title {
    color: var(--muted);
    font-size: 12px;
    margin: 18px 8px 8px;
}

.menu-btn {
    width: 100%;
    border: 0;
    background: transparent;
    color: var(--text);
    text-align: right;
    padding: 10px 12px;
    border-radius: 11px;
    margin: 2px 0;
}

.menu-btn:hover {
    background: var(--panel2);
}

.main {
    margin-right: 280px;
    width: calc(100% - 280px);
    min-height: 100vh;
}

.topbar {
    position: sticky;
    top: 0;
    z-index: 50;
    height: 68px;
    background: var(--bg);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 22px;
}

.top-actions {
    display: flex;
    gap: 8px;
}

.icon-btn {
    border: 1px solid var(--border);
    background: var(--panel);
    color: var(--text);
    width: 42px;
    height: 42px;
    border-radius: 12px;
}

.mobile-menu {
    display: none;
}

.content {
    max-width: 1100px;
    width: 100%;
    margin: auto;
    padding: 28px 20px 170px;
}

.hero {
    text-align: center;
    padding: 25px 10px;
}

.hero-icon {
    width: 76px;
    height: 76px;
    border-radius: 24px;
    background: linear-gradient(135deg,#087f8c,#36c2ce);
    color: white;
    margin: auto;
    display: grid;
    place-items: center;
    font-size: 36px;
    box-shadow: var(--shadow);
}

.hero h2 {
    font-size: 30px;
    margin: 18px 0 8px;
}

.hero p {
    color: var(--muted);
    max-width: 700px;
    margin: auto;
    line-height: 1.9;
}

.quick {
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 10px;
    margin: 20px 0;
}

.quick button {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 15px;
    padding: 14px 8px;
    color: var(--text);
}

.quick button:hover {
    border-color: var(--primary);
}

.chat {
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.message {
    display: flex;
    gap: 9px;
    align-items: flex-start;
}

.message.user {
    flex-direction: row-reverse;
}

.avatar {
    flex: 0 0 38px;
    width: 38px;
    height: 38px;
    border-radius: 13px;
    display: grid;
    place-items: center;
    background: var(--primary);
    color: white;
}

.message.user .avatar {
    background: #495057;
}

.bubble {
    max-width: 84%;
    background: var(--panel);
    border: 1px solid var(--border);
    padding: 14px 16px;
    border-radius: 17px;
    line-height: 1.9;
    white-space: pre-wrap;
    box-shadow: 0 3px 15px rgba(0,0,0,.03);
}

.message.user .bubble {
    background: var(--primary);
    color: white;
    border-color: transparent;
}

.typing {
    opacity: .65;
}

.composer-wrap {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 280px;
    background: linear-gradient(
        to top,
        var(--bg) 75%,
        transparent
    );
    padding: 14px 20px 18px;
    z-index: 80;
}

.composer {
    max-width: 920px;
    margin: auto;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 8px;
    display: flex;
    align-items: flex-end;
    gap: 7px;
    box-shadow: var(--shadow);
}

.composer textarea {
    flex: 1;
    resize: none;
    border: 0;
    outline: 0;
    background: transparent;
    color: var(--text);
    min-height: 45px;
    max-height: 160px;
    padding: 11px 8px;
}

.voice-btn,
.send-btn {
    width: 45px;
    height: 45px;
    border-radius: 14px;
    border: 0;
    flex: 0 0 auto;
}

.voice-btn {
    background: var(--panel2);
    color: var(--text);
}

.voice-btn.active {
    background: var(--danger);
    color: white;
    animation: pulse 1s infinite;
}

.send-btn {
    background: var(--primary);
    color: white;
}

@keyframes pulse {
    50% {
        transform: scale(1.08);
    }
}

.panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 18px;
    margin-top: 18px;
}

.panel h3 {
    margin-top: 0;
}

.grid {
    display: grid;
    grid-template-columns: repeat(2,1fr);
    gap: 12px;
}

.card {
    background: var(--panel2);
    border-radius: 14px;
    padding: 14px;
    margin: 8px 0;
    line-height: 1.8;
}

.btn {
    border: 0;
    border-radius: 10px;
    padding: 9px 13px;
    background: var(--primary);
    color: white;
}

.btn.secondary {
    background: var(--panel);
    color: var(--text);
    border: 1px solid var(--border);
}

.btn.danger {
    background: var(--danger);
}

.btn.success {
    background: var(--success);
}

input,
select {
    width: 100%;
    border: 1px solid var(--border);
    background: var(--panel);
    color: var(--text);
    border-radius: 11px;
    padding: 10px;
    outline: none;
}

.hidden {
    display: none !important;
}

.overlay {
    display: none;
}

.voice-status {
    position: fixed;
    bottom: 105px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--text);
    color: var(--bg);
    border-radius: 30px;
    padding: 10px 18px;
    z-index: 200;
    box-shadow: var(--shadow);
}

.status-box {
    margin-top: 12px;
    padding: 12px;
    border-radius: 12px;
    background: var(--panel2);
    color: var(--muted);
}

.feature-title {
    font-size: 18px;
    margin-bottom: 8px;
}

@media (max-width: 850px) {

    .sidebar {
        transform: translateX(100%);
    }

    .sidebar.open {
        transform: translateX(0);
    }

    .main {
        margin-right: 0;
        width: 100%;
    }

    .composer-wrap {
        right: 0;
    }

    .mobile-menu {
        display: block;
    }

    .quick {
        grid-template-columns: repeat(2,1fr);
    }

    .grid {
        grid-template-columns: 1fr;
    }

    .overlay.show {
        display: block;
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,.45);
        z-index: 90;
    }
}

@media (max-width: 500px) {

    .content {
        padding-left: 10px;
        padding-right: 10px;
    }

    .hero h2 {
        font-size: 24px;
    }

    .bubble {
        max-width: 90%;
    }
}

</style>

</head>

<body>

<div id="overlay" class="overlay"></div>

<div class="app">

<aside id="sidebar" class="sidebar">

<div class="logo">

<div class="logo-icon">⚕</div>

<div>
<h1>MedAI</h1>
<small>Medical AI Assistant</small>
</div>

</div>

<div class="menu-title">AI</div>

<button class="menu-btn" onclick="newChat()">
➕ نوی Chat
</button>

<button class="menu-btn" onclick="startVoiceMode()">
🎙️ Voice Chat
</button>

<button class="menu-btn" onclick="showHistory()">
🕘 History
</button>

<button class="menu-btn" onclick="showFavorites()">
⭐ Favorites
</button>

<div class="menu-title">Medical Tools</div>

<button class="menu-btn" onclick="toolPrompt('Symptoms Checker')">
🩺 Symptoms Checker
</button>

<button class="menu-btn" onclick="toolPrompt('Vital Signs')">
❤️ Vital Signs
</button>

<button class="menu-btn" onclick="toolPrompt('Medicine Information')">
💊 Medicine Info
</button>

<button class="menu-btn" onclick="toolPrompt('Lab Report')">
🧪 Lab Report
</button>

<button class="menu-btn" onclick="toolPrompt('Disease Comparison')">
🦠 Disease Compare
</button>

<button class="menu-btn" onclick="toolPrompt('Emergency Checker')">
🚨 Emergency
</button>

<button class="menu-btn" onclick="toolPrompt('Drug Interaction')">
💊 Drug Interaction
</button>

<button class="menu-btn" onclick="toolPrompt('First Aid')">
🩹 First Aid
</button>

<button class="menu-btn" onclick="toolPrompt('Medical Dictionary')">
📚 Medical Dictionary
</button>

<button class="menu-btn" onclick="toolPrompt('Risk Assessment')">
📊 Risk Assessment
</button>

<button class="menu-btn" onclick="toolPrompt('Health Report')">
❤️ Health Report
</button>

<button class="menu-btn" onclick="toolPrompt('Medical Images')">
🖼️ Medical Images
</button>

<button class="menu-btn" onclick="toolPrompt('Medical Quiz')">
🧠 Medical Quiz
</button>

<div class="menu-title">Personal</div>

<button class="menu-btn" onclick="showTracker()">
📈 Health Tracker
</button>

<button class="menu-btn" onclick="showReminders()">
⏰ Medicine Reminder
</button>

<button class="menu-btn" onclick="toggleDark()">
🌙 Dark Mode
</button>

<button class="menu-btn" onclick="showAbout()">
ℹ️ About MedAI
</button>

</aside>


<main class="main">

<header class="topbar">

<button
id="mobileMenu"
class="icon-btn mobile-menu"
onclick="toggleSidebar()">
☰
</button>

<strong>MedAI</strong>

<div class="top-actions">

<button
class="icon-btn"
onclick="startVoiceMode()">
🎙️
</button>

<button
class="icon-btn"
onclick="toggleDark()">
🌙
</button>

</div>

</header>


<section class="content">

<div class="hero">

<div class="hero-icon">⚕</div>

<h2>MedAI ته ښه راغلاست</h2>

<p>
خپله روغتیايي پوښتنه ولیکئ یا د 🎙️ تڼۍ له لارې
خبرې وکړئ. MedAI به تعلیمي طبي معلومات درکړي.
</p>

</div>


<div class="quick">

<button onclick="quickSend('زه ځینې نښې لرم، مرسته راسره وکړه.')">
🩺 نښې
</button>

<button onclick="quickSend('زما د وینې فشار، نبض، تودوخې، تنفس او SpO2 په اړه معلومات راکړه.')">
❤️ Vital Signs
</button>

<button onclick="quickSend('د دې دوا په اړه عمومي معلومات راکړه.')">
💊 دوا
</button>

<button onclick="quickSend('د دې لابراتوار نتیجه راته تشریح کړه.')">
🧪 Lab
</button>

<button onclick="quickSend('د دوو ناروغیو ترمنځ توپیر راته ووایه.')">
🦠 Disease
</button>

<button onclick="quickSend('زه غواړم پوه شم چې دا بیړنی حالت خو نه دی.')">
🚨 Emergency
</button>

<button onclick="quickSend('ایا دا دوه درمل یو ځای اخیستل کېدای شي؟')">
💊 Interaction
</button>

<button onclick="quickSend('د لومړنۍ مرستې مهم معلومات راکړه.')">
🩹 First Aid
</button>

</div>


<div id="chat" class="chat">

<div class="message">

<div class="avatar">⚕</div>

<div class="bubble">
سلام! زه <strong>MedAI</strong> یم.
خپله طبي پوښتنه ولیکئ، یا د 🎙️ تڼۍ کېکاږئ.
</div>

</div>

</div>


<div id="extraPanel"></div>

</section>


<div class="composer-wrap">

<div class="composer">

<textarea
id="message"
rows="1"
placeholder="خپله طبي پوښتنه ولیکئ..."
onkeydown="handleKey(event)"
></textarea>

<button
id="voiceBtn"
class="voice-btn"
onclick="toggleVoice()">
🎙️
</button>

<button
class="send-btn"
onclick="sendMessage()">
➤
</button>

</div>

</div>


<div id="voiceStatus"
class="voice-status hidden">
🎙️ زه اورم...
</div>

</main>

</div>


<script>

const chat = document.getElementById("chat");
const input = document.getElementById("message");
const voiceBtn = document.getElementById("voiceBtn");
const voiceStatus = document.getElementById("voiceStatus");
const extraPanel = document.getElementById("extraPanel");
const sidebar = document.getElementById("sidebar");
const overlay = document.getElementById("overlay");

const HISTORY_KEY = "medai_history";
const FAVORITES_KEY = "medai_favorites";
const TRACKER_KEY = "medai_tracker";
const REMINDER_KEY = "medai_reminders";
const DARK_KEY = "medai_dark";

let recognition = null;
let listening = false;
let voiceMode = false;
let speaking = false;
let sending = false;

const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;


/* ========================================================
   STORAGE
   ======================================================== */

function readStorage(key, fallback = []) {

    try {

        const value =
            localStorage.getItem(key);

        if (!value) {
            return fallback;
        }

        return JSON.parse(value);

    } catch {

        return fallback;
    }
}


function writeStorage(key, value) {

    try {

        localStorage.setItem(
            key,
            JSON.stringify(value)
        );

    } catch {}
}


/* ========================================================
   CHAT UI
   ======================================================== */

function addMessage(text, role = "ai", favorite = false) {

    const wrapper =
        document.createElement("div");

    wrapper.className =
        "message " +
        (role === "user" ? "user" : "");

    const avatar =
        document.createElement("div");

    avatar.className = "avatar";

    avatar.textContent =
        role === "user" ? "👤" : "⚕";

    const bubble =
        document.createElement("div");

    bubble.className = "bubble";

    bubble.textContent = text;

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);

    if (favorite) {

        const br =
            document.createElement("br");

        const button =
            document.createElement("button");

        button.className =
            "btn secondary";

        button.textContent =
            "⭐ Save";

        button.style.marginTop = "8px";

        button.onclick = () => {

            saveFavorite(text);

            button.textContent =
                "✓ Saved";
        };

        bubble.appendChild(br);
        bubble.appendChild(button);
    }

    chat.appendChild(wrapper);

    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: "smooth"
    });
}


function addTyping() {

    removeTyping();

    const wrapper =
        document.createElement("div");

    wrapper.id = "typingMessage";
    wrapper.className = "message";

    const avatar =
        document.createElement("div");

    avatar.className = "avatar";
    avatar.textContent = "⚕";

    const bubble =
        document.createElement("div");

    bubble.className =
        "bubble typing";

    bubble.textContent =
        "MedAI لیکي...";

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);

    chat.appendChild(wrapper);
}


function removeTyping() {

    const item =
        document.getElementById(
            "typingMessage"
        );

    if (item) {
        item.remove();
    }
}


/* ========================================================
   CHAT
   ======================================================== */

async function sendMessage(customText = null) {

    if (sending) {
        return;
    }

    const text =
        (
            customText !== null
                ? customText
                : input.value
        ).trim();

    if (!text) {
        return;
    }

    sending = true;

    input.value = "";

    addMessage(
        text,
        "user"
    );

    const history =
        readStorage(
            HISTORY_KEY,
            []
        );

    const apiHistory =
        history
            .filter(x =>
                x.role === "user" ||
                x.role === "ai"
            )
            .slice(-20)
            .map(x => ({
                role:
                    x.role === "ai"
                        ? "model"
                        : "user",
                text: x.text
            }));

    saveHistory({
        role: "user",
        text: text,
        time: new Date().toISOString()
    });

    addTyping();

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
                        message: text,
                        history:
                            apiHistory
                    })
                }
            );

        const data =
            await response.json();

        removeTyping();

        if (!data.ok) {

            addMessage(
                "❌ " +
                (
                    data.error ||
                    "یوه ستونزه رامنځته شوه."
                )
            );

            return;
        }

        addMessage(
            data.text,
            "ai",
            true
        );

        saveHistory({
            role: "ai",
            text: data.text,
            time: new Date().toISOString()
        });

        if (voiceMode) {

            speak(data.text);
        }

    } catch (error) {

        removeTyping();

        addMessage(
            "❌ له server سره اړیکه ونه شوه. بیا هڅه وکړئ."
        );

    } finally {

        sending = false;
    }
}


function quickSend(text) {
    sendMessage(text);
}


function handleKey(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();
    }
}


function newChat() {

    voiceMode = false;

    stopSpeaking();

    chat.innerHTML = "";

    extraPanel.innerHTML = "";

    addMessage(
        "سلام! نوی Chat پیل شو. څنګه مرسته درسره وکړم؟"
    );

    closeSidebar();
}


/* ========================================================
   VOICE INPUT
   ======================================================== */

if (SpeechRecognition) {

    recognition =
        new SpeechRecognition();

    recognition.lang = "ps-AF";
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => {

        listening = true;

        voiceBtn.classList.add(
            "active"
        );

        voiceStatus.classList.remove(
            "hidden"
        );

        voiceStatus.textContent =
            "🎙️ زه اورم... خبرې وکړئ";
    };

    recognition.onresult = event => {

        let finalText = "";
        let interimText = "";

        for (
            let i = event.resultIndex;
            i < event.results.length;
            i++
        ) {

            const transcript =
                event.results[i][0].transcript;

            if (
                event.results[i].isFinal
            ) {

                finalText += transcript;

            } else {

                interimText += transcript;
            }
        }

        input.value =
            finalText || interimText;
    };

    recognition.onerror = event => {

        listening = false;

        voiceBtn.classList.remove(
            "active"
        );

        voiceStatus.classList.add(
            "hidden"
        );

        if (
            event.error === "not-allowed"
        ) {

            alert(
                "Microphone permission ورکړئ."
            );
        }
    };

    recognition.onend = () => {

        listening = false;

        voiceBtn.classList.remove(
            "active"
        );

        voiceStatus.classList.add(
            "hidden"
        );

        if (
            voiceMode &&
            input.value.trim()
        ) {

            sendMessage();
        }
    };

}


function toggleVoice() {

    if (!recognition) {

        alert(
            "دا browser Voice Recognition نه ملاتړ کوي. Chrome یا Edge وکاروئ."
        );

        return;
    }

    if (listening) {

        recognition.stop();

        return;
    }

    voiceMode = true;

    try {

        recognition.start();

    } catch {}
}


function startVoiceMode() {

    closeSidebar();

    voiceMode = true;

    if (!recognition) {

        alert(
            "Chrome یا Edge وکاروئ او Microphone permission ورکړئ."
        );

        return;
    }

    if (!listening) {

        try {

            recognition.start();

        } catch {}
    }
}


/* ========================================================
   TEXT TO SPEECH
   ======================================================== */

function speak(text) {

    if (
        !("speechSynthesis" in window)
    ) {
        return;
    }

    window.speechSynthesis.cancel();

    const utterance =
        new SpeechSynthesisUtterance(text);

    utterance.lang = "ps-AF";
    utterance.rate = 0.92;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onstart = () => {

        speaking = true;

        voiceStatus.classList.remove(
            "hidden"
        );

        voiceStatus.textContent =
            "🔊 MedAI خبرې کوي...";
    };

    utterance.onend = () => {

        speaking = false;

        voiceStatus.classList.add(
            "hidden"
        );
    };

    window.speechSynthesis.speak(
        utterance
    );
}


function stopSpeaking() {

    if (
        "speechSynthesis" in window
    ) {

        window.speechSynthesis.cancel();
    }

    speaking = false;

    voiceStatus.classList.add(
        "hidden"
    );
}


/* ========================================================
   HISTORY
   ======================================================== */

function saveHistory(item) {

    const history =
        readStorage(
            HISTORY_KEY,
            []
        );

    history.push(item);

    if (history.length > 100) {

        history.splice(
            0,
            history.length - 100
        );
    }

    writeStorage(
        HISTORY_KEY,
        history
    );
}


function showHistory() {

    closeSidebar();

    const history =
        readStorage(
            HISTORY_KEY,
            []
        );

    extraPanel.innerHTML = "";

    const panel =
        document.createElement("div");

    panel.className = "panel";

    panel.innerHTML =
        "<h3>🕘 Chat History</h3>";

    if (!history.length) {

        const p =
            document.createElement("p");

        p.textContent =
            "تر اوسه History نشته.";

        panel.appendChild(p);

    } else {

        history
            .slice()
            .reverse()
            .slice(0, 50)
            .forEach(item => {

                const card =
                    document.createElement(
                        "div"
                    );

                card.className = "card";

                card.textContent =
                    item.text;

                panel.appendChild(card);
            });
    }

    const clear =
        document.createElement("button");

    clear.className =
        "btn danger";

    clear.textContent =
        "Clear History";

    clear.onclick = () => {

        localStorage.removeItem(
            HISTORY_KEY
        );

        showHistory();
    };

    panel.appendChild(clear);

    extraPanel.appendChild(panel);

    panel.scrollIntoView({
        behavior: "smooth"
    });
}


/* ========================================================
   FAVORITES
   ======================================================== */

function saveFavorite(text) {

    const favorites =
        readStorage(
            FAVORITES_KEY,
            []
        );

    if (!favorites.includes(text)) {

        favorites.push(text);
    }

    writeStorage(
        FAVORITES_KEY,
        favorites
    );
}


function showFavorites() {

    closeSidebar();

    const favorites =
        readStorage(
            FAVORITES_KEY,
            []
        );

    extraPanel.innerHTML = "";

    const panel =
        document.createElement("div");

    panel.className = "panel";

    panel.innerHTML =
        "<h3>⭐ Favorites</h3>";

    if (!favorites.length) {

        const p =
            document.createElement("p");

        p.textContent =
            "تر اوسه Favorite نشته.";

        panel.appendChild(p);

    } else {

        favorites.forEach(
            (item, index) => {

                const card =
                    document.createElement(
                        "div"
                    );

                card.className = "card";

                const text =
                    document.createElement(
                        "div"
                    );

                text.textContent = item;

                const button =
                    document.createElement(
                        "button"
                    );

                button.className =
                    "btn danger";

                button.textContent =
                    "Delete";

                button.onclick = () => {

                    favorites.splice(
                        index,
                        1
                    );

                    writeStorage(
                        FAVORITES_KEY,
                        favorites
                    );

                    showFavorites();
                };

                card.appendChild(text);
                card.appendChild(button);

                panel.appendChild(card);
            }
        );
    }

    extraPanel.appendChild(panel);
}


/* ========================================================
   MEDICAL TOOLS
   ======================================================== */

function toolPrompt(tool) {

    closeSidebar();

    const prompts = {

        "Symptoms Checker":
            "زما لاندې نښې د تعلیمي طبي معلوماتو له مخې تحلیل کړه. احتمالي عام علتونه، مهم warning signs، کوم معلومات مهم دي، او کوم وخت باید روغتیايي مسلکي ته مراجعه وشي، تشریح کړه. نښې: ",

        "Vital Signs":
            "Vital Signs لکه Blood Pressure، Pulse، Temperature، Respiratory Rate او SpO2 تشریح کړه. د هر یوه اهمیت او عمومي reference ranges هم تشریح کړه، خو واضح کړه چې عمر او حالت مهم دی.",

        "Medicine Information":
            "د دې دوا په اړه عمومي معلومات راکړه: استعمال، common side effects، مهم احتیاطونه، common interactions او کله باید ډاکټر یا pharmacist سره مشوره وشي. دوا: ",

        "Lab Report":
            "زما Lab Report په تعلیمي ډول تشریح کړه. هر test څه اندازه کوي، result څه معنی لرلای شي، reference range ولې مهم دی، او کوم موارد باید له ډاکټر سره تعقیب شي. Report: ",

        "Disease Comparison":
            "د دوو ناروغیو ترمنځ د symptoms، causes، diagnosis او general treatment په اړه neutral comparison جوړ کړه. ناروغۍ: ",

        "Emergency Checker":
            "د دې حالت له مخې ووایه چې کوم emergency warning signs باید جدي ونیول شي او کله باید عاجله طبي مرسته وغوښتل شي. حالت: ",

        "Drug Interaction":
            "د لاندې درملو د ممکنه interactions په اړه عمومي معلومات راکړه. د خطر نښې او د pharmacist/doctor سره د مشورې اړتیا هم تشریح کړه. درمل: ",

        "First Aid":
            "د دې حالت لپاره خوندي First Aid ګامونه تشریح کړه او ووایه چې کوم وخت باید emergency services یا روغتون ته مراجعه وشي. حالت: ",

        "Medical Dictionary":
            "د کارونکي لپاره یو ساده Medical Dictionary جوړ کړه. اصطلاحات په ساده پښتو تشریح کړه.",

        "Risk Assessment":
            "د روغتیايي risk assessment لپاره کوم معلومات مهم دي؟ د lifestyle، family history، age، symptoms او known conditions رول تشریح کړه. تشخیص مه کوه.",

        "Health Report":
            "زما لپاره یو منظم Health Report template جوړ کړه چې symptoms، medicines، allergies، vital signs، lab results، medical history او questions for doctor ولري.",

        "Medical Images":
            "د یوې طبي موضوع لپاره د تعلیمي diagram یا image تشریح راکړه، او ووایه چې په image کې کوم anatomy یا feature باید وکتل شي. که image موجود نه وي، دا واضح کړه.",

        "Medical Quiz":
            "زما لپاره 5 پوښتنې Medical Quiz جوړ کړه. هره پوښتنه 4 انتخابونه ولري. په پای کې correct answers او لنډ explanations ورکړه."
    };

    input.value =
        prompts[tool] ||
        tool;

    input.focus();
}


/* ========================================================
   HEALTH TRACKER
   ======================================================== */

function showTracker() {

    closeSidebar();

    extraPanel.innerHTML = `

    <div class="panel">

        <h3>📈 Health Tracker</h3>

        <div class="grid">

            <div>
                <label>Weight</label>
                <input
                    id="trackWeight"
                    placeholder="kg">
            </div>

            <div>
                <label>Blood Pressure</label>
                <input
                    id="trackBP"
                    placeholder="120/80">
            </div>

            <div>
                <label>Heart Rate</label>
                <input
                    id="trackHR"
                    placeholder="bpm">
            </div>

            <div>
                <label>Temperature</label>
                <input
                    id="trackTemp"
                    placeholder="°C">
            </div>

            <div>
                <label>SpO2</label>
                <input
                    id="trackSpO2"
                    placeholder="%">
            </div>

            <div>
                <label>Notes</label>
                <input
                    id="trackNotes"
                    placeholder="یادښت">
            </div>

        </div>

        <br>

        <button
            class="btn"
            onclick="saveTracker()">
            Save
        </button>

        <div id="trackerList"></div>

    </div>
    `;

    renderTracker();
}


function saveTracker() {

    const tracker =
        readStorage(
            TRACKER_KEY,
            []
        );

    tracker.push({

        date:
            new Date().toLocaleString(),

        weight:
            document.getElementById(
                "trackWeight"
            ).value,

        bp:
            document.getElementById(
                "trackBP"
            ).value,

        hr:
            document.getElementById(
                "trackHR"
            ).value,

        temp:
            document.getElementById(
                "trackTemp"
            ).value,

        spo2:
            document.getElementById(
                "trackSpO2"
            ).value,

        notes:
            document.getElementById(
                "trackNotes"
            ).value
    });

    writeStorage(
        TRACKER_KEY,
        tracker
    );

    renderTracker();
}


function renderTracker() {

    const list =
        document.getElementById(
            "trackerList"
        );

    if (!list) {
        return;
    }

    list.innerHTML = "";

    const tracker =
        readStorage(
            TRACKER_KEY,
            []
        );

    tracker
        .slice()
        .reverse()
        .slice(0, 30)
        .forEach(item => {

            const card =
                document.createElement(
                    "div"
                );

            card.className = "card";

            card.textContent =
`📅 ${item.date}
Weight: ${item.weight || "-"}
BP: ${item.bp || "-"}
HR: ${item.hr || "-"}
Temp: ${item.temp || "-"}
SpO2: ${item.spo2 || "-"}
Notes: ${item.notes || "-"}`;

            list.appendChild(card);
        });
}


/* ========================================================
   MEDICINE REMINDER
   ======================================================== */

function showReminders() {

    closeSidebar();

    extraPanel.innerHTML = `

    <div class="panel">

        <h3>⏰ Medicine Reminder</h3>

        <input
            id="medicineName"
            placeholder="دوا نوم">

        <br><br>

        <input
            id="medicineTime"
            type="time">

        <br><br>

        <button
            class="btn"
            onclick="addReminder()">
            Add Reminder
        </button>

        <div
            class="status-box">
            یادونه: browser notification د page خلاص پاتې کېدو سره ښه کار کوي.
        </div>

        <div id="reminderList"></div>

    </div>
    `;

    renderReminders();

    requestNotificationPermission();
}


function addReminder() {

    const name =
        document.getElementById(
            "medicineName"
        ).value.trim();

    const time =
        document.getElementById(
            "medicineTime"
        ).value;

    if (!name || !time) {

        alert(
            "دوا نوم او وخت ولیکئ."
        );

        return;
    }

    const reminders =
        readStorage(
            REMINDER_KEY,
            []
        );

    reminders.push({

        id: Date.now(),

        name: name,

        time: time
    });

    writeStorage(
        REMINDER_KEY,
        reminders
    );

    renderReminders();
}


function renderReminders() {

    const list =
        document.getElementById(
            "reminderList"
        );

    if (!list) {
        return;
    }

    list.innerHTML = "";

    const reminders =
        readStorage(
            REMINDER_KEY,
            []
        );

    reminders.forEach(reminder => {

        const card =
            document.createElement(
                "div"
            );

        card.className = "card";

        const text =
            document.createElement(
                "div"
            );

        text.textContent =
            `${reminder.name} — ${reminder.time}`;

        const button =
            document.createElement(
                "button"
            );

        button.className =
            "btn danger";

        button.textContent =
            "Delete";

        button.onclick = () => {

            const filtered =
                reminders.filter(
                    x =>
                        x.id !==
                        reminder.id
                );

            writeStorage(
                REMINDER_KEY,
                filtered
            );

            renderReminders();
        };

        card.appendChild(text);
        card.appendChild(button);

        list.appendChild(card);
    });
}


/* ========================================================
   NOTIFICATIONS
   ======================================================== */

async function requestNotificationPermission() {

    if (
        "Notification" in window &&
        Notification.permission === "default"
    ) {

        try {

            await Notification.requestPermission();

        } catch {}
    }
}


function checkReminders() {

    const reminders =
        readStorage(
            REMINDER_KEY,
            []
        );

    if (!reminders.length) {
        return;
    }

    const now = new Date();

    const hh =
        String(
            now.getHours()
        ).padStart(2,"0");

    const mm =
        String(
            now.getMinutes()
        ).padStart(2,"0");

    const current =
        `${hh}:${mm}`;

    const day =
        `${now.getFullYear()}-` +
        `${String(now.getMonth()+1).padStart(2,"0")}-` +
        `${String(now.getDate()).padStart(2,"0")}`;

    reminders.forEach(reminder => {

        if (
            reminder.time !== current
        ) {
            return;
        }

        const key =
            `medai_reminder_${reminder.id}`;

        const stamp =
            `${day}_${current}`;

        if (
            localStorage.getItem(key) ===
            stamp
        ) {
            return;
        }

        localStorage.setItem(
            key,
            stamp
        );

        const message =
            `⏰ د دوا وخت دی: ${reminder.name}`;

        if (
            "Notification" in window &&
            Notification.permission ===
            "granted"
        ) {

            try {

                new Notification(
                    "MedAI Medicine Reminder",
                    {
                        body: message
                    }
                );

            } catch {}
        }

        alert(message);

        speak(
            `د دوا وخت دی. ${reminder.name}`
        );
    });
}


setInterval(
    checkReminders,
    30000
);


/* ========================================================
   DARK MODE
   ======================================================== */

function toggleDark() {

    document.body.classList.toggle(
        "dark"
    );

    localStorage.setItem(
        DARK_KEY,
        document.body.classList.contains(
            "dark"
        )
            ? "1"
            : "0"
    );
}


if (
    localStorage.getItem(
        DARK_KEY
    ) === "1"
) {

    document.body.classList.add(
        "dark"
    );
}


/* ========================================================
   SIDEBAR
   ======================================================== */

function toggleSidebar() {

    sidebar.classList.toggle(
        "open"
    );

    overlay.classList.toggle(
        "show"
    );
}


function closeSidebar() {

    sidebar.classList.remove(
        "open"
    );

    overlay.classList.remove(
        "show"
    );
}


overlay.addEventListener(
    "click",
    closeSidebar
);


/* ========================================================
   ABOUT
   ======================================================== */

function showAbout() {

    closeSidebar();

    extraPanel.innerHTML = `

    <div class="panel">

        <h3>ℹ️ About MedAI</h3>

        <p>
        MedAI یو تعلیمي Medical AI Assistant دی.
        </p>

        <div class="status-box">
        ⚕ Developer: Toyebullah Dawoodzay<br>
        📅 Year: 2026<br>
        🤖 AI: Gemini<br>
        🌐 Language: Pashto / English / Dari / Urdu
        </div>

        <p>
        MedAI د طبي معلوماتو لپاره دی او د qualified
        doctor یا healthcare professional بدیل نه دی.
        </p>

    </div>
    `;
}


/* ========================================================
   START
   ======================================================== */

input.focus();

</script>

</body>
</html>
"""


# =========================================================
# ROUTES
# =========================================================

@app.get("/")
def index():

    response = make_response(
        render_template_string(PAGE)
    )

    return response


@app.post("/api/chat")
def api_chat():

    data = json_body()

    message =
        clean_text(
            data.get("message")
        )

    if not message:

        return jsonify({
            "ok": False,
            "error": "پیغام خالي دی."
        }), 400

    raw_history =
        data.get("history", [])

    if not isinstance(raw_history, list):
        raw_history = []

    history = []

    for item in raw_history[-MAX_HISTORY:]:

        if not isinstance(item, dict):
            continue

        role = item.get("role")

        if role not in (
            "user",
            "model"
        ):
            continue

        text =
            clean_text(
                item.get("text"),
                6000
            )

        if text:

            history.append({
                "role": role,
                "text": text
            })

    result =
        gemini_request(
            message,
            history
        )

    if not result["ok"]:

        return jsonify(result), 502

    return jsonify({
        "ok": True,
        "text": result["text"]
    })


@app.get("/health")
def health():

    return jsonify({

        "ok": True,

        "service": "MedAI",

        "ai_configured":
            bool(GEMINI_API_KEY),

        "model":
            GEMINI_MODEL

    })


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(413)
def too_large(error):

    return jsonify({
        "ok": False,
        "error": "Request is too large."
    }), 413


@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "ok": False,
        "error": "Not found."
    }), 404


@app.errorhandler(500)
def server_error(error):

    logger.exception(
        "Server error"
    )

    return jsonify({
        "ok": False,
        "error": "Internal server error."
    }), 500


# =========================================================
# LOCAL RUN
# =========================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
