import os
import requests
from flask import Flask, request, jsonify
app = Flask(__name__)
import os
import requests
from flask import Flask, request, jsonify
app = Flask(__name__)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
HTML = r"""
<!DOCTYPE html>
<html lang="ps" dir="rtl">
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
            font-family: Arial, Tahoma, sans-serif;
            background: #f4f7fb;
            color: #172033;
            transition: background 0.3s, color 0.3s;
        }

        body.dark {
            background: #111827;
            color: #f3f4f6;
        }

        .container {
            width: 94%;
            max-width: 1000px;
            margin: auto;
            padding: 20px 0 40px;
        }

        header,
        .card {
            background: #ffffff;
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 18px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.07);
            transition: background 0.3s, color 0.3s;
        }

        body.dark header,
        body.dark .card {
            background: #1f2937;
            color: #f3f4f6;
        }

        .top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }

        h1 {
            margin: 0;
            color: #1677ff;
        }

        h2 {
            margin-top: 0;
        }

        .subtitle {
            margin-top: 8px;
            color: #667085;
        }

        body.dark .subtitle {
            color: #cbd5e1;
        }

        button {
            border: 0;
            border-radius: 12px;
            padding: 11px 15px;
            cursor: pointer;
            font-size: 15px;
            margin: 4px;
        }

        .dark-button {
            background: #111827;
            color: white;
        }

        body.dark .dark-button {
            background: #f3f4f6;
            color: #111827;
        }

        textarea {
            width: 100%;
            min-height: 120px;
            resize: vertical;
            padding: 15px;
            border-radius: 14px;
            border: 1px solid #d0d5dd;
            font-size: 16px;
            outline: none;
            background: white;
            color: #111827;
        }

        body.dark textarea {
            background: #111827;
            color: white;
            border-color: #475569;
        }

        .send-button {
            background: #1677ff;
            color: white;
            width: 100%;
            margin: 10px 0;
            font-weight: bold;
        }

        .voice-button {
            background: #7c3aed;
            color: white;
        }

        .speak-button {
            background: #059669;
            color: white;
        }

        .stop-button {
            background: #dc2626;
            color: white;
        }

        .save-button {
            background: #f59e0b;
            color: white;
        }

        .section-title {
            margin-top: 0;
        }

        #answer {
            line-height: 1.9;
            white-space: pre-wrap;
        }

        .warning {
            background: #fff3cd;
            color: #664d03;
            border-radius: 12px;
            padding: 13px;
            margin-top: 15px;
            line-height: 1.7;
        }

        body.dark .warning {
            background: #4a3b16;
            color: #ffe69c;
        }

        .images {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-top: 15px;
        }

        .images img {
            width: 100%;
            height: 180px;
            object-fit: cover;
            border-radius: 14px;
        }

        .topics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
        }

        .topic-card {
            background: #f8fafc;
            border-radius: 14px;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: 0.2s;
            border: 1px solid #e5e7eb;
        }

        body.dark .topic-card {
            background: #111827;
            border-color: #374151;
        }

        .topic-card:hover {
            transform: translateY(-2px);
            border-color: #1677ff;
        }

        .topic-icon {
            font-size: 30px;
            display: block;
            margin-bottom: 7px;
        }

        .faq-item {
            background: #f8fafc;
            border-radius: 12px;
            margin-bottom: 10px;
            overflow: hidden;
            border: 1px solid #e5e7eb;
        }

        body.dark .faq-item {
            background: #111827;
            border-color: #374151;
        }

        .faq-question {
            width: 100%;
            text-align: right;
            background: transparent;
            margin: 0;
            font-weight: bold;
            color: inherit;
        }

        .faq-answer {
            display: none;
            padding: 0 15px 15px;
            line-height: 1.8;
        }

        .history-item {
            background: #f8fafc;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 8px;
            cursor: pointer;
        }

        body.dark .history-item {
            background: #111827;
        }

        .status {
            text-align: center;
            margin: 10px;
            color: #667085;
        }

        body.dark .status {
            color: #cbd5e1;
        }

        @media (max-width: 600px) {
            .container {
                width: 96%;
                padding-top: 10px;
            }

            header,
            .card {
                padding: 15px;
                border-radius: 14px;
            }

            button {
                width: 100%;
                margin: 5px 0;
            }

            .top button {
                width: auto;
            }
        }
    </style>
</head>

<body>

<div class="container">

    <header>
        <div class="top">
            <div>
                <h1>🩺 MedAI</h1>

                <div class="subtitle">
                    ستاسو هوښیار طبي معلوماتي مرستیال
                </div>
            </div>

            <button
                class="dark-button"
                type="button"
                onclick="toggleDarkMode()"
                id="darkBtn">
                🌙 Dark Mode
            </button>
        </div>
    </header>


    <!-- MEDICAL TOPICS -->

    <div class="card">

        <h2>🗂️ طبي موضوعات</h2>

        <div class="topics">

            <div class="topic-card"
                 onclick="selectTopic('Diabetes')">
                <span class="topic-icon">🩸</span>
                شکر / Diabetes
            </div>

            <div class="topic-card"
                 onclick="selectTopic('Hypertension')">
                <span class="topic-icon">❤️</span>
                لوړ فشار
            </div>

            <div class="topic-card"
                 onclick="selectTopic('Pneumonia')">
                <span class="topic-icon">🫁</span>
                سینه بغل
            </div>

            <div class="topic-card"
                 onclick="selectTopic('Heart disease')">
                <span class="topic-icon">❤️</span>
                د زړه ناروغۍ
            </div>

            <div class="topic-card"
                 onclick="selectTopic('Kidney disease')">
                <span class="topic-icon">🫘</span>
                د پښتورګو ناروغۍ
            </div>

            <div class="topic-card"
                 onclick="selectTopic('Liver disease')">
                <span class="topic-icon">🫀</span>
                د ځیګر ناروغۍ
            </div>

            <div class="topic-card"
                 onclick="selectTopic('Asthma')">
                <span class="topic-icon">🫁</span>
                استما
            </div>

            <div class="topic-card"
                 onclick="selectTopic('Cancer')">
                <span class="topic-icon">🧬</span>
                سرطان
            </div>

        </div>

    </div>


    <!-- CHAT -->

    <div class="card">

        <h2>🤖 له MedAI څخه پوښتنه وکړئ</h2>

        <textarea
            id="msg"
            placeholder="خپله طبي پوښتنه دلته ولیکئ..."></textarea>

        <button
            class="voice-button"
            type="button"
            onclick="startVoice()">
            🎤 په غږ پوښتنه وکړئ
        </button>

        <button
            class="send-button"
            type="button"
            onclick="sendMessage()">
            🔎 پوښتنه واستوئ
        </button>

        <div
            id="status"
            class="status">
        </div>

    </div>


    <!-- ANSWER -->

    <div class="card">

        <h2>📋 ځواب</h2>

        <div id="answer">
            ستاسو ځواب به دلته ښکاره شي.
        </div>

        <div class="warning">
            ⚠️ دا معلومات یوازې د زده کړې او عمومي پوهاوي لپاره دي.
            MedAI د ډاکټر بدیل نه دی. د جدي یا بیړني حالت په صورت کې
            له روغتیايي مسلکي سره اړیکه ونیسئ.
        </div>

        <div style="margin-top:15px;">

            <button
                class="speak-button"
                type="button"
                onclick="speakAnswer()">
                🔊 ځواب واورئ
            </button>

            <button
                class="stop-button"
                type="button"
                onclick="stopSpeaking()">
                ⏹️ غږ ودروئ
            </button>

            <button
                class="save-button"
                type="button"
                onclick="saveFavorite()">
                ⭐ Save
            </button>

        </div>

    </div>


    <!-- IMAGES -->

    <div class="card">

        <h2>🖼️ طبي عکسونه</h2>

        <div
            id="images"
            class="images">
        </div>

    </div>


    <!-- FAQ -->

    <div class="card">

        <h2>❓ عامې پوښتنې (FAQ)</h2>

        <div class="faq-item">

            <button
                class="faq-question"
                type="button"
                onclick="toggleFAQ(this)">
                MedAI څه شی دی؟
            </button>

            <div class="faq-answer">
                MedAI یو معلوماتي طبي AI مرستیال دی چې د طبي موضوعاتو
                په اړه عمومي معلومات وړاندې کوي.
            </div>

        </div>


        <div class="faq-item">

            <button
                class="faq-question"
                type="button"
                onclick="toggleFAQ(this)">
                آیا MedAI تشخیص کوي؟
            </button>

            <div class="faq-answer">
                نه. MedAI باید د مسلکي ډاکټر د معاینې او تشخیص بدیل ونه ګڼل شي.
            </div>

        </div>


        <div class="faq-item">

            <button
                class="faq-question"
                type="button"
                onclick="toggleFAQ(this)">
                آیا زه په خپله ژبه پوښتنه کولی شم؟
            </button>

            <div class="faq-answer">
                هو. پوښتنه په خپله ژبه ولیکئ؛ AI هڅه کوي ځواب هم
                په هماغه ژبه وړاندې کړي.
            </div>

        </div>


        <div class="faq-item">

            <button
                class="faq-question"
                type="button"
                onclick="toggleFAQ(this)">
                آیا طبي عکسونه هم ښيي؟
            </button>

            <div class="faq-answer">
                هو، د اړوندو طبي موضوعاتو لپاره موجود Wikimedia عکسونه
                ښودل کېدای شي.
            </div>

        </div>

    </div>


    <!-- HISTORY -->

    <div class="card">

        <h2>🕘 History</h2>

        <div id="history"></div>

        <button
            type="button"
            onclick="clearHistory()">
            🗑️ History پاکول
        </button>

    </div>


    <!-- FAVORITES -->

    <div class="card">

        <h2>⭐ Saved Questions</h2>

        <div id="favorites"></div>

    </div>

</div>


<script>

/* -------------------------
   DARK MODE
------------------------- */

function toggleDarkMode() {

    document.body.classList.toggle("dark");

    const isDark =
        document.body.classList.contains("dark");

    localStorage.setItem(
        "medai_dark",
        isDark ? "1" : "0"
    );

    updateDarkButton();
}


function updateDarkButton() {

    const button =
        document.getElementById("darkBtn");

    if (!button) {
        return;
    }

    if (
        document.body.classList.contains("dark")
    ) {
        button.innerText = "☀️ Light Mode";
    } else {
        button.innerText = "🌙 Dark Mode";
    }
}


function loadDarkMode() {

    const saved =
        localStorage.getItem("medai_dark");

    if (saved === "1") {
        document.body.classList.add("dark");
    }

    updateDarkButton();
}


/* -------------------------
   MEDICAL TOPICS
------------------------- */

function selectTopic(topic) {

    const message =
        "Please explain " +
        topic +
        " in detail, including definition, causes, types, risk factors, signs and symptoms, diagnosis, treatment, prevention, complications, and important points.";

    document.getElementById("msg").value =
        message;

    document.getElementById("msg").focus();
}


/* -------------------------
   FAQ
------------------------- */

function toggleFAQ(button) {

    const answer =
        button.nextElementSibling;

    if (answer.style.display === "block") {

        answer.style.display = "none";

    } else {

        answer.style.display = "block";
    }
}


/* -------------------------
   VOICE QUESTION
------------------------- */

function startVoice() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {

        alert(
            "ستاسو Chrome د Voice Question ملاتړ نه کوي."
        );

        return;
    }

    const recognition =
        new SpeechRecognition();

    recognition.lang = "ps-AF";

    recognition.interimResults = false;

    recognition.maxAlternatives = 1;


    recognition.onstart = function() {

        document.getElementById("msg").value =
            "🎤 واورېدل کېږي...";
    };


    recognition.onresult = function(event) {

        const text =
            event.results[0][0].transcript;

        document.getElementById("msg").value =
            text;
    };


    recognition.onerror = function() {

        document.getElementById("msg").value = "";

        alert(
            "د غږ په اخیستلو کې ستونزه رامنځته شوه."
        );
    };


    recognition.start();
}


/* -------------------------
   SEND MESSAGE
------------------------- */

async function sendMessage() {

    const message =
        document
            .getElementById("msg")
            .value
            .trim();


    if (!message) {

        alert(
            "مهرباني وکړئ پوښتنه ولیکئ."
        );

        return;
    }


    currentQuestion = message;


    document.getElementById("status").innerText =
        "⏳ ځواب چمتو کېږي...";


    document.getElementById("answer").innerText =
        "مهرباني وکړئ انتظار وکړئ...";


    document.getElementById("images").innerHTML =
        "";


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
                        message: message
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Server error"
            );
        }


        const answer =
            data.answer ||
            "ځواب ونه موندل شو.";


        document.getElementById("answer").innerText =
            answer;


        showImages(
            data.images || []
        );


        saveHistory(
            message,
            answer
        );


        document.getElementById("status").innerText =
            "✅ ځواب چمتو شو.";

    } catch (error) {

        document.getElementById("answer").innerText =
            "❌ ستونزه: " +
            error.message;

        document.getElementById("status").innerText =
            "";
    }
}


/* -------------------------
   MEDICAL IMAGES
------------------------- */

function showImages(images) {

    const container =
        document.getElementById("images");

    container.innerHTML = "";


    images.forEach(function(url) {

        const image =
            document.createElement("img");

        image.src = url;

        image.alt = "Medical image";

        image.loading = "lazy";

        container.appendChild(image);
    });
}


/* -------------------------
   VOICE OUTPUT
------------------------- */

function speakAnswer() {

    const answer =
        document
            .getElementById("answer")
            .innerText
            .trim();


    if (
        !answer ||
        answer ===
        "ستاسو ځواب به دلته ښکاره شي."
    ) {

        alert(
            "لومړی یوه پوښتنه وکړئ."
        );

        return;
    }


    if (
        !("speechSynthesis" in window)
    ) {

        alert(
            "ستاسو Chrome د Voice Output ملاتړ نه کوي."
        );

        return;
    }


    window.speechSynthesis.cancel();


    const speech =
        new SpeechSynthesisUtterance(
            answer
        );


    speech.lang = "en-US";

    speech.rate = 0.9;

    speech.pitch = 1;

    speech.volume = 1;


    window.speechSynthesis.speak(
        speech
    );
}


function stopSpeaking() {

    if (
        "speechSynthesis" in window
    ) {

        window.speechSynthesis.cancel();
    }
}


/* -------------------------
   HISTORY
------------------------- */

function saveHistory(
    question,
    answer
) {

    let history =
        JSON.parse(
            localStorage.getItem(
                "medai_history"
            ) || "[]"
        );


    history.unshift({
        question: question,
        answer: answer,
        date:
            new Date().toLocaleString()
    });


    history =
        history.slice(0, 20);


    localStorage.setItem(
        "medai_history",
        JSON.stringify(history)
    );


    showHistory();
}


function showHistory() {

    const container =
        document.getElementById(
            "history"
        );


    let history =
        JSON.parse(
            localStorage.getItem(
                "medai_history"
            ) || "[]"
        );


    container.innerHTML = "";


    if (history.length === 0) {

        container.innerText =
            "تر اوسه History نشته.";

        return;
    }


    history.forEach(
        function(item) {

            const div =
                document.createElement(
                    "div"
                );


            div.className =
                "history-item";


            div.innerText =
                item.question;


            div.onclick =
                function() {

                    document
                        .getElementById("msg")
                        .value =
                        item.question;


                    document
                        .getElementById("answer")
                        .innerText =
                        item.answer;


                    currentQuestion =
                        item.question;
                };


            container.appendChild(div);
        }
    );
}


function clearHistory() {

    localStorage.removeItem(
        "medai_history"
    );

    showHistory();
}


/* -------------------------
   FAVORITES
------------------------- */

function saveFavorite() {

    if (!currentQuestion) {

        alert(
            "لومړی یوه پوښتنه وکړئ."
        );

        return;
    }


    const answer =
        document
            .getElementById("answer")
            .innerText;


    let favorites =
        JSON.parse(
            localStorage.getItem(
                "medai_favorites"
            ) || "[]"
        );


    favorites.unshift({

        question:
            currentQuestion,

        answer:
            answer
    });


    favorites =
        favorites.slice(0, 30);


    localStorage.setItem(
        "medai_favorites",
        JSON.stringify(favorites)
    );


    showFavorites();


    alert(
        "⭐ پوښتنه Save شوه."
    );
}


function showFavorites() {

    const container =
        document.getElementById(
            "favorites"
        );


    let favorites =
        JSON.parse(
            localStorage.getItem(
                "medai_favorites"
            ) || "[]"
        );


    container.innerHTML = "";


    if (favorites.length === 0) {

        container.innerText =
            "تر اوسه Saved پوښتنې نشته.";

        return;
    }


    favorites.forEach(
        function(item) {

            const div =
                document.createElement(
                    "div"
                );


            div.className =
                "history-item";


            div.innerText =
                "⭐ " +
                item.question;


            div.onclick =
                function() {

                    document
                        .getElementById("msg")
                        .value =
                        item.question;


                    document
                        .getElementById("answer")
                        .innerText =
                        item.answer;


                    currentQuestion =
                        item.question;
                };


            container.appendChild(div);
        }
    );
}


/* -------------------------
   START
------------------------- */

let currentQuestion = "";

loadDarkMode();

showHistory();

showFavorites();

</script>

</body>
</html>
"""


# ==========================================
# MEDICAL IMAGE SEARCH
# ==========================================

def get_medical_images(query):

    try:

        url = "https://commons.wikimedia.org/w/api.php"

        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query + " medical",
            "gsrnamespace": 6,
            "gsrlimit": 6,
            "prop": "imageinfo",
            "iiprop": "url"
        }


        response = requests.get(
            url,
            params=params,
            timeout=10
        )


        response.raise_for_status()


        data = response.json()


        pages = (
            data
            .get("query", {})
            .get("pages", {})
        )


        images = []


        for page in pages.values():

            image_info =
                page.get("imageinfo", [])


            if image_info:

                image_url =
                    image_info[0].get("url")


                if image_url:

                    images.append(
                        image_url
                    )


        return images


    except Exception:

        return []


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return HTML


# ==========================================
# CHAT
# ==========================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    try:

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


        if not message:

            return jsonify({
                "error":
                    "Question is required."
            }), 400


        if not GEMINI_API_KEY:

            return jsonify({
                "error":
                    "GEMINI_API_KEY is not configured."
            }), 500


        prompt = f"""
You are MedAI, an educational medical information assistant.

Answer the user's question in the SAME LANGUAGE
that the user used.

Provide medically responsible educational information.

When appropriate, organize the answer using:

Definition
Causes
Types
Risk Factors
Signs and Symptoms
Diagnosis
Treatment
Prevention
Complications
Important Points

Safety rules:

- Do not claim to diagnose the user.
- Do not pretend to examine the patient.
- Do not invent medical facts.
- Do not provide personalized prescription or dosage instructions.
- If symptoms may indicate an emergency, advise urgent medical care.
- Make clear that the information is educational.
- Use understandable language.

User question:

{message}
"""


        api_url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-3.5-flash-lite:generateContent"
        )


        response = requests.post(

            api_url,

            params={
                "key":
                    GEMINI_API_KEY
            },

            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text":
                                    prompt
                            }
                        ]
                    }
                ]
            },

            timeout=60
        )


        if response.status_code != 200:

            return jsonify({
                "error":
                    "Gemini API error: "
                    + response.text[:500]
            }), 500


        gemini_data =
            response.json()


        answer = ""


        candidates =
            gemini_data.get(
                "candidates",
                []
            )


        if candidates:

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


            if parts:

                answer =
                    parts[0].get(
                        "text",
                        ""
                    )


        if not answer:

            answer =
                "ځواب ترلاسه نه شو."


        images =
            get_medical_images(
                message
            )


        return jsonify({

            "answer":
                answer,

            "images":
                images

        })


    except Exception as error:

        return jsonify({

            "error":
                str(error)

        }), 500


# ==========================================
# RUN
# ==========================================

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
