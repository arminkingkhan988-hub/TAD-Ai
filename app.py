import os
import base64
import requests

from flask import Flask, request, jsonify, render_template_string


# =========================================================
# MEDAI - FLASK APP
# =========================================================

app = Flask(__name__)

# -------------------------
# Configuration
# -------------------------

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    + GEMINI_MODEL
    + ":generateContent"
)

MAX_MESSAGE_LENGTH = 12000
MAX_HISTORY = 20
MAX_IMAGE_SIZE = 8 * 1024 * 1024


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are MedAI, a helpful general-purpose AI assistant.

You can answer questions about:
- General knowledge
- Education
- Science
- Mathematics
- Programming
- Technology
- Writing
- Translation
- History
- Business
- Everyday questions
- Medicine and health

LANGUAGE RULE:
Answer in the same language the user uses.
If the user writes Pashto, answer in Pashto.
If the user writes Dari, answer in Dari.
If the user writes English, answer in English.
If the user mixes languages, naturally match the user's language.

STYLE:
- Be clear and useful.
- Be friendly.
- Give direct answers.
- Use headings and bullet points when helpful.
- For coding questions, provide practical code.
- Do not unnecessarily repeat the question.
- If the question is unclear, ask a short clarification.

MEDICAL SAFETY:
For medical questions, provide general educational information.
Do not pretend to be a doctor.
Do not make a certain diagnosis from limited information.
For emergencies, tell the user to contact local emergency medical services or seek urgent medical care.
Mention important warning signs when appropriate.
Do not recommend dangerous medication use.
For medication dosage, consider age, weight, medical conditions, allergies,
other medicines, and local medical guidance.

IMAGE:
If an image is provided, analyze what can reasonably be observed.
For medical images, do not claim certainty or provide a definitive diagnosis.
Explain limitations and recommend professional medical evaluation when appropriate.

PRIVACY:
Do not ask for unnecessary personal information.
"""


# =========================================================
# HELPERS
# =========================================================

def clean_history(history):
    """Keep only safe, useful conversation history."""
    if not isinstance(history, list):
        return []

    cleaned = []

    for item in history[-MAX_HISTORY:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role", "user")
        text = item.get("text", "")

        if not isinstance(text, str):
            continue

        text = text.strip()

        if not text:
            continue

        if len(text) > MAX_MESSAGE_LENGTH:
            text = text[:MAX_MESSAGE_LENGTH]

        if role not in ("user", "assistant"):
            role = "user"

        cleaned.append({
            "role": role,
            "text": text
        })

    return cleaned


def build_prompt(message, history):
    parts = [SYSTEM_PROMPT]

    if history:
        parts.append("\nCONVERSATION HISTORY:")

        for item in history:
            role_name = "User" if item["role"] == "user" else "Assistant"
            parts.append(
                f"{role_name}: {item['text']}"
            )

    parts.append("\nCURRENT USER MESSAGE:")
    parts.append(message)

    return "\n\n".join(parts)


def call_gemini(message, history, image_data=None, mime_type=None):
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it in Vercel Environment Variables."
        )

    prompt = build_prompt(message, history)

    parts = [
        {
            "text": prompt
        }
    ]

    # Optional image
    if image_data:
        if not isinstance(image_data, str):
            raise ValueError("Invalid image data.")

        if len(image_data) > MAX_IMAGE_SIZE * 2:
            raise ValueError("Image is too large.")

        try:
            # Accept either raw base64 or data:image/...;base64,...
            if "," in image_data and image_data.startswith("data:"):
                image_data = image_data.split(",", 1)[1]

            # Validate base64
            base64.b64decode(image_data, validate=True)

        except Exception:
            raise ValueError("Invalid image format.")

        parts.append(
            {
                "inline_data": {
                    "mime_type": mime_type or "image/jpeg",
                    "data": image_data
                }
            }
        )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": parts
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(
        GEMINI_URL,
        headers=headers,
        params={
            "key": GEMINI_API_KEY
        },
        json=payload,
        timeout=55
    )

    if response.status_code != 200:
        try:
            error_data = response.json()
        except Exception:
            error_data = response.text

        raise RuntimeError(
            f"Gemini API error. HTTP {response.status_code}: {error_data}"
        )

    data = response.json()

    candidates = data.get("candidates", [])

    if not candidates:
        raise RuntimeError("Gemini returned no response.")

    candidate = candidates[0]

    content = candidate.get("content", {})
    response_parts = content.get("parts", [])

    texts = []

    for part in response_parts:
        text = part.get("text")

        if isinstance(text, str):
            texts.append(text)

    answer = "\n".join(texts).strip()

    if not answer:
        raise RuntimeError("Gemini returned an empty answer.")

    return answer


# =========================================================
# SECURITY HEADERS
# =========================================================

@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# =========================================================
# HOME PAGE
# =========================================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>MedAI</title>

<style>

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    padding: 0;
    height: 100%;
    font-family:
        Inter,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Arial,
        sans-serif;
}

body {
    background: #ffffff;
    color: #171717;
    overflow: hidden;
}

button,
textarea,
input {
    font: inherit;
}

button {
    cursor: pointer;
}


/* =====================================================
   APP
   ===================================================== */

.app {
    display: flex;
    height: 100vh;
    width: 100%;
}


/* =====================================================
   SIDEBAR
   ===================================================== */

.sidebar {
    width: 270px;
    background: #f7f7f8;
    border-right: 1px solid #e5e5e5;
    display: flex;
    flex-direction: column;
    padding: 14px;
    transition: transform 0.25s ease;
}

.brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 7px 18px;
}

.brand-icon {
    width: 36px;
    height: 36px;
    border-radius: 12px;
    background: #111827;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
}

.brand-name {
    font-size: 18px;
    font-weight: 700;
}

.new-chat {
    border: 1px solid #dedede;
    background: white;
    border-radius: 12px;
    padding: 11px 13px;
    text-align: left;
    display: flex;
    gap: 10px;
    align-items: center;
    margin-bottom: 15px;
}

.new-chat:hover {
    background: #eeeeee;
}

.sidebar-title {
    font-size: 12px;
    color: #777;
    padding: 8px;
}

.history {
    flex: 1;
    overflow-y: auto;
}

.history-item {
    padding: 10px;
    border-radius: 9px;
    cursor: pointer;
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.history-item:hover {
    background: #e9e9e9;
}

.sidebar-bottom {
    border-top: 1px solid #ddd;
    padding-top: 10px;
}

.theme-btn {
    width: 100%;
    border: 0;
    background: transparent;
    padding: 10px;
    text-align: left;
    border-radius: 9px;
}

.theme-btn:hover {
    background: #e9e9e9;
}


/* =====================================================
   MAIN
   ===================================================== */

.main {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.topbar {
    height: 58px;
    display: flex;
    align-items: center;
    padding: 0 18px;
    border-bottom: 1px solid #eeeeee;
    gap: 12px;
}

.menu-btn {
    display: none;
    border: 0;
    background: transparent;
    font-size: 23px;
}

.model-name {
    font-weight: 600;
}

.status {
    margin-left: auto;
    color: #666;
    font-size: 13px;
}


/* =====================================================
   CHAT
   ===================================================== */

.chat {
    flex: 1;
    overflow-y: auto;
    padding: 28px 20px 170px;
}

.chat-inner {
    width: min(900px, 100%);
    margin: auto;
}

.welcome {
    min-height: 65vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
}

.welcome-icon {
    width: 62px;
    height: 62px;
    background: #111827;
    color: white;
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 27px;
    margin-bottom: 18px;
}

.welcome h1 {
    font-size: 30px;
    margin: 0 0 10px;
}

.welcome p {
    color: #707070;
    margin: 0;
}


/* =====================================================
   MESSAGES
   ===================================================== */

.message {
    display: flex;
    gap: 12px;
    margin: 0 auto 25px;
    line-height: 1.65;
}

.avatar {
    width: 34px;
    height: 34px;
    flex: 0 0 34px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
}

.user .avatar {
    background: #e8e8e8;
    color: #333;
}

.assistant .avatar {
    background: #111827;
    color: white;
}

.message-body {
    flex: 1;
    min-width: 0;
}

.message-role {
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 3px;
}

.message-text {
    white-space: pre-wrap;
    word-break: break-word;
}

.message-image {
    max-width: min(500px, 100%);
    border-radius: 12px;
    margin-top: 8px;
    border: 1px solid #ddd;
}


/* =====================================================
   THINKING
   ===================================================== */

.thinking {
    display: flex;
    gap: 5px;
    align-items: center;
    height: 25px;
}

.dot {
    width: 7px;
    height: 7px;
    background: #888;
    border-radius: 50%;
    animation: bounce 1.1s infinite;
}

.dot:nth-child(2) {
    animation-delay: 0.15s;
}

.dot:nth-child(3) {
    animation-delay: 0.3s;
}

@keyframes bounce {
    0%, 60%, 100% {
        transform: translateY(0);
    }

    30% {
        transform: translateY(-5px);
    }
}


/* =====================================================
   COMPOSER
   ===================================================== */

.composer-area {
    position: fixed;
    bottom: 0;
    left: 270px;
    right: 0;
    padding: 18px 20px 22px;
    background:
        linear-gradient(
            to top,
            rgba(255,255,255,1) 65%,
            rgba(255,255,255,0)
        );
}

.composer {
    width: min(900px, 100%);
    margin: auto;
    border: 1px solid #d8d8d8;
    background: white;
    border-radius: 18px;
    box-shadow: 0 5px 25px rgba(0,0,0,0.08);
    padding: 10px;
}

.preview {
    display: none;
    position: relative;
    padding: 6px;
}

.preview img {
    width: 90px;
    height: 90px;
    object-fit: cover;
    border-radius: 12px;
}

.remove-image {
    position: absolute;
    top: 0;
    left: 85px;
    width: 25px;
    height: 25px;
    border-radius: 50%;
    border: 0;
    background: #111;
    color: white;
}

.input-row {
    display: flex;
    align-items: flex-end;
    gap: 8px;
}

textarea {
    flex: 1;
    resize: none;
    min-height: 45px;
    max-height: 180px;
    border: 0;
    outline: 0;
    padding: 12px;
    background: transparent;
}

.icon-btn,
.send-btn {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    border: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}

.icon-btn {
    background: transparent;
}

.icon-btn:hover {
    background: #eeeeee;
}

.send-btn {
    background: #111827;
    color: white;
}

.send-btn:disabled {
    opacity: 0.4;
}

.hint {
    text-align: center;
    color: #888;
    font-size: 11px;
    margin-top: 8px;
}


/* =====================================================
   DARK MODE
   ===================================================== */

body.dark {
    background: #212121;
    color: #f3f3f3;
}

body.dark .sidebar {
    background: #171717;
    border-color: #333;
}

body.dark .topbar {
    border-color: #333;
}

body.dark .new-chat,
body.dark .composer {
    background: #2b2b2b;
    border-color: #444;
    color: #fff;
}

body.dark textarea {
    color: white;
}

body.dark .composer-area {
    background:
        linear-gradient(
            to top,
            rgba(33,33,33,1) 65%,
            rgba(33,33,33,0)
        );
}

body.dark .user .avatar {
    background: #444;
    color: white;
}

body.dark .history-item:hover,
body.dark .theme-btn:hover,
body.dark .icon-btn:hover {
    background: #303030;
}

body.dark .welcome p,
body.dark .status {
    color: #aaa;
}


/* =====================================================
   MOBILE
   ===================================================== */

@media (max-width: 750px) {

    .sidebar {
        position: fixed;
        z-index: 50;
        top: 0;
        bottom: 0;
        left: 0;
        transform: translateX(-100%);
        box-shadow: 5px 0 25px rgba(0,0,0,.15);
    }

    .sidebar.open {
        transform: translateX(0);
    }

    .menu-btn {
        display: block;
    }

    .composer-area {
        left: 0;
        padding: 10px 10px 14px;
    }

    .chat {
        padding-left: 12px;
        padding-right: 12px;
    }

    .welcome h1 {
        font-size: 25px;
    }

}

</style>
</head>


<body>

<div class="app">

    <aside class="sidebar" id="sidebar">

        <div class="brand">
            <div class="brand-icon">M</div>
            <div class="brand-name">MedAI</div>
        </div>

        <button class="new-chat" onclick="newChat()">
            <span>＋</span>
            <span>New chat</span>
        </button>

        <div class="sidebar-title">
            Recent chats
        </div>

        <div class="history" id="historyList"></div>

        <div class="sidebar-bottom">
            <button class="theme-btn" onclick="toggleTheme()">
                🌓 Theme
            </button>
        </div>

    </aside>


    <main class="main">

        <header class="topbar">

            <button class="menu-btn" onclick="toggleSidebar()">
                ☰
            </button>

            <div class="model-name">
                MedAI
            </div>

            <div class="status" id="status">
                Online
            </div>

        </header>


        <section class="chat" id="chat">

            <div class="chat-inner" id="chatInner">

                <div class="welcome" id="welcome">

                    <div class="welcome-icon">
                        ✦
                    </div>

                    <h1>How can I help you?</h1>

                    <p>
                        Ask anything — education, coding, science, health, writing and more.
                    </p>

                </div>

            </div>

        </section>

    </main>


    <div class="composer-area">

        <div class="composer">

            <div class="preview" id="preview">

                <img id="previewImage" alt="Selected image">

                <button
                    class="remove-image"
                    onclick="removeImage()">
                    ×
                </button>

            </div>


            <div class="input-row">

                <input
                    type="file"
                    id="imageInput"
                    accept="image/*"
                    hidden
                >

                <button
                    class="icon-btn"
                    onclick="document.getElementById('imageInput').click()"
                    title="Upload image">
                    📎
                </button>

                <textarea
                    id="messageInput"
                    rows="1"
                    placeholder="Message MedAI..."
                    oninput="autoResize(this)"
                    onkeydown="handleKey(event)"
                ></textarea>

                <button
                    class="icon-btn"
                    onclick="startVoice()"
                    title="Voice input">
                    🎤
                </button>

                <button
                    class="send-btn"
                    id="sendBtn"
                    onclick="sendMessage()">
                    ↑
                </button>

            </div>

            <div class="hint">
                MedAI can make mistakes. Check important information.
            </div>

        </div>

    </div>

</div>


<script>

let messages = [];
let selectedImage = null;


/* =====================================================
   LOCAL STORAGE
   ===================================================== */

function saveCurrentChat() {
    localStorage.setItem(
        "medai_current_chat",
        JSON.stringify(messages)
    );

    updateHistory();
}


function loadCurrentChat() {

    try {

        const saved = localStorage.getItem(
            "medai_current_chat"
        );

        if (!saved) {
            return;
        }

        const data = JSON.parse(saved);

        if (!Array.isArray(data)) {
            return;
        }

        messages = data;

        if (messages.length > 0) {
            document.getElementById("welcome").style.display = "none";
        }

        for (const message of messages) {
            renderMessage(
                message.role,
                message.text,
                message.image
            );
        }

    } catch (error) {
        console.error(error);
    }
}


function updateHistory() {

    const historyList =
        document.getElementById("historyList");

    historyList.innerHTML = "";

    if (!messages.length) {
        return;
    }

    const title =
        messages.find(x => x.role === "user");

    const item =
        document.createElement("div");

    item.className = "history-item";

    item.textContent =
        title
        ? title.text.slice(0, 45)
        : "New chat";

    item.onclick = () => {
        document.getElementById("chat").scrollTop = 0;
    };

    historyList.appendChild(item);
}


/* =====================================================
   NEW CHAT
   ===================================================== */

function newChat() {

    messages = [];

    localStorage.removeItem(
        "medai_current_chat"
    );

    const inner =
        document.getElementById("chatInner");

    inner.innerHTML = `
        <div class="welcome" id="welcome">

            <div class="welcome-icon">
                ✦
            </div>

            <h1>How can I help you?</h1>

            <p>
                Ask anything — education, coding, science, health, writing and more.
            </p>

        </div>
    `;

    removeImage();
}


/* =====================================================
   MESSAGE RENDER
   ===================================================== */

function renderMessage(role, text, image) {

    const welcome =
        document.getElementById("welcome");

    if (welcome) {
        welcome.style.display = "none";
    }

    const container =
        document.getElementById("chatInner");

    const message =
        document.createElement("div");

    message.className =
        "message " + role;

    const avatar =
        document.createElement("div");

    avatar.className = "avatar";

    avatar.textContent =
        role === "user" ? "You" : "M";

    const body =
        document.createElement("div");

    body.className = "message-body";

    const roleName =
        document.createElement("div");

    roleName.className = "message-role";

    roleName.textContent =
        role === "user" ? "You" : "MedAI";

    const textElement =
        document.createElement("div");

    textElement.className = "message-text";

    textElement.textContent = text || "";

    body.appendChild(roleName);

    if (image) {

        const imageElement =
            document.createElement("img");

        imageElement.className =
            "message-image";

        imageElement.src = image;

        imageElement.alt =
            "Uploaded image";

        body.appendChild(imageElement);
    }

    body.appendChild(textElement);

    message.appendChild(avatar);
    message.appendChild(body);

    container.appendChild(message);

    scrollToBottom();
}


function addThinking() {

    const container =
        document.getElementById("chatInner");

    const message =
        document.createElement("div");

    message.className =
        "message assistant";

    message.id = "thinkingMessage";

    message.innerHTML = `
        <div class="avatar">M</div>

        <div class="message-body">

            <div class="message-role">
                MedAI
            </div>

            <div class="thinking">

                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>

            </div>

        </div>
    `;

    container.appendChild(message);

    scrollToBottom();
}


function removeThinking() {

    const thinking =
        document.getElementById("thinkingMessage");

    if (thinking) {
        thinking.remove();
    }
}


/* =====================================================
   SEND MESSAGE
   ===================================================== */

async function sendMessage() {

    const input =
        document.getElementById("messageInput");

    const sendBtn =
        document.getElementById("sendBtn");

    const text =
        input.value.trim();

    if (!text && !selectedImage) {
        return;
    }

    const imageForUI =
        selectedImage
        ? selectedImage.dataUrl
        : null;

    messages.push({
        role: "user",
        text: text || "Please analyze this image.",
        image: imageForUI
    });

    renderMessage(
        "user",
        text || "Please analyze this image.",
        imageForUI
    );

    saveCurrentChat();

    input.value = "";

    autoResize(input);

    sendBtn.disabled = true;

    addThinking();

    document.getElementById("status").textContent =
        "Thinking...";

    try {

        const history =
            messages.slice(0, -1).map(item => ({
                role: item.role,
                text: item.text
            }));

        const payload = {
            message:
                text || "Please analyze this image.",
            history: history
        };

        if (selectedImage) {

            payload.image =
                selectedImage.base64;

            payload.mime_type =
                selectedImage.mimeType;
        }

        const response =
            await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

        const data =
            await response.json();

        removeThinking();

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Server error"
            );
        }

        messages.push({
            role: "assistant",
            text: data.answer
        });

        renderMessage(
            "assistant",
            data.answer,
            null
        );

        saveCurrentChat();

        document.getElementById("status").textContent =
            "Online";

    } catch (error) {

        removeThinking();

        const errorText =
            "Sorry, something went wrong.\n\n" +
            error.message;

        messages.push({
            role: "assistant",
            text: errorText
        });

        renderMessage(
            "assistant",
            errorText,
            null
        );

        saveCurrentChat();

        document.getElementById("status").textContent =
            "Error";

    } finally {

        sendBtn.disabled = false;

        input.focus();
    }
}


/* =====================================================
   IMAGE PICKER
   ===================================================== */

document
    .getElementById("imageInput")
    .addEventListener("change", function(event) {

        const file =
            event.target.files[0];

        if (!file) {
            return;
        }

        if (!file.type.startsWith("image/")) {

            alert("Please select an image.");

            return;
        }

        if (file.size > 8 * 1024 * 1024) {

            alert(
                "Image must be smaller than 8 MB."
            );

            return;
        }

        const reader =
            new FileReader();

        reader.onload = function(e) {

            const dataUrl =
                e.target.result;

            const base64 =
                dataUrl.split(",")[1];

            selectedImage = {
                dataUrl: dataUrl,
                base64: base64,
                mimeType: file.type
            };

            document.getElementById(
                "previewImage"
            ).src = dataUrl;

            document.getElementById(
                "preview"
            ).style.display = "block";
        };

        reader.readAsDataURL(file);
    });


function removeImage() {

    selectedImage = null;

    document.getElementById(
        "imageInput"
    ).value = "";

    document.getElementById(
        "preview"
    ).style.display = "none";
}


/* =====================================================
   VOICE INPUT
   ===================================================== */

function startVoice() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {

        alert(
            "Voice input is not supported in this browser."
        );

        return;
    }

    const recognition =
        new SpeechRecognition();

    recognition.lang = "ps-AF";

    recognition.interimResults = true;

    recognition.continuous = false;

    recognition.onresult = function(event) {

        let transcript = "";

        for (
            let i = event.resultIndex;
            i < event.results.length;
            i++
        ) {
            transcript +=
                event.results[i][0].transcript;
        }

        document.getElementById(
            "messageInput"
        ).value = transcript;

        autoResize(
            document.getElementById("messageInput")
        );
    };

    recognition.onerror = function() {

        alert(
            "Voice input could not be started."
        );
    };

    recognition.start();
}


/* =====================================================
   TEXT TO SPEECH
   ===================================================== */

function speakText(text) {

    if (!("speechSynthesis" in window)) {
        return;
    }

    window.speechSynthesis.cancel();

    const utterance =
        new SpeechSynthesisUtterance(text);

    utterance.lang = "ps-AF";

    utterance.rate = 0.95;

    window.speechSynthesis.speak(
        utterance
    );
}


/* =====================================================
   KEYBOARD
   ===================================================== */

function handleKey(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();
    }
}


function autoResize(element) {

    element.style.height = "auto";

    element.style.height =
        Math.min(
            element.scrollHeight,
            180
        ) + "px";
}


/* =====================================================
   SCROLL
   ===================================================== */

function scrollToBottom() {

    const chat =
        document.getElementById("chat");

    setTimeout(() => {

        chat.scrollTo({
            top: chat.scrollHeight,
            behavior: "smooth"
        });

    }, 50);
}


/* =====================================================
   SIDEBAR
   ===================================================== */

function toggleSidebar() {

    document
        .getElementById("sidebar")
        .classList.toggle("open");
}


/* =====================================================
   THEME
   ===================================================== */

function toggleTheme() {

    document.body.classList.toggle("dark");

    localStorage.setItem(
        "medai_dark",
        document.body.classList.contains("dark")
    );
}


function loadTheme() {

    const dark =
        localStorage.getItem("medai_dark");

    if (dark === "true") {
        document.body.classList.add("dark");
    }
}


/* =====================================================
   START
   ===================================================== */

loadTheme();

loadCurrentChat();

updateHistory();

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


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "MedAI",
        "model": GEMINI_MODEL,
        "api_key_configured": bool(GEMINI_API_KEY)
    })


@app.route("/api/chat", methods=["POST"])
def api_chat():

    try:

        data = request.get_json(silent=True) or {}

        message = data.get("message", "")

        if not isinstance(message, str):
            message = ""

        message = message.strip()

        if len(message) > MAX_MESSAGE_LENGTH:
            return jsonify({
                "error": "Message is too long."
            }), 400

        history = clean_history(
            data.get("history", [])
        )

        image_data = data.get("image")

        mime_type = data.get(
            "mime_type",
            "image/jpeg"
        )

        if not message and not image_data:
            return jsonify({
                "error": "Please enter a message or upload an image."
            }), 400

        answer = call_gemini(
            message=message,
            history=history,
            image_data=image_data,
            mime_type=mime_type
        )

        return jsonify({
            "answer": answer
        })

    except ValueError as error:

        return jsonify({
            "error": str(error)
        }), 400

    except requests.exceptions.Timeout:

        return jsonify({
            "error": "Gemini request timed out. Please try again."
        }), 504

    except requests.exceptions.RequestException as error:

        return jsonify({
            "error": "Could not connect to Gemini.",
            "details": str(error)
        }), 502

    except Exception as error:

        print("MedAI error:", repr(error))

        return jsonify({
            "error": str(error)
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not found"
    }), 404


# =========================================================
# LOCAL DEVELOPMENT
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
