import os
import re
import time
import logging
from collections import defaultdict, deque
from functools import wraps

import requests
from flask import Flask, request, jsonify, render_template_string


# =========================================================
# MEDAI - Flask + Gemini
# =========================================================

app = Flask(__name__)

# -------------------------
# Configuration
# -------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/"
    f"v1beta/models/{GEMINI_MODEL}:generateContent"
)

MAX_TEXT = 12000
MAX_HISTORY = 16

RATE_LIMIT = 30
RATE_WINDOW = 60

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medai")

request_log = defaultdict(deque)


# =========================================================
# Security
# =========================================================

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "microphone=(self)"

    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "media-src 'self' blob:;"
    )

    return response


# =========================================================
# Helpers
# =========================================================

def clean_text(value, limit=MAX_TEXT):
    if value is None:
        return ""

    value = str(value)
    value = value.replace("\x00", "")
    value = re.sub(r"\s+", " ", value).strip()

    return value[:limit]


def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.remote_addr or "unknown"


def rate_limit_check():
    now = time.time()
    ip = get_client_ip()

    bucket = request_log[ip]

    while bucket and now - bucket[0] > RATE_WINDOW:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT:
        return False

    bucket.append(now)
    return True


def json_body():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {}

    return data


def error_response(message, status=400):
    return jsonify({
        "ok": False,
        "error": message
    }), status


# =========================================================
# Medical System Prompt
# =========================================================

def medical_system_prompt():
    return """
You are MedAI, a medical information assistant.

IMPORTANT SAFETY RULES:

1. You are not a replacement for a licensed doctor.
2. Never claim certainty when symptoms are ambiguous.
3. Never invent laboratory values, diagnoses, medications, doses,
   medical references, or patient information.
4. Give general medical information and safe next steps.
5. If the situation may be an emergency, clearly tell the user
   to contact local emergency services or go to the nearest emergency department.
6. For severe symptoms such as chest pain, severe breathing difficulty,
   stroke-like symptoms, severe bleeding, loss of consciousness,
   seizures, poisoning, suicidal thoughts, or serious allergic reaction,
   prioritize urgent professional help.
7. Do not recommend prescription medication changes as if you are the patient's doctor.
8. If a medication is mentioned, explain general information,
   important precautions, and advise checking with a pharmacist/doctor.
9. For children, pregnancy, elderly people, serious chronic illness,
   or complex medication combinations, recommend professional evaluation.
10. Do not diagnose from a single symptom.
11. Ask relevant follow-up questions when necessary.
12. Use clear, simple language.

LANGUAGE:

The user may speak Pashto, Dari, Persian, Urdu, Arabic, or English.

Reply in the same language as the user whenever possible.

For Pashto:
- Use natural, understandable Pashto.
- Avoid unnecessary English.
- Medical English terms can be included in parentheses when useful.

RESPONSE FORMAT:

Use short sections when appropriate:

لنډ ځواب
احتمالي لاملونه
څه وکړم؟
کله ډاکټر ته لاړ شم؟
بیړنی حالت

Do not pretend that you examined the patient.
Do not claim to have access to medical records unless they are explicitly provided.

This is educational medical information, not a personal diagnosis.
"""


# =========================================================
# Gemini API
# =========================================================

def gemini_request(user_text, history=None):
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured on the server."
        )

    user_text = clean_text(user_text)

    if not user_text:
        raise ValueError("Message is empty.")

    contents = []

    # Conversation history
    if isinstance(history, list):
        history = history[-MAX_HISTORY:]

        for item in history:
            if not isinstance(item, dict):
                continue

            role = item.get("role")
            text = clean_text(item.get("text", ""), MAX_TEXT)

            if not text:
                continue

            if role == "user":
                contents.append({
                    "role": "user",
                    "parts": [
                        {"text": text}
                    ]
                })

            elif role in ("assistant", "model"):
                contents.append({
                    "role": "model",
                    "parts": [
                        {"text": text}
                    ]
                })

    # Make sure final turn is the new user message.
    if not contents or contents[-1].get("role") != "user":
        contents.append({
            "role": "user",
            "parts": [
                {"text": user_text}
            ]
        })
    else:
        # If frontend already included the same final message,
        # don't duplicate it.
        last_text = (
            contents[-1]
            .get("parts", [{}])[0]
            .get("text", "")
        )

        if last_text != user_text:
            contents.append({
                "role": "user",
                "parts": [
                    {"text": user_text}
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
            "maxOutputTokens": 4096
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
            timeout=55
        )
    except requests.RequestException as exc:
        logger.exception("Gemini connection error")
        raise RuntimeError(
            "AI service could not be reached."
        ) from exc

    if response.status_code >= 400:
        logger.error(
            "Gemini error %s: %s",
            response.status_code,
            response.text[:2000]
        )

        try:
            data = response.json()
            message = (
                data.get("error", {}).get("message")
                or "Gemini API request failed."
            )
        except Exception:
            message = "Gemini API request failed."

        raise RuntimeError(message)

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "AI returned invalid JSON."
        ) from exc

    text_parts = []

    for candidate in data.get("candidates", []):
        content = candidate.get("content", {})

        for part in content.get("parts", []):
            text = part.get("text")

            if text:
                text_parts.append(text)

    answer = "\n".join(text_parts).strip()

    if not answer:
        # Some responses may contain a direct text field.
        answer = str(data.get("text", "")).strip()

    if not answer:
        raise RuntimeError(
            "AI returned no readable answer."
        )

    return answer


# =========================================================
# Routes
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return render_template_string(PAGE)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "service": "MedAI",
        "model": GEMINI_MODEL,
        "gemini_configured": bool(GEMINI_API_KEY)
    })


@app.route("/api/chat", methods=["POST"])
def api_chat():
    if not rate_limit_check():
        return error_response(
            "Too many requests. Please wait a little and try again.",
            429
        )

    data = json_body()

    message = clean_text(data.get("message", ""))
    history = data.get("history", [])

    if not message:
        return error_response(
            "مهرباني وکړئ خپله پوښتنه ولیکئ.",
            400
        )

    if len(message) > MAX_TEXT:
        return error_response(
            "پیغام ډېر اوږد دی.",
            413
        )

    try:
        answer = gemini_request(
            message,
            history
        )

        return jsonify({
            "ok": True,
            "answer": answer,
            "model": GEMINI_MODEL
        })

    except ValueError as exc:
        return error_response(str(exc), 400)

    except RuntimeError as exc:
        logger.exception("Medical AI error")

        return error_response(
            str(exc),
            502
        )

    except Exception:
        logger.exception("Unexpected server error")

        return error_response(
            "Unexpected server error.",
            500
        )


# =========================================================
# Error Handlers
# =========================================================

@app.errorhandler(413)
def request_too_large(error):
    return error_response(
        "Request is too large.",
        413
    )


@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return error_response(
            "API endpoint not found.",
            404
        )

    return render_template_string(PAGE), 200


@app.errorhandler(500)
def internal_error(error):
    logger.exception("Internal server error")
    return error_response(
        "Internal server error.",
        500
    )


# =========================================================
# FRONTEND
# =========================================================

PAGE = r"""
<!DOCTYPE html>
<html lang="ps" dir="rtl">
<head>
<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0,
               maximum-scale=1.0, viewport-fit=cover">

<meta name="theme-color" content="#0b1220">

<title>MedAI — Medical AI Assistant</title>

<style>

:root {
    --bg: #f5f7fb;
    --panel: #ffffff;
    --panel2: #eef3f8;
    --text: #172033;
    --muted: #697386;
    --primary: #1677ff;
    --primary2: #005ce6;
    --danger: #dc2626;
    --success: #16a34a;
    --border: #dfe5ec;
    --shadow: 0 10px 30px rgba(0,0,0,.08);
}

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    width: 100%;
    height: 100%;
    font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}

body {
    background: var(--bg);
    color: var(--text);
    overflow: hidden;
}

button,
input,
textarea {
    font: inherit;
}

button {
    cursor: pointer;
}

.app {
    display: flex;
    width: 100%;
    height: 100vh;
}

.sidebar {
    width: 285px;
    background: var(--panel);
    border-left: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    z-index: 20;
}

.brand {
    padding: 22px;
    border-bottom: 1px solid var(--border);
}

.brand-title {
    font-size: 26px;
    font-weight: 900;
}

.brand-title span {
    color: var(--primary);
}

.brand-subtitle {
    color: var(--muted);
    font-size: 13px;
    margin-top: 5px;
}

.sidebar-scroll {
    flex: 1;
    overflow-y: auto;
    padding: 14px;
}

.section-title {
    color: var(--muted);
    font-size: 12px;
    font-weight: 800;
    margin: 14px 8px 8px;
}

.menu-btn {
    width: 100%;
    border: 0;
    background: transparent;
    padding: 11px 12px;
    margin-bottom: 3px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--text);
    text-align: right;
}

.menu-btn:hover {
    background: var(--panel2);
}

.menu-icon {
    width: 30px;
    text-align: center;
}

.sidebar-bottom {
    padding: 12px;
    border-top: 1px solid var(--border);
}

.main {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
}

.topbar {
    height: 70px;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
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
}

.page-title {
    font-size: 18px;
    font-weight: 900;
}

.status {
    font-size: 12px;
    color: var(--success);
}

.top-actions {
    display: flex;
    gap: 8px;
}

.icon-btn {
    width: 42px;
    height: 42px;
    border: 1px solid var(--border);
    background: var(--panel);
    border-radius: 12px;
}

.chat-area {
    flex: 1;
    overflow-y: auto;
    padding: 28px;
}

.chat-container {
    width: min(950px, 100%);
    margin: auto;
}

.welcome {
    text-align: center;
    padding: 35px 10px 25px;
}

.logo-circle {
    width: 72px;
    height: 72px;
    border-radius: 22px;
    margin: auto;
    display: grid;
    place-items: center;
    font-size: 34px;
    background: var(--primary);
    color: white;
    box-shadow: var(--shadow);
}

.welcome h1 {
    margin: 18px 0 8px;
    font-size: 30px;
}

.welcome p {
    margin: 0;
    color: var(--muted);
}

.quick-grid {
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(150px, 1fr));
    gap: 10px;
    margin: 25px auto;
    max-width: 800px;
}

.quick-btn {
    border: 1px solid var(--border);
    background: var(--panel);
    border-radius: 15px;
    padding: 14px;
    text-align: right;
    box-shadow: 0 4px 12px rgba(0,0,0,.03);
}

.quick-btn:hover {
    border-color: var(--primary);
    transform: translateY(-1px);
}

.messages {
    display: flex;
    flex-direction: column;
    gap: 18px;
}

.message {
    display: flex;
    gap: 10px;
    max-width: 88%;
}

.message.user {
    margin-right: auto;
    flex-direction: row-reverse;
}

.avatar {
    flex: 0 0 38px;
    width: 38px;
    height: 38px;
    border-radius: 12px;
    display: grid;
    place-items: center;
    background: var(--primary);
    color: white;
    font-weight: 900;
}

.user .avatar {
    background: #111827;
}

.bubble {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 13px 15px;
    line-height: 1.8;
    white-space: pre-wrap;
    word-break: break-word;
    box-shadow: 0 3px 10px rgba(0,0,0,.03);
}

.user .bubble {
    background: var(--primary);
    color: white;
    border-color: var(--primary);
}

.typing {
    display: inline-flex;
    gap: 4px;
    align-items: center;
}

.typing i {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--muted);
    animation: blink 1s infinite;
}

.typing i:nth-child(2) {
    animation-delay: .15s;
}

.typing i:nth-child(3) {
    animation-delay: .3s;
}

@keyframes blink {
    0%, 80%, 100% {
        opacity: .2;
    }
    40% {
        opacity: 1;
    }
}

.composer-wrap {
    background: var(--panel);
    border-top: 1px solid var(--border);
    padding: 12px 18px 16px;
}

.composer {
    width: min(950px, 100%);
    margin: auto;
    display: flex;
    align-items: flex-end;
    gap: 8px;
    background: var(--panel);
}

.input-box {
    flex: 1;
    position: relative;
}

textarea {
    width: 100%;
    min-height: 52px;
    max-height: 160px;
    resize: none;
    border: 1px solid var(--border);
    border-radius: 17px;
    padding: 14px 50px 14px 14px;
    outline: none;
    background: var(--bg);
    color: var(--text);
}

textarea:focus {
    border-color: var(--primary);
}

.send-btn,
.voice-btn {
    width: 52px;
    height: 52px;
    border: 0;
    border-radius: 16px;
    color: white;
    background: var(--primary);
}

.voice-btn {
    background: #111827;
}

.voice-btn.active {
    background: var(--danger);
    animation: pulse 1.2s infinite;
}

@keyframes pulse {
    50% {
        transform: scale(1.05);
    }
}

.composer-note {
    width: min(950px, 100%);
    margin: 8px auto 0;
    color: var(--muted);
    font-size: 11px;
    text-align: center;
}

.overlay {
    display: none;
}

.toast {
    position: fixed;
    left: 20px;
    bottom: 20px;
    background: #111827;
    color: white;
    padding: 12px 16px;
    border-radius: 12px;
    z-index: 100;
    opacity: 0;
    transform: translateY(15px);
    pointer-events: none;
    transition: .25s;
}

.toast.show {
    opacity: 1;
    transform: translateY(0);
}

.voice-status {
    display: none;
    position: fixed;
    left: 50%;
    top: 80px;
    transform: translateX(-50%);
    background: var(--danger);
    color: white;
    padding: 10px 18px;
    border-radius: 20px;
    z-index: 50;
    font-size: 13px;
    box-shadow: var(--shadow);
}

.voice-status.show {
    display: block;
}

.dark {
    --bg: #0b1220;
    --panel: #111827;
    --panel2: #182235;
    --text: #f1f5f9;
    --muted: #94a3b8;
    --border: #263247;
    --shadow: 0 10px 30px rgba(0,0,0,.3);
}

@media (max-width: 850px) {

    .sidebar {
        position: fixed;
        top: 0;
        right: -300px;
        height: 100%;
        transition: right .25s ease;
        box-shadow: var(--shadow);
    }

    .sidebar.open {
        right: 0;
    }

    .mobile-menu {
        display: grid;
        place-items: center;
    }

    .overlay.show {
        display: block;
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,.35);
        z-index: 15;
    }

    .chat-area {
        padding: 14px;
    }

    .message {
        max-width: 96%;
    }

    .welcome h1 {
        font-size: 25px;
    }

    .quick-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .topbar {
        height: 62px;
    }

}

</style>
</head>

<body>

<div class="app">

    <aside class="sidebar" id="sidebar">

        <div class="brand">
            <div class="brand-title">
                Med<span>AI</span>
            </div>
            <div class="brand-subtitle">
                Medical AI Assistant
            </div>
        </div>

        <div class="sidebar-scroll">

            <div class="section-title">
                طبي وسایل
            </div>

            <button class="menu-btn"
                    onclick="quickPrompt('زما نښې تحلیل کړه. نښې مې دا دي: ')">
                <span class="menu-icon">🩺</span>
                <span>Symptoms Checker</span>
            </button>

            <button class="menu-btn"
                    onclick="quickPrompt('زما vital signs دا دي: عمر، تبه، د وینې فشار، نبض، SpO2. مهرباني وکړئ عمومي تشریح یې کړئ.')">
                <span class="menu-icon">❤️</span>
                <span>Vital Signs</span>
            </button>

            <button class="menu-btn"
                    onclick="quickPrompt('د دې دوو ناروغیو ترمنځ توپیر راته تشریح کړه: ')">
                <span class="menu-icon">⚖️</span>
                <span>Disease Compare</span>
            </button>

            <button class="menu-btn"
                    onclick="quickPrompt('زه د ډاکټر سره د لیدنې لپاره دا معلومات منظمول غواړم: ')">
                <span class="menu-icon">👨‍⚕️</span>
                <span>Doctor Assistant</span>
            </button>

            <button class="menu-btn"
                    onclick="quickPrompt('دا د لابراتوار راپور دی. په ساده ژبه یې تشریح کړه او ووایه کوم موارد د ډاکټر سره شریک کړم: ')">
                <span class="menu-icon">🧪</span>
                <span>Lab Report</span>
            </button>

            <button class="menu-btn"
                    onclick="quickPrompt('د دې دوا په اړه عمومي معلومات راکړه: نوم، استعمال، عام عوارض، مهم احتیاطونه او interactions: ')">
                <span class="menu-icon">💊</span>
                <span>Medicine Info</span>
            </button>

            <button class="menu-btn"
                    onclick="quickPrompt('دا طبي اصطلاح په ساده پښتو تشریح کړه: ')">
                <span class="menu-icon">📖</span>
                <span>Medical Dictionary</span>
            </button>

            <button class="menu-btn"
                    onclick="quickPrompt('زما د نښو له مخې راته ووایه چې ایا بیړنۍ طبي پاملرنې ته اړتیا لیدل کېږي: ')">
                <span class="menu-icon">🚨</span>
                <span>Emergency Checker</span>
            </button>

            <button class="menu-btn"
                    onclick="quickPrompt('د لاندې دواګانو د interaction په اړه عمومي معلومات راکړه: ')">
                <span class="menu-icon">⚠️</span>
                <span>Drug Interaction</span>
            </button>

            <button class="menu-btn"
                    onclick="quickPrompt('د دې حالت لپاره لومړنۍ مرستې څه دي؟ حالت: ')">
                <span class="menu-icon">🆘</span>
                <span>First Aid</span>
            </button>

            <button class="menu-btn"
                    onclick="quickPrompt('د دې معلوماتو پر اساس عمومي health risk factors تشریح کړه: ')">
                <span class="menu-icon">📊</span>
                <span>Risk Assessment</span>
            </button>

            <button class="menu-btn"
                    onclick="quickPrompt('زما د روغتیا لپاره یو منظم عمومي health report جوړ کړه. معلومات: ')">
                <span class="menu-icon">📋</span>
                <span>Health Report</span>
            </button>

            <button class="menu-btn"
                    onclick="quickPrompt('د دې طبي موضوع په اړه یو لنډ quiz جوړ کړه: ')">
                <span class="menu-icon">🧠</span>
                <span>Medical Quiz</span>
            </button>

            <div class="section-title">
                شخصي
            </div>

            <button class="menu-btn" onclick="showHistory()">
                <span class="menu-icon">🕘</span>
                <span>History</span>
            </button>

            <button class="menu-btn" onclick="showFavorites()">
                <span class="menu-icon">⭐</span>
                <span>Favorites</span>
            </button>

            <button class="menu-btn" onclick="showTracker()">
                <span class="menu-icon">📈</span>
                <span>Health Tracker</span>
            </button>

            <button class="menu-btn" onclick="showReminders()">
                <span class="menu-icon">⏰</span>
                <span>Medicine Reminders</span>
            </button>

        </div>

        <div class="sidebar-bottom">

            <button class="menu-btn"
                    onclick="toggleDarkMode()">
                <span class="menu-icon">🌙</span>
                <span>Dark Mode</span>
            </button>

            <button class="menu-btn"
                    onclick="clearChat()">
                <span class="menu-icon">🗑️</span>
                <span>New Chat</span>
            </button>

        </div>

    </aside>

    <div class="overlay"
         id="overlay"
         onclick="closeSidebar()">
    </div>

    <main class="main">

        <header class="topbar">

            <div class="top-left">

                <button class="icon-btn mobile-menu"
                        onclick="openSidebar()">
                    ☰
                </button>

                <div>
                    <div class="page-title">
                        MedAI
                    </div>

                    <div class="status">
                        ● AI Online
                    </div>
                </div>

            </div>

            <div class="top-actions">

                <button class="icon-btn"
                        onclick="toggleDarkMode()"
                        title="Dark Mode">
                    🌙
                </button>

                <button class="icon-btn"
                        onclick="newChat()"
                        title="New Chat">
                    ＋
                </button>

            </div>

        </header>

        <div class="voice-status"
             id="voiceStatus">
            🎙️ د غږ حالت فعال دی — خبرې وکړئ
        </div>

        <section class="chat-area"
                 id="chatArea">

            <div class="chat-container">

                <div class="welcome"
                     id="welcome">

                    <div class="logo-circle">
                        🩺
                    </div>

                    <h1>
                        MedAI ته ښه راغلاست
                    </h1>

                    <p>
                        خپل طبي سوال په پښتو، دري، اردو یا English ولیکئ یا خبرې وکړئ.
                    </p>

                    <div class="quick-grid">

                        <button class="quick-btn"
                                onclick="quickPrompt('زه تبه لرم او بدن مې درد کوي. عمومي معلومات راکړه.')">
                            🌡️ تبه او بدن درد
                        </button>

                        <button class="quick-btn"
                                onclick="quickPrompt('د لوړ فشار په اړه معلومات راکړه.')">
                            ❤️ لوړ فشار
                        </button>

                        <button class="quick-btn"
                                onclick="quickPrompt('د معدې درد عام لاملونه څه دي؟')">
                            🩻 د معدې درد
                        </button>

                        <button class="quick-btn"
                                onclick="quickPrompt('د سر درد کوم وخت بیړنی حالت ګڼل کېږي؟')">
                            🧠 سر درد
                        </button>

                        <button class="quick-btn"
                                onclick="quickPrompt('د شکر ناروغۍ عامې نښې کومې دي؟')">
                            🩸 شکر
                        </button>

                        <button class="quick-btn"
                                onclick="quickPrompt('د عام زکام او فلو ترمنځ توپیر څه دی؟')">
                            🤧 زکام / فلو
                        </button>

                    </div>

                </div>

                <div class="messages"
                     id="messages">
                </div>

            </div>

        </section>

        <div class="composer-wrap">

            <div class="composer">

                <button class="voice-btn"
                        id="voiceButton"
                        onclick="toggleVoiceMode()"
                        title="Voice Mode">
                    🎙️
                </button>

                <div class="input-box">

                    <textarea
                        id="messageInput"
                        placeholder="خپله طبي پوښتنه ولیکئ..."
                        rows="1"></textarea>

                </div>

                <button class="send-btn"
                        id="sendButton"
                        onclick="sendMessage()">
                    ➤
                </button>

            </div>

            <div class="composer-note">
                MedAI طبي معلومات وړاندې کوي؛ د جدي یا بیړني حالت لپاره له مسلکي روغتیايي کارکوونکي سره اړیکه ونیسئ.
            </div>

        </div>

    </main>

</div>

<div class="toast"
     id="toast">
</div>


<script>

/* ========================================================
   State
   ======================================================== */

let messages = [];
let favorites = [];
let tracker = [];
let reminders = [];

let voiceMode = false;
let recognition = null;
let recognitionRunning = false;
let speaking = false;
let waitingForAI = false;


/* ========================================================
   Storage
   ======================================================== */

function loadStorage() {

    try {
        messages =
            JSON.parse(
                localStorage.getItem("medai_messages") || "[]"
            );

        favorites =
            JSON.parse(
                localStorage.getItem("medai_favorites") || "[]"
            );

        tracker =
            JSON.parse(
                localStorage.getItem("medai_tracker") || "[]"
            );

        reminders =
            JSON.parse(
                localStorage.getItem("medai_reminders") || "[]"
            );

    } catch (e) {

        messages = [];
        favorites = [];
        tracker = [];
        reminders = [];
    }

}


function saveStorage() {

    localStorage.setItem(
        "medai_messages",
        JSON.stringify(messages.slice(-100))
    );

    localStorage.setItem(
        "medai_favorites",
        JSON.stringify(favorites.slice(-100))
    );

    localStorage.setItem(
        "medai_tracker",
        JSON.stringify(tracker.slice(-200))
    );

    localStorage.setItem(
        "medai_reminders",
        JSON.stringify(reminders.slice(-100))
    );

}


/* ========================================================
   UI
   ======================================================== */

function $(id) {
    return document.getElementById(id);
}


function showToast(text) {

    const toast = $("toast");

    toast.textContent = text;
    toast.classList.add("show");

    clearTimeout(showToast.timer);

    showToast.timer =
        setTimeout(() => {
            toast.classList.remove("show");
        }, 2600);

}


function openSidebar() {

    $("sidebar").classList.add("open");
    $("overlay").classList.add("show");

}


function closeSidebar() {

    $("sidebar").classList.remove("open");
    $("overlay").classList.remove("show");

}


function toggleDarkMode() {

    document.body.classList.toggle("dark");

    localStorage.setItem(
        "medai_dark",
        document.body.classList.contains("dark")
            ? "1"
            : "0"
    );

}


function loadDarkMode() {

    if (
        localStorage.getItem("medai_dark") === "1"
    ) {
        document.body.classList.add("dark");
    }

}


function scrollBottom() {

    const area = $("chatArea");

    area.scrollTop = area.scrollHeight;

}


function addMessage(role, text, options = {}) {

    const messagesEl = $("messages");

    $("welcome").style.display = "none";

    const wrapper =
        document.createElement("div");

    wrapper.className =
        "message " + role;

    const avatar =
        document.createElement("div");

    avatar.className = "avatar";

    avatar.textContent =
        role === "user"
            ? "👤"
            : "🩺";

    const bubble =
        document.createElement("div");

    bubble.className = "bubble";

    bubble.textContent = text;

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);

    messagesEl.appendChild(wrapper);

    if (!options.skipStore) {

        messages.push({
            role: role,
            text: text,
            time: Date.now()
        });

        saveStorage();

    }

    scrollBottom();

    return wrapper;
}


function addTyping() {

    $("welcome").style.display = "none";

    const wrapper =
        document.createElement("div");

    wrapper.className =
        "message assistant";

    wrapper.id = "typingMessage";

    const avatar =
        document.createElement("div");

    avatar.className = "avatar";
    avatar.textContent = "🩺";

    const bubble =
        document.createElement("div");

    bubble.className = "bubble";

    bubble.innerHTML =
        '<span class="typing">' +
        '<i></i><i></i><i></i>' +
        '</span>';

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);

    $("messages").appendChild(wrapper);

    scrollBottom();

}


function removeTyping() {

    const el =
        $("typingMessage");

    if (el) {
        el.remove();
    }

}


function renderStoredMessages() {

    const messagesEl =
        $("messages");

    messagesEl.innerHTML = "";

    if (!messages.length) {

        $("welcome").style.display = "block";
        return;

    }

    $("welcome").style.display = "none";

    messages.forEach(item => {

        addMessage(
            item.role,
            item.text,
            { skipStore: true }
        );

    });

}


/* ========================================================
   Chat
   ======================================================== */

function quickPrompt(text) {

    $("messageInput").value = text;
    $("messageInput").focus();

    closeSidebar();

}


function newChat() {

    messages = [];

    saveStorage();

    $("messages").innerHTML = "";
    $("welcome").style.display = "block";

    showToast("نوې خبرې پیل شوې.");

}


function clearChat() {

    newChat();

}


async function sendMessage(customText = null) {

    if (waitingForAI) {
        return;
    }

    let text =
        customText !== null
            ? customText
            : $("messageInput").value.trim();

    if (!text) {
        return;
    }

    if (text.length > 12000) {

        showToast(
            "پیغام ډېر اوږد دی."
        );

        return;
    }

    $("messageInput").value = "";

    addMessage(
        "user",
        text
    );

    addTyping();

    waitingForAI = true;

    $("sendButton").disabled = true;

    try {

        const history =
            messages
                .slice(-17, -1)
                .map(item => ({
                    role:
                        item.role === "assistant"
                            ? "assistant"
                            : "user",
                    text: item.text
                }));

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
                        history: history
                    })
                }
            );

        let data;

        try {
            data = await response.json();
        } catch (e) {
            throw new Error(
                "Server returned invalid response."
            );
        }

        removeTyping();

        if (!response.ok || !data.ok) {

            throw new Error(
                data.error ||
                "AI service error."
            );

        }

        const answer =
            String(data.answer || "").trim();

        if (!answer) {
            throw new Error(
                "AI returned an empty answer."
            );
        }

        addMessage(
            "assistant",
            answer
        );

        if (voiceMode) {
            speakAnswer(answer);
        }

    } catch (error) {

        removeTyping();

        const message =
            error?.message ||
            "Unknown error.";

        addMessage(
            "assistant",
            "بخښنه، ستونزه رامنځته شوه:\n\n" +
            message
        );

        showToast(
            "AI خدمت کې ستونزه ده."
        );

    } finally {

        waitingForAI = false;
        $("sendButton").disabled = false;

        if (
            voiceMode &&
            !speaking &&
            !recognitionRunning
        ) {
            setTimeout(
                startRecognition,
                700
            );
        }

    }

}


/* ========================================================
   Enter / textarea
   ======================================================== */

$("messageInput").addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();
            sendMessage();

        }

    }
);


$("messageInput").addEventListener(
    "input",
    function() {

        this.style.height = "auto";

        this.style.height =
            Math.min(
                this.scrollHeight,
                160
            ) + "px";

    }
);


/* ========================================================
   Voice Recognition
   ======================================================== */

function createRecognition() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        return null;
    }

    const rec =
        new SpeechRecognition();

    rec.lang = "ps-AF";
    rec.continuous = false;
    rec.interimResults = true;
    rec.maxAlternatives = 1;

    rec.onstart = function() {

        recognitionRunning = true;

        $("voiceButton")
            .classList.add("active");

        $("voiceStatus")
            .classList.add("show");

    };


    rec.onresult = function(event) {

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

        const current =
            (
                finalText ||
                interimText
            ).trim();

        if (current) {
            $("messageInput").value = current;
        }

        if (finalText.trim()) {

            const message =
                finalText.trim();

            setTimeout(
                () => sendMessage(message),
                100
            );

        }

    };


    rec.onerror = function(event) {

        recognitionRunning = false;

        console.warn(
            "Speech recognition error:",
            event.error
        );

        if (
            event.error === "not-allowed" ||
            event.error === "service-not-allowed"
        ) {

            voiceMode = false;

            $("voiceButton")
                .classList.remove("active");

            $("voiceStatus")
                .classList.remove("show");

            showToast(
                "د مایکروفون اجازه ورکړئ."
            );

        }

    };


    rec.onend = function() {

        recognitionRunning = false;

        if (!voiceMode) {

            $("voiceButton")
                .classList.remove("active");

            $("voiceStatus")
                .classList.remove("show");

            return;
        }

        if (
            waitingForAI ||
            speaking
        ) {

            return;

        }

        setTimeout(
            startRecognition,
            500
        );

    };

    return rec;

}


function startRecognition() {

    if (!voiceMode) {
        return;
    }

    if (recognitionRunning) {
        return;
    }

    if (waitingForAI || speaking) {
        return;
    }

    if (!recognition) {

        recognition =
            createRecognition();

        if (!recognition) {

            showToast(
                "ستاسې براوزر Voice Recognition نه ملاتړ کوي."
            );

            voiceMode = false;
            return;
        }

    }

    try {

        recognition.start();

    } catch (e) {

        console.warn(
            "Recognition start failed",
            e
        );

    }

}


function stopRecognition() {

    if (!recognition) {
        return;
    }

    try {
        recognition.stop();
    } catch (e) {}

    recognitionRunning = false;

}


function toggleVoiceMode() {

    voiceMode =
        !voiceMode;

    if (voiceMode) {

        startRecognition();

        showToast(
            "Voice Mode فعال شو."
        );

    } else {

        stopRecognition();

        speechSynthesis.cancel();

        speaking = false;

        $("voiceButton")
            .classList.remove("active");

        $("voiceStatus")
            .classList.remove("show");

        showToast(
            "Voice Mode بند شو."
        );

    }

}


/* ========================================================
   Voice Output
   ======================================================== */

function choosePashtoVoice() {

    const voices =
        speechSynthesis.getVoices();

    if (!voices.length) {
        return null;
    }

    return (
        voices.find(v =>
            /^ps(-|_)/i.test(v.lang)
        ) ||

        voices.find(v =>
            /^fa(-|_)/i.test(v.lang)
        ) ||

        voices.find(v =>
            /^ur(-|_)/i.test(v.lang)
        ) ||

        voices.find(v =>
            /^ar(-|_)/i.test(v.lang)
        ) ||

        voices.find(v =>
            /^en(-|_)/i.test(v.lang)
        ) ||

        voices[0]
    );

}


function speakAnswer(text) {

    if (
        !("speechSynthesis" in window)
    ) {
        return;
    }

    speechSynthesis.cancel();

    const utterance =
        new SpeechSynthesisUtterance(
            text
        );

    const voice =
        choosePashtoVoice();

    if (voice) {

        utterance.voice = voice;
        utterance.lang = voice.lang;

    } else {

        utterance.lang = "ps-AF";

    }

    utterance.rate = 0.95;
    utterance.pitch = 1;

    speaking = true;

    utterance.onend = function() {

        speaking = false;

        if (
            voiceMode &&
            !waitingForAI
        ) {

            setTimeout(
                startRecognition,
                400
            );

        }

    };

    utterance.onerror = function() {

        speaking = false;

        if (
            voiceMode &&
            !waitingForAI
        ) {

            setTimeout(
                startRecognition,
                400
            );

        }

    };

    speechSynthesis.speak(
        utterance
    );

}


/* ========================================================
   History
   ======================================================== */

function showHistory() {

    closeSidebar();

    if (!messages.length) {

        showToast(
            "History خالي دی."
        );

        return;

    }

    const last =
        messages
            .slice(-10)
            .map(
                x =>
                    (
                        x.role === "user"
                            ? "👤 "
                            : "🩺 "
                    ) +
                    x.text
            )
            .join("\n\n");

    alert(
        "Recent History\n\n" +
        last
    );

}


/* ========================================================
   Favorites
   ======================================================== */

function showFavorites() {

    closeSidebar();

    if (!favorites.length) {

        showToast(
            "Favorites خالي دي."
        );

        return;

    }

    alert(
        "Favorites:\n\n" +
        favorites
            .map(
                (x, i) =>
                    `${i + 1}. ${x}`
            )
            .join("\n\n")
    );

}


/* ========================================================
   Health Tracker
   ======================================================== */

function showTracker() {

    closeSidebar();

    const input =
        prompt(
            "Tracker ته څه ثبتول غواړئ؟\nمثال: BP 120/80"
        );

    if (!input) {
        return;
    }

    tracker.push({
        text: input,
        time: new Date().toISOString()
    });

    saveStorage();

    showToast(
        "Health Tracker کې ثبت شو."
    );

}


/* ========================================================
   Medicine Reminders
   ======================================================== */

function showReminders() {

    closeSidebar();

    const name =
        prompt(
            "د دوا نوم ولیکئ:"
        );

    if (!name) {
        return;
    }

    const timeText =
        prompt(
            "وخت ولیکئ، مثال 14:30"
        );

    if (!timeText) {
        return;
    }

    if (
        !/^\d{1,2}:\d{2}$/.test(
            timeText
        )
    ) {

        showToast(
            "وخت باید HH:MM وي."
        );

        return;

    }

    reminders.push({
        id: Date.now(),
        name: name,
        time: timeText,
        notified: false
    });

    saveStorage();

    requestNotificationPermission();

    showToast(
        `Reminder جوړ شو: ${name} - ${timeText}`
    );

}


async function requestNotificationPermission() {

    if (
        "Notification" in window &&
        Notification.permission === "default"
    ) {

        try {
            await Notification.requestPermission();
        } catch (e) {}

    }

}


function checkReminders() {

    if (!reminders.length) {
        return;
    }

    const now =
        new Date();

    const hh =
        String(
            now.getHours()
        ).padStart(2, "0");

    const mm =
        String(
            now.getMinutes()
        ).padStart(2, "0");

    const current =
        `${hh}:${mm}`;

    let changed = false;

    reminders.forEach(reminder => {

        if (
            reminder.time === current &&
            !reminder.notified
        ) {

            reminder.notified = true;

            changed = true;

            const message =
                `د دوا وخت دی: ${reminder.name}`;

            showToast(message);

            if (
                "Notification" in window &&
                Notification.permission === "granted"
            ) {

                try {

                    new Notification(
                        "MedAI Medicine Reminder",
                        {
                            body: message
                        }
                    );

                } catch (e) {}

            }

        }

        if (
            reminder.time !== current
        ) {

            reminder.notified = false;

        }

    });

    if (changed) {
        saveStorage();
    }

}

setInterval(
    checkReminders,
    30000
);


/* ========================================================
   Startup
   ======================================================== */

loadStorage();
loadDarkMode();
renderStoredMessages();

if (
    "speechSynthesis" in window
) {

    speechSynthesis.onvoiceschanged =
        function() {};

}

</script>

</body>
</html>
"""


# =========================================================
# Local Development
# =========================================================

if __name__ == "__main__":
    port = int(
        os.getenv("PORT", "5000")
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
