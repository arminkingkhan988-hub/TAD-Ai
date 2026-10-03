import os
import base64
import requests

from flask import Flask, request, jsonify, render_template_string


# =========================================================
# APP
# =========================================================

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
).strip()

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
- Coding
- Technology
- Writing
- Translation
- History
- Business
- Medicine and health
- Image understanding

Language rules:
- Reply in the same language as the user.
- If the user writes Pashto, answer in Pashto.
- If the user writes Dari/Persian, answer in Dari/Persian.
- If the user writes English, answer in English.
- You can understand mixed languages.

Answer clearly and naturally.
Do not unnecessarily repeat the user's question.

For medical questions:
- Give general educational information.
- Do not pretend to be a doctor.
- Do not provide dangerous or unnecessarily specific instructions.
- For emergencies, advise the user to contact local emergency medical services or a qualified healthcare professional.

For images:
- Analyze the image when an image is provided.
- Describe visible information carefully.
- If something cannot be determined from the image, say so.
"""


# =========================================================
# HTML / FRONTEND
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
    width: 100%;
    height: 100%;
    font-family:
        Inter,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}

body {
    background: #ffffff;
    color: #111827;
    overflow: hidden;
}

body.dark {
    background: #212121;
    color: #f5f5f5;
}


/* =========================================================
   APP
   ========================================================= */

.app {
    display: flex;
    width: 100%;
    height: 100vh;
}


/* =========================================================
   SIDEBAR
   ========================================================= */

.sidebar {
    width: 270px;
    height: 100vh;
    background: #f7f7f8;
    border-right: 1px solid #e5e7eb;
    display: flex;
    flex-direction: column;
    padding: 14px;
}

.dark .sidebar {
    background: #171717;
    border-color: #303030;
}

.logo {
    font-size: 21px;
    font-weight: 700;
    padding: 12px 10px 18px;
}

.new-chat {
    width: 100%;
    border: 1px solid #d1d5db;
    background: white;
    border-radius: 10px;
    padding: 12px;
    cursor: pointer;
    font-size: 15px;
    text-align: left;
}

.dark .new-chat {
    background: #212121;
    color: white;
    border-color: #444;
}

.new-chat:hover {
    background: #eeeeee;
}

.dark .new-chat:hover {
    background: #2b2b2b;
}

.sidebar-title {
    margin: 24px 10px 8px;
    font-size: 12px;
    color: #777;
    text-transform: uppercase;
}

.chat-history {
    flex: 1;
    overflow-y: auto;
}

.history-item {
    padding: 10px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.history-item:hover {
    background: #e9e9e9;
}

.dark .history-item:hover {
    background: #292929;
}

.sidebar-bottom {
    display: flex;
    gap: 8px;
}

.sidebar-button {
    flex: 1;
    border: 1px solid #ddd;
    background: white;
    border-radius: 8px;
    padding: 9px;
    cursor: pointer;
}

.dark .sidebar-button {
    background: #222;
    color: white;
    border-color: #444;
}


/* =========================================================
   MAIN
   ========================================================= */

.main {
    flex: 1;
    height: 100vh;
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.topbar {
    height: 58px;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    align-items: center;
    padding: 0 18px;
    gap: 12px;
}

.dark .topbar {
    border-color: #333;
}

.mobile-menu {
    display: none;
    border: none;
    background: transparent;
    font-size: 22px;
    cursor: pointer;
    color: inherit;
}

.model-name {
    font-weight: 600;
}


/* =========================================================
   CHAT
   ========================================================= */

.chat {
    flex: 1;
    overflow-y: auto;
    padding: 28px 20px 160px;
}

.messages {
    max-width: 850px;
    margin: auto;
}

.message {
    display: flex;
    gap: 12px;
    margin: 22px 0;
}

.avatar {
    width: 34px;
    height: 34px;
    min-width: 34px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 700;
}

.user-avatar {
    background: #111827;
    color: white;
}

.ai-avatar {
    background: #10a37f;
    color: white;
}

.message-content {
    flex: 1;
    line-height: 1.7;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}

.welcome {
    text-align: center;
    margin-top: 16vh;
}

.welcome h1 {
    font-size: 34px;
    margin-bottom: 8px;
}

.welcome p {
    color: #777;
}


/* =========================================================
   THINKING
   ========================================================= */

.thinking {
    display: inline-flex;
    gap: 5px;
    padding: 8px 0;
}

.thinking span {
    width: 7px;
    height: 7px;
    background: #888;
    border-radius: 50%;
    animation: blink 1.3s infinite;
}

.thinking span:nth-child(2) {
    animation-delay: .2s;
}

.thinking span:nth-child(3) {
    animation-delay: .4s;
}

@keyframes blink {
    0%, 80%, 100% {
        opacity: .25;
    }

    40% {
        opacity: 1;
    }
}


/* =========================================================
   COMPOSER
   ========================================================= */

.composer-area {
    position: fixed;
    left: 270px;
    right: 0;
    bottom: 0;
    padding: 18px 20px 20px;
    background: linear-gradient(
        transparent,
        rgba(255,255,255,.96) 25%
    );
}

.dark .composer-area {
    background: linear-gradient(
        transparent,
        rgba(33,33,33,.96) 25%
    );
}

.composer {
    max-width: 850px;
    margin: auto;
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 16px;
    padding: 10px;
    box-shadow: 0 4px 20px rgba(0,0,0,.08);
}

.dark .composer {
    background: #2b2b2b;
    border-color: #444;
}

.input-row {
    display: flex;
    align-items: flex-end;
    gap: 8px;
}

textarea {
    flex: 1;
    resize: none;
    border: none;
    outline: none;
    background: transparent;
    color: inherit;
    font-size: 16px;
    line-height: 1.5;
    min-height: 42px;
    max-height: 180px;
    padding: 8px;
}

.icon-button {
    width: 42px;
    height: 42px;
    border: none;
    background: transparent;
    border-radius: 9px;
    cursor: pointer;
    font-size: 20px;
    color: inherit;
}

.icon-button:hover {
    background: #eee;
}

.dark .icon-button:hover {
    background: #444;
}

.send-button {
    width: 42px;
    height: 42px;
    border: none;
    background: #111827;
    color: white;
    border-radius: 10px;
    cursor: pointer;
    font-size: 18px;
}

.send-button:disabled {
    opacity: .4;
    cursor: not-allowed;
}


/* =========================================================
   IMAGE PREVIEW
   ========================================================= */

.preview {
    display: none;
    position: relative;
    margin: 5px 8px 10px;
}

.preview img {
    width: 100px;
    height: 100px;
    object-fit: cover;
    border-radius: 10px;
    border: 1px solid #ddd;
}

.remove-image {
    position: absolute;
    left: 88px;
    top: -7px;
    width: 24px;
    height: 24px;
    border: none;
    border-radius: 50%;
    background: #111;
    color: white;
    cursor: pointer;
}


/* =========================================================
   MOBILE
   ========================================================= */

@media (max-width: 760px) {

    .sidebar {
        position: fixed;
        z-index: 100;
        left: -280px;
        top: 0;
        transition: left .2s;
    }

    .sidebar.open {
        left: 0;
    }

    .mobile-menu {
        display: block;
    }

    .composer-area {
        left: 0;
        padding: 10px;
    }

    .chat {
        padding-left: 12px;
        padding-right: 12px;
    }

    .welcome h1 {
        font-size: 28px;
    }

}

</style>
</head>


<body>

<div class="app">

    <aside class="sidebar" id="sidebar">

        <div class="logo">
            🩺 MedAI
        </div>

        <button
            class="new-chat"
            onclick="newChat()"
        >
            ＋ New chat
        </button>

        <div class="sidebar-title">
            Recent chats
        </div>

        <div
            class="chat-history"
            id="chatHistory"
        ></div>

        <div class="sidebar-bottom">

            <button
                class="sidebar-button"
                onclick="toggleTheme()"
            >
                🌙 Theme
            </button>

            <button
                class="sidebar-button"
                onclick="clearHistory()"
            >
                🗑 Clear
            </button>

        </div>

    </aside>


    <main class="main">

        <header class="topbar">

            <button
                class="mobile-menu"
                onclick="toggleSidebar()"
            >
                ☰
            </button>

            <div class="model-name">
                MedAI
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
                        Ask anything — in Pashto, Dari, or English.
                    </p>

                </div>

            </div>

        </section>


        <div class="composer-area">

            <div class="composer">

                <div
                    class="preview"
                    id="preview"
                >

                    <img
                        id="previewImage"
                        alt="Preview"
                    >

                    <button
                        class="remove-image"
                        onclick="removeImage()"
                    >
                        ×
                    </button>

                </div>


                <div class="input-row">

                    <button
                        class="icon-button"
                        onclick="document.getElementById('imageInput').click()"
                        title="Upload image"
                    >
                        📎
                    </button>

                    <input
                        id="imageInput"
                        type="file"
                        accept="image/*"
                        hidden
                        onchange="handleImage(event)"
                    >


                    <textarea
                        id="messageInput"
                        placeholder="Message MedAI..."
                        rows="1"
                        onkeydown="handleKey(event)"
                    ></textarea>


                    <button
                        class="icon-button"
                        onclick="startVoice()"
                        title="Voice input"
                    >
                        🎤
                    </button>


                    <button
                        class="send-button"
                        id="sendButton"
                        onclick="sendMessage()"
                    >
                        ↑
                    </button>

                </div>

            </div>

        </div>

    </main>

</div>


<script>

const messageInput =
    document.getElementById("messageInput");

const messages =
    document.getElementById("messages");

const chatBox =
    document.getElementById("chat");

const sendButton =
    document.getElementById("sendButton");

const imageInput =
    document.getElementById("imageInput");

const preview =
    document.getElementById("preview");

const previewImage =
    document.getElementById("previewImage");

const sidebar =
    document.getElementById("sidebar");

let history = [];

let selectedImage = null;

let selectedMimeType = null;


/* =========================================================
   LOAD THEME
   ========================================================= */

if (localStorage.getItem("medai-theme") === "dark") {
    document.body.classList.add("dark");
}


/* =========================================================
   LOAD HISTORY
   ========================================================= */

function loadHistory() {

    try {

        const saved =
            localStorage.getItem("medai-history");

        if (saved) {
            history = JSON.parse(saved);
        }

    } catch (error) {

        history = [];

    }

    renderHistory();
}


function saveHistory() {

    localStorage.setItem(
        "medai-history",
        JSON.stringify(history)
    );

    renderHistory();
}


function renderHistory() {

    const box =
        document.getElementById("chatHistory");

    box.innerHTML = "";

    history.slice(-20).reverse().forEach(
        function(item) {

            const div =
                document.createElement("div");

            div.className = "history-item";

            div.textContent =
                item.substring(0, 60);

            box.appendChild(div);

        }
    );
}


/* =========================================================
   NEW CHAT
   ========================================================= */

function newChat() {

    messages.innerHTML = "";

    const welcome =
        document.createElement("div");

    welcome.className = "welcome";

    welcome.innerHTML = `
        <h1>How can I help you?</h1>
        <p>Ask anything — in Pashto, Dari, or English.</p>
    `;

    messages.appendChild(welcome);

    removeImage();

    messageInput.value = "";

    sidebar.classList.remove("open");
}


/* =========================================================
   CLEAR HISTORY
   ========================================================= */

function clearHistory() {

    history = [];

    localStorage.removeItem(
        "medai-history"
    );

    renderHistory();
}


/* =========================================================
   THEME
   ========================================================= */

function toggleTheme() {

    document.body.classList.toggle("dark");

    localStorage.setItem(
        "medai-theme",
        document.body.classList.contains("dark")
            ? "dark"
            : "light"
    );
}


/* =========================================================
   SIDEBAR
   ========================================================= */

function toggleSidebar() {

    sidebar.classList.toggle("open");
}


/* =========================================================
   IMAGE
   ========================================================= */

function handleImage(event) {

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

        alert("Image must be smaller than 8 MB.");

        imageInput.value = "";

        return;
    }

    selectedMimeType = file.type;

    const reader =
        new FileReader();

    reader.onload = function(e) {

        selectedImage =
            e.target.result.split(",")[1];

        previewImage.src =
            e.target.result;

        preview.style.display =
            "block";
    };

    reader.readAsDataURL(file);
}


function removeImage() {

    selectedImage = null;

    selectedMimeType = null;

    imageInput.value = "";

    preview.style.display =
        "none";

    previewImage.src = "";
}


/* =========================================================
   MESSAGE UI
   ========================================================= */

function addMessage(
    role,
    text
) {

    const welcome =
        document.getElementById("welcome");

    if (welcome) {
        welcome.remove();
    }

    const wrapper =
        document.createElement("div");

    wrapper.className =
        "message";

    const avatar =
        document.createElement("div");

    avatar.className =
        "avatar " +
        (role === "user"
            ? "user-avatar"
            : "ai-avatar");

    avatar.textContent =
        role === "user"
            ? "U"
            : "AI";

    const content =
        document.createElement("div");

    content.className =
        "message-content";

    content.textContent =
        text;

    wrapper.appendChild(avatar);

    wrapper.appendChild(content);

    messages.appendChild(wrapper);

    chatBox.scrollTop =
        chatBox.scrollHeight;

    return content;
}


function showThinking() {

    const wrapper =
        document.createElement("div");

    wrapper.className =
        "message";

    wrapper.id =
        "thinkingMessage";

    const avatar =
        document.createElement("div");

    avatar.className =
        "avatar ai-avatar";

    avatar.textContent =
        "AI";

    const content =
        document.createElement("div");

    content.className =
        "message-content";

    content.innerHTML = `
        <div class="thinking">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;

    wrapper.appendChild(avatar);

    wrapper.appendChild(content);

    messages.appendChild(wrapper);

    chatBox.scrollTop =
        chatBox.scrollHeight;
}


function removeThinking() {

    const element =
        document.getElementById(
            "thinkingMessage"
        );

    if (element) {
        element.remove();
    }
}


/* =========================================================
   SEND
   ========================================================= */

async function sendMessage() {

    const text =
        messageInput.value.trim();

    if (!text && !selectedImage) {
        return;
    }

    sendButton.disabled = true;

    addMessage(
        "user",
        text || "Image"
    );

    if (text) {
        history.push(text);
        saveHistory();
    }

    const oldHistory =
        history.slice(-20).map(
            function(item) {
                return {
                    role: "user",
                    text: item
                };
            }
        );

    messageInput.value = "";

    showThinking();

    const imageToSend =
        selectedImage;

    const mimeToSend =
        selectedMimeType;

    removeImage();

    try {

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
                        message: text,
                        history: oldHistory,
                        image: imageToSend,
                        mime_type: mimeToSend
                    })
                }
            );

        const data =
            await response.json();

        removeThinking();

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Request failed."
            );
        }

        const answer =
            data.answer ||
            "No answer received.";

        addMessage(
            "assistant",
            answer
        );

    } catch (error) {

        removeThinking();

        addMessage(
            "assistant",
            "Error: " + error.message
        );

    } finally {

        sendButton.disabled = false;

        messageInput.focus();
    }
}


/* =========================================================
   KEYBOARD
   ========================================================= */

function handleKey(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();
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
            "Voice input is not supported by this browser."
        );

        return;
    }

    const recognition =
        new SpeechRecognition();

    recognition.lang =
        "ps-AF";

    recognition.interimResults =
        false;

    recognition.continuous =
        false;

    recognition.onresult =
        function(event) {

            const transcript =
                event.results[0][0].transcript;

            messageInput.value +=
                transcript;
        };

    recognition.onerror =
        function() {

            alert(
                "Voice input could not be started."
            );
        };

    recognition.start();
}


/* =========================================================
   START
   ========================================================= */

loadHistory();

messageInput.focus();

</script>

</body>
</html>
"""


# =========================================================
# HELPERS
# =========================================================

def clean_history(history_data):
    """
    Keep only safe and useful conversation history.
    """

    if not isinstance(history_data, list):
        return []

    cleaned = []

    for item in history_data[-MAX_HISTORY:]:

        if not isinstance(item, dict):
            continue

        role = item.get("role", "")
        text = item.get("text", "")

        if role not in ("user", "assistant"):
            continue

        if not isinstance(text, str):
            continue

        text = text.strip()

        if not text:
            continue

        cleaned.append({
            "role": role,
            "text": text[:6000]
        })

    return cleaned


def build_prompt(message, history_data):
    """
    Build a simple conversation prompt.
    """

    parts = [
        SYSTEM_PROMPT,
        "",
        "Conversation history:"
    ]

    for item in history_data:

        role_name = (
            "User"
            if item["role"] == "user"
            else "Assistant"
        )

        parts.append(
            role_name + ": " + item["text"]
        )

    parts.extend([
        "",
        "Current user message:",
        message if message else "(No text; analyze the uploaded image.)",
        "",
        "Answer the user now."
    ])

    return "\n".join(parts)


def ask_gemini(
    message,
    history_data,
    image_data=None,
    mime_type="image/jpeg"
):
    """
    Send the request to Gemini.
    """

    if not GEMINI_API_KEY:

        raise ValueError(
            "GEMINI_API_KEY is not configured in Vercel Environment Variables."
        )

    if not message and not image_data:

        raise ValueError(
            "Please enter a message or upload an image."
        )

    parts = []

    prompt = build_prompt(
        message,
        history_data
    )

    parts.append({
        "text": prompt
    })

    if image_data:

        try:

            decoded_image = base64.b64decode(
                image_data,
                validate=True
            )

        except Exception:

            raise ValueError(
                "Invalid image data."
            )

        if len(decoded_image) > MAX_IMAGE_SIZE:

            raise ValueError(
                "Image is too large. Maximum size is 8 MB."
            )

        parts.append({
            "inline_data": {
                "mime_type": mime_type or "image/jpeg",
                "data": image_data
            }
        })

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

    try:

        response = requests.post(
            GEMINI_URL,
            params={
                "key": GEMINI_API_KEY
            },
            headers={
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=55
        )

    except requests.exceptions.Timeout:

        raise requests.exceptions.Timeout()

    except requests.exceptions.RequestException as error:

        raise requests.exceptions.RequestException(
            str(error)
        )

    if response.status_code != 200:

        error_text = response.text[:1500]

        raise ValueError(
            "Gemini API error. HTTP "
            + str(response.status_code)
            + ". "
            + error_text
        )

    try:

        result = response.json()

    except Exception:

        raise ValueError(
            "Gemini returned an invalid response."
        )

    candidates = result.get(
        "candidates",
        []
    )

    if not candidates:

        raise ValueError(
            "Gemini returned no answer."
        )

    candidate = candidates[0]

    content = candidate.get(
        "content",
        {}
    )

    response_parts = content.get(
        "parts",
        []
    )

    answer_parts = []

    for part in response_parts:

        text = part.get("text")

        if text:
            answer_parts.append(text)

    answer = "\n".join(
        answer_parts
    ).strip()

    if not answer:

        raise ValueError(
            "Gemini returned an empty answer."
        )

    return answer


# =========================================================
# ROUTES
# =========================================================

@app.route("/")
def home():

    return render_template_string(
        HTML
    )


@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "service": "MedAI"
    })


@app.route(
    "/api/chat",
    methods=["POST"]
)
def chat_api():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        message = data.get(
            "message",
            ""
        )

        if not isinstance(message, str):
            message = ""

        message = message.strip()

        if len(message) > MAX_MESSAGE_LENGTH:

            return jsonify({
                "error": "Message is too long."
            }), 400

        history_data = clean_history(
            data.get(
                "history",
                []
            )
        )

        image_data = data.get(
            "image"
        )

        mime_type = data.get(
            "mime_type",
            "image/jpeg"
        )

        if not isinstance(image_data, str):
            image_data = None

        if not message and not image_data:

            return jsonify({
                "error":
                    "Please enter a message or upload an image."
            }), 400

        answer = ask_gemini(
            message=message,
            history_data=history_data,
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
            "error":
                "Gemini request timed out. Please try again."
        }), 504

    except requests.exceptions.RequestException as error:

        print(
            "MedAI connection error:",
            repr(error)
        )

        return jsonify({
            "error":
                "Could not connect to Gemini."
        }), 502

    except Exception as error:

        print(
            "MedAI ERROR:",
            repr(error)
        )

        return jsonify({
            "error":
                "Server error: " + str(error)
        }), 500


@app.errorhandler(404)
def page_not_found(error):

    return jsonify({
        "error": "Page not found."
    }), 404


# =========================================================
# LOCAL SERVER
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
