from flask import Flask, request, jsonify, render_template_string
import os
import json
import base64
import urllib.request
import urllib.error
import time

app = Flask(__name__)

# =========================================================
# CONFIG
# =========================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# General AI
GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
).strip()

# Image generation
IMAGE_MODEL = os.environ.get(
    "IMAGE_MODEL",
    "gemini-3.1-flash-image"
).strip()

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/{model}:generateContent"
)

MAX_MESSAGE = 20000
MAX_HISTORY = 16

# Keep uploaded images reasonably small for serverless requests.
MAX_IMAGE_BYTES = 8 * 1024 * 1024


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are MedAI, a modern general-purpose AI assistant.

You should answer a wide variety of questions, similar to a
general AI assistant.

You can help with:

- General questions
- Education
- Science
- Mathematics
- Programming
- Coding
- Technology
- Business
- History
- Geography
- Writing
- Rewriting
- Translation
- Summaries
- Study help
- Creative writing
- Problem solving
- Everyday questions
- Medical and health information
- Image understanding

LANGUAGE:

If the user writes in Pashto, answer in Pashto.

If the user writes in Dari, answer in Dari.

If the user writes in English, answer in English.

If the user mixes languages, respond naturally.

CONVERSATION:

Use the conversation history when available.

Understand follow-up questions.

Do not unnecessarily repeat previous answers.

GENERAL BEHAVIOR:

Be helpful, natural and clear.

For simple questions, answer directly.

For complicated questions, use sections,
steps and examples.

Do not invent facts.

If you are uncertain, say so.

Do not claim to have done something you did not do.

CODING:

When asked for programming help, provide complete,
working code when appropriate.

Check code carefully for obvious syntax errors.

Never expose API keys or private secrets.

IMAGE UNDERSTANDING:

If an image is provided, inspect it carefully and
answer the user's question about the image.

Do not pretend to see details that are not actually
visible.

MEDICAL SAFETY:

You may provide general medical information.

You are not a replacement for a licensed doctor.

Do not claim a diagnosis with certainty.

If symptoms could indicate a serious emergency,
recommend urgent medical evaluation.

Do not recommend dangerous self-treatment.

For medication questions, explain that the correct
medicine and dosage depend on the individual,
condition, age, medical history and interactions.

EMERGENCY:

If a user describes a potentially life-threatening
situation, prioritize immediate safety and recommend
urgent emergency medical care.

STYLE:

Be friendly, respectful and concise when possible.

Use Markdown when useful.

Do not repeatedly say that you are an AI.

Product:
MedAI

Developer:
Toyebullah Dawoodzay

Year:
2026
"""


# =========================================================
# HELPERS
# =========================================================

def make_request(url, payload, timeout=90):
    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }
    )

    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8")

    return json.loads(raw)


def extract_text(data):
    try:
        candidates = data.get("candidates", [])

        if not candidates:
            return None

        content = candidates[0].get(
            "content",
            {}
        )

        parts = content.get(
            "parts",
            []
        )

        texts = []

        for part in parts:

            text = part.get("text")

            if isinstance(text, str):
                texts.append(text)

        answer = "".join(texts).strip()

        return answer or None

    except Exception:
        return None


def extract_images(data):
    images = []

    try:
        candidates = data.get("candidates", [])

        for candidate in candidates:

            content = candidate.get(
                "content",
                {}
            )

            parts = content.get(
                "parts",
                []
            )

            for part in parts:

                inline = part.get(
                    "inlineData"
                )

                if not inline:
                    inline = part.get(
                        "inline_data"
                    )

                if not inline:
                    continue

                image_data = inline.get(
                    "data"
                )

                mime_type = inline.get(
                    "mimeType"
                )

                if not mime_type:
                    mime_type = inline.get(
                        "mime_type"
                    )

                if image_data:

                    images.append({
                        "mime_type": mime_type or "image/png",
                        "data": image_data
                    })

    except Exception:
        pass

    return images


def clean_history(history):
    if not isinstance(history, list):
        return []

    result = []

    for item in history[-MAX_HISTORY:]:

        if not isinstance(item, dict):
            continue

        role = item.get("role")
        text = item.get("text")

        if role not in ("user", "model"):
            continue

        if not isinstance(text, str):
            continue

        text = text.strip()

        if not text:
            continue

        result.append({
            "role": role,
            "parts": [
                {
                    "text": text
                }
            ]
        })

    return result


def call_text_model(
    model,
    message,
    history,
    image_data=None,
    image_mime=None
):
    contents = clean_history(history)

    parts = []

    # Image first
    if image_data:

        parts.append({
            "inline_data": {
                "mime_type": image_mime or "image/jpeg",
                "data": image_data
            }
        })

    parts.append({
        "text": message
    })

    contents.append({
        "role": "user",
        "parts": parts
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

    url = GEMINI_URL.format(
        model=model
    )

    return make_request(
        url,
        payload,
        timeout=90
    )


# =========================================================
# CHAT WITH RETRIES
# =========================================================

def chat_with_retry(
    message,
    history,
    image_data=None,
    image_mime=None
):
    last_error = None

    # Use current model first, then a stable fallback.
    models = [
        GEMINI_MODEL,
        "gemini-3.7-flash",
        "gemini-3.5-flash"
    ]

    # Remove duplicates
    models = list(dict.fromkeys(models))

    for model in models:

        for attempt in range(4):

            try:

                result = call_text_model(
                    model=model,
                    message=message,
                    history=history,
                    image_data=image_data,
                    image_mime=image_mime
                )

                answer = extract_text(result)

                if answer:

                    return {
                        "reply": answer,
                        "model": model
                    }

                last_error = (
                    "Gemini returned an empty response."
                )

            except urllib.error.HTTPError as error:

                status = error.code

                try:
                    body = (
                        error.read()
                        .decode("utf-8")
                    )
                except Exception:
                    body = ""

                last_error = (
                    f"HTTP {status}: {body[:1200]}"
                )

                # Temporary errors
                if status in (
                    429,
                    500,
                    502,
                    503,
                    504
                ):

                    if attempt < 3:

                        time.sleep(
                            min(
                                2 ** attempt,
                                8
                            )
                        )

                        continue

                    # Move to next model
                    break

                # Invalid request / auth / permission
                return {
                    "error": (
                        f"Gemini API error "
                        f"HTTP {status}"
                    ),
                    "details": body[:1200]
                }

            except urllib.error.URLError as error:

                last_error = (
                    f"Network error: {error}"
                )

                if attempt < 3:

                    time.sleep(
                        min(
                            2 ** attempt,
                            8
                        )
                    )

                    continue

                break

            except Exception as error:

                last_error = str(error)
                break

    return {
        "error": (
            "Gemini service is temporarily "
            "unavailable."
        ),
        "details": last_error
    }


# =========================================================
# SECURITY
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
    ] = (
        "camera=(), "
        "microphone=(self), "
        "geolocation=()"
    )

    return response


# =========================================================
# FRONTEND
# =========================================================

HTML = r"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<meta name="theme-color"
      content="#0d0d0d">

<title>MedAI</title>

<style>

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    width: 100%;
    height: 100%;
}

body {

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Roboto,
        Arial,
        sans-serif;

    background: #ffffff;

    color: #171717;

    transition:
        background .2s,
        color .2s;
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

    display: flex;

    width: 100%;
    height: 100vh;

    overflow: hidden;
}


/* =====================================================
SIDEBAR
===================================================== */

.sidebar {

    width: 270px;

    background: #f7f7f8;

    border-right:
        1px solid #e5e5e5;

    display: flex;

    flex-direction: column;

    padding: 14px;

    flex-shrink: 0;

    transition: .2s;
}

.brand {

    display: flex;

    align-items: center;

    gap: 10px;

    padding: 8px 5px 18px;
}

.brand-logo {

    width: 38px;
    height: 38px;

    border-radius: 12px;

    background: #111111;

    color: #ffffff;

    display: flex;

    align-items: center;

    justify-content: center;

    font-weight: 800;

    font-size: 18px;
}

.brand-name {

    font-weight: 800;

    font-size: 19px;
}

.new-chat {

    width: 100%;

    padding: 11px 13px;

    background: #ffffff;

    border:
        1px solid #dddddd;

    border-radius: 10px;

    text-align: left;

    font-weight: 600;

    margin-bottom: 18px;
}

.new-chat:hover {

    background: #eeeeee;
}

.section-label {

    font-size: 11px;

    color: #777777;

    text-transform: uppercase;

    font-weight: 700;

    padding: 7px;
}

.history {

    flex: 1;

    overflow-y: auto;
}

.history-item {

    padding: 9px 10px;

    border-radius: 8px;

    font-size: 13px;

    white-space: nowrap;

    overflow: hidden;

    text-overflow: ellipsis;

    margin-bottom: 2px;
}

.history-item:hover {

    background: #e8e8e8;
}

.sidebar-bottom {

    border-top:
        1px solid #dddddd;

    padding-top: 10px;
}

.side-button {

    width: 100%;

    border: 0;

    background: transparent;

    text-align: left;

    padding: 10px;

    border-radius: 8px;
}

.side-button:hover {

    background: #e8e8e8;
}


/* =====================================================
MAIN
===================================================== */

.main {

    flex: 1;

    min-width: 0;

    display: flex;

    flex-direction: column;
}

.topbar {

    height: 60px;

    border-bottom:
        1px solid #eeeeee;

    display: flex;

    align-items: center;

    padding: 0 18px;

    gap: 12px;

    flex-shrink: 0;
}

.mobile-menu {

    display: none;

    border: 0;

    background: transparent;

    font-size: 23px;
}

.title {

    font-weight: 700;

    font-size: 15px;
}

.top-space {

    flex: 1;
}

.icon-button {

    border: 0;

    background: transparent;

    padding: 8px;

    border-radius: 8px;
}

.icon-button:hover {

    background: #eeeeee;
}


/* =====================================================
CHAT
===================================================== */

.chat {

    flex: 1;

    overflow-y: auto;

    padding:
        30px 20px 170px;
}

.chat-inner {

    max-width: 860px;

    margin: auto;
}

.welcome {

    min-height: 60vh;

    display: flex;

    align-items: center;

    justify-content: center;

    flex-direction: column;

    text-align: center;
}

.welcome-logo {

    width: 68px;

    height: 68px;

    border-radius: 20px;

    background: #111111;

    color: white;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 26px;

    font-weight: 800;

    margin-bottom: 20px;
}

.welcome h1 {

    font-size: 34px;

    margin:
        0 0 10px;
}

.welcome p {

    color: #777777;

    margin: 0;
}


/* =====================================================
MESSAGES
===================================================== */

.message {

    display: flex;

    gap: 12px;

    margin-bottom: 28px;
}

.avatar {

    width: 34px;
    height: 34px;

    flex: 0 0 34px;

    border-radius: 10px;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 12px;

    font-weight: 800;
}

.user .avatar {

    background: #eeeeee;
}

.ai .avatar {

    background: #111111;

    color: white;
}

.message-content {

    flex: 1;

    min-width: 0;
}

.message-name {

    font-size: 12px;

    font-weight: 700;

    margin-bottom: 5px;
}

.message-text {

    white-space: pre-wrap;

    line-height: 1.7;

    overflow-wrap: anywhere;
}

.message-image {

    max-width: 360px;

    width: 100%;

    border-radius: 12px;

    margin-bottom: 8px;

    border:
        1px solid #dddddd;
}

.copy-btn {

    border: 0;

    background: transparent;

    color: #777777;

    font-size: 12px;

    padding:
        5px 0;
}


/* =====================================================
TYPING
===================================================== */

.typing {

    display: flex;

    gap: 5px;

    padding: 8px 0;
}

.dot {

    width: 7px;

    height: 7px;

    border-radius: 50%;

    background: #999999;

    animation:
        blink 1.2s infinite;
}

.dot:nth-child(2) {

    animation-delay:
        .15s;
}

.dot:nth-child(3) {

    animation-delay:
        .3s;
}

@keyframes blink {

    0%, 80%, 100% {
        opacity: .25;
    }

    40% {
        opacity: 1;
    }
}


/* =====================================================
COMPOSER
===================================================== */

.input-area {

    position: fixed;

    left: 270px;

    right: 0;

    bottom: 0;

    padding:
        35px 20px 18px;

    background:
        linear-gradient(
            transparent,
            #ffffff 28%
        );
}

.input-inner {

    max-width: 860px;

    margin: auto;
}

.preview {

    display: none;

    position: relative;

    margin-bottom: 8px;
}

.preview img {

    max-height: 130px;

    max-width: 200px;

    border-radius: 10px;

    border:
        1px solid #dddddd;
}

.remove-image {

    position: absolute;

    top: -7px;

    left: 185px;

    width: 25px;

    height: 25px;

    border: 0;

    border-radius: 50%;

    background: #111111;

    color: #ffffff;
}

.composer {

    display: flex;

    align-items: flex-end;

    gap: 7px;

    padding: 8px;

    background: #ffffff;

    border:
        1px solid #d5d5d5;

    border-radius: 16px;

    box-shadow:
        0 8px 30px
        rgba(0,0,0,.08);
}

textarea {

    flex: 1;

    min-height: 42px;

    max-height: 180px;

    resize: none;

    border: 0;

    outline: 0;

    padding: 10px;

    line-height: 1.5;

    background: transparent;
}

.tool-button {

    width: 40px;

    height: 40px;

    border: 0;

    border-radius: 10px;

    background: #f1f1f1;
}

.tool-button:hover {

    background: #e5e5e5;
}

.send {

    background: #111111;

    color: white;
}

.disclaimer {

    text-align: center;

    font-size: 11px;

    color: #999999;

    margin-top: 7px;
}

.file-input {

    display: none;
}


/* =====================================================
DARK
===================================================== */

body.dark {

    background: #212121;

    color: #f5f5f5;
}

body.dark .sidebar {

    background: #171717;

    border-color: #333333;
}

body.dark .new-chat {

    background: #212121;

    color: white;

    border-color: #444444;
}

body.dark .history-item:hover,
body.dark .side-button:hover,
body.dark .icon-button:hover {

    background: #2d2d2d;
}

body.dark .sidebar-bottom {

    border-color: #333333;
}

body.dark .topbar {

    border-color: #333333;
}

body.dark .input-area {

    background:
        linear-gradient(
            transparent,
            #212121 28%
        );
}

body.dark .composer {

    background: #2b2b2b;

    border-color: #444444;
}

body.dark textarea {

    color: white;
}

body.dark .tool-button {

    background: #3a3a3a;

    color: white;
}

body.dark .welcome p {

    color: #999999;
}


/* =====================================================
MOBILE
===================================================== */

@media (max-width: 760px) {

    .sidebar {

        position: fixed;

        z-index: 100;

        left: -280px;

        top: 0;

        bottom: 0;

        box-shadow:
            10px 0 30px
            rgba(0,0,0,.15);
    }

    .sidebar.open {

        left: 0;
    }

    .mobile-menu {

        display: block;
    }

    .input-area {

        left: 0;

        padding:
            30px 9px 12px;
    }

    .chat {

        padding:
            20px 12px 150px;
    }

    .welcome h1 {

        font-size: 27px;
    }
}

</style>

</head>

<body>

<div class="app">

    <!-- SIDEBAR -->

    <aside class="sidebar" id="sidebar">

        <div class="brand">

            <div class="brand-logo">
                M
            </div>

            <div class="brand-name">
                MedAI
            </div>

        </div>

        <button
            class="new-chat"
            onclick="newChat()">

            ＋ New chat

        </button>

        <div class="section-label">
            Recent chats
        </div>

        <div
            class="history"
            id="history">
        </div>

        <div class="sidebar-bottom">

            <button
                class="side-button"
                onclick="toggleDark()">

                ◐ Dark mode

            </button>

            <button
                class="side-button"
                onclick="clearHistory()">

                🗑 Clear chats

            </button>

            <button
                class="side-button"
                onclick="about()">

                ℹ About

            </button>

        </div>

    </aside>


    <!-- MAIN -->

    <main class="main">

        <header class="topbar">

            <button
                class="mobile-menu"
                onclick="toggleSidebar()">

                ☰

            </button>

            <div class="title">
                MedAI
            </div>

            <div class="top-space"></div>

            <button
                class="icon-button"
                onclick="toggleDark()">

                ◐

            </button>

        </header>


        <!-- CHAT -->

        <section
            class="chat"
            id="chat">

            <div
                class="chat-inner"
                id="chatInner">

                <div
                    class="welcome"
                    id="welcome">

                    <div class="welcome-logo">
                        M
                    </div>

                    <h1>
                        How can I help you?
                    </h1>

                    <p>
                        Ask MedAI anything.
                    </p>

                </div>

            </div>

        </section>


        <!-- INPUT -->

        <div class="input-area">

            <div class="input-inner">

                <div
                    class="preview"
                    id="preview">

                    <img
                        id="previewImage"
                        src=""
                        alt="Selected image">

                    <button
                        class="remove-image"
                        onclick="removeImage()">

                        ×

                    </button>

                </div>


                <div class="composer">

                    <!-- IMAGE PICKER -->

                    <button
                        class="tool-button"
                        onclick="openImagePicker()"
                        title="Add image">

                        🖼️

                    </button>

                    <input
                        type="file"
                        id="imageInput"
                        class="file-input"
                        accept="image/png,image/jpeg,image/webp,image/gif"
                        onchange="selectImage(event)">


                    <!-- VOICE -->

                    <button
                        class="tool-button"
                        onclick="voiceInput()"
                        title="Voice">

                        🎙️

                    </button>


                    <!-- TEXT -->

                    <textarea
                        id="message"
                        rows="1"
                        placeholder="Message MedAI..."
                        onkeydown="handleKey(event)"
                        oninput="resizeText(this)">
                    </textarea>


                    <!-- SEND -->

                    <button
                        class="tool-button send"
                        id="sendButton"
                        onclick="sendMessage()">

                        ↑

                    </button>

                </div>

                <div class="disclaimer">

                    MedAI can make mistakes.
                    Check important information.

                </div>

            </div>

        </div>

    </main>

</div>


<script>

/* =====================================================
STATE
===================================================== */

let messages = [];

let selectedImage = null;

let conversations =
    JSON.parse(
        localStorage.getItem(
            "medai_chats"
        ) || "[]"
    );

let darkMode =
    localStorage.getItem(
        "medai_dark"
    ) === "true";


/* =====================================================
START
===================================================== */

if (darkMode) {

    document.body.classList.add(
        "dark"
    );
}

renderHistory();


/* =====================================================
SIDEBAR
===================================================== */

function toggleSidebar() {

    document
        .getElementById("sidebar")
        .classList.toggle("open");
}


/* =====================================================
DARK MODE
===================================================== */

function toggleDark() {

    darkMode = !darkMode;

    document.body.classList.toggle(
        "dark",
        darkMode
    );

    localStorage.setItem(
        "medai_dark",
        darkMode
    );
}


/* =====================================================
ABOUT
===================================================== */

function about() {

    alert(
        "MedAI\\n\\n" +
        "General-purpose AI assistant.\\n\\n" +
        "Developer: Toyebullah Dawoodzay\\n" +
        "2026"
    );
}


/* =====================================================
NEW CHAT
===================================================== */

function newChat() {

    messages = [];

    removeImage();

    document
        .getElementById("chatInner")
        .innerHTML = `

        <div
            class="welcome"
            id="welcome">

            <div class="welcome-logo">
                M
            </div>

            <h1>
                How can I help you?
            </h1>

            <p>
                Ask MedAI anything.
            </p>

        </div>
    `;

    document
        .getElementById("message")
        .focus();

    closeMobileSidebar();
}


/* =====================================================
IMAGE PICKER
===================================================== */

function openImagePicker() {

    document
        .getElementById("imageInput")
        .click();
}


function selectImage(event) {

    const file =
        event.target.files[0];

    if (!file) {
        return;
    }

    if (file.size > 8 * 1024 * 1024) {

        alert(
            "Image is too large. " +
            "Please select an image under 8 MB."
        );

        event.target.value = "";

        return;
    }

    if (!file.type.startsWith("image/")) {

        alert(
            "Please select an image file."
        );

        return;
    }

    selectedImage = file;

    const reader =
        new FileReader();

    reader.onload = function(e) {

        document
            .getElementById(
                "previewImage"
            )
            .src = e.target.result;

        document
            .getElementById(
                "preview"
            )
            .style.display = "block";
    };

    reader.readAsDataURL(file);
}


function removeImage() {

    selectedImage = null;

    const input =
        document.getElementById(
            "imageInput"
        );

    input.value = "";

    document
        .getElementById(
            "preview"
        )
        .style.display = "none";

    document
        .getElementById(
            "previewImage"
        )
        .src = "";
}


/* =====================================================
SEND
===================================================== */

async function sendMessage() {

    const textarea =
        document.getElementById(
            "message"
        );

    const text =
        textarea.value.trim();

    if (!text && !selectedImage) {
        return;
    }

    const oldHistory =
        [...messages];

    let imageToSend =
        selectedImage;

    let imagePreview =
        null;

    if (imageToSend) {

        imagePreview =
            await fileToDataURL(
                imageToSend
            );
    }

    textarea.value = "";

    textarea.style.height =
        "42px";

    removeImage();

    addMessage(
        "user",
        text ||
        "Please analyze this image.",
        imagePreview
    );

    const typingId =
        addTyping();

    document
        .getElementById(
            "sendButton"
        )
        .disabled = true;

    try {

        let imageBase64 = null;

        let imageMime = null;

        if (imageToSend) {

            const dataUrl =
                imagePreview;

            imageBase64 =
                dataUrl.split(",")[1];

            imageMime =
                imageToSend.type;
        }

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
                        message:
                            text ||
                            "Analyze this image.",
                        history:
                            oldHistory,
                        image:
                            imageBase64,
                        image_mime:
                            imageMime
                    })
                }
            );

        const data =
            await response.json();

        removeTyping(
            typingId
        );

        if (!response.ok) {

            addMessage(
                "ai",
                data.error ||
                "Something went wrong."
            );

            return;
        }

        addMessage(
            "ai",
            data.reply ||
            "I could not generate a response."
        );

        saveChat();

    } catch (error) {

        removeTyping(
            typingId
        );

        addMessage(
            "ai",
            "Connection error. Please try again."
        );

    } finally {

        document
            .getElementById(
                "sendButton"
            )
            .disabled = false;

        textarea.focus();
    }
}


/* =====================================================
FILE TO DATA URL
===================================================== */

function fileToDataURL(file) {

    return new Promise(
        (resolve, reject) => {

            const reader =
                new FileReader();

            reader.onload =
                () => resolve(
                    reader.result
                );

            reader.onerror =
                reject;

            reader.readAsDataURL(
                file
            );
        }
    );
}


/* =====================================================
ADD MESSAGE
===================================================== */

function addMessage(
    role,
    text,
    imageData = null
) {

    const welcome =
        document.getElementById(
            "welcome"
        );

    if (welcome) {
        welcome.remove();
    }

    const chatInner =
        document.getElementById(
            "chatInner"
        );

    const div =
        document.createElement(
            "div"
        );

    div.className =
        "message " + role;

    div.innerHTML = `

        <div class="avatar">
            ${role === "user" ? "U" : "M"}
        </div>

        <div class="message-content">

            <div class="message-name">
                ${role === "user" ? "You" : "MedAI"}
            </div>

            ${
                imageData
                ?
                `
                <img
                    class="message-image"
                    src="${imageData}"
                    alt="Uploaded image">
                `
                :
                ""
            }

            <div class="message-text"></div>

            ${
                role === "ai"
                ?
                `
                <button
                    class="copy-btn"
                    onclick="copyMessage(this)">
                    Copy
                </button>
                `
                :
                ""
            }

        </div>
    `;

    div.querySelector(
        ".message-text"
    ).textContent = text;

    chatInner.appendChild(
        div
    );

    messages.push({
        role:
            role === "user"
                ? "user"
                : "model",

        text: text
    });

    scrollBottom();
}


/* =====================================================
TYPING
===================================================== */

function addTyping() {

    const id =
        "typing-" +
        Date.now();

    const div =
        document.createElement(
            "div"
        );

    div.className =
        "message";

    div.id = id;

    div.innerHTML = `

        <div class="avatar">
            M
        </div>

        <div class="message-content">

            <div class="message-name">
                MedAI
            </div>

            <div class="typing">

                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>

            </div>

        </div>
    `;

    document
        .getElementById(
            "chatInner"
        )
        .appendChild(div);

    scrollBottom();

    return id;
}


function removeTyping(id) {

    const element =
        document.getElementById(
            id
        );

    if (element) {
        element.remove();
    }
}


/* =====================================================
COPY
===================================================== */

async function copyMessage(button) {

    const text =
        button
        .parentElement
        .querySelector(
            ".message-text"
        )
        .textContent;

    try {

        await navigator.clipboard.writeText(
            text
        );

        button.textContent =
            "Copied!";

        setTimeout(
            () => {
                button.textContent =
                    "Copy";
            },
            1200
        );

    } catch {

        button.textContent =
            "Copy failed";
    }
}


/* =====================================================
HISTORY
===================================================== */

function saveChat() {

    if (
        messages.length === 0
    ) {
        return;
    }

    const firstUser =
        messages.find(
            x => x.role === "user"
        );

    const title =
        firstUser
            ? firstUser.text
                .slice(0, 60)
            : "New chat";

    conversations.unshift({
        id: Date.now(),
        title: title,
        messages: [
            ...messages
        ]
    });

    conversations =
        conversations.slice(
            0,
            30
        );

    localStorage.setItem(
        "medai_chats",
        JSON.stringify(
            conversations
        )
    );

    renderHistory();
}


function renderHistory() {

    const container =
        document.getElementById(
            "history"
        );

    container.innerHTML = "";

    conversations.forEach(
        item => {

            const div =
                document.createElement(
                    "div"
                );

            div.className =
                "history-item";

            div.textContent =
                item.title;

            div.onclick =
                () => loadChat(item);

            container.appendChild(
                div
            );
        }
    );
}


function loadChat(item) {

    messages = [];

    document
        .getElementById(
            "chatInner"
        )
        .innerHTML = "";

    item.messages.forEach(
        message => {

            addMessage(
                message.role === "user"
                    ? "user"
                    : "ai",
                message.text
            );
        }
    );

    closeMobileSidebar();

    scrollBottom();
}


function clearHistory() {

    if (
        !confirm(
            "Clear all saved chats?"
        )
    ) {
        return;
    }

    conversations = [];

    localStorage.removeItem(
        "medai_chats"
    );

    renderHistory();

    newChat();
}


/* =====================================================
VOICE
===================================================== */

function voiceInput() {

    const Recognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!Recognition) {

        alert(
            "Voice input is not supported in this browser."
        );

        return;
    }

    const recognition =
        new Recognition();

    recognition.lang =
        "en-US";

    recognition.interimResults =
        false;

    recognition.maxAlternatives =
        1;

    recognition.onresult =
        function(event) {

            const result =
                event.results[0][0]
                    .transcript;

            const textarea =
                document.getElementById(
                    "message"
                );

            textarea.value +=
                (
                    textarea.value
                        ? " "
                        : ""
                ) + result;

            resizeText(
                textarea
            );
        };

    recognition.start();
}


/* =====================================================
TEXTAREA
===================================================== */

function resizeText(element) {

    element.style.height =
        "auto";

    element.style.height =
        Math.min(
            element.scrollHeight,
            180
        ) + "px";
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


/* =====================================================
SCROLL
===================================================== */

function scrollBottom() {

    const chat =
        document.getElementById(
            "chat"
        );

    setTimeout(
        () => {

            chat.scrollTo({
                top:
                    chat.scrollHeight,
                behavior:
                    "smooth"
            });

        },
        30
    );
}


/* =====================================================
MOBILE
===================================================== */

function closeMobileSidebar() {

    if (
        window.innerWidth <= 760
    ) {

        document
            .getElementById(
                "sidebar"
            )
            .classList.remove(
                "open"
            );
    }
}

</script>

</body>

</html>
"""


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return render_template_string(
        HTML
    )


# =========================================================
# HEALTH
# =========================================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "ok",
        "service": "MedAI",
        "chat_model": GEMINI_MODEL,
        "image_model": IMAGE_MODEL,
        "api_key_configured":
            bool(GEMINI_API_KEY)
    })


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
                "GEMINI_API_KEY is not configured."
        }), 500

    data =
        request.get_json(
            silent=True
        ) or {}

    message = str(
        data.get(
            "message",
            ""
        )
    ).strip()

    if not message:
        message = "Please analyze this image."

    if len(message) > MAX_MESSAGE:

        return jsonify({
            "error":
                "Message is too long."
        }), 400

    history =
        data.get(
            "history",
            []
        )

    image_data =
        data.get(
            "image"
        )

    image_mime =
        data.get(
            "image_mime"
        )

    # Validate image
    if image_data:

        if not isinstance(
            image_data,
            str
        ):

            return jsonify({
                "error":
                    "Invalid image data."
            }), 400

        try:

            raw_image =
                base64.b64decode(
                    image_data,
                    validate=True
                )

            if len(raw_image) > MAX_IMAGE_BYTES:

                return jsonify({
                    "error":
                        "Image is too large."
                }), 400

        except Exception:

            return jsonify({
                "error":
                    "Invalid image encoding."
            }), 400

        allowed_mime = {
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/gif"
        }

        if image_mime not in allowed_mime:

            return jsonify({
                "error":
                    "Unsupported image type."
            }), 400

    result = chat_with_retry(
        message=message,
        history=history,
        image_data=image_data,
        image_mime=image_mime
    )

    if result.get("reply"):

        return jsonify({
            "reply":
                result["reply"],
            "model":
                result.get(
                    "model",
                    GEMINI_MODEL
                )
        })

    return jsonify({
        "error":
            result.get(
                "error",
                "AI service error."
            ),
        "details":
            result.get(
                "details",
                ""
            )
    }), 503


# =========================================================
# CHAT ALIAS
# =========================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat_alias():

    return api_chat()


# =========================================================
# 404
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "error": "Not found"
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
                5000
            )
        ),
        debug=False
    )
