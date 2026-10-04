import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """
You are MedAI, a helpful AI assistant.

Rules:
- Answer in the same language as the user.
- Support Pashto, Dari, and English.
- Help with education, science, coding, mathematics, technology,
  history, business, writing, and general questions.
- For medical questions, provide general educational information only.
- Do not pretend to be a doctor.
- For emergencies, advise contacting a qualified healthcare professional
  or local emergency medical services.
- Be clear, friendly, accurate, and useful.
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
    background: #f5f7fb;
    color: #111827;
    transition: 0.2s;
}

body.dark {
    background: #111827;
    color: #f9fafb;
}

.app {
    max-width: 1000px;
    margin: auto;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.header {
    height: 65px;
    padding: 12px 16px;
    background: #111827;
    color: white;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.logo {
    font-size: 21px;
    font-weight: bold;
}

.header-buttons {
    display: flex;
    gap: 8px;
}

.header button {
    border: 0;
    border-radius: 9px;
    padding: 9px 12px;
    cursor: pointer;
    font-size: 14px;
}

.new-btn {
    background: white;
    color: #111827;
}

.theme-btn {
    background: #374151;
    color: white;
}

.chat {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    min-height: calc(100vh - 145px);
}

.message-row {
    display: flex;
    margin: 14px 0;
}

.message-row.user-row {
    justify-content: flex-end;
}

.message-box {
    max-width: 82%;
    border-radius: 15px;
    padding: 12px 14px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
}

.user-message {
    background: #2563eb;
    color: white;
}

.ai-message {
    background: white;
    color: #111827;
    border: 1px solid #e5e7eb;
}

body.dark .ai-message {
    background: #1f2937;
    color: #f9fafb;
    border-color: #374151;
}

.message-actions {
    margin-top: 7px;
    display: flex;
    gap: 6px;
}

.copy-btn {
    border: 1px solid #d1d5db;
    background: transparent;
    border-radius: 7px;
    padding: 5px 8px;
    cursor: pointer;
    font-size: 12px;
}

body.dark .copy-btn {
    color: white;
    border-color: #4b5563;
}

.input-area {
    position: sticky;
    bottom: 0;
    padding: 12px;
    background: rgba(255,255,255,0.96);
    border-top: 1px solid #ddd;
    display: flex;
    gap: 9px;
}

body.dark .input-area {
    background: rgba(17,24,39,0.96);
    border-color: #374151;
}

textarea {
    flex: 1;
    resize: none;
    min-height: 50px;
    max-height: 150px;
    padding: 13px;
    border: 1px solid #d1d5db;
    border-radius: 12px;
    font-size: 16px;
    outline: none;
    background: white;
    color: #111827;
}

body.dark textarea {
    background: #1f2937;
    color: white;
    border-color: #4b5563;
}

.send-btn {
    background: #2563eb;
    color: white;
    border: 0;
    border-radius: 12px;
    padding: 0 18px;
    cursor: pointer;
    font-size: 15px;
}

.send-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.welcome {
    text-align: center;
    padding: 70px 20px;
}

.welcome h2 {
    margin-bottom: 10px;
}

.welcome p {
    opacity: 0.7;
}

.loading {
    opacity: 0.65;
}

@media (max-width: 600px) {

    .header {
        height: 60px;
    }

    .logo {
        font-size: 18px;
    }

    .header button {
        padding: 8px 9px;
    }

    .chat {
        padding: 12px;
    }

    .message-box {
        max-width: 94%;
    }

    .input-area {
        padding: 8px;
    }

    textarea {
        font-size: 15px;
    }

    .send-btn {
        padding: 0 14px;
    }
}
</style>
</head>

<body>

<div class="app">

    <div class="header">

        <div class="logo">
            🤖 MedAI
        </div>

        <div class="header-buttons">

            <button class="theme-btn" onclick="toggleTheme()">
                🌙
            </button>

            <button class="new-btn" onclick="newChat()">
                New Chat
            </button>

        </div>

    </div>


    <div id="chat" class="chat">

        <div class="welcome" id="welcome">

            <h2>👋 Welcome to MedAI</h2>

            <p>
                Ask me anything in Pashto, Dari, or English.
            </p>

        </div>

    </div>


    <div class="input-area">

        <textarea
            id="message"
            placeholder="Type your message..."
            onkeydown="handleKey(event)"
        ></textarea>

        <button
            id="sendBtn"
            class="send-btn"
            onclick="sendMessage()"
        >
            Send
        </button>

    </div>

</div>


<script>

let messages = [];


// -------------------------
// Load saved history
// -------------------------

function loadHistory() {

    try {

        const saved = localStorage.getItem("medai_messages");

        if (saved) {

            messages = JSON.parse(saved);

            messages.forEach(function(message) {

                addMessage(
                    message.content,
                    message.role,
                    false
                );

            });

        }

    } catch (error) {

        messages = [];

    }
}


// -------------------------
// Save history
// -------------------------

function saveHistory() {

    try {

        localStorage.setItem(
            "medai_messages",
            JSON.stringify(messages)
        );

    } catch (error) {

        console.log("History could not be saved.");

    }
}


// -------------------------
// Add message
// -------------------------

function addMessage(text, role, showCopy = true) {

    const chat = document.getElementById("chat");

    const welcome = document.getElementById("welcome");

    if (welcome) {
        welcome.remove();
    }

    const row = document.createElement("div");

    row.className =
        "message-row " +
        (role === "user" ? "user-row" : "");


    const box = document.createElement("div");

    box.className =
        "message-box " +
        (role === "user"
            ? "user-message"
            : "ai-message");


    box.textContent = text;


    if (role === "assistant" && showCopy) {

        const actions = document.createElement("div");

        actions.className = "message-actions";


        const copyButton = document.createElement("button");

        copyButton.className = "copy-btn";

        copyButton.textContent = "📋 Copy";


        copyButton.onclick = async function() {

            try {

                await navigator.clipboard.writeText(text);

                copyButton.textContent = "✅ Copied";

                setTimeout(function() {

                    copyButton.textContent = "📋 Copy";

                }, 1500);

            } catch (error) {

                copyButton.textContent = "❌ Failed";

            }

        };


        actions.appendChild(copyButton);

        box.appendChild(actions);
    }


    row.appendChild(box);

    chat.appendChild(row);

    chat.scrollTop = chat.scrollHeight;


    return row;
}


// -------------------------
// Send message
// -------------------------

async function sendMessage() {

    const input = document.getElementById("message");

    const sendBtn = document.getElementById("sendBtn");

    const text = input.value.trim();


    if (!text) {
        return;
    }


    addMessage(text, "user");

    messages.push({
        role: "user",
        content: text
    });

    saveHistory();


    input.value = "";

    sendBtn.disabled = true;


    const loading = addMessage(
        "⏳ Thinking...",
        "assistant",
        false
    );

    loading.classList.add("loading");


    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                messages: messages
            })

        });


        const data = await response.json();


        loading.remove();


        if (!response.ok) {

            addMessage(
                "❌ " + (
                    data.error ||
                    "Something went wrong."
                ),
                "assistant"
            );

            sendBtn.disabled = false;

            return;
        }


        const answer =
            data.answer ||
            "No answer received.";


        addMessage(
            answer,
            "assistant"
        );


        messages.push({
            role: "assistant",
            content: answer
        });


        saveHistory();


    } catch (error) {

        loading.remove();


        addMessage(
            "❌ Connection error. Please try again.",
            "assistant"
        );

    }


    sendBtn.disabled = false;

    input.focus();
}


// -------------------------
// Enter key
// -------------------------

function handleKey(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();
    }
}


// -------------------------
// New Chat
// -------------------------

function newChat() {

    if (
        messages.length > 0 &&
        !confirm("Start a new chat?")
    ) {
        return;
    }


    messages = [];


    localStorage.removeItem(
        "medai_messages"
    );


    document.getElementById("chat").innerHTML = `

        <div class="welcome" id="welcome">

            <h2>👋 Welcome to MedAI</h2>

            <p>
                Ask me anything in Pashto, Dari, or English.
            </p>

        </div>

    `;
}


// -------------------------
// Dark / Light Mode
// -------------------------

function toggleTheme() {

    document.body.classList.toggle("dark");


    const dark =
        document.body.classList.contains("dark");


    localStorage.setItem(
        "medai_theme",
        dark ? "dark" : "light"
    );
}


// -------------------------
// Load theme
// -------------------------

function loadTheme() {

    const theme =
        localStorage.getItem("medai_theme");


    if (theme === "dark") {

        document.body.classList.add("dark");

    }
}


// -------------------------
// Start
// -------------------------

loadTheme();

loadHistory();

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
def chat():

    if not GROQ_API_KEY:

        return jsonify({
            "error": "GROQ_API_KEY is not configured in Vercel."
        }), 500


    data = request.get_json(silent=True) or {}

    user_messages = data.get("messages", [])


    if not user_messages:

        return jsonify({
            "error": "No message provided."
        }), 400


    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]


    for msg in user_messages[-20:]:

        role = msg.get("role")

        content = msg.get("content")


        if (
            role in ["user", "assistant"]
            and content
        ):

            messages.append({
                "role": role,
                "content": str(content)
            })


    try:

        response = requests.post(

            GROQ_URL,

            headers={
                "Authorization":
                    f"Bearer {GROQ_API_KEY}",

                "Content-Type":
                    "application/json"
            },

            json={

                "model": MODEL,

                "messages": messages,

                "temperature": 0.7,

                "max_tokens": 1200
            },

            timeout=55
        )


        if response.status_code == 429:

            return jsonify({
                "error":
                    "Groq rate limit reached. Please try again later."
            }), 429


        if response.status_code in [401, 403]:

            return jsonify({
                "error":
                    "Groq API key is invalid or not authorized."
            }), response.status_code


        if response.status_code >= 400:

            try:

                details = response.json()

            except Exception:

                details = response.text


            return jsonify({

                "error":
                    "Groq API error",

                "details":
                    details

            }), response.status_code


        result = response.json()


        answer = (

            result
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content")
        )


        if not answer:

            return jsonify({
                "error":
                    "No answer returned by Groq."
            }), 500


        return jsonify({
            "answer": answer
        })


    except requests.exceptions.Timeout:

        return jsonify({
            "error":
                "Groq request timed out. Please try again."
        }), 504


    except Exception as e:

        return jsonify({

            "error":
                "Server error",

            "details":
                str(e)

        }), 500


if __name__ == "__main__":
    app.run()
