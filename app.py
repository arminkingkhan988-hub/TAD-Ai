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
    padding: 25px 15px;
    text-align: center;
}

.header h1 {
    margin: 0 0 8px;
    font-size: 32px;
}

.container {
    max-width: 1000px;
    margin: auto;
    padding: 16px;
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
}

textarea,
input {
    width: 100%;
    padding: 14px;
    border: 2px solid #dbe3ee;
    border-radius: 12px;
    font-size: 16px;
    font-family: inherit;
    background: white;
    color: #172033;
}

body.dark textarea,
body.dark input {
    background: #0f172a;
    color: white;
    border-color: #334155;
}

textarea {
    min-height: 110px;
    resize: vertical;
}

button {
    border: none;
    border-radius: 10px;
    padding: 11px 16px;
    cursor: pointer;
    font-size: 15px;
    margin: 5px;
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

.dark-btn {
    background: #172033;
    color: white;
}

body.dark .dark-btn {
    background: #e5e7eb;
    color: #111827;
}

.search-btn {
    background: #7c3aed;
    color: white;
}

.quiz-btn {
    background: #ea580c;
    color: white;
}

.topic-grid,
.image-grid,
.search-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
}

.topic {
    background: #e8f1ff;
    color: #0756b8;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    cursor: pointer;
    font-weight: bold;
}

body.dark .topic {
    background: #203452;
    color: #93c5fd;
}

.result {
    white-space: pre-wrap;
    line-height: 1.9;
    font-size: 16px;
}

.warning {
    background: #fff3cd;
    color: #664d03;
    padding: 14px;
    border-radius: 10px;
    line-height: 1.8;
}

body.dark .warning {
    background: #3b3215;
    color: #ffe69c;
}

.loading {
    display: none;
    text-align: center;
    padding: 15px;
}

.image-card {
    background: #f8fafc;
    padding: 8px;
    border-radius: 12px;
}

body.dark .image-card {
    background: #202c3d;
}

.image-card img {
    width: 100%;
    height: 190px;
    object-fit: cover;
    border-radius: 10px;
}

.image-card p {
    font-size: 13px;
    margin: 7px;
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
}

.quiz-option {
    display: block;
    width: 100%;
    text-align: right;
    background: #eef3f8;
    color: #172033;
    margin: 8px 0;
}

body.dark .quiz-option {
    background: #253247;
    color: white;
}

.quiz-result {
    font-size: 18px;
    font-weight: bold;
    margin-top: 12px;
}

@media (max-width: 600px) {
    .header h1 {
        font-size: 26px;
    }

    button {
        width: calc(100% - 10px);
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

<div class="card">
    <button class="dark-btn" onclick="toggleDarkMode()">
        🌙 Dark Mode
    </button>

    <button class="stop-btn" onclick="stopSpeaking()">
        ⏹️ Stop Voice
    </button>
</div>

<div class="card">
    <h2>🤖 Medical AI</h2>

    <textarea id="msg"
        placeholder="خپله طبي پوښتنه دلته ولیکئ..."></textarea>

    <button class="voice-btn" onclick="startVoice()">
        🎤 Voice Question
    </button>

    <button class="main-btn" onclick="askAI()">
        🤖 Ask MedAI
    </button>

    <div id="loading" class="loading">
        ⏳ AI ځواب جوړوي...
    </div>
</div>

<div class="card">
    <div class="warning">
        ⚠️ <b>Medical Safety:</b><br>
        MedAI یوازې د تعلیمي او معلوماتي موخو لپاره دی.
        دا د ډاکټر معاینه یا تشخیص نه بدلوي.
        د بیړني حالت په صورت کې ژر تر ژره طبي مرسته وغواړئ.
    </div>
</div>

<div class="card">
    <h2>🩺 Medical Topics</h2>

    <div class="topic-grid">

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
    <h2>💡 AI Answer</h2>

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

    <button class="quiz-btn" onclick="saveFavorite()">
        ⭐ Save Favorite
    </button>
</div>

<div class="card">
    <h2>🖼️ Medical Images</h2>

    <div id="images" class="image-grid">
        <p>د پوښتنې وروسته اړوند طبي عکسونه دلته ښکاره کېږي.</p>
    </div>
</div>

<div class="card">
    <h2>🔎 Medical Search</h2>

    <input id="searchInput"
        placeholder="مثلاً: diabetes, heart, asthma">

    <button class="search-btn" onclick="searchMedical()">
        🔎 Search
    </button>

    <div id="searchResults" class="search-grid"></div>
</div>

<div class="card">
    <h2>🧠 Medical Quiz</h2>

    <p id="quizQuestion">
        د Quiz د پیل لپاره لاندې تڼۍ کېکاږئ.
    </p>

    <div id="quizOptions"></div>

    <div id="quizResult" class="quiz-result"></div>

    <button class="quiz-btn" onclick="newQuiz()">
        🧠 New Quiz
    </button>
</div>

<div class="card">
    <h2>🕘 History</h2>

    <button class="stop-btn" onclick="clearHistory()">
        🗑️ Clear History
    </button>

    <div id="history"></div>
</div>

<div class="card">
    <h2>⭐ Favorites</h2>

    <div id="favorites"></div>
</div>

<div class="card">
    <h2>❓ FAQ</h2>

    <button class="faq-question" onclick="toggleFAQ(1)">
        MedAI څه شی دی؟
    </button>

    <div id="faq1" class="faq-answer">
        MedAI د طبي معلوماتو لپاره AI مرستیال دی.
    </div>

    <button class="faq-question" onclick="toggleFAQ(2)">
        آیا MedAI تشخیص کوي؟
    </button>

    <div id="faq2" class="faq-answer">
        نه. دا تعلیمي معلومات وړاندې کوي او د ډاکټر بدیل نه دی.
    </div>

    <button class="faq-question" onclick="toggleFAQ(3)">
        آیا په خپله ژبه پوښتنه کولی شم؟
    </button>

    <div id="faq3" class="faq-answer">
        هو. پوښتنه په خپله ژبه ولیکئ او AI به هڅه وکړي په هماغه ژبه ځواب ورکړي.
    </div>

    <button class="faq-question" onclick="toggleFAQ(4)">
        آیا عکسونه هم شته؟
    </button>

    <div id="faq4" class="faq-answer">
        هو. MedAI د Wikimedia Commons له لارې اړوند طبي عکسونه لټوي.
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
        alert("مهرباني وکړئ لومړی پوښتنه ولیکئ.");
        return;
    }

    document.getElementById("loading").style.display = "block";

    document.getElementById("answer").innerText =
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

        document.getElementById("answer").innerText =
            data.answer || "ځواب ترلاسه نه شو.";

        showImages(data.images || []);

        saveHistory(
            message,
            data.answer || ""
        );

        loadHistory();

    } catch (error) {

        document.getElementById("answer").innerText =
            "❌ ستونزه: " + error.message;

    } finally {

        document.getElementById("loading").style.display =
            "none";
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

    images.forEach(function(item) {

        const box =
            document.createElement("div");

        box.className = "image-card";

        const img =
            document.createElement("img");

        img.src = item.url;

        img.alt = item.title || "Medical image";

        img.loading = "lazy";

        img.onerror = function() {
            box.style.display = "none";
        };

        const title =
            document.createElement("p");

        title.innerText =
            item.title || "Medical image";

        box.appendChild(img);

        box.appendChild(title);

        container.appendChild(box);
    });
}


async function searchMedical() {

    const query =
        document.getElementById("searchInput")
        .value
        .trim();

    if (!query) {
        alert("د لټون لپاره موضوع ولیکئ.");
        return;
    }

    const container =
        document.getElementById("searchResults");

    container.innerHTML =
        "<p>⏳ Searching...</p>";

    try {

        const response = await fetch(
            "/search?q=" +
            encodeURIComponent(query)
        );

        const data =
            await response.json();

        container.innerHTML = "";

        if (!data.images || data.images.length === 0) {

            container.innerHTML =
                "<p>هیڅ طبي عکس ونه موندل شو.</p>";

            return;
        }

        data.images.forEach(function(item) {

            const box =
                document.createElement("div");

            box.className =
                "image-card";

            const img =
                document.createElement("img");

            img.src = item.url;

            img.alt =
                item.title || query;

            img.loading = "lazy";

            img.onerror = function() {
                box.style.display = "none";
            };

            const title =
                document.createElement("p");

            title.innerText =
                item.title || query;

            box.appendChild(img);

            box.appendChild(title);

            container.appendChild(box);
        });

    } catch (error) {

        container.innerHTML =
            "<p>❌ Search error.</p>";
    }
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

        document.getElementById("msg").value =
            event.results[0][0].transcript;
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

    const text =
        document.getElementById("answer")
        .innerText
        .trim();

    if (!text) {
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
        new SpeechSynthesisUtterance(text);

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

    const dark =
        document.body.classList.contains("dark");

    localStorage.setItem(
        "medai_dark",
        dark ? "1" : "0"
    );
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

    history = history.slice(0, 20);

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

    history.forEach(function(item) {

        const div =
            document.createElement("div");

        div.className =
            "history-item";

        div.innerHTML =
            "<b>" +
            escapeHTML(item.question) +
            "</b><br>" +
            "<small>" +
            escapeHTML(item.time) +
            "</small>";

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

    localStorage.removeItem(
        "medai_history"
    );

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
        alert("لومړی یوه پوښتنه وکړئ.");
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

    favorites = favorites.slice(0, 20);

    localStorage.setItem(
        "medai_favorites",
        JSON.stringify(favorites)
    );

    loadFavorites();

    alert("⭐ Favorite ته Save شو.");
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
            "⭐ " +
            escapeHTML(item.question);

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


const quizQuestions = [

    {
        question: "Which organ pumps blood around the body?",
        options: [
            "Heart",
            "Lung",
            "Kidney",
            "Stomach"
        ],
        answer: 0
    },

    {
        question: "Which organ is mainly responsible for breathing?",
        options: [
            "Heart",
            "Lung",
            "Kidney",
            "Liver"
        ],
        answer: 1
    },

    {
        question: "Diabetes mainly affects which substance?",
        options: [
            "Blood sugar",
            "Bone",
            "Hair",
            "Skin"
        ],
        answer: 0
    },

    {
        question: "Which organ filters waste from blood?",
        options: [
            "Heart",
            "Kidney",
            "Lung",
            "Brain"
        ],
        answer: 1
    }

];

let currentQuiz = null;


function newQuiz() {

    const random =
        Math.floor(
            Math.random() *
            quizQuestions.length
        );

    currentQuiz =
        quizQuestions[random];

    document.getElementById(
        "quizQuestion"
    ).innerText =
        currentQuiz.question;

    document.getElementById(
        "quizResult"
    ).innerText = "";

    const container =
        document.getElementById(
            "quizOptions"
        );

    container.innerHTML = "";

    currentQuiz.options.forEach(
        function(option, index) {

            const button =
                document.createElement("button");

            button.className =
                "quiz-option";

            button.innerText =
                option;

            button.onclick = function() {
                checkQuiz(index);
            };

            container.appendChild(button);
        }
    );
}


function checkQuiz(index) {

    const result =
        document.getElementById(
            "quizResult"
        );

    if (!currentQuiz) {
        return;
    }

    if (index === currentQuiz.answer) {

        result.innerText =
            "✅ سم ځواب!";

    } else {

        result.innerText =
            "❌ ناسم ځواب. صحیح ځواب: " +
            currentQuiz.options[
                currentQuiz.answer
            ];
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

        if (
            localStorage.getItem("medai_dark")
            === "1"
        ) {
            document.body.classList.add("dark");
        }

        loadHistory();

        loadFavorites();

        newQuiz();
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
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": 8,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 600
        }

        response = requests.get(
            url,
            params=params,
            timeout=15,
            headers={
                "User-Agent": "MedAI/1.0"
            }
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

            image_info = page.get(
                "imageinfo",
                []
            )

            if not image_info:
                continue

            info = image_info[0]

            image_url = (
                info.get("thumburl")
                or info.get("url")
            )

            title = page.get(
                "title",
                "Medical Image"
            )

            if image_url:

                images.append({
                    "url": image_url,
                    "title": title
                })

        return images

    except Exception:
        return []


def ask_gemini(message):

    if not GEMINI_API_KEY:

        return (
            "GEMINI_API_KEY نه ده تنظیم شوې. "
            "مهرباني وکړئ Vercel Environment Variables "
            "کې GEMINI_API_KEY وګورئ."
        )

    prompt = f"""
You are MedAI, a medical educational AI assistant.

Answer in the SAME LANGUAGE as the user's question.

Give clear, organized and educational medical information.

When appropriate, use these sections:

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

- Do not diagnose the user.
- Do not pretend to physically examine anyone.
- Do not invent medical facts.
- Do not provide personalized prescription or dosage instructions.
- Explain that a qualified healthcare professional should evaluate personal medical concerns.
- If symptoms may indicate an emergency, advise urgent medical care.
- Keep the answer understandable.

User question:

{message}
"""

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.5-flash-lite:generateContent"
    )

    response = requests.post(
        url,
        params={
            "key": GEMINI_API_KEY
        },
        json={
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        },
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

    except Exception as error:

        return jsonify({
            "error": "Server error: " + str(error)
        }), 500


@app.route("/search", methods=["GET"])
def search():

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:

        return jsonify({
            "images": []
        })

    images = get_medical_images(
        query + " medical"
    )

    return jsonify({
        "images": images
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
