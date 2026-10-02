from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# ============================================================
# CONFIG
# ============================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# خپل Gemini model دلته ساتلی شو
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-3.5-flash-lite:generateContent"
)

WIKIMEDIA_URL = "https://commons.wikimedia.org/w/api.php"


# ============================================================
# GEMINI
# ============================================================

def ask_gemini(prompt):
    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY نه دی تنظیم شوی."

    try:
        response = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
            timeout=60
        )

        if response.status_code != 200:
            return "د AI سره د اړیکې پر مهال ستونزه رامنځته شوه."

        data = response.json()

        candidates = data.get("candidates", [])

        if not candidates:
            return "AI ځواب ورنه کړ."

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        for part in parts:
            if part.get("text"):
                return part["text"]

        return "AI ځواب ورنه کړ."

    except requests.exceptions.Timeout:
        return "د AI ځواب ډېر وخت ونیو. بیا هڅه وکړئ."

    except Exception:
        return "د AI سره د اړیکې پر مهال ستونزه رامنځته شوه."


# ============================================================
# MEDAI PROMPT
# ============================================================

def build_prompt(instruction, user_text):

    return f"""
You are MedAI, an educational medical information assistant.

Developer:
Toyebullah Dawoodzay

Created:
2026

IMPORTANT RULES:

- Answer in the SAME LANGUAGE as the user's question.
- If the user writes Pashto, answer in Pashto.
- Use simple and clear language.
- Provide educational medical information only.
- Do not diagnose from symptoms alone.
- Do not claim to physically examine the patient.
- Do not invent medical facts.
- Do not provide personalized prescription dosing.
- Do not tell users to start, stop, or change prescription medicines.
- If emergency warning signs are present, advise urgent professional medical care.
- Do not replace a qualified healthcare professional.
- Clearly mention uncertainty when information is incomplete.
- Do not create fake laboratory reference ranges.
- Do not create fake medical scores.
- Do not assume missing patient information.

If asked who created you, say:

"زه MedAI یم، د Toyebullah Dawoodzay لخوا په ۲۰۲۶ کال کې جوړ شوی یم."

TASK:

{instruction}

USER INFORMATION:

{user_text}
"""


# ============================================================
# WIKIMEDIA MEDICAL IMAGES
# ============================================================

def get_medical_images(query):

    try:

        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query + " medical",
            "gsrnamespace": 6,
            "gsrlimit": 8,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 700
        }

        response = requests.get(
            WIKIMEDIA_URL,
            params=params,
            headers={
                "User-Agent": "MedAI/1.0"
            },
            timeout=20
        )

        if response.status_code != 200:
            return []

        data = response.json()

        pages = data.get("query", {}).get("pages", {})

        images = []

        for page in pages.values():

            image_info = page.get("imageinfo", [])

            if image_info:

                info = image_info[0]

                url = (
                    info.get("thumburl")
                    or info.get("url")
                )

                if url:

                    images.append(
                        {
                            "url": url,
                            "title": page.get(
                                "title",
                                "Medical Image"
                            )
                        }
                    )

        return images

    except Exception:
        return []


# ============================================================
# HTML
# ============================================================

HTML = r"""
<!DOCTYPE html>

<html lang="ps" dir="rtl">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width,
               initial-scale=1.0,
               maximum-scale=1.0,
               user-scalable=no">

<meta name="theme-color" content="#0b7fab">

<title>MedAI</title>


<style>

/* =========================================================
   VARIABLES
========================================================= */

:root {

    --bg: #ffffff;
    --sidebar: #f7f7f8;
    --card: #ffffff;
    --input: #f7f7f8;

    --text: #1f2937;
    --muted: #6b7280;

    --border: #e5e7eb;

    --primary: #087fba;
    --primary-dark: #075985;

    --danger: #dc2626;
    --success: #059669;

    --shadow: 0 8px 30px rgba(0,0,0,.08);
}


/* DARK */

body.dark {

    --bg: #212121;
    --sidebar: #171717;
    --card: #212121;
    --input: #2f2f2f;

    --text: #ececec;
    --muted: #a3a3a3;

    --border: #3f3f3f;

    --primary: #19a7d8;
    --primary-dark: #0b7fab;
}


/* =========================================================
   GLOBAL
========================================================= */

* {
    box-sizing: border-box;
}

html,
body {

    margin: 0;
    padding: 0;

    width: 100%;
    height: 100%;

    font-family:
        Arial,
        Tahoma,
        sans-serif;

    background: var(--bg);
    color: var(--text);
}


button,
input,
textarea,
select {

    font-family: inherit;
}


button {

    cursor: pointer;
}


/* =========================================================
   APP
========================================================= */

.app {

    display: flex;

    width: 100%;
    height: 100vh;

    overflow: hidden;
}


/* =========================================================
   SIDEBAR
========================================================= */

.sidebar {

    width: 290px;

    background: var(--sidebar);

    border-left: 1px solid var(--border);

    display: flex;

    flex-direction: column;

    position: fixed;

    right: 0;
    top: 0;
    bottom: 0;

    z-index: 100;

    transform: translateX(100%);

    transition: .25s ease;
}


.sidebar.open {

    transform: translateX(0);
}


/* sidebar header */

.sidebar-header {

    height: 64px;

    padding: 12px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    border-bottom: 1px solid var(--border);
}


.sidebar-brand {

    display: flex;

    align-items: center;

    gap: 10px;

    font-weight: bold;

    font-size: 18px;
}


.brand-icon {

    width: 38px;
    height: 38px;

    border-radius: 12px;

    display: grid;

    place-items: center;

    background: var(--primary);

    color: white;

    font-size: 21px;
}


.close-sidebar {

    border: 0;

    background: transparent;

    color: var(--text);

    font-size: 22px;

    width: 40px;
    height: 40px;

    border-radius: 10px;
}


.close-sidebar:hover {

    background: var(--border);
}


/* sidebar body */

.sidebar-body {

    flex: 1;

    overflow-y: auto;

    padding: 10px;
}


/* new chat */

.new-chat {

    width: 100%;

    border: 1px solid var(--border);

    background: var(--card);

    color: var(--text);

    border-radius: 12px;

    padding: 12px;

    text-align: right;

    font-size: 15px;

    margin-bottom: 12px;
}


.new-chat:hover {

    background: var(--input);
}


/* menu section */

.menu-title {

    color: var(--muted);

    font-size: 12px;

    font-weight: bold;

    padding: 12px 10px 7px;
}


/* feature button */

.menu-item {

    width: 100%;

    display: flex;

    align-items: center;

    gap: 10px;

    border: 0;

    background: transparent;

    color: var(--text);

    padding: 10px;

    border-radius: 10px;

    text-align: right;

    font-size: 14px;

    margin-bottom: 2px;
}


.menu-item:hover {

    background: var(--border);
}


.menu-icon {

    width: 28px;

    text-align: center;

    font-size: 17px;
}


/* sidebar footer */

.sidebar-footer {

    border-top: 1px solid var(--border);

    padding: 10px;
}


/* =========================================================
   MAIN
========================================================= */

.main {

    width: 100%;
    height: 100vh;

    display: flex;

    flex-direction: column;

    background: var(--bg);
}


/* =========================================================
   TOP BAR
========================================================= */

.topbar {

    height: 64px;

    border-bottom: 1px solid var(--border);

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding: 0 15px;

    background: var(--bg);

    flex-shrink: 0;
}


.top-left {

    display: flex;

    align-items: center;

    gap: 10px;
}


.menu-button {

    width: 42px;
    height: 42px;

    border: 0;

    border-radius: 10px;

    background: transparent;

    color: var(--text);

    font-size: 23px;
}


.menu-button:hover {

    background: var(--border);
}


.top-title {

    font-size: 18px;

    font-weight: bold;
}


.top-actions {

    display: flex;

    gap: 5px;
}


.icon-button {

    width: 40px;
    height: 40px;

    border: 0;

    background: transparent;

    color: var(--text);

    border-radius: 10px;

    font-size: 18px;
}


.icon-button:hover {

    background: var(--border);
}


/* =========================================================
   CHAT AREA
========================================================= */

.chat-area {

    flex: 1;

    overflow-y: auto;

    padding: 25px 15px 150px;
}


.chat-inner {

    max-width: 850px;

    margin: auto;
}


/* welcome */

.welcome {

    min-height: 55vh;

    display: flex;

    align-items: center;

    justify-content: center;

    text-align: center;

    flex-direction: column;
}


.welcome-icon {

    width: 70px;
    height: 70px;

    border-radius: 22px;

    background: var(--primary);

    color: white;

    display: grid;

    place-items: center;

    font-size: 36px;

    margin-bottom: 18px;

    box-shadow:
        0 10px 35px rgba(8,127,186,.25);
}


.welcome h1 {

    margin: 0 0 10px;

    font-size: 30px;
}


.welcome p {

    margin: 0;

    color: var(--muted);

    max-width: 500px;

    line-height: 1.8;
}


/* messages */

.message {

    margin: 20px 0;

    display: flex;

    gap: 12px;

    align-items: flex-start;
}


.message.user {

    justify-content: flex-start;
}


.message.ai {

    justify-content: flex-start;
}


.avatar {

    min-width: 36px;
    width: 36px;
    height: 36px;

    border-radius: 11px;

    display: grid;

    place-items: center;

    font-size: 18px;

    background: var(--primary);

    color: white;
}


.user .avatar {

    background: #64748b;
}


.message-content {

    max-width: 85%;

    line-height: 1.9;

    white-space: pre-wrap;

    font-size: 15px;
}


.user .message-content {

    background: var(--input);

    padding: 10px 14px;

    border-radius: 16px;

    border-top-right-radius: 5px;
}


.ai .message-content {

    padding: 5px 0;
}


/* =========================================================
   QUICK TOOLS
========================================================= */

.quick-tools {

    display: flex;

    gap: 8px;

    overflow-x: auto;

    padding: 10px 0;

    scrollbar-width: none;
}


.quick-tools::-webkit-scrollbar {

    display: none;
}


.quick-tool {

    flex-shrink: 0;

    border: 1px solid var(--border);

    background: var(--card);

    color: var(--text);

    border-radius: 20px;

    padding: 8px 13px;

    font-size: 13px;
}


.quick-tool:hover {

    border-color: var(--primary);

    color: var(--primary);
}


/* =========================================================
   CHAT INPUT
========================================================= */

.input-area {

    position: fixed;

    bottom: 0;

    left: 0;
    right: 0;

    background: linear-gradient(
        transparent,
        var(--bg) 28%
    );

    padding: 20px 12px 12px;

    z-index: 50;
}


.input-inner {

    max-width: 850px;

    margin: auto;
}


.chat-box {

    display: flex;

    align-items: flex-end;

    gap: 7px;

    background: var(--input);

    border: 1px solid var(--border);

    border-radius: 24px;

    padding: 7px;

    box-shadow: var(--shadow);
}


.chat-box textarea {

    flex: 1;

    border: 0;

    outline: 0;

    resize: none;

    background: transparent;

    color: var(--text);

    min-height: 42px;

    max-height: 150px;

    padding: 10px;

    font-size: 15px;
}


.chat-action {

    width: 42px;
    height: 42px;

    flex-shrink: 0;

    border: 0;

    border-radius: 50%;

    background: transparent;

    color: var(--text);

    font-size: 18px;
}


.chat-action:hover {

    background: var(--border);
}


.send-button {

    background: var(--primary);

    color: white;
}


.send-button:hover {

    filter: brightness(1.08);

    background: var(--primary);
}


.disclaimer {

    text-align: center;

    color: var(--muted);

    font-size: 10px;

    padding-top: 7px;
}


/* =========================================================
   TOOL PANEL
========================================================= */

.overlay {

    display: none;

    position: fixed;

    inset: 0;

    background: rgba(0,0,0,.4);

    z-index: 90;
}


.overlay.show {

    display: block;
}


.tool-panel {

    position: fixed;

    z-index: 120;

    inset: 0;

    background: var(--bg);

    overflow-y: auto;

    display: none;
}


.tool-panel.show {

    display: block;
}


.panel-header {

    height: 64px;

    position: sticky;

    top: 0;

    background: var(--bg);

    border-bottom: 1px solid var(--border);

    display: flex;

    align-items: center;

    gap: 12px;

    padding: 0 15px;

    z-index: 5;
}


.panel-header h2 {

    margin: 0;

    font-size: 18px;
}


.back-button {

    width: 42px;
    height: 42px;

    border: 0;

    background: transparent;

    color: var(--text);

    font-size: 23px;

    border-radius: 10px;
}


.panel-body {

    max-width: 800px;

    margin: auto;

    padding: 20px 14px 60px;
}


/* =========================================================
   FORM
========================================================= */

.field {

    margin-bottom: 12px;
}


.field label {

    display: block;

    font-size: 13px;

    color: var(--muted);

    margin-bottom: 5px;
}


input,
textarea,
select {

    width: 100%;

    padding: 12px;

    border-radius: 12px;

    border: 1px solid var(--border);

    background: var(--input);

    color: var(--text);

    outline: none;

    font-size: 15px;
}


textarea {

    min-height: 120px;

    resize: vertical;
}


input:focus,
textarea:focus,
select:focus {

    border-color: var(--primary);

    box-shadow:
        0 0 0 3px rgba(8,127,186,.12);
}


.primary-button {

    width: 100%;

    padding: 13px;

    border: 0;

    border-radius: 12px;

    background: var(--primary);

    color: white;

    font-size: 15px;

    font-weight: bold;
}


.primary-button:hover {

    filter: brightness(1.05);
}


.danger-button {

    width: 100%;

    padding: 12px;

    border: 0;

    border-radius: 12px;

    background: var(--danger);

    color: white;

    font-weight: bold;
}


/* result */

.result {

    margin-top: 15px;

    padding: 15px;

    background: var(--input);

    border-radius: 14px;

    line-height: 1.9;

    white-space: pre-wrap;

    min-height: 20px;
}


/* =========================================================
   IMAGES
========================================================= */

.image-grid {

    display: grid;

    grid-template-columns:
        repeat(2, 1fr);

    gap: 10px;

    margin-top: 15px;
}


.image-card {

    background: var(--card);

    border: 1px solid var(--border);

    border-radius: 14px;

    overflow: hidden;
}


.image-card img {

    width: 100%;

    height: 180px;

    object-fit: cover;

    display: block;
}


.image-title {

    padding: 8px;

    font-size: 11px;

    color: var(--muted);
}


/* =========================================================
   LIST
========================================================= */

.list-item {

    background: var(--input);

    border: 1px solid var(--border);

    border-radius: 13px;

    padding: 12px;

    margin-bottom: 8px;
}


.list-item strong {

    display: block;

    margin-bottom: 4px;
}


.list-item small {

    color: var(--muted);
}


/* =========================================================
   LOADING
========================================================= */

.loading {

    display: none;

    text-align: center;

    color: var(--primary);

    padding: 12px;
}


.loading.show {

    display: block;
}


/* =========================================================
   RESPONSIVE
========================================================= */

@media (min-width: 900px) {

    .sidebar {

        position: relative;

        transform: translateX(0);

        right: auto;

        border-left: 0;

        border-right: 1px solid var(--border);
    }

    .close-sidebar {

        display: none;
    }

    .menu-button {

        display: none;
    }

    .main {

        margin-right: 0;
    }

}


@media (max-width: 600px) {

    .sidebar {

        width: 88%;

        max-width: 330px;
    }

    .welcome h1 {

        font-size: 25px;
    }

    .welcome {

        min-height: 48vh;
    }

    .message-content {

        max-width: 88%;
    }

    .image-grid {

        grid-template-columns: 1fr 1fr;
    }

}


/* =========================================================
   RTL
========================================================= */

html[dir="rtl"] .sidebar {

    right: 0;
    left: auto;
}


html[dir="rtl"] .user {

    justify-content: flex-start;
}


</style>

</head>


<body>


<div class="app">


<!-- =====================================================
     SIDEBAR
===================================================== -->

<aside id="sidebar" class="sidebar">

    <div class="sidebar-header">

        <div class="sidebar-brand">

            <div class="brand-icon">
                🩺
            </div>

            <span>MedAI</span>

        </div>

        <button
            class="close-sidebar"
            onclick="closeSidebar()">

            ✕

        </button>

    </div>


    <div class="sidebar-body">


        <button
            class="new-chat"
            onclick="newChat()">

            ＋ نوی Chat

        </button>


        <div class="menu-title">
            اصلي
        </div>


        <button
            class="menu-item"
            onclick="closeSidebar()">

            <span class="menu-icon">💬</span>

            <span>New Chat</span>

        </button>


        <!-- =================================================
             MEDICAL FEATURES
        ================================================== -->

        <div class="menu-title">
            طبي Features
        </div>


        <button class="menu-item"
                onclick="openTool('symptoms')">
            <span class="menu-icon">🧠</span>
            <span>Symptom Education</span>
        </button>


        <button class="menu-item"
                onclick="openTool('vitals')">
            <span class="menu-icon">❤️</span>
            <span>Vital Signs Guide</span>
        </button>


        <button class="menu-item"
                onclick="openTool('compare')">
            <span class="menu-icon">⚖️</span>
            <span>Disease Comparison</span>
        </button>


        <button class="menu-item"
                onclick="openTool('doctor')">
            <span class="menu-icon">👨‍⚕️</span>
            <span>Doctor Visit Assistant</span>
        </button>


        <button class="menu-item"
                onclick="openTool('lab')">
            <span class="menu-icon">🧪</span>
            <span>Lab Report Explainer</span>
        </button>


        <button class="menu-item"
                onclick="openTool('medicine')">
            <span class="menu-icon">💊</span>
            <span>Medicine Information</span>
        </button>


        <button class="menu-item"
                onclick="openTool('dictionary')">
            <span class="menu-icon">📖</span>
            <span>Medical Dictionary</span>
        </button>


        <button class="menu-item"
                onclick="openTool('emergency')">
            <span class="menu-icon">🚨</span>
            <span>Emergency Checker</span>
        </button>


        <button class="menu-item"
                onclick="openTool('images')">
            <span class="menu-icon">🖼️</span>
            <span>Medical Images</span>
        </button>


        <button class="menu-item"
                onclick="openTool('interaction')">
            <span class="menu-icon">💊</span>
            <span>Medicine Interaction</span>
        </button>


        <button class="menu-item"
                onclick="openTool('report')">
            <span class="menu-icon">📋</span>
            <span>Medical Report Explainer</span>
        </button>


        <button class="menu-item"
                onclick="openTool('firstaid')">
            <span class="menu-icon">🩹</span>
            <span>First Aid Guide</span>
        </button>


        <button class="menu-item"
                onclick="openTool('glossary')">
            <span class="menu-icon">📚</span>
            <span>Medical Glossary</span>
        </button>


        <button class="menu-item"
                onclick="openTool('risk')">
            <span class="menu-icon">🧠</span>
            <span>Medical Risk Assessment</span>
        </button>


        <button class="menu-item"
                onclick="openTool('quiz')">
            <span class="menu-icon">📝</span>
            <span>Medical Quiz</span>
        </button>


        <button class="menu-item"
                onclick="openTool('healthreport')">
            <span class="menu-icon">📊</span>
            <span>Health Report Generator</span>
        </button>


        <!-- =================================================
             HEALTH
        ================================================== -->

        <div class="menu-title">
            Health
        </div>


        <button class="menu-item"
                onclick="openTool('tracker')">

            <span class="menu-icon">📈</span>

            <span>Health Tracker</span>

        </button>


        <button class="menu-item"
                onclick="openTool('reminder')">

            <span class="menu-icon">⏰</span>

            <span>Medication Reminder</span>

        </button>


        <!-- =================================================
             PERSONAL
        ================================================== -->

        <div class="menu-title">
            Personal
        </div>


        <button class="menu-item"
                onclick="openTool('history')">

            <span class="menu-icon">🕘</span>

            <span>History</span>

        </button>


        <button class="menu-item"
                onclick="openTool('favorites')">

            <span class="menu-icon">⭐</span>

            <span>Favorites</span>

        </button>


    </div>


    <div class="sidebar-footer">


        <button
            class="menu-item"
            onclick="toggleDark()">

            <span class="menu-icon">🌙</span>

            <span>Dark / Light Mode</span>

        </button>


        <button
            class="menu-item"
            onclick="openTool('about')">

            <span class="menu-icon">ℹ️</span>

            <span>About MedAI</span>

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
                class="menu-button"
                onclick="openSidebar()">

                ☰

            </button>


            <div class="top-title">
                MedAI
            </div>


        </div>


        <div class="top-actions">


            <button
                class="icon-button"
                onclick="startVoice()"
                title="Voice">

                🎤

            </button>


            <button
                class="icon-button"
                onclick="toggleDark()"
                title="Dark Mode">

                🌙

            </button>


        </div>


    </header>



    <!-- =================================================
         CHAT AREA
    ================================================== -->

    <section
        id="chatArea"
        class="chat-area">


        <div
            id="chatInner"
            class="chat-inner">


            <!-- WELCOME -->

            <div
                id="welcome"
                class="welcome">


                <div class="welcome-icon">
                    🩺
                </div>


                <h1>
                    MedAI ته ښه راغلاست
                </h1>


                <p>
                    زه ستا د طبي معلوماتو هوښیار مرستیال یم.
                    خپله پوښتنه ولیکه او یا له Menu څخه کوم طبي Tool انتخاب کړه.
                </p>


            </div>


        </div>

    </section>



    <!-- =================================================
         INPUT
    ================================================== -->

    <div class="input-area">


        <div class="input-inner">


            <div class="quick-tools">


                <button
                    class="quick-tool"
                    onclick="openTool('symptoms')">

                    🧠 نښې

                </button>


                <button
                    class="quick-tool"
                    onclick="openTool('medicine')">

                    💊 درمل

                </button>


                <button
                    class="quick-tool"
                    onclick="openTool('lab')">

                    🧪 Lab

                </button>


                <button
                    class="quick-tool"
                    onclick="openTool('vitals')">

                    ❤️ Vital

                </button>


                <button
                    class="quick-tool"
                    onclick="openTool('emergency')">

                    🚨 Emergency

                </button>


                <button
                    class="quick-tool"
                    onclick="openTool('firstaid')">

                    🩹 First Aid

                </button>


            </div>


            <div class="chat-box">


                <button
                    class="chat-action"
                    onclick="startVoice()"
                    title="Voice">

                    🎤

                </button>


                <textarea
                    id="question"
                    rows="1"
                    placeholder="خپله طبي پوښتنه ولیکئ..."
                    onkeydown="handleEnter(event)"></textarea>


                <button
                    class="chat-action send-button"
                    onclick="askAI()">

                    ↑

                </button>


            </div>


            <div class="disclaimer">

                MedAI تعلیمي طبي معلومات وړاندې کوي؛ د ډاکټر بدیل نه دی.

            </div>


        </div>

    </div>


</main>


</div>



<!-- =====================================================
     OVERLAY
===================================================== -->

<div
    id="overlay"
    class="overlay"
    onclick="closeSidebar()">
</div>



<!-- =====================================================
     TOOL PANEL
===================================================== -->

<section
    id="toolPanel"
    class="tool-panel">


    <div class="panel-header">


        <button
            class="back-button"
            onclick="closeTool()">

            ←

        </button>


        <h2 id="panelTitle">
            MedAI Tool
        </h2>


    </div>


    <div
        id="panelBody"
        class="panel-body">
    </div>


</section>



<script>

/* =========================================================
   GLOBAL
========================================================= */

let currentAnswer = "";

let recognition = null;


/* =========================================================
   HELPERS
========================================================= */

function $(id) {

    return document.getElementById(id);

}


function escapeHTML(text) {

    const div = document.createElement("div");

    div.textContent = text;

    return div.innerHTML;

}


function showLoading(id) {

    const el = $(id);

    if (el) {

        el.classList.add("show");

    }

}


function hideLoading(id) {

    const el = $(id);

    if (el) {

        el.classList.remove("show");

    }

}


/* =========================================================
   SIDEBAR
========================================================= */

function openSidebar() {

    $("sidebar").classList.add("open");

    $("overlay").classList.add("show");

}


function closeSidebar() {

    $("sidebar").classList.remove("open");

    $("overlay").classList.remove("show");

}


/* =========================================================
   DARK MODE
========================================================= */

function toggleDark() {

    document.body.classList.toggle("dark");

    localStorage.setItem(
        "medai_dark",
        document.body.classList.contains("dark")
    );

}


if (
    localStorage.getItem("medai_dark") === "true"
) {

    document.body.classList.add("dark");

}


/* =========================================================
   NEW CHAT
========================================================= */

function newChat() {

    $("chatInner").innerHTML = `

        <div id="welcome" class="welcome">

            <div class="welcome-icon">
                🩺
            </div>

            <h1>
                MedAI ته ښه راغلاست
            </h1>

            <p>
                خپله طبي پوښتنه ولیکئ.
            </p>

        </div>

    `;

    $("question").value = "";

    closeSidebar();

}


/* =========================================================
   ENTER
========================================================= */

function handleEnter(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        askAI();

    }

}


/* =========================================================
   CHAT MESSAGE
========================================================= */

function addMessage(type, text) {

    const welcome = $("welcome");

    if (welcome) {

        welcome.remove();

    }


    const message = document.createElement("div");

    message.className =
        "message " + type;


    const avatar =
        type === "user"
            ? "👤"
            : "🩺";


    message.innerHTML = `

        <div class="avatar">
            ${avatar}
        </div>

        <div class="message-content">
            ${escapeHTML(text)}
        </div>

    `;


    $("chatInner").appendChild(message);


    $("chatArea").scrollTop =
        $("chatArea").scrollHeight;

}


/* =========================================================
   MAIN CHAT
========================================================= */

async function askAI() {

    const input = $("question");

    const question =
        input.value.trim();


    if (!question) {

        return;

    }


    addMessage(
        "user",
        question
    );


    input.value = "";


    const loading =
        document.createElement("div");


    loading.className =
        "message ai";


    loading.innerHTML = `

        <div class="avatar">
            🩺
        </div>

        <div class="message-content">
            AI کار کوي...
        </div>

    `;


    $("chatInner")
        .appendChild(loading);


    $("chatArea").scrollTop =
        $("chatArea").scrollHeight;


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
                            question:
                                question
                        })
                }
            );


        const data =
            await response.json();


        loading.remove();


        const answer =
            data.answer ||
            data.error ||
            "ځواب ترلاسه نه شو.";


        currentAnswer =
            answer;


        addMessage(
            "ai",
            answer
        );


        saveHistory(
            question,
            answer
        );


    }

    catch (error) {

        loading.remove();

        addMessage(
            "ai",
            "د سرور سره د اړیکې ستونزه."
        );

    }

}


/* =========================================================
   SPECIAL API
========================================================= */

async function specialRequest(
    endpoint,
    text,
    resultElement
) {

    if (!text.trim()) {

        $(resultElement).textContent =
            "مهرباني وکړئ معلومات ولیکئ.";

        return;

    }


    $(resultElement).textContent =
        "AI کار کوي...";


    try {

        const response =
            await fetch(
                endpoint,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            text:
                                text
                        })
                }
            );


        const data =
            await response.json();


        $(resultElement).textContent =
            data.answer ||
            data.error ||
            "ځواب ترلاسه نه شو.";

    }

    catch (error) {

        $(resultElement).textContent =
            "د سرور سره د اړیکې ستونزه.";

    }

}


/* =========================================================
   TOOL PANEL
========================================================= */

function openTool(tool) {

    closeSidebar();

    const panel =
        $("toolPanel");

    const title =
        $("panelTitle");

    const body =
        $("panelBody");


    panel.classList.add("show");


    /* -----------------------------------------------------
       SYMPTOMS
    ----------------------------------------------------- */

    if (tool === "symptoms") {

        title.textContent =
            "🧠 Symptom Education";


        body.innerHTML = `

            <div class="field">

                <label>
                    خپلې نښې ولیکئ
                </label>

                <textarea
                    id="toolInput"
                    placeholder="لکه: تبه، ټوخی، ستړیا..."></textarea>

            </div>


            <button
                class="primary-button"
                onclick="runTool('/symptoms')">

                🧠 نښې تشریح کړه

            </button>


            <div
                id="toolResult"
                class="result"></div>

        `;

    }


    /* -----------------------------------------------------
       VITALS
    ----------------------------------------------------- */

    else if (tool === "vitals") {

        title.textContent =
            "❤️ Vital Signs";


        body.innerHTML = `

            <div class="field">

                <label>
                    Vital Signs معلومات
                </label>

                <textarea
                    id="toolInput"
                    placeholder="Blood Pressure: 140/90
Pulse: 85
Temperature: 37.5
Oxygen: 96"></textarea>

            </div>


            <button
                class="primary-button"
                onclick="runTool('/vitals')">

                ❤️ تشریح کړه

            </button>


            <div
                id="toolResult"
                class="result"></div>

        `;

    }


    /* -----------------------------------------------------
       DOCTOR
    ----------------------------------------------------- */

    else if (tool === "doctor") {

        title.textContent =
            "👨‍⚕️ Doctor Visit Assistant";


        body.innerHTML = `

            <div class="field">

                <label>
                    معلومات
                </label>

                <textarea
                    id="toolInput"
                    placeholder="خپلې نښې، د پیل وخت، بدلونونه، درمل او پوښتنې ولیکئ..."></textarea>

            </div>


            <button
                class="primary-button"
                onclick="runTool('/doctor')">

                👨‍⚕️ معلومات منظم کړه

            </button>


            <div
                id="toolResult"
                class="result"></div>

        `;

    }


    /* -----------------------------------------------------
       LAB
    ----------------------------------------------------- */

    else if (tool === "lab") {

        title.textContent =
            "🧪 Lab Report";


        body.innerHTML = `

            <div class="field">

                <label>
                    Lab Report
                </label>

                <textarea
                    id="toolInput"
                    placeholder="د لابراتوار راپور دلته ولیکئ..."></textarea>

            </div>


            <button
                class="primary-button"
                onclick="runTool('/lab')">

                🧪 راپور تشریح کړه

            </button>


            <div
                id="toolResult"
                class="result"></div>

        `;

    }


    /* -----------------------------------------------------
       MEDICINE
    ----------------------------------------------------- */

    else if (tool === "medicine") {

        title.textContent =
            "💊 Medicine Information";


        body.innerHTML = `

            <div class="field">

                <label>
                    د درملو نوم
                </label>

                <input
                    id="toolInput"
                    placeholder="مثلاً Paracetamol">

            </div>


            <button
                class="primary-button"
                onclick="runTool('/medicine')">

                💊 معلومات

            </button>


            <div
                id="toolResult"
                class="result"></div>

        `;

    }


    /* -----------------------------------------------------
       DICTIONARY
    ----------------------------------------------------- */

    else if (tool === "dictionary") {

        title.textContent =
            "📖 Medical Dictionary";


        body.innerHTML = `

            <div class="field">

                <label>
                    طبي اصطلاح
                </label>

                <input
                    id="toolInput"
                    placeholder="Hypertension">

            </div>


            <button
                class="primary-button"
                onclick="runTool('/dictionary')">

                📖 تشریح

            </button>


            <div
                id="toolResult"
                class="result"></div>

        `;

    }


    /* -----------------------------------------------------
       EMERGENCY
    ----------------------------------------------------- */

    else if (tool === "emergency") {

        title.textContent =
            "🚨 Emergency Checker";


        body.innerHTML = `

            <div class="field">

                <label>
                    نښې
                </label>

                <textarea
                    id="toolInput"
                    placeholder="اوسنۍ نښې ولیکئ..."></textarea>

            </div>


            <button
                class="danger-button"
                onclick="runTool('/emergency')">

                🚨 بیړنۍ نښې وګوره

            </button>


            <div
                id="toolResult"
                class="result"></div>

        `;

    }


    /* -----------------------------------------------------
       INTERACTION
    ----------------------------------------------------- */

    else if (tool === "interaction") {

        title.textContent =
            "💊 Medicine Interaction";


        body.innerHTML = `

            <div class="field">

                <label>
                    د درملو نومونه
                </label>

                <textarea
                    id="toolInput"
                    placeholder="Medicine A
Medicine B
Medicine C"></textarea>

            </div>


            <button
                class="primary-button"
                onclick="runTool('/interaction')">

                💊 تداخل وګوره

            </button>


            <div
                id="toolResult"
                class="result"></div>

        `;

    }


    /* -----------------------------------------------------
       REPORT
    ----------------------------------------------------- */

    else if (tool === "report") {

        title.textContent =
            "📋 Medical Report";


        body.innerHTML = `

            <div class="field">

                <label>
                    طبي راپور
                </label>

                <textarea
                    id="toolInput"
                    placeholder="طبي راپور دلته ولیکئ..."></textarea>

            </div>


            <button
                class="primary-button"
                onclick="runTool('/report')">

                📋 تشریح

            </button>


            <div
                id="toolResult"
                class="result"></div>

        `;

    }


    /* -----------------------------------------------------
       FIRST AID
    ----------------------------------------------------- */

    else if (tool === "firstaid") {

        title.textContent =
            "🩹 First Aid";


        body.innerHTML = `

            <div class="field">

                <label>
                    حالت
                </label>

                <input
                    id="toolInput"
                    placeholder="Burn, Cut, Nosebleed...">

            </div>


            <button
                class="primary-button"
                onclick="runTool('/firstaid')">

                🩹 First Aid

            </button>


            <div
                id="toolResult"
                class="result"></div>

        `;

    }


    /* -----------------------------------------------------
       GLOSSARY
    ----------------------------------------------------- */

    else if (tool === "glossary") {

        title.textContent =
            "📚 Medical Glossary";


        body.innerHTML = `

            <div class="field">

                <label>
                    طبي اصطلاحات
                </label>

                <textarea
                    id="toolInput"
                    placeholder="اصطلاحات ولیکئ..."></textarea>

            </div>


            <button
                class="primary-button"
                onclick="runTool('/glossary')">

                📚 ساده تشریح

            </button>


            <div
                id="toolResult"
                class="result"></div>

        `;

    }


    /* -----------------------------------------------------
       RISK
    ----------------------------------------------------- */

    else if (tool === "risk") {

        title.textContent =
            "🧠 Risk Assessment";


        body.innerHTML = `

            <div class="field">

                <label>
                    روغتیايي معلومات
                </label>

                <textarea
                    id="toolInput"
                    placeholder="عمر، نښې، موده او نور اړوند معلومات..."></textarea>

            </div>


            <button
                class="primary-button"
                onclick="runTool('/risk')">

                🧠 د خطر نښې وڅېړه

            </button>


            <div
                id="toolResult"
                class="result"></div>

        `;

    }


    /* -----------------------------------------------------
       QUIZ
    ----------------------------------------------------- */

    else if (tool === "quiz") {

        title.textContent =
            "📝 Medical Quiz";


        body.innerHTML = `

            <p>
                د طبي زده کړې لپاره ۵ پوښتنې جوړېږي.
            </p>


            <button
                class="primary-button"
                onclick="generateQuiz()">

                📝 Quiz جوړ کړه

            </button>


            <div
                id="toolResult"
                class="result"></div>

        `;

    }


    /* -----------------------------------------------------
       HEALTH REPORT
    ----------------------------------------------------- */

    else if (tool === "healthreport") {

        title.textContent =
            "📊 Health Report";


        body.innerHTML = `

            <div class="field">

                <label>
                    روغتیايي معلومات
                </label>

                <textarea
                    id="toolInput"
                    placeholder="خپل روغتیايي معلومات ولیکئ..."></textarea>

            </div>


            <button
                class="primary-button"
                onclick="generateHealthReport()">

                📊 راپور جوړ کړه

            </button>


            <div
                id="toolResult"
                class="result"></div>

        `;

    }


    /* -----------------------------------------------------
       TRACKER
    ----------------------------------------------------- */

    else if (tool === "tracker") {

        title.textContent =
            "📈 Health Tracker";


        body.innerHTML = `

            <div class="field">

                <label>
                    ډول
                </label>

                <select id="trackerType">

                    <option>
                        Blood Pressure
                    </option>

                    <option>
                        Pulse
                    </option>

                    <option>
                        Temperature
                    </option>

                    <option>
                        Weight
                    </option>

                    <option>
                        Blood Sugar
                    </option>

                    <option>
                        Oxygen
                    </option>

                </select>

            </div>


            <div class="field">

                <label>
                    Value
                </label>

                <input
                    id="trackerValue"
                    placeholder="مثلاً 120/80">

            </div>


            <div class="field">

                <label>
                    یادونه
                </label>

                <input
                    id="trackerNote"
                    placeholder="اختیاري">

            </div>


            <button
                class="primary-button"
                onclick="addTracker()">

                ＋ ثبت کړه

            </button>


            <div
                id="trackerList"
                style="margin-top:15px;">
            </div>


            <button
                class="danger-button"
                onclick="clearTracker()"
                style="margin-top:10px;">

                ټول پاک کړه

            </button>

        `;

        loadTracker();

    }


    /* -----------------------------------------------------
       REMINDER
    ----------------------------------------------------- */

    else if (tool === "reminder") {

        title.textContent =
            "⏰ Medication Reminder";


        body.innerHTML = `

            <div class="field">

                <label>
                    د درملو نوم
                </label>

                <input
                    id="reminderMedicine"
                    placeholder="د درملو نوم">

            </div>


            <div class="field">

                <label>
                    وخت
                </label>

                <input
                    id="reminderTime"
                    type="time">

            </div>


            <div class="field">

                <label>
                    یادونه
                </label>

                <input
                    id="reminderNote"
                    placeholder="اختیاري">

            </div>


            <button
                class="primary-button"
                onclick="addReminder()">

                ⏰ Reminder اضافه کړه

            </button>


            <div
                id="reminders"
                style="margin-top:15px;">
            </div>

        `;

        loadReminders();

    }


    /* -----------------------------------------------------
       IMAGES
    ----------------------------------------------------- */

    else if (tool === "images") {

        title.textContent =
            "🖼️ Medical Images";


        body.innerHTML = `

            <div class="field">

                <label>
                    د انځور موضوع
                </label>

                <input
                    id="imageQuery"
                    placeholder="Human Heart">

            </div>


            <button
                class="primary-button"
                onclick="loadImages()">

                🖼️ انځورونه ولټوه

            </button>


            <div
                id="imageResults"
                class="image-grid">
            </div>

        `;

    }


    /* -----------------------------------------------------
       COMPARE
    ----------------------------------------------------- */

    else if (tool === "compare") {

        title.textContent =
            "⚖️ Disease Comparison";


        body.innerHTML = `

            <div class="field">

                <label>
                    لومړۍ ناروغي
                </label>

                <input
                    id="disease1"
                    placeholder="Diabetes">

            </div>


            <div class="field">

                <label>
                    دوهمه ناروغي
                </label>

                <input
                    id="disease2"
                    placeholder="Hypertension">

            </div>


            <button
                class="primary-button"
                onclick="compareDiseases()">

                ⚖️ پرتله کړه

            </button>


            <div
                id="toolResult"
                class="result"></div>

        `;

    }


    /* -----------------------------------------------------
       HISTORY
    ----------------------------------------------------- */

    else if (tool === "history") {

        title.textContent =
            "🕘 History";


        body.innerHTML = `

            <div id="historyList"></div>


            <button
                class="danger-button"
                onclick="clearHistory()">

                History پاک کړه

            </button>

        `;

        loadHistory();

    }


    /* -----------------------------------------------------
       FAVORITES
    ----------------------------------------------------- */

    else if (tool === "favorites") {

        title.textContent =
            "⭐ Favorites";


        body.innerHTML = `

            <div id="favoritesList"></div>


            <button
                class="danger-button"
                onclick="clearFavorites()">

                Favorites پاک کړه

            </button>

        `;

        loadFavorites();

    }


    /* -----------------------------------------------------
       ABOUT
    ----------------------------------------------------- */

    else if (tool === "about") {

        title.textContent =
            "ℹ️ About MedAI";


        body.innerHTML = `

            <div class="result">

                <h2>
                    🩺 MedAI
                </h2>

                <p>
                    ستاسو هوښیار طبي معلوماتي مرستیال.
                </p>

                <p>
                    <strong>Developer:</strong>
                    Toyebullah Dawoodzay
                </p>

                <p>
                    <strong>Created:</strong>
                    2026
                </p>

                <p>
                    MedAI د تعلیمي طبي معلوماتو لپاره جوړ شوی.
                    دا د مسلکي روغتیايي متخصص بدیل نه دی.
                </p>

            </div>

        `;

    }

}


/* =========================================================
   CLOSE TOOL
========================================================= */

function closeTool() {

    $("toolPanel")
        .classList.remove("show");

}


/* =========================================================
   RUN TOOL
========================================================= */

async function runTool(endpoint) {

    const input =
        $("toolInput");

    const result =
        $("toolResult");


    if (!input || !result) {

        return;

    }


    const text =
        input.value.trim();


    if (!text) {

        result.textContent =
            "مهرباني وکړئ معلومات ولیکئ.";

        return;

    }


    result.textContent =
        "AI کار کوي...";


    try {

        const response =
            await fetch(
                endpoint,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            text: text
                        })
                }
            );


        const data =
            await response.json();


        result.textContent =
            data.answer ||
            data.error ||
            "ځواب ترلاسه نه شو.";

    }

    catch (error) {

        result.textContent =
            "د سرور سره د اړیکې ستونزه.";

    }

}


/* =========================================================
   COMPARE
========================================================= */

async function compareDiseases() {

    const a =
        $("disease1").value.trim();

    const b =
        $("disease2").value.trim();


    if (!a || !b) {

        $("toolResult").textContent =
            "دواړه ناروغۍ ولیکئ.";

        return;

    }


    $("toolResult").textContent =
        "AI کار کوي...";


    try {

        const response =
            await fetch(
                "/compare",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            disease1: a,
                            disease2: b
                        })
                }
            );


        const data =
            await response.json();


        $("toolResult").textContent =
            data.answer ||
            data.error ||
            "ځواب ترلاسه نه شو.";

    }

    catch (error) {

        $("toolResult").textContent =
            "د سرور ستونزه.";

    }

}


/* =========================================================
   QUIZ
========================================================= */

async function generateQuiz() {

    const result =
        $("toolResult");


    result.textContent =
        "AI کار کوي...";


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
                            question:
                                "Create a 5-question educational medical quiz with four choices and correct answers. Answer in the same language as the user."
                        })
                }
            );


        const data =
            await response.json();


        result.textContent =
            data.answer ||
            data.error ||
            "Quiz جوړ نه شو.";

    }

    catch (error) {

        result.textContent =
            "د Quiz ستونزه.";

    }

}


/* =========================================================
   MEDICAL IMAGES
========================================================= */

async function loadImages() {

    const query =
        $("imageQuery").value.trim();

    const box =
        $("imageResults");


    if (!query) {

        box.innerHTML =
            "<p>موضوع ولیکئ.</p>";

        return;

    }


    box.innerHTML =
        "<p>انځورونه لټول کېږي...</p>";


    try {

        const response =
            await fetch(
                "/images?q=" +
                encodeURIComponent(query)
            );


        const data =
            await response.json();


        box.innerHTML = "";


        if (
            !data.images ||
            !data.images.length
        ) {

            box.innerHTML =
                "<p>انځورونه پیدا نه شول.</p>";

            return;

        }


        data.images.forEach(
            image => {

                const card =
                    document.createElement(
                        "div"
                    );

                card.className =
                    "image-card";


                card.innerHTML = `

                    <img
                        src="${escapeHTML(image.url)}"
                        alt="${escapeHTML(image.title)}"
                        loading="lazy">

                    <div class="image-title">
                        ${escapeHTML(image.title)}
                    </div>

                `;


                box.appendChild(card);

            }
        );

    }

    catch (error) {

        box.innerHTML =
            "<p>د انځورونو ستونزه.</p>";

    }

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
            "ستاسو browser د Voice Input ملاتړ نه کوي."
        );

        return;

    }


    recognition =
        new SpeechRecognition();


    recognition.lang =
        "ps-AF";


    recognition.interimResults =
        false;


    recognition.continuous =
        false;


    recognition.onresult =
        function(event) {

            const text =
                event
                    .results[0][0]
                    .transcript;


            $("question").value =
                text;

        };


    recognition.onerror =
        function() {

            alert(
                "Voice کې ستونزه رامنځته شوه."
            );

        };


    recognition.start();

}


/* =========================================================
   VOICE OUTPUT
========================================================= */

function speakAnswer() {

    if (!currentAnswer) {

        return;

    }


    if (
        !("speechSynthesis" in window)
    ) {

        return;

    }


    speechSynthesis.cancel();


    const utterance =
        new SpeechSynthesisUtterance(
            currentAnswer
        );


    utterance.lang =
        "ps-AF";


    utterance.rate =
        .9;


    speechSynthesis.speak(
        utterance
    );

}


/* =========================================================
   HISTORY
========================================================= */

function saveHistory(
    question,
    answer
) {

    let history =
        JSON.parse(
            localStorage.getItem(
                "medai_history"
            ) || "[]"
        );


    history.unshift({

        question:
            question,

        answer:
            answer,

        time:
            new Date().toLocaleString()

    });


    history =
        history.slice(0, 50);


    localStorage.setItem(
        "medai_history",
        JSON.stringify(history)
    );

}


function loadHistory() {

    const box =
        $("historyList");


    if (!box) {

        return;

    }


    const history =
        JSON.parse(
            localStorage.getItem(
                "medai_history"
            ) || "[]"
        );


    if (!history.length) {

        box.innerHTML =
            "<p>History خالي دی.</p>";

        return;

    }


    box.innerHTML =
        history
            .map(
                (item, index) => `

                    <div class="list-item">

                        <strong>
                            ${escapeHTML(item.question)}
                        </strong>

                        <small>
                            ${escapeHTML(item.time)}
                        </small>

                        <p>
                            ${escapeHTML(item.answer)}
                        </p>

                        <button
                            class="primary-button"
                            onclick="favoriteFromHistory(${index})">

                            ⭐ Favorite

                        </button>

                    </div>

                `
            )
            .join("");

}


function clearHistory() {

    localStorage.removeItem(
        "medai_history"
    );


    loadHistory();

}


function favoriteFromHistory(
    index
) {

    const history =
        JSON.parse(
            localStorage.getItem(
                "medai_history"
            ) || "[]"
        );


    if (!history[index]) {

        return;

    }


    let favorites =
        JSON.parse(
            localStorage.getItem(
                "medai_favorites"
            ) || "[]"
        );


    favorites.unshift(
        history[index]
    );


    favorites =
        favorites.slice(0, 50);


    localStorage.setItem(
        "medai_favorites",
        JSON.stringify(favorites)
    );


    alert(
        "Favorite ته اضافه شو ⭐"
    );

}


/* =========================================================
   FAVORITES
========================================================= */

function loadFavorites() {

    const box =
        $("favoritesList");


    if (!box) {

        return;

    }


    const favorites =
        JSON.parse(
            localStorage.getItem(
                "medai_favorites"
            ) || "[]"
        );


    if (!favorites.length) {

        box.innerHTML =
            "<p>Favorites خالي دي.</p>";

        return;

    }


    box.innerHTML =
        favorites
            .map(
                item => `

                    <div class="list-item">

                        <strong>
                            ${escapeHTML(item.question)}
                        </strong>

                        <small>
                            ${escapeHTML(item.time)}
                        </small>

                        <p>
                            ${escapeHTML(item.answer)}
                        </p>

                    </div>

                `
            )
            .join("");

}


function clearFavorites() {

    localStorage.removeItem(
        "medai_favorites"
    );


    loadFavorites();

}


/* =========================================================
   REMINDERS
========================================================= */

function addReminder() {

    const medicine =
        $("reminderMedicine")
            .value
            .trim();


    const time =
        $("reminderTime")
            .value;


    const note =
        $("reminderNote")
            .value
            .trim();


    if (!medicine || !time) {

        alert(
            "د درملو نوم او وخت ولیکئ."
        );

        return;

    }


    let reminders =
        JSON.parse(
            localStorage.getItem(
                "medai_reminders"
            ) || "[]"
        );


    reminders.push({

        medicine:
            medicine,

        time:
            time,

        note:
            note

    });


    localStorage.setItem(
        "medai_reminders",
        JSON.stringify(reminders)
    );


    $("reminderMedicine").value =
        "";

    $("reminderTime").value =
        "";

    $("reminderNote").value =
        "";


    loadReminders();

}


function loadReminders() {

    const box =
        $("reminders");


    if (!box) {

        return;

    }


    const reminders =
        JSON.parse(
            localStorage.getItem(
                "medai_reminders"
            ) || "[]"
        );


    box.innerHTML =
        reminders
            .map(
                (item, index) => `

                    <div class="list-item">

                        <strong>
                            💊 ${escapeHTML(item.medicine)}
                        </strong>

                        <p>
                            ⏰ ${escapeHTML(item.time)}
                        </p>

                        <small>
                            ${escapeHTML(item.note || "")}
                        </small>

                        <button
                            class="danger-button"
                            onclick="deleteReminder(${index})">

                            حذف

                        </button>

                    </div>

                `
            )
            .join("");

}


function deleteReminder(index) {

    let reminders =
        JSON.parse(
            localStorage.getItem(
                "medai_reminders"
            ) || "[]"
        );


    reminders.splice(
        index,
        1
    );


    localStorage.setItem(
        "medai_reminders",
        JSON.stringify(reminders)
    );


    loadReminders();

}


/* =========================================================
   HEALTH TRACKER
========================================================= */

function addTracker() {

    const type =
        $("trackerType").value;


    const value =
        $("trackerValue")
            .value
            .trim();


    const note =
        $("trackerNote")
            .value
            .trim();


    if (!value) {

        alert(
            "Value ولیکئ."
        );

        return;

    }


    let tracker =
        JSON.parse(
            localStorage.getItem(
                "medai_tracker"
            ) || "[]"
        );


    tracker.unshift({

        type:
            type,

        value:
            value,

        note:
            note,

        time:
            new Date().toLocaleString()

    });


    tracker =
        tracker.slice(0, 100);


    localStorage.setItem(
        "medai_tracker",
        JSON.stringify(tracker)
    );


    $("trackerValue").value =
        "";

    $("trackerNote").value =
        "";


    loadTracker();

}


function loadTracker() {

    const box =
        $("trackerList");


    if (!box) {

        return;

    }


    const tracker =
        JSON.parse(
            localStorage.getItem(
                "medai_tracker"
            ) || "[]"
        );


    if (!tracker.length) {

        box.innerHTML =
            "<p>تر اوسه معلومات نشته.</p>";

        return;

    }


    box.innerHTML =
        tracker
            .map(
                (item, index) => `

                    <div class="list-item">

                        <strong>
                            ${escapeHTML(item.type)}
                        </strong>

                        <p>
                            Value:
                            ${escapeHTML(item.value)}
                        </p>

                        <small>
                            ${escapeHTML(item.time)}
                        </small>

                        <p>
                            ${escapeHTML(item.note || "")}
                        </p>

                        <button
                            class="danger-button"
                            onclick="deleteTracker(${index})">

                            حذف

                        </button>

                    </div>

                `
            )
            .join("");

}


function deleteTracker(index) {

    let tracker =
        JSON.parse(
            localStorage.getItem(
                "medai_tracker"
            ) || "[]"
        );


    tracker.splice(
        index,
        1
    );


    localStorage.setItem(
        "medai_tracker",
        JSON.stringify(tracker)
    );


    loadTracker();

}


function clearTracker() {

    localStorage.removeItem(
        "medai_tracker"
    );


    loadTracker();

}


/* =========================================================
   HEALTH REPORT
========================================================= */

async function generateHealthReport() {

    const manual =
        $("toolInput")
            ? $("toolInput")
                .value
                .trim()
            : "";


    const tracker =
        JSON.parse(
            localStorage.getItem(
                "medai_tracker"
            ) || "[]"
        );


    if (
        !manual &&
        !tracker.length
    ) {

        $("toolResult").textContent =
            "لومړی معلومات ولیکئ یا Health Tracker وکاروئ.";

        return;

    }


    $("toolResult").textContent =
        "AI کار کوي...";


    const text =
        "User Notes:\n" +
        manual +
        "\n\nHealth Tracker:\n" +
        JSON.stringify(tracker);


    try {

        const response =
            await fetch(
                "/health-report",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            text:
                                text
                        })
                }
            );


        const data =
            await response.json();


        $("toolResult").textContent =
            data.answer ||
            data.error ||
            "راپور جوړ نه شو.";

    }

    catch (error) {

        $("toolResult").textContent =
            "د راپور ستونزه.";

    }

}


/* =========================================================
   STARTUP
========================================================= */

console.log(
    "MedAI loaded successfully."
);

</script>

</body>

</html>
"""


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def home():
    return HTML


# ============================================================
# CHAT
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}

    question = str(
        data.get("question", "")
    ).strip()


    if not question:

        return jsonify({
            "error": "پوښتنه خالي ده."
        }), 400


    instruction = """
Give a structured medical educational answer.

Use sections when appropriate:

Definition
Causes
Types
Risk Factors
Signs and Symptoms
Diagnosis
Treatment
Prevention
Complications
Important Points

Do not diagnose the user.
"""


    answer = ask_gemini(
        build_prompt(
            instruction,
            question
        )
    )


    return jsonify({
        "answer": answer
    })


# ============================================================
# SIMPLE ROUTE HELPER
# ============================================================

def simple_route(
    instruction,
    empty_message
):

    data = request.get_json(
        silent=True
    ) or {}


    text = str(
        data.get("text", "")
    ).strip()


    if not text:

        return jsonify({
            "error": empty_message
        }), 400


    answer = ask_gemini(
        build_prompt(
            instruction,
            text
        )
    )


    return jsonify({
        "answer": answer
    })


# ============================================================
# SYMPTOMS
# ============================================================

@app.route(
    "/symptoms",
    methods=["POST"]
)
def symptoms():

    return simple_route(
        """
Explain symptoms educationally.

Include:
- what the symptoms may mean generally
- body systems that can be involved
- common possibilities
- warning signs
- when professional evaluation may be appropriate

Do not diagnose.
""",
        "نښې ولیکئ."
    )


# ============================================================
# VITALS
# ============================================================

@app.route(
    "/vitals",
    methods=["POST"]
)
def vitals():

    return simple_route(
        """
Explain the provided vital signs educationally.

Discuss:
- what each measurement represents
- general concepts
- factors that can affect readings
- why repeated measurements may matter
- when professional evaluation may be appropriate

Do not diagnose.
""",
        "Vital signs معلومات ولیکئ."
    )


# ============================================================
# DOCTOR
# ============================================================

@app.route(
    "/doctor",
    methods=["POST"]
)
def doctor():

    return simple_route(
        """
Organize the user's notes for a doctor visit.

Use:
- Main concern
- Symptoms
- When symptoms started
- Changes
- Relevant measurements
- Medicines mentioned
- Tests mentioned
- Questions for doctor

Do not add information that the user did not provide.
""",
        "معلومات ولیکئ."
    )


# ============================================================
# LAB
# ============================================================

@app.route(
    "/lab",
    methods=["POST"]
)
def lab():

    return simple_route(
        """
Explain the laboratory information educationally.

Discuss:
- what the test measures
- why it is commonly used
- what high or low results can sometimes be associated with
- factors that can affect results
- why reference ranges differ between laboratories

Do not diagnose.
Do not invent missing values.
""",
        "Lab معلومات ولیکئ."
    )


# ============================================================
# MEDICINE
# ============================================================

@app.route(
    "/medicine",
    methods=["POST"]
)
def medicine():

    return simple_route(
        """
Give general educational medicine information.

Include:
- what the medicine is
- common uses
- general mechanism
- common side effects
- precautions
- important interaction categories

Do not provide personalized dosing.
Do not tell the user to start, stop, or change a prescription medicine.
""",
        "د درملو نوم ولیکئ."
    )


# ============================================================
# DICTIONARY
# ============================================================

@app.route(
    "/dictionary",
    methods=["POST"]
)
def dictionary():

    return simple_route(
        """
Explain the medical term in very simple language.

Include:
- Definition
- Why it matters
- Medical context
- Short example

Answer in the user's language.
""",
        "اصطلاح ولیکئ."
    )


# ============================================================
# EMERGENCY
# ============================================================

@app.route(
    "/emergency",
    methods=["POST"]
)
def emergency():

    return simple_route(
        """
Review the provided information only for general emergency warning signs.

Separate:
- Emergency warning signs
- Other information
- Appropriate action

If serious warning signs are present, advise urgent professional medical care.

Do not diagnose.
""",
        "نښې ولیکئ."
    )


# ============================================================
# INTERACTION
# ============================================================

@app.route(
    "/interaction",
    methods=["POST"]
)
def interaction():

    return simple_route(
        """
Review listed medicines for known or potentially important interactions.

Explain:
- medicines involved
- possible interaction
- why it may matter
- what kind of professional review may be appropriate

Do not tell the user to stop or change medicines.
Do not provide personalized medication instructions.
""",
        "د درملو نومونه ولیکئ."
    )


# ============================================================
# REPORT
# ============================================================

@app.route(
    "/report",
    methods=["POST"]
)
def report():

    return simple_route(
        """
Explain the medical report simply.

Include:
- subject
- important findings
- medical terms
- what findings can generally be associated with
- useful questions for a healthcare professional
- limitations

Do not diagnose.
Do not invent missing information.
""",
        "طبي راپور ولیکئ."
    )


# ============================================================
# FIRST AID
# ============================================================

@app.route(
    "/firstaid",
    methods=["POST"]
)
def firstaid():

    return simple_route(
        """
Give a general first-aid educational guide.

Include:
- immediate priorities
- basic first-aid steps
- what not to do
- emergency warning signs
- when professional medical care is needed

Do not provide dangerous instructions.
""",
        "حالت ولیکئ."
    )


# ============================================================
# GLOSSARY
# ============================================================

@app.route(
    "/glossary",
    methods=["POST"]
)
def glossary():

    return simple_route(
        """
Explain each medical term in very simple language.

For each term include:
- meaning
- medical use
- short example

Answer in the user's language.
""",
        "اصطلاحات ولیکئ."
    )


# ============================================================
# RISK
# ============================================================

@app.route(
    "/risk",
    methods=["POST"]
)
def risk():

    return simple_route(
        """
Review the provided information for general medical risk indicators.

Identify:
- reported risk factors
- warning signs
- missing information
- when urgent professional evaluation may be appropriate
- when routine professional evaluation may be appropriate

Do not calculate a fake medical score.
Do not diagnose.
Do not predict outcomes.
""",
        "معلومات ولیکئ."
    )


# ============================================================
# HEALTH REPORT
# ============================================================

@app.route(
    "/health-report",
    methods=["POST"]
)
def health_report():

    return simple_route(
        """
Create an educational health summary.

Include:
- Summary
- Recorded measurements
- Symptoms or concerns
- Directly observable trends
- Questions for healthcare professional
- Limitations

Do not diagnose.
Do not invent information.
""",
        "د روغتیا معلومات ولیکئ."
    )


# ============================================================
# DISEASE COMPARISON
# ============================================================

@app.route(
    "/compare",
    methods=["POST"]
)
def compare_route():

    data = request.get_json(
        silent=True
    ) or {}


    disease1 = str(
        data.get(
            "disease1",
            ""
        )
    ).strip()


    disease2 = str(
        data.get(
            "disease2",
            ""
        )
    ).strip()


    if not disease1 or not disease2:

        return jsonify({
            "error":
                "دواړه ناروغۍ ولیکئ."
        }), 400


    text = (
        "Disease 1: "
        + disease1
        + "\nDisease 2: "
        + disease2
    )


    answer = ask_gemini(
        build_prompt(
            """
Compare the two conditions educationally.

Include:
- Definition
- Causes
- Risk Factors
- Symptoms
- Diagnosis approaches
- Treatment approaches
- Similarities
- Differences
- Warning signs

Do not diagnose the user.
""",
            text
        )
    )


    return jsonify({
        "answer": answer
    })


# ============================================================
# IMAGES
# ============================================================

@app.route(
    "/images",
    methods=["GET"]
)
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


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({
        "status": "ok",
        "app": "MedAI",
        "developer":
            "Toyebullah Dawoodzay",
        "created": 2026
    })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )


    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
