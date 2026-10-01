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
<title>MedAI - Medical AI Assistant</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, Tahoma, sans-serif;
    background: #f4f7fb;
    color: #172033;
    transition: 0.25s;
}

body.dark {
    background: #111827;
    color: #f3f4f6;
}

header {
    background: linear-gradient(135deg, #0f766e, #2563eb);
    color: white;
    padding: 28px 18px;
    text-align: center;
}

header h1 {
    margin: 0 0 8px;
    font-size: 32px;
}

header p {
    margin: 0;
}

.container {
    width: min(1100px, 94%);
    margin: 20px auto 50px;
}

.card {
    background: white;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 18px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.07);
}

body.dark .card {
    background: #1f2937;
}

h2 {
    color: #0f766e;
}

body.dark h2 {
    color: #5eead4;
}

textarea,
input,
select {
    width: 100%;
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    padding: 14px;
    font-size: 16px;
    outline: none;
    background: white;
    color: #172033;
    font-family: inherit;
    margin-bottom: 10px;
}

body.dark textarea,
body.dark input,
body.dark select {
    background: #111827;
    color: white;
    border-color: #4b5563;
}

textarea {
    min-height: 130px;
    resize: vertical;
}

button {
    border: none;
    border-radius: 12px;
    padding: 12px 18px;
    font-size: 15px;
    cursor: pointer;
    background: #0f766e;
    color: white;
    margin: 5px;
}

button:hover {
    opacity: 0.9;
}

.secondary {
    background: #2563eb;
}

.danger {
    background: #dc2626;
}

.purple {
    background: #7c3aed;
}

.orange {
    background: #ea580c;
}

.green {
    background: #16a34a;
}

.warning {
    background: #fff7ed;
    border-right: 5px solid #f97316;
    padding: 15px;
    border-radius: 12px;
    line-height: 1.8;
}

body.dark .warning {
    background: #431407;
}

.result {
    white-space: pre-wrap;
    line-height: 1.9;
    margin-top: 15px;
}

.loading {
    text-align: center;
    padding: 12px;
    font-weight: bold;
}

.topics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
}

.topic {
    background: #ecfeff;
    border: 1px solid #a5f3fc;
    color: #155e75;
    padding: 16px;
    border-radius: 14px;
    text-align: center;
    cursor: pointer;
    font-weight: bold;
}

body.dark .topic {
    background: #164e63;
    color: #cffafe;
}

.images {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 14px;
}

.image-card {
    background: #f8fafc;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
}

body.dark .image-card {
    background: #111827;
    border-color: #374151;
}

.image-card img {
    width: 100%;
    height: 170px;
    object-fit: cover;
    display: block;
}

.image-card div {
    padding: 8px;
    font-size: 13px;
}

.history-item,
.favorite-item {
    padding: 12px;
    border-bottom: 1px solid #e5e7eb;
    cursor: pointer;
}

body.dark .history-item,
body.dark .favorite-item {
    border-color: #374151;
}

.faq-question {
    width: 100%;
    text-align: right;
    background: #e0f2fe;
    color: #075985;
}

body.dark .faq-question {
    background: #0c4a6e;
    color: #e0f2fe;
}

.faq-answer {
    display: none;
    padding: 12px;
    line-height: 1.8;
}

.grid-two {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
}

@media (max-width: 700px) {
    .grid-two {
        grid-template-columns: 1fr;
    }

    header h1 {
        font-size: 26px;
    }

    button {
        width: 100%;
    }
}
</style>
</head>

<body>

<header>
    <h1>🩺 MedAI</h1>
    <p>ستاسو هوښیار طبي معلوماتي مرستیال</p>
</header>

<div class="container">

<div class="card">
    <button onclick="toggleDarkMode()">🌙 Dark Mode</button>
    <button class="danger" onclick="stopSpeaking()">⏹️ Stop Voice</button>
</div>

<div class="warning">
    <strong>⚠️ طبي خوندیتوب:</strong><br>
    MedAI یوازې د تعلیمي او معلوماتي موخو لپاره دی.
    د AI ځواب د ډاکټر د معاینې، تشخیص یا نسخې بدیل نه دی.
    د جدي یا بیړنیو نښو په صورت کې ژر تر ژره مسلکي طبي مرسته وغواړئ.
</div>

<!-- MAIN AI -->

<div class="card">
    <h2>🤖 له MedAI څخه پوښتنه وکړئ</h2>

    <textarea id="question"
        placeholder="خپله طبي پوښتنه په هره ژبه ولیکئ..."></textarea>

    <button class="green" onclick="startVoice()">
        🎤 Voice Question
    </button>

    <button class="secondary" onclick="askAI()">
        🤖 Ask MedAI
    </button>

    <div id="aiLoading"></div>

    <div id="answer" class="result">
        ستاسو ځواب به دلته ښکاره شي.
    </div>

    <button onclick="speakAnswer()">🔊 Voice Output</button>
    <button class="danger" onclick="stopSpeaking()">⏹️ Stop Voice</button>
    <button onclick="saveFavorite()">⭐ Save Favorite</button>
</div>

<!-- TOPICS -->

<div class="card">
    <h2>🩺 Medical Topics</h2>

    <div class="topics">
        <div class="topic" onclick="setTopic('Diabetes')">🩸 Diabetes</div>
        <div class="topic" onclick="setTopic('Heart Disease')">❤️ Heart Disease</div>
        <div class="topic" onclick="setTopic('Hypertension')">💓 Blood Pressure</div>
        <div class="topic" onclick="setTopic('Asthma')">🫁 Asthma</div>
        <div class="topic" onclick="setTopic('Cancer')">🧬 Cancer</div>
        <div class="topic" onclick="setTopic('Kidney Disease')">🫘 Kidney</div>
        <div class="topic" onclick="setTopic('Liver Disease')">🧫 Liver</div>
        <div class="topic" onclick="setTopic('Anemia')">🩸 Anemia</div>
    </div>
</div>

<!-- 1 SYMPTOM EDUCATION -->

<div class="card">
    <h2>🩺 Symptom Education</h2>

    <p>
        خپلې نښې ولیکئ. MedAI به یې عمومي او تعلیمي تشریح وکړي.
        دا د ناروغۍ تشخیص نه دی.
    </p>

    <textarea id="symptomInput"
        placeholder="مثال: تبه، ټوخی او ستړیا"></textarea>

    <button class="purple" onclick="explainSymptoms()">
        🩺 Explain Symptoms
    </button>

    <div id="symptomLoading"></div>
    <div id="symptomResult" class="result"></div>
</div>

<!-- 2 VITAL SIGNS -->

<div class="card">
    <h2>❤️ Vital Signs Guide</h2>

    <p>
        خپل اندازه شوي ارزښتونه ولیکئ، لکه د وینې فشار،
        نبض، تودوخه یا SpO₂.
    </p>

    <textarea id="vitalInput"
        placeholder="مثال: Blood pressure 140/90, pulse 85, temperature 38°C"></textarea>

    <button class="secondary" onclick="explainVitals()">
        ❤️ Explain Vital Signs
    </button>

    <div id="vitalLoading"></div>
    <div id="vitalResult" class="result"></div>
</div>

<!-- 3 DISEASE COMPARISON -->

<div class="card">
    <h2>⚖️ Disease Comparison</h2>

    <div class="grid-two">

        <input id="diseaseOne"
            placeholder="لومړۍ ناروغي، مثال: Flu">

        <input id="diseaseTwo"
            placeholder="دوهمه ناروغي، مثال: COVID-19">

    </div>

    <button class="orange" onclick="compareDiseases()">
        ⚖️ Compare Diseases
    </button>

    <div id="compareLoading"></div>
    <div id="compareResult" class="result"></div>
</div>

<!-- 4 DOCTOR VISIT ASSISTANT -->

<div class="card">
    <h2>👨‍⚕️ Doctor Visit Assistant</h2>

    <p>
        خپلې نښې، د پیل وخت، درمل او مهم معلومات ولیکئ.
        MedAI به یې د ډاکټر سره د شریکولو لپاره منظم کړي.
    </p>

    <textarea id="doctorInput"
        placeholder="مثال:
زما ستونزه د ۳ ورځو راهیسې ده.
تبه لرم او ټوخی کوم.
اوس Paracetamol کاروم.
نور معلومات..."></textarea>

    <button onclick="prepareDoctorVisit()">
        👨‍⚕️ Prepare Doctor Notes
    </button>

    <div id="doctorLoading"></div>
    <div id="doctorResult" class="result"></div>
</div>

<!-- LAB -->

<div class="card">
    <h2>🧪 Lab Report Explainer</h2>

    <textarea id="labInput"
        placeholder="مثال: Hemoglobin 10, WBC 8000, Platelets 250000"></textarea>

    <button onclick="explainLab()">🧪 Explain Lab Report</button>

    <div id="labLoading"></div>
    <div id="labResult" class="result"></div>
</div>

<!-- MEDICINE -->

<div class="card">
    <h2>💊 Medicine Information</h2>

    <input id="medicineInput"
        placeholder="د درمل نوم، مثال: Paracetamol">

    <button onclick="explainMedicine()">
        💊 Get Medicine Information
    </button>

    <div id="medicineLoading"></div>
    <div id="medicineResult" class="result"></div>
</div>

<!-- DICTIONARY -->

<div class="card">
    <h2>📖 Medical Dictionary</h2>

    <input id="dictionaryInput"
        placeholder="طبي اصطلاح، مثال: Hypertension">

    <button onclick="explainDictionary()">
        📖 Explain Term
    </button>

    <div id="dictionaryLoading"></div>
    <div id="dictionaryResult" class="result"></div>
</div>

<!-- EMERGENCY -->

<div class="card">
    <h2>🚨 Emergency Detection</h2>

    <textarea id="emergencyInput"
        placeholder="خپلې نښې ولیکئ..."></textarea>

    <button class="danger" onclick="checkEmergency()">
        🚨 Check Emergency Signs
    </button>

    <div id="emergencyLoading"></div>
    <div id="emergencyResult" class="result"></div>
</div>

<!-- IMAGES -->

<div class="card">
    <h2>🖼️ Medical Images</h2>

    <input id="imageSearch"
        placeholder="د ناروغۍ یا طبي اصطلاح نوم">

    <button onclick="searchMedical()">
        🔎 Search Medical Images
    </button>

    <div id="images" class="images"></div>
</div>

<!-- HISTORY -->

<div class="card">
    <h2>🕘 History</h2>

    <button onclick="loadHistory()">Load History</button>
    <button class="danger" onclick="clearHistory()">Clear History</button>

    <div id="historyList"></div>
</div>

<!-- FAVORITES -->

<div class="card">
    <h2>⭐ Favorites</h2>

    <button onclick="loadFavorites()">Load Favorites</button>

    <div id="favoritesList"></div>
</div>

<!-- FAQ -->

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
        نه. MedAI یوازې عمومي او تعلیمي معلومات وړاندې کوي.
    </div>

    <button class="faq-question" onclick="toggleFAQ(3)">
        آیا په هره ژبه پوښتنه کولی شم؟
    </button>

    <div id="faq3" class="faq-answer">
        هو. پوښتنه په خپله ژبه ولیکئ او AI هڅه کوي په هماغه ژبه ځواب ورکړي.
    </div>

    <button class="faq-question" onclick="toggleFAQ(4)">
        د بیړني حالت پر مهال څه وکړم؟
    </button>

    <div id="faq4" class="faq-answer">
        که جدي یا ناڅاپي نښې موجودې وي، د محلي بیړنیو خدماتو یا روغتیايي مرکز سره ژر اړیکه ونیسئ.
    </div>
</div>

</div>

<script>

/* =========================
   MAIN AI
========================= */

async function askAI() {

    const message =
        document.getElementById("question").value.trim();

    if (!message) {
        alert("مهرباني وکړئ خپله پوښتنه ولیکئ.");
        return;
    }

    document.getElementById("aiLoading").innerHTML =
        '<div class="loading">⏳ MedAI ځواب جوړوي...</div>';

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
            throw new Error(data.error || "Request failed");
        }

        document.getElementById("answer").innerText =
            data.answer || "ځواب ترلاسه نه شو.";

        if (data.images) {
            displayImages(data.images);
        }

        saveHistory(message, data.answer);

    } catch (error) {

        document.getElementById("answer").innerText =
            "❌ ستونزه: " + error.message;

    } finally {

        document.getElementById("aiLoading").innerHTML = "";
    }
}


/* =========================
   GENERIC AI FUNCTION
========================= */

async function sendSpecialRequest(
    endpoint,
    inputId,
    resultId,
    loadingId
) {

    const query =
        document.getElementById(inputId).value.trim();

    if (!query) {
        alert("مهرباني وکړئ معلومات ولیکئ.");
        return;
    }

    document.getElementById(loadingId).innerHTML =
        '<div class="loading">⏳ معلومات پروسس کېږي...</div>';

    try {

        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                query: query
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Request failed");
        }

        document.getElementById(resultId).innerText =
            data.answer || "ځواب ترلاسه نه شو.";

    } catch (error) {

        document.getElementById(resultId).innerText =
            "❌ ستونزه: " + error.message;

    } finally {

        document.getElementById(loadingId).innerHTML = "";
    }
}


/* =========================
   SYMPTOMS
========================= */

function explainSymptoms() {

    sendSpecialRequest(
        "/symptoms",
        "symptomInput",
        "symptomResult",
        "symptomLoading"
    );
}


/* =========================
   VITAL SIGNS
========================= */

function explainVitals() {

    sendSpecialRequest(
        "/vitals",
        "vitalInput",
        "vitalResult",
        "vitalLoading"
    );
}


/* =========================
   LAB
========================= */

function explainLab() {

    sendSpecialRequest(
        "/lab",
        "labInput",
        "labResult",
        "labLoading"
    );
}


/* =========================
   MEDICINE
========================= */

function explainMedicine() {

    sendSpecialRequest(
        "/medicine",
        "medicineInput",
        "medicineResult",
        "medicineLoading"
    );
}


/* =========================
   DICTIONARY
========================= */

function explainDictionary() {

    sendSpecialRequest(
        "/dictionary",
        "dictionaryInput",
        "dictionaryResult",
        "dictionaryLoading"
    );
}


/* =========================
   EMERGENCY
========================= */

function checkEmergency() {

    sendSpecialRequest(
        "/emergency",
        "emergencyInput",
        "emergencyResult",
        "emergencyLoading"
    );
}


/* =========================
   DISEASE COMPARISON
========================= */

async function compareDiseases() {

    const one =
        document.getElementById("diseaseOne").value.trim();

    const two =
        document.getElementById("diseaseTwo").value.trim();

    if (!one || !two) {
        alert("دواړه ناروغۍ ولیکئ.");
        return;
    }

    document.getElementById("compareLoading").innerHTML =
        '<div class="loading">⏳ ناروغۍ مقایسه کېږي...</div>';

    try {

        const response = await fetch("/compare", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                one: one,
                two: two
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Comparison failed");
        }

        document.getElementById("compareResult").innerText =
            data.answer;

    } catch (error) {

        document.getElementById("compareResult").innerText =
            "❌ ستونزه: " + error.message;

    } finally {

        document.getElementById("compareLoading").innerHTML = "";
    }
}


/* =========================
   DOCTOR VISIT
========================= */

function prepareDoctorVisit() {

    sendSpecialRequest(
        "/doctor",
        "doctorInput",
        "doctorResult",
        "doctorLoading"
    );
}


/* =========================
   MEDICAL IMAGES
========================= */

async function searchMedical() {

    const query =
        document.getElementById("imageSearch").value.trim();

    if (!query) {
        alert("د طبي موضوع نوم ولیکئ.");
        return;
    }

    const container =
        document.getElementById("images");

    container.innerHTML =
        "<p>⏳ طبي عکسونه لټول کېږي...</p>";

    try {

        const response = await fetch(
            "/images?q=" + encodeURIComponent(query)
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Image search failed");
        }

        displayImages(data.images || []);

    } catch (error) {

        container.innerHTML =
            "<p>❌ د عکسونو په لټون کې ستونزه رامنځته شوه.</p>";
    }
}


function displayImages(images) {

    const container =
        document.getElementById("images");

    container.innerHTML = "";

    if (!images || images.length === 0) {

        container.innerHTML =
            "<p>د دې موضوع لپاره عکس ونه موندل شو.</p>";

        return;
    }

    images.forEach(function(image) {

        const card =
            document.createElement("div");

        card.className = "image-card";

        const img =
            document.createElement("img");

        img.src = image.url;

        img.alt =
            image.title || "Medical Image";

        img.loading = "lazy";

        img.onerror = function() {
            card.remove();
        };

        const title =
            document.createElement("div");

        title.innerText =
            image.title || "Medical Image";

        card.appendChild(img);

        card.appendChild(title);

        container.appendChild(card);
    });
}


/* =========================
   VOICE
========================= */

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

        document.getElementById("question").value =
            "🎤 واورېدل کېږي...";
    };

    recognition.onresult = function(event) {

        document.getElementById("question").value =
            event.results[0][0].transcript;
    };

    recognition.onerror = function() {

        document.getElementById("question").value = "";

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
        alert("لومړی پوښتنه وکړئ.");
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

    speech.volume = 1;

    window.speechSynthesis.speak(speech);
}


function stopSpeaking() {

    if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
    }
}


/* =========================
   DARK MODE
========================= */

function toggleDarkMode() {

    document.body.classList.toggle("dark");

    localStorage.setItem(
        "medai_dark",
        document.body.classList.contains("dark")
            ? "1"
            : "0"
    );
}


/* =========================
   HISTORY
========================= */

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
        history.slice(0, 30);

    localStorage.setItem(
        "medai_history",
        JSON.stringify(history)
    );
}


function loadHistory() {

    const container =
        document.getElementById("historyList");

    const history =
        JSON.parse(
            localStorage.getItem("medai_history") || "[]"
        );

    container.innerHTML = "";

    if (history.length === 0) {

        container.innerHTML =
            "<p>History خالي دی.</p>";

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
            "</b><br><small>" +
            escapeHTML(item.time) +
            "</small>";

        div.onclick = function() {

            document.getElementById("question").value =
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


/* =========================
   FAVORITES
========================= */

function saveFavorite() {

    const question =
        document.getElementById("question")
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

    favorites =
        favorites.slice(0, 30);

    localStorage.setItem(
        "medai_favorites",
        JSON.stringify(favorites)
    );

    loadFavorites();

    alert("⭐ Favorite ته Save شو.");
}


function loadFavorites() {

    const container =
        document.getElementById("favoritesList");

    const favorites =
        JSON.parse(
            localStorage.getItem("medai_favorites") || "[]"
        );

    container.innerHTML = "";

    if (favorites.length === 0) {

        container.innerHTML =
            "<p>Favorite خالي دی.</p>";

        return;
    }

    favorites.forEach(function(item) {

        const div =
            document.createElement("div");

        div.className =
            "favorite-item";

        div.innerHTML =
            "⭐ " +
            escapeHTML(item.question);

        div.onclick = function() {

            document.getElementById("question").value =
                item.question;

            document.getElementById("answer").innerText =
                item.answer;
        };

        container.appendChild(div);
    });
}


/* =========================
   FAQ
========================= */

function toggleFAQ(number) {

    const element =
        document.getElementById("faq" + number);

    if (element.style.display === "block") {

        element.style.display = "none";

    } else {

        element.style.display = "block";
    }
}


/* =========================
   TOPIC
========================= */

function setTopic(topic) {

    document.getElementById("question").value =
        topic +
        " په اړه بشپړ طبي معلومات راکړئ.";

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


/* =========================
   SECURITY
========================= */

function escapeHTML(text) {

    const div =
        document.createElement("div");

    div.textContent =
        text || "";

    return div.innerHTML;
}


/* =========================
   STARTUP
========================= */

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

            info_list = page.get(
                "imageinfo",
                []
            )

            if not info_list:
                continue

            info = info_list[0]

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


def ask_gemini(prompt):

    if not GEMINI_API_KEY:

        return (
            "GEMINI_API_KEY نه ده تنظیم شوې. "
            "په Vercel Environment Variables کې یې وګورئ."
        )

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.5-flash-lite:generateContent"
    )

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
        params={
            "key": GEMINI_API_KEY
        },
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


def build_prompt(instruction, user_text):

    return f"""
You are MedAI, a medical educational AI assistant.

Answer in the SAME LANGUAGE as the user's question or text.

You provide educational information only.

Do not diagnose the person.
Do not pretend to examine the person.
Do not invent facts.
Do not provide personalized prescriptions or dosage instructions.
For urgent symptoms, clearly advise appropriate urgent medical care.

{instruction}

User information:

{user_text}
"""


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

        prompt = build_prompt(
            """
Give a structured medical explanation.
When appropriate include:
Definition, Causes, Types, Risk Factors,
Signs and Symptoms, Diagnosis, Treatment,
Prevention, Complications and Important Points.
""",
            message
        )

        answer = ask_gemini(prompt)

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


@app.route("/symptoms", methods=["POST"])
def symptoms():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        query = str(
            data.get("query", "")
        ).strip()

        if not query:

            return jsonify({
                "error": "نښې نه دي لیکل شوې."
            }), 400

        prompt = build_prompt(
            """
Explain the symptoms educationally.
Discuss what body systems or common conditions
can sometimes be associated with them.
Explain warning signs that need medical attention.
Do not diagnose the user.
""",
            query
        )

        return jsonify({
            "answer": ask_gemini(prompt)
        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


@app.route("/vitals", methods=["POST"])
def vitals():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        query = str(
            data.get("query", "")
        ).strip()

        if not query:

            return jsonify({
                "error": "Vital signs نه دي لیکل شوي."
            }), 400

        prompt = build_prompt(
            """
Explain the provided vital-sign values.
Explain what each measurement means and why it matters.
Mention that interpretation depends on age, situation,
measurement method and clinical context.
Do not diagnose the user.
""",
            query
        )

        return jsonify({
            "answer": ask_gemini(prompt)
        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


@app.route("/compare", methods=["POST"])
def compare():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        one = str(
            data.get("one", "")
        ).strip()

        two = str(
            data.get("two", "")
        ).strip()

        if not one or not two:

            return jsonify({
                "error": "دواړه ناروغۍ اړینې دي."
            }), 400

        prompt = build_prompt(
            """
Compare the two medical conditions.
Use:
Definition,
Common causes,
Typical symptoms,
Risk factors,
Diagnosis,
Treatment approaches,
Important differences,
Similarities,
and warning signs.

Keep the comparison educational.
Do not say that the user has either condition.
""",
            "Condition 1: " + one +
            "\nCondition 2: " + two
        )

        return jsonify({
            "answer": ask_gemini(prompt)
        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


@app.route("/doctor", methods=["POST"])
def doctor():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        query = str(
            data.get("query", "")
        ).strip()

        if not query:

            return jsonify({
                "error": "معلومات نه دي لیکل شوې."
            }), 400

        prompt = build_prompt(
            """
Turn the user's notes into a clear doctor-visit summary.

Organize:
1. Main concern
2. Symptoms
3. When symptoms started
4. Changes over time
5. Medicines mentioned
6. Relevant measurements or tests
7. Questions to ask the doctor

Do not add facts that the user did not provide.
""",
            query
        )

        return jsonify({
            "answer": ask_gemini(prompt)
        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


@app.route("/lab", methods=["POST"])
def lab():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        query = str(
            data.get("query", "")
        ).strip()

        if not query:

            return jsonify({
                "error": "Lab information نشته."
            }), 400

        prompt = build_prompt(
            """
Explain the laboratory tests and values.
Explain what each test generally measures,
why it is used, and what can affect its result.
Do not diagnose the user.
Mention that reference ranges can differ by laboratory.
""",
            query
        )

        return jsonify({
            "answer": ask_gemini(prompt)
        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


@app.route("/medicine", methods=["POST"])
def medicine():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        query = str(
            data.get("query", "")
        ).strip()

        if not query:

            return jsonify({
                "error": "د درمل نوم نشته."
            }), 400

        prompt = build_prompt(
            """
Give general educational information about the medicine.
Include:
What it is,
common uses,
common side effects,
important precautions,
major interaction categories,
and when professional advice is important.

Do not prescribe it.
Do not give a personalized dose.
Do not tell the user to start or stop a medicine.
""",
            query
        )

        return jsonify({
            "answer": ask_gemini(prompt)
        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


@app.route("/dictionary", methods=["POST"])
def dictionary():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        query = str(
            data.get("query", "")
        ).strip()

        if not query:

            return jsonify({
                "error": "اصطلاح نشته."
            }), 400

        prompt = build_prompt(
            """
Explain this medical term in simple language.
Give a short definition, why it matters,
and a simple example when useful.
""",
            query
        )

        return jsonify({
            "answer": ask_gemini(prompt)
        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


@app.route("/emergency", methods=["POST"])
def emergency():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        query = str(
            data.get("query", "")
        ).strip()

        if not query:

            return jsonify({
                "error": "نښې نشته."
            }), 400

        prompt = build_prompt(
            """
Assess the text only for general emergency warning signs.

Clearly separate:
URGENT WARNING SIGNS
and
GENERAL INFORMATION.

If symptoms could represent a serious emergency,
tell the user to seek urgent medical care.

Do not diagnose.
Do not say that absence of a warning sign guarantees safety.
""",
            query
        )

        return jsonify({
            "answer": ask_gemini(prompt)
        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


@app.route("/images", methods=["GET"])
def images():

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:

        return jsonify({
            "images": []
        })

    return jsonify({
        "images": get_medical_images(query)
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
