from flask import Flask, request, jsonify, render_template_string
import os
import json
import urllib.request
import urllib.error
import time

app = Flask(__name__)

# =========================================================
# GEMINI CONFIGURATION
# =========================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
).strip()

GEMINI_FALLBACK_MODEL = os.environ.get(
    "GEMINI_FALLBACK_MODEL",
    "gemini-3.8-flash"
).strip()

GEMINI_BASE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/{model}:generateContent"
)

# =========================================================
# MEDICAL SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are MedAI, an educational medical information assistant.

Developer: Toyebullah Dawoodzay.
Created in 2026.

IMPORTANT LANGUAGE RULE:
Answer in the SAME LANGUAGE as the user's question.

If the user asks in Pashto, answer in Pashto.
If the user asks in Dari, answer in Dari.
If the user asks in English, answer in English.
If the user asks in Urdu, answer in Urdu.
If the user asks in Arabic, answer in Arabic.

Use simple, clear, understandable language.

Provide educational medical information only.

SAFETY RULES:

- Do not diagnose a person from symptoms alone.
- Do not claim that you physically examined the patient.
- Do not invent medical facts.
- Do not provide personalized prescription instructions.
- Do not provide personalized medication dosing.
- Do not tell users to start, stop, or change prescription medicines.
- Explain that a qualified healthcare professional should make personal medical decisions.
- If emergency warning signs are present, advise urgent professional medical care.
- Do not replace a qualified healthcare professional.

For symptoms:
Explain possible general causes or categories,
but clearly state that symptoms alone cannot confirm a diagnosis.

For medicines:
Provide general educational information such as:
what the medicine is commonly used for,
general precautions,
common side effects,
and important safety considerations.

Do not provide personalized dose changes.

If asked who created you, say:

"زه MedAI یم، د Toyebullah Dawoodzay لخوا په ۲۰۲۶ کال کې جوړ شوی یم."

Always prioritize patient safety.
"""

# =========================================================
# CHATGPT STYLE MOBILE UI
# =========================================================

HTML = r"""
<!doctype html>
<html lang="ps" dir="rtl">

<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#ffffff">

<title>MedAI</title>

<style>

*{
    box-sizing:border-box;
}

:root{
    --bg:#ffffff;
    --panel:#f7f7f8;
    --text:#202123;
    --muted:#6b6f76;
    --border:#e5e5e5;
    --blue:#1677ff;
    --blue-dark:#0d5ed7;
    --user:#eef6ff;
    --danger:#d93025;
}

body.dark{
    --bg:#212121;
    --panel:#171717;
    --text:#ececec;
    --muted:#a0a0a0;
    --border:#383838;
    --user:#26384d;
}

html,
body{
    margin:0;
    padding:0;
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

/* ========================================================
   APP
======================================================== */

.app{
    width:100%;
    height:100vh;
    display:flex;
    background:var(--bg);
}

/* ========================================================
   SIDEBAR
======================================================== */

.sidebar{
    width:285px;
    height:100vh;
    background:var(--panel);
    border-left:1px solid var(--border);
    padding:12px;
    display:flex;
    flex-direction:column;
    position:fixed;
    right:0;
    top:0;
    z-index:30;
    transition:.25s ease;
}

.sidebar-header{
    display:flex;
    align-items:center;
    justify-content:space-between;
    margin-bottom:12px;
}

.logo-area{
    display:flex;
    align-items:center;
    gap:9px;
}

.logo{
    width:38px;
    height:38px;
    border-radius:11px;
    display:flex;
    align-items:center;
    justify-content:center;
    background:var(--blue);
    color:white;
    font-size:21px;
}

.logo-name{
    font-weight:700;
    font-size:18px;
}

.new-chat{
    width:100%;
    display:flex;
    align-items:center;
    justify-content:center;
    gap:8px;
    margin-bottom:12px;
    background:var(--blue);
}

.menu-title{
    color:var(--muted);
    font-size:12px;
    margin:13px 8px 7px;
}

.side-btn{
    width:100%;
    background:transparent;
    color:var(--text);
    text-align:right;
    padding:12px;
    border-radius:10px;
    display:flex;
    align-items:center;
    gap:10px;
    margin-bottom:3px;
}

.side-btn:hover{
    background:rgba(128,128,128,.12);
}

.sidebar-bottom{
    margin-top:auto;
    border-top:1px solid var(--border);
    padding-top:10px;
}

/* ========================================================
   MAIN
======================================================== */

.main{
    width:calc(100% - 285px);
    height:100vh;
    margin-right:285px;
    position:relative;
    display:flex;
    flex-direction:column;
}

/* ========================================================
   TOP BAR
======================================================== */

.topbar{
    height:58px;
    min-height:58px;
    border-bottom:1px solid var(--border);
    background:var(--bg);
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:0 18px;
    position:relative;
    z-index:10;
}

.top-left{
    display:flex;
    align-items:center;
    gap:9px;
}

.top-title{
    font-size:16px;
    font-weight:700;
}

.model{
    color:var(--muted);
    font-size:12px;
}

.icon-btn{
    width:39px;
    height:39px;
    padding:0;
    border-radius:10px;
    background:transparent;
    color:var(--text);
    border:1px solid transparent;
    font-size:19px;
}

.icon-btn:hover{
    background:var(--panel);
}

.mobile-menu{
    display:none;
}

/* ========================================================
   CHAT AREA
======================================================== */

.chat-area{
    flex:1;
    overflow-y:auto;
    padding:25px 18px 175px;
    scroll-behavior:smooth;
}

.chat-content{
    max-width:760px;
    margin:auto;
}

/* ========================================================
   WELCOME
======================================================== */

.welcome{
    min-height:55vh;
    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;
    padding:25px 10px;
}

.welcome-inner{
    width:100%;
}

.welcome-logo{
    width:64px;
    height:64px;
    border-radius:20px;
    background:var(--blue);
    color:white;
    margin:0 auto 17px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:34px;
    box-shadow:0 10px 30px rgba(22,119,255,.2);
}

.welcome h1{
    margin:0 0 10px;
    font-size:28px;
}

.welcome p{
    color:var(--muted);
    line-height:1.8;
    margin:0 auto 25px;
    max-width:560px;
}

.suggestions{
    display:grid;
    grid-template-columns:repeat(2,1fr);
    gap:9px;
    max-width:600px;
    margin:auto;
}

.suggestion{
    background:var(--bg);
    color:var(--text);
    border:1px solid var(--border);
    padding:13px 10px;
    border-radius:13px;
    text-align:right;
    cursor:pointer;
}

.suggestion:hover{
    border-color:var(--blue);
}

/* ========================================================
   MESSAGES
======================================================== */

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
    margin:8px 0;
}

.message.ai{
    background:transparent;
}

.avatar{
    min-width:32px;
    width:32px;
    height:32px;
    border-radius:9px;
    display:flex;
    align-items:center;
    justify-content:center;
    background:var(--blue);
    color:white;
    font-size:16px;
}

.user .avatar{
    background:#68707a;
}

.message-body{
    flex:1;
    min-width:0;
    white-space:pre-wrap;
    overflow-wrap:anywhere;
}

.message-actions{
    display:flex;
    gap:4px;
    margin-top:8px;
}

.message-action{
    background:transparent;
    color:var(--muted);
    padding:5px 8px;
    font-size:13px;
}

.message-action:hover{
    background:var(--panel);
}

/* ========================================================
   COMPOSER
======================================================== */

.composer-wrap{
    position:absolute;
    bottom:0;
    left:0;
    right:0;
    padding:16px 18px 18px;
    background:
        linear-gradient(
            transparent,
            var(--bg) 28%
        );
}

.composer{
    max-width:760px;
    margin:auto;
    border:1px solid var(--border);
    background:var(--bg);
    border-radius:18px;
    box-shadow:0 6px 28px rgba(0,0,0,.08);
    overflow:hidden;
}

.composer textarea{
    width:100%;
    min-height:58px;
    max-height:180px;
    border:0;
    outline:0;
    resize:none;
    padding:16px 16px 5px;
    background:transparent;
    color:var(--text);
    font-size:15px;
    line-height:1.7;
}

.composer textarea::placeholder{
    color:var(--muted);
}

.composer-bottom{
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:6px 8px 8px;
}

.composer-tools{
    display:flex;
    gap:4px;
}

.tool-btn{
    width:38px;
    height:38px;
    padding:0;
    border-radius:10px;
    background:transparent;
    color:var(--muted);
    font-size:18px;
}

.tool-btn:hover{
    background:var(--panel);
}

.send-btn{
    width:42px;
    height:42px;
    padding:0;
    border-radius:12px;
    background:var(--blue);
    color:white;
    font-size:18px;
}

.send-btn:hover{
    background:var(--blue-dark);
}

.send-btn:disabled{
    opacity:.45;
}

.disclaimer{
    max-width:760px;
    margin:7px auto 0;
    text-align:center;
    color:var(--muted);
    font-size:10px;
}

/* ========================================================
   STATUS
======================================================== */

.status{
    text-align:center;
    color:var(--muted);
    font-size:12px;
    margin:8px;
}

.loading{
    animation:pulse 1s infinite;
}

@keyframes pulse{
    50%{opacity:.35}
}

/* ========================================================
   MODAL
======================================================== */

.modal{
    display:none;
    position:fixed;
    inset:0;
    background:rgba(0,0,0,.55);
    z-index:100;
    padding:15px;
    overflow:auto;
}

.modal.show{
    display:block;
}

.modal-box{
    max-width:650px;
    margin:45px auto;
    background:var(--bg);
    color:var(--text);
    border-radius:18px;
    padding:18px;
    border:1px solid var(--border);
}

.modal-box h3{
    margin-top:0;
}

.modal-input,
.modal-box textarea,
.modal-box select{
    width:100%;
    padding:12px;
    border-radius:11px;
    border:1px solid var(--border);
    background:var(--panel);
    color:var(--text);
    outline:none;
    margin-bottom:9px;
}

.modal-row{
    display:flex;
    gap:8px;
    margin-top:8px;
}

.modal-row button{
    flex:1;
}

.pill{
    display:inline-block;
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:20px;
    padding:6px 10px;
    margin:3px;
    font-size:12px;
}

.small{
    color:var(--muted);
    font-size:12px;
    line-height:1.7;
}

.danger{
    background:#feeceb;
    color:var(--danger);
}

/* ========================================================
   MOBILE
======================================================== */

@media(max-width:760px){

    body{
        overflow:hidden;
    }

    .sidebar{
        width:290px;
        transform:translateX(100%);
        box-shadow:-15px 0 40px rgba(0,0,0,.16);
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

    .topbar{
        padding:0 10px;
    }

    .chat-area{
        padding:
            18px
            12px
            170px;
    }

    .chat-content{
        width:100%;
    }

    .welcome{
        min-height:58vh;
    }

    .welcome h1{
        font-size:25px;
    }

    .welcome-logo{
        width:58px;
        height:58px;
        font-size:29px;
    }

    .suggestions{
        grid-template-columns:1fr;
    }

    .message{
        padding:13px 1px;
    }

    .message.user{
        padding:12px;
    }

    .composer-wrap{
        padding:
            8px
            8px
            calc(8px + env(safe-area-inset-bottom));
    }

    .composer{
        border-radius:17px;
    }

    .composer textarea{
        min-height:52px;
        padding:14px 13px 4px;
    }

    .disclaimer{
        font-size:9px;
        padding:0 15px;
    }

    .top-title{
        font-size:15px;
    }

    .model{
        display:none;
    }
}

/* ========================================================
   EXTRA SMALL
======================================================== */

@media(max-width:380px){

    .suggestion{
        font-size:13px;
    }

    .avatar{
        min-width:29px;
        width:29px;
        height:29px;
    }

    .message{
        gap:8px;
    }

}

</style>
</head>

<body>

<div class="app">

<!-- =====================================================
     SIDEBAR
===================================================== -->

<aside class="sidebar" id="sidebar">

    <div class="sidebar-header">

        <div class="logo-area">

            <div class="logo">🩺</div>

            <div class="logo-name">
                MedAI
            </div>

        </div>

        <button
            class="icon-btn"
            onclick="closeSidebar()"
        >
            ✕
        </button>

    </div>

    <button
        class="new-chat"
        onclick="newChat()"
    >
        ＋ نوی چټ
    </button>

    <div class="menu-title">
        چټ او معلومات
    </div>

    <button
        class="side-btn"
        onclick="showHistory()"
    >
        🕘 تاریخچه
    </button>

    <button
        class="side-btn"
        onclick="showFavorites()"
    >
        ⭐ خوښې
    </button>

    <div class="menu-title">
        طبي وسایل
    </div>

    <button
        class="side-btn"
        onclick="askPreset('د دې نښو په اړه عمومي طبي معلومات راکړه: ')"
    >
        🩺 نښې
    </button>

    <button
        class="side-btn"
        onclick="askPreset('د دې درمل په اړه عمومي معلومات راکړه: ')"
    >
        💊 درمل
    </button>

    <button
        class="side-btn"
        onclick="askPreset('دا Lab Report په ساده ژبه تشریح کړه: ')"
    >
        🧪 لابراتوار
    </button>

    <button
        class="side-btn"
        onclick="askPreset('د First Aid مهم اصول راکړه.')"
    >
        🩹 لومړنۍ مرسته
    </button>

    <button
        class="side-btn"
        onclick="askPreset('د Emergency warning signs په اړه معلومات راکړه.')"
    >
        🚨 بیړنی حالت
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
        ⏰ درملو یادونه
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
            onclick="openModal('account')"
        >
            👤 حساب
        </button>

        <button
            class="side-btn"
            onclick="openModal('about')"
        >
            ℹ️ د MedAI په اړه
        </button>

    </div>

</aside>


<!-- =====================================================
     MAIN
===================================================== -->

<main class="main">

    <!-- TOP BAR -->

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
                    طبي معلوماتي مرستیال
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


    <!-- CHAT -->

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
                        له MedAI سره خبرې وکړئ
                    </h1>

                    <p>
                        ستاسې هوښیار طبي معلوماتي مرستیال.
                        خپله پوښتنه ولیکئ او د تعلیمي طبي معلوماتو
                        لپاره ځواب ترلاسه کړئ.
                    </p>


                    <div class="suggestions">

                        <button
                            class="suggestion"
                            onclick="askPreset('د شکر ناروغۍ په اړه مهم معلومات راکړه.')"
                        >
                            🩸 د شکر په اړه معلومات
                        </button>

                        <button
                            class="suggestion"
                            onclick="askPreset('د لوړ فشار په اړه عمومي معلومات راکړه.')"
                        >
                            ❤️ د فشار معلومات
                        </button>

                        <button
                            class="suggestion"
                            onclick="askPreset('د زړه د ناروغیو په اړه معلومات راکړه.')"
                        >
                            🫀 د زړه معلومات
                        </button>

                        <button
                            class="suggestion"
                            onclick="askPreset('د سالنډۍ یا Asthma په اړه معلومات راکړه.')"
                        >
                            🫁 د سالنډۍ معلومات
                        </button>

                    </div>

                </div>

            </div>

        </div>

    </section>


    <!-- COMPOSER -->

    <div class="composer-wrap">

        <div
            id="status"
            class="status"
        ></div>

        <div class="composer">

            <textarea
                id="question"
                rows="1"
                placeholder="له MedAI څخه پوښتنه وکړئ..."
            ></textarea>


            <div class="composer-bottom">

                <div class="composer-tools">

                    <button
                        class="tool-btn"
                        onclick="startVoice()"
                        title="Voice"
                    >
                        🎤
                    </button>

                    <button
                        class="tool-btn"
                        onclick="speakAnswer()"
                        title="Listen"
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
                    title="Send"
                >
                    ➤
                </button>

            </div>

        </div>


        <div class="disclaimer">

            MedAI یوازې تعلیمي طبي معلومات وړاندې کوي؛
            د ډاکټر بدیل نه دی.

        </div>

    </div>

</main>

</div>


<!-- =====================================================
     MODAL
===================================================== -->

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
   STORAGE
======================================================== */

let lastAnswer = "";

let historyList =
    JSON.parse(
        localStorage.getItem("medai_history") || "[]"
    );

let favorites =
    JSON.parse(
        localStorage.getItem("medai_favorites") || "[]"
    );

let reminders =
    JSON.parse(
        localStorage.getItem("medai_reminders") || "[]"
    );

let tracker =
    JSON.parse(
        localStorage.getItem("medai_tracker") || "[]"
    );


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
   NEW CHAT
======================================================== */

function newChat(){

    const chat =
        document.getElementById("chatContent");

    chat.innerHTML = `

        <div class="welcome" id="welcome">

            <div class="welcome-inner">

                <div class="welcome-logo">
                    🩺
                </div>

                <h1>
                    له MedAI سره خبرې وکړئ
                </h1>

                <p>
                    ستاسې هوښیار طبي معلوماتي مرستیال.
                    خپله پوښتنه ولیکئ.
                </p>

                <div class="suggestions">

                    <button
                        class="suggestion"
                        onclick="askPreset('د شکر ناروغۍ په اړه مهم معلومات راکړه.')"
                    >
                        🩸 د شکر په اړه معلومات
                    </button>

                    <button
                        class="suggestion"
                        onclick="askPreset('د لوړ فشار په اړه عمومي معلومات راکړه.')"
                    >
                        ❤️ د فشار معلومات
                    </button>

                    <button
                        class="suggestion"
                        onclick="askPreset('د زړه د ناروغیو په اړه معلومات راکړه.')"
                    >
                        🫀 د زړه معلومات
                    </button>

                    <button
                        class="suggestion"
                        onclick="askPreset('د سالنډۍ یا Asthma په اړه معلومات راکړه.')"
                    >
                        🫁 د سالنډۍ معلومات
                    </button>

                </div>

            </div>

        </div>
    `;

    lastAnswer = "";

    document.getElementById("question").value = "";

    document.getElementById("status").textContent = "";

    closeSidebar();

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
   ESCAPE HTML
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

    content.innerHTML += `

        <div class="message user">

            <div class="avatar">
                👤
            </div>

            <div class="message-body">
                ${escapeHtml(text)}
            </div>

        </div>

    `;

}


/* ========================================================
   ADD AI MESSAGE
======================================================== */

function addAIMessage(text){

    const content =
        document.getElementById("chatContent");

    const wrapper =
        document.createElement("div");

    wrapper.className = "message ai";

    wrapper.innerHTML = `

        <div class="avatar">
            🩺
        </div>

        <div class="message-body">

            <div class="ai-text"></div>

            <div class="message-actions">

                <button
                    class="message-action"
                    onclick="copyText(this)"
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
                    onclick="speakAnswer()"
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
   ASK PRESET
======================================================== */

function askPreset(text){

    document.getElementById("question").value = text;

    autoResize();

    askAI();

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

    addUserMessage(message);

    input.value = "";

    autoResize();

    button.disabled = true;

    status.innerHTML =
        '<span class="loading">MedAI فکر کوي...</span>';

    scrollToBottom();

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
                            message:message
                        })
                }
            );


        let data = {};

        try{

            data = await response.json();

        }catch{

            data = {};

        }


        if(!response.ok){

            throw new Error(
                data.error ||
                "API request failed."
            );

        }


        lastAnswer =
            data.reply ||
            "ځواب ترلاسه نه شو.";


        addAIMessage(lastAnswer);

        addHistory(
            message,
            lastAnswer
        );


        status.textContent =
            data.model
                ? "چمتو دی"
                : "";


        scrollToBottom();


    }catch(error){

        addAIMessage(
            "بخښنه، یوه ستونزه رامنځته شوه:\n" +
            error.message
        );

        status.textContent =
            "API Error";


        scrollToBottom();

    }finally{

        button.disabled = false;

    }

}


/* ========================================================
   SCROLL
======================================================== */

function scrollToBottom(){

    const area =
        document.getElementById("chatArea");

    setTimeout(
        function(){

            area.scrollTop =
                area.scrollHeight;

        },
        50
    );

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
            180
        ) + "px";

}

document
    .getElementById("question")
    .addEventListener(
        "input",
        autoResize
    );


/* ========================================================
   ENTER TO SEND
======================================================== */

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

function copyText(button){

    const message =
        button
            .closest(".message")
            .querySelector(".ai-text")
            .textContent;

    if(
        navigator.clipboard
    ){

        navigator.clipboard.writeText(message);

    }

}


/* ========================================================
   VOICE OUTPUT
======================================================== */

function speakAnswer(){

    if(
        lastAnswer &&
        "speechSynthesis" in window
    ){

        speechSynthesis.cancel();

        const speech =
            new SpeechSynthesisUtterance(
                lastAnswer
            );

        speech.lang = "ps-AF";

        speechSynthesis.speak(
            speech
        );

    }

}


/* ========================================================
   STOP VOICE
======================================================== */

function stopVoice(){

    if(
        "speechSynthesis" in window
    ){

        speechSynthesis.cancel();

    }

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

    recognition.lang = "ps-AF";

    recognition.interimResults = false;

    recognition.onresult =
        function(event){

            document.getElementById(
                "question"
            ).value =
                event.results[0][0].transcript;

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
            "لومړی یو AI ځواب ترلاسه کړئ."
        );

        return;

    }

    favorites.unshift(lastAnswer);

    favorites =
        favorites.slice(0,30);

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

function addHistory(q,a){

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


    /* ACCOUNT */

    if(type === "account"){

        const account =
            JSON.parse(
                localStorage.getItem(
                    "medai_account"
                ) || "{}"
            );

        html = `

            <h3>👤 حساب</h3>

            <p class="small">
                دا د محلي Demo حساب دی.
                معلومات یوازې په دې وسیله کې ساتل کېږي.
            </p>

            <input
                class="modal-input"
                id="name"
                placeholder="نوم"
                value="${escapeHtml(account.name || "")}"
            >

            <input
                class="modal-input"
                id="email"
                placeholder="Email"
                value="${escapeHtml(account.email || "")}"
            >

            <div class="modal-row">

                <button onclick="localAccount()">
                    Save
                </button>

                <button
                    class="secondary"
                    onclick="closeModal()"
                >
                    Close
                </button>

            </div>

            <div
                id="accountStatus"
                class="small"
            ></div>
        `;

    }


    /* HISTORY */

    if(type === "history"){

        html = `

            <h3>🕘 تاریخچه</h3>

            ${
                historyList.length
                ?
                historyList.map(
                    function(x){

                        return `

                            <div
                                class="message ai"
                                style="border-bottom:1px solid var(--border)"
                            >

                                <div class="avatar">
                                    🩺
                                </div>

                                <div class="message-body">

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

            <h3>⭐ خوښې</h3>

            ${
                favorites.length
                ?
                favorites.map(
                    function(x){

                        return `
                            <div class="message ai">
                                <div class="avatar">🩺</div>
                                <div class="message-body">
                                    ${escapeHtml(x)}
                                </div>
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

            <h3>📊 Health Tracker</h3>

            <input
                class="modal-input"
                id="metric"
                placeholder="مثلاً وزن 70kg"
            >

            <div class="modal-row">

                <button onclick="saveTracker()">
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
                    tracker.map(
                        function(x){

                            return `
                                <span class="pill">
                                    ${escapeHtml(x)}
                                </span>
                            `;

                        }
                    ).join("")
                }
            </div>
        `;

    }


    /* REMINDER */

    if(type === "reminder"){

        html = `

            <h3>⏰ Medication Reminder</h3>

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

                <button onclick="saveReminder()">
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
                }
            </div>
        `;

    }


    /* ABOUT */

    if(type === "about"){

        html = `

            <h3>ℹ️ د MedAI په اړه</h3>

            <p>
                MedAI یو تعلیمي طبي معلوماتي AI دی.
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
                MedAI د ډاکټر بدیل نه دی.
                د بیړني حالت پر مهال مسلکي طبي مرسته وغواړئ.
            </p>

            <button onclick="closeModal()">
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
   ACCOUNT
======================================================== */

function localAccount(){

    const name =
        document.getElementById("name").value.trim();

    const email =
        document.getElementById("email").value.trim();

    localStorage.setItem(
        "medai_account",
        JSON.stringify({
            name:name,
            email:email
        })
    );

    document.getElementById(
        "accountStatus"
    ).textContent =
        "حساب په دې وسیله کې خوندي شو.";

}


/* ========================================================
   TRACKER
======================================================== */

function saveTracker(){

    const value =
        document
            .getElementById("metric")
            .value
            .trim();

    if(!value){
        return;
    }

    tracker.unshift(
        new Date().toLocaleDateString()
        + " — "
        + value
    );

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

    const text =
        document
            .getElementById("reminderText")
            .value
            .trim();

    const time =
        document
            .getElementById("reminderTime")
            .value;

    if(!text || !time){
        return;
    }

    reminders.unshift({
        text:text,
        time:time
    });

    localStorage.setItem(
        "medai_reminders",
        JSON.stringify(reminders)
    );

    alert(
        "یادونه خوندي شوه."
    );

    openModal("reminder");

}


/* ========================================================
   MODAL OUTSIDE CLICK
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
   CLOSE SIDEBAR ON OUTSIDE MOBILE
======================================================== */

document.addEventListener(
    "click",
    function(event){

        const sidebar =
            document.getElementById("sidebar");

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


/* ========================================================
   ESC KEY
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

</script>

</body>
</html>
"""


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template_string(HTML)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return jsonify({

        "status":"ok",

        "primary_model":
            GEMINI_MODEL,

        "fallback_model":
            GEMINI_FALLBACK_MODEL,

        "api_key_configured":
            bool(GEMINI_API_KEY)

    })


# =========================================================
# GEMINI CHAT API
# =========================================================

@app.route(
    "/api/chat",
    methods=["POST"]
)
def chat():

    if not GEMINI_API_KEY:

        return jsonify({

            "error":
                "GEMINI_API_KEY په Vercel کې نه دی تنظیم شوی."

        }), 500


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

            "error":
                "مهرباني وکړئ خپله پوښتنه ولیکئ."

        }), 400


    models = [
        GEMINI_MODEL,
        GEMINI_FALLBACK_MODEL
    ]


    models = list(
        dict.fromkeys(models)
    )


    last_error = None


    for model in models:

        url = GEMINI_BASE_URL.format(
            model=model
        )


        payload = {

            "contents":[

                {

                    "role":"user",

                    "parts":[

                        {

                            "text":
                                SYSTEM_PROMPT
                                +
                                "\n\nUSER QUESTION:\n"
                                +
                                message

                        }

                    ]

                }

            ],

            "generationConfig":{

                "temperature":0.3,

                "maxOutputTokens":1200

            }

        }


        body = json.dumps(
            payload
        ).encode("utf-8")


        for attempt in range(3):

            req = urllib.request.Request(

                url,

                data=body,

                headers={

                    "Content-Type":
                        "application/json",

                    "x-goog-api-key":
                        GEMINI_API_KEY

                },

                method="POST"

            )


            try:

                with urllib.request.urlopen(
                    req,
                    timeout=45
                ) as response:

                    result = json.loads(
                        response
                            .read()
                            .decode("utf-8")
                    )


                candidates = result.get(
                    "candidates",
                    []
                )


                if not candidates:

                    last_error = (
                        f"{model}: "
                        "Gemini returned no candidates."
                    )

                    break


                content = candidates[0].get(
                    "content",
                    {}
                )


                parts = content.get(
                    "parts",
                    []
                )


                text = "".join(

                    part.get(
                        "text",
                        ""
                    )

                    for part in parts

                    if isinstance(
                        part,
                        dict
                    )

                ).strip()


                if text:

                    return jsonify({

                        "reply":
                            text,

                        "model":
                            model

                    }), 200


                last_error = (
                    f"{model}: "
                    "Gemini returned empty response."
                )

                break


            except urllib.error.HTTPError as error:

                detail = error.read().decode(
                    "utf-8",
                    errors="ignore"
                )


                last_error = (
                    f"{model}: "
                    f"HTTP {error.code} — "
                    f"{detail}"
                )


                retryable = error.code in (
                    429,
                    500,
                    502,
                    503,
                    504
                )


                if retryable:

                    time.sleep(
                        2 ** attempt
                    )

                    continue


                break


            except urllib.error.URLError as error:

                last_error = (
                    f"{model}: "
                    "connection error — "
                    f"{error}"
                )

                time.sleep(
                    2 ** attempt
                )

                continue


            except Exception as error:

                last_error = (
                    f"{model}: "
                    f"{str(error)}"
                )

                break


    return jsonify({

        "error":
            "Gemini اوس مهال مصروف دی. "
            "سیستم څو ځله هڅه وکړه، "
            "خو ځواب ترلاسه نه شو. "
            "مهرباني وکړئ څو شېبې وروسته بیا هڅه وکړئ."

    }), 503


# =========================================================
# CHAT ALIAS
# =========================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat_alias():

    return chat()


# =========================================================
# LOCAL DEVELOPMENT
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
