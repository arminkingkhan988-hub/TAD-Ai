import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# =========================================================
# CONFIG
# =========================================================

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

TEXT_MODEL = "openai/gpt-oss-20b"
VISION_MODEL = "qwen/qwen3.8-27b"

MAX_IMAGE_SIZE = 8 * 1024 * 1024


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are MedAI, a helpful AI assistant.

You can help with:
- Education
- Science
- Mathematics
- Programming
- Technology
- History
- Business
- Writing
- General knowledge
- Health and medical education

Rules:

1. Always answer in the same language as the user.
2. Support Pashto, Dari, and English.
3. If the user writes in Pashto, answer in Pashto.
4. If the user writes in Dari, answer in Dari.
5. If the user writes in English, answer in English.
6. For medical questions, provide general educational information.
7. Never claim to be a doctor.
8. Do not provide a definite diagnosis based only on chat or an image.
9. Do not tell users to start or stop prescription medicine without professional advice.
10. If symptoms may indicate an emergency, advise the user to contact local emergency medical services or a qualified healthcare professional.
11. Be clear, respectful, friendly, and useful.
12. Do not unnecessarily repeat the user's question.
"""


# =========================================================
# HELPERS
# =========================================================

def groq_error_response(response):
    try:
        details = response.json()
    except Exception:
        details = response.text

    return jsonify({
        "error": "Groq API error",
        "details": details,
        "status_code": response.status_code
    }), response.status_code


def clean_messages(messages):
    if not isinstance(messages, list):
        return []

    cleaned = []

    for item in messages[-20:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content")

        if role not in ["user", "assistant"]:
            continue

        if not isinstance(content, str):
            continue

        content = content.strip()

        if not content:
            continue

        cleaned.append({
            "role": role,
            "content": content
        })

    return cleaned


# =========================================================
# MAIN PAGE
# =========================================================

@app.route("/")
def home():
    return render_template_string(HTML)


# =========================================================
# HEALTH
# =========================================================

@app.route("/health")
def health():
    return jsonify({
        "service": "MedAI",
        "status": "ok"
    })


# =========================================================
# CHAT
# =========================================================

@app.route("/chat", methods=["POST"])
def chat():

    if not GROQ_API_KEY:
        return jsonify({
            "error": "GROQ_API_KEY is not configured."
        }), 500

    try:
        data = request.get_json(silent=True) or {}

        messages = clean_messages(data.get("messages", []))

        if not messages:
            return jsonify({
                "error": "No messages provided."
            }), 400

        payload = {
            "model": TEXT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ] + messages,
            "temperature": 0.7,
            "max_completion_tokens": 1500
        }

        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60
        )

        if response.status_code >= 400:
            return groq_error_response(response)

        result = response.json()

        answer = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        if not answer:
            return jsonify({
                "error": "No answer was returned by Groq."
            }), 502

        return jsonify({
            "answer": answer
        })

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Groq request timed out."
        }), 504

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Could not connect to Groq.",
            "details": str(e)
        }), 502

    except Exception as e:
        return jsonify({
            "error": "Chat error.",
            "details": str(e)
        }), 500


# =========================================================
# IMAGE SEARCH - WIKIMEDIA COMMONS
# =========================================================

@app.route("/images", methods=["GET"])
def images():

    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({
            "images": []
        })

    try:
        api_url = "https://commons.wikimedia.org/w/api.php"

        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": "6",
            "gsrlimit": "12",
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": "500",
            "origin": "*"
        }

        response = requests.get(
            api_url,
            params=params,
            headers={
                "User-Agent": "MedAI/1.0 AI Assistant"
            },
            timeout=20
        )

        if response.status_code >= 400:
            return jsonify({
                "error": "Image search service is unavailable.",
                "details": response.text
            }), 502

        data = response.json()

        results = []

        for page in data.get("query", {}).get("pages", []):

            imageinfo = page.get("imageinfo", [])

            if not imageinfo:
                continue

            info = imageinfo[0]

            image_url = info.get("thumburl") or info.get("url")

            if not image_url:
                continue

            results.append({
                "title": page.get("title", "Image"),
                "url": image_url,
                "original_url": info.get("url", image_url)
            })

        return jsonify({
            "images": results
        })

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Image search timed out."
        }), 504

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Image search service is unavailable.",
            "details": str(e)
        }), 502

    except Exception as e:
        return jsonify({
            "error": "Image search error.",
            "details": str(e)
        }), 500


# =========================================================
# IMAGE ANALYSIS
# =========================================================

@app.route("/analyze-image", methods=["POST"])
def analyze_image():

    if not GROQ_API_KEY:
        return jsonify({
            "error": "GROQ_API_KEY is not configured."
        }), 500

    try:
        data = request.get_json(silent=True) or {}

        image = data.get("image")
        question = data.get("question", "").strip()

        if not image:
            return jsonify({
                "error": "No image was provided."
            }), 400

        if not isinstance(image, str):
            return jsonify({
                "error": "Invalid image format."
            }), 400

        if not image.startswith("data:image/"):
            return jsonify({
                "error": "Image must be a valid image data URL."
            }), 400

        if len(image) > 12 * 1024 * 1024:
            return jsonify({
                "error": "Image is too large."
            }), 413

        if not question:
            question = (
                "Analyze this image and explain clearly what you can see. "
                "If it is a medical image, provide only general educational "
                "information and do not make a definite diagnosis."
            )

        vision_prompt = f"""
{question}

Important:
- Answer in the same language as the user's question.
- If this is a medical image, do not claim a definite diagnosis.
- Explain visible findings carefully.
- If the image is unclear, say so.
- Do not invent details that cannot be seen.
"""

        payload = {
            "model": VISION_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": vision_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.2,
            "max_completion_tokens": 1500
        }

        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=90
        )

        if response.status_code >= 400:
            return groq_error_response(response)

        result = response.json()

        answer = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        if not answer:
            return jsonify({
                "error": "No image analysis result was returned."
            }), 502

        return jsonify({
            "answer": answer
        })

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Image analysis timed out."
        }), 504

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Could not connect to Groq image analysis.",
            "details": str(e)
        }), 502

    except Exception as e:
        return jsonify({
            "error": "Image analysis error.",
            "details": str(e)
        }), 500


# =========================================================
# HTML
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

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    font-family: Arial, Helvetica, sans-serif;
}

body {
    background: #f5f7fb;
    color: #111827;
    transition: 0.2s;
}

body.dark {
    background: #0f172a;
    color: #f8fafc;
}

.app {
    display: flex;
    width: 100%;
    height: 100vh;
    overflow: hidden;
}

/* SIDEBAR */

.sidebar {
    width: 260px;
    background: #ffffff;
    border-right: 1px solid #e5e7eb;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

body.dark .sidebar {
    background: #111827;
    border-color: #1f2937;
}

.logo {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 8px;
}

.logo span {
    font-size: 13px;
    font-weight: normal;
    color: #64748b;
}

.side-button {
    width: 100%;
    padding: 12px;
    border: 0;
    border-radius: 10px;
    background: #eef2ff;
    color: #1e293b;
    cursor: pointer;
    text-align: left;
    font-size: 14px;
}

.side-button:hover {
    background: #e0e7ff;
}

body.dark .side-button {
    background: #1e293b;
    color: #f8fafc;
}

.history-title {
    margin-top: 10px;
    font-size: 13px;
    color: #64748b;
}

.history {
    flex: 1;
    overflow-y: auto;
}

/* MAIN */

.main {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.topbar {
    height: 64px;
    padding: 10px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #e5e7eb;
    background: rgba(255,255,255,0.95);
}

body.dark .topbar {
    background: #111827;
    border-color: #1f2937;
}

.top-title {
    font-weight: bold;
    font-size: 18px;
}

.top-actions {
    display: flex;
    gap: 7px;
}

.icon-button {
    border: 0;
    background: transparent;
    cursor: pointer;
    padding: 8px;
    border-radius: 8px;
    font-size: 17px;
}

.icon-button:hover {
    background: #e5e7eb;
}

body.dark .icon-button:hover {
    background: #1e293b;
}

/* CHAT */

.chat {
    flex: 1;
    overflow-y: auto;
    padding: 25px;
}

.empty {
    max-width: 700px;
    margin: 70px auto;
    text-align: center;
}

.empty h1 {
    font-size: 34px;
    margin-bottom: 10px;
}

.empty p {
    color: #64748b;
}

.message {
    max-width: 850px;
    margin: 0 auto 18px auto;
    display: flex;
}

.message.user {
    justify-content: flex-end;
}

.bubble {
    max-width: 80%;
    padding: 13px 16px;
    border-radius: 15px;
    line-height: 1.55;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}

.message.user .bubble {
    background: #2563eb;
    color: white;
}

.message.assistant .bubble {
    background: white;
    border: 1px solid #e5e7eb;
}

body.dark .message.assistant .bubble {
    background: #1e293b;
    border-color: #334155;
}

/* INPUT */

.input-area {
    padding: 12px 18px 18px;
    border-top: 1px solid #e5e7eb;
    background: #ffffff;
}

body.dark .input-area {
    background: #111827;
    border-color: #1f2937;
}

.tools {
    max-width: 900px;
    margin: 0 auto 8px;
    display: flex;
    gap: 7px;
    flex-wrap: wrap;
}

.tool {
    border: 1px solid #dbeafe;
    background: #eff6ff;
    color: #1d4ed8;
    border-radius: 8px;
    padding: 7px 10px;
    cursor: pointer;
}

body.dark .tool {
    background: #172554;
    border-color: #1e3a8a;
    color: #bfdbfe;
}

.input-row {
    max-width: 900px;
    margin: auto;
    display: flex;
    gap: 8px;
    align-items: flex-end;
}

textarea {
    flex: 1;
    min-height: 52px;
    max-height: 180px;
    resize: vertical;
    border: 1px solid #cbd5e1;
    border-radius: 13px;
    padding: 14px;
    outline: none;
    font-size: 15px;
    background: white;
    color: #111827;
}

body.dark textarea {
    background: #1e293b;
    color: white;
    border-color: #475569;
}

.send {
    width: 52px;
    height: 52px;
    border: 0;
    border-radius: 13px;
    background: #2563eb;
    color: white;
    cursor: pointer;
    font-size: 19px;
}

/* PANELS */

.panel {
    max-width: 900px;
    margin: 0 auto 10px;
    padding: 12px;
    border: 1px solid #dbeafe;
    border-radius: 12px;
    background: #f8fafc;
}

body.dark .panel {
    background: #172033;
    border-color: #334155;
}

.hidden {
    display: none !important;
}

/* IMAGE UPLOAD */

.upload-row {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.upload-row input[type="file"] {
    padding: 10px;
}

.upload-question {
    width: 100%;
    padding: 10px;
    border-radius: 9px;
    border: 1px solid #cbd5e1;
}

body.dark .upload-question {
    background: #0f172a;
    color: white;
    border-color: #475569;
}

.preview-box {
    margin-top: 10px;
}

.preview-box img {
    max-width: 280px;
    max-height: 280px;
    border-radius: 12px;
    display: block;
}

/* IMAGE SEARCH */

.image-results {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 10px;
    margin-top: 10px;
}

.image-card {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
    background: white;
}

body.dark .image-card {
    background: #1e293b;
    border-color: #334155;
}

.image-card img {
    width: 100%;
    height: 130px;
    object-fit: cover;
    display: block;
}

.image-card div {
    padding: 7px;
    font-size: 12px;
}

/* THINKING */

.thinking {
    opacity: 0.7;
    font-style: italic;
}

/* MEDICAL */

.medical-warning {
    max-width: 900px;
    margin: 0 auto 10px;
    padding: 12px;
    border-radius: 10px;
    background: #fff7ed;
    border: 1px solid #fed7aa;
    color: #9a3412;
}

/* MOBILE */

@media (max-width: 800px) {

    .sidebar {
        display: none;
    }

    .chat {
        padding: 15px;
    }

    .bubble {
        max-width: 90%;
    }

    .topbar {
        padding: 10px;
    }

    .input-area {
        padding: 10px;
    }

    .empty h1 {
        font-size: 27px;
    }
}

</style>

</head>

<body>

<div class="app">

    <!-- SIDEBAR -->

    <aside class="sidebar">

        <div class="logo">
            🩺 MedAI
            <span>AI Assistant</span>
        </div>

        <button
            class="side-button"
            type="button"
            onclick="newChat()"
        >
            ➕ New Chat
        </button>

        <button
            class="side-button"
            type="button"
            onclick="toggleSearch()"
        >
            🔎 Search Chat
        </button>

        <button
            class="side-button"
            type="button"
            onclick="exportChat()"
        >
            📥 Export Chat
        </button>

        <div class="history-title">
            Chat History
        </div>

        <div
            id="history"
            class="history"
        ></div>

    </aside>


    <!-- MAIN -->

    <main class="main">

        <header class="topbar">

            <div class="top-title">
                MedAI
            </div>

            <div class="top-actions">

                <button
                    class="icon-button"
                    type="button"
                    title="New Chat"
                    onclick="newChat()"
                >
                    ➕
                </button>

                <button
                    class="icon-button"
                    type="button"
                    title="Dark / Light"
                    onclick="toggleDark()"
                >
                    🌙
                </button>

            </div>

        </header>


        <!-- CHAT -->

        <section
            id="chat"
            class="chat"
        ></section>


        <!-- SEARCH PANEL -->

        <div
            id="searchPanel"
            class="panel hidden"
        >

            <input
                id="chatSearchInput"
                type="text"
                placeholder="Search this chat..."
                style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;"
                oninput="searchChat()"
            >

            <div id="searchResults"></div>

        </div>


        <!-- IMAGE SEARCH PANEL -->

        <div
            id="imageSearchPanel"
            class="panel hidden"
        >

            <div style="display:flex;gap:8px;">

                <input
                    id="imageSearchInput"
                    type="text"
                    placeholder="Search images..."
                    style="flex:1;padding:10px;border-radius:8px;border:1px solid #cbd5e1;"
                    onkeydown="if(event.key==='Enter') searchImages()"
                >

                <button
                    type="button"
                    class="tool"
                    onclick="searchImages()"
                >
                    Search
                </button>

            </div>

            <div
                id="imageResults"
                class="image-results"
            ></div>

        </div>


        <!-- UPLOAD PANEL -->

        <div
            id="uploadPanel"
            class="panel hidden"
        >

            <div class="upload-row">

                <input
                    type="file"
                    id="imageInput"
                    accept="image/png,image/jpeg,image/webp"
                >

                <div
                    id="previewBox"
                    class="preview-box"
                ></div>

                <input
                    id="imageQuestion"
                    class="upload-question"
                    type="text"
                    placeholder="Ask something about this image..."
                >

                <button
                    type="button"
                    class="tool"
                    onclick="analyzeImage()"
                >
                    🔍 Analyze Image
                </button>

            </div>

        </div>


        <!-- MEDICAL WARNING -->

        <div
            id="medicalWarning"
            class="medical-warning hidden"
        ></div>


        <!-- INPUT -->

        <div class="input-area">

            <div class="tools">

                <button
                    class="tool"
                    type="button"
                    onclick="toggleUpload()"
                >
                    📤 Image Upload
                </button>

                <button
                    class="tool"
                    type="button"
                    onclick="toggleImageSearch()"
                >
                    🖼️ Image Search
                </button>

                <button
                    class="tool"
                    type="button"
                    onclick="toggleSearch()"
                >
                    🔎 Search
                </button>

                <button
                    class="tool"
                    type="button"
                    onclick="checkMedicalSafety()"
                >
                    🏥 Medical Safety
                </button>

            </div>


            <div class="input-row">

                <textarea
                    id="messageInput"
                    placeholder="Ask MedAI anything..."
                    onkeydown="handleKey(event)"
                ></textarea>

                <button
                    id="sendButton"
                    class="send"
                    type="button"
                    onclick="sendMessage()"
                >
                    ➤
                </button>

            </div>

        </div>

    </main>

</div>


<script>

/* =========================================================
   STATE
========================================================= */

let messages = [];

let selectedImageBase64 = null;

const STORAGE_KEY = "medai_messages_v2";


/* =========================================================
   ELEMENTS
========================================================= */

const chatElement =
    document.getElementById("chat");

const inputElement =
    document.getElementById("messageInput");

const imageInput =
    document.getElementById("imageInput");


/* =========================================================
   INITIALIZE
========================================================= */

document.addEventListener("DOMContentLoaded", function() {

    loadMessages();

    loadDarkMode();

    imageInput.addEventListener(
        "change",
        handleImageSelected
    );

    renderMessages();

});


/* =========================================================
   LOAD / SAVE
========================================================= */

function loadMessages() {

    try {

        const saved =
            localStorage.getItem(STORAGE_KEY);

        if (!saved) {
            messages = [];
            return;
        }

        const parsed =
            JSON.parse(saved);

        if (Array.isArray(parsed)) {
            messages = parsed;
        } else {
            messages = [];
        }

    } catch (error) {

        console.error(
            "Could not load messages:",
            error
        );

        messages = [];
    }
}


function saveMessages() {

    try {

        localStorage.setItem(
            STORAGE_KEY,
            JSON.stringify(messages)
        );

    } catch (error) {

        console.error(
            "Could not save messages:",
            error
        );
    }

}


/* =========================================================
   RENDER CHAT
========================================================= */

function renderMessages() {

    chatElement.innerHTML = "";

    if (messages.length === 0) {

        const empty =
            document.createElement("div");

        empty.className = "empty";

        empty.innerHTML = `
            <h1>🩺 Welcome to MedAI</h1>
            <p>
                Ask questions about education, science,
                coding, technology, health and more.
            </p>
        `;

        chatElement.appendChild(empty);

        return;
    }


    messages.forEach(function(message, index) {

        const wrapper =
            document.createElement("div");

        wrapper.className =
            "message " +
            (message.role === "user"
                ? "user"
                : "assistant");


        const bubble =
            document.createElement("div");

        bubble.className = "bubble";

        bubble.textContent =
            message.content;


        wrapper.appendChild(bubble);


        if (message.role === "assistant") {

            const copyButton =
                document.createElement("button");

            copyButton.type = "button";

            copyButton.textContent = "📋";

            copyButton.style.marginLeft = "7px";
            copyButton.style.border = "0";
            copyButton.style.background = "transparent";
            copyButton.style.cursor = "pointer";

            copyButton.onclick = function() {

                copyText(
                    message.content
                );

            };

            wrapper.appendChild(copyButton);
        }


        chatElement.appendChild(wrapper);

    });


    chatElement.scrollTop =
        chatElement.scrollHeight;

    updateHistory();

}


/* =========================================================
   SEND MESSAGE
========================================================= */

async function sendMessage() {

    const text =
        inputElement.value.trim();

    if (!text) {
        return;
    }


    messages.push({
        role: "user",
        content: text
    });

    inputElement.value = "";

    saveMessages();

    renderMessages();


    const thinking =
        document.createElement("div");

    thinking.className =
        "message assistant";

    thinking.id =
        "thinkingMessage";

    thinking.innerHTML =
        '<div class="bubble thinking">MedAI is thinking...</div>';

    chatElement.appendChild(thinking);

    chatElement.scrollTop =
        chatElement.scrollHeight;


    try {

        const response =
            await fetch("/chat", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    messages: messages
                })

            });


        const data =
            await response.json();


        if (!response.ok) {

            let errorMessage =
                data.error ||
                "Chat request failed.";

            if (data.details) {

                errorMessage +=
                    "\n" +
                    (
                        typeof data.details === "string"
                        ? data.details
                        : JSON.stringify(data.details)
                    );
            }

            throw new Error(
                errorMessage
            );
        }


        const answer =
            data.answer ||
            "No answer received.";


        messages.push({
            role: "assistant",
            content: answer
        });

        saveMessages();

    } catch (error) {

        console.error(error);

        messages.push({
            role: "assistant",
            content:
                "⚠️ " +
                error.message
        });

        saveMessages();

    }


    const thinkingElement =
        document.getElementById(
            "thinkingMessage"
        );

    if (thinkingElement) {
        thinkingElement.remove();
    }

    renderMessages();

}


/* =========================================================
   ENTER KEY
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
   NEW CHAT
========================================================= */

function newChat() {

    console.log(
        "New Chat clicked"
    );


    messages = [];

    selectedImageBase64 = null;


    localStorage.removeItem(
        STORAGE_KEY
    );


    chatElement.innerHTML = "";


    inputElement.value = "";


    document.getElementById(
        "chatSearchInput"
    ).value = "";


    document.getElementById(
        "searchResults"
    ).innerHTML = "";


    document.getElementById(
        "imageSearchInput"
    ).value = "";


    document.getElementById(
        "imageResults"
    ).innerHTML = "";


    document.getElementById(
        "imageInput"
    ).value = "";


    document.getElementById(
        "imageQuestion"
    ).value = "";


    document.getElementById(
        "previewBox"
    ).innerHTML = "";


    document.getElementById(
        "medicalWarning"
    ).innerHTML = "";


    document.getElementById(
        "medicalWarning"
    ).classList.add(
        "hidden"
    );


    document.getElementById(
        "searchPanel"
    ).classList.add(
        "hidden"
    );


    document.getElementById(
        "imageSearchPanel"
    ).classList.add(
        "hidden"
    );


    document.getElementById(
        "uploadPanel"
    ).classList.add(
        "hidden"
    );


    renderMessages();

    inputElement.focus();

}


/* =========================================================
   COPY
========================================================= */

async function copyText(text) {

    try {

        await navigator.clipboard.writeText(
            text
        );

        alert("Copied!");

    } catch (error) {

        console.error(error);

        alert("Could not copy text.");

    }

}


/* =========================================================
   DARK MODE
========================================================= */

function toggleDark() {

    document.body.classList.toggle(
        "dark"
    );

    localStorage.setItem(
        "medai_dark",
        document.body.classList.contains("dark")
            ? "1"
            : "0"
    );

}


function loadDarkMode() {

    const dark =
        localStorage.getItem(
            "medai_dark"
        );

    if (dark === "1") {

        document.body.classList.add(
            "dark"
        );

    }

}


/* =========================================================
   SEARCH CHAT
========================================================= */

function toggleSearch() {

    const panel =
        document.getElementById(
            "searchPanel"
        );

    panel.classList.toggle(
        "hidden"
    );

}


function searchChat() {

    const query =
        document.getElementById(
            "chatSearchInput"
        ).value
        .trim()
        .toLowerCase();


    const result =
        document.getElementById(
            "searchResults"
        );


    result.innerHTML = "";


    if (!query) {
        return;
    }


    messages.forEach(function(message) {

        if (
            message.content
                .toLowerCase()
                .includes(query)
        ) {

            const item =
                document.createElement("div");

            item.style.padding = "8px 0";

            item.textContent =
                (
                    message.role === "user"
                    ? "You: "
                    : "MedAI: "
                ) +
                message.content;

            result.appendChild(item);

        }

    });

}


/* =========================================================
   EXPORT CHAT
========================================================= */

function exportChat() {

    if (messages.length === 0) {

        alert(
            "There is no chat to export."
        );

        return;
    }


    let text =
        "MedAI Chat\n\n";


    messages.forEach(function(message) {

        text +=
            (
                message.role === "user"
                ? "You"
                : "MedAI"
            ) +
            ":\n" +
            message.content +
            "\n\n";

    });


    const blob =
        new Blob(
            [text],
            {
                type: "text/plain"
            }
        );


    const url =
        URL.createObjectURL(blob);


    const link =
        document.createElement("a");

    link.href = url;

    link.download =
        "medai-chat.txt";

    document.body.appendChild(
        link
    );

    link.click();

    link.remove();

    URL.revokeObjectURL(url);

}


/* =========================================================
   IMAGE UPLOAD PANEL
========================================================= */

function toggleUpload() {

    const panel =
        document.getElementById(
            "uploadPanel"
        );

    panel.classList.toggle(
        "hidden"
    );

}


/* =========================================================
   IMAGE SELECT
========================================================= */

function handleImageSelected(event) {

    const file =
        event.target.files &&
        event.target.files[0];


    if (!file) {

        selectedImageBase64 = null;

        document.getElementById(
            "previewBox"
        ).innerHTML = "";

        return;
    }


    if (!file.type.startsWith("image/")) {

        alert(
            "Please select an image."
        );

        event.target.value = "";

        selectedImageBase64 = null;

        return;
    }


    if (
        file.size >
        8 * 1024 * 1024
    ) {

        alert(
            "Image must be smaller than 8 MB."
        );

        event.target.value = "";

        selectedImageBase64 = null;

        return;
    }


    const reader =
        new FileReader();


    reader.onload = function(e) {

        selectedImageBase64 =
            e.target.result;


        const preview =
            document.getElementById(
                "previewBox"
            );


        preview.innerHTML = "";


        const image =
            document.createElement(
                "img"
            );


        image.src =
            selectedImageBase64;


        image.alt =
            "Selected image";


        preview.appendChild(
            image
        );

    };


    reader.onerror = function() {

        selectedImageBase64 = null;

        alert(
            "Could not read the image."
        );

    };


    reader.readAsDataURL(
        file
    );

}


/* =========================================================
   IMAGE ANALYSIS
========================================================= */

async function analyzeImage() {

    if (!selectedImageBase64) {

        alert(
            "Please select an image first."
        );

        return;
    }


    const questionElement =
        document.getElementById(
            "imageQuestion"
        );


    const question =
        questionElement.value.trim() ||
        "Please analyze this image and explain what you see.";


    const button =
        document.querySelector(
            '#uploadPanel button'
        );


    if (button) {

        button.disabled = true;

        button.textContent =
            "Analyzing...";

    }


    try {

        const response =
            await fetch(
                "/analyze-image",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        image:
                            selectedImageBase64,

                        question:
                            question
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            let errorMessage =
                data.error ||
                "Image analysis failed.";

            if (data.details) {

                errorMessage +=
                    "\n" +
                    (
                        typeof data.details === "string"
                        ? data.details
                        : JSON.stringify(data.details)
                    );
            }

            throw new Error(
                errorMessage
            );
        }


        const answer =
            data.answer ||
            "No image analysis result received.";


        messages.push({
            role: "user",
            content:
                "🖼️ " + question
        });


        messages.push({
            role: "assistant",
            content:
                answer
        });


        saveMessages();

        renderMessages();


        document.getElementById(
            "uploadPanel"
        ).classList.add(
            "hidden"
        );


    } catch (error) {

        console.error(
            "Image analysis:",
            error
        );

        alert(
            error.message
        );

    } finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                "🔍 Analyze Image";

        }

    }

}


/* =========================================================
   IMAGE SEARCH
========================================================= */

function toggleImageSearch() {

    const panel =
        document.getElementById(
            "imageSearchPanel"
        );

    panel.classList.toggle(
        "hidden"
    );

}


async function searchImages() {

    const query =
        document.getElementById(
            "imageSearchInput"
        ).value.trim();


    const result =
        document.getElementById(
            "imageResults"
        );


    result.innerHTML = "";


    if (!query) {

        return;
    }


    result.textContent =
        "Searching images...";


    try {

        const response =
            await fetch(
                "/images?q=" +
                encodeURIComponent(query)
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Image search failed."
            );
        }


        result.innerHTML = "";


        if (
            !data.images ||
            data.images.length === 0
        ) {

            result.textContent =
                "No images found.";

            return;
        }


        data.images.forEach(
            function(item) {

                const card =
                    document.createElement(
                        "div"
                    );

                card.className =
                    "image-card";


                const image =
                    document.createElement(
                        "img"
                    );

                image.src =
                    item.url;

                image.alt =
                    item.title || "Image";

                image.loading =
                    "lazy";


                const title =
                    document.createElement(
                        "div"
                    );

                title.textContent =
                    item.title || "Image";


                card.appendChild(
                    image
                );

                card.appendChild(
                    title
                );


                result.appendChild(
                    card
                );

            }
        );


    } catch (error) {

        console.error(error);

        result.textContent =
            error.message;

    }

}


/* =========================================================
   MEDICAL SAFETY
========================================================= */

function checkMedicalSafety() {

    const warning =
        document.getElementById(
            "medicalWarning"
        );


    warning.classList.remove(
        "hidden"
    );


    warning.textContent =
        "🏥 Medical Safety: MedAI provides general educational information and is not a doctor. For serious, worsening, or emergency symptoms, contact a qualified healthcare professional or local emergency medical service.";

}


/* =========================================================
   HISTORY
========================================================= */

function updateHistory() {

    const history =
        document.getElementById(
            "history"
        );


    history.innerHTML = "";


    const userMessages =
        messages.filter(
            function(message) {
                return message.role === "user";
            }
        );


    userMessages
        .slice(-10)
        .reverse()
        .forEach(
            function(message) {

                const item =
                    document.createElement(
                        "button"
                    );


                item.type =
                    "button";


                item.style.width =
                    "100%";

                item.style.border =
                    "0";

                item.style.background =
                    "transparent";

                item.style.textAlign =
                    "left";

                item.style.padding =
                    "8px";

                item.style.cursor =
                    "pointer";

                item.textContent =
                    message.content.length > 40
                    ? message.content.slice(0, 40) + "..."
                    : message.content;


                item.onclick =
                    function() {

                        inputElement.value =
                            message.content;

                        inputElement.focus();

                    };


                history.appendChild(
                    item
                );

            }
        );

}

</script>

</body>

</html>
"""


# =========================================================
# RUN
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
