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

    <title>MedAI - Medical AI</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, Tahoma, sans-serif;
            background: #f4f7fb;
            color: #172033;
            transition: 0.3s;
        }

        body.dark {
            background: #101827;
            color: #f1f5f9;
        }

        .header {
            background: linear-gradient(135deg, #0d6efd, #00a6a6);
            color: white;
            padding: 22px 15px;
            text-align: center;
        }

        .header h1 {
            margin: 0 0 8px;
            font-size: 32px;
        }

        .header p {
            margin: 0;
            font-size: 16px;
        }

        .container {
            max-width: 1000px;
            margin: auto;
            padding: 18px;
        }

        .top-buttons {
            display: flex;
            justify-content: center;
            gap: 10px;
            flex-wrap: wrap;
            margin: 15px 0;
        }

        button {
            border: none;
            border-radius: 10px;
            padding: 11px 16px;
            cursor: pointer;
            font-size: 15px;
        }

        .dark-btn {
            background: #172033;
            color: white;
        }

        body.dark .dark-btn {
            background: #e5e7eb;
            color: #111827;
        }

        .card {
            background: white;
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 18px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.07);
        }

        body.dark .card {
            background: #172033;
            box-shadow: 0 5px 20px rgba(0,0,0,0.25);
        }

        .question-area {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        textarea {
            flex: 1;
            min-width: 220px;
            min-height: 100px;
            resize: vertical;
            border: 2px solid #dbe3ee;
            border-radius: 12px;
            padding: 14px;
            font-size: 16px;
            font-family: inherit;
            background: white;
            color: #172033;
        }

        body.dark textarea {
            background: #0f172a;
            color: white;
            border-color: #334155;
        }

        .main-btn {
            background: #0d6efd;
            color: white;
        }

        .voice-btn {
            background: #16a34a;
            color: white;
        }

        .stop-btn {
            background: #dc2626;
            color: white;
        }

        .result {
            white-space: pre-wrap;
            line-height: 1.9;
            font-size: 16px;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 15px;
            font-size: 17px;
        }

        .warning {
            background: #fff3cd;
            color: #664d03;
            border-right: 5px solid #ffc107;
            padding: 14px;
            border-radius: 10px;
            line-height: 1.8;
        }

        body.dark .warning {
            background: #3b3215;
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
            border-radius: 12px;
            background: #eee;
        }

        .topics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 10px;
        }

        .topic {
            background: #e8f1ff;
            color: #0756b8;
            padding: 15px 10px;
            border-radius: 12px;
            text-align: center;
            cursor: pointer;
            font-weight: bold;
        }

        body.dark .topic {
            background: #203452;
            color: #93c5fd;
        }

        .faq-item {
            margin-bottom: 10px;
        }

        .faq-question {
            width: 100%;
            text-align: right;
            background: #eef3f8;
            color: #172033;
        }

        body.dark .faq-question {
            background: #253247;
            color: white;
        }

        .faq-answer {
            display: none;
            padding: 12px;
            line-height: 1.8;
            border: 1px solid #dbe3ee;
            border-top: none;
            border-radius: 0 0 10px 10px;
        }

        body.dark .faq-answer {
            border-color: #334155;
        }

        .history-item {
            background: #f7f9fc;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 8px;
            cursor: pointer;
        }

        body.dark .history-item {
            background: #202c3d;
        }

        .small {
            color: #64748b;
            font-size: 13px;
        }

        body.dark .small {
            color: #94a3b8;
        }

        @media (max-width: 600px) {
            .header h1 {
                font-size: 26px;
            }

            .container {
                padding: 10px;
            }

            button {
                width: 100%;
            }

            .question-area button {
                width: 100%;
            }
        }
    </style>
</head>

<body>

<div class="header">
    <h1>🩺 MedAI</h1>
    <p>Medical AI Assistant</p>
</div>

<div class="container">

    <div class="top-buttons">
        <button class="dark-btn" onclick="toggleDarkMode()">
            🌙 Dark Mode
        </button>

        <button class="stop-btn" onclick="stopSpeaking()">
            ⏹️ Stop Voice
        </button>
    </div>

    <div class="card">
        <h2>🤖 Medical AI</h2>

        <div class="question-area">
            <textarea
                id="msg"
                placeholder="خپله طبي پوښتنه دلته ولیکئ..."
            ></textarea>

            <button class="voice-btn" onclick="startVoice()">
                🎤 Voice Question
            </button>

            <button class="main-btn" onclick="askAI()">
                🤖 Ask MedAI
            </button>
        </div>

        <div id="loading" class="loading">
            ⏳ مهرباني وکړئ، ځواب جوړېږي...
        </div>
    </div>

    <div class="card">
        <div class="warning">
            ⚠️ <b>Medical Safety:</b><br>
            MedAI یوازې د تعلیمي او معلوماتي موخو لپاره دی.
            دا د ډاکټر معاینه یا تشخیص نه بدلوي.
            که د سینې شدید درد، د ساه سخت مشکل، بې هوښۍ،
            شدید خونریزي یا بل عاجل حالت وي، ژر تر ژره
            بیړنۍ طبي مرسته وغواړئ.
        </div>
    </div>

    <div class="card">
        <h2>🩺 Medical Topics</h2>

        <div class="topics">

            <div class="topic" onclick="setTopic('Diabetes')">
                🩸 Diabetes
            </div>

            <div class="topic" onclick="setTopic('Blood Pressure')">
                ❤️ Blood Pressure
            </div>

            <div class="topic" onclick="setTopic('Asthma')">
                🫁 Asthma
            </div>

            <div class="topic" onclick="setTopic('Heart Disease')">
                ❤️ Heart Disease
            </div>

            <div class="topic" onclick="setTopic('Anemia')">
                🩸 Anemia
            </div>

            <div class="topic" onclick="setTopic('Migraine')">
                🧠 Migraine
            </div>

            <div class="topic" onclick="setTopic('Pneumonia')">
                🫁 Pneumonia
            </div>

            <div class="topic" onclick="setTopic('Gastritis')">
                🥗 Gastritis
            </div>

        </div>
    </div>

    <div class="card">
        <h2>💡 Answer</h2>

        <div id="answer" class="result">
ستاسو ځواب به دلته ښکاره شي.
        </div>

        <br>

        <button class="main-btn" onclick="speakAnswer()">
            🔊 Voice Output
        </button>

        <button class="stop-btn" onclick="stopSpeaking()">
            ⏹️ Stop
        </button>
    </div>

    <div class="card">
        <h2>🖼️ Medical Images</h2>

        <div id="images" class="images">
        </div>
    </div>

    <div class="card">
        <h2>🕘 History</h2>

        <button class="stop-btn" onclick="clearHistory()">
            🗑️ Clear History
        </button>

        <br><br>

        <div id="history"></div>
    </div>

    <div class="card">
        <h2>⭐ Favorites</h2>

        <div id="favorites"></div>
    </div>

    <div class="card">
        <h2>❓ FAQ</h2>

        <div class="faq-item">
            <button class="faq-question" onclick="toggleFAQ(1)">
                MedAI څه شی دی؟
            </button>

            <div id="faq1" class="faq-answer">
                MedAI یو AI طبي معلوماتي مرستیال دی چې د طبي موضوعاتو
                په اړه عمومي او تعلیمي معلومات وړاندې کوي.
            </div>
        </div>

        <div class="faq-item">
            <button class="faq-question" onclick="toggleFAQ(2)">
                آیا MedAI تشخیص کولی شي؟
            </button>

            <div id="faq2" class="faq-answer">
                نه. MedAI باید د مسلکي ډاکټر د تشخیص او معاینې بدیل ونه ګڼل شي.
            </div>
        </div>

        <div class="faq-item">
            <button class="faq-question" onclick="toggleFAQ(3)">
                آیا زه په خپله ژبه پوښتنه کولی شم؟
            </button>

            <div id="faq3" class="faq-answer">
                هو. پوښتنه په خپله ژبه ولیکئ؛ AI هڅه کوي ځواب
                په هماغه ژبه وړاندې کړي.
            </div>
        </div>

        <div class="faq-item">
            <button class="faq-question" onclick="toggleFAQ(4)">
                آیا طبي عکسونه هم ښکاره کېږي؟
            </button>

            <div id="faq4" class="faq-answer">
                هو. که اړوند عکسونه موجود وي، MedAI یې د Wikimedia
                Commons له لارې ښکاره کوي.
            </div>
        </div>

    </div>

</div>

<script>

function setTopic(topic) {
    document.getElementById("msg").value =
        "Please explain " + topic + " in detail.";
    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


async function askAI() {

    const message =
        document.getElementById("msg").value.trim();

    if (!message) {
        alert("مهرباني وکړئ لومړی خپله پوښتنه ولیکئ.");
        return;
    }

    const loading =
        document.getElementById("loading");

    const answer =
        document.getElementById("answer");

    loading.style.display = "block";

    answer.innerText =
        "⏳ AI ځواب جوړوي...";

    document.getElementById("images").innerHTML = "";

    try {

        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Server error"
            );
        }

        answer.innerText =
            data.answer || "ځواب ترلاسه نه شو.";

        saveHistory(message, data.answer);

        showImages(data.images || []);

        loadHistory();

    } catch (error) {

        answer.innerText =
            "❌ ستونزه رامنځته شوه: " +
            error.message;

    } finally {

        loading.style.display = "none";
    }
}


function showImages(images) {

    const container =
        document.getElementById("images");

    container.innerHTML = "";

    if (!images || images.length === 0) {
        container.innerHTML =
            "<p>د دې موضوع لپاره عکس ونه موندل شو.</p>";
        return;
    }

    images.forEach(function(url) {

        const img =
            document.createElement("img");

        img.src = url;

        img.alt = "Medical image";

        img.onerror = function() {
            img.style.display = "none";
        };

        container.appendChild(img);
    });
}


function startVoice() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {

        alert(
            "ستاسو Browser د Voice Question ملاتړ نه کوي."
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


function speakAnswer() {

    const answer =
        document.getElementById("answer")
        .innerText
        .trim();

    if (
        !answer ||
        answer === "ستاسو ځواب به دلته ښکاره شي."
    ) {

        alert("لومړی یوه پوښتنه وکړئ.");

        return;
    }

    if (!("speechSynthesis" in window)) {

        alert(
            "ستاسو Browser د Voice Output ملاتړ نه کوي."
        );

        return;
    }

    window.speechSynthesis.cancel();

    const speech =
        new SpeechSynthesisUtterance(answer);

    speech.lang = "en-US";

    speech.rate = 0.9;

    speech.pitch = 1;

    speech.volume = 1;

    window.speechSynthesis.speak(speech);
}


function stopSpeaking() {

    if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
    }
}


function toggleDarkMode() {

    document.body.classList.toggle("dark");

    const enabled =
        document.body.classList.contains("dark");

    localStorage.setItem(
        "medai_dark",
        enabled ? "1" : "0"
    );
}


function loadDarkMode() {

    const enabled =
        localStorage.getItem("medai_dark");

    if (enabled === "1") {
        document.body.classList.add("dark");
    }
}


function saveHistory(question, answer) {

    let history =
        JSON.parse(
            localStorage.getItem("medai_history") || "[]"
        );

    history.unshift({
        question: question,
        answer: answer,
        time: new Date().toLocaleString()
    });

    history =
        history.slice(0, 20);

    localStorage.setItem(
        "medai_history",
        JSON.stringify(history)
    );
}


function loadHistory() {

    const container =
        document.getElementById("history");

    const history =
        JSON.parse(
            localStorage.getItem("medai_history") || "[]"
        );

    container.innerHTML = "";

    if (history.length === 0) {

        container.innerHTML =
            "<p>تر اوسه History نشته.</p>";

        return;
    }

    history.forEach(function(item, index) {

        const div =
            document.createElement("div");

        div.className =
            "history-item";

        div.innerHTML =
            "<b>" +
            escapeHTML(item.question) +
            "</b><br>" +
            "<span class='small'>" +
            escapeHTML(item.time) +
            "</span>";

        div.onclick = function() {

            document.getElementById("msg").value =
                item.question;

            document.getElementById("answer").innerText =
                item.answer;
        };

        container.appendChild(div);
    });
}


function clearHistory() {

    localStorage.removeItem("medai_history");

    loadHistory();
}


function saveFavorite() {

    const question =
        document.getElementById("msg")
        .value
        .trim();

    const answer =
        document.getElementById("answer")
        .innerText
        .trim();

    if (!question || !answer) {
        return;
    }

    let favorites =
        JSON.parse(
            localStorage.getItem("medai_favorites") || "[]"
        );

    favorites.unshift({
        question: question,
        answer: answer
    });

    favorites =
        favorites.slice(0, 20);

    localStorage.setItem(
        "medai_favorites",
        JSON.stringify(favorites)
    );

    loadFavorites();
}


function loadFavorites() {

    const container =
        document.getElementById("favorites");

    const favorites =
        JSON.parse(
            localStorage.getItem("medai_favorites") || "[]"
        );

    container.innerHTML = "";

    if (favorites.length === 0) {

        container.innerHTML =
            "<p>تر اوسه Favorite نشته.</p>";

        return;
    }

    favorites.forEach(function(item) {

        const div =
            document.createElement("div");

        div.className =
            "history-item";

        div.innerHTML =
            "⭐ <b>" +
            escapeHTML(item.question) +
            "</b>";

        div.onclick = function() {

            document.getElementById("msg").value =
                item.question;

            document.getElementById("answer").innerText =
                item.answer;
        };

        container.appendChild(div);
    });
}


function toggleFAQ(number) {

    const element =
        document.getElementById(
            "faq" + number
        );

    if (element.style.display === "block") {
        element.style.display = "none";
    } else {
        element.style.display = "block";
    }
}


function escapeHTML(text) {

    const div =
        document.createElement("div");

    div.textContent =
        text || "";

    return div.innerHTML;
}


document.addEventListener(
    "DOMContentLoaded",
    function() {

        loadDarkMode();

        loadHistory();

        loadFavorites();
    }
);

</script>

</body>
</html>
"""


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

        pages = data.get(
            "query",
            {}
        ).get(
            "pages",
            {}
        )

        images = []

        for page in pages.values():

            image_info = page.get(
                "imageinfo",
                []
            )

            if image_info:

                image_url = image_info[0].get(
                    "url"
                )

                if image_url:
                    images.append(image_url)

        return images

    except Exception:
        return []


def ask_gemini(message):

    if not GEMINI_API_KEY:
        return (
            "GEMINI_API_KEY نه ده تنظیم شوې. "
            "مهرباني وکړئ په Vercel Environment Variables "
            "کې GEMINI_API_KEY اضافه کړئ."
        )

    prompt = f"""
You are MedAI, a medical educational AI assistant.

The user can ask in any language.

Answer in the SAME LANGUAGE as the user's question.

Provide clear, educational medical information.

Use this structure when appropriate:

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

Important safety rules:

- Do not claim to diagnose the user.
- Do not pretend to physically examine the patient.
- Do not invent medical facts.
- Do not provide personalized prescription or dosage instructions.
- Explain that a qualified healthcare professional should evaluate personal medical concerns.
- If the question describes a possible emergency, clearly advise urgent medical care.
- Keep the answer understandable and organized.

User question:

{message}
"""

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.5-flash-lite:generateContent"
    )

    params = {
        "key": GEMINI_API_KEY
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    response = requests.post(
        url,
        params=params,
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    candidates = data.get(
        "candidates",
        []
    )

    if not candidates:
        return "AI ځواب ترلاسه نه کړ."

    content = candidates[0].get(
        "content",
        {}
    )

    parts = content.get(
        "parts",
        []
    )

    if not parts:
        return "AI ځواب ترلاسه نه کړ."

    return parts[0].get(
        "text",
        "AI ځواب ترلاسه نه کړ."
    )


@app.route("/", methods=["GET"])
def home():
    return HTML


@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        message = str(
            data.get("message", "")
        ).strip()

        if not message:

            return jsonify({
                "error": "پوښتنه تشه ده."
            }), 400

        answer = ask_gemini(
            message
        )

        images = get_medical_images(
            message
        )

        return jsonify({
            "answer": answer,
            "images": images
        })

    except requests.exceptions.Timeout:

        return jsonify({
            "error": "AI server ته د ځواب وخت ختم شو."
        }), 504

    except requests.exceptions.RequestException:

        return jsonify({
            "error": "د AI server سره اړیکه ونه شوه."
        }), 502

    except Exception as e:

        return jsonify({
            "error": "Server error: " + str(e)
        }), 500


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
