import os
import requests

from flask import Flask, request, jsonify, render_template_string


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)


# =========================================================
# GEMINI SETTINGS
# =========================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

GEMINI_MODEL = "gemini-2.5-flash"

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    + GEMINI_MODEL
    + ":generateContent"
)


# =========================================================
# HTML
# =========================================================

HTML = """
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

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #ffffff;
    color: #111827;
}

body.dark {
    background: #212121;
    color: #ffffff;
}

.app {
    min-height: 100vh;
    display: flex;
}

.sidebar {
    width: 250px;
    background: #f7f7f8;
    border-right: 1px solid #ddd;
    padding: 18px;
}

.dark .sidebar {
    background: #171717;
    border-color: #333;
}

.logo {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 25px;
}

.new-chat,
.theme-btn {
    width: 100%;
    padding: 12px;
    border-radius: 10px;
    border: 1px solid #ddd;
    background: white;
    cursor: pointer;
    margin-bottom: 10px;
    font-size: 15px;
}

.dark .new-chat,
.dark .theme-btn {
    background: #222;
    color: white;
    border-color: #444;
}

.main {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.header {
    height: 60px;
    border-bottom: 1px solid #ddd;
    display: flex;
    align-items: center;
    padding: 0 20px;
    font-weight: bold;
}

.dark .header {
    border-color: #333;
}

.chat {
    flex: 1;
    overflow-y: auto;
    padding: 25px 15px 150px;
}

.messages {
    max-width: 850px;
    margin: auto;
}

.welcome {
    text-align: center;
    margin-top: 15vh;
}

.welcome h1 {
    font-size: 34px;
}

.welcome p {
    color: #777;
}

.message {
    display: flex;
    gap: 12px;
    margin: 25px 0;
}

.avatar {
    width: 35px;
    height: 35px;
    min-width: 35px;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    color: white;
    font-weight: bold;
}

.user {
    background: #111827;
}

.ai {
    background: #10a37f;
}

.message-text {
    white-space: pre-wrap;
    line-height: 1.7;
    overflow-wrap: anywhere;
}

.composer-area {
    position: fixed;
    bottom: 0;
    left: 250px;
    right: 0;
    padding: 15px;
    background: linear-gradient(
        transparent,
        rgba(255,255,255,.98) 25%
    );
}

.dark .composer-area {
    background: linear-gradient(
        transparent,
        rgba(33,33,33,.98) 25%
    );
}

.composer {
    max-width: 850px;
    margin: auto;
    display: flex;
    gap: 8px;
    border: 1px solid #ccc;
    border-radius: 15px;
    padding: 8px;
    background: white;
}

.dark .composer {
    background: #2b2b2b;
    border-color: #444;
}

textarea {
    flex: 1;
    border: none;
    outline: none;
    resize: none;
    padding: 10px;
    font-size: 16px;
    background: transparent;
    color: inherit;
    min-height: 42px;
}

button {
    border: none;
    cursor: pointer;
}

.send {
    width: 45px;
    height: 45px;
    border-radius: 10px;
    background: #111827;
    color: white;
    font-size: 20px;
}

.loading {
    color: #777;
}

@media(max-width: 700px) {

    .sidebar {
        display: none;
    }

    .composer-area {
        left: 0;
    }

    .welcome h1 {
        font-size: 27px;
    }

}

</style>

</head>


<body>

<div class="app">

    <aside class="sidebar">

        <div class="logo">
            🩺 MedAI
        </div>

        <button
            class="new-chat"
            onclick="newChat()"
        >
            ＋ New Chat
        </button>

        <button
            class="theme-btn"
            onclick="toggleTheme()"
        >
            🌙 Dark / Light
        </button>

    </aside>


    <main class="main">

        <header class="header">
            MedAI
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
                        په پښتو، دري یا English کې پوښتنه وکړئ.
                    </p>

                </div>

            </div>

        </section>


        <div class="composer-area">

            <div class="composer">

                <textarea
                    id="message"
                    placeholder="Message MedAI..."
                    rows="1"
                    onkeydown="handleKey(event)"
                ></textarea>

                <button
                    class="send"
                    id="send"
                    onclick="sendMessage()"
                >
                    ↑
                </button>

            </div>

        </div>

    </main>

</div>


<script>

const messageInput =
    document.getElementById("message");

const messages =
    document.getElementById("messages");

const sendButton =
    document.getElementById("send");

const chat =
    document.getElementById("chat");


function addMessage(role, text) {

    const welcome =
        document.getElementById("welcome");

    if (welcome) {
        welcome.remove();
    }

    const row =
        document.createElement("div");

    row.className =
        "message";

    const avatar =
        document.createElement("div");

    avatar.className =
        "avatar " +
        (role === "user" ? "user" : "ai");

    avatar.textContent =
        role === "user" ? "U" : "AI";

    const content =
        document.createElement("div");

    content.className =
        "message-text";

    content.textContent =
        text;

    row.appendChild(avatar);

    row.appendChild(content);

    messages.appendChild(row);

    chat.scrollTop =
        chat.scrollHeight;
}


function showLoading() {

    const row =
        document.createElement("div");

    row.id =
        "loading";

    row.className =
        "message";

    const avatar =
        document.createElement("div");

    avatar.className =
        "avatar ai";

    avatar.textContent =
        "AI";

    const content =
        document.createElement("div");

    content.className =
        "message-text loading";

    content.textContent =
        "⏳ MedAI فکر کوي...";

    row.appendChild(avatar);

    row.appendChild(content);

    messages.appendChild(row);

    chat.scrollTop =
        chat.scrollHeight;
}


function removeLoading() {

    const loading =
        document.getElementById("loading");

    if (loading) {
        loading.remove();
    }
}


async function sendMessage() {

    const message =
        messageInput.value.trim();

    if (!message) {
        return;
    }

    addMessage(
        "user",
        message
    );

    messageInput.value = "";

    sendButton.disabled = true;

    showLoading();

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
                        message: message
                    })
                }
            );

        const data =
            await response.json();

        removeLoading();

        if (!response.ok) {

            addMessage(
                "assistant",
                "خطا: " +
                (
                    data.error ||
                    "Unknown error"
                )
            );

            return;
        }

        addMessage(
            "assistant",
            data.answer ||
            "ځواب ترلاسه نه شو."
        );

    } catch (error) {

        removeLoading();

        addMessage(
            "assistant",
            "د سرور سره اړیکه ونه شوه: " +
            error.message
        );

    } finally {

        sendButton.disabled = false;

        messageInput.focus();
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


function newChat() {

    messages.innerHTML = "";

    const welcome =
        document.createElement("div");

    welcome.className =
        "welcome";

    welcome.id =
        "welcome";

    welcome.innerHTML =
        `
        <h1>How can I help you?</h1>
        <p>
            په پښتو، دري یا English کې پوښتنه وکړئ.
        </p>
        `;

    messages.appendChild(welcome);

    messageInput.value = "";

    messageInput.focus();
}


function toggleTheme() {

    document.body.classList.toggle(
        "dark"
    );

    localStorage.setItem(
        "medai-theme",
        document.body.classList.contains("dark")
            ? "dark"
            : "light"
    );
}


if (
    localStorage.getItem("medai-theme")
    === "dark"
) {

    document.body.classList.add(
        "dark"
    );
}

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
        "status": "ok",
        "service": "MedAI"
    })


# =========================================================
# GEMINI CHAT
# =========================================================

@app.route("/api/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        message = data.get(
            "message",
            ""
        )

        if not isinstance(
            message,
            str
        ):

            message = ""

        message = message.strip()

        if not message:

            return jsonify({
                "error":
                    "مهرباني وکړئ پوښتنه ولیکئ."
            }), 400


        if not GEMINI_API_KEY:

            return jsonify({
                "error":
                    "GEMINI_API_KEY په Vercel کې نشته."
            }), 500


        payload = {

            "contents": [

                {

                    "parts": [

                        {

                            "text":
                            """
You are MedAI, a helpful AI assistant.

Important language rule:
Always answer in the same language as the user.

If the user speaks Pashto,
answer in Pashto.

If the user speaks Dari,
answer in Dari.

If the user speaks English,
answer in English.

You can answer general questions,
education, science, coding, mathematics,
technology, writing, translation,
history, business and health questions.

For medical questions,
give general educational information
and encourage professional medical care
for serious or emergency situations.

User question:
"""
                            + message

                        }

                    ]

                }

            ]

        }


        response = requests.post(

            GEMINI_URL,

            params={
                "key": GEMINI_API_KEY
            },

            headers={
                "Content-Type":
                    "application/json"
            },

            json=payload,

            timeout=45

        )


        if response.status_code != 200:

            print(
                "Gemini API:",
                response.status_code,
                response.text[:1000]
            )

            return jsonify({

                "error":
                    "Gemini API error",

                "status":
                    response.status_code,

                "details":
                    response.text[:1000]

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


        content =
            candidates[0].get(
                "content",
                {}
            )


        parts =
            content.get(
                "parts",
                []
            )


        answer_parts = []


        for part in parts:

            text =
                part.get("text")

            if text:

                answer_parts.append(
                    text
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
                "Gemini ته د غوښتنې وخت ختم شو. بیا هڅه وکړئ."

        }), 504


    except requests.exceptions.RequestException as error:

        print(
            "Request error:",
            repr(error)
        )

        return jsonify({

            "error":
                "Gemini سره اتصال ونه شو."

        }), 502


    except Exception as error:

        print(
            "Server error:",
            repr(error)
        )

        return jsonify({

            "error":
                "Server error: " + str(error)

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
                5000
            )
        ),

        debug=False

    )
