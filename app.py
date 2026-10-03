import os
import requests

from flask import Flask, request, jsonify, render_template_string


app = Flask(__name__)


# =========================================================
# Gemini Configuration
# =========================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
).strip()


# =========================================================
# MedAI System Instructions
# =========================================================

SYSTEM_PROMPT = """
You are MedAI, a helpful AI assistant.

You can help with:

- Medicine and health
- Education
- Science
- Mathematics
- Programming and coding
- History
- Business
- Writing
- General knowledge
- Everyday questions

Language rules:

1. Answer in the same language as the user.
2. Support Pashto, Dari, and English.
3. If the user writes Pashto, answer in Pashto.
4. If the user writes Dari, answer in Dari.
5. If the user writes English, answer in English.

Medical safety:

1. You are an AI assistant, not a doctor.
2. Provide general educational information.
3. Do not claim to diagnose a patient.
4. Do not pretend to replace a doctor.
5. For emergencies, advise the user to seek immediate professional medical help.
6. Be clear, respectful, and helpful.

General behavior:

- Give useful answers.
- Explain difficult topics simply.
- For coding questions, provide practical examples.
- For mathematics, show the important steps.
- Do not unnecessarily repeat the user's question.
"""


# =========================================================
# HTML Interface
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
            background: #f5f7fb;
            color: #111827;
        }


        .app {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }


        header {
            background: #2563eb;
            color: white;
            padding: 16px;
            text-align: center;
            font-size: 22px;
            font-weight: bold;
        }


        .chat {
            width: 100%;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            flex: 1;
        }


        .message {
            margin: 12px 0;
            padding: 14px 16px;
            border-radius: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
        }


        .user {
            background: #dbeafe;
            margin-left: 15%;
        }


        .ai {
            background: white;
            border: 1px solid #e5e7eb;
            margin-right: 15%;
        }


        .input-area {
            position: sticky;
            bottom: 0;
            background: #f5f7fb;
            padding: 15px;
            border-top: 1px solid #ddd;
        }


        .input-box {
            max-width: 900px;
            margin: auto;
            display: flex;
            gap: 10px;
        }


        textarea {
            flex: 1;
            min-height: 55px;
            max-height: 180px;
            resize: vertical;
            padding: 14px;
            border: 1px solid #ccc;
            border-radius: 12px;
            font-size: 16px;
            outline: none;
            font-family: Arial, sans-serif;
        }


        textarea:focus {
            border-color: #2563eb;
        }


        button {
            border: none;
            border-radius: 12px;
            padding: 0 22px;
            background: #2563eb;
            color: white;
            font-size: 16px;
            cursor: pointer;
        }


        button:hover {
            background: #1d4ed8;
        }


        button:disabled {
            background: #9ca3af;
            cursor: not-allowed;
        }


        .status {
            max-width: 900px;
            margin: 8px auto 0;
            color: #666;
            font-size: 14px;
        }


        .welcome {
            text-align: center;
            margin-top: 40px;
            color: #555;
        }


        @media (max-width: 600px) {

            .chat {
                padding: 12px;
            }


            .user,
            .ai {
                margin-left: 0;
                margin-right: 0;
            }


            .input-box {
                flex-direction: column;
            }


            textarea {
                width: 100%;
            }


            button {
                min-height: 48px;
            }

        }

    </style>

</head>


<body>


<div class="app">


    <header>
        🤖 MedAI
    </header>


    <main
        class="chat"
        id="chat"
    >

        <div
            class="welcome"
            id="welcome"
        >
            <h2>Welcome to MedAI</h2>

            <p>
                Ask me anything in Pashto, Dari, or English.
            </p>
        </div>

    </main>


    <div class="input-area">


        <div class="input-box">

            <textarea
                id="message"
                placeholder="Write your question..."
                onkeydown="handleKey(event)"
            ></textarea>


            <button
                id="sendButton"
                onclick="sendMessage()"
            >
                Send
            </button>

        </div>


        <div
            class="status"
            id="status"
        ></div>


    </div>


</div>



<script>


async function sendMessage() {

    const input =
        document.getElementById("message");

    const chat =
        document.getElementById("chat");

    const status =
        document.getElementById("status");

    const button =
        document.getElementById("sendButton");


    const message =
        input.value.trim();


    if (!message) {
        return;
    }


    const welcome =
        document.getElementById("welcome");


    if (welcome) {
        welcome.remove();
    }


    addMessage(
        message,
        "user"
    );


    input.value = "";


    button.disabled = true;

    status.textContent =
        "MedAI is thinking...";


    try {


        const response = await fetch(
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


        if (data.reply) {

            addMessage(
                data.reply,
                "ai"
            );

        }

        else if (data.error) {

            let errorText =
                "Error: " + data.error;


            if (data.status_code) {

                errorText +=
                    "\\nStatus: " +
                    data.status_code;

            }


            if (data.details) {

                errorText +=
                    "\\n\\nDetails: " +
                    data.details;

            }


            addMessage(
                errorText,
                "ai"
            );

        }

        else {

            addMessage(
                "No response received.",
                "ai"
            );

        }


    }

    catch (error) {

        addMessage(
            "Connection error. Please try again.",
            "ai"
        );

    }


    status.textContent = "";

    button.disabled = false;

    input.focus();

}



function addMessage(
    text,
    type
) {

    const chat =
        document.getElementById("chat");


    const div =
        document.createElement("div");


    div.className =
        "message " + type;


    div.textContent = text;


    chat.appendChild(div);


    window.scrollTo({
        top:
            document.body.scrollHeight,
        behavior:
            "smooth"
    });

}



function handleKey(event) {

    if (
        event.key === "Enter"
        &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();

    }

}


</script>


</body>

</html>
"""


# =========================================================
# Home
# =========================================================

@app.route("/")
def home():

    return render_template_string(
        HTML
    )


# =========================================================
# Health Check
# =========================================================

@app.route("/health")
def health():

    return jsonify({
        "service": "MedAI",
        "status": "ok"
    })


# =========================================================
# Gemini Chat API
# =========================================================

@app.route(
    "/api/chat",
    methods=["POST"]
)
def chat():


    # Check API key

    if not GEMINI_API_KEY:

        return jsonify({
            "error":
                "GEMINI_API_KEY is not configured."
        }), 500


    # Read JSON

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


    # Check message

    if not message:

        return jsonify({
            "error":
                "Message is required."
        }), 400


    # Gemini URL

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )


    # Gemini request

    payload = {

        "contents": [

            {

                "role": "user",

                "parts": [

                    {

                        "text":
                            SYSTEM_PROMPT
                            +
                            "\n\nUser question:\n"
                            +
                            message

                    }

                ]

            }

        ],


        "generationConfig": {

            "temperature": 0.7,

            "maxOutputTokens": 2048

        }

    }


    try:


        response = requests.post(

            url,

            headers={

                "Content-Type":
                    "application/json",

                "x-goog-api-key":
                    GEMINI_API_KEY

            },

            json=payload,

            timeout=60

        )


        # Gemini returned an error

        if response.status_code != 200:

            return jsonify({

                "error":
                    "Gemini API error",

                "status_code":
                    response.status_code,

                "details":
                    response.text

            }), response.status_code


        # Convert response to JSON

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
                    "Gemini returned no candidates.",

                "details":
                    result

            }), 500


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


        reply = ""


        for part in parts:

            if "text" in part:

                reply += part["text"]


        if not reply:

            return jsonify({

                "error":
                    "Gemini returned an empty response.",

                "details":
                    result

            }), 500


        return jsonify({

            "reply":
                reply

        })


    except requests.exceptions.Timeout:

        return jsonify({

            "error":
                "Gemini request timed out."

        }), 504


    except requests.exceptions.RequestException as e:

        return jsonify({

            "error":
                "Could not connect to Gemini.",

            "details":
                str(e)

        }), 502


    except Exception as e:

        return jsonify({

            "error":
                "Server error.",

            "details":
                str(e)

        }), 500


# =========================================================
# Local Development
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
