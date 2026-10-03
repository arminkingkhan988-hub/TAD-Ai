import os
import requests

from flask import Flask, request, jsonify, render_template_string


app = Flask(__name__)


# =========================================================
# GEMINI
# =========================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
).strip()

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    + GEMINI_MODEL
    + ":generateContent"
)


SYSTEM_PROMPT = """
You are MedAI, a helpful multilingual AI assistant.

Always answer in the same language as the user.

If the user writes Pashto:
answer in Pashto.

If the user writes Dari:
answer in Dari.

If the user writes English:
answer in English.

You can help with:

- General questions
- Education
- Science
- Mathematics
- Programming
- Technology
- Writing
- Translation
- History
- Business
- Health information

Medical safety:

Give general educational information only.

Do not claim to diagnose someone.

Do not pretend that an image can provide a certain diagnosis.

For serious or emergency symptoms, advise the user
to seek appropriate professional or emergency medical care.

Do not tell users to change prescription medication
without professional medical advice.

Be clear, helpful and honest about uncertainty.
"""


# =========================================================
# COMPLETE FRONTEND
# =========================================================

HTML = r"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>MedAI</title>


<style>

:root {

    --bg: #ffffff;

    --panel: #f7f7f8;

    --panel2: #ffffff;

    --text: #171717;

    --muted: #6b7280;

    --border: #dddddd;

    --accent: #10a37f;

    --danger: #dc2626;

    --user: #111827;
}


body.dark {

    --bg: #212121;

    --panel: #171717;

    --panel2: #2b2b2b;

    --text: #f5f5f5;

    --muted: #aaaaaa;

    --border: #444444;

    --user: #374151;
}


* {

    box-sizing: border-box;

}


body {

    margin: 0;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background: var(--bg);

    color: var(--text);

}


button,
textarea,
input {

    font: inherit;

}


button {

    cursor: pointer;

}


.app {

    height: 100vh;

    display: flex;

    overflow: hidden;

}


/* SIDEBAR */

.sidebar {

    width: 280px;

    background: var(--panel);

    border-right:
        1px solid
        var(--border);

    display: flex;

    flex-direction: column;

    padding: 14px;

    gap: 10px;

}


.brand {

    font-size: 23px;

    font-weight: 800;

    padding:
        8px 6px 14px;

}


.brand span {

    color: var(--accent);

}


.new-chat,
.side-button {

    width: 100%;

    border:
        1px solid
        var(--border);

    background:
        var(--panel2);

    color:
        var(--text);

    border-radius: 10px;

    padding: 11px;

    text-align: left;

}


.new-chat {

    font-weight: bold;

}


.new-chat:hover,
.side-button:hover {

    background:
        rgba(127,127,127,.12);

}


.history {

    flex: 1;

    overflow-y: auto;

}


.history-title {

    font-size: 12px;

    color: var(--muted);

    padding:
        12px 6px 7px;

}


.history-item {

    display: flex;

    align-items: center;

    gap: 5px;

    border-radius: 9px;

    padding: 8px;

}


.history-item:hover {

    background:
        rgba(127,127,127,.12);

}


.history-open {

    flex: 1;

    overflow: hidden;

    white-space: nowrap;

    text-overflow: ellipsis;

    text-align: left;

    background: none;

    border: 0;

    color: var(--text);

}


.history-delete {

    border: 0;

    background: none;

    color: var(--muted);

}


.bottom-tools {

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 8px;

}


/* MAIN */

.main {

    flex: 1;

    min-width: 0;

    display: flex;

    flex-direction: column;

}


.header {

    height: 58px;

    border-bottom:
        1px solid
        var(--border);

    display: flex;

    align-items: center;

    justify-content:
        space-between;

    padding:
        0 18px;

}


.header-title {

    font-weight: 800;

}


.header-actions {

    display: flex;

    gap: 7px;

}


.icon-button {

    width: 38px;

    height: 36px;

    border:
        1px solid
        var(--border);

    border-radius: 9px;

    background:
        var(--panel2);

    color:
        var(--text);

}


/* CHAT */

.chat {

    flex: 1;

    overflow-y: auto;

    padding:
        25px 14px 180px;

}


.messages {

    max-width: 900px;

    margin: auto;

}


.welcome {

    text-align: center;

    margin:
        12vh auto 30px;

    max-width: 680px;

}


.welcome h1 {

    font-size: 38px;

    margin-bottom: 10px;

}


.welcome p {

    color: var(--muted);

}


.cards {

    display: grid;

    grid-template-columns:
        repeat(2, 1fr);

    gap: 10px;

    margin-top: 25px;

}


.card {

    padding: 15px;

    border:
        1px solid
        var(--border);

    border-radius: 13px;

    background:
        var(--panel2);

    color:
        var(--text);

    text-align: left;

}


.card b {

    display: block;

    margin-bottom: 5px;

}


/* MESSAGE */

.message {

    display: flex;

    gap: 12px;

    margin: 24px 0;

}


.avatar {

    width: 34px;

    height: 34px;

    min-width: 34px;

    border-radius: 50%;

    display: flex;

    align-items: center;

    justify-content: center;

    color: white;

    font-weight: bold;

}


.avatar-user {

    background:
        var(--user);

}


.avatar-ai {

    background:
        var(--accent);

}


.message-body {

    min-width: 0;

    flex: 1;

}


.message-header {

    display: flex;

    gap: 8px;

    margin-bottom: 5px;

}


.message-name {

    font-weight: bold;

}


.message-time {

    color:
        var(--muted);

    font-size: 11px;

}


.message-text {

    white-space: pre-wrap;

    line-height: 1.7;

    overflow-wrap:
        anywhere;

}


.message-image {

    max-width: 330px;

    max-height: 260px;

    border-radius: 12px;

    border:
        1px solid
        var(--border);

    display: block;

    margin-bottom: 8px;

}


.message-tools {

    display: flex;

    gap: 5px;

    margin-top: 6px;

}


.message-tools button {

    border: 0;

    background: none;

    color: var(--muted);

}


/* COMPOSER */

.composer-area {

    position: fixed;

    left: 280px;

    right: 0;

    bottom: 0;

    padding:
        14px 14px 18px;

    background:
        linear-gradient(
            transparent,
            var(--bg) 25%
        );

}


.composer {

    max-width: 900px;

    margin: auto;

    border:
        1px solid
        var(--border);

    border-radius: 17px;

    background:
        var(--panel2);

    padding: 8px;

}


.preview {

    display: none;

    align-items: center;

    gap: 8px;

    padding: 5px;

}


.preview.show {

    display: flex;

}


.preview img {

    width: 65px;

    height: 65px;

    object-fit: cover;

    border-radius: 8px;

}


.preview button {

    border: 0;

    background:
        var(--panel);

    color:
        var(--text);

    padding: 7px;

    border-radius: 7px;

}


.input-row {

    display: flex;

    align-items: end;

    gap: 7px;

}


textarea {

    flex: 1;

    min-height: 46px;

    max-height: 180px;

    resize: none;

    border: 0;

    outline: 0;

    background: transparent;

    color:
        var(--text);

    padding: 11px 8px;

}


.tool-button {

    width: 42px;

    height: 42px;

    border: 0;

    border-radius: 10px;

    background: transparent;

    color:
        var(--text);

}


.tool-button:hover {

    background:
        rgba(127,127,127,.12);

}


.send-button {

    width: 44px;

    height: 44px;

    border: 0;

    border-radius: 11px;

    background:
        var(--accent);

    color: white;

    font-size: 20px;

}


.send-button:disabled {

    opacity: .5;

}


.status {

    text-align: center;

    font-size: 12px;

    color:
        var(--muted);

    padding-top: 7px;

}


/* MODAL */

.modal {

    position: fixed;

    inset: 0;

    background:
        rgba(0,0,0,.55);

    display: none;

    align-items: center;

    justify-content: center;

    padding: 20px;

    z-index: 50;

}


.modal.show {

    display: flex;

}


.modal-box {

    width:
        min(600px, 100%);

    max-height: 85vh;

    overflow-y: auto;

    background:
        var(--panel2);

    border:
        1px solid
        var(--border);

    border-radius: 16px;

    padding: 20px;

}


.modal-head {

    display: flex;

    justify-content:
        space-between;

    align-items: center;

}


.modal-head button {

    border: 0;

    background: none;

    color:
        var(--text);

    font-size: 22px;

}


.field {

    margin: 14px 0;

}


.field label {

    display: block;

    font-size: 13px;

    color:
        var(--muted);

    margin-bottom: 6px;

}


.field input {

    width: 100%;

    padding: 10px;

    border:
        1px solid
        var(--border);

    border-radius: 9px;

    background:
        var(--bg);

    color:
        var(--text);

}


.small-button {

    border:
        1px solid
        var(--border);

    background:
        var(--panel);

    color:
        var(--text);

    border-radius: 8px;

    padding:
        7px 10px;

}


.reminder {

    border:
        1px solid
        var(--border);

    border-radius: 10px;

    padding: 10px;

    margin: 7px 0;

    display: flex;

    justify-content:
        space-between;

    gap: 10px;

}


.notice {

    color:
        var(--muted);

    font-size: 12px;

}


@media(max-width:760px) {

    .sidebar {

        display: none;

    }

    .composer-area {

        left: 0;

    }

    .cards {

        grid-template-columns:
            1fr;

    }

    .welcome h1 {

        font-size: 30px;

    }

    .chat {

        padding-left: 10px;

        padding-right: 10px;

    }

}

</style>

</head>


<body>


<div class="app">


<!-- SIDEBAR -->

<aside class="sidebar">

    <div class="brand">
        🩺 <span>Med</span>AI
    </div>


    <button
        class="new-chat"
        onclick="newChat()"
    >
        ＋ New Chat
    </button>


    <div class="history">

        <div class="history-title">
            CHAT HISTORY
        </div>

        <div id="history"></div>

    </div>


    <div class="bottom-tools">

        <button
            class="side-button"
            onclick="toggleTheme()"
        >
            🌙 Theme
        </button>

        <button
            class="side-button"
            onclick="openReminders()"
        >
            ⏰ Reminders
        </button>

        <button
            class="side-button"
            onclick="exportChat()"
        >
            ⬇ Export
        </button>

        <button
            class="side-button"
            onclick="clearHistory()"
        >
            🗑 Clear
        </button>

    </div>

</aside>


<!-- MAIN -->

<main class="main">


<header class="header">

    <div class="header-title">
        MedAI
    </div>


    <div class="header-actions">

        <button
            class="icon-button"
            onclick="startVoice()"
        >
            🎙
        </button>

        <button
            class="icon-button"
            onclick="toggleTheme()"
        >
            ☾
        </button>

    </div>

</header>


<section
    class="chat"
    id="chat"
>


<div
    class="messages"
    id="messages"
>


<div
    class="welcome"
    id="welcome"
>

<h1>
    How can I help you?
</h1>


<p>
    پښتو، دري او English.
    Ask anything.
</p>


<div class="cards">


<button
    class="card"
    onclick="quickMessage('Explain this topic simply')"
>

<b>
📚 Learn
</b>

Explain difficult topics.

</button>


<button
    class="card"
    onclick="quickMessage('Help me write a professional message')"
>

<b>
✍️ Write
</b>

Write or improve text.

</button>


<button
    class="card"
    onclick="quickMessage('Help me debug my code')"
>

<b>
💻 Code
</b>

Programming help.

</button>


<button
    class="card"
    onclick="quickMessage('Give me general health information about common symptoms')"
>

<b>
🩺 Health
</b>

General health information.

</button>


</div>

</div>

</div>

</section>


<!-- COMPOSER -->

<div class="composer-area">


<div class="composer">


<div
    class="preview"
    id="preview"
>

<img
    id="previewImage"
    alt="Selected image"
>


<button
    onclick="removeImage()"
>
Remove
</button>

</div>


<div class="input-row">


<button
    class="tool-button"
    onclick="document.getElementById('imageInput').click()"
>
＋
</button>


<textarea
    id="message"
    placeholder="Message MedAI..."
    rows="1"
></textarea>


<button
    class="tool-button"
    onclick="startVoice()"
>
🎙
</button>


<button
    class="send-button"
    id="sendButton"
    onclick="sendMessage()"
>
↑
</button>


</div>


<input
    id="imageInput"
    type="file"
    accept="image/*"
    hidden
>


<div
    class="status"
    id="status"
>
AI responses may contain mistakes.
For urgent medical problems, contact professional care.
</div>


</div>

</div>


</main>

</div>


<!-- REMINDER MODAL -->

<div
    class="modal"
    id="reminderModal"
>


<div class="modal-box">


<div class="modal-head">

<h3>
⏰ Reminders
</h3>


<button
    onclick="closeReminders()"
>
×
</button>

</div>


<div class="field">

<label>
Reminder
</label>

<input
    id="reminderText"
    placeholder="Take medicine"
/>

</div>


<div class="field">

<label>
Date and time
</label>

<input
    id="reminderTime"
    type="datetime-local"
/>

</div>


<button
    class="small-button"
    onclick="addReminder()"
>
Add Reminder
</button>


<p class="notice">

Reminders are stored in this browser.

</p>


<hr>


<div id="reminders"></div>


</div>

</div>


<script>


// =========================================================
// STATE
// =========================================================

let selectedImage = null;

let recognition = null;


let currentChat = {

    id:
        crypto.randomUUID
        ? crypto.randomUUID()
        : String(Date.now()),

    title:
        "New Chat",

    messages: []

};


// =========================================================
// HELPERS
// =========================================================

function get(id) {

    return document.getElementById(id);

}


function setStatus(text) {

    get("status").textContent =
        text;

}


// =========================================================
// THEME
// =========================================================

function toggleTheme() {

    document.body.classList.toggle(
        "dark"
    );


    localStorage.setItem(

        "medai-theme",

        document.body.classList.contains(
            "dark"
        )
        ? "dark"
        : "light"

    );

}


if (
    localStorage.getItem(
        "medai-theme"
    ) === "dark"
) {

    document.body.classList.add(
        "dark"
    );

}


// =========================================================
// HISTORY
// =========================================================

function saveChat() {

    localStorage.setItem(

        "medai-current",

        JSON.stringify(
            currentChat
        )

    );


    let history =
        JSON.parse(

            localStorage.getItem(
                "medai-history"
            ) || "[]"

        );


    const index =
        history.findIndex(

            x =>
                x.id ===
                currentChat.id

        );


    const item = {

        id:
            currentChat.id,

        title:
            currentChat.title,

        messages:
            currentChat.messages

    };


    if (index >= 0) {

        history[index] =
            item;

    }

    else {

        history.unshift(
            item
        );

    }


    history =
        history.slice(
            0,
            50
        );


    localStorage.setItem(

        "medai-history",

        JSON.stringify(
            history
        )

    );


    renderHistory();

}


function renderHistory() {

    const box =
        get("history");

    box.innerHTML = "";


    const history =
        JSON.parse(

            localStorage.getItem(
                "medai-history"
            ) || "[]"

        );


    history.forEach(
        item => {

            const row =
                document.createElement(
                    "div"
                );

            row.className =
                "history-item";


            const open =
                document.createElement(
                    "button"
                );

            open.className =
                "history-open";

            open.textContent =
                item.title ||
                "New Chat";


            open.onclick =
                () => {

                    currentChat =
                        JSON.parse(
                            JSON.stringify(
                                item
                            )
                        );

                    renderMessages();

                };


            const del =
                document.createElement(
                    "button"
                );

            del.className =
                "history-delete";

            del.textContent =
                "×";


            del.onclick =
                () => {

                    const updated =
                        history.filter(
                            x =>
                                x.id !==
                                item.id
                        );


                    localStorage.setItem(

                        "medai-history",

                        JSON.stringify(
                            updated
                        )

                    );


                    renderHistory();

                };


            row.append(
                open,
                del
            );


            box.appendChild(
                row
            );

        }
    );

}


// =========================================================
// NEW CHAT
// =========================================================

function newChat() {

    currentChat = {

        id:
            crypto.randomUUID
            ? crypto.randomUUID()
            : String(Date.now()),

        title:
            "New Chat",

        messages: []

    };


    renderMessages();

    get("message").focus();

}


// =========================================================
// RENDER MESSAGES
// =========================================================

function renderMessages() {

    const box =
        get("messages");

    box.innerHTML = "";


    if (
        currentChat.messages.length === 0
    ) {

        box.innerHTML = `

        <div
            class="welcome"
            id="welcome"
        >

        <h1>
            How can I help you?
        </h1>

        <p>
            پښتو، دري او English.
        </p>

        </div>

        `;

        return;

    }


    currentChat.messages.forEach(

        msg => {

            drawMessage(
                msg.role,
                msg.text,
                msg.image,
                false
            );

        }

    );


    scrollChat();

}


// =========================================================
// DRAW MESSAGE
// =========================================================

function drawMessage(
    role,
    text,
    image = null,
    save = true
) {

    const welcome =
        get("welcome");


    if (welcome) {

        welcome.remove();

    }


    const row =
        document.createElement(
            "div"
        );

    row.className =
        "message";


    const avatar =
        document.createElement(
            "div"
        );


    avatar.className =
        "avatar " +
        (
            role === "user"
            ? "avatar-user"
            : "avatar-ai"
        );


    avatar.textContent =
        role === "user"
        ? "U"
        : "AI";


    const body =
        document.createElement(
            "div"
        );


    body.className =
        "message-body";


    const header =
        document.createElement(
            "div"
        );


    header.className =
        "message-header";


    const name =
        document.createElement(
            "span"
        );


    name.className =
        "message-name";


    name.textContent =
        role === "user"
        ? "You"
        : "MedAI";


    const time =
        document.createElement(
            "span"
        );


    time.className =
        "message-time";


    time.textContent =
        new Date().toLocaleTimeString(
            [],
            {
                hour:
                    "2-digit",

                minute:
                    "2-digit"
            }
        );


    header.append(
        name,
        time
    );


    body.appendChild(
        header
    );


    if (image) {

        const imageElement =
            document.createElement(
                "img"
            );


        imageElement.className =
            "message-image";


        imageElement.src =
            image;


        body.appendChild(
            imageElement
        );

    }


    const textElement =
        document.createElement(
            "div"
        );


    textElement.className =
        "message-text";


    textElement.textContent =
        text;


    body.appendChild(
        textElement
    );


    if (
        role === "assistant"
    ) {

        const tools =
            document.createElement(
                "div"
            );


        tools.className =
            "message-tools";


        const copy =
            document.createElement(
                "button"
            );


        copy.textContent =
            "📋";


        copy.onclick =
            () => {

                navigator.clipboard.writeText(
                    text
                );

            };


        const speak =
            document.createElement(
                "button"
            );


        speak.textContent =
            "🔊";


        speak.onclick =
            () => {

                speakText(
                    text
                );

            };


        tools.append(
            copy,
            speak
        );


        body.appendChild(
            tools
        );

    }


    row.append(
        avatar,
        body
    );


    get("messages")
        .appendChild(
            row
        );


    if (save) {

        currentChat.messages.push({

            role:
                role,

            text:
                text,

            image:
                image

        });


        saveChat();

    }


    scrollChat();

}


// =========================================================
// SEND MESSAGE
// =========================================================

async function sendMessage() {

    const input =
        get("message");


    const message =
        input.value.trim();


    if (
        !message &&
        !selectedImage
    ) {

        return;

    }


    const image =
        selectedImage
        ? selectedImage.data
        : null;


    const imageMime =
        selectedImage
        ? selectedImage.mime
        : null;


    drawMessage(

        "user",

        message ||
        "Please analyze this image.",

        image,

        true

    );


    input.value = "";

    input.style.height =
        "46px";


    removeImage();


    get("sendButton")
        .disabled = true;


    setStatus(
        "⏳ MedAI is thinking..."
    );


    const loading =
        document.createElement(
            "div"
        );


    loading.id =
        "loading";


    loading.className =
        "message";


    loading.innerHTML = `

    <div
        class="avatar avatar-ai"
    >
        AI
    </div>

    <div
        class="message-body"
    >

        <div
            class="message-text"
        >
            ⏳ Thinking...
        </div>

    </div>

    `;


    get("messages")
        .appendChild(
            loading
        );


    scrollChat();


    try {

        const history =
            currentChat.messages
                .slice(-12)
                .map(
                    m => ({
                        role:
                            m.role,

                        text:
                            m.text
                    })
                );


        const response =
            await fetch(
                "/api/chat",
                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            message:
                                message,

                            history:
                                history,

                            image:
                                image,

                            image_mime:
                                imageMime

                        })

                }
            );


        const data =
            await response.json();


        const loadingElement =
            get("loading");


        if (loadingElement) {

            loadingElement.remove();

        }


        if (!response.ok) {

            throw new Error(

                data.error ||
                "Server error"

            );

        }


        drawMessage(

            "assistant",

            data.answer,

            null,

            true

        );


        if (

            currentChat.title ===
            "New Chat" &&

            message

        ) {

            currentChat.title =
                message.slice(
                    0,
                    45
                );


            if (
                message.length > 45
            ) {

                currentChat.title +=
                    "…";

            }


            saveChat();

        }


        setStatus(
            "Ready"
        );

    }

    catch (error) {

        const loadingElement =
            get("loading");


        if (loadingElement) {

            loadingElement.remove();

        }


        drawMessage(

            "assistant",

            "خطا: " +
            error.message,

            null,

            true

        );


        setStatus(
            "Ready"
        );

    }


    finally {

        get("sendButton")
            .disabled = false;


        input.focus();

    }

}


// =========================================================
// IMAGE
// =========================================================

get("imageInput")
.addEventListener(

    "change",

    event => {

        const file =
            event.target.files[0];


        if (!file) {

            return;

        }


        if (
            file.size >
            8 * 1024 * 1024
        ) {

            alert(
                "Image must be smaller than 8 MB."
            );

            return;

        }


        const reader =
            new FileReader();


        reader.onload =
            () => {

                selectedImage = {

                    data:
                        reader.result,

                    mime:
                        file.type

                };


                get(
                    "previewImage"
                ).src =
                    reader.result;


                get(
                    "preview"
                ).classList.add(
                    "show"
                );

            };


        reader.readAsDataURL(
            file
        );

    }

);


function removeImage() {

    selectedImage =
        null;


    get(
        "imageInput"
    ).value =
        "";


    get(
        "preview"
    ).classList.remove(
        "show"
    );

}


// =========================================================
// VOICE INPUT
// =========================================================

function startVoice() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;


    if (!SpeechRecognition) {

        alert(
            "Voice input is not supported by this browser. Try Chrome."
        );

        return;

    }


    if (recognition) {

        recognition.stop();

        recognition =
            null;

        return;

    }


    recognition =
        new SpeechRecognition();


    recognition.lang =
        "en-US";


    recognition.interimResults =
        false;


    recognition.maxAlternatives =
        1;


    setStatus(
        "🎙 Listening..."
    );


    recognition.onresult =
        event => {

            get(
                "message"
            ).value =
                event
                .results[0][0]
                .transcript;


            setStatus(
                "Ready"
            );

        };


    recognition.onerror =
        () => {

            setStatus(
                "Voice input stopped."
            );

        };


    recognition.onend =
        () => {

            recognition =
                null;

        };


    recognition.start();

}


// =========================================================
// VOICE OUTPUT
// =========================================================

function speakText(text) {

    if (
        !("speechSynthesis" in window)
    ) {

        alert(
            "Text-to-speech is not supported."
        );

        return;

    }


    speechSynthesis.cancel();


    const speech =
        new SpeechSynthesisUtterance(
            text
        );


    speech.lang =
        "en-US";


    speechSynthesis.speak(
        speech
    );

}


// =========================================================
// QUICK MESSAGE
// =========================================================

function quickMessage(text) {

    get(
        "message"
    ).value =
        text;


    sendMessage();

}


// =========================================================
// EXPORT
// =========================================================

function exportChat() {

    const text =
        currentChat.messages
        .map(
            m =>
                (
                    m.role === "user"
                    ? "You"
                    : "MedAI"
                ) +
                ": " +
                m.text
        )
        .join(
            "\n\n"
        );


    const blob =
        new Blob(
            [text],
            {
                type:
                    "text/plain"
            }
        );


    const url =
        URL.createObjectURL(
            blob
        );


    const link =
        document.createElement(
            "a"
        );


    link.href =
        url;


    link.download =
        "medai-chat.txt";


    link.click();


    URL.revokeObjectURL(
        url
    );

}


// =========================================================
// CLEAR
// =========================================================

function clearHistory() {

    if (
        !confirm(
            "Delete all local chat history?"
        )
    ) {

        return;

    }


    localStorage.removeItem(
        "medai-history"
    );


    newChat();

    renderHistory();

}


// =========================================================
// REMINDERS
// =========================================================

function openReminders() {

    get(
        "reminderModal"
    ).classList.add(
        "show"
    );


    renderReminders();

}


function closeReminders() {

    get(
        "reminderModal"
    ).classList.remove(
        "show"
    );

}


function getReminders() {

    return JSON.parse(

        localStorage.getItem(
            "medai-reminders"
        ) || "[]"

    );

}


function saveReminders(
    reminders
) {

    localStorage.setItem(

        "medai-reminders",

        JSON.stringify(
            reminders
        )

    );

}


function addReminder() {

    const text =
        get(
            "reminderText"
        ).value.trim();


    const time =
        get(
            "reminderTime"
        ).value;


    if (
        !text ||
        !time
    ) {

        alert(
            "Reminder text and time are required."
        );

        return;

    }


    const reminders =
        getReminders();


    reminders.push({

        id:
            Date.now(),

        text:
            text,

        time:
            time,

        done:
            false

    });


    saveReminders(
        reminders
    );


    get(
        "reminderText"
    ).value =
        "";


    get(
        "reminderTime"
    ).value =
        "";


    renderReminders();

}


function renderReminders() {

    const box =
        get(
            "reminders"
        );


    box.innerHTML =
        "";


    const reminders =
        getReminders();


    if (
        reminders.length === 0
    ) {

        box.innerHTML =
            '<p class="notice">No reminders.</p>';

        return;

    }


    reminders.forEach(

        reminder => {

            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "reminder";


            const text =
                document.createElement(
                    "span"
                );


            text.textContent =
                reminder.text +
                " — " +
                new Date(
                    reminder.time
                ).toLocaleString();


            const button =
                document.createElement(
                    "button"
                );


            button.className =
                "small-button";


            button.textContent =
                "Delete";


            button.onclick =
                () => {

                    saveReminders(

                        getReminders()
                        .filter(
                            x =>
                                x.id !==
                                reminder.id
                        )

                    );


                    renderReminders();

                };


            row.append(
                text,
                button
            );


            box.appendChild(
                row
            );

        }

    );

}


// =========================================================
// REMINDER CHECK
// =========================================================

function checkReminders() {

    const reminders =
        getReminders();


    const now =
        Date.now();


    let changed =
        false;


    reminders.forEach(

        reminder => {

            if (

                !reminder.done &&

                new Date(
                    reminder.time
                ).getTime() <=
                now

            ) {

                reminder.done =
                    true;

                changed =
                    true;


                alert(
                    "⏰ Reminder: " +
                    reminder.text
                );

            }

        }

    );


    if (changed) {

        saveReminders(
            reminders
        );

    }


    setTimeout(
        checkReminders,
        30000
    );

}


// =========================================================
// TEXTAREA
// =========================================================

get(
    "message"
)
.addEventListener(

    "input",

    function () {

        this.style.height =
            "auto";


        this.style.height =
            Math.min(
                this.scrollHeight,
                180
            ) + "px";

    }

);


get(
    "message"
)
.addEventListener(

    "keydown",

    event => {

        if (

            event.key ===
            "Enter" &&

            !event.shiftKey

        ) {

            event.preventDefault();

            sendMessage();

        }

    }

);


// =========================================================
// LOAD
// =========================================================

function loadApp() {

    renderHistory();


    const saved =
        localStorage.getItem(
            "medai-current"
        );


    if (saved) {

        try {

            currentChat =
                JSON.parse(
                    saved
                );


            renderMessages();

        }

        catch (error) {

            console.log(error);

        }

    }


    checkReminders();

}


loadApp();


</script>


</body>

</html>
"""


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template_string(
        HTML
    )


# =========================================================
# HEALTH
# =========================================================

@app.route("/health")
def health():

    return jsonify({

        "status":
            "ok",

        "service":
            "MedAI"

    })


# =========================================================
# BUILD GEMINI CONTENT
# =========================================================

def build_contents(
    message,
    history,
    image,
    image_mime
):

    contents = []


    for item in history[-12:]:

        role =
            "user" if
            item.get("role") == "user"
            else "model"


        text =
            str(
                item.get(
                    "text",
                    ""
                )
            )[:6000]


        if text:

            contents.append({

                "role":
                    role,

                "parts": [

                    {
                        "text":
                            text
                    }

                ]

            })


    parts = [

        {

            "text":
                SYSTEM_PROMPT +
                "\n\nCurrent user message:\n" +
                message

        }

    ]


    if image:

        raw_image =
            image.split(
                ",",
                1
            )[1] if "," in image else image


        parts.append({

            "inline_data": {

                "mime_type":
                    image_mime or
                    "image/jpeg",

                "data":
                    raw_image

            }

        })


    contents.append({

        "role":
            "user",

        "parts":
            parts

    })


    return contents


# =========================================================
# CHAT API
# =========================================================

@app.route(
    "/api/chat",
    methods=["POST"]
)
def api_chat():

    if not GEMINI_API_KEY:

        return jsonify({

            "error":
                "GEMINI_API_KEY په Vercel Environment Variables کې نشته."

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


    history =
        data.get(
            "history",
            []
        )


    image =
        data.get(
            "image"
        )


    image_mime =
        data.get(
            "image_mime"
        )


    if not message and not image:

        return jsonify({

            "error":
                "پیغام یا تصویر ورکړئ."

        }), 400


    if not isinstance(
        history,
        list
    ):

        history = []


    try:

        payload = {

            "contents":
                build_contents(
                    message,
                    history,
                    image,
                    image_mime
                ),

            "generationConfig": {

                "temperature":
                    0.7,

                "maxOutputTokens":
                    4096

            }

        }


        response =
            requests.post(

                GEMINI_URL,

                params={

                    "key":
                        GEMINI_API_KEY

                },

                headers={

                    "Content-Type":
                        "application/json"

                },

                json=payload,

                timeout=60

            )


        if (
            response.status_code != 200
        ):

            try:

                details =
                    response.json()

            except Exception:

                details =
                    response.text[:1500]


            return jsonify({

                "error":
                    "Gemini API error",

                "status":
                    response.status_code,

                "details":
                    details

            }), 502


        result =
            response.json()


        candidates =
            result.get(
                "candidates",
                []
            )


        if not candidates:

            return jsonify({

                "error":
                    "Gemini هېڅ ځواب ورنه کړ.",

                "details":
                    result

            }), 502


        parts =
            candidates[0] \
            .get(
                "content",
                {}
            ) \
            .get(
                "parts",
                []
            )


        answer_parts = []


        for part in parts:

            if part.get("text"):

                answer_parts.append(
                    part["text"]
                )


        answer =
            "\n".join(
                answer_parts
            ).strip()


        if not answer:

            return jsonify({

                "error":
                    "Gemini خالي ځواب ورکړ."

            }), 502


        return jsonify({

            "answer":
                answer

        })


    except requests.exceptions.Timeout:

        return jsonify({

            "error":
                "Gemini ته د غوښتنې وخت ختم شو."

        }), 504


    except requests.exceptions.RequestException:

        return jsonify({

            "error":
                "Gemini سره اتصال ونه شو."

        }), 502


    except Exception as error:

        print(
            "MedAI ERROR:",
            repr(error)
        )


        return jsonify({

            "error":
                "Server error: " +
                str(error)

        }), 500


# =========================================================
# START
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
