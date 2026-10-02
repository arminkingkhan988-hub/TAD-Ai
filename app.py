import os
import re
import time
import html
import logging
from functools import wraps

import requests
from flask import Flask, request, jsonify, render_template_string, make_response

# =========================================================
# MedAI - Single File Medical AI Assistant
# Developer: Toyebullah Dawoodzay
# =========================================================

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 512 * 1024  # 512 KB

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"

MAX_TEXT = 12000
RATE_WINDOW = 60
RATE_LIMIT = 30

request_log = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medai")


# ---------------------------------------------------------
# Security
# ---------------------------------------------------------

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "microphone=(self), camera=(self), geolocation=()"
    )
    response.headers["Cache-Control"] = "no-store"
    return response


def rate_limit():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
    ip = ip.split(",")[0].strip()

    now = time.time()
    bucket = request_log.setdefault(ip, [])

    bucket[:] = [t for t in bucket if now - t < RATE_WINDOW]

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


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def clean_text(value, max_len=MAX_TEXT):
    if value is None:
        return ""

    value = str(value)
    value = value.replace("\x00", "")
    value = value.strip()

    if len(value) > max_len:
        value = value[:max_len]

    return value


def json_body():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {}

    return data


def medical_system_prompt():
    return """
You are MedAI, an educational medical AI assistant.

Developer: Toyebullah Dawoodzay
Year: 2026

IMPORTANT MEDICAL SAFETY RULES:
- Give educational medical information.
- Do not claim to be a human doctor.
- Do not diagnose a person with certainty from symptoms alone.
- Do not invent medical facts, test results, medicines, or citations.
- Clearly mention uncertainty when information is insufficient.
- Do not provide personalized prescription dosing.
- Do not tell a person to start, stop, or change prescription medicine without a qualified clinician.
- For emergency warning signs, tell the user to seek urgent/emergency medical care.
- If chest pain, severe breathing difficulty, severe allergic reaction, stroke-like symptoms, uncontrolled bleeding, seizure, loss of consciousness, severe poisoning, or another potentially life-threatening emergency is described, prioritize emergency advice.
- Keep answers understandable.
- When the user writes Pashto, answer in Pashto.
- When the user writes English, answer in English.
- You can understand Pashto, Dari, Urdu, and English.
- Do not unnecessarily frighten the user.
- Do not make definitive claims about a patient's condition without examination/testing.
- For medicines, explain general uses, common risks, interactions, and when professional advice is needed.
- For lab results, explain possible meanings but emphasize that reference ranges and clinical context matter.
- For children, pregnancy, elderly people, or serious chronic conditions, recommend professional medical evaluation when appropriate.

You are an educational assistant, not a replacement for a doctor.
"""


def gemini_request(user_text, previous_id=None):
    if not GEMINI_API_KEY:
        return {
            "ok": False,
            "error": (
                "GEMINI_API_KEY is not configured on the server."
            )
        }

    user_text = clean_text(user_text)

    if not user_text:
        return {
            "ok": False,
            "error": "Please enter a message."
        }

    payload = {
        "model": GEMINI_MODEL,
        "input": user_text,
        "system_instruction": medical_system_prompt()
    }

    if previous_id:
        payload["previous_interaction_id"] = clean_text(
            previous_id, 300
        )

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
            logger.error(
                "Gemini error %s: %s",
                response.status_code,
                response.text[:1000]
            )

            return {
                "ok": False,
                "error": "AI service returned an error. Please try again."
            }

        data = response.json()

        output = data.get("output_text")

        if not output:
            steps = data.get("steps", [])

            texts = []

            for step in steps:
                if step.get("type") != "model_output":
                    continue

                content = step.get("content", [])

                for block in content:
                    if block.get("type") == "text":
                        text_value = block.get("text", "")
                        if text_value:
                            texts.append(text_value)

            output = "\n".join(texts).strip()

        if not output:
            return {
                "ok": False,
                "error": "The AI returned an empty response."
            }

        return {
            "ok": True,
            "text": output,
            "interaction_id": data.get("id")
        }

    except requests.Timeout:
        return {
            "ok": False,
            "error": "AI request timed out. Please try again."
        }

    except requests.RequestException:
        return {
            "ok": False,
            "error": "Could not connect to the AI service."
        }

    except Exception as exc:
        logger.exception("Unexpected Gemini error: %s", exc)

        return {
            "ok": False,
            "error": "An unexpected server error occurred."
        }


# ---------------------------------------------------------
# Main page
# ---------------------------------------------------------

PAGE = r"""
<!DOCTYPE html>
<html lang="ps" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<meta name="theme-color" content="#0b7285">
<meta name="description"
      content="MedAI - Medical AI Assistant">

<title>MedAI - Medical AI</title>

<style>

* {
    box-sizing: border-box;
}

:root {
    --bg: #f5f7fa;
    --panel: #ffffff;
    --panel2: #f0f4f7;
    --text: #17212b;
    --muted: #6b7785;
    --primary: #087f8c;
    --primary2: #0b7285;
    --border: #dfe5ea;
    --danger: #c92a2a;
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
    width: 285px;
    background: var(--panel);
    border-left: 1px solid var(--border);
    padding: 18px;
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
    gap: 12px;
    padding: 8px 4px 20px;
}

.logo-icon {
    width: 45px;
    height: 45px;
    border-radius: 14px;
    display: grid;
    place-items: center;
    color: white;
    font-size: 23px;
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
    padding: 11px 12px;
    border-radius: 12px;
    margin: 2px 0;
}

.menu-btn:hover {
    background: var(--panel2);
}

.main {
    margin-right: 285px;
    width: calc(100% - 285px);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.topbar {
    position: sticky;
    top: 0;
    z-index: 50;
    height: 68px;
    background: color-mix(
        in srgb,
        var(--bg) 90%,
        transparent
    );
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
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
    max-width: 1050px;
    width: 100%;
    margin: auto;
    padding: 35px 22px 180px;
}

.hero {
    text-align: center;
    padding: 35px 10px 22px;
}

.hero-icon {
    width: 76px;
    height: 76px;
    border-radius: 25px;
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
    margin: 20px 0 8px;
}

.hero p {
    color: var(--muted);
    max-width: 650px;
    margin: auto;
    line-height: 1.9;
}

.quick {
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 12px;
    margin: 25px 0;
}

.quick button {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 15px 10px;
    color: var(--text);
    box-shadow: 0 4px 15px rgba(0,0,0,.03);
}

.quick button:hover {
    border-color: var(--primary);
    transform: translateY(-1px);
}

.chat {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.message {
    display: flex;
    gap: 10px;
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
    max-width: 82%;
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
    right: 285px;
    background: linear-gradient(
        to top,
        var(--bg) 75%,
        transparent
    );
    padding: 15px 22px 20px;
    z-index: 80;
}

.composer {
    max-width: 900px;
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
    margin-top: 15px;
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
    border-radius: 15px;
    padding: 15px;
}

.card button {
    margin-top: 8px;
}

.btn {
    border: 0;
    border-radius: 11px;
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

input,
select {
    width: 100%;
    border: 1px solid var(--border);
    background: var(--panel);
    color: var(--text);
    border-radius: 12px;
    padding: 11px;
    outline: none;
}

input:focus,
select:focus {
    border-color: var(--primary);
}

.hidden {
    display: none !important;
}

.overlay {
    display: none;
}

.voice-status {
    position: fixed;
    bottom: 100px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--text);
    color: var(--bg);
    border-radius: 30px;
    padding: 10px 18px;
    z-index: 200;
    box-shadow: var(--shadow);
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
        padding-left: 12px;
        padding-right: 12px;
    }

    .hero h2 {
        font-size: 24px;
    }

    .bubble {
        max-width: 88%;
    }

    .quick {
        gap: 8px;
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

    <button class="menu-btn" onclick="openVoiceMode()">
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
        🩺 Symptoms
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
        📚 Dictionary
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
            onclick="openVoiceMode()"
            title="Voice Chat">
            🎙️
        </button>

        <button
            class="icon-btn"
            onclick="toggleDark()"
            title="Dark Mode">
            🌙
        </button>
    </div>

</header>


<section class="content">

<div class="hero">

    <div class="hero-icon">⚕</div>

    <h2>MedAI ته ښه راغلاست</h2>

    <p>
        خپل روغتیايي پوښتنه ولیکئ یا د 🎙️ تڼۍ له لارې
        خبرې وکړئ. MedAI به هڅه وکړي چې ساده او
        تعلیمي طبي معلومات درکړي.
    </p>

</div>


<div class="quick">

    <button onclick="quickSend('زه ځینې نښې لرم، مرسته راسره وکړه.')">
        🩺 نښې
    </button>

    <button onclick="quickSend('زما د وینې فشار او نبض څنګه ارزول کېږي؟')">
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
            خپله طبي پوښتنه ولیکئ، یا د 🎙️ Voice تڼۍ کېکاږئ
            او خبرې راسره وکړئ.
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
            onclick="toggleVoice()"
            title="Voice Input">
            🎙️
        </button>

        <button
            class="send-btn"
            onclick="sendMessage()"
            title="Send">
            ➤
        </button>

    </div>

</div>


<div id="voiceStatus" class="voice-status hidden">
    🎙️ زه اورم...
</div>

</main>
</div>


<script>

/* ========================================================
   MedAI Frontend
   ======================================================== */

const chat = document.getElementById("chat");
const input = document.getElementById("message");
const voiceBtn = document.getElementById("voiceBtn");
const voiceStatus = document.getElementById("voiceStatus");
const extraPanel = document.getElementById("extraPanel");
const sidebar = document.getElementById("sidebar");
const overlay = document.getElementById("overlay");

let currentInteractionId = null;
let recognition = null;
let listening = false;
let voiceMode = false;
let speaking = false;

const HISTORY_KEY = "medai_history";
const FAVORITES_KEY = "medai_favorites";
const TRACKER_KEY = "medai_tracker";
const REMINDER_KEY = "medai_reminders";
const DARK_KEY = "medai_dark";


/* --------------------------------------------------------
   Storage
   -------------------------------------------------------- */

function readStorage(key, fallback = []) {
    try {
        const value = localStorage.getItem(key);

        if (!value) return fallback;

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


/* --------------------------------------------------------
   Safe DOM
   -------------------------------------------------------- */

function addMessage(text, role = "ai", options = {}) {

    const wrapper = document.createElement("div");

    wrapper.className =
        "message " +
        (role === "user" ? "user" : "");

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent =
        role === "user" ? "👤" : "⚕";

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    bubble.textContent = text;

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);

    if (options.favorite) {

        const fav = document.createElement("button");

        fav.className = "btn secondary";
        fav.textContent = "⭐ Save";

        fav.style.marginTop = "8px";

        fav.onclick = () => {
            saveFavorite(text);
            fav.textContent = "✓ Saved";
        };

        bubble.appendChild(
            document.createElement("br")
        );

        bubble.appendChild(fav);
    }

    chat.appendChild(wrapper);

    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: "smooth"
    });

    return bubble;
}


function addTyping() {

    const wrapper = document.createElement("div");

    wrapper.id = "typingMessage";
    wrapper.className = "message";

    const avatar = document.createElement("div");

    avatar.className = "avatar";
    avatar.textContent = "⚕";

    const bubble = document.createElement("div");

    bubble.className = "bubble typing";
    bubble.textContent = "MedAI لیکي...";

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);

    chat.appendChild(wrapper);

    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: "smooth"
    });
}


function removeTyping() {

    const item =
        document.getElementById("typingMessage");

    if (item) item.remove();
}


/* --------------------------------------------------------
   Chat
   -------------------------------------------------------- */

async function sendMessage(customText = null) {

    const text =
        (customText !== null
            ? customText
            : input.value).trim();

    if (!text) return;

    input.value = "";

    addMessage(text, "user");

    saveHistory({
        role: "user",
        text: text,
        time: new Date().toISOString()
    });

    addTyping();

    try {

        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: text,
                previous_interaction_id:
                    currentInteractionId
            })
        });

        const data = await response.json();

        removeTyping();

        if (!data.ok) {

            addMessage(
                "❌ " + (data.error || "یوه ستونزه رامنځته شوه."),
                "ai"
            );

            return;
        }

        currentInteractionId =
            data.interaction_id || null;

        addMessage(
            data.text,
            "ai",
            { favorite: true }
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
            "❌ له سرور سره اړیکه ونه شوه. بیا هڅه وکړئ.",
            "ai"
        );
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

    currentInteractionId = null;

    chat.innerHTML = "";

    addMessage(
        "سلام! نوی Chat پیل شو. څنګه مرسته درسره وکړم؟",
        "ai"
    );

    closeSidebar();
}


/* --------------------------------------------------------
   Voice Recognition
   -------------------------------------------------------- */

const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;

if (SpeechRecognition) {

    recognition =
        new SpeechRecognition();

    recognition.lang = "ps-AF";

    recognition.continuous = false;

    recognition.interimResults = true;

    recognition.onstart = () => {

        listening = true;

        voiceBtn.classList.add("active");

        voiceStatus.classList.remove("hidden");

        voiceStatus.textContent =
            "🎙️ زه اورم... خبرې وکړئ";
    };

    recognition.onresult = (event) => {

        let finalText = "";
        let interimText = "";

        for (
            let i = event.resultIndex;
            i < event.results.length;
            i++
        ) {

            const transcript =
                event.results[i][0].transcript;

            if (event.results[i].isFinal) {
                finalText += transcript;
            } else {
                interimText += transcript;
            }
        }

        input.value =
            finalText || interimText;
    };

    recognition.onerror = (event) => {

        listening = false;

        voiceBtn.classList.remove("active");

        voiceStatus.classList.add("hidden");

        if (event.error === "not-allowed") {
            alert(
                "Microphone permission ورکړئ، بیا هڅه وکړئ."
            );
        }
    };

    recognition.onend = () => {

        listening = false;

        voiceBtn.classList.remove("active");

        voiceStatus.classList.add("hidden");

        if (
            input.value.trim() &&
            voiceMode
        ) {
            sendMessage();
        }
    };

} else {

    recognition = null;
}


function toggleVoice() {

    if (!recognition) {

        alert(
            "ستاسو browser د Voice Recognition ملاتړ نه کوي. Chrome یا Edge وکاروئ."
        );

        return;
    }

    if (listening) {

        recognition.stop();

        return;
    }

    voiceMode = true;

    recognition.start();
}


function openVoiceMode() {

    voiceMode = true;

    closeSidebar();

    if (!recognition) {

        alert(
            "ستاسو browser د Voice Recognition ملاتړ نه کوي. Chrome یا Edge وکاروئ."
        );

        return;
    }

    if (!listening) {
        recognition.start();
    }
}


/* --------------------------------------------------------
   Text To Speech
   -------------------------------------------------------- */

function speak(text) {

    if (!("speechSynthesis" in window)) {

        return;
    }

    window.speechSynthesis.cancel();

    const utterance =
        new SpeechSynthesisUtterance(text);

    utterance.lang = "ps-AF";

    utterance.rate = 0.92;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    utterance.onstart = () => {
        speaking = true;
    };

    utterance.onend = () => {
        speaking = false;

        if (voiceMode) {
            voiceStatus.classList.add("hidden");
        }
    };

    window.speechSynthesis.speak(
        utterance
    );
}


function stopSpeaking() {

    if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
    }

    speaking = false;
}


/* --------------------------------------------------------
   Voice Mode
   -------------------------------------------------------- */

function toggleVoiceMode() {

    voiceMode = !voiceMode;

    if (!voiceMode) {
        stopSpeaking();
    }
}


/* --------------------------------------------------------
   History
   -------------------------------------------------------- */

function saveHistory(item) {

    const history =
        readStorage(HISTORY_KEY, []);

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
        readStorage(HISTORY_KEY, []);

    extraPanel.innerHTML = "";

    const panel =
        document.createElement("div");

    panel.className = "panel";

    const title =
        document.createElement("h3");

    title.textContent =
        "🕘 Chat History";

    panel.appendChild(title);

    if (!history.length) {

        const p =
            document.createElement("p");

        p.textContent =
            "تر اوسه History نشته.";

        panel.appendChild(p);

    } else {

        [...history]
            .reverse()
            .slice(0, 30)
            .forEach(item => {

                const card =
                    document.createElement("div");

                card.className = "card";

                const text =
                    document.createElement("div");

                text.textContent =
                    item.text;

                card.appendChild(text);

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

    extraPanel.scrollIntoView({
        behavior: "smooth"
    });
}


/* --------------------------------------------------------
   Favorites
   -------------------------------------------------------- */

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

    const title =
        document.createElement("h3");

    title.textContent =
        "⭐ Favorites";

    panel.appendChild(title);

    if (!favorites.length) {

        const p =
            document.createElement("p");

        p.textContent =
            "تر اوسه Favorite نشته.";

        panel.appendChild(p);

    } else {

        favorites.forEach((item, index) => {

            const card =
                document.createElement("div");

            card.className = "card";

            const text =
                document.createElement("div");

            text.textContent = item;

            const btn =
                document.createElement("button");

            btn.className =
                "btn danger";

            btn.textContent =
                "Delete";

            btn.onclick = () => {

                favorites.splice(index, 1);

                writeStorage(
                    FAVORITES_KEY,
                    favorites
                );

                showFavorites();
            };

            card.appendChild(text);

            card.appendChild(btn);

            panel.appendChild(card);
        });
    }

    extraPanel.appendChild(panel);

    extraPanel.scrollIntoView({
        behavior: "smooth"
    });
}


/* --------------------------------------------------------
   Medical Tools
   -------------------------------------------------------- */

function toolPrompt(tool) {

    closeSidebar();

    const prompts = {

        "Symptoms Checker":
            "زه غواړم د خپلو نښو په اړه تعلیمي معلومات ترلاسه کړم. کومې نښې مهمې دي، کوم احتمالي لاملونه شته، او کوم وخت باید ډاکټر ته ولاړ شم؟",

        "Vital Signs":
            "د Vital Signs لکه وینې فشار، نبض، تودوخې، تنفس او SpO2 په اړه معلومات راکړه او تشریح کړه چې د هر یوه اهمیت څه دی.",

        "Medicine Information":
            "د لاندې دوا په اړه عمومي معلومات راکړه: نوم، استعمال، عام side effects، مهم احتیاطونه او ممکنه interactions.",

        "Lab Report":
            "زه غواړم د خپل Lab Report نتیجه درسره شریکه کړم. تشریح یې کړه او ووایه چې کوم موارد باید له ډاکټر سره تعقیب شي.",

        "Disease Comparison":
            "د دوو ناروغیو ترمنځ د نښو، علتونو، تشخیص او عمومي درملنې توپیرونه تشریح کړه.",

        "Emergency Checker":
            "زه غواړم پوه شم چې کومې طبي نښې بیړنۍ پاملرنې ته اړتیا لري.",

        "Drug Interaction":
            "د دوو یا څو درملو احتمالي interactions په اړه عمومي معلومات راکړه او مهم احتیاطونه یې ووایه.",

        "First Aid":
            "د یوې عامې طبي بیړنۍ پېښې لپاره د First Aid مهم او خوندي ګامونه تشریح کړه.",

        "Medical Dictionary":
            "د طبي اصطلاحاتو یو ساده Medical Dictionary جوړ کړه.",

        "Risk Assessment":
            "د روغتیايي خطرونو د عمومي ارزونې لپاره کوم معلومات مهم دي؟",

        "Health Report":
            "د روغتیايي معلوماتو د منظم Health Report لپاره یو ساده template جوړ کړه.",

        "Medical Images":
            "د یوې طبي موضوع لپاره مناسب تعلیمي medical images یا diagram تشریح کړه او ووایه چې څه باید پکې ولیدل شي.",

        "Medical Quiz":
            "زما لپاره یو 5 پوښتنې Medical Quiz جوړ کړه. هره پوښتنه څلور انتخابونه ولري."
    };

    input.value =
        prompts[tool] ||
        tool;

    input.focus();
}


function showTracker() {

    closeSidebar();

    extraPanel.innerHTML = "";

    const panel =
        document.createElement("div");

    panel.className = "panel";

    panel.innerHTML = `
        <h3>📈 Health Tracker</h3>

        <div class="grid">

            <div>
                <label>Weight</label>
                <input id="trackWeight"
                       placeholder="kg">
            </div>

            <div>
                <label>Blood Pressure</label>
                <input id="trackBP"
                       placeholder="120/80">
            </div>

            <div>
                <label>Heart Rate</label>
                <input id="trackHR"
                       placeholder="bpm">
            </div>

            <div>
                <label>Temperature</label>
                <input id="trackTemp"
                       placeholder="°C">
            </div>

        </div>

        <br>

        <button
            class="btn"
            onclick="saveTracker()">
            Save
        </button>

        <div id="trackerList"></div>
    `;

    extraPanel.appendChild(panel);

    renderTracker();
}


function saveTracker() {

    const tracker =
        readStorage(
            TRACKER_KEY,
            []
        );

    tracker.push({
        date: new Date().toLocaleString(),
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

    if (!list) return;

    list.innerHTML = "";

    const tracker =
        readStorage(
            TRACKER_KEY,
            []
        );

    tracker
        .slice()
        .reverse()
        .slice(0, 20)
        .forEach(item => {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "card";

            card.textContent =
                `${item.date}
Weight: ${item.weight || "-"}
BP: ${item.bp || "-"}
HR: ${item.hr || "-"}
Temp: ${item.temp || "-"}`;

            list.appendChild(card);
        });
}


/* --------------------------------------------------------
   Medicine Reminder
   -------------------------------------------------------- */

function showReminders() {

    closeSidebar();

    extraPanel.innerHTML = "";

    const panel =
        document.createElement("div");

    panel.className = "panel";

    panel.innerHTML = `
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

        <div id="reminderList"></div>
    `;

    extraPanel.appendChild(panel);

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

    if (!list) return;

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

        card.className =
            "card";

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

            const newList =
                reminders.filter(
                    r =>
                        r.id !== reminder.id
                );

            writeStorage(
                REMINDER_KEY,
                newList
            );

            renderReminders();
        };

        card.appendChild(text);

        card.appendChild(button);

        list.appendChild(card);
    });
}


/* --------------------------------------------------------
   Notifications
   -------------------------------------------------------- */

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

    if (!reminders.length) return;

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

    const todayKey =
        now.toISOString()
        .slice(0,10);

    reminders.forEach(reminder => {

        const lastKey =
            `medai_reminder_${reminder.id}`;

        const last =
            localStorage.getItem(
                lastKey
            );

        const stamp =
            `${todayKey}_${current}`;

        if (
            reminder.time === current &&
            last !== stamp
        ) {

            localStorage.setItem(
                lastKey,
                stamp
            );

            if (
                "Notification" in window &&
                Notification.permission === "granted"
            ) {

                new Notification(
                    "MedAI Medicine Reminder",
                    {
                        body:
                            `دوا: ${reminder.name}`,
                        icon: ""
                    }
                );

            } else {

                alert(
                    `⏰ د دوا وخت دی: ${reminder.name}`
                );
            }

            speak(
                `د دوا وخت دی: ${reminder.name}`
            );
        }
    });
}

setInterval(
    checkReminders,
    30000
);


/* --------------------------------------------------------
   Dark Mode
   -------------------------------------------------------- */

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
    document.body.classList.add("dark");
}


/* --------------------------------------------------------
   Sidebar
   -------------------------------------------------------- */

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


/* --------------------------------------------------------
   Extra UI
   -------------------------------------------------------- */

function clearExtra() {

    extraPanel.innerHTML = "";
}


/* --------------------------------------------------------
   Start
   -------------------------------------------------------- */

input.focus();

</script>

</body>
</html>
"""


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------

@app.get("/")
def index():
    response = make_response(
        render_template_string(PAGE)
    )

    response.headers["Content-Security-Policy"] = (
        "default-src 'self' 'unsafe-inline'; "
        "connect-src 'self'; "
        "img-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline';"
    )

    return response


@app.post("/api/chat")
def api_chat():

    data = json_body()

    message = clean_text(
        data.get("message")
    )

    previous_id = clean_text(
        data.get(
            "previous_interaction_id",
            ""
        ),
        300
    )

    if not message:
        return jsonify({
            "ok": False,
            "error": "پیغام خالي دی."
        }), 400

    result = gemini_request(
        message,
        previous_id or None
    )

    if not result["ok"]:
        return jsonify(result), 502

    return jsonify({
        "ok": True,
        "text": result["text"],
        "interaction_id":
            result.get("interaction_id")
    })


# ---------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------

@app.get("/health")
def health():

    return jsonify({
        "ok": True,
        "service": "MedAI",
        "ai_configured": bool(
            GEMINI_API_KEY
        ),
        "model": GEMINI_MODEL
    })


# ---------------------------------------------------------
# Error handlers
# ---------------------------------------------------------

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
    logger.exception("Server error")
    return jsonify({
        "ok": False,
        "error": "Internal server error."
    }), 500


# ---------------------------------------------------------
# Run
# ---------------------------------------------------------

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
