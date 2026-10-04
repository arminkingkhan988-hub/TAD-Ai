import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """
You are MedAI, a helpful AI assistant.

You can answer general questions about:
- Education
- Science
- Mathematics
- Programming and coding
- Technology
- History
- Business
- Writing
- General knowledge
- Health and medical topics

Important rules:
1. Answer in the same language as the user.
2. Support Pashto, Dari, and English.
3. For medical questions, provide safe general information.
4. Do not pretend to be a doctor.
5. For emergencies or serious symptoms, recommend contacting a qualified healthcare professional or emergency service.
6. Be clear, friendly, and useful.
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
            transition: 0.2s;
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
            font-size: 13px;
            opacity: 0.65;
            display: block;
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
            padding: 9px 12px;
            cursor: pointer;
            background: #e8eef7;
            color: #172033;
            font-size: 14px;
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
            font-size: 14px;
        }

        .search-box {
            display: none;
            padding: 10px 18px;
            background: white;
            border-bottom: 1px solid #ddd;
        }

        body.dark .search-box {
            background: #1f2937;
            border-color: #374151;
        }

        .search-box input {
            width: 100%;
            padding: 11px;
            border: 1px solid #ccd3df;
            border-radius: 8px;
            outline: none;
            font-size: 15px;
        }

        body.dark .search-box input {
            background: #111827;
            color: white;
            border-color: #4b5563;
        }

        .search-results {
            padding: 8px 18px;
            font-size: 13px;
            opacity: 0.8;
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
            <button onclick="toggleSearch()">🔍 Search</button>
            <button onclick="exportChat()">📥 Export</button>
            <button onclick="toggleDark()">🌙</button>
        </div>
    </header>

    <div class="search-box" id="searchBox">
        <input
            id="searchInput"
            type="text"
            placeholder="Search in this chat..."
            oninput="searchChat()"
        >
        <div class="search-results" id="searchResults"></div>
    </div>

    <main class="chat" id="chat">
    </main>

    <div class="thinking" id="thinking">
        🤔 MedAI is thinking...
    </div>

    <div class="composer">
        <textarea
            id="messageInput"
            placeholder="Ask MedAI anything..."
            onkeydown="handleKey(event)"
        ></textarea>

        <button class="send" onclick="sendMessage()">
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
            const saved = localStorage.getItem("medai_messages");

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
                    <p>Ask me anything about education, science, coding, health, technology and more.</p>
                </div>
            `;
            return;
        }

        messages.forEach(function(message, index) {
            const div = document.createElement("div");

            div.className =
                "message " +
                (message.role === "user" ? "user" : "assistant");

            const text = document.createElement("div");
            text.textContent = message.content;

            div.appendChild(text);

            if (message.role === "assistant") {
                const actions = document.createElement("div");
                actions.className = "message-actions";

                const copy = document.createElement("button");
                copy.className = "copy-btn";
                copy.textContent = "📋 Copy";

                copy.onclick = function() {
                    copyText(message.content, copy);
                };

                actions.appendChild(copy);
                div.appendChild(actions);
            }

            chat.appendChild(div);
        });

        chat.scrollTop = chat.scrollHeight;
    }

    async function sendMessage() {
        const text = input.value.trim();

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

        thinking.style.display = "block";

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

            if (!response.ok) {
                throw new Error(
                    data.error || "Something went wrong."
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
                content: "⚠️ " + error.message
            });

            saveMessages();
            renderMessages();

        } finally {
            thinking.style.display = "none";
        }
    }

    function handleKey(event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    }

    function copyText(text, button) {
        navigator.clipboard.writeText(text)
            .then(function() {
                const oldText = button.textContent;
                button.textContent = "✅ Copied";

                setTimeout(function() {
                    button.textContent = oldText;
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
        localStorage.removeItem("medai_messages");

        renderMessages();

        document.getElementById("searchInput").value = "";
        document.getElementById("searchResults").textContent = "";
    }

    function toggleDark() {
        document.body.classList.toggle("dark");

        localStorage.setItem(
            "medai_dark",
            document.body.classList.contains("dark")
        );
    }

    function loadDarkMode() {
        const dark = localStorage.getItem("medai_dark");

        if (dark === "true") {
            document.body.classList.add("dark");
        }
    }

    function toggleSearch() {
        const box = document.getElementById("searchBox");

        if (box.style.display === "block") {
            box.style.display = "none";
            document.getElementById("searchInput").value = "";
            document.getElementById("searchResults").textContent = "";
        } else {
            box.style.display = "block";
            document.getElementById("searchInput").focus();
        }
    }

    function searchChat() {
        const query =
            document.getElementById("searchInput")
                .value
                .trim()
                .toLowerCase();

        const results =
            document.getElementById("searchResults");

        if (!query) {
            results.textContent = "";
            renderMessages();
            return;
        }

        const matches = messages.filter(function(message) {
            return message.content
                .toLowerCase()
                .includes(query);
        });

        results.textContent =
            matches.length +
            " matching message(s) found.";

        chat.innerHTML = "";

        if (matches.length === 0) {
            chat.innerHTML = `
                <div class="empty">
                    🔍 No matching messages found.
                </div>
            `;
            return;
        }

        matches.forEach(function(message) {
            const div = document.createElement("div");

            div.className =
                "message " +
                (message.role === "user"
                    ? "user"
                    : "assistant");

            const text = document.createElement("div");
            text.textContent = message.content;

            div.appendChild(text);
            chat.appendChild(div);
        });
    }

    function exportChat() {
        if (messages.length === 0) {
            alert("There is no chat to export.");
            return;
        }

        let content = "MedAI Chat Export\n";
        content += "=================\n\n";

        messages.forEach(function(message) {
            const role =
                message.role === "user"
                    ? "You"
                    : "MedAI";

            content += role + ":\n";
            content += message.content + "\n\n";
        });

        const blob = new Blob(
            [content],
            { type: "text/plain;charset=utf-8" }
        );

        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");

        link.href = url;
        link.download =
            "medai-chat-" +
            new Date().toISOString()
                .slice(0, 10) +
            ".txt";

        document.body.appendChild(link);
        link.click();
        link.remove();

        URL.revokeObjectURL(url);
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
            "error": "GROQ_API_KEY is not configured."
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
        "model": MODEL,
        "messages": groq_messages,
        "temperature": 0.7,
        "max_tokens": 1200
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
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
            "error": "AI request timed out. Please try again."
        }), 504

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to the AI service."
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
            message = (
                error_data.get("error", {})
                .get("message", "Groq API error.")
            )
        except Exception:
            message = "Groq API error."

        return jsonify({
            "error": message
        }), response.status_code

    try:
        result = response.json()

        answer = (
            result["choices"][0]["message"]["content"]
        )

    except (KeyError, IndexError, TypeError, ValueError):
        return jsonify({
            "error": "Invalid response received from Groq."
        }), 502

    return jsonify({
        "answer": answer
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
