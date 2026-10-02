from flask import Flask, request, jsonify, render_template_string
import os
import requests
import datetime
import base64

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

TEXT_MODEL = "gemini-3.8-flash"
LIVE_MODEL = "gemini-3.8-live"

GEMINI_TEXT_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{TEXT_MODEL}:generateContent"
)

AUTH_TOKEN_URL = (
    "https://generativelanguage.googleapis.com/v1beta/auth_tokens"
)

WIKIMEDIA_URL = "https://commons.wikimedia.org/w/api.php"


# =========================================================
# GEMINI TEXT
# =========================================================

def ask_gemini(prompt):
    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY په Vercel کې نه ده ټاکل شوې."

    try:
        r = requests.post(
            GEMINI_TEXT_URL,
            params={"key": GEMINI_API_KEY},
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.35,
                    "maxOutputTokens": 2048
                }
            },
            timeout=50
        )

        if r.status_code != 200:
            try:
                data = r.json()
                msg = data.get("error", {}).get(
                    "message",
                    "Gemini API Error"
                )
            except Exception:
                msg = r.text[:500]

            return f"Gemini Error: {msg}"

        data = r.json()

        candidates = data.get("candidates", [])

        if not candidates:
            return "AI ځواب ورنه کړ."

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )

        result = ""

        for part in parts:
            if isinstance(part, dict) and "text" in part:
                result += part["text"]

        return result.strip() or "AI ځواب خالي و."

    except requests.RequestException as e:
        return f"Network Error: {e}"

    except Exception as e:
        return f"Server Error: {e}"


def medical_prompt(task, user_text):
    return f"""
ته MedAI یې، یو طبي معلوماتي AI مرستیال.

د کارونکي ژبه هماغه وساته.
که کاروونکی پښتو وايي، په ساده او روانه پښتو ځواب ورکړه.

مهم اصول:
1. قطعي تشخیص مه کوه.
2. ځان د حقیقي ډاکټر په توګه مه معرفي کوه.
3. خطرناک یا شخصي نسخه مه لیکه.
4. د درملو شخصي دوز مه ټاکه.
5. که بیړنۍ نښې موجودې وي، سمدستي بیړنۍ طبي مرستې ته د تګ سپارښتنه وکړه.
6. معلومات تعلیمي او واضح وساته.
7. که معلومات کافي نه وي، واضح یې ووایه.
8. د ماشومانو، امیندوارۍ، شدیدو نښو او جدي ناروغیو په اړه ځانګړی احتیاط وکړه.

دنده:
{task}

د کارونکي معلومات:
{user_text}
"""


# =========================================================
# WIKIMEDIA IMAGES
# =========================================================

def get_medical_images(query):
    try:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"{query} medical",
            "gsrnamespace": 6,
            "gsrlimit": 12,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 500,
            "format": "json"
        }

        r = requests.get(
            WIKIMEDIA_URL,
            params=params,
            timeout=20,
            headers={
                "User-Agent": "MedAI/1.0"
            }
        )

        if r.status_code != 200:
            return []

        pages = r.json().get(
            "query",
            {}
        ).get(
            "pages",
            {}
        )

        images = []

        for page in pages.values():
            info = page.get("imageinfo", [])

            if not info:
                continue

            item = info[0]

            url = (
                item.get("thumburl")
                or item.get("url")
            )

            if not url:
                continue

            images.append({
                "title": page.get(
                    "title",
                    "Medical image"
                ),
                "url": url
            })

        return images

    except Exception:
        return []


# =========================================================
# HTML
# =========================================================

HTML = r"""
<!DOCTYPE html>
<html lang="ps" dir="rtl">
<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
             initial-scale=1,
             maximum-scale=1,
             user-scalable=no"
>

<meta
    name="theme-color"
    content="#07111f"
>

<title>MedAI</title>

<style>

* {
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}

html,
body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    font-family:
        Tahoma,
        Arial,
        sans-serif;
    background: #07111f;
    color: #fff;
}

body {
    overflow: hidden;
}

button,
input,
textarea {
    font-family: inherit;
}

button {
    cursor: pointer;
}

.app {
    width: 100%;
    height: 100dvh;
    display: flex;
    flex-direction: column;
    background:
        radial-gradient(
            circle at top right,
            #173e6a 0,
            transparent 35%
        ),
        radial-gradient(
            circle at bottom left,
            #11335a 0,
            transparent 32%
        ),
        #07111f;
}

.topbar {
    height: 64px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 13px;
    background: rgba(3, 9, 18, .88);
    border-bottom:
        1px solid
        rgba(255,255,255,.08);
    backdrop-filter: blur(18px);
}

.brand {
    display: flex;
    align-items: center;
    gap: 9px;
}

.logo {
    width: 42px;
    height: 42px;
    border-radius: 14px;
    display: grid;
    place-items: center;
    font-size: 22px;
    background:
        linear-gradient(
            135deg,
            #19c9ff,
            #2675ff
        );
    box-shadow:
        0 10px 30px
        rgba(25,130,255,.25);
}

.brand-name {
    font-size: 18px;
    font-weight: 900;
}

.brand-sub {
    font-size: 10px;
    opacity: .55;
}

.icon-button {
    width: 43px;
    height: 43px;
    border: 0;
    border-radius: 14px;
    background:
        rgba(255,255,255,.07);
    color: #fff;
    font-size: 20px;
}

.main {
    flex: 1;
    overflow-y: auto;
    padding: 18px 14px 105px;
}

.hero {
    text-align: center;
    padding: 22px 5px 20px;
}

.hero-icon {
    width: 78px;
    height: 78px;
    margin: auto;
    border-radius: 26px;
    display: grid;
    place-items: center;
    font-size: 38px;
    background:
        linear-gradient(
            135deg,
            #157cff,
            #10c99c
        );
    box-shadow:
        0 18px 55px
        rgba(0,160,255,.24);
}

.hero h1 {
    font-size: 27px;
    margin: 15px 0 6px;
}

.hero p {
    font-size: 13px;
    opacity: .6;
    margin: 0;
}

.chat {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.message {
    max-width: 90%;
    padding: 12px 14px;
    border-radius: 18px;
    line-height: 1.85;
    font-size: 14px;
    white-space: pre-wrap;
}

.message.ai {
    align-self: flex-start;
    background:
        rgba(255,255,255,.065);
    border:
        1px solid
        rgba(255,255,255,.07);
}

.message.user {
    align-self: flex-end;
    background:
        linear-gradient(
            135deg,
            #176dff,
            #098fdd
        );
}

.quick-grid {
    display: grid;
    grid-template-columns:
        repeat(2, minmax(0,1fr));
    gap: 9px;
    margin-top: 16px;
}

.quick {
    min-height: 67px;
    border:
        1px solid
        rgba(255,255,255,.07);
    border-radius: 17px;
    background:
        rgba(255,255,255,.055);
    color: #fff;
    text-align: right;
    padding: 10px;
}

.quick b {
    display: block;
    margin-bottom: 4px;
}

.quick span {
    opacity: .5;
    font-size: 10px;
}

.composer {
    position: fixed;
    z-index: 40;
    right: 0;
    left: 0;
    bottom: 0;
    padding:
        9px 11px
        calc(9px + env(safe-area-inset-bottom));
    background:
        rgba(3,9,18,.94);
    border-top:
        1px solid
        rgba(255,255,255,.08);
    backdrop-filter: blur(18px);
}

.composer-inner {
    max-width: 850px;
    margin: auto;
    display: flex;
    gap: 7px;
    align-items: center;
}

.message-input {
    flex: 1;
    min-width: 0;
    height: 48px;
    border:
        1px solid
        rgba(255,255,255,.1);
    border-radius: 16px;
    outline: none;
    background:
        rgba(255,255,255,.07);
    color: #fff;
    padding: 0 13px;
    font-size: 14px;
}

.send-button,
.call-button {
    width: 48px;
    height: 48px;
    border: 0;
    border-radius: 16px;
    color: #fff;
    font-size: 21px;
}

.send-button {
    background: #1677ff;
}

.call-button {
    background: #16a979;
}

.menu {
    display: none;
    position: fixed;
    z-index: 100;
    inset: 0;
    background:
        rgba(0,0,0,.65);
}

.menu.open {
    display: block;
}

.menu-panel {
    position: absolute;
    top: 0;
    bottom: 0;
    right: 0;
    width: min(370px, 89vw);
    padding: 17px;
    overflow-y: auto;
    background: #091423;
    box-shadow:
        -20px 0 60px
        rgba(0,0,0,.4);
}

.menu-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}

.tool-button {
    width: 100%;
    border:
        1px solid
        rgba(255,255,255,.07);
    background:
        rgba(255,255,255,.05);
    color: #fff;
    border-radius: 15px;
    padding: 13px;
    text-align: right;
    margin-bottom: 8px;
}

.tool-button strong {
    display: block;
}

.tool-button small {
    opacity: .5;
}

.tool-area {
    display: none;
}

.tool-area.show {
    display: block;
}

.back-button {
    border: 0;
    background: transparent;
    color: #fff;
    font-size: 25px;
    padding: 4px;
}

.card {
    background:
        rgba(255,255,255,.055);
    border:
        1px solid
        rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 15px;
    margin-bottom: 12px;
}

.card input,
.card textarea,
.card select {
    width: 100%;
    border:
        1px solid
        rgba(255,255,255,.1);
    background:
        rgba(255,255,255,.07);
    color: #fff;
    border-radius: 12px;
    padding: 11px;
    margin-top: 8px;
    outline: none;
}

.action {
    width: 100%;
    border: 0;
    border-radius: 13px;
    background: #1677ff;
    color: #fff;
    padding: 12px;
    margin-top: 9px;
}

.result {
    white-space: pre-wrap;
    line-height: 1.85;
    margin-top: 12px;
}

.images {
    display: grid;
    grid-template-columns:
        repeat(2,minmax(0,1fr));
    gap: 8px;
    margin-top: 12px;
}

.images img {
    width: 100%;
    aspect-ratio: 1;
    object-fit: cover;
    border-radius: 13px;
}


/* =========================================
   LIVE VOICE
========================================= */

.voice-screen {
    position: fixed;
    z-index: 500;
    inset: 0;
    display: none;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 24px;
    text-align: center;
    background:
        radial-gradient(
            circle at center,
            #164678 0,
            #07111f 58%
        );
}

.voice-screen.show {
    display: flex;
}

.voice-title {
    font-size: 25px;
    font-weight: 900;
}

.voice-status {
    margin-top: 8px;
    font-size: 13px;
    opacity: .65;
}

.voice-orb {
    width: 185px;
    height: 185px;
    margin:
        42px 0
        30px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    font-size: 64px;
    background:
        radial-gradient(
            circle,
            #36ceff,
            #1475ff 55%,
            #0b1e3d
        );
    box-shadow:
        0 0 0 20px
        rgba(40,150,255,.08),
        0 0 0 45px
        rgba(40,150,255,.035),
        0 0 80px
        rgba(40,150,255,.38);
    animation:
        voicePulse 2.2s
        infinite ease-in-out;
}

@keyframes voicePulse {

    0%,
    100% {
        transform: scale(1);
    }

    50% {
        transform: scale(1.07);
    }
}

.voice-transcript {
    width: 100%;
    max-width: 650px;
    min-height: 95px;
    max-height: 230px;
    overflow-y: auto;
    border-radius: 18px;
    padding: 14px;
    background:
        rgba(255,255,255,.06);
    line-height: 1.8;
}

.end-call {
    width: 68px;
    height: 68px;
    border: 0;
    border-radius: 50%;
    background: #e53935;
    color: #fff;
    font-size: 28px;
    margin-top: 24px;
    box-shadow:
        0 12px 35px
        rgba(229,57,53,.3);
}

@media (min-width: 800px) {

    .main {
        max-width: 900px;
        width: 100%;
        margin: auto;
    }

    .quick-grid {
        grid-template-columns:
            repeat(4,1fr);
    }
}

</style>
</head>


<body>

<div class="app">

<header class="topbar">

    <button
        class="icon-button"
        onclick="openMenu()">
        ☰
    </button>

    <div class="brand">

        <div class="logo">
            🩺
        </div>

        <div>
            <div class="brand-name">
                MedAI
            </div>

            <div class="brand-sub">
                ستاسو طبي AI مرستیال
            </div>
        </div>

    </div>

    <button
        class="icon-button"
        onclick="startVoice()">
        🎙️
    </button>

</header>


<main class="main">

<section class="hero">

    <div class="hero-icon">
        🩺
    </div>

    <h1>
        سلام! زه MedAI یم
    </h1>

    <p>
        ولیکئ یا له ما سره په مستقیمه توګه خبرې وکړئ.
    </p>

</section>


<div id="chat" class="chat">

    <div class="message ai">
        سلام! زه MedAI یم. خپل طبي سوال ولیکئ یا د 🎙️ تڼۍ کېکاږئ او له ما سره خبرې وکړئ.
    </div>

</div>


<div class="quick-grid">

<button
    class="quick"
    onclick="quick('د شکر ناروغۍ په اړه معلومات راکړه')">
    🩸
    <b>شکر</b>
    <span>Diabetes</span>
</button>

<button
    class="quick"
    onclick="quick('د لوړ فشار په اړه معلومات راکړه')">
    ❤️
    <b>فشار</b>
    <span>Hypertension</span>
</button>

<button
    class="quick"
    onclick="quick('د زړه د ناروغۍ مهمې نښې کومې دي؟')">
    ❤️
    <b>زړه</b>
    <span>Heart</span>
</button>

<button
    class="quick"
    onclick="quick('د سالنډۍ په اړه معلومات راکړه')">
    🫁
    <b>سالنډي</b>
    <span>Asthma</span>
</button>

<button
    class="quick"
    onclick="quick('د پښتورګو د ناروغۍ نښې څه دي؟')">
    🫘
    <b>پښتورګي</b>
    <span>Kidney</span>
</button>

<button
    class="quick"
    onclick="quick('د ځیګر ناروغۍ په اړه معلومات راکړه')">
    🧬
    <b>ځیګر</b>
    <span>Liver</span>
</button>

<button
    class="quick"
    onclick="quick('د سرطان په اړه عمومي معلومات راکړه')">
    🎗️
    <b>سرطان</b>
    <span>Cancer</span>
</button>

<button
    class="quick"
    onclick="quick('د لومړنۍ مرستې مهم اصول راکړه')">
    🚑
    <b>لومړنۍ مرسته</b>
    <span>First Aid</span>
</button>

</div>


<div
    id="toolArea"
    class="tool-area">
</div>

</main>


<div class="composer">

<div class="composer-inner">

<button
    class="call-button"
    onclick="startVoice()">
    🎙️
</button>

<input
    id="messageInput"
    class="message-input"
    placeholder="خپل طبي سوال ولیکئ..."
    autocomplete="off"
    onkeydown="
        if(event.key === 'Enter')
        sendMessage()
    "
>

<button
    class="send-button"
    onclick="sendMessage()">
    ➤
</button>

</div>

</div>

</div>


<!-- MENU -->

<div
    id="menu"
    class="menu"
    onclick="menuClick(event)">

<div class="menu-panel">

<div class="menu-head">

<h2>
    MedAI
</h2>

<button
    class="icon-button"
    onclick="closeMenu()">
    ×
</button>

</div>


<button
    class="tool-button"
    onclick="openTool('symptoms')">
    🔍
    <strong>د نښو معلومات</strong>
    <small>Symptoms</small>
</button>


<button
    class="tool-button"
    onclick="openTool('vitals')">
    ❤️
    <strong>حیاتي نښې</strong>
    <small>Vitals</small>
</button>


<button
    class="tool-button"
    onclick="openTool('doctor')">
    👨‍⚕️
    <strong>Doctor Assistant</strong>
    <small>د ډاکټر مرسته</small>
</button>


<button
    class="tool-button"
    onclick="openTool('lab')">
    🧪
    <strong>Lab Report</strong>
    <small>لابراتوار</small>
</button>


<button
    class="tool-button"
    onclick="openTool('medicine')">
    💊
    <strong>Medicine Info</strong>
    <small>درمل</small>
</button>


<button
    class="tool-button"
    onclick="openTool('dictionary')">
    📖
    <strong>Medical Dictionary</strong>
    <small>طبي قاموس</small>
</button>


<button
    class="tool-button"
    onclick="openTool('emergency')">
    🚨
    <strong>Emergency Checker</strong>
    <small>بیړنی حالت</small>
</button>


<button
    class="tool-button"
    onclick="openTool('interaction')">
    ⚠️
    <strong>Drug Interaction</strong>
    <small>د درملو تعامل</small>
</button>


<button
    class="tool-button"
    onclick="openTool('report')">
    📄
    <strong>Medical Report</strong>
    <small>طبي راپور</small>
</button>


<button
    class="tool-button"
    onclick="openTool('firstaid')">
    🩹
    <strong>First Aid</strong>
    <small>لومړنۍ مرسته</small>
</button>


<button
    class="tool-button"
    onclick="openTool('risk')">
    📊
    <strong>Risk Assessment</strong>
    <small>د خطر ارزونه</small>
</button>


<button
    class="tool-button"
    onclick="openTool('compare')">
    ⚖️
    <strong>Disease Comparison</strong>
    <small>مقایسه</small>
</button>


<button
    class="tool-button"
    onclick="openTool('images')">
    🖼️
    <strong>Medical Images</strong>
    <small>طبي انځورونه</small>
</button>


<button
    class="tool-button"
    onclick="openTool('quiz')">
    🧠
    <strong>Medical Quiz</strong>
    <small>طبي Quiz</small>
</button>


<button
    class="tool-button"
    onclick="openTool('tracker')">
    📈
    <strong>Health Tracker</strong>
    <small>روغتیايي ثبت</small>
</button>


<button
    class="tool-button"
    onclick="openTool('history')">
    🕘
    <strong>History</strong>
    <small>تاریخ</small>
</button>


<button
    class="tool-button"
    onclick="openTool('about')">
    ℹ️
    <strong>About</strong>
    <small>د MedAI معلومات</small>
</button>

</div>
</div>


<!-- LIVE VOICE -->

<div
    id="voiceScreen"
    class="voice-screen">

<div class="voice-title">
    MedAI Voice
</div>

<div
    id="voiceStatus"
    class="voice-status">
    اتصال جوړېږي...
</div>

<div class="voice-orb">
    🩺
</div>

<div
    id="voiceTranscript"
    class="voice-transcript">
    د خبرو لپاره چمتو کېږي...
</div>

<button
    class="end-call"
    onclick="endVoice()">
    ☎
</button>

</div>


<script type="module">

import {
    GoogleGenAI,
    Modality
} from "https://esm.sh/@google/genai";


/* ======================================================
   GLOBALS
====================================================== */

let liveSession = null;
let microphoneStream = null;
let audioContext = null;
let playbackContext = null;
let processor = null;

let voiceRunning = false;

let audioQueue = [];
let playingAudio = false;

let currentModelText = "";


/* ======================================================
   NORMAL CHAT
====================================================== */

window.sendMessage = async function(text = null) {

    const input =
        document.getElementById(
            "messageInput"
        );

    const message =
        text || input.value.trim();

    if (!message) {
        return;
    }

    input.value = "";

    addMessage(
        message,
        "user"
    );

    const loading =
        addMessage(
            "⏳ لږ انتظار وکړئ...",
            "ai"
        );

    try {

        const response =
            await fetch(
                "/chat",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body:
                        JSON.stringify({
                            message
                        })
                }
            );

        const data =
            await response.json();

        loading.remove();

        const answer =
            data.answer ||
            "ځواب ترلاسه نه شو.";

        addMessage(
            answer,
            "ai"
        );

        saveHistory(
            message,
            answer
        );

    } catch (error) {

        loading.textContent =
            "سرور سره اړیکه ونه شوه.";

    }
};


window.quick = function(text) {
    window.sendMessage(text);
};


function addMessage(text, type) {

    const div =
        document.createElement(
            "div"
        );

    div.className =
        "message " + type;

    div.textContent = text;

    document
        .getElementById("chat")
        .appendChild(div);

    const main =
        document.querySelector(".main");

    main.scrollTo({
        top: main.scrollHeight,
        behavior: "smooth"
    });

    return div;
}


function saveHistory(user, ai) {

    let list =
        JSON.parse(
            localStorage.getItem(
                "medai_history"
            ) || "[]"
        );

    list.push({
        user,
        ai,
        time:
            new Date()
            .toLocaleString()
    });

    if (list.length > 100) {
        list =
            list.slice(-100);
    }

    localStorage.setItem(
        "medai_history",
        JSON.stringify(list)
    );
}


/* ======================================================
   MENU
====================================================== */

window.openMenu = function() {

    document
        .getElementById("menu")
        .classList.add("open");
};


window.closeMenu = function() {

    document
        .getElementById("menu")
        .classList.remove("open");
};


window.menuClick = function(event) {

    if (
        event.target.id === "menu"
    ) {
        window.closeMenu();
    }
};


/* ======================================================
   TOOL SYSTEM
====================================================== */

window.openTool = function(type) {

    window.closeMenu();

    const area =
        document.getElementById(
            "toolArea"
        );

    area.classList.add("show");

    let html = `
        <button
            class="back-button"
            onclick="closeTool()">
            ← بېرته
        </button>
    `;


    if (type === "symptoms") {

        html += generalTool(
            "🔍 د نښو معلومات",
            "خپلې نښې ولیکئ."
        );
    }


    if (type === "doctor") {

        html += generalTool(
            "👨‍⚕️ Doctor Assistant",
            "د ناروغ معلومات ولیکئ."
        );
    }


    if (type === "lab") {

        html += generalTool(
            "🧪 Lab Report",
            "د لابراتوار پایلې ولیکئ."
        );
    }


    if (type === "medicine") {

        html += generalTool(
            "💊 Medicine Info",
            "د درمل نوم ولیکئ."
        );
    }


    if (type === "dictionary") {

        html += generalTool(
            "📖 Medical Dictionary",
            "طبي اصطلاح ولیکئ."
        );
    }


    if (type === "emergency") {

        html += generalTool(
            "🚨 Emergency Checker",
            "نښې ولیکئ."
        );
    }


    if (type === "interaction") {

        html += generalTool(
            "⚠️ Drug Interaction",
            "د درملو نومونه ولیکئ."
        );
    }


    if (type === "report") {

        html += generalTool(
            "📄 Medical Report",
            "د ناروغ معلومات ولیکئ."
        );
    }


    if (type === "firstaid") {

        html += generalTool(
            "🩹 First Aid",
            "حالت ولیکئ."
        );
    }


    if (type === "risk") {

        html += generalTool(
            "📊 Risk Assessment",
            "روغتیايي معلومات ولیکئ."
        );
    }


    if (type === "vitals") {

        html += `
        <div class="card">

            <h2>
                ❤️ حیاتي نښې
            </h2>

            <input
                id="bp"
                placeholder="BP: 120/80"
            >

            <input
                id="pulse"
                placeholder="Pulse"
            >

            <input
                id="temperature"
                placeholder="Temperature"
            >

            <input
                id="oxygen"
                placeholder="SpO2"
            >

            <input
                id="weight"
                placeholder="Weight"
            >

            <button
                class="action"
                onclick="analyzeTool(
                    'vitals',
                    getVitals()
                )">
                تحلیل
            </button>

            <div
                id="toolResult"
                class="result">
            </div>

        </div>
        `;
    }


    if (type === "compare") {

        html += `
        <div class="card">

            <h2>
                ⚖️ Disease Comparison
            </h2>

            <input
                id="disease1"
                placeholder="لومړۍ ناروغي"
            >

            <input
                id="disease2"
                placeholder="دوهمه ناروغي"
            >

            <button
                class="action"
                onclick="analyzeTool(
                    'compare',
                    disease1.value +
                    ' او ' +
                    disease2.value
                )">
                مقایسه
            </button>

            <div
                id="toolResult"
                class="result">
            </div>

        </div>
        `;
    }


    if (type === "images") {

        html += `
        <div class="card">

            <h2>
                🖼️ Medical Images
            </h2>

            <input
                id="imageQuery"
                placeholder="مثال: human heart"
            >

            <button
                class="action"
                onclick="loadImages()">
                انځورونه پیدا کړه
            </button>

            <div
                id="imageResult"
                class="images">
            </div>

        </div>
        `;
    }


    if (type === "quiz") {

        html += generalTool(
            "🧠 Medical Quiz",
            "د Quiz موضوع ولیکئ."
        );
    }


    if (type === "tracker") {

        html += `
        <div class="card">

            <h2>
                📈 Health Tracker
            </h2>

            <input
                id="trackerBP"
                placeholder="BP"
            >

            <input
                id="trackerPulse"
                placeholder="Pulse"
            >

            <input
                id="trackerTemp"
                placeholder="Temperature"
            >

            <input
                id="trackerWeight"
                placeholder="Weight"
            >

            <input
                id="trackerSugar"
                placeholder="Blood Sugar"
            >

            <input
                id="trackerOxygen"
                placeholder="Oxygen"
            >

            <button
                class="action"
                onclick="saveTracker()">
                ثبت کړه
            </button>

            <div
                id="trackerResult"
                class="result">
            </div>

        </div>
        `;
    }


    if (type === "history") {

        const list =
            JSON.parse(
                localStorage.getItem(
                    "medai_history"
                ) || "[]"
            );

        html += `
        <div class="card">

            <h2>
                🕘 History
            </h2>

            ${
                list.length
                ?
                list
                .slice()
                .reverse()
                .map(
                    item => `
                    <div class="card">
                        <b>پوښتنه:</b>
                        <div>
                            ${escapeHTML(
                                item.user
                            )}
                        </div>

                        <br>

                        <b>ځواب:</b>
                        <div>
                            ${escapeHTML(
                                item.ai
                            )}
                        </div>

                        <small>
                            ${escapeHTML(
                                item.time
                            )}
                        </small>
                    </div>
                    `
                )
                .join("")
                :
                "<p>تر اوسه تاریخ نشته.</p>"
            }

        </div>
        `;
    }


    if (type === "about") {

        html += `
        <div class="card">

            <h2>
                🩺 MedAI
            </h2>

            <p>
                MedAI د طبي معلوماتو لپاره
                AI مرستیال دی.
            </p>

            <p>
                دا د مسلکي ډاکټر بدیل نه دی.
            </p>

            <p>
                جوړونکی:
                Armin King Khan
            </p>

        </div>
        `;
    }


    area.innerHTML = html;

    area.scrollIntoView({
        behavior: "smooth"
    });
};


window.closeTool = function() {

    const area =
        document.getElementById(
            "toolArea"
        );

    area.classList.remove("show");

    area.innerHTML = "";
};


function generalTool(title, placeholder) {

    return `
    <div class="card">

        <h2>
            ${title}
        </h2>

        <textarea
            id="toolInput"
            rows="5"
            placeholder="${placeholder}">
        </textarea>

        <button
            class="action"
            onclick="analyzeTool(
                'general',
                toolInput.value
            )">
            تحلیل
        </button>

        <div
            id="toolResult"
            class="result">
        </div>

    </div>
    `;
}


window.getVitals = function() {

    return `
BP: ${document.getElementById("bp").value}
Pulse: ${document.getElementById("pulse").value}
Temperature: ${document.getElementById("temperature").value}
Oxygen: ${document.getElementById("oxygen").value}
Weight: ${document.getElementById("weight").value}
`;
};


window.analyzeTool = async function(
    type,
    text
) {

    if (!text || !text.trim()) {
        return;
    }

    const result =
        document.getElementById(
            "toolResult"
        );

    if (!result) return;

    result.textContent =
        "⏳ تحلیل روان دی...";

    try {

        const response =
            await fetch(
                "/tool",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body:
                        JSON.stringify({
                            type,
                            text
                        })
                }
            );

        const data =
            await response.json();

        result.textContent =
            data.answer ||
            "ځواب ترلاسه نه شو.";

    } catch (error) {

        result.textContent =
            "Server Error.";

    }
};


window.loadImages = async function() {

    const query =
        document.getElementById(
            "imageQuery"
        ).value.trim();

    if (!query) return;

    const result =
        document.getElementById(
            "imageResult"
        );

    result.textContent =
        "⏳";

    try {

        const response =
            await fetch(
                "/images?q=" +
                encodeURIComponent(query)
            );

        const data =
            await response.json();

        if (
            !data.images ||
            !data.images.length
        ) {

            result.textContent =
                "انځور ونه موندل شو.";

            return;
        }

        result.innerHTML =
            data.images
            .map(
                image => `
                <a
                    href="${escapeAttr(
                        image.url
                    )}"
                    target="_blank"
                    rel="noopener">

                    <img
                        src="${escapeAttr(
                            image.url
                        )}"
                        loading="lazy"
                        alt="${escapeAttr(
                            image.title
                        )}">
                </a>
                `
            )
            .join("");

    } catch (error) {

        result.textContent =
            "انځورونه ونه موندل شول.";

    }
};


window.saveTracker = function() {

    const data = {

        bp:
            document.getElementById(
                "trackerBP"
            ).value,

        pulse:
            document.getElementById(
                "trackerPulse"
            ).value,

        temp:
            document.getElementById(
                "trackerTemp"
            ).value,

        weight:
            document.getElementById(
                "trackerWeight"
            ).value,

        sugar:
            document.getElementById(
                "trackerSugar"
            ).value,

        oxygen:
            document.getElementById(
                "trackerOxygen"
            ).value,

        time:
            new Date()
            .toLocaleString()
    };


    let list =
        JSON.parse(
            localStorage.getItem(
                "medai_tracker"
            ) || "[]"
        );

    list.push(data);

    if (list.length > 100) {
        list =
            list.slice(-100);
    }

    localStorage.setItem(
        "medai_tracker",
        JSON.stringify(list)
    );


    document.getElementById(
        "trackerResult"
    ).textContent =
        "معلومات ثبت شول.";
};


function escapeHTML(value) {

    return String(value)
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}


function escapeAttr(value) {
    return escapeHTML(value);
}


/* ======================================================
   LIVE VOICE START
====================================================== */

window.startVoice = async function() {

    if (voiceRunning) {
        return;
    }

    document
        .getElementById(
            "voiceScreen"
        )
        .classList.add("show");

    setVoiceStatus(
        "🔄 اتصال جوړېږي..."
    );

    setVoiceText(
        "مایکروفون ته اجازه ورکړئ..."
    );


    try {

        await openMicrophone();

    } catch (error) {

        setVoiceStatus(
            "❌ مایکروفون فعال نه شو"
        );

        setVoiceText(
            "Browser Settings کې Microphone Permission فعاله کړئ."
        );

        return;
    }


    try {

        const response =
            await fetch(
                "/voice-token",
                {
                    method: "GET",
                    cache: "no-store"
                }
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            !data.token
        ) {

            throw new Error(
                data.error ||
                "Voice Token ترلاسه نه شو."
            );
        }


        const ai =
            new GoogleGenAI({
                apiKey:
                    data.token
            });


        liveSession =
            await ai.live.connect({

                model:
                    "gemini-3.8-live",

                config: {

                    responseModalities: [
                        Modality.AUDIO
                    ],

                    systemInstruction: `
ته MedAI یې.

له کارونکي سره طبیعي ژوندۍ خبرې کوه.

که کاروونکی پښتو خبرې کوي،
په روانه او ساده پښتو ځواب ورکړه.

که English خبرې کوي،
په English ځواب ورکړه.

ته د طبي معلوماتو AI مرستیال یې.

قطعي تشخیص مه کوه.
شخصي نسخه مه لیکه.
د درملو شخصي دوز مه ټاکه.

که کاروونکی د بیړني حالت
نښې ولري، واضح ووایه چې
سمدستي بیړنۍ طبي مرسته ترلاسه کړي.

ځوابونه لنډ، طبیعي او د
Voice Conversation لپاره مناسب وساته.

کاروونکي ته اجازه ورکړه چې
خبرې بشپړې کړي.

ته د کارونکي خبرې اورې او
په غږ ځواب ورکوې.
`
                },

                callbacks: {

                    onopen() {

                        voiceRunning =
                            true;

                        setVoiceStatus(
                            "🟢 MedAI اوري..."
                        );

                        setVoiceText(
                            "خبرې پیل کړئ..."
                        );

                        startAudioInput();
                    },


                    onmessage(message) {

                        handleLiveMessage(
                            message
                        );
                    },


                    onerror(error) {

                        console.error(
                            "LIVE ERROR",
                            error
                        );

                        setVoiceStatus(
                            "❌ Voice Error"
                        );

                        setVoiceText(
                            error?.message ||
                            "Voice اتصال کې ستونزه راغله."
                        );
                    },


                    onclose(event) {

                        console.log(
                            "LIVE CLOSED",
                            event
                        );

                        if (
                            voiceRunning
                        ) {

                            setVoiceStatus(
                                "Voice اتصال بند شو."
                            );
                        }
                    }

                }

            });

    } catch (error) {

        console.error(
            error
        );

        setVoiceStatus(
            "❌ Voice اتصال ونه شو"
        );

        setVoiceText(
            error.message ||
            "بیا هڅه وکړئ."
        );

        stopAudioInput();
    }
};


/* ======================================================
   MICROPHONE
====================================================== */

async function openMicrophone() {

    microphoneStream =
        await navigator.mediaDevices
        .getUserMedia({

            audio: {

                channelCount: 1,

                echoCancellation:
                    true,

                noiseSuppression:
                    true,

                autoGainControl:
                    true

            },

            video: false
        });
}


async function startAudioInput() {

    if (!microphoneStream) {
        return;
    }


    audioContext =
        new AudioContext();


    if (
        audioContext.state ===
        "suspended"
    ) {

        await audioContext.resume();
    }


    const source =
        audioContext
        .createMediaStreamSource(
            microphoneStream
        );


    processor =
        audioContext
        .createScriptProcessor(
            4096,
            1,
            1
        );


    source.connect(
        processor
    );


    processor.connect(
        audioContext.destination
    );


    processor.onaudioprocess =
        function(event) {

            if (
                !voiceRunning ||
                !liveSession
            ) {
                return;
            }


            const input =
                event
                .inputBuffer
                .getChannelData(0);


            const pcm =
                downsampleTo16k(
                    input,
                    audioContext.sampleRate
                );


            const base64 =
                int16ToBase64(
                    pcm
                );


            try {

                liveSession
                .sendRealtimeInput({

                    audio: {

                        data:
                            base64,

                        mimeType:
                            "audio/pcm;rate=16000"
                    }

                });

            } catch (error) {

                console.error(
                    "SEND AUDIO ERROR",
                    error
                );
            }
        };
}


/* ======================================================
   RESAMPLE
====================================================== */

function downsampleTo16k(
    buffer,
    inputRate
) {

    if (
        inputRate === 16000
    ) {

        const result =
            new Int16Array(
                buffer.length
            );

        for (
            let i = 0;
            i < buffer.length;
            i++
        ) {

            const sample =
                Math.max(
                    -1,
                    Math.min(
                        1,
                        buffer[i]
                    )
                );

            result[i] =
                sample < 0
                ? sample * 32768
                : sample * 32767;
        }

        return result;
    }


    const ratio =
        inputRate / 16000;


    const newLength =
        Math.round(
            buffer.length /
            ratio
        );


    const result =
        new Int16Array(
            newLength
        );


    let offsetResult = 0;
    let offsetBuffer = 0;


    while (
        offsetResult <
        newLength
    ) {

        const nextOffset =
            Math.round(
                (offsetResult + 1) *
                ratio
            );


        let accum = 0;
        let count = 0;


        for (
            let i =
                offsetBuffer;
            i <
                nextOffset &&
            i <
                buffer.length;
            i++
        ) {

            accum +=
                buffer[i];

            count++;
        }


        const sample =
            count
            ? accum / count
            : 0;


        const clamped =
            Math.max(
                -1,
                Math.min(
                    1,
                    sample
                )
            );


        result[offsetResult] =
            clamped < 0
            ? clamped * 32768
            : clamped * 32767;


        offsetResult++;

        offsetBuffer =
            nextOffset;
    }


    return result;
}


function int16ToBase64(
    int16
) {

    const bytes =
        new Uint8Array(
            int16.buffer
        );


    let binary = "";


    const chunk = 0x8000;


    for (
        let i = 0;
        i < bytes.length;
        i += chunk
    ) {

        binary +=
            String.fromCharCode(
                ...bytes.subarray(
                    i,
                    Math.min(
                        i + chunk,
                        bytes.length
                    )
                )
            );
    }


    return btoa(binary);
}


/* ======================================================
   LIVE RESPONSE
====================================================== */

function handleLiveMessage(
    message
) {

    if (!message) {
        return;
    }


    const serverContent =
        message.serverContent;


    if (!serverContent) {
        return;
    }


    const modelTurn =
        serverContent.modelTurn;


    if (
        modelTurn &&
        Array.isArray(
            modelTurn.parts
        )
    ) {

        for (
            const part
            of modelTurn.parts
        ) {

            if (part.text) {

                currentModelText +=
                    part.text;

                setVoiceText(
                    currentModelText
                );

                setVoiceStatus(
                    "🔵 MedAI خبرې کوي..."
                );
            }


            if (
                part.inlineData &&
                part.inlineData.data
            ) {

                queuePCM(
                    part.inlineData.data,
                    part.inlineData.mimeType
                );
            }
        }
    }


    if (
        serverContent.turnComplete
    ) {

        currentModelText = "";

        setVoiceStatus(
            "🟢 MedAI اوري..."
        );
    }
}


/* ======================================================
   AUDIO OUTPUT
====================================================== */

function queuePCM(
    base64,
    mimeType
) {

    audioQueue.push({
        base64,
        mimeType
    });


    if (!playingAudio) {

        playNextPCM();
    }
}


async function playNextPCM() {

    if (
        audioQueue.length === 0
    ) {

        playingAudio = false;

        return;
    }


    playingAudio = true;


    const item =
        audioQueue.shift();


    try {

        const sampleRate =
            getSampleRate(
                item.mimeType
            );


        const bytes =
            base64ToBytes(
                item.base64
            );


        const int16 =
            new Int16Array(
                bytes.buffer,
                bytes.byteOffset,
                Math.floor(
                    bytes.byteLength / 2
                )
            );


        const float32 =
            new Float32Array(
                int16.length
            );


        for (
            let i = 0;
            i < int16.length;
            i++
        ) {

            float32[i] =
                int16[i] / 32768;
        }


        if (!playbackContext) {

            playbackContext =
                new AudioContext();
        }


        if (
            playbackContext.state ===
            "suspended"
        ) {

            await playbackContext.resume();
        }


        const audioBuffer =
            playbackContext
            .createBuffer(
                1,
                float32.length,
                sampleRate
            );


        audioBuffer.copyToChannel(
            float32,
            0
        );


        const source =
            playbackContext
            .createBufferSource();


        source.buffer =
            audioBuffer;


        source.connect(
            playbackContext.destination
        );


        source.onended =
            function() {

                playNextPCM();
            };


        source.start();

    } catch (error) {

        console.error(
            "PLAYBACK ERROR",
            error
        );

        playingAudio = false;

        playNextPCM();
    }
}


function getSampleRate(
    mimeType
) {

    const match =
        String(
            mimeType || ""
        ).match(
            /rate=(\d+)/
        );


    if (match) {

        return Number(
            match[1]
        );
    }


    return 24000;
}


function base64ToBytes(
    base64
) {

    const binary =
        atob(base64);


    const bytes =
        new Uint8Array(
            binary.length
        );


    for (
        let i = 0;
        i < binary.length;
        i++
    ) {

        bytes[i] =
            binary.charCodeAt(i);
    }


    return bytes;
}


/* ======================================================
   END CALL
====================================================== */

window.endVoice = function() {

    voiceRunning =
        false;


    try {

        if (liveSession) {

            liveSession.close();
        }

    } catch (e) {}


    liveSession = null;


    stopAudioInput();


    if (playbackContext) {

        try {
            playbackContext.close();
        } catch (e) {}

        playbackContext =
            null;
    }


    audioQueue = [];

    playingAudio =
        false;


    currentModelText =
        "";


    document
        .getElementById(
            "voiceScreen"
        )
        .classList.remove(
            "show"
        );
};


function stopAudioInput() {

    if (processor) {

        try {
            processor.disconnect();
        } catch (e) {}

        processor =
            null;
    }


    if (audioContext) {

        try {
            audioContext.close();
        } catch (e) {}

        audioContext =
            null;
    }


    if (microphoneStream) {

        microphoneStream
            .getTracks()
            .forEach(
                track => track.stop()
            );

        microphoneStream =
            null;
    }
}


function setVoiceStatus(
    text
) {

    const element =
        document.getElementById(
            "voiceStatus"
        );

    if (element) {

        element.textContent =
            text;
    }
}


function setVoiceText(
    text
) {

    const element =
        document.getElementById(
            "voiceTranscript"
        );

    if (element) {

        element.textContent =
            text;
    }
}


/* ======================================================
   CLEANUP
====================================================== */

window.addEventListener(
    "beforeunload",
    function() {

        if (voiceRunning) {

            window.endVoice();
        }
    }
);


document.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Escape" &&
            voiceRunning
        ) {

            window.endVoice();
        }
    }
);

</script>

</body>
</html>
"""


# =========================================================
# ROUTES
# =========================================================

@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json(
        silent=True
    ) or {}

    message = str(
        data.get(
            "message",
            ""
        )
    ).strip()

    if not message:
        return jsonify({
            "answer":
                "مهرباني وکړئ پوښتنه ولیکئ."
        }), 400


    prompt = medical_prompt(
        "د کارونکي پوښتنې ته واضح او ساده طبي معلومات ورکړه.",
        message
    )


    answer =
        ask_gemini(prompt)


    return jsonify({
        "answer": answer
    })


@app.route("/tool", methods=["POST"])
def tool():

    data = request.get_json(
        silent=True
    ) or {}

    tool_type = str(
        data.get(
            "type",
            "general"
        )
    ).strip()

    text = str(
        data.get(
            "text",
            ""
        )
    ).strip()


    if not text:
        return jsonify({
            "answer":
                "مهرباني وکړئ معلومات ولیکئ."
        }), 400


    tasks = {

        "symptoms":
            "د نښو عمومي طبي معناوې، عام علتونه، خطر نښې او د ډاکټر سره د اړیکې اړتیا تشریح کړه.",

        "vitals":
            "د حیاتي نښو عمومي تعلیمي تشریح وکړه او که کومه اندازه د بیړنۍ ارزونې اړتیا ښيي، یادونه یې وکړه.",

        "doctor":
            "معلومات منظم کړه او هغه مهمې پوښتنې ولیکه چې د ډاکټر لپاره مهمې دي.",

        "lab":
            "د لابراتوار پایلې په ساده ژبه تشریح کړه او مهم احتمالي موارد یې بیان کړه.",

        "medicine":
            "د درمل عمومي استعمالونه، عام عوارض او مهم احتیاطونه تشریح کړه، خو شخصي دوز مه ټاکه.",

        "dictionary":
            "طبي اصطلاح په ساده پښتو تشریح کړه.",

        "emergency":
            "د بیړنیو نښو احتمال وارزوه او د خطر په صورت کې د بیړنۍ طبي مرستې سپارښتنه وکړه.",

        "interaction":
            "د درملو د احتمالي تعاملاتو په اړه عمومي معلومات ورکړه او د فارمسست یا ډاکټر سره د تایید سپارښتنه وکړه.",

        "report":
            "معلومات په منظم طبي راپور کې تنظیم کړه، پرته له قطعي تشخیص څخه.",

        "firstaid":
            "د ورکړل شوي حالت لپاره خوندي عمومي لومړنۍ مرستې ولیکه.",

        "risk":
            "د روغتیايي خطر عوامل په تعلیمي ډول تشریح کړه، خو قطعي Risk Score مه جوړوه.",

        "compare":
            "د دوو ناروغیو نښې، عام علتونه، تشخیص او مهم توپیرونه په ساده ډول مقایسه کړه.",

        "general":
            "د موضوع په اړه واضح، ساده او تعلیمي طبي معلومات ورکړه."
    }


    task =
        tasks.get(
            tool_type,
            tasks["general"]
        )


    answer =
        ask_gemini(
            medical_prompt(
                task,
                text
            )
        )


    return jsonify({
        "answer": answer
    })


@app.route("/images")
def images():

    query =
        request.args.get(
            "q",
            ""
        ).strip()


    if not query:
        return jsonify({
            "images": []
        })


    return jsonify({
        "images":
            get_medical_images(
                query
            )
    })


# =========================================================
# EPHEMERAL TOKEN
# =========================================================

@app.route("/voice-token")
def voice_token():

    if not GEMINI_API_KEY:

        return jsonify({
            "error":
                "GEMINI_API_KEY په Vercel Environment Variables کې نشته."
        }), 500


    try:

        now =
            datetime.datetime.now(
                datetime.timezone.utc
            )


        expire =
            now +
            datetime.timedelta(
                minutes=30
            )


        new_session_expire =
            now +
            datetime.timedelta(
                minutes=1
            )


        payload = {

            "uses": 1,

            "expireTime":
                expire.isoformat()
                .replace(
                    "+00:00",
                    "Z"
                ),

            "newSessionExpireTime":
                new_session_expire
                .isoformat()
                .replace(
                    "+00:00",
                    "Z"
                ),

            "liveConnectConstraints": {

                "model":
                    f"models/{LIVE_MODEL}",

                "config": {

                    "responseModalities": [
                        "AUDIO"
                    ],

                    "sessionResumption": {}
                }
            }
        }


        r =
            requests.post(

                AUTH_TOKEN_URL,

                headers={

                    "x-goog-api-key":
                        GEMINI_API_KEY,

                    "Content-Type":
                        "application/json"
                },

                json=payload,

                timeout=25
            )


        if r.status_code != 200:

            try:

                data =
                    r.json()

                message =
                    data.get(
                        "error",
                        {}
                    ).get(
                        "message",
                        "Token creation failed"
                    )

            except Exception:

                message =
                    r.text[:1000]


            return jsonify({
                "error": message
            }), r.status_code


        data =
            r.json()


        token =
            data.get(
                "name"
            )


        if not token:

            return jsonify({
                "error":
                    "Gemini token ونه موندل شو."
            }), 500


        return jsonify({
            "token": token
        })


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# HEALTH
# =========================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "gemini_configured":
            bool(GEMINI_API_KEY),
        "live_voice": True,
        "text_chat": True
    })


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    port =
        int(
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
