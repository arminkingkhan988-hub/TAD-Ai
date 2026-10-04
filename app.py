import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

TEXT_MODEL = "openai/gpt-oss-20b"
VISION_MODEL = "qwen/qwen3.6-27b"


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
3. For medical questions, provide general educational information.
4. Never claim to be a doctor.
5. Do not give a definite diagnosis based only on chat or an image.
6. Do not tell users to start or stop prescription medicine without professional advice.
7. If symptoms may indicate an emergency, advise the user to contact local emergency medical services or a qualified healthcare professional.
8. Be clear, respectful, friendly, and useful.
"""


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

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f4f7fb;
    color: #172033;
}

body.dark {
    background: #111827;
    color: #f3f4f6;
}

.app {
    max-width: 1100px;
    height: 100vh;
    margin: auto;
    display: flex;
    flex-direction: column;
}

header {
    padding: 14px 18px;
    background: white;
    border-bottom: 1px solid #ddd;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}

body.dark header {
    background: #1f2937;
    border-color: #374151;
}

.logo {
    font-size: 22px;
    font-weight: bold;
}

.logo span {
    display: block;
    font-size: 12px;
    opacity: 0.6;
    font-weight: normal;
}

.actions {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    justify-content: flex-end;
}

button {
    border: 0;
    border-radius: 8px;
    padding: 9px 11px;
    cursor: pointer;
    background: #e8eef7;
    color: #172033;
}

button:hover {
    opacity: 0.8;
}

body.dark button {
    background: #374151;
    color: white;
}

.chat {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}

.message {
    max-width: 82%;
    margin-bottom: 15px;
    padding: 13px 15px;
    border-radius: 14px;
    line-height: 1.55;
    white-space: pre-wrap;
    word-wrap: break-word;
}

.user {
    margin-left: auto;
    background: #2563eb;
    color: white;
    border-bottom-right-radius: 4px;
}

.assistant {
    margin-right: auto;
    background: white;
    border: 1px solid #e1e5eb;
    border-bottom-left-radius: 4px;
}

body.dark .assistant {
    background: #1f2937;
    border-color: #374151;
}

.message-actions {
    margin-top: 8px;
}

.copy-btn {
    font-size: 12px;
    padding: 5px 8px;
}

.thinking {
    display: none;
    margin: 0 20px 10px;
    opacity: 0.7;
}

.panel {
    display: none;
    padding: 10px 18px;
    background: white;
    border-bottom: 1px solid #ddd;
}

body.dark .panel {
    background: #1f2937;
    border-color: #374151;
}

.panel-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.panel input {
    flex: 1;
    min-width: 180px;
    padding: 10px;
    border: 1px solid #ccd3df;
    border-radius: 8px;
    font-size: 14px;
}

body.dark .panel input {
    background: #111827;
    color: white;
    border-color: #4b5563;
}

.search-results {
    margin-top: 8px;
    font-size: 13px;
}

.image-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
    gap: 12px;
    margin-top: 12px;
}

.image-card {
    background: white;
    border: 1px solid #ddd;
    border-radius: 10px;
    overflow: hidden;
}

body.dark .image-card {
    background: #111827;
    border-color: #374151;
}

.image-card img {
    width: 100%;
    height: 160px;
    object-fit: cover;
    display: block;
}

.image-info {
    padding: 8px;
    font-size: 12px;
}

.image-info a {
    color: #2563eb;
    text-decoration: none;
}

.medical-warning {
    display: none;
    margin: 10px 18px;
    padding: 12px;
    border-radius: 10px;
    background: #fff7ed;
    border: 1px solid #fdba74;
    color: #9a3412;
    font-size: 14px;
}

body.dark .medical-warning {
    background: #431407;
    color: #fed7aa;
}

.emergency-warning {
    display: none;
    margin: 10px 18px;
    padding: 12px;
    border-radius: 10px;
    background: #fee2e2;
    border: 1px solid #ef4444;
    color: #991b1b;
    font-weight: bold;
}

body.dark .emergency-warning {
    background: #450a0a;
    color: #fecaca;
}

.upload-area {
    padding: 15px;
    border: 2px dashed #9ca3af;
    border-radius: 10px;
    text-align: center;
}

.preview {
    max-width: 220px;
    max-height: 220px;
    margin: 12px auto;
    display: none;
    border-radius: 10px;
}

.composer {
    padding: 12px;
    background: white;
    border-top: 1px solid #ddd;
    display: flex;
    gap: 8px;
}

body.dark .composer {
    background: #1f2937;
    border-color: #374151;
}

textarea {
    flex: 1;
    resize: none;
    min-height: 48px;
    max-height: 150px;
    border: 1px solid #ccd3df;
    border-radius: 10px;
    padding: 12px;
    font-size: 15px;
    outline: none;
    font-family: inherit;
}

body.dark textarea {
    background: #111827;
    color: white;
    border-color: #4b5563;
}

.send {
    background: #2563eb;
    color: white;
    min-width: 75px;
}

.empty {
    text-align: center;
    opacity: 0.6;
    padding: 60px 20px;
}

.error-box {
    padding: 10px;
    margin-top: 10px;
    border-radius: 8px;
    background: #fee2e2;
    color: #991b1b;
}

body.dark .error-box {
    background: #450a0a;
    color: #fecaca;
}

@media (max-width: 600px) {

    .app {
        height: 100dvh;
    }

    header {
        align-items: flex-start;
    }

    .actions button {
        padding: 7px 8px;
        font-size: 12px;
    }

    .message {
        max-width: 92%;
    }

    .chat {
        padding: 12px;
    }

    .composer {
        padding: 8px;
    }

    .image-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

</style>
</head>

<body>

<div class="app">

<header>

    <div class="logo">
        🤖 MedAI
        <span>AI Assistant</span>
    </div>

    <div class="actions">

        <button onclick="newChat()">🆕 New</button>

        <button onclick="toggleSearch()">
            🔍 Search
        </button>

        <button onclick="toggleImageSearch()">
            🖼️ Images
        </button>

        <button onclick="toggleUpload()">
            📤 Upload
        </button>

        <button onclick="exportChat()">
            📥 Export
        </button>

        <button onclick="toggleDark()">
            🌙
        </button>

    </div>

</header>


<div class="panel" id="searchPanel">

    <div class="panel-row">

        <input
            id="searchInput"
            type="text"
            placeholder="Search in this chat..."
            oninput="searchChat()"
        >

    </div>

    <div
        class="search-results"
        id="searchResults"
    ></div>

</div>


<div class="panel" id="imagePanel">

    <div class="panel-row">

        <input
            id="imageQuery"
            type="text"
            placeholder="Search images..."
            onkeydown="if(event.key==='Enter') searchImages()"
        >

        <button onclick="searchImages()">
            🔍 Search
        </button>

    </div>

    <div id="imageResults"></div>

</div>


<div class="panel" id="uploadPanel">

    <div class="upload-area">

        <strong>📤 Upload Image</strong>

        <p>
            Upload an image and ask MedAI about it.
        </p>

        <input
            type="file"
            id="imageFile"
            accept="image/jpeg,image/png,image/webp,image/gif"
            onchange="previewImage(event)"
        >

        <img
            id="imagePreview"
            class="preview"
        >

        <input
            id="imageQuestion"
            type="text"
            placeholder="What should I ask about this image?"
            style="width:100%;margin-top:10px;padding:10px;border:1px solid #ccd3df;border-radius:8px;"
        >

        <br><br>

        <button onclick="analyzeImage()">
            🤖 Analyze Image
        </button>

    </div>

</div>


<div
    id="medicalWarning"
    class="medical-warning"
>
    🏥 <strong>Medical Safety:</strong>
    MedAI provides general educational information and is not a doctor.
    For diagnosis or treatment, consult a qualified healthcare professional.
</div>


<div
    id="emergencyWarning"
    class="emergency-warning"
>
    🚨 Possible emergency:
    If you have severe symptoms or believe this is an emergency,
    contact local emergency medical services or a qualified healthcare
    professional immediately.
</div>


<main class="chat" id="chat"></main>


<div class="thinking" id="thinking">
    🤔 MedAI is thinking...
</div>


<div class="composer">

    <textarea
        id="messageInput"
        placeholder="Ask MedAI anything..."
        onkeydown="handleKey(event)"
    ></textarea>

    <button
        class="send"
        onclick="sendMessage()"
    >
        Send
    </button>

</div>

</div>


<script>

let messages = [];

const chat = document.getElementById("chat");
const input = document.getElementById("messageInput");
const thinking = document.getElementById("thinking");


function loadMessages() {

    try {

        const saved = localStorage.getItem(
            "medai_messages"
        );

        if (saved) {
            messages = JSON.parse(saved);
        }

    } catch (error) {

        messages = [];

    }

    renderMessages();
}


function saveMessages() {

    localStorage.setItem(
        "medai_messages",
        JSON.stringify(messages)
    );
}


function renderMessages() {

    chat.innerHTML = "";

    if (messages.length === 0) {

        chat.innerHTML = `
            <div class="empty">
                <h2>🤖 Welcome to MedAI</h2>
                <p>
                    Ask me anything about education,
                    science, coding, health,
                    technology and more.
                </p>
            </div>
        `;

        return;
    }


    messages.forEach(function(message) {

        const div =
            document.createElement("div");

        div.className =
            "message " +
            (
                message.role === "user"
                    ? "user"
                    : "assistant"
            );


        const text =
            document.createElement("div");

        text.textContent =
            message.content;

        div.appendChild(text);


        if (message.role === "assistant") {

            const actions =
                document.createElement("div");

            actions.className =
                "message-actions";


            const copy =
                document.createElement("button");

            copy.className =
                "copy-btn";

            copy.textContent =
                "📋 Copy";


            copy.onclick = function() {

                copyText(
                    message.content,
                    copy
                );

            };


            actions.appendChild(copy);

            div.appendChild(actions);
        }


        chat.appendChild(div);

    });


    chat.scrollTop = chat.scrollHeight;
}


async function sendMessage() {

    const text =
        input.value.trim();

    if (!text) {
        return;
    }


    input.value = "";


    messages.push({
        role: "user",
        content: text
    });


    saveMessages();
    renderMessages();

    checkMedicalSafety(text);


    thinking.style.display = "block";


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

                    body: JSON.stringify({
                        messages: messages
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Something went wrong."
            );
        }


        messages.push({
            role: "assistant",
            content: data.answer
        });


        saveMessages();
        renderMessages();


    } catch (error) {

        messages.push({
            role: "assistant",
            content:
                "⚠️ " + error.message
        });


        saveMessages();
        renderMessages();


    } finally {

        thinking.style.display = "none";

    }
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


function copyText(text, button) {

    navigator.clipboard.writeText(text)
        .then(function() {

            const oldText =
                button.textContent;

            button.textContent =
                "✅ Copied";

            setTimeout(function() {

                button.textContent =
                    oldText;

            }, 1500);

        })
        .catch(function() {

            alert("Copy failed.");

        });
}


function newChat() {

    if (messages.length > 0) {

        const confirmed = confirm(
            "Start a new chat? The current chat will be cleared."
        );

        if (!confirmed) {
            return;
        }
    }


    messages = [];


    localStorage.removeItem(
        "medai_messages"
    );


    input.value = "";


    document.getElementById(
        "searchInput"
    ).value = "";


    document.getElementById(
        "searchResults"
    ).textContent = "";


    document.getElementById(
        "imageQuery"
    ).value = "";


    document.getElementById(
        "imageResults"
    ).innerHTML = "";


    document.getElementById(
        "imageFile"
    ).value = "";


    document.getElementById(
        "imageQuestion"
    ).value = "";


    document.getElementById(
        "imagePreview"
    ).style.display = "none";


    document.getElementById(
        "medicalWarning"
    ).style.display = "none";


    document.getElementById(
        "emergencyWarning"
    ).style.display = "none";


    thinking.style.display = "none";


    renderMessages();
}


function toggleDark() {

    document.body.classList.toggle("dark");

    localStorage.setItem(
        "medai_dark",
        document.body.classList.contains("dark")
    );
}


function loadDarkMode() {

    if (
        localStorage.getItem("medai_dark")
        === "true"
    ) {

        document.body.classList.add("dark");
    }
}


function toggleSearch() {

    const panel =
        document.getElementById(
            "searchPanel"
        );


    panel.style.display =
        panel.style.display === "block"
            ? "none"
            : "block";


    if (panel.style.display === "block") {

        document.getElementById(
            "searchInput"
        ).focus();

    }
}


function searchChat() {

    const query =
        document.getElementById(
            "searchInput"
        )
        .value
        .trim()
        .toLowerCase();


    const results =
        document.getElementById(
            "searchResults"
        );


    if (!query) {

        results.textContent = "";

        renderMessages();

        return;
    }


    const matches =
        messages.filter(function(message) {

            return message.content
                .toLowerCase()
                .includes(query);

        });


    results.textContent =
        matches.length +
        " matching message(s) found.";


    chat.innerHTML = "";


    matches.forEach(function(message) {

        const div =
            document.createElement("div");


        div.className =
            "message " +
            (
                message.role === "user"
                    ? "user"
                    : "assistant"
            );


        const text =
            document.createElement("div");


        text.textContent =
            message.content;


        div.appendChild(text);

        chat.appendChild(div);

    });
}


function exportChat() {

    if (messages.length === 0) {

        alert(
            "There is no chat to export."
        );

        return;
    }


    let content =
        "MedAI Chat Export\n";

    content +=
        "=================\n\n";


    messages.forEach(function(message) {

        const role =
            message.role === "user"
                ? "You"
                : "MedAI";


        content +=
            role + ":\n";

        content +=
            message.content +
            "\n\n";

    });


    const blob =
        new Blob(
            [content],
            {
                type:
                    "text/plain;charset=utf-8"
            }
        );


    const url =
        URL.createObjectURL(blob);


    const link =
        document.createElement("a");


    link.href = url;

    link.download =
        "medai-chat.txt";


    document.body.appendChild(link);

    link.click();

    link.remove();

    URL.revokeObjectURL(url);
}


function toggleImageSearch() {

    const panel =
        document.getElementById(
            "imagePanel"
        );


    panel.style.display =
        panel.style.display === "block"
            ? "none"
            : "block";


    if (panel.style.display === "block") {

        document.getElementById(
            "imageQuery"
        ).focus();
    }
}


async function searchImages() {

    const query =
        document.getElementById(
            "imageQuery"
        )
        .value
        .trim();


    const results =
        document.getElementById(
            "imageResults"
        );


    if (!query) {
        return;
    }


    results.innerHTML =
        "<p>🔍 Searching images...</p>";


    try {

        const response =
            await fetch(
                "/images?q=" +
                encodeURIComponent(query)
            );


        const data =
            await response.json();


        if (!response.ok) {

            let message =
                data.error ||
                "Image search failed.";

            if (data.details) {
                message +=
                    "<br><small>" +
                    String(data.details) +
                    "</small>";
            }

            throw new Error(message);
        }


        results.innerHTML = "";


        if (
            !data.images ||
            data.images.length === 0
        ) {

            results.innerHTML =
                "<p>No images found.</p>";

            return;
        }


        const grid =
            document.createElement("div");

        grid.className =
            "image-grid";


        data.images.forEach(function(image) {

            const card =
                document.createElement("div");

            card.className =
                "image-card";


            const img =
                document.createElement("img");

            img.src =
                image.thumbnail;

            img.alt =
                image.title;

            img.loading =
                "lazy";


            card.appendChild(img);


            const info =
                document.createElement("div");

            info.className =
                "image-info";


            const title =
                document.createElement("div");

            title.textContent =
                image.title;


            const link =
                document.createElement("a");

            link.href =
                image.page;

            link.target =
                "_blank";

            link.rel =
                "noopener noreferrer";

            link.textContent =
                "Open Wikimedia source";


            info.appendChild(title);

            info.appendChild(
                document.createElement("br")
            );

            info.appendChild(link);


            card.appendChild(info);

            grid.appendChild(card);

        });


        results.appendChild(grid);


    } catch (error) {

        results.innerHTML =
            '<div class="error-box">⚠️ ' +
            error.message +
            "</div>";
    }
}


function toggleUpload() {

    const panel =
        document.getElementById(
            "uploadPanel"
        );


    panel.style.display =
        panel.style.display === "block"
            ? "none"
            : "block";
}


function previewImage(event) {

    const file =
        event.target.files[0];


    const preview =
        document.getElementById(
            "imagePreview"
        );


    if (!file) {

        preview.style.display =
            "none";

        return;
    }


    if (!file.type.startsWith("image/")) {

        alert(
            "Please select an image."
        );

        event.target.value = "";

        return;
    }


    preview.src =
        URL.createObjectURL(file);


    preview.style.display =
        "block";
}


function fileToBase64(file) {

    return new Promise(function(resolve, reject) {

        const reader =
            new FileReader();


        reader.onload = function() {
            resolve(reader.result);
        };


        reader.onerror = function() {
            reject(
                new Error(
                    "Could not read image."
                )
            );
        };


        reader.readAsDataURL(file);

    });
}


async function analyzeImage() {

    const file =
        document.getElementById(
            "imageFile"
        ).files[0];


    const question =
        document.getElementById(
            "imageQuestion"
        ).value.trim();


    if (!file) {

        alert(
            "Please select an image first."
        );

        return;
    }


    if (!file.type.startsWith("image/")) {

        alert(
            "Please select a valid image."
        );

        return;
    }


    if (file.size > 8 * 1024 * 1024) {

        alert(
            "Please use an image smaller than 8 MB."
        );

        return;
    }


    thinking.style.display =
        "block";


    try {

        const base64 =
            await fileToBase64(file);


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
                        image: base64,

                        question:
                            question ||
                            "Describe this image."
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Image analysis failed."
            );
        }


        messages.push({
            role: "user",
            content:
                "📷 Image question: " +
                (
                    question ||
                    "Describe this image."
                )
        });


        messages.push({
            role: "assistant",
            content: data.answer
        });


        saveMessages();

        renderMessages();


    } catch (error) {

        messages.push({
            role: "assistant",
            content:
                "⚠️ " + error.message
        });

        saveMessages();

        renderMessages();


    } finally {

        thinking.style.display =
            "none";
    }
}


function checkMedicalSafety(text) {

    const lower =
        text.toLowerCase();


    const medicalWords = [
        "doctor",
        "medicine",
        "medication",
        "symptom",
        "disease",
        "pain",
        "fever",
        "cough",
        "blood",
        "injury",
        "hospital",
        "medical",
        "health",
        "tablet",
        "pill",
        "دوا",
        "درمل",
        "ناروغ",
        "ناروغي",
        "درد",
        "تبه",
        "روغتیا",
        "ډاکټر",
        "بیماری",
        "پزشک"
    ];


    const emergencyWords = [
        "chest pain",
        "difficulty breathing",
        "can't breathe",
        "cannot breathe",
        "severe bleeding",
        "unconscious",
        "stroke",
        "heart attack",
        "poisoning",
        "seizure",
        "شدید خونریزی",
        "سخت نفس",
        "د ساه",
        "ډېر خونریزي",
        "بې هوشه",
        "تشنج"
    ];


    const isMedical =
        medicalWords.some(function(word) {
            return lower.includes(word);
        });


    const isEmergency =
        emergencyWords.some(function(word) {
            return lower.includes(word);
        });


    document.getElementById(
        "medicalWarning"
    ).style.display =
        isMedical
            ? "block"
            : "none";


    document.getElementById(
        "emergencyWarning"
    ).style.display =
        isEmergency
            ? "block"
            : "none";
}


loadDarkMode();

loadMessages();

</script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/health")
def health():
    return jsonify({
        "service": "MedAI",
        "status": "ok"
    })


@app.route("/chat", methods=["POST"])
def chat_api():

    if not GROQ_API_KEY:
        return jsonify({
            "error": "GROQ_API_KEY is not configured in Vercel."
        }), 500

    data = request.get_json(silent=True) or {}

    incoming_messages = data.get("messages", [])

    if not isinstance(incoming_messages, list):
        return jsonify({
            "error": "Invalid messages format."
        }), 400

    clean_messages = []

    for message in incoming_messages[-20:]:

        if not isinstance(message, dict):
            continue

        role = message.get("role")
        content = message.get("content")

        if role not in ["user", "assistant"]:
            continue

        if not isinstance(content, str):
            continue

        content = content.strip()

        if not content:
            continue

        clean_messages.append({
            "role": role,
            "content": content
        })

    if not clean_messages:
        return jsonify({
            "error": "Please enter a message."
        }), 400

    groq_messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    groq_messages.extend(clean_messages)

    payload = {
        "model": TEXT_MODEL,
        "messages": groq_messages,
        "temperature": 0.7,
        "max_tokens": 1200
    }

    headers = {
        "Authorization": "Bearer " + GROQ_API_KEY,
        "Content-Type": "application/json"
    }

    try:

        response = requests.post(
            GROQ_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

    except requests.exceptions.Timeout:

        return jsonify({
            "error": "AI request timed out."
        }), 504

    except requests.exceptions.RequestException as error:

        return jsonify({
            "error": "Could not connect to Groq.",
            "details": str(error)
        }), 502

    if response.status_code == 401:

        return jsonify({
            "error": "Groq API key is invalid."
        }), 401

    if response.status_code == 403:

        return jsonify({
            "error": "Groq API access was denied."
        }), 403

    if response.status_code == 429:

        return jsonify({
            "error": "Groq free limit has been reached. Please try again later."
        }), 429

    if response.status_code >= 400:

        try:
            error_data = response.json()
        except Exception:
            error_data = {}

        error_obj = error_data.get(
            "error",
            {}
        )

        if isinstance(error_obj, dict):

            message = error_obj.get(
                "message",
                "Groq API error."
            )

        else:

            message = str(error_obj)

        return jsonify({
            "error": message
        }), response.status_code

    try:

        result = response.json()

        answer = (
            result["choices"][0]
            ["message"]
            ["content"]
        )

    except (
        KeyError,
        IndexError,
        TypeError,
        ValueError
    ):

        return jsonify({
            "error": "Invalid response from Groq."
        }), 502

    return jsonify({
        "answer": answer
    })


@app.route("/images")
def image_search():

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:

        return jsonify({
            "error": "Please enter an image search term."
        }), 400

    api_url = (
        "https://commons.wikimedia.org/w/api.php"
    )

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

    headers = {
        "User-Agent":
            "MedAI/1.0 (AI assistant)"
    }

    try:

        response = requests.get(
            api_url,
            params=params,
            headers=headers,
            timeout=25
        )

        response.raise_for_status()

        data = response.json()

    except requests.exceptions.Timeout:

        return jsonify({
            "error":
                "Wikimedia image search timed out."
        }), 504

    except requests.exceptions.RequestException as error:

        return jsonify({
            "error":
                "Could not connect to Wikimedia Commons.",
            "details":
                str(error)
        }), 502

    except ValueError:

        return jsonify({
            "error":
                "Wikimedia returned an invalid response."
        }), 502

    pages = (
        data
        .get("query", {})
        .get("pages", [])
    )

    images = []

    for page in pages:

        image_info = page.get(
            "imageinfo",
            []
        )

        if not image_info:
            continue

        info = image_info[0]

        original = info.get("url")

        thumbnail = info.get(
            "thumburl"
        )

        if not thumbnail:
            thumbnail = original

        if not thumbnail:
            continue

        title = page.get(
            "title",
            "Image"
        )

        page_url = (
            "https://commons.wikimedia.org/wiki/"
            + title.replace(" ", "_")
        )

        images.append({
            "title":
                title.replace(
                    "File:",
                    ""
                ),
            "thumbnail":
                thumbnail,
            "original":
                original,
            "page":
                page_url
        })

    return jsonify({
        "images": images
    })


@app.route("/analyze-image", methods=["POST"])
def analyze_image():

    if not GROQ_API_KEY:

        return jsonify({
            "error":
                "GROQ_API_KEY is not configured."
        }), 500

    data = request.get_json(
        silent=True
    ) or {}

    image = data.get("image")

    question = data.get(
        "question",
        "Describe this image."
    )

    if not image:

        return jsonify({
            "error":
                "No image was provided."
        }), 400

    if not isinstance(image, str):

        return jsonify({
            "error":
                "Invalid image data."
        }), 400

    if not image.startswith("data:image/"):

        return jsonify({
            "error":
                "Invalid image format."
        }), 400

    if len(image) > 12_000_000:

        return jsonify({
            "error":
                "Image is too large. Please use an image smaller than 8 MB."
        }), 413

    vision_prompt = f"""
Analyze this image carefully.

User question:
{question}

Rules:
- Answer in the same language as the user.
- Describe only what you can reasonably identify.
- Do not invent details.
- If this is a medical image, do not provide a definitive diagnosis.
- For medical interpretation, recommend a qualified healthcare professional.
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
        "max_completion_tokens": 1200
    }

    headers = {
        "Authorization":
            "Bearer " + GROQ_API_KEY,
        "Content-Type":
            "application/json"
    }

    try:

        response = requests.post(
            GROQ_URL,
            headers=headers,
            json=payload,
            timeout=90
        )

    except requests.exceptions.Timeout:

        return jsonify({
            "error":
                "Image analysis timed out."
        }), 504

    except requests.exceptions.RequestException as error:

        return jsonify({
            "error":
                "Could not connect to Groq.",
            "details":
                str(error)
        }), 502

    if response.status_code == 401:

        return jsonify({
            "error":
                "Groq API key is invalid."
        }), 401

    if response.status_code == 403:

        return jsonify({
            "error":
                "Groq image access was denied."
        }), 403

    if response.status_code == 429:

        return jsonify({
            "error":
                "Groq vision rate limit has been reached."
        }), 429

    if response.status_code >= 400:

        try:
            details = response.json()
        except Exception:
            details = response.text

        return jsonify({
            "error":
                "Groq image analysis error.",
            "details":
                details
        }), response.status_code

    try:

        result = response.json()

        answer = (
            result["choices"][0]
            ["message"]
            ["content"]
        )

    except (
        KeyError,
        IndexError,
        TypeError,
        ValueError
    ):

        return jsonify({
            "error":
                "Invalid image analysis response."
        }), 502

    return jsonify({
        "answer": answer
    })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )
