from flask import Flask, request, jsonify, render_template_string
import os
import requests
import datetime

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

GEMINI_TEXT_MODEL = "gemini-3.8-flash"
GEMINI_LIVE_MODEL = "gemini-3.8-live"

TEXT_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    + GEMINI_TEXT_MODEL
    + ":generateContent"
)

AUTH_TOKEN_URL = "https://generativelanguage.googleapis.com/v1beta/auth_tokens"
WIKIMEDIA_URL = "https://commons.wikimedia.org/w/api.php"


def ask_gemini(prompt):
    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY په Vercel Environment Variables کې نشته."

    try:
        response = requests.post(
            TEXT_API_URL,
            params={"key": GEMINI_API_KEY},
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 2048
                }
            },
            timeout=45
        )

        if response.status_code != 200:
            try:
                error = response.json()
                message = error.get("error", {}).get("message", "Gemini API error")
            except Exception:
                message = response.text[:500]

            return "Gemini Error: " + message

        data = response.json()

        candidates = data.get("candidates", [])
        if not candidates:
            return "AI ځواب ورنه کړ."

        parts = candidates[0].get("content", {}).get("parts", [])

        text = ""
        for part in parts:
            if "text" in part:
                text += part["text"]

        return text.strip() or "AI ځواب خالي و."

    except Exception as e:
        return "Server Error: " + str(e)


def medical_prompt(task, text):
    return f"""
ته MedAI یې، د طبي معلوماتو لپاره AI مرستیال یې.

د کارونکي ژبه هماغه وساته چې کاروونکی یې کاروي.
که کاروونکی په پښتو خبرې کوي، په ساده او روانه پښتو ځواب ورکړه.

مهم طبي اصول:
- ځان د ډاکټر په توګه مه معرفي کوه.
- قطعي تشخیص مه کوه.
- شخصي نسخه، د درملو دقیق دوز، یا خطرناک درملنیز امر مه ورکوه.
- د بیړنیو نښو په صورت کې سمدستي بیړنۍ طبي مرستې ته د تګ سپارښتنه وکړه.
- معلومات باید تعلیمي وي.
- د کارونکي عمر، سابقه، درمل، حساسیتونه او نور مهم معلومات که موجود نه وي، فرض یې مه کوه.
- د سرطان، زړه، سټروک، ساه بندۍ، شدیدې وینې بهېدنې او نورو بیړنیو حالتونو لپاره واضح خبرداری ورکړه.
- که پوښتنه د درملو په اړه وي، عمومي معلومات ورکړه او د ډاکټر/فارمسست سره د تایید یادونه وکړه.

دنده:
{task}

د کارونکي معلومات:
{text}
"""


def get_medical_images(query):
    try:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query + " medical",
            "gsrnamespace": 6,
            "gsrlimit": 12,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 500,
            "format": "json"
        }

        response = requests.get(
            WIKIMEDIA_URL,
            params=params,
            timeout=20,
            headers={"User-Agent": "MedAI/1.0"}
        )

        if response.status_code != 200:
            return []

        pages = response.json().get("query", {}).get("pages", {})

        result = []

        for page in pages.values():
            imageinfo = page.get("imageinfo", [])
            if not imageinfo:
                continue

            info = imageinfo[0]

            result.append({
                "title": page.get("title", "Medical image"),
                "url": info.get("thumburl") or info.get("url", "")
            })

        return result

    except Exception:
        return []


HTML = r"""
<!DOCTYPE html>
<html lang="ps" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

<meta name="theme-color" content="#0b1220">

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
    font-family: Tahoma, Arial, sans-serif;
    background: #07101d;
    color: #f7f9fc;
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
        radial-gradient(circle at top right, #17345d 0, transparent 32%),
        radial-gradient(circle at bottom left, #122744 0, transparent 30%),
        #07101d;
}

.topbar {
    height: 64px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 14px;
    border-bottom: 1px solid rgba(255,255,255,.08);
    background: rgba(5,12,23,.82);
    backdrop-filter: blur(16px);
}

.brand {
    display: flex;
    align-items: center;
    gap: 10px;
}

.logo {
    width: 42px;
    height: 42px;
    border-radius: 14px;
    display: grid;
    place-items: center;
    background: linear-gradient(135deg,#19c7ff,#2879ff);
    box-shadow: 0 8px 30px rgba(0,150,255,.28);
    font-size: 22px;
}

.brand-text {
    font-weight: 800;
    font-size: 18px;
}

.brand-sub {
    font-size: 10px;
    opacity: .55;
    margin-top: 2px;
}

.icon-btn {
    width: 42px;
    height: 42px;
    border: 0;
    border-radius: 13px;
    color: white;
    background: rgba(255,255,255,.07);
    font-size: 20px;
}

.main {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    padding: 16px 14px 115px;
}

.hero {
    text-align: center;
    padding: 24px 10px 18px;
}

.hero-icon {
    width: 78px;
    height: 78px;
    margin: auto;
    border-radius: 25px;
    display: grid;
    place-items: center;
    font-size: 38px;
    background: linear-gradient(135deg,#147dff,#12c8a0);
    box-shadow: 0 18px 50px rgba(0,170,255,.25);
}

.hero h1 {
    margin: 15px 0 6px;
    font-size: 28px;
}

.hero p {
    margin: 0;
    opacity: .65;
    font-size: 13px;
}

.chat {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.msg {
    max-width: 88%;
    padding: 12px 14px;
    border-radius: 17px;
    line-height: 1.8;
    font-size: 14px;
    white-space: pre-wrap;
}

.msg.ai {
    align-self: flex-start;
    background: rgba(255,255,255,.07);
    border: 1px solid rgba(255,255,255,.07);
}

.msg.user {
    align-self: flex-end;
    background: linear-gradient(135deg,#166cff,#138fe8);
}

.quick-grid {
    display: grid;
    grid-template-columns: repeat(2,1fr);
    gap: 9px;
    margin-top: 15px;
}

.quick {
    min-height: 64px;
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 17px;
    color: white;
    background: rgba(255,255,255,.055);
    padding: 10px;
    text-align: right;
}

.quick b {
    display: block;
    margin-bottom: 4px;
}

.quick span {
    font-size: 11px;
    opacity: .55;
}

.composer {
    position: fixed;
    right: 0;
    left: 0;
    bottom: 0;
    z-index: 30;
    padding: 9px 12px calc(9px + env(safe-area-inset-bottom));
    background: rgba(4,10,19,.93);
    backdrop-filter: blur(18px);
    border-top: 1px solid rgba(255,255,255,.08);
}

.composer-row {
    max-width: 850px;
    margin: auto;
    display: flex;
    gap: 7px;
    align-items: center;
}

.input {
    flex: 1;
    min-width: 0;
    height: 48px;
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 16px;
    outline: none;
    color: white;
    background: rgba(255,255,255,.07);
    padding: 0 14px;
    font-size: 14px;
}

.send,
.mic {
    width: 48px;
    height: 48px;
    border: 0;
    border-radius: 16px;
    color: white;
    font-size: 21px;
}

.send {
    background: #1677ff;
}

.mic {
    background: #19a87b;
}

.menu {
    position: fixed;
    inset: 0;
    z-index: 100;
    display: none;
    background: rgba(0,0,0,.65);
}

.menu.show {
    display: block;
}

.menu-panel {
    position: absolute;
    top: 0;
    bottom: 0;
    right: 0;
    width: min(360px, 88vw);
    background: #0a1424;
    padding: 18px;
    overflow-y: auto;
    box-shadow: -15px 0 50px rgba(0,0,0,.35);
}

.menu-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.tool {
    width: 100%;
    border: 1px solid rgba(255,255,255,.07);
    background: rgba(255,255,255,.05);
    color: white;
    border-radius: 15px;
    padding: 13px;
    margin-bottom: 8px;
    text-align: right;
}

.tool strong {
    display: block;
}

.tool small {
    opacity: .55;
}

.tool-screen {
    display: none;
}

.tool-screen.show {
    display: block;
}

.back {
    border: 0;
    background: transparent;
    color: white;
    font-size: 25px;
    margin-bottom: 10px;
}

.card {
    background: rgba(255,255,255,.055);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 15px;
    margin-bottom: 12px;
}

.card input,
.card textarea,
.card select {
    width: 100%;
    margin-top: 8px;
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 12px;
    padding: 11px;
    background: rgba(255,255,255,.07);
    color: white;
    outline: none;
}

.action {
    width: 100%;
    border: 0;
    border-radius: 13px;
    padding: 12px;
    margin-top: 9px;
    color: white;
    background: #1677ff;
}

.result {
    white-space: pre-wrap;
    line-height: 1.8;
    margin-top: 12px;
}

.images {
    display: grid;
    grid-template-columns: repeat(2,1fr);
    gap: 8px;
}

.images img {
    width: 100%;
    aspect-ratio: 1;
    object-fit: cover;
    border-radius: 12px;
}

.voice-screen {
    position: fixed;
    inset: 0;
    z-index: 200;
    display: none;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 25px;
    background:
        radial-gradient(circle at center, #143a6a 0, #07101d 55%);
}

.voice-screen.show {
    display: flex;
}

.voice-title {
    font-size: 24px;
    font-weight: 800;
}

.voice-status {
    margin-top: 8px;
    opacity: .65;
}

.voice-orb {
    width: 180px;
    height: 180px;
    margin: 45px 0 35px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    font-size: 65px;
    background: radial-gradient(circle,#36c8ff,#1475ff 55%,#102a51);
    box-shadow:
        0 0 0 20px rgba(35,140,255,.08),
        0 0 0 45px rgba(35,140,255,.04),
        0 0 80px rgba(35,140,255,.35);
    animation: breathe 2.2s infinite ease-in-out;
}

@keyframes breathe {
    0%,100% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.07);
    }
}

.voice-text {
    width: 100%;
    max-width: 620px;
    min-height: 90px;
    max-height: 220px;
    overflow-y: auto;
    padding: 14px;
    border-radius: 18px;
    background: rgba(255,255,255,.06);
    text-align: center;
    line-height: 1.8;
}

.end-call {
    margin-top: 25px;
    width: 68px;
    height: 68px;
    border: 0;
    border-radius: 50%;
    background: #e53935;
    color: white;
    font-size: 28px;
    box-shadow: 0 10px 35px rgba(229,57,53,.35);
}

@media (min-width: 800px) {
    .main {
        max-width: 900px;
        width: 100%;
        margin: auto;
    }

    .quick-grid {
        grid-template-columns: repeat(4,1fr);
    }
}
</style>
</head>

<body>

<div class="app">

    <header class="topbar">
        <button class="icon-btn" onclick="openMenu()">☰</button>

        <div class="brand">
            <div class="logo">🩺</div>
            <div>
                <div class="brand-text">MedAI</div>
                <div class="brand-sub">ستاسو طبي AI مرستیال</div>
            </div>
        </div>

        <button class="icon-btn" onclick="startVoiceCall()">🎙️</button>
    </header>

    <main class="main">

        <section class="hero">
            <div class="hero-icon">🩺</div>
            <h1>سلام! زه MedAI یم</h1>
            <p>خپل طبي سوال ولیکئ یا له ما سره خبرې وکړئ.</p>
        </section>

        <div id="chat" class="chat">
            <div class="msg ai">
                سلام! زه MedAI یم. ستاسو د طبي معلوماتو په اړه مرسته کولی شم.
                د بیړني حالت پر مهال د روغتیايي خدماتو سره اړیکه ونیسئ.
            </div>
        </div>

        <div class="quick-grid">
            <button class="quick" onclick="quick('د شکر ناروغۍ په اړه معلومات راکړه')">
                🩸 <b>شکر</b>
                <span>Diabetes</span>
            </button>

            <button class="quick" onclick="quick('د لوړ فشار په اړه معلومات راکړه')">
                ❤️ <b>فشار</b>
                <span>Hypertension</span>
            </button>

            <button class="quick" onclick="quick('د زړه د ناروغۍ مهمې نښې کومې دي؟')">
                ❤️ <b>زړه</b>
                <span>Heart</span>
            </button>

            <button class="quick" onclick="quick('د سالنډۍ په اړه معلومات راکړه')">
                🫁 <b>سالنډي</b>
                <span>Asthma</span>
            </button>

            <button class="quick" onclick="quick('د پښتورګو د ناروغۍ نښې څه دي؟')">
                🫘 <b>پښتورګي</b>
                <span>Kidney</span>
            </button>

            <button class="quick" onclick="quick('د ځیګر د ناروغیو په اړه معلومات راکړه')">
                🧬 <b>ځیګر</b>
                <span>Liver</span>
            </button>

            <button class="quick" onclick="quick('د سرطان په اړه عمومي معلومات راکړه')">
                🎗️ <b>سرطان</b>
                <span>Cancer</span>
            </button>

            <button class="quick" onclick="quick('د لومړنۍ مرستې مهم اصول راکړه')">
                🚑 <b>لومړنۍ مرسته</b>
                <span>First Aid</span>
            </button>
        </div>

        <div id="toolScreen" class="tool-screen"></div>

    </main>

    <div class="composer">
        <div class="composer-row">
            <button class="mic" onclick="startVoiceCall()">🎙️</button>

            <input
                id="message"
                class="input"
                placeholder="خپل طبي سوال ولیکئ..."
                onkeydown="if(event.key==='Enter') sendMessage()"
            >

            <button class="send" onclick="sendMessage()">➤</button>
        </div>
    </div>

</div>


<!-- MENU -->

<div id="menu" class="menu" onclick="menuBackground(event)">

    <div class="menu-panel">

        <div class="menu-title">
            <h2>MedAI</h2>
            <button class="icon-btn" onclick="closeMenu()">×</button>
        </div>

        <button class="tool" onclick="showTool('symptoms')">
            🔍 <strong>د نښو معلومات</strong>
            <small>د علایمو تعلیمي معلومات</small>
        </button>

        <button class="tool" onclick="showTool('vitals')">
            ❤️ <strong>حیاتي نښې</strong>
            <small>BP، نبض، حرارت، اکسیجن</small>
        </button>

        <button class="tool" onclick="showTool('doctor')">
            👨‍⚕️ <strong>Doctor Assistant</strong>
            <small>د ډاکټر لپاره مرسته</small>
        </button>

        <button class="tool" onclick="showTool('lab')">
            🧪 <strong>Lab Report</strong>
            <small>د لابراتوار راپور تشریح</small>
        </button>

        <button class="tool" onclick="showTool('medicine')">
            💊 <strong>Medicine Info</strong>
            <small>د درملو عمومي معلومات</small>
        </button>

        <button class="tool" onclick="showTool('dictionary')">
            📖 <strong>Medical Dictionary</strong>
            <small>طبي لغتونه</small>
        </button>

        <button class="tool" onclick="showTool('emergency')">
            🚨 <strong>Emergency Checker</strong>
            <small>د بیړني حالت نښې</small>
        </button>

        <button class="tool" onclick="showTool('interaction')">
            ⚠️ <strong>Drug Interaction</strong>
            <small>د درملو تعاملات</small>
        </button>

        <button class="tool" onclick="showTool('report')">
            📄 <strong>Medical Report</strong>
            <small>طبي راپور</small>
        </button>

        <button class="tool" onclick="showTool('firstaid')">
            🩹 <strong>First Aid</strong>
            <small>لومړنۍ مرسته</small>
        </button>

        <button class="tool" onclick="showTool('risk')">
            📊 <strong>Risk Assessment</strong>
            <small>د خطر تعلیمي ارزونه</small>
        </button>

        <button class="tool" onclick="showTool('compare')">
            ⚖️ <strong>Disease Comparison</strong>
            <small>د ناروغیو مقایسه</small>
        </button>

        <button class="tool" onclick="showTool('images')">
            🖼️ <strong>Medical Images</strong>
            <small>طبي انځورونه</small>
        </button>

        <button class="tool" onclick="showTool('quiz')">
            🧠 <strong>Medical Quiz</strong>
            <small>طبي پوښتنې</small>
        </button>

        <button class="tool" onclick="showTool('tracker')">
            📈 <strong>Health Tracker</strong>
            <small>ستاسو روغتیايي ثبتونه</small>
        </button>

        <button class="tool" onclick="showTool('history')">
            🕘 <strong>History</strong>
            <small>پخوانۍ خبرې</small>
        </button>

        <button class="tool" onclick="showTool('favorites')">
            ⭐ <strong>Favorites</strong>
            <small>خوښې شوې معلومات</small>
        </button>

        <button class="tool" onclick="showTool('about')">
            ℹ️ <strong>About MedAI</strong>
            <small>د اپلیکیشن معلومات</small>
        </button>

    </div>
</div>


<!-- VOICE CALL -->

<div id="voiceScreen" class="voice-screen">

    <div class="voice-title">MedAI Voice</div>

    <div id="voiceStatus" class="voice-status">
        د خبرو لپاره چمتو...
    </div>

    <div class="voice-orb">🩺</div>

    <div id="voiceText" class="voice-text">
        د مایکروفون اجازه ورکړئ او خبرې پیل کړئ.
    </div>

    <button class="end-call" onclick="endVoiceCall()">☎</button>

</div>


<script>
const $ = id => document.getElementById(id);

let voiceActive = false;
let recognition = null;
let voiceSession = null;

const historyData =
    JSON.parse(localStorage.getItem("medai_history") || "[]");

function saveHistory(user, ai) {
    historyData.push({
        user,
        ai,
        time: new Date().toLocaleString()
    });

    if (historyData.length > 100) {
        historyData.shift();
    }

    localStorage.setItem(
        "medai_history",
        JSON.stringify(historyData)
    );
}


function addMessage(text, type="ai") {
    const div = document.createElement("div");

    div.className = "msg " + type;
    div.textContent = text;

    $("chat").appendChild(div);

    $("chat").scrollIntoView({
        behavior: "smooth",
        block: "end"
    });
}


async function sendMessage(text=null) {

    const input = $("message");

    const message = text || input.value.trim();

    if (!message) return;

    input.value = "";

    addMessage(message, "user");

    addMessage("⏳ لږ انتظار وکړئ...", "ai");

    const loading = $("chat").lastElementChild;

    try {

        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        const data = await response.json();

        loading.remove();

        const answer = data.answer || "ځواب ترلاسه نه شو.";

        addMessage(answer, "ai");

        saveHistory(message, answer);

    } catch (error) {

        loading.textContent =
            "د سرور سره اړیکه ونه شوه. بیا هڅه وکړئ.";

    }
}


function quick(text) {
    sendMessage(text);
}


function openMenu() {
    $("menu").classList.add("show");
}


function closeMenu() {
    $("menu").classList.remove("show");
}


function menuBackground(event) {
    if (event.target === $("menu")) {
        closeMenu();
    }
}


function showTool(name) {

    closeMenu();

    const screen = $("toolScreen");

    let html = "";

    if (name === "symptoms") {
        html = toolPage(
            "🔍 د نښو معلومات",
            "خپلې نښې ولیکئ.",
            "د مثال په ډول: تبه، ټوخی، ستړیا..."
        );
    }

    if (name === "vitals") {
        html = `
            ${backButton()}
            <div class="card">
                <h2>❤️ حیاتي نښې</h2>
                <input id="bp" placeholder="د وینې فشار لکه 120/80">
                <input id="pulse" placeholder="نبض">
                <input id="temp" placeholder="حرارت">
                <input id="oxygen" placeholder="اکسیجن SpO₂">
                <input id="weight" placeholder="وزن">
                <button class="action"
                    onclick="analyzeTool('vitals',
                    'BP='+bp.value+
                    ', Pulse='+pulse.value+
                    ', Temperature='+temp.value+
                    ', Oxygen='+oxygen.value+
                    ', Weight='+weight.value)">
                    تحلیل
                </button>
                <div id="toolResult" class="result"></div>
            </div>
        `;
    }

    if (name === "doctor") {
        html = toolPage(
            "👨‍⚕️ Doctor Assistant",
            "د ناروغ معلومات ولیکئ.",
            "عمر، نښې، موده او مهم معلومات..."
        );
    }

    if (name === "lab") {
        html = toolPage(
            "🧪 Lab Report",
            "د لابراتوار راپور یا پایلې ولیکئ.",
            "مثال: Hemoglobin 10..."
        );
    }

    if (name === "medicine") {
        html = toolPage(
            "💊 Medicine Info",
            "د درمل نوم ولیکئ.",
            "مثال: Paracetamol"
        );
    }

    if (name === "dictionary") {
        html = toolPage(
            "📖 Medical Dictionary",
            "طبي اصطلاح ولیکئ.",
            "مثال: Hypertension"
        );
    }

    if (name === "emergency") {
        html = toolPage(
            "🚨 Emergency Checker",
            "خپلې نښې ولیکئ.",
            "مثال: د سینې شدید درد او ساه لنډي"
        );
    }

    if (name === "interaction") {
        html = toolPage(
            "⚠️ Drug Interaction",
            "د درملو نومونه ولیکئ.",
            "مثال: Aspirin + Ibuprofen"
        );
    }

    if (name === "report") {
        html = toolPage(
            "📄 Medical Report",
            "د ناروغ معلومات ولیکئ.",
            "معلومات..."
        );
    }

    if (name === "firstaid") {
        html = toolPage(
            "🩹 First Aid",
            "د حالت نوم یا نښې ولیکئ.",
            "مثال: سوځېدنه"
        );
    }

    if (name === "risk") {
        html = toolPage(
            "📊 Risk Assessment",
            "خپل روغتیايي معلومات ولیکئ.",
            "عمر، نښې، فشار، شکر..."
        );
    }

    if (name === "compare") {
        html = `
            ${backButton()}
            <div class="card">
                <h2>⚖️ Disease Comparison</h2>
                <input id="d1" placeholder="لومړۍ ناروغي">
                <input id="d2" placeholder="دوهمه ناروغي">
                <button class="action"
                    onclick="analyzeTool(
                    'compare',
                    d1.value+' او '+d2.value)">
                    مقایسه
                </button>
                <div id="toolResult" class="result"></div>
            </div>
        `;
    }

    if (name === "images") {
        html = `
            ${backButton()}
            <div class="card">
                <h2>🖼️ Medical Images</h2>
                <input id="imageQuery"
                    placeholder="مثال: human heart">
                <button class="action"
                    onclick="loadImages()">
                    انځورونه پیدا کړه
                </button>
                <div id="imageResult" class="images"></div>
            </div>
        `;
    }

    if (name === "quiz") {
        html = toolPage(
            "🧠 Medical Quiz",
            "د کومې موضوع Quiz غواړئ؟",
            "مثال: Diabetes"
        );
    }

    if (name === "tracker") {
        html = `
            ${backButton()}
            <div class="card">
                <h2>📈 Health Tracker</h2>

                <input id="trackBP" placeholder="BP">
                <input id="trackPulse" placeholder="Pulse">
                <input id="trackTemp" placeholder="Temperature">
                <input id="trackWeight" placeholder="Weight">
                <input id="trackSugar" placeholder="Blood Sugar">
                <input id="trackOxygen" placeholder="Oxygen">

                <button class="action"
                    onclick="saveTracker()">
                    ثبت یې کړه
                </button>

                <div id="trackerResult" class="result"></div>
            </div>
        `;
    }

    if (name === "history") {

        const items = JSON.parse(
            localStorage.getItem("medai_history") || "[]"
        );

        html = `
            ${backButton()}
            <div class="card">
                <h2>🕘 History</h2>
                ${
                    items.length
                    ? items.slice().reverse().map(x => `
                        <div class="card">
                            <b>پوښتنه:</b>
                            <div>${escapeHtml(x.user)}</div>
                            <br>
                            <b>ځواب:</b>
                            <div>${escapeHtml(x.ai)}</div>
                            <small>${escapeHtml(x.time)}</small>
                        </div>
                    `).join("")
                    : "<p>تر اوسه تاریخ نشته.</p>"
                }
            </div>
        `;
    }

    if (name === "favorites") {
        html = `
            ${backButton()}
            <div class="card">
                <h2>⭐ Favorites</h2>
                <p>د خوښې معلومات د Chat له ځوابونو څخه خوندي کولی شئ.</p>
            </div>
        `;
    }

    if (name === "about") {
        html = `
            ${backButton()}
            <div class="card">
                <h2>🩺 MedAI</h2>
                <p>
                    MedAI د طبي معلوماتو لپاره AI مرستیال دی.
                </p>
                <p>
                    دا اپلیکیشن د طبي معلوماتو لپاره دی او
                    د مسلکي ډاکټر بدیل نه دی.
                </p>
                <hr>
                <p>
                    جوړونکی: Armin King Khan
                </p>
            </div>
        `;
    }

    screen.innerHTML = html;
    screen.classList.add("show");

    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: "smooth"
    });
}


function backButton() {
    return `
        <button class="back"
            onclick="hideTool()">
            → بېرته
        </button>
    `;
}


function hideTool() {
    $("toolScreen").classList.remove("show");
    $("toolScreen").innerHTML = "";
}


function toolPage(title, label, placeholder) {
    return `
        ${backButton()}
        <div class="card">
            <h2>${title}</h2>
            <p>${label}</p>
            <textarea
                id="toolInput"
                rows="5"
                placeholder="${placeholder}">
            </textarea>
            <button class="action"
                onclick="analyzeTool('general', toolInput.value)">
                تحلیل
            </button>
            <div id="toolResult" class="result"></div>
        </div>
    `;
}


async function analyzeTool(type, text) {

    if (!text || !text.trim()) {
        return;
    }

    $("toolResult").textContent = "⏳ تحلیل روان دی...";

    try {

        const response = await fetch("/tool", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                type,
                text
            })
        });

        const data = await response.json();

        $("toolResult").textContent =
            data.answer || "ځواب ترلاسه نه شو.";

    } catch (error) {

        $("toolResult").textContent =
            "Server error.";

    }
}


async function loadImages() {

    const query = $("imageQuery").value.trim();

    if (!query) return;

    $("imageResult").innerHTML = "⏳";

    try {

        const response = await fetch(
            "/images?q=" + encodeURIComponent(query)
        );

        const data = await response.json();

        if (!data.images || !data.images.length) {
            $("imageResult").innerHTML =
                "انځور ونه موندل شو.";
            return;
        }

        $("imageResult").innerHTML =
            data.images.map(img => `
                <a href="${escapeAttr(img.url)}"
                   target="_blank"
                   rel="noopener">
                    <img
                        src="${escapeAttr(img.url)}"
                        alt="${escapeAttr(img.title)}"
                        loading="lazy">
                </a>
            `).join("");

    } catch (error) {

        $("imageResult").innerHTML =
            "انځورونه ونه موندل شول.";

    }
}


function saveTracker() {

    const data = {
        bp: $("trackBP").value,
        pulse: $("trackPulse").value,
        temp: $("trackTemp").value,
        weight: $("trackWeight").value,
        sugar: $("trackSugar").value,
        oxygen: $("trackOxygen").value,
        time: new Date().toLocaleString()
    };

    const list = JSON.parse(
        localStorage.getItem("medai_tracker") || "[]"
    );

    list.push(data);

    if (list.length > 100) {
        list.shift();
    }

    localStorage.setItem(
        "medai_tracker",
        JSON.stringify(list)
    );

    $("trackerResult").textContent =
        "ستاسو معلومات ثبت شول.";
}


function escapeHtml(value) {
    return String(value)
        .replaceAll("&","&amp;")
        .replaceAll("<","&lt;")
        .replaceAll(">","&gt;")
        .replaceAll('"',"&quot;")
        .replaceAll("'","&#039;");
}


function escapeAttr(value) {
    return escapeHtml(value);
}


/* ============================
   GEMINI LIVE VOICE CALL
   ============================ */

async function startVoiceCall() {

    if (voiceActive) return;

    $("voiceScreen").classList.add("show");

    $("voiceStatus").textContent =
        "د مایکروفون اجازه غوښتل کېږي...";

    $("voiceText").textContent =
        "لږ انتظار وکړئ...";

    try {

        const permission =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });

        permission.getTracks().forEach(track => track.stop());

    } catch (error) {

        $("voiceStatus").textContent =
            "مایکروفون ته اجازه ورکړئ.";

        $("voiceText").textContent =
            "د موبایل Browser Settings کې Microphone اجازه فعاله کړئ.";

        return;
    }

    voiceActive = true;

    $("voiceStatus").textContent =
        "🔵 MedAI سره خبرې وکړئ";

    try {

        const tokenResponse = await fetch("/voice-token");

        const tokenData = await tokenResponse.json();

        if (!tokenResponse.ok || !tokenData.token) {
            throw new Error(
                tokenData.error || "Voice token error"
            );
        }

        await connectGeminiLive(tokenData.token);

    } catch (error) {

        console.error(error);

        $("voiceStatus").textContent =
            "Voice اتصال جوړ نه شو.";

        $("voiceText").textContent =
            error.message || "بیا هڅه وکړئ.";

        voiceActive = false;
    }
}


async function connectGeminiLive(token) {

    /*
      Google GenAI browser SDK is loaded below.
      This creates a direct Live API connection
      using the short-lived token.
    */

    if (!window.GoogleGenAI) {

        await loadScript(
            "https://esm.sh/@google/genai"
        );

    }

    const module =
        await import("https://esm.sh/@google/genai");

    const GoogleGenAI =
        module.GoogleGenAI;

    const Modality =
        module.Modality;

    const ai = new GoogleGenAI({
        apiKey: token
    });

    let currentInput = "";
    let currentOutput = "";

    voiceSession = await ai.live.connect({
        model: "gemini-3.8-live",

        config: {
            responseModalities: [Modality.AUDIO],

            systemInstruction: `
ته MedAI یې.

له کارونکي سره په طبیعي ډول خبرې کوه.
که کاروونکی پښتو خبرې کوي، په روانه پښتو ځواب ورکړه.
که English وي، English ځواب ورکړه.

ته د طبي معلوماتو AI مرستیال یې.
قطعي تشخیص مه کوه.
شخصي نسخه مه لیکه.
د خطرناک حالت په صورت کې بیړنۍ طبي مرسته توصیه کړه.
لنډ، واضح او طبیعي ځوابونه ورکړه.

کاروونکی باید داسې احساس وکړي لکه له AI سره
ژوندۍ خبرې کوي.
`
        },

        callbacks: {

            onopen: () => {

                $("voiceStatus").textContent =
                    "🟢 MedAI اوري...";

                startMicrophoneStream();

            },

            onmessage: message => {

                handleLiveMessage(message);

            },

            onerror: error => {

                console.error(
                    "Gemini Live Error:",
                    error
                );

                $("voiceStatus").textContent =
                    "د Voice اتصال کې ستونزه راغله.";

            },

            onclose: event => {

                console.log(
                    "Gemini Live closed",
                    event
                );

                if (voiceActive) {

                    $("voiceStatus").textContent =
                        "Voice اتصال بند شو.";
                }

            }
        }
    );
}


async function startMicrophoneStream() {

    try {

        const stream =
            await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

        const audioContext =
            new AudioContext();

        const source =
            audioContext.createMediaStreamSource(stream);

        const processor =
            audioContext.createScriptProcessor(
                4096,
                1,
                1
            );

        source.connect(processor);
        processor.connect(audioContext.destination);

        processor.onaudioprocess = event => {

            if (!voiceActive || !voiceSession) {
                return;
            }

            const input =
                event.inputBuffer.getChannelData(0);

            const pcm16 =
                floatTo16BitPCM(input);

            const base64 =
                arrayBufferToBase64(
                    pcm16.buffer
                );

            try {

                voiceSession.sendRealtimeInput({
                    audio: {
                        data: base64,
                        mimeType: "audio/pcm;rate=16000"
                    }
                });

            } catch (error) {

                console.error(error);

            }
        };

        window.medaiAudioContext =
            audioContext;

        window.medaiAudioStream =
            stream;

        window.medaiProcessor =
            processor;

    } catch (error) {

        $("voiceText").textContent =
            "مایکروفون فعال نه شو.";
    }
}


function floatTo16BitPCM(input) {

    const output =
        new Int16Array(input.length);

    for (
        let i = 0;
        i < input.length;
        i++
    ) {

        const value =
            Math.max(-1, Math.min(1, input[i]));

        output[i] =
            value < 0
                ? value * 0x8000
                : value * 0x7fff;
    }

    return output;
}


function arrayBufferToBase64(buffer) {

    let binary = "";

    const bytes =
        new Uint8Array(buffer);

    const chunk = 0x8000;

    for (
        let i = 0;
        i < bytes.length;
        i += chunk
    ) {

        binary += String.fromCharCode(
            ...bytes.subarray(
                i,
                Math.min(i + chunk, bytes.length)
            )
        );
    }

    return btoa(binary);
}


let audioQueue = [];
let audioPlaying = false;


function handleLiveMessage(message) {

    try {

        if (!message) return;

        const serverContent =
            message.serverContent;

        if (!serverContent) return;

        const modelTurn =
            serverContent.modelTurn;

        if (modelTurn && modelTurn.parts) {

            for (
                const part of modelTurn.parts
            ) {

                if (part.text) {

                    currentLiveText(
                        part.text
                    );

                }

                if (
                    part.inlineData &&
                    part.inlineData.data
                ) {

                    queueAudio(
                        part.inlineData.data
                    );
                }
            }
        }

        if (
            serverContent.turnComplete
        ) {

            $("voiceStatus").textContent =
                "🟢 MedAI اوري...";
        }

    } catch (error) {

        console.error(
            "Live message error:",
            error
        );
    }
}


function currentLiveText(text) {

    $("voiceText").textContent =
        text;

    $("voiceStatus").textContent =
        "🔵 MedAI خبرې کوي...";
}


function queueAudio(base64) {

    audioQueue.push(base64);

    if (!audioPlaying) {
        playNextAudio();
    }
}


async function playNextAudio() {

    if (!audioQueue.length) {

        audioPlaying = false;

        return;
    }

    audioPlaying = true;

    const base64 =
        audioQueue.shift();

    try {

        const bytes =
            base64ToUint8Array(base64);

        const audioBuffer =
            await decodePCM16(
                bytes,
                24000
            );

        const context =
            window.medaiPlaybackContext ||
            new AudioContext({
                sampleRate: 24000
            });

        window.medaiPlaybackContext =
            context;

        const buffer =
            context.createBuffer(
                1,
                audioBuffer.length,
                24000
            );

        buffer.copyToChannel(
            audioBuffer,
            0
        );

        const source =
            context.createBufferSource();

        source.buffer = buffer;

        source.connect(
            context.destination
        );

        source.onended = () => {

            playNextAudio();

        };

        source.start();

    } catch (error) {

        console.error(
            "Audio playback error:",
            error
        );

        audioPlaying = false;
        playNextAudio();
    }
}


function base64ToUint8Array(base64) {

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


async function decodePCM16(
    bytes,
    sampleRate
) {

    const input =
        new Int16Array(
            bytes.buffer,
            bytes.byteOffset,
            Math.floor(bytes.byteLength / 2)
        );

    const output =
        new Float32Array(
            input.length
        );

    for (
        let i = 0;
        i < input.length;
        i++
    ) {

        output[i] =
            input[i] / 32768;
    }

    return output;
}


function endVoiceCall() {

    voiceActive = false;

    try {

        if (voiceSession) {

            voiceSession.close();

        }

    } catch (e) {}

    voiceSession = null;

    if (window.medaiProcessor) {

        try {
            window.medaiProcessor.disconnect();
        } catch(e) {}

        window.medaiProcessor = null;
    }

    if (window.medaiAudioStream) {

        window.medaiAudioStream
            .getTracks()
            .forEach(track => track.stop());

        window.medaiAudioStream = null;
    }

    if (window.medaiAudioContext) {

        try {
            window.medaiAudioContext.close();
        } catch(e) {}

        window.medaiAudioContext = null;
    }

    if (window.medaiPlaybackContext) {

        try {
            window.medaiPlaybackContext.close();
        } catch(e) {}

        window.medaiPlaybackContext = null;
    }

    audioQueue = [];
    audioPlaying = false;

    $("voiceScreen").classList.remove(
        "show"
    );

    $("voiceStatus").textContent =
        "د خبرو لپاره چمتو...";
}


function loadScript(src) {

    return new Promise(
        (resolve, reject) => {

            const script =
                document.createElement("script");

            script.src = src;
            script.onload = resolve;
            script.onerror = reject;

            document.head.appendChild(
                script
            );
        }
    );
}


/* ESC closes voice */

document.addEventListener(
    "keydown",
    event => {

        if (event.key === "Escape") {

            if (voiceActive) {
                endVoiceCall();
            }

            closeMenu();
            hideTool();
        }
    }
);
</script>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    message = str(
        data.get("message", "")
    ).strip()

    if not message:
        return jsonify({
            "answer": "مهرباني وکړئ پوښتنه ولیکئ."
        }), 400

    prompt = medical_prompt(
        "د کارونکي پوښتنې ته واضح طبي معلومات ورکړه.",
        message
    )

    answer = ask_gemini(prompt)

    return jsonify({
        "answer": answer
    })


@app.route("/tool", methods=["POST"])
def tool():
    data = request.get_json(silent=True) or {}

    tool_type = str(
        data.get("type", "general")
    ).strip()

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "answer": "مهرباني وکړئ معلومات ولیکئ."
        }), 400

    tasks = {
        "symptoms":
            "د دې نښو ممکنه عمومي طبي معناوې، عام علتونه، د خطر نښې او د ډاکټر سره د اړیکې وخت تشریح کړه.",

        "vitals":
            "د ورکړل شوو حیاتي نښو عمومي تعلیمي تشریح وکړه. که کومه اندازه بالقوه خطرناکه ښکاري، واضح یې یادونه وکړه.",

        "doctor":
            "دا معلومات د Doctor Assistant په ډول منظم او واضح کړه، مهمې نښې او هغه پوښتنې هم ولیکه چې ډاکټر یې باید وپوښتي.",

        "lab":
            "د لابراتوار پایلې په ساده ژبه تشریح کړه. نورمال/غیرنورمال حالتونه یوازې د عمومي معلوماتو په توګه بیان کړه.",

        "medicine":
            "د دې درمل په اړه عمومي معلومات، استعمالونه، عام احتیاطونه او عام عوارض تشریح کړه. شخصي دوز مه ټاکه.",

        "dictionary":
            "دا طبي اصطلاح په ساده پښتو تشریح کړه.",

        "emergency":
            "وګوره چې کومې بیړنۍ نښې ممکن موجودې وي. که د بیړني حالت امکان وي، سمدستي طبي مرستې ته د تګ واضح سپارښتنه وکړه.",

        "interaction":
            "د ورکړل شوو درملو د احتمالي تعاملاتو په اړه عمومي معلومات ورکړه او د ډاکټر یا فارمسست سره د تایید سپارښتنه وکړه.",

        "report":
            "له ورکړل شوو معلوماتو څخه یو منظم تعلیمي طبي راپور جوړ کړه، خو قطعي تشخیص مه کوه.",

        "firstaid":
            "د ورکړل شوي حالت لپاره د لومړنۍ مرستې خوندي او عمومي ګامونه ولیکه.",

        "risk":
            "د ورکړل شوو معلوماتو له مخې د احتمالي روغتیايي خطر عوامل په تعلیمي ډول تشریح کړه. قطعي Risk Score مه جوړوه.",

        "compare":
            "د دوو ناروغیو ترمنځ نښې، عام علتونه، د تشخیص عمومي لارې او مهم توپیرونه په ساده جدول/برخو کې تشریح کړه.",

        "general":
            "د کارونکي موضوع په واضح، ساده او طبي ډول تشریح کړه."
    }

    task = tasks.get(
        tool_type,
        tasks["general"]
    )

    answer = ask_gemini(
        medical_prompt(task, text)
    )

    return jsonify({
        "answer": answer
    })


@app.route("/images")
def images():
    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:
        return jsonify({
            "images": []
        })

    return jsonify({
        "images": get_medical_images(query)
    })


@app.route("/voice-token", methods=["GET"])
def voice_token():

    if not GEMINI_API_KEY:
        return jsonify({
            "error":
                "GEMINI_API_KEY په Vercel Environment Variables کې نشته."
        }), 500

    try:

        now = datetime.datetime.now(
            datetime.timezone.utc
        )

        expire_time = (
            now + datetime.timedelta(minutes=30)
        ).isoformat().replace(
            "+00:00",
            "Z"
        )

        new_session_expire_time = (
            now + datetime.timedelta(minutes=1)
        ).isoformat().replace(
            "+00:00",
            "Z"
        )

        payload = {
            "uses": 1,
            "expireTime": expire_time,
            "newSessionExpireTime":
                new_session_expire_time,

            "liveConnectConstraints": {
                "model":
                    "models/gemini-3.8-live",

                "config": {
                    "responseModalities": [
                        "AUDIO"
                    ],

                    "sessionResumption": {}
                }
            }
        }

        response = requests.post(
            AUTH_TOKEN_URL,
            headers={
                "x-goog-api-key":
                    GEMINI_API_KEY,
                "Content-Type":
                    "application/json"
            },
            json=payload,
            timeout=20
        )

        if response.status_code != 200:

            try:
                error = response.json()

                message = error.get(
                    "error",
                    {}
                ).get(
                    "message",
                    "Token creation failed"
                )

            except Exception:

                message = response.text[:500]

            return jsonify({
                "error": message
            }), response.status_code

        data = response.json()

        token = data.get("name")

        if not token:

            return jsonify({
                "error":
                    "Gemini ephemeral token ونه موندل شو."
            }), 500

        return jsonify({
            "token": token
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "gemini_key": bool(GEMINI_API_KEY),
        "voice": True
    })


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
