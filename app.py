import os
import time
import logging
from collections import defaultdict, deque
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# =========================================================
# MedAI - Single File Medical AI Web App
# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
).strip()

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/"
    f"v1beta/models/{GEMINI_MODEL}:generateContent"
)

WIKIMEDIA_URL = "https://commons.wikimedia.org/w/api.php"

MAX_TEXT = 12000
RATE_LIMIT = 30
RATE_WINDOW = 60

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MedAI")

rate_store = defaultdict(deque)


# =========================================================
# Security
# =========================================================

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "microphone=(self)"
    return response


def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def is_rate_limited():
    now = time.time()
    ip = get_client_ip()
    q = rate_store[ip]

    while q and now - q[0] > RATE_WINDOW:
        q.popleft()

    if len(q) >= RATE_LIMIT:
        return True

    q.append(now)
    return False


def clean_text(value, limit=MAX_TEXT):
    if not isinstance(value, str):
        return ""
    return value.strip()[:limit]


# =========================================================
# Medical Prompt
# =========================================================

def medical_prompt(task, text):
    return f"""
You are MedAI, an educational medical AI assistant.

Developer: Toyebullah Dawoodzay
Year: 2026

RULES:

- Reply in the same language as the user.
- If the user writes Pashto, reply in simple clear Pashto.
- Give educational medical information only.
- You are not a doctor.
- Do not claim to examine the patient.
- Do not diagnose from symptoms alone.
- Do not invent medical facts.
- Do not invent laboratory reference ranges.
- Do not invent medicine information.
- Do not provide personalized prescription dosing.
- Do not tell a patient to start, stop, or change prescription medicine.
- For medicine questions, provide general educational information only.
- Clearly mention uncertainty when necessary.
- For severe symptoms, children, pregnancy, elderly patients,
  chronic disease, or possible drug interactions, recommend
  professional medical evaluation.
- If there may be an emergency, advise urgent medical care first.
- Never delay emergency treatment because of an AI response.

TASK:
{task}

USER:
{text}
""".strip()


# =========================================================
# Gemini
# =========================================================

def ask_gemini(prompt):

    if not GEMINI_API_KEY:
        return (
            "⚠️ Gemini API Key تنظیم شوی نه دی.\n\n"
            "په خپل hosting کې GEMINI_API_KEY "
            "Environment Variable اضافه کړه."
        )

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1800
        }
    }

    try:
        r = requests.post(
            GEMINI_URL,
            headers=headers,
            json=payload,
            timeout=45
        )

        if r.status_code >= 400:
            logger.error(
                "Gemini error %s: %s",
                r.status_code,
                r.text[:1000]
            )

            return (
                "⚠️ د AI خدمت سره ستونزه ده.\n"
                "Gemini Model یا API Key وګوره."
            )

        data = r.json()

        candidates = data.get("candidates", [])

        if not candidates:
            return "AI ځواب ونه شو ترلاسه کېدای."

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )

        answer = "\n".join(
            p.get("text", "")
            for p in parts
            if p.get("text")
        )

        return answer.strip() or "AI خالي ځواب ورکړ."

    except requests.Timeout:
        return "⏳ د AI ځواب ډېر وخت ونیو. بیا هڅه وکړه."

    except requests.RequestException:
        logger.exception("Gemini network error")
        return "🌐 د AI خدمت سره د شبکې ستونزه ده."

    except Exception:
        logger.exception("Gemini error")
        return "یوه ناڅاپي ستونزه رامنځته شوه."


def ai_tool(task, text):
    text = clean_text(text)

    if not text:
        return jsonify({
            "answer": "مهرباني وکړه معلومات ولیکه."
        }), 400

    if is_rate_limited():
        return jsonify({
            "answer":
                "ډېرې غوښتنې وشوې. لږه شېبه وروسته بیا هڅه وکړه."
        }), 429

    return jsonify({
        "answer": ask_gemini(
            medical_prompt(task, text)
        )
    })


# =========================================================
# MAIN HTML
# =========================================================

HTML = r"""
<!DOCTYPE html>
<html lang="ps" dir="rtl">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width,initial-scale=1">

<meta name="theme-color"
      content="#0f766e">

<title>MedAI - Medical AI</title>

<style>

*{
box-sizing:border-box;
}

:root{
--bg:#f3f7f8;
--card:#ffffff;
--text:#172027;
--muted:#68777d;
--primary:#0f766e;
--primary2:#115e59;
--border:#dce6e8;
--danger:#b42318;
--shadow:0 10px 30px rgba(0,0,0,.07);
}

body.dark{
--bg:#0d1516;
--card:#172122;
--text:#edf6f5;
--muted:#a7b6b8;
--border:#2a393b;
--shadow:0 10px 30px rgba(0,0,0,.3);
}

body{
margin:0;
background:var(--bg);
color:var(--text);
font-family:
system-ui,
-apple-system,
"Segoe UI",
"Noto Sans Arabic",
sans-serif;
line-height:1.8;
}

button,input,textarea{
font:inherit;
}

button{
cursor:pointer;
}

.top{
position:sticky;
top:0;
z-index:100;
height:68px;
background:var(--card);
border-bottom:1px solid var(--border);
display:flex;
align-items:center;
justify-content:space-between;
padding:0 16px;
}

.logo{
display:flex;
align-items:center;
gap:10px;
}

.logoIcon{
width:42px;
height:42px;
border-radius:13px;
display:grid;
place-items:center;
background:var(--primary);
color:#fff;
font-size:23px;
}

.logo b{
font-size:20px;
display:block;
}

.logo small{
font-size:10px;
color:var(--muted);
display:block;
}

.actions{
display:flex;
gap:7px;
}

.icon{
width:42px;
height:42px;
border:1px solid var(--border);
border-radius:12px;
background:transparent;
color:var(--text);
}

.drawer{
position:fixed;
right:-340px;
top:0;
bottom:0;
width:320px;
z-index:200;
overflow-y:auto;
background:var(--card);
border-left:1px solid var(--border);
padding:16px;
transition:.25s;
}

.drawer.open{
right:0;
}

.overlay{
display:none;
position:fixed;
inset:0;
z-index:150;
background:rgba(0,0,0,.45);
}

.overlay.show{
display:block;
}

.drawerHeader{
display:flex;
align-items:center;
justify-content:space-between;
margin-bottom:15px;
}

.nav{
width:100%;
border:0;
background:transparent;
color:var(--text);
padding:11px;
border-radius:10px;
text-align:right;
margin:2px 0;
}

.nav:hover{
background:rgba(15,118,110,.1);
color:var(--primary);
}

.navTitle{
font-size:12px;
color:var(--muted);
margin:12px 10px 5px;
}

main{
max-width:1050px;
margin:auto;
padding:20px 14px 100px;
}

.hidden{
display:none!important;
}

.hero{
background:linear-gradient(
135deg,
#0f766e,
#164e63
);
color:white;
border-radius:24px;
padding:28px;
display:flex;
align-items:center;
justify-content:space-between;
box-shadow:var(--shadow);
}

.hero h1{
margin:7px 0;
font-size:31px;
}

.hero h1 span{
color:#b9f4eb;
}

.hero p{
margin:0;
opacity:.9;
}

.heroIcon{
font-size:70px;
}

.badge{
display:inline-block;
background:rgba(255,255,255,.14);
border-radius:50px;
padding:4px 10px;
font-size:11px;
}

.warning{
margin:15px 0;
background:#fff7e6;
border:1px solid #efd39e;
color:#654b1b;
border-radius:14px;
padding:13px;
}

.quick{
display:grid;
grid-template-columns:repeat(4,1fr);
gap:10px;
margin:15px 0;
}

.quick button{
background:var(--card);
color:var(--text);
border:1px solid var(--border);
border-radius:15px;
padding:15px 7px;
box-shadow:var(--shadow);
font-size:23px;
}

.quick span{
display:block;
font-size:12px;
margin-top:3px;
}

.card{
background:var(--card);
border:1px solid var(--border);
border-radius:20px;
box-shadow:var(--shadow);
padding:16px;
}

.chatHead{
display:flex;
align-items:center;
justify-content:space-between;
padding-bottom:10px;
border-bottom:1px solid var(--border);
}

.online{
color:var(--primary);
font-size:12px;
}

.messages{
height:430px;
overflow-y:auto;
padding:15px 3px;
}

.message{
max-width:86%;
padding:11px 14px;
border-radius:16px;
margin:9px 0;
white-space:pre-wrap;
word-break:break-word;
}

.bot{
background:var(--bg);
margin-left:auto;
}

.user{
background:var(--primary);
color:white;
margin-right:auto;
}

.quickPrompts{
display:flex;
gap:7px;
overflow-x:auto;
padding:8px 0;
}

.quickPrompts button{
white-space:nowrap;
background:var(--bg);
color:var(--text);
border:1px solid var(--border);
border-radius:50px;
padding:7px 11px;
font-size:11px;
}

.composer{
display:flex;
gap:8px;
align-items:end;
padding-top:10px;
border-top:1px solid var(--border);
}

.composer textarea{
flex:1;
resize:none;
min-height:48px;
max-height:150px;
background:var(--bg);
color:var(--text);
border:1px solid var(--border);
border-radius:14px;
padding:11px;
outline:none;
}

.send{
width:50px;
height:50px;
border:0;
border-radius:14px;
background:var(--primary);
color:#fff;
}

.mic{
width:50px;
height:50px;
border:1px solid var(--border);
border-radius:14px;
background:var(--card);
color:var(--text);
}

.voice{
display:flex;
gap:8px;
margin-top:8px;
}

.small{
background:var(--bg);
color:var(--text);
border:1px solid var(--border);
border-radius:50px;
padding:7px 11px;
font-size:11px;
}

.sectionHead{
display:flex;
align-items:center;
justify-content:space-between;
gap:10px;
margin-bottom:15px;
}

.sectionHead h2{
margin:0;
}

.back{
border:1px solid var(--border);
background:var(--card);
color:var(--text);
border-radius:10px;
padding:7px 12px;
}

textarea.toolInput{
width:100%;
min-height:180px;
resize:vertical;
background:var(--bg);
color:var(--text);
border:1px solid var(--border);
border-radius:14px;
padding:13px;
outline:none;
}

.row{
display:flex;
gap:8px;
margin-top:10px;
flex-wrap:wrap;
}

.primary{
border:0;
background:var(--primary);
color:#fff;
border-radius:11px;
padding:10px 16px;
}

.secondary{
border:1px solid var(--border);
background:var(--card);
color:var(--text);
border-radius:11px;
padding:10px 16px;
}

.result{
margin-top:15px;
background:var(--bg);
border-radius:14px;
padding:15px;
white-space:pre-wrap;
word-break:break-word;
}

.list{
display:grid;
gap:10px;
}

.item{
background:var(--card);
border:1px solid var(--border);
border-radius:15px;
padding:13px;
}

.itemTop{
display:flex;
align-items:center;
justify-content:space-between;
gap:8px;
}

.item p{
white-space:pre-wrap;
}

.danger{
border:1px solid #e8aaa5;
background:transparent;
color:var(--danger);
border-radius:8px;
padding:5px 9px;
}

.form{
display:grid;
grid-template-columns:repeat(2,1fr);
gap:12px;
margin-bottom:15px;
}

label{
display:flex;
flex-direction:column;
gap:5px;
font-size:13px;
}

input{
background:var(--bg);
color:var(--text);
border:1px solid var(--border);
border-radius:10px;
padding:10px;
outline:none;
}

.muted{
color:var(--muted);
font-size:13px;
}

.prose{
line-height:2;
}

.images{
display:grid;
grid-template-columns:repeat(2,1fr);
gap:12px;
}

.imageCard{
overflow:hidden;
border:1px solid var(--border);
border-radius:14px;
background:var(--card);
color:var(--text);
text-decoration:none;
}

.imageCard img{
width:100%;
height:190px;
object-fit:cover;
display:block;
}

.imageCard div{
padding:9px;
font-size:12px;
}

.toast{
position:fixed;
bottom:25px;
left:50%;
transform:translate(-50%,100px);
background:#172027;
color:#fff;
padding:9px 15px;
border-radius:10px;
z-index:500;
transition:.25s;
}

.toast.show{
transform:translate(-50%,0);
}

.loading{
opacity:.65;
pointer-events:none;
}

@media(max-width:700px){

main{
padding:12px 9px 80px;
}

.hero{
padding:20px;
}

.hero h1{
font-size:24px;
}

.heroIcon{
font-size:48px;
}

.quick{
grid-template-columns:repeat(2,1fr);
}

.messages{
height:360px;
}

.form,
.images{
grid-template-columns:1fr;
}

.drawer{
width:290px;
}

}

</style>
</head>

<body>

<header class="top">

<div class="logo">

<div class="logoIcon">🩺</div>

<div>
<b>MedAI</b>
<small>Medical AI Assistant</small>
</div>

</div>

<div class="actions">

<button class="icon" id="darkBtn">☾</button>

<button class="icon" id="menuBtn">☰</button>

</div>

</header>


<aside class="drawer" id="drawer">

<div class="drawerHeader">

<b>MedAI</b>

<button class="icon" id="closeMenu">×</button>

</div>

<button class="nav" data-view="home">
🏠 کور
</button>

<button class="nav" data-view="history">
🕘 History
</button>

<button class="nav" data-view="favorites">
⭐ Favorites
</button>

<button class="nav" data-view="tracker">
❤️ Health Tracker
</button>

<button class="nav" data-view="reminders">
💊 Medicine Reminder
</button>

<div class="navTitle">
Medical Tools
</div>

<button class="nav" data-tool="symptoms">🩺 Symptoms</button>
<button class="nav" data-tool="vitals">❤️ Vital Signs</button>
<button class="nav" data-tool="compare">⚖️ Disease Compare</button>
<button class="nav" data-tool="doctor">👨‍⚕️ Doctor Assistant</button>
<button class="nav" data-tool="lab">🧪 Lab Report</button>
<button class="nav" data-tool="medicine">💊 Medicine Info</button>
<button class="nav" data-tool="dictionary">📖 Medical Dictionary</button>
<button class="nav" data-tool="emergency">🚨 Emergency Checker</button>
<button class="nav" data-tool="interaction">🔄 Drug Interaction</button>
<button class="nav" data-tool="report">📋 Medical Report</button>
<button class="nav" data-tool="firstaid">🩹 First Aid</button>
<button class="nav" data-tool="glossary">📚 Medical Glossary</button>
<button class="nav" data-tool="risk">📊 Risk Assessment</button>
<button class="nav" data-tool="health-report">📈 Health Report</button>
<button class="nav" data-tool="quiz">🧠 Medical Quiz</button>
<button class="nav" data-tool="images">🖼️ Medical Images</button>

<div class="navTitle">
Other
</div>

<button class="nav" data-view="privacy">
🔒 Privacy & Safety
</button>

</aside>

<div class="overlay" id="overlay"></div>


<main>


<!-- HOME -->

<section id="home">

<div class="hero">

<div>

<span class="badge">
AI • Medical Education
</span>

<h1>
سلام! زه
<span>MedAI</span>
یم 👋
</h1>

<p>
د روغتیا او طب په اړه تعلیمي معلومات ترلاسه کړه.
</p>

</div>

<div class="heroIcon">
🩺
</div>

</div>


<div class="warning">

<b>⚠️ مهم:</b>

MedAI د ډاکټر بدیل نه دی.
که د سینې سخت درد، د ساه ستونزه،
بې‌هوښي، شدید خونریزي یا بل بیړنی حالت وي،
عاجله طبي مرسته وغواړه.

</div>


<div class="quick">

<button data-tool="symptoms">
🩺
<span>Symptoms</span>
</button>

<button data-tool="vitals">
❤️
<span>Vital Signs</span>
</button>

<button data-tool="medicine">
💊
<span>Medicine</span>
</button>

<button data-tool="lab">
🧪
<span>Lab Report</span>
</button>

<button data-tool="firstaid">
🩹
<span>First Aid</span>
</button>

<button data-tool="emergency">
🚨
<span>Emergency</span>
</button>

<button data-tool="interaction">
🔄
<span>Interaction</span>
</button>

<button data-tool="quiz">
🧠
<span>Quiz</span>
</button>

</div>


<div class="card">

<div class="chatHead">

<b>MedAI Chat</b>

<span class="online">
● Online
</span>

</div>


<div class="messages" id="messages">

<div class="message bot">
سلام! خپله طبي پوښتنه ولیکه.
زه به په ساده پښتو کې تعلیمي معلومات درکړم.
</div>

</div>


<div class="quickPrompts">

<button>
د وینې فشار څه معنا لري؟
</button>

<button>
د تبې عام لاملونه څه دي؟
</button>

<button>
د شکر ناروغۍ عامې نښې څه دي؟
</button>

</div>


<div class="composer">

<button class="mic" id="micBtn">
🎙️
</button>

<textarea
id="message"
placeholder="خپله پوښتنه ولیکه..."
rows="1"
></textarea>

<button class="send" id="sendBtn">
➤
</button>

</div>


<div class="voice">

<button class="small" id="speakBtn">
🔊 وروستی ځواب
</button>

<button class="small" id="stopBtn">
⏹️ Stop
</button>

</div>

</div>

</section>


<!-- TOOL -->

<section id="toolPage" class="hidden">

<div class="sectionHead">

<div>
<h2 id="toolTitle"></h2>
<div class="muted" id="toolDescription"></div>
</div>

<button class="back" id="backHome">
← کور
</button>

</div>


<div class="card">

<textarea
class="toolInput"
id="toolInput"
placeholder="معلومات دلته ولیکه..."
></textarea>


<div class="row">

<button class="primary" id="runTool">
AI ځواب
</button>

<button class="secondary" id="clearTool">
پاکول
</button>

</div>


<div
id="toolResult"
class="result hidden"
></div>

</div>

</section>


<!-- HISTORY -->

<section id="history" class="hidden">

<div class="sectionHead">

<h2>🕘 History</h2>

<button class="secondary" id="clearHistory">
ټول پاکول
</button>

</div>

<div class="list" id="historyList"></div>

</section>


<!-- FAVORITES -->

<section id="favorites" class="hidden">

<div class="sectionHead">

<h2>⭐ Favorites</h2>

<button class="secondary" id="clearFavorites">
ټول پاکول
</button>

</div>

<div class="list" id="favoriteList"></div>

</section>


<!-- TRACKER -->

<section id="tracker" class="hidden">

<div class="sectionHead">

<h2>❤️ Health Tracker</h2>

</div>


<div class="card">

<div class="form">

<label>
Blood Pressure
<input id="bp" placeholder="120/80">
</label>

<label>
Pulse
<input id="pulse" type="number" placeholder="72">
</label>

<label>
Temperature
<input id="temperature" type="number" step="0.1" placeholder="37.0">
</label>

<label>
Weight
<input id="weight" type="number" step="0.1" placeholder="70">
</label>

<label>
Blood Sugar
<input id="sugar" placeholder="100">
</label>

<label>
Oxygen %
<input id="oxygen" type="number" placeholder="98">
</label>

</div>

<button class="primary" id="saveTracker">
Save
</button>

</div>


<br>

<div class="list" id="trackerList"></div>

</section>


<!-- REMINDERS -->

<section id="reminders" class="hidden">

<div class="sectionHead">

<h2>💊 Medicine Reminder</h2>

</div>


<div class="card">

<div class="form">

<label>
Medicine
<input id="medicineName"
placeholder="د درمل نوم">
</label>

<label>
Time
<input id="medicineTime"
type="time">
</label>

<label>
Note
<input id="medicineNote"
placeholder="یادونه">
</label>

</div>


<button
class="primary"
id="addReminder"
>
Reminder اضافه کړه
</button>


<p class="muted">
Reminder په دې browser کې ساتل کېږي.
Notification اجازه ورکړه چې خبرتیاوې فعاله شي.
</p>

</div>


<br>

<div class="list" id="reminderList"></div>

</section>


<!-- PRIVACY -->

<section id="privacy" class="hidden">

<div class="card prose">

<h2>🔒 Privacy & Safety</h2>

<h3>Data</h3>

<p>
History، Favorites، Health Tracker او Medicine Reminders
په browser کې localStorage کې ساتل کېږي.
په دې نسخه کې User Account او Cloud Database نشته.
</p>

<h3>AI Safety</h3>

<p>
MedAI د تعلیمي طبي معلوماتو لپاره دی.
دا د ډاکټر، نرس، pharmacist یا emergency service بدیل نه دی.
</p>

<h3>Emergency</h3>

<p>
که حالت بیړنی وي، د AI ځواب ته انتظار مه کوه.
له عاجلو طبي خدماتو سره اړیکه ونیسه یا روغتون ته لاړ شه.
</p>

</div>

</section>


<div class="toast" id="toast"></div>

</main>


<script>

const TOOL_INFO = {

symptoms:[
"🩺 Symptoms",
"خپلې نښې ولیکه؛ احتمالي لاملونه او د خطر نښې به تشریح شي."
],

vitals:[
"❤️ Vital Signs",
"د وینې فشار، نبض، تودوخه، اکسیجن یا نور vital signs ولیکه."
],

compare:[
"⚖️ Disease Compare",
"د دوو یا څو ناروغیو نومونه ولیکه."
],

doctor:[
"👨‍⚕️ Doctor Assistant",
"د ډاکټر لپاره خپل حالت یا پوښتنې تنظیم کړه."
],

lab:[
"🧪 Lab Report",
"د لابراتوار result ولیکه."
],

medicine:[
"💊 Medicine Info",
"د درمل نوم ولیکه."
],

dictionary:[
"📖 Medical Dictionary",
"د طبي اصطلاح نوم ولیکه."
],

emergency:[
"🚨 Emergency Checker",
"خپل اوسنی حالت ولیکه."
],

interaction:[
"🔄 Drug Interaction",
"د درملو نومونه ولیکه."
],

report:[
"📋 Medical Report",
"خپل طبي یادښتونه ولیکه."
],

firstaid:[
"🩹 First Aid",
"د ټپ یا حالت معلومات ولیکه."
],

glossary:[
"📚 Medical Glossary",
"طبي اصطلاح ولیکه."
],

risk:[
"📊 Risk Assessment",
"خپل اړوند روغتیايي معلومات ولیکه."
],

"health-report":[
"📈 Health Report",
"خپل health measurements ولیکه."
],

quiz:[
"🧠 Medical Quiz",
"د quiz موضوع ولیکه."
],

images:[
"🖼️ Medical Images",
"د طبي انځور موضوع ولیکه."
]

};


const TASKS = {

symptoms:
"Explain possible causes and warning signs of the described symptoms. Do not diagnose.",

vitals:
"Explain the supplied vital signs educationally. Consider context and do not diagnose.",

compare:
"Compare the mentioned diseases by symptoms, causes, diagnosis and important differences. Do not diagnose.",

doctor:
"Help the user prepare for a healthcare professional visit. Organize information and suggest useful questions.",

lab:
"Explain laboratory results educationally. Explain what tests generally measure and possible meanings. Do not diagnose or invent reference ranges.",

medicine:
"Give general educational information about the medicine, common uses, common side effects, warnings and interaction concerns. Do not prescribe or give personalized dosing.",

dictionary:
"Define the medical term in simple Pashto.",

emergency:
"Look for emergency warning signs. If there may be an emergency, advise urgent medical care immediately.",

interaction:
"Explain possible drug-drug, drug-food and drug-condition interactions. If information is insufficient, say so.",

report:
"Organize the supplied medical notes into a clear educational medical summary without inventing missing information.",

firstaid:
"Give general first-aid information and prioritize emergency escalation for life-threatening conditions.",

glossary:
"Explain the requested medical glossary term or terms in simple Pashto.",

risk:
"Explain relevant health risk factors and warning signs. Do not calculate a validated risk score without required validated inputs.",

"health-report":
"Create an educational health summary from supplied measurements. Separate facts from possible interpretations.",

quiz:
"Create a short educational medical quiz with multiple choices, correct answers and explanations."

};


// =========================================================
// Storage
// =========================================================

let history =
JSON.parse(
localStorage.getItem("medai_history") || "[]"
);

let favorites =
JSON.parse(
localStorage.getItem("medai_favorites") || "[]"
);

let tracker =
JSON.parse(
localStorage.getItem("medai_tracker") || "[]"
);

let reminders =
JSON.parse(
localStorage.getItem("medai_reminders") || "[]"
);

let lastAnswer = "";


// =========================================================
// Helpers
// =========================================================

function $(id){
return document.getElementById(id);
}

function escapeHTML(value){

return String(value ?? "")
.replace(/[&<>"']/g,function(c){

return {
"&":"&amp;",
"<":"&lt;",
">":"&gt;",
'"':"&quot;",
"'":"&#039;"

}[c];

});

}

function save(key,value){

localStorage.setItem(
key,
JSON.stringify(value)
);

}

function toast(text){

$("toast").textContent = text;

$("toast").classList.add("show");

setTimeout(
() => $("toast").classList.remove("show"),
2200
);

}


// =========================================================
// Navigation
// =========================================================

const pages = [
"home",
"toolPage",
"history",
"favorites",
"tracker",
"reminders",
"privacy"
];


function showPage(page){

pages.forEach(p =>
$(p).classList.add("hidden")
);

$(page).classList.remove("hidden");

window.scrollTo({
top:0,
behavior:"smooth"
});

}


function closeDrawer(){

$("drawer").classList.remove("open");

$("overlay").classList.remove("show");

}


$("menuBtn").onclick = () => {

$("drawer").classList.add("open");

$("overlay").classList.add("show");

};


$("closeMenu").onclick =
closeDrawer;

$("overlay").onclick =
closeDrawer;


document.querySelectorAll("[data-view]")
.forEach(btn => {

btn.onclick = () => {

closeDrawer();

const view = btn.dataset.view;

showPage(view);

if(view === "history")
renderHistory();

if(view === "favorites")
renderFavorites();

if(view === "tracker")
renderTracker();

if(view === "reminders")
renderReminders();

};

});


document.querySelectorAll("[data-tool]")
.forEach(btn => {

btn.onclick = () => {

openTool(btn.dataset.tool);

};

});


function openTool(tool){

closeDrawer();

const info = TOOL_INFO[tool];

if(!info)
return;

$("toolTitle").textContent =
info[0];

$("toolDescription").textContent =
info[1];

$("toolInput").value = "";

$("toolResult").classList.add("hidden");

$("runTool").dataset.tool =
tool;

showPage("toolPage");

}


// =========================================================
// Chat
// =========================================================

function addMessage(text,type){

const div =
document.createElement("div");

div.className =
"message " + type;

div.textContent =
text;

$("messages").appendChild(div);

$("messages").scrollTop =
$("messages").scrollHeight;

}


async function sendMessage(){

const input =
$("message");

const text =
input.value.trim();

if(!text)
return;

addMessage(
text,
"user"
);

input.value = "";

$("sendBtn").disabled = true;


try{

const response =
await fetch(
"/chat",
{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
message:text
})
}
);

const data =
await response.json();

if(!response.ok)
throw new Error(
data.answer ||
data.error ||
"Request failed"
);

const answer =
data.answer || "";

lastAnswer =
answer;

addMessage(
answer,
"bot"
);


history.unshift({

id:
Date.now().toString(),

question:
text,

answer:
answer,

date:
new Date().toLocaleString("ps-AF")

});


history =
history.slice(0,100);

save(
"medai_history",
history
);


}catch(error){

addMessage(
error.message ||
"یوه ستونزه راغله.",
"bot"
);

}finally{

$("sendBtn").disabled = false;

}

}


$("sendBtn").onclick =
sendMessage;


$("message").addEventListener(
"keydown",
function(e){

if(
e.key === "Enter" &&
!e.shiftKey
){

e.preventDefault();

sendMessage();

}

}
);


// =========================================================
// Quick Prompts
// =========================================================

document.querySelectorAll(
".quickPrompts button"
).forEach(btn => {

btn.onclick = () => {

$("message").value =
btn.textContent.trim();

sendMessage();

};

});


// =========================================================
// Tool Runner
// =========================================================

$("runTool").onclick =
async function(){

const tool =
this.dataset.tool;

const text =
$("toolInput").value.trim();

if(!text){

toast("معلومات ولیکه.");

return;

}


const result =
$("toolResult");

result.classList.remove("hidden");

result.textContent =
"⏳ AI ځواب جوړوي...";


if(tool === "images"){

await loadImages(text);

return;

}


try{

const response =
await fetch(
"/" + tool,
{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
text:text
})
}
);

const data =
await response.json();

if(!response.ok)
throw new Error(
data.answer ||
data.error ||
"Request failed"
);

result.textContent =
data.answer || "";

lastAnswer =
data.answer || "";

}catch(error){

result.textContent =
error.message ||
"ستونزه راغله.";

}

};


$("clearTool").onclick =
() => {

$("toolInput").value = "";

$("toolResult").classList.add(
"hidden"
);

};


$("backHome").onclick =
() => showPage("home");


// =========================================================
// Images
// =========================================================

async function loadImages(query){

const result =
$("toolResult");

result.textContent =
"🖼️ انځورونه لټول کېږي...";

try{

const response =
await fetch(
"/images?q=" +
encodeURIComponent(query)
);

const data =
await response.json();

if(
!data.items ||
!data.items.length
){

result.textContent =
"انځورونه ونه موندل شول.";

return;

}


result.innerHTML =

'<div class="images">' +

data.items.map(item => {

const image =
escapeHTML(item.url);

const source =
escapeHTML(item.source);

const title =
escapeHTML(item.title);

return `

<a
class="imageCard"
href="${source}"
target="_blank"
rel="noopener noreferrer"
>

<img
src="${image}"
alt="${title}"
loading="lazy"
>

<div>
${title}
<br>
<small>
Wikimedia Commons
</small>
</div>

</a>

`;

}).join("") +

"</div>";


}catch{

result.textContent =
"د انځورونو په لټون کې ستونزه راغله.";

}

}


// =========================================================
// Dark Mode
// =========================================================

$("darkBtn").onclick =
() => {

document.body.classList.toggle(
"dark"
);

localStorage.setItem(
"medai_dark",
document.body.classList.contains("dark")
? "1"
: "0"
);

};


if(
localStorage.getItem("medai_dark")
===
"1"
){

document.body.classList.add("dark");

}


// =========================================================
// History
// =========================================================

function renderHistory(){

const box =
$("historyList");

if(!history.length){

box.innerHTML =
`
<div class="item">
History خالي دی.
</div>
`;

return;

}


box.innerHTML =
history.map(
(item,index) => `

<div class="item">

<div class="itemTop">

<b>
${escapeHTML(item.question)}
</b>

<div>

<button
class="secondary"
onclick="favoriteItem(${index})"
>
⭐
</button>

<button
class="danger"
onclick="deleteHistory(${index})"
>
حذف
</button>

</div>

</div>

<small class="muted">
${escapeHTML(item.date)}
</small>

<p>
${escapeHTML(item.answer)}
</p>

</div>

`
).join("");

}


window.deleteHistory =
function(index){

history.splice(
index,
1
);

save(
"medai_history",
history
);

renderHistory();

};


window.favoriteItem =
function(index){

const item =
history[index];

const exists =
favorites.some(
f =>
f.question === item.question &&
f.answer === item.answer
);

if(exists){

toast(
"له مخکې Favorites کې شته."
);

return;

}

favorites.unshift(item);

save(
"medai_favorites",
favorites
);

toast(
"⭐ Favorites ته اضافه شو."
);

};


$("clearHistory").onclick =
() => {

history = [];

save(
"medai_history",
history
);

renderHistory();

};


// =========================================================
// Favorites
// =========================================================

function renderFavorites(){

const box =
$("favoriteList");

if(!favorites.length){

box.innerHTML =
`
<div class="item">
Favorites خالي دی.
</div>
`;

return;

}


box.innerHTML =
favorites.map(
(item,index) => `

<div class="item">

<div class="itemTop">

<b>
${escapeHTML(item.question)}
</b>

<button
class="danger"
onclick="deleteFavorite(${index})"
>
حذف
</button>

</div>

<small class="muted">
${escapeHTML(item.date)}
</small>

<p>
${escapeHTML(item.answer)}
</p>

</div>

`
).join("");

}


window.deleteFavorite =
function(index){

favorites.splice(
index,
1
);

save(
"medai_favorites",
favorites
);

renderFavorites();

};


$("clearFavorites").onclick =
() => {

favorites = [];

save(
"medai_favorites",
favorites
);

renderFavorites();

};


// =========================================================
// Health Tracker
// =========================================================

$("saveTracker").onclick =
() => {

const item = {

id:
Date.now().toString(),

date:
new Date().toLocaleString("ps-AF"),

bp:
$("bp").value.trim(),

pulse:
$("pulse").value.trim(),

temperature:
$("temperature").value.trim(),

weight:
$("weight").value.trim(),

sugar:
$("sugar").value.trim(),

oxygen:
$("oxygen").value.trim()

};


if(
!item.bp &&
!item.pulse &&
!item.temperature &&
!item.weight &&
!item.sugar &&
!item.oxygen
){

toast(
"لږ تر لږه یو measurement ولیکه."
);

return;

}


tracker.unshift(item);

tracker =
tracker.slice(0,100);

save(
"medai_tracker",
tracker
);

renderTracker();

toast(
"❤️ Health data خوندي شو."
);

};


function renderTracker(){

const box =
$("trackerList");

if(!tracker.length){

box.innerHTML =
`
<div class="item">
تر اوسه Health data نشته.
</div>
`;

return;

}


box.innerHTML =
tracker.map(
(item,index) => `

<div class="item">

<div class="itemTop">

<b>
${escapeHTML(item.date)}
</b>

<button
class="danger"
onclick="deleteTracker(${index})"
>
حذف
</button>

</div>

<p>

BP:
${escapeHTML(item.bp || "-")}

<br>

Pulse:
${escapeHTML(item.pulse || "-")}

<br>

Temperature:
${escapeHTML(item.temperature || "-")}

<br>

Weight:
${escapeHTML(item.weight || "-")}

<br>

Sugar:
${escapeHTML(item.sugar || "-")}

<br>

Oxygen:
${escapeHTML(item.oxygen || "-")}

</p>

</div>

`
).join("");

}


window.deleteTracker =
function(index){

tracker.splice(
index,
1
);

save(
"medai_tracker",
tracker
);

renderTracker();

};


// =========================================================
// Medicine Reminder
// =========================================================

$("addReminder").onclick =
async () => {

const name =
$("medicineName").value.trim();

const time =
$("medicineTime").value;

const note =
$("medicineNote").value.trim();


if(!name || !time){

toast(
"د درمل نوم او وخت ولیکه."
);

return;

}


reminders.push({

id:
Date.now().toString(),

name:name,

time:time,

note:note

});


save(
"medai_reminders",
reminders
);

renderReminders();

$("medicineName").value = "";

$("medicineTime").value = "";

$("medicineNote").value = "";


if(
"Notification" in window &&
Notification.permission ===
"default"
){

try{

await Notification.requestPermission();

}catch{}

}


toast(
"💊 Reminder اضافه شو."
);

};


function renderReminders(){

const box =
$("reminderList");

if(!reminders.length){

box.innerHTML =
`
<div class="item">
تر اوسه Reminder نشته.
</div>
`;

return;

}


box.innerHTML =
reminders.map(
(item,index) => `

<div class="item">

<div class="itemTop">

<b>
💊 ${escapeHTML(item.name)}
</b>

<button
class="danger"
onclick="deleteReminder(${index})"
>
حذف
</button>

</div>

<p>
⏰ ${escapeHTML(item.time)}

${
item.note
?
"<br>📝 " +
escapeHTML(item.note)
:
""
}

</p>

</div>

`
).join("");

}


window.deleteReminder =
function(index){

reminders.splice(
index,
1
);

save(
"medai_reminders",
reminders
);

renderReminders();

};


// =========================================================
// Reminder Checker
// =========================================================

setInterval(
function(){

const now =
new Date();

const hh =
String(now.getHours())
.padStart(2,"0");

const mm =
String(now.getMinutes())
.padStart(2,"0");

const current =
hh + ":" + mm;

reminders.forEach(
item => {

if(
item.time !== current
)
return;


const key =
"medai_notified_" +
item.id +
"_" +
now.toDateString() +
"_" +
current;


if(
localStorage.getItem(key)
)
return;


localStorage.setItem(
key,
"1"
);


if(
"Notification" in window &&
Notification.permission ===
"granted"
){

new Notification(
"MedAI 💊 Reminder",
{
body:
"د درملو وخت: " +
item.name
}
);

}else{

toast(
"💊 د درملو وخت: " +
item.name
);

}

}
);

},
15000
);


// =========================================================
// Voice Input
// =========================================================

let recognition = null;

if(
"SpeechRecognition" in window ||
"webkitSpeechRecognition" in window
){

const SR =
window.SpeechRecognition ||
window.webkitSpeechRecognition;

recognition =
new SR();

recognition.lang =
"ps-AF";

recognition.interimResults =
false;

recognition.maxAlternatives =
1;

recognition.onresult =
event => {

$("message").value =
event.results[0][0]
.transcript;

};

recognition.onerror =
() => {

toast(
"Voice input فعال نه شو."
);

};

}else{

$("micBtn").disabled =
true;

}


$("micBtn").onclick =
() => {

if(recognition){

try{

recognition.start();

}catch{}

}

};


// =========================================================
// Voice Output
// =========================================================

$("speakBtn").onclick =
() => {

if(!lastAnswer){

toast(
"تر اوسه AI ځواب نشته."
);

return;

}

if(
!("speechSynthesis" in window)
){

toast(
"Voice output په browser کې نشته."
);

return;

}

speechSynthesis.cancel();

const speech =
new SpeechSynthesisUtterance(
lastAnswer
);

speech.lang =
"ps-AF";

speech.rate =
0.9;

speechSynthesis.speak(
speech
);

};


$("stopBtn").onclick =
() => {

if("speechSynthesis" in window)
speechSynthesis.cancel();

};


// =========================================================
// API - Chat
// =========================================================

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


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "app": "MedAI",
        "year": 2026,
        "gemini_configured": bool(GEMINI_API_KEY),
        "model": GEMINI_MODEL,
        "time": datetime.now(timezone.utc).isoformat()
    })


@app.post("/chat")
def chat():

    data = request.get_json(silent=True) or {}

    message = clean_text(
        data.get("message")
    )

    if not message:
        return jsonify({
            "answer": "مهرباني وکړه خپله پوښتنه ولیکه."
        }), 400

    if is_rate_limited():
        return jsonify({
            "answer":
                "ډېرې غوښتنې وشوې. لږه شېبه وروسته بیا هڅه وکړه."
        }), 429

    prompt = medical_prompt(
        "Answer the user's medical question.",
        message
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# Medical Tools
# =========================================================

@app.post("/symptoms")
def symptoms():

    data = request.get_json(silent=True) or {}

    return ai_tool(
        TASKS["symptoms"],
        data.get("text")
    )


@app.post("/vitals")
def vitals():

    data = request.get_json(silent=True) or {}

    return ai_tool(
        TASKS["vitals"],
        data.get("text")
    )


@app.post("/compare")
def compare():

    data = request.get_json(silent=True) or {}

    return ai_tool(
        TASKS["compare"],
        data.get("text")
    )


@app.post("/doctor")
def doctor():

    data = request.get_json(silent=True) or {}

    return ai_tool(
        TASKS["doctor"],
        data.get("text")
    )


@app.post("/lab")
def lab():

    data = request.get_json(silent=True) or {}

    return ai_tool(
        TASKS["lab"],
        data.get("text")
    )


@app.post("/medicine")
def medicine():

    data = request.get_json(silent=True) or {}

    return ai_tool(
        TASKS["medicine"],
        data.get("text")
    )


@app.post("/dictionary")
def dictionary():

    data = request.get_json(silent=True) or {}

    return ai_tool(
        TASKS["dictionary"],
        data.get("text")
    )


@app.post("/emergency")
def emergency():

    data = request.get_json(silent=True) or {}

    return ai_tool(
        TASKS["emergency"],
        data.get("text")
    )


@app.post("/interaction")
def interaction():

    data = request.get_json(silent=True) or {}

    return ai_tool(
        TASKS["interaction"],
        data.get("text")
    )


@app.post("/report")
def report():

    data = request.get_json(silent=True) or {}

    return ai_tool(
        TASKS["report"],
        data.get("text")
    )


@app.post("/firstaid")
def firstaid():

    data = request.get_json(silent=True) or {}

    return ai_tool(
        TASKS["firstaid"],
        data.get("text")
    )


@app.post("/glossary")
def glossary():

    data = request.get_json(silent=True) or {}

    return ai_tool(
        TASKS["glossary"],
        data.get("text")
    )


@app.post("/risk")
def risk():

    data = request.get_json(silent=True) or {}

    return ai_tool(
        TASKS["risk"],
        data.get("text")
    )


@app.post("/health-report")
def health_report():

    data = request.get_json(silent=True) or {}

    return ai_tool(
        TASKS["health-report"],
        data.get("text")
    )


@app.post("/quiz")
def quiz():

    data = request.get_json(silent=True) or {}

    return ai_tool(
        TASKS["quiz"],
        data.get("text")
    )


# =========================================================
# Wikimedia Images
# =========================================================

@app.get("/images")
def images():

    if is_rate_limited():

        return jsonify({
            "items": [],
            "error":
                "Too many requests"
        }), 429


    query =
    clean_text(
        request.args.get("q", ""),
        200
    )


    if not query:

        return jsonify({
            "items": []
        })


    params = {

        "action":
            "query",

        "generator":
            "search",

        "gsrsearch":
            query,

        "gsrnamespace":
            6,

        "gsrlimit":
            8,

        "prop":
            "imageinfo",

        "iiprop":
            "url",

        "iiurlwidth":
            600,

        "format":
            "json",

        "origin":
            "*"

    }


    try:

        r = requests.get(
            WIKIMEDIA_URL,
            params=params,
            timeout=15
        )

        r.raise_for_status()

        pages =
        r.json().get(
            "query",
            {}
        ).get(
            "pages",
            {}
        )


        items = []


        for page in pages.values():

            info =
            (
                page.get(
                    "imageinfo"
                ) or [{}]
            )[0]


            items.append({

                "title":
                    page.get(
                        "title",
                        ""
                    ),

                "url":
                    info.get(
                        "thumburl"
                    ) or info.get(
                        "url",
                        ""
                    ),

                "source":
                    info.get(
                        "descriptionurl"
                    ) or
                    "https://commons.wikimedia.org/"

            })


        return jsonify({
            "items": items
        })


    except Exception:

        logger.exception(
            "Wikimedia error"
        )

        return jsonify({
            "items": [],
            "error":
                "انځورونه ونه موندل شول."
        }), 502


# =========================================================
# Error Handling
# =========================================================

@app.errorhandler(413)
def too_large(error):

    return jsonify({
        "answer":
            "غوښتنه ډېره لویه ده. متن لنډ کړه."
    }), 413


@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "error":
            "دا صفحه ونه موندل شوه."
    }), 404


@app.errorhandler(500)
def server_error(error):

    logger.exception(
        "Internal server error"
    )

    return jsonify({
        "error":
            "د سرور داخلي ستونزه."
    }), 500


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024

    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "5000"
            )
        ),
        debug=False
    )
