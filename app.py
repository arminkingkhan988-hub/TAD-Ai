from flask import Flask, request, jsonify, render_template_string
import os
import json
import urllib.request
import urllib.error
import time

app = Flask(__name__)

# =========================================================
# CONFIG
# =========================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# Current Gemini model
GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
).strip()

# Fallback model
GEMINI_FALLBACK_MODEL = os.environ.get(
    "GEMINI_FALLBACK_MODEL",
    "gemini-3.5-flash"
).strip()

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/{model}:generateContent"
)

MAX_MESSAGE = 20000
MAX_HISTORY = 24


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are MedAI, a general-purpose AI assistant.

Your name is MedAI.

Developer:
Toyebullah Dawoodzay.

Created:
2026.

IMPORTANT:
You are NOT limited to medical questions.

You should answer general questions like a modern general-purpose AI assistant.

You can help with:

- General knowledge
- Science
- Mathematics
- Programming
- Coding
- Debugging
- Technology
- Education
- Writing
- Rewriting
- Translation
- Summaries
- Business
- Study help
- History
- Geography
- Languages
- Creative writing
- Ideas and brainstorming
- Explanations
- Computer questions
- Website development
- Python
- JavaScript
- HTML
- CSS
- Flask
- APIs
- Databases
- AI
- General life information
- And other normal questions.

LANGUAGE RULE:

Always answer in the same language as the user's question whenever possible.

If the user asks in Pashto, answer in Pashto.

If the user asks in Dari, answer in Dari.

If the user asks in Urdu, answer in Urdu.

If the user asks in Arabic, answer in Arabic.

If the user asks in English, answer in English.

If the user asks in another language, answer in that language if you can.

For Pashto, use clear and natural Pashto.

Do not unnecessarily translate the user's question.

GENERAL ANSWERING RULES:

- Understand the user's actual question.
- Give a direct answer.
- Be helpful and clear.
- Do not unnecessarily refuse normal questions.
- If the question needs explanation, explain step by step.
- If the user asks for code, provide useful working code.
- If the user asks to rewrite something, provide the rewritten version.
- If the user asks for translation, translate accurately.
- If the user asks a mathematical question, calculate carefully.
- If you are uncertain about a fact, clearly say that you are uncertain.
- Never invent sources, facts, quotations, or events.
- Do not pretend to have performed an action that you did not perform.
- Do not claim internet access unless an actual browsing tool is available.
- Do not claim to see files, images, accounts, or private information unless they are actually provided.

MEDICAL SAFETY:

You can provide general educational medical information.

However:

- Do not claim to diagnose a person.
- Symptoms alone cannot confirm a diagnosis.
- Do not claim that you physically examined the user.
- Do not provide unsafe personalized medical treatment.
- Do not provide personalized prescription dosing.
- Do not tell a user to start, stop, or change prescription medicine without professional medical guidance.
- Encourage consultation with a qualified healthcare professional for personal medical decisions.
- For possible emergencies, clearly recommend urgent professional medical help.
- If symptoms suggest a possible emergency, explain the warning signs and advise appropriate urgent care.
- Do not create false certainty.

MEDICINES:

For medicine questions, you may explain:

- Common uses
- General mechanism
- Common side effects
- General precautions
- Common interactions
- Questions to discuss with a doctor or pharmacist

Do not give personalized prescription changes or unsafe dosing instructions.

If asked who created you, say:

"زه MedAI یم، د Toyebullah Dawoodzay لخوا په ۲۰۲۶ کال کې جوړ شوی یم."

Be useful, respectful, concise when the question is simple, and detailed when the user asks for detail.
"""


# =========================================================
# GEMINI REQUEST
# =========================================================

def call_gemini(model, message, history):

    url = GEMINI_URL.format(model=model)

    contents = []

    for item in (history or [])[-MAX_HISTORY:]:

        if not isinstance(item, dict):
            continue

        role = item.get("role", "user")

        if role not in ("user", "model"):
            role = "user"

        text = str(
            item.get("text", "")
        ).strip()

        if not text:
            continue

        contents.append({
            "role": role,
            "parts": [
                {
                    "text": text[:MAX_MESSAGE]
                }
            ]
        })

    # Always add the current user message.
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
                    "text": SYSTEM_PROMPT
                }
            ]
        },
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": 4096
        }
    }

    body = json.dumps(
        payload,
        ensure_ascii=False
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        },
        method="POST"
    )

    with urllib.request.urlopen(
        req,
        timeout=60
    ) as response:

        raw = response.read().decode(
            "utf-8",
            errors="replace"
        )

    return json.loads(raw)


# =========================================================
# EXTRACT GEMINI RESPONSE
# =========================================================

def extract_answer(data):

    candidates = data.get("candidates") or []

    if not candidates:
        raise RuntimeError(
            "Gemini returned no candidates."
        )

    parts = (
        candidates[0]
        .get("content", {})
        .get("parts", [])
    )

    answer = "".join(
        part.get("text", "")
        for part in parts
        if isinstance(part, dict)
    ).strip()

    if not answer:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return answer


# =========================================================
# SECURITY HEADERS
# =========================================================

@app.after_request
def security_headers(response):

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "X-Frame-Options"
    ] = "SAMEORIGIN"

    response.headers[
        "Referrer-Policy"
    ] = "strict-origin-when-cross-origin"

    response.headers[
        "Permissions-Policy"
    ] = "camera=(), geolocation=(), payment=()"

    return response


# =========================================================
# FRONTEND
# =========================================================

HTML = r"""
<!doctype html>

<html lang="ps" dir="rtl">

<head>

<meta charset="utf-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1"
>

<meta
    name="theme-color"
    content="#ffffff"
>

<title>MedAI</title>

<style>

*{
    box-sizing:border-box;
}

:root{
    --bg:#ffffff;
    --panel:#f7f7f8;
    --text:#202123;
    --muted:#6b7280;
    --border:#e5e7eb;
    --blue:#1677ff;
    --blue2:#0d5ed7;
    --user:#eef6ff;
}

body.dark{
    --bg:#212121;
    --panel:#171717;
    --text:#eeeeee;
    --muted:#a1a1aa;
    --border:#383838;
    --user:#29394d;
}

html,
body{
    margin:0;
    width:100%;
    height:100%;
    background:var(--bg);
    color:var(--text);
    font-family:
        Arial,
        "Noto Sans Arabic",
        sans-serif;
}

body{
    overflow:hidden;
}

button,
textarea,
input{
    font:inherit;
}

button{
    cursor:pointer;
}

/* APP */

.app{
    width:100%;
    height:100vh;
    display:flex;
}

/* SIDEBAR */

.sidebar{
    width:280px;
    height:100vh;
    background:var(--panel);
    border-left:1px solid var(--border);
    position:fixed;
    right:0;
    top:0;
    z-index:50;
    padding:13px;
    display:flex;
    flex-direction:column;
    transition:.25s;
}

.logo-area{
    display:flex;
    align-items:center;
    gap:9px;
    margin-bottom:14px;
}

.logo{
    width:40px;
    height:40px;
    border-radius:12px;
    background:var(--blue);
    color:white;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:22px;
}

.logo-name{
    font-size:19px;
    font-weight:800;
}

.new-chat{
    width:100%;
    border:0;
    background:var(--blue);
    color:white;
    padding:12px;
    border-radius:11px;
    font-weight:700;
    margin-bottom:12px;
}

.new-chat:hover{
    background:var(--blue2);
}

.menu-title{
    color:var(--muted);
    font-size:11px;
    margin:12px 7px 6px;
}

.side-btn{
    width:100%;
    border:0;
    background:transparent;
    color:var(--text);
    padding:11px;
    border-radius:10px;
    text-align:right;
    margin-bottom:2px;
}

.side-btn:hover{
    background:rgba(128,128,128,.12);
}

.sidebar-bottom{
    margin-top:auto;
    border-top:1px solid var(--border);
    padding-top:8px;
}

/* MAIN */

.main{
    width:calc(100% - 280px);
    margin-right:280px;
    height:100vh;
    display:flex;
    flex-direction:column;
    position:relative;
}

/* TOPBAR */

.topbar{
    height:58px;
    min-height:58px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:0 17px;
    border-bottom:1px solid var(--border);
    background:var(--bg);
    z-index:10;
}

.top-left{
    display:flex;
    align-items:center;
    gap:9px;
}

.top-title{
    font-weight:800;
    font-size:16px;
}

.model{
    color:var(--muted);
    font-size:11px;
}

.icon-btn{
    border:0;
    background:transparent;
    color:var(--text);
    width:39px;
    height:39px;
    border-radius:10px;
    font-size:18px;
}

.icon-btn:hover{
    background:var(--panel);
}

.mobile-menu{
    display:none;
}

/* CHAT */

.chat-area{
    flex:1;
    overflow-y:auto;
    padding:25px 18px 180px;
}

.chat-content{
    max-width:820px;
    margin:auto;
}

/* WELCOME */

.welcome{
    min-height:60vh;
    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;
}

.welcome-inner{
    width:100%;
}

.welcome-logo{
    width:68px;
    height:68px;
    border-radius:21px;
    background:var(--blue);
    color:white;
    display:flex;
    align-items:center;
    justify-content:center;
    margin:0 auto 16px;
    font-size:35px;
}

.welcome h1{
    margin:0 0 9px;
    font-size:28px;
}

.welcome p{
    max-width:650px;
    margin:0 auto 25px;
    color:var(--muted);
    line-height:1.8;
}

.suggestions{
    max-width:650px;
    margin:auto;
    display:grid;
    grid-template-columns:repeat(2,1fr);
    gap:9px;
}

.suggestion{
    border:1px solid var(--border);
    background:var(--bg);
    color:var(--text);
    padding:14px;
    border-radius:13px;
    text-align:right;
}

.suggestion:hover{
    border-color:var(--blue);
}

/* MESSAGES */

.message{
    display:flex;
    gap:12px;
    padding:17px 3px;
    line-height:1.9;
}

.message.user{
    background:var(--user);
    border-radius:15px;
    padding:14px;
    margin:7px 0;
}

.avatar{
    width:33px;
    min-width:33px;
    height:33px;
    border-radius:10px;
    background:var(--blue);
    color:white;
    display:flex;
    align-items:center;
    justify-content:center;
}

.user .avatar{
    background:#68707a;
}

.message-body{
    flex:1;
    min-width:0;
    overflow-wrap:anywhere;
}

.ai-text{
    white-space:pre-wrap;
}

.message-actions{
    display:flex;
    gap:3px;
    margin-top:8px;
}

.message-action{
    border:0;
    background:transparent;
    color:var(--muted);
    padding:5px 8px;
    border-radius:7px;
}

.message-action:hover{
    background:var(--panel);
}

/* COMPOSER */

.composer-wrap{
    position:absolute;
    bottom:0;
    left:0;
    right:0;
    padding:13px 18px 17px;
    background:linear-gradient(
        transparent,
        var(--bg) 30%
    );
}

.composer{
    max-width:820px;
    margin:auto;
    border:1px solid var(--border);
    border-radius:18px;
    background:var(--bg);
    box-shadow:0 6px 28px rgba(0,0,0,.08);
    overflow:hidden;
}

textarea{
    resize:none;
}

#question{
    width:100%;
    min-height:58px;
    max-height:190px;
    padding:15px;
    border:0;
    outline:0;
    background:transparent;
    color:var(--text);
    line-height:1.7;
}

.composer-bottom{
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:6px 8px 8px;
}

.composer-tools{
    display:flex;
    gap:3px;
}

.tool-btn{
    border:0;
    background:transparent;
    color:var(--muted);
    width:38px;
    height:38px;
    border-radius:9px;
}

.tool-btn:hover{
    background:var(--panel);
}

.send-btn{
    width:43px;
    height:43px;
    border:0;
    border-radius:12px;
    background:var(--blue);
    color:white;
    font-size:18px;
}

.send-btn:disabled{
    opacity:.45;
}

.disclaimer{
    max-width:820px;
    margin:7px auto 0;
    color:var(--muted);
    font-size:10px;
    text-align:center;
}

.status{
    max-width:820px;
    margin:0 auto 4px;
    color:var(--muted);
    font-size:12px;
    text-align:center;
}

/* MODAL */

.modal{
    display:none;
    position:fixed;
    inset:0;
    z-index:100;
    background:rgba(0,0,0,.55);
    padding:15px;
    overflow:auto;
}

.modal.show{
    display:block;
}

.modal-box{
    max-width:680px;
    margin:45px auto;
    background:var(--bg);
    color:var(--text);
    border:1px solid var(--border);
    border-radius:18px;
    padding:20px;
}

.modal-box h3{
    margin-top:0;
}

.modal-input{
    width:100%;
    padding:12px;
    border-radius:10px;
    border:1px solid var(--border);
    background:var(--panel);
    color:var(--text);
    margin-bottom:9px;
    outline:0;
}

.modal-row{
    display:flex;
    gap:8px;
    margin-top:8px;
}

.modal-row button{
    flex:1;
    padding:10px;
    border:0;
    border-radius:9px;
}

.primary{
    background:var(--blue);
    color:white;
}

.secondary{
    background:var(--panel);
    color:var(--text);
}

.danger{
    background:#ffe8e6;
    color:#c62828;
}

.small{
    color:var(--muted);
    font-size:12px;
    line-height:1.8;
}

.history-item{
    border-bottom:1px solid var(--border);
    padding:12px 0;
}

.favorite-item{
    border:1px solid var(--border);
    border-radius:10px;
    padding:12px;
    margin-bottom:8px;
    white-space:pre-wrap;
}

.pill{
    display:inline-block;
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:20px;
    padding:6px 10px;
    margin:4px;
    font-size:12px;
}

/* MOBILE */

@media(max-width:760px){

    .sidebar{
        width:290px;
        transform:translateX(100%);
        box-shadow:-15px 0 40px rgba(0,0,0,.18);
    }

    .sidebar.open{
        transform:translateX(0);
    }

    .main{
        width:100%;
        margin-right:0;
    }

    .mobile-menu{
        display:block;
    }

    .model{
        display:none;
    }

    .chat-area{
        padding:18px 11px 175px;
    }

    .composer-wrap{
        padding:8px 8px 12px;
    }

    .suggestions{
        grid-template-columns:1fr;
    }

    .welcome h1{
        font-size:24px;
    }

    .welcome-logo{
        width:58px;
        height:58px;
        font-size:30px;
    }

    .message{
        padding:13px 1px;
    }

}

</style>

</head>

<body>

<div class="app">

<!-- SIDEBAR -->

<aside
    class="sidebar"
    id="sidebar"
>

    <div class="logo-area">

        <div class="logo">
            🩺
        </div>

        <div class="logo-name">
            MedAI
        </div>

    </div>

    <button
        class="new-chat"
        onclick="newChat()"
    >
        ＋ نوی چټ
    </button>

    <div class="menu-title">
        اصلي
    </div>

    <button
        class="side-btn"
        onclick="showHistory()"
    >
        🕘 د چټ تاریخچه
    </button>

    <button
        class="side-btn"
        onclick="showFavorites()"
    >
        ⭐ خوښې
    </button>

    <div class="menu-title">
        AI Tools
    </div>

    <button
        class="side-btn"
        onclick="preset('د دې موضوع په اړه معلومات راکړه: ')"
    >
        💡 معلومات
    </button>

    <button
        class="side-btn"
        onclick="preset('دا متن راته ولیکه/اصلاح کړه: ')"
    >
        ✍️ لیکل
    </button>

    <button
        class="side-btn"
        onclick="preset('دا متن راته وژباړه: ')"
    >
        🌐 ژباړه
    </button>

    <button
        class="side-btn"
        onclick="preset('دا موضوع راته په ساده ډول تشریح کړه: ')"
    >
        📚 زده کړه
    </button>

    <button
        class="side-btn"
        onclick="preset('دا طبي موضوع راته تشریح کړه: ')"
    >
        🩺 طبي معلومات
    </button>

    <button
        class="side-btn"
        onclick="preset('دا کوډ راته اصلاح او تشریح کړه: ')"
    >
        💻 Coding
    </button>

    <button
        class="side-btn"
        onclick="openModal('tracker')"
    >
        📊 Health Tracker
    </button>

    <button
        class="side-btn"
        onclick="openModal('reminder')"
    >
        ⏰ Reminders
    </button>

    <div class="sidebar-bottom">

        <button
            class="side-btn"
            onclick="toggleDark()"
        >
            🌙 Dark / Light
        </button>

        <button
            class="side-btn"
            onclick="openModal('about')"
        >
            ℹ️ د MedAI په اړه
        </button>

    </div>

</aside>


<!-- MAIN -->

<main class="main">

    <header class="topbar">

        <div class="top-left">

            <button
                class="icon-btn mobile-menu"
                onclick="toggleSidebar()"
            >
                ☰
            </button>

            <div>

                <div class="top-title">
                    MedAI
                </div>

                <div class="model">
                    General AI Assistant
                </div>

            </div>

        </div>

        <div>

            <button
                class="icon-btn"
                onclick="newChat()"
                title="New Chat"
            >
                ＋
            </button>

            <button
                class="icon-btn"
                onclick="toggleDark()"
                title="Dark Mode"
            >
                ◐
            </button>

        </div>

    </header>


    <section
        class="chat-area"
        id="chatArea"
    >

        <div
            class="chat-content"
            id="chatContent"
        >

            <div
                class="welcome"
                id="welcome"
            >

                <div class="welcome-inner">

                    <div class="welcome-logo">
                        🩺
                    </div>

                    <h1>
                        له MedAI څخه هره پوښتنه وکړئ
                    </h1>

                    <p>
                        MedAI یو General AI Assistant دی.
                        طبي، تعلیمي، تخنیکي، Coding، ژباړې،
                        لیکلو او نورو عادي پوښتنو ته ځواب ورکوي.
                    </p>

                    <div class="suggestions">

                        <button
                            class="suggestion"
                            onclick="preset('Gemini AI څه شی دی؟')"
                        >
                            🤖 AI څه شی دی؟
                        </button>

                        <button
                            class="suggestion"
                            onclick="preset('Python راته له صفر څخه تشریح کړه.')"
                        >
                            💻 Python زده کړه
                        </button>

                        <button
                            class="suggestion"
                            onclick="preset('د انسان د زړه د کار کولو طریقه تشریح کړه.')"
                        >
                            🫀 طبي معلومات
                        </button>

                        <button
                            class="suggestion"
                            onclick="preset('دا جمله انګلیسي ته وژباړه: سلام، څنګه یې؟')"
                        >
                            🌐 ژباړه
                        </button>

                    </div>

                </div>

            </div>

        </div>

    </section>


    <!-- COMPOSER -->

    <div class="composer-wrap">

        <div
            class="status"
            id="status"
        ></div>

        <div class="composer">

            <textarea
                id="question"
                rows="1"
                placeholder="له MedAI څخه هره پوښتنه وکړئ..."
            ></textarea>

            <div class="composer-bottom">

                <div class="composer-tools">

                    <button
                        class="tool-btn"
                        onclick="startVoice()"
                        title="Voice Input"
                    >
                        🎤
                    </button>

                    <button
                        class="tool-btn"
                        onclick="speakLast()"
                        title="Read Answer"
                    >
                        🔊
                    </button>

                    <button
                        class="tool-btn"
                        onclick="saveFavorite()"
                        title="Favorite"
                    >
                        ⭐
                    </button>

                </div>

                <button
                    id="sendBtn"
                    class="send-btn"
                    onclick="askAI()"
                >
                    ➤
                </button>

            </div>

        </div>

        <div class="disclaimer">
            MedAI د معلوماتو او زده کړې لپاره دی.
            د مهمو طبي پرېکړو لپاره له مسلکي روغتیايي کارکوونکي سره مشوره وکړئ.
        </div>

    </div>

</main>

</div>


<!-- MODAL -->

<div
    class="modal"
    id="modal"
>

    <div
        class="modal-box"
        id="modalBox"
    ></div>

</div>


<script>

/* ========================================================
   STATE
======================================================== */

let lastAnswer = "";

let conversation = [];

let historyList =
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


/* ========================================================
   HELPERS
======================================================== */

function escapeHtml(value){

    return String(value).replace(
        /[&<>"']/g,
        function(c){

            return {
                "&":"&amp;",
                "<":"&lt;",
                ">":"&gt;",
                '"':"&quot;",
                "'":"&#39;"
            }[c];

        }
    );

}


function scrollBottom(){

    const area =
        document.getElementById("chatArea");

    setTimeout(
        function(){

            area.scrollTop =
                area.scrollHeight;

        },
        60
    );

}


/* ========================================================
   SIDEBAR
======================================================== */

function toggleSidebar(){

    document
        .getElementById("sidebar")
        .classList
        .toggle("open");

}

function closeSidebar(){

    document
        .getElementById("sidebar")
        .classList
        .remove("open");

}


/* ========================================================
   DARK MODE
======================================================== */

function toggleDark(){

    document.body.classList.toggle("dark");

    localStorage.setItem(
        "medai_dark",
        document.body.classList.contains("dark")
            ? "1"
            : "0"
    );

}

if(
    localStorage.getItem("medai_dark") === "1"
){

    document.body.classList.add("dark");

}


/* ========================================================
   NEW CHAT
======================================================== */

function newChat(){

    conversation = [];

    lastAnswer = "";

    const content =
        document.getElementById("chatContent");

    content.innerHTML = `

        <div
            class="welcome"
            id="welcome"
        >

            <div class="welcome-inner">

                <div class="welcome-logo">
                    🩺
                </div>

                <h1>
                    له MedAI څخه هره پوښتنه وکړئ
                </h1>

                <p>
                    خپله پوښتنه ولیکئ.
                </p>

                <div class="suggestions">

                    <button
                        class="suggestion"
                        onclick="preset('AI څه شی دی؟')"
                    >
                        🤖 AI
                    </button>

                    <button
                        class="suggestion"
                        onclick="preset('Python راته تشریح کړه.')"
                    >
                        💻 Python
                    </button>

                    <button
                        class="suggestion"
                        onclick="preset('د زړه په اړه معلومات راکړه.')"
                    >
                        🫀 طب
                    </button>

                    <button
                        class="suggestion"
                        onclick="preset('دا جمله انګلیسي ته وژباړه: سلام')"
                    >
                        🌐 ژباړه
                    </button>

                </div>

            </div>

        </div>

    `;

    document.getElementById(
        "question"
    ).value = "";

    document.getElementById(
        "status"
    ).textContent = "";

    closeSidebar();

}


/* ========================================================
   ADD USER MESSAGE
======================================================== */

function addUserMessage(text){

    const content =
        document.getElementById("chatContent");

    const welcome =
        document.getElementById("welcome");

    if(welcome){

        welcome.remove();

    }

    const wrapper =
        document.createElement("div");

    wrapper.className =
        "message user";

    wrapper.innerHTML = `

        <div class="avatar">
            👤
        </div>

        <div class="message-body">
            ${escapeHtml(text)}
        </div>

    `;

    content.appendChild(wrapper);

}


/* ========================================================
   ADD AI MESSAGE
======================================================== */

function addAIMessage(text){

    const content =
        document.getElementById("chatContent");

    const wrapper =
        document.createElement("div");

    wrapper.className =
        "message ai";

    wrapper.innerHTML = `

        <div class="avatar">
            🩺
        </div>

        <div class="message-body">

            <div class="ai-text"></div>

            <div class="message-actions">

                <button
                    class="message-action"
                    onclick="copyMessage(this)"
                >
                    📋 کاپي
                </button>

                <button
                    class="message-action"
                    onclick="saveFavorite()"
                >
                    ⭐ خوندي
                </button>

                <button
                    class="message-action"
                    onclick="speakLast()"
                >
                    🔊 واورئ
                </button>

            </div>

        </div>

    `;

    wrapper
        .querySelector(".ai-text")
        .textContent = text;

    content.appendChild(wrapper);

    return wrapper;

}


/* ========================================================
   PRESET
======================================================== */

function preset(text){

    const input =
        document.getElementById("question");

    input.value = text;

    autoResize();

    input.focus();

    closeSidebar();

}


/* ========================================================
   ASK AI
======================================================== */

async function askAI(){

    const input =
        document.getElementById("question");

    const button =
        document.getElementById("sendBtn");

    const status =
        document.getElementById("status");

    const message =
        input.value.trim();

    if(!message){

        return;

    }

    if(message.length > 20000){

        alert(
            "پوښتنه ډېره اوږده ده."
        );

        return;

    }

    addUserMessage(message);

    input.value = "";

    autoResize();

    button.disabled = true;

    status.textContent =
        "MedAI فکر کوي...";

    scrollBottom();


    const oldHistory =
        conversation.slice(-24);


    try{

        const response =
            await fetch(
                "/api/chat",
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({

                            message:message,

                            history:
                                oldHistory

                        })

                    }
                );


        let data = {};

        try{

            data =
                await response.json();

        }catch{

            data = {};

        }


        if(!response.ok){

            throw new Error(
                data.error ||
                "API request failed."
            );

        }


        const answer =
            data.reply ||
            "ځواب ترلاسه نه شو.";


        lastAnswer = answer;


        addAIMessage(answer);


        conversation.push(
            {
                role:"user",
                text:message
            },
            {
                role:"model",
                text:answer
            }
        );


        saveHistory(
            message,
            answer
        );


        status.textContent =
            data.model
                ? "چمتو دی"
                : "";


        scrollBottom();


    }catch(error){

        addAIMessage(
            "بخښنه، ستونزه رامنځته شوه:\n\n" +
            error.message
        );

        status.textContent =
            "Error";

        scrollBottom();

    }finally{

        button.disabled = false;

    }

}


/* ========================================================
   AUTO RESIZE
======================================================== */

function autoResize(){

    const textarea =
        document.getElementById("question");

    textarea.style.height = "auto";

    textarea.style.height =
        Math.min(
            textarea.scrollHeight,
            190
        ) + "px";

}


/* ========================================================
   ENTER
======================================================== */

document
    .getElementById("question")
    .addEventListener(
        "input",
        autoResize
    );


document
    .getElementById("question")
    .addEventListener(
        "keydown",
        function(event){

            if(
                event.key === "Enter" &&
                !event.shiftKey
            ){

                event.preventDefault();

                askAI();

            }

        }
    );


/* ========================================================
   COPY
======================================================== */

function copyMessage(button){

    const text =
        button
            .closest(".message")
            .querySelector(".ai-text")
            .textContent;

    if(navigator.clipboard){

        navigator.clipboard.writeText(text);

        button.textContent =
            "✓ کاپي شو";

        setTimeout(
            function(){

                button.textContent =
                    "📋 کاپي";

            },
            1200
        );

    }

}


/* ========================================================
   VOICE OUTPUT
======================================================== */

function speakLast(){

    if(
        !lastAnswer ||
        !("speechSynthesis" in window)
    ){

        return;

    }

    speechSynthesis.cancel();

    const speech =
        new SpeechSynthesisUtterance(
            lastAnswer
        );

    speech.lang = "ps-AF";

    speech.rate = 1;

    speechSynthesis.speak(
        speech
    );

}


/* ========================================================
   VOICE INPUT
======================================================== */

function startVoice(){

    const Recognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if(!Recognition){

        alert(
            "ستاسې براوزر Voice Input نه ملاتړ کوي."
        );

        return;

    }

    const recognition =
        new Recognition();

    recognition.lang =
        "ps-AF";

    recognition.interimResults =
        false;

    recognition.maxAlternatives =
        1;

    recognition.onresult =
        function(event){

            const text =
                event
                    .results[0][0]
                    .transcript;

            document.getElementById(
                "question"
            ).value = text;

            autoResize();

        };

    recognition.onerror =
        function(){

            alert(
                "Voice Input کې ستونزه راغله."
            );

        };

    recognition.start();

}


/* ========================================================
   FAVORITES
======================================================== */

function saveFavorite(){

    if(!lastAnswer){

        alert(
            "لومړی AI ځواب ترلاسه کړئ."
        );

        return;

    }

    if(!favorites.includes(lastAnswer)){

        favorites.unshift(
            lastAnswer
        );

    }

    favorites =
        favorites.slice(0,50);

    localStorage.setItem(
        "medai_favorites",
        JSON.stringify(favorites)
    );

}


function showFavorites(){

    openModal("favorites");

    closeSidebar();

}


function clearFavorites(){

    favorites = [];

    localStorage.setItem(
        "medai_favorites",
        "[]"
    );

    openModal("favorites");

}


/* ========================================================
   HISTORY
======================================================== */

function saveHistory(q,a){

    historyList.unshift({

        q:q,

        a:a,

        t:new Date().toLocaleString()

    });

    historyList =
        historyList.slice(0,50);

    localStorage.setItem(
        "medai_history",
        JSON.stringify(historyList)
    );

}


function showHistory(){

    openModal("history");

    closeSidebar();

}


function clearHistory(){

    historyList = [];

    localStorage.setItem(
        "medai_history",
        "[]"
    );

    openModal("history");

}


/* ========================================================
   MODAL
======================================================== */

function openModal(type){

    const modal =
        document.getElementById("modal");

    const box =
        document.getElementById("modalBox");

    let html = "";


    /* HISTORY */

    if(type === "history"){

        html = `

            <h3>
                🕘 د چټ تاریخچه
            </h3>

            ${
                historyList.length
                ?

                historyList.map(
                    function(x){

                        return `

                            <div class="history-item">

                                <div class="small">
                                    ${escapeHtml(x.t)}
                                </div>

                                <b>
                                    پوښتنه:
                                </b>

                                <div>
                                    ${escapeHtml(x.q)}
                                </div>

                                <br>

                                <b>
                                    ځواب:
                                </b>

                                <div>
                                    ${escapeHtml(x.a)}
                                </div>

                            </div>

                        `;

                    }
                ).join("")

                :

                "<p>تر اوسه تاریخچه نشته.</p>"
            }

            <div class="modal-row">

                <button
                    class="danger"
                    onclick="clearHistory()"
                >
                    Clear
                </button>

                <button
                    class="secondary"
                    onclick="closeModal()"
                >
                    Close
                </button>

            </div>

        `;

    }


    /* FAVORITES */

    if(type === "favorites"){

        html = `

            <h3>
                ⭐ خوښې
            </h3>

            ${
                favorites.length
                ?

                favorites.map(
                    function(x){

                        return `
                            <div class="favorite-item">
                                ${escapeHtml(x)}
                            </div>
                        `;

                    }
                ).join("")

                :

                "<p>تر اوسه Favorite نشته.</p>"
            }

            <div class="modal-row">

                <button
                    class="danger"
                    onclick="clearFavorites()"
                >
                    Clear
                </button>

                <button
                    class="secondary"
                    onclick="closeModal()"
                >
                    Close
                </button>

            </div>

        `;

    }


    /* TRACKER */

    if(type === "tracker"){

        html = `

            <h3>
                📊 Health Tracker
            </h3>

            <p class="small">
                دلته ساده روغتیايي یادښتونه
                په همدې براوزر کې ساتل کېږي.
            </p>

            <input
                class="modal-input"
                id="metric"
                placeholder="مثلاً: وزن 70kg"
            >

            <div class="modal-row">

                <button
                    class="primary"
                    onclick="saveTracker()"
                >
                    Save
                </button>

                <button
                    class="secondary"
                    onclick="closeModal()"
                >
                    Close
                </button>

            </div>

            <div>

                ${
                    tracker.length
                    ?

                    tracker.map(
                        function(x){

                            return `
                                <span class="pill">
                                    ${escapeHtml(x)}
                                </span>
                            `;

                        }
                    ).join("")

                    :

                    "<p class='small'>هیڅ یادښت نشته.</p>"
                }

            </div>

        `;

    }


    /* REMINDER */

    if(type === "reminder"){

        html = `

            <h3>
                ⏰ Reminders
            </h3>

            <p class="small">
                یادونې په دې براوزر کې ساتل کېږي.
            </p>

            <input
                class="modal-input"
                id="reminderText"
                placeholder="د یادونې متن"
            >

            <input
                class="modal-input"
                id="reminderTime"
                type="time"
            >

            <div class="modal-row">

                <button
                    class="primary"
                    onclick="saveReminder()"
                >
                    Save
                </button>

                <button
                    class="secondary"
                    onclick="closeModal()"
                >
                    Close
                </button>

            </div>

            <div>

                ${
                    reminders.length
                    ?

                    reminders.map(
                        function(x){

                            return `
                                <span class="pill">
                                    ${escapeHtml(x.text)}
                                    —
                                    ${escapeHtml(x.time)}
                                </span>
                            `;

                        }
                    ).join("")

                    :

                    "<p class='small'>هیڅ reminder نشته.</p>"
                }

            </div>

        `;

    }


    /* ABOUT */

    if(type === "about"){

        html = `

            <h3>
                ℹ️ د MedAI په اړه
            </h3>

            <p>
                MedAI یو General AI Assistant دی
                چې د Gemini API له لارې ځوابونه جوړوي.
            </p>

            <p>
                <b>Developer:</b>
                Toyebullah Dawoodzay
            </p>

            <p>
                <b>Created:</b>
                2026
            </p>

            <p class="small">
                MedAI د طبي معلوماتو لپاره د ډاکټر
                بدیل نه دی.
            </p>

            <button
                class="secondary"
                onclick="closeModal()"
            >
                Close
            </button>

        `;

    }


    box.innerHTML = html;

    modal.classList.add("show");

}


function closeModal(){

    document
        .getElementById("modal")
        .classList
        .remove("show");

}


/* ========================================================
   TRACKER
======================================================== */

function saveTracker(){

    const input =
        document.getElementById("metric");

    if(!input){

        return;

    }

    const value =
        input.value.trim();

    if(!value){

        return;

    }

    tracker.unshift(
        new Date().toLocaleDateString()
        + " — "
        + value
    );

    tracker =
        tracker.slice(0,100);

    localStorage.setItem(
        "medai_tracker",
        JSON.stringify(tracker)
    );

    openModal("tracker");

}


/* ========================================================
   REMINDER
======================================================== */

function saveReminder(){

    const textInput =
        document.getElementById(
            "reminderText"
        );

    const timeInput =
        document.getElementById(
            "reminderTime"
        );

    if(!textInput || !timeInput){

        return;

    }

    const text =
        textInput.value.trim();

    const time =
        timeInput.value;

    if(!text || !time){

        return;

    }

    reminders.unshift({

        text:text,

        time:time

    });

    reminders =
        reminders.slice(0,100);

    localStorage.setItem(
        "medai_reminders",
        JSON.stringify(reminders)
    );

    openModal("reminder");

}


/* ========================================================
   MODAL CLICK
======================================================== */

document
    .getElementById("modal")
    .addEventListener(
        "click",
        function(event){

            if(
                event.target.id === "modal"
            ){

                closeModal();

            }

        }
    );


/* ========================================================
   ESC
======================================================== */

document.addEventListener(
    "keydown",
    function(event){

        if(event.key === "Escape"){

            closeModal();

            closeSidebar();

        }

    }
);


/* ========================================================
   MOBILE OUTSIDE SIDEBAR
======================================================== */

document.addEventListener(
    "click",
    function(event){

        const sidebar =
            document.getElementById(
                "sidebar"
            );

        if(
            window.innerWidth <= 760 &&
            sidebar.classList.contains("open") &&
            !sidebar.contains(event.target) &&
            !event.target.closest(".mobile-menu")
        ){

            closeSidebar();

        }

    }
);

</script>

</body>

</html>
"""


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return render_template_string(
        HTML
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return jsonify({

        "ok": True,

        "service": "MedAI",

        "primary_model":
            GEMINI_MODEL,

        "fallback_model":
            GEMINI_FALLBACK_MODEL,

        "gemini_configured":
            bool(GEMINI_API_KEY)

    })


# =========================================================
# CHAT API
# =========================================================

@app.post("/api/chat")
def api_chat():

    if not GEMINI_API_KEY:

        return jsonify({

            "error":
                "GEMINI_API_KEY په Vercel Environment Variables کې نه دی تنظیم شوی."

        }), 500


    data =
        request.get_json(
            silent=True
        ) or {}


    message =
        str(
            data.get(
                "message",
                ""
            )
        ).strip()


    if not message:

        return jsonify({

            "error":
                "مهرباني وکړئ خپله پوښتنه ولیکئ."

        }), 400


    if len(message) > MAX_MESSAGE:

        return jsonify({

            "error":
                "ستاسې پوښتنه ډېره اوږده ده."

        }), 413


    history =
        data.get(
            "history",
            []
        )


    if not isinstance(history, list):

        history = []


    models = [
        GEMINI_MODEL,
        GEMINI_FALLBACK_MODEL
    ]


    models = list(
        dict.fromkeys(models)
    )


    last_error = ""


    for model in models:

        for attempt in range(3):

            try:

                result =
                    call_gemini(
                        model,
                        message,
                        history
                    )


                answer =
                    extract_answer(
                        result
                    )


                return jsonify({

                    "reply":
                        answer,

                    "model":
                        model

                }), 200


            except urllib.error.HTTPError as error:

                try:

                    detail =
                        error.read().decode(
                            "utf-8",
                            errors="ignore"
                        )

                except Exception:

                    detail = ""


                last_error = (
                    f"{model}: HTTP "
                    f"{error.code} "
                    f"{detail[:500]}"
                )


                # Retry temporary errors.
                if error.code in (
                    429,
                    500,
                    502,
                    503,
                    504
                ):

                    time.sleep(
                        2 ** attempt
                    )

                    continue


                break


            except urllib.error.URLError as error:

                last_error = (
                    f"{model}: "
                    f"connection error: {error}"
                )

                time.sleep(
                    2 ** attempt
                )

                continue


            except Exception as error:

                last_error = (
                    f"{model}: "
                    f"{error}"
                )

                break


    return jsonify({

        "error":
            "Gemini ته د ځواب ترلاسه کولو کې ستونزه راغله. "
            "لږ وروسته بیا هڅه وکړئ."

    }), 503


# =========================================================
# CHAT ALIAS
# =========================================================

@app.post("/chat")
def chat_alias():

    return api_chat()


# =========================================================
# 404
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({

        "error":
            "Page not found."

    }), 404


# =========================================================
# LOCAL RUN
# =========================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(
            os.environ.get(
                "PORT",
                "5000"
            )
        ),

        debug=False

    )
