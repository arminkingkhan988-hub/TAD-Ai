from flask import Flask, request, jsonify
import os
import requests
import urllib.parse

app = Flask(__name__)


@app.route("/")
def home():
    return """
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
    padding: 20px;
    font-family: Arial, sans-serif;
    background: #f4f7fb;
    color: #222;
}

.container {
    max-width: 900px;
    margin: auto;
}

h1 {
    text-align: center;
    color: #1677ff;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #666;
    margin-bottom: 25px;
}

textarea {
    width: 100%;
    height: 130px;
    padding: 15px;
    border: 1px solid #ccc;
    border-radius: 12px;
    font-size: 18px;
    resize: vertical;
    font-family: Arial, sans-serif;
}

button {
    width: 100%;
    margin-top: 12px;
    padding: 15px;
    border: none;
    border-radius: 12px;
    background: #1677ff;
    color: white;
    font-size: 18px;
    cursor: pointer;
}

button:hover {
    opacity: 0.9;
}

button:disabled {
    background: #999;
    cursor: not-allowed;
}

.voice-button {
    background: #28a745;
}

.speak-button {
    background: #8e44ad;
}

.stop-button {
    background: #dc3545;
}

.action-buttons {
    display: flex;
    gap: 10px;
    margin-top: 12px;
}

.action-buttons button {
    margin-top: 0;
}

.save-button {
    background: #f5a623;
}

.history-button {
    background: #555;
}

.clear-button {
    background: #777;
}

.delete-button {
    background: #dc3545;
}

#answer {
    margin-top: 20px;
    padding: 22px;
    background: white;
    border-radius: 12px;
    line-height: 2;
    white-space: pre-wrap;
    min-height: 80px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

#images {
    margin-top: 25px;
}

.image-title {
    font-size: 21px;
    font-weight: bold;
    margin-bottom: 15px;
}

.image-grid {
    display: grid;
    grid-template-columns: repeat(
        auto-fit,
        minmax(220px, 1fr)
    );
    gap: 15px;
}

.image-card {
    background: white;
    padding: 10px;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}

.image-card img {
    width: 100%;
    height: 220px;
    object-fit: contain;
    border-radius: 10px;
    background: #eee;
    display: block;
}

.image-caption {
    margin-top: 8px;
    font-size: 14px;
    line-height: 1.5;
}

.image-caption a {
    color: #1677ff;
    text-decoration: none;
}

.no-image {
    padding: 15px;
    background: #fff4d6;
    border-radius: 10px;
    color: #6b5200;
}

.warning {
    margin-top: 25px;
    padding: 15px;
    background: #fff4d6;
    border-radius: 10px;
    color: #6b5200;
    line-height: 1.8;
}

#historyPanel,
#favoritesPanel {
    display: none;
    margin-top: 20px;
    background: white;
    padding: 18px;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}

.history-title {
    font-size: 22px;
    font-weight: bold;
    margin-bottom: 15px;
}

.history-item,
.favorite-item {
    padding: 14px;
    border: 1px solid #ddd;
    border-radius: 10px;
    margin-bottom: 10px;
    background: #fafafa;
}

.favorite-item {
    background: #fffdf5;
}

.history-question {
    font-weight: bold;
    color: #1677ff;
    margin-bottom: 6px;
    cursor: pointer;
}

.favorite-question {
    font-weight: bold;
    color: #f5a623;
    margin-bottom: 8px;
}

.favorite-answer {
    white-space: pre-wrap;
    line-height: 1.8;
    margin-bottom: 10px;
}

.history-date {
    font-size: 12px;
    color: #888;
}

.history-actions,
.favorite-actions {
    display: flex;
    gap: 8px;
    margin-top: 10px;
}

.history-actions button,
.favorite-actions button {
    margin-top: 0;
    padding: 8px;
    font-size: 14px;
}

@media (max-width: 600px) {
    body {
        padding: 12px;
    }

    textarea {
        font-size: 16px;
    }

    .action-buttons,
    .history-actions,
    .favorite-actions {
        flex-direction: column;
    }
}
</style>
</head>

<body>

<div class="container">

<h1>🩺 MedAI</h1>

<div class="subtitle">
    ستاسو د طبي زده کړو هوښیار مرستیال
</div>

<textarea
    id="msg"
    placeholder="Ask any medical question..."
></textarea>

<button
    class="voice-button"
    type="button"
    onclick="startVoice()"
>
    🎤 په غږ پوښتنه وکړئ
</button>

<button
    id="askButton"
    type="button"
    onclick="sendQuestion()"
>
    پوښتنه
</button>

<div class="action-buttons">

    <button
        class="history-button"
        type="button"
        onclick="toggleHistory()"
    >
        📜 History
    </button>

    <button
        class="save-button"
        type="button"
        onclick="saveCurrentAnswer()"
    >
        ⭐ Save
    </button>

</div>

<div id="answer">
    ستاسو ځواب به دلته ښکاره شي.
</div>

<button
    class="speak-button"
    type="button"
    onclick="speakAnswer()"
>
    🔊 ځواب واورئ
</button>

<button
    class="stop-button"
    type="button"
    onclick="stopSpeaking()"
>
    ⏹️ غږ ودروئ
</button>

<div id="images"></div>

<div id="historyPanel">

    <div class="history-title">
        📜 د پخوانیو پوښتنو تاریخ
    </div>

    <div id="historyList"></div>

    <button
        class="clear-button"
        type="button"
        onclick="clearHistory()"
    >
        🗑️ Clear History
    </button>

</div>

<div id="favoritesPanel">

    <div class="history-title">
        ⭐ خوندي شوي ځوابونه
    </div>

    <div id="favoritesList"></div>

</div>

<div class="warning">
⚠️ MedAI د طبي زده کړو او معلوماتو لپاره دی.
دا د ډاکټر بدیل نه دی.
د جدي یا بیړنیو نښو په صورت کې له روغتیايي مسلکي کس سره اړیکه ونیسئ.
</div>

</div>

<script>

let currentQuestion = "";
let currentAnswer = "";

let history = JSON.parse(
    localStorage.getItem("medai_history") || "[]"
);

let favorites = JSON.parse(
    localStorage.getItem("medai_favorites") || "[]"
);


/* Voice Question */

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

    const recognition = new SpeechRecognition();

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


/* Voice Output */

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

    speech.lang = detectSpeechLanguage(
        currentQuestion
    );

    speech.rate = 0.9;
    speech.pitch = 1;
    speech.volume = 1;

    window.speechSynthesis.speak(speech);
}


/* Stop Voice */

function stopSpeaking() {

    if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
    }
}


/* Detect language for voice */

function detectSpeechLanguage(text) {

    if (!text) {
        return "en-US";
    }

    if (/[\u0600-\u06FF]/.test(text)) {
        return "ps-AF";
    }

    return "en-US";
}


/* Send Question */

async function sendQuestion() {

    const message =
        document.getElementById("msg")
        .value
        .trim();

    const answer =
        document.getElementById("answer");

    const images =
        document.getElementById("images");

    const button =
        document.getElementById("askButton");

    if (!message) {

        answer.innerText =
            "Please enter your question.";

        images.innerHTML = "";

        return;
    }

    stopSpeaking();

    currentQuestion = message;

    currentAnswer = "";

    answer.innerText =
        "⏳ ځواب چمتو کېږي...";

    images.innerHTML = "";

    button.disabled = true;

    button.innerText =
        "⏳ مهرباني وکړئ انتظار وکړئ";

    try {

        const response = await fetch(
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

        if (data.answer) {

            answer.innerText =
                data.answer;

            currentAnswer =
                data.answer;

            addToHistory(
                message,
                data.answer
            );

        } else {

            answer.innerText =
                data.error ||
                "یوه ستونزه رامنځته شوه.";

            currentAnswer = "";
        }


        if (
            Array.isArray(data.images) &&
            data.images.length > 0
        ) {

            let html = `
                <div class="image-title">
                    🖼️ Related Medical Images
                </div>

                <div class="image-grid">
            `;

            data.images.forEach(function(image) {

                html += `
                    <div class="image-card">

                        <a
                            href="${image.page_url}"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            <img
                                src="${image.image_url}"
                                alt="${escapeHtml(image.title)}"
                                loading="lazy"
                            >
                        </a>

                        <div class="image-caption">

                            <a
                                href="${image.page_url}"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                ${escapeHtml(image.title)}
                            </a>

                        </div>

                    </div>
                `;

            });

            html += "</div>";

            images.innerHTML = html;

        } else {

            images.innerHTML = `
                <div class="no-image">
                    🖼️ No suitable image was found
                    for this topic.
                </div>
            `;
        }

    } catch (error) {

        console.error(error);

        answer.innerText =
            "❌ د سرور سره د اړیکې ستونزه رامنځته شوه.";

        images.innerHTML = "";
    }

    button.disabled = false;

    button.innerText = "پوښتنه";
}


/* History */

function addToHistory(question, answer) {

    history.unshift({
        question: question,
        answer: answer,
        date: new Date().toLocaleString()
    });

    history = history.slice(0, 50);

    localStorage.setItem(
        "medai_history",
        JSON.stringify(history)
    );

    renderHistory();
}


function toggleHistory() {

    const panel =
        document.getElementById("historyPanel");

    if (
        panel.style.display === "none" ||
        panel.style.display === ""
    ) {

        panel.style.display = "block";

        renderHistory();

    } else {

        panel.style.display = "none";
    }
}


function renderHistory() {

    const list =
        document.getElementById("historyList");

    if (history.length === 0) {

        list.innerHTML = `
            <div class="no-image">
                تراوسه هېڅ History نشته.
            </div>
        `;

        return;
    }

    let html = "";

    history.forEach(function(item, index) {

        html += `
            <div class="history-item">

                <div
                    class="history-question"
                    onclick="loadHistory(${index})"
                >
                    ${escapeHtml(item.question)}
                </div>

                <div class="history-date">
                    ${escapeHtml(item.date)}
                </div>

                <div class="history-actions">

                    <button
                        type="button"
                        onclick="loadHistory(${index})"
                    >
                        📖 Open
                    </button>

                    <button
                        class="delete-button"
                        type="button"
                        onclick="deleteHistory(${index})"
                    >
                        🗑️ Delete
                    </button>

                </div>

            </div>
        `;
    });

    list.innerHTML = html;
}


function loadHistory(index) {

    const item = history[index];

    if (!item) {
        return;
    }

    document.getElementById("msg").value =
        item.question;

    document.getElementById("answer").innerText =
        item.answer;

    currentQuestion =
        item.question;

    currentAnswer =
        item.answer;

    document.getElementById(
        "historyPanel"
    ).style.display = "none";

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


function deleteHistory(index) {

    history.splice(index, 1);

    localStorage.setItem(
        "medai_history",
        JSON.stringify(history)
    );

    renderHistory();
}


function clearHistory() {

    if (
        !confirm(
            "ایا غواړئ ټول History پاک کړئ؟"
        )
    ) {
        return;
    }

    history = [];

    localStorage.removeItem(
        "medai_history"
    );

    renderHistory();
}


/* Favorites */

function saveCurrentAnswer() {

    if (
        !currentQuestion ||
        !currentAnswer
    ) {

        alert(
            "لومړی یوه پوښتنه وکړئ."
        );

        return;
    }

    const exists =
        favorites.some(function(item) {

            return (
                item.question ===
                currentQuestion
            );

        });

    if (exists) {

        alert(
            "دا ځواب مخکې خوندي شوی."
        );

        return;
    }

    favorites.unshift({

        question:
            currentQuestion,

        answer:
            currentAnswer,

        date:
            new Date().toLocaleString()
    });

    favorites =
        favorites.slice(0, 50);

    localStorage.setItem(
        "medai_favorites",
        JSON.stringify(favorites)
    );

    alert(
        "⭐ ځواب خوندي شو."
    );

    renderFavorites();
}


function renderFavorites() {

    const list =
        document.getElementById(
            "favoritesList"
        );

    if (favorites.length === 0) {

        list.innerHTML = `
            <div class="no-image">
                تراوسه هېڅ خوندي شوی ځواب نشته.
            </div>
        `;

        return;
    }

    let html = "";

    favorites.forEach(function(item, index) {

        html += `
            <div class="favorite-item">

                <div class="favorite-question">
                    ⭐ ${escapeHtml(item.question)}
                </div>

                <div class="favorite-answer">
                    ${escapeHtml(item.answer)}
                </div>

                <div class="history-date">
                    ${escapeHtml(item.date)}
                </div>

                <div class="favorite-actions">

                    <button
                        type="button"
                        onclick="loadFavorite(${index})"
                    >
                        📖 Open
                    </button>

                    <button
                        class="delete-button"
                        type="button"
                        onclick="deleteFavorite(${index})"
                    >
                        🗑️ Delete
                    </button>

                </div>

            </div>
        `;
    });

    list.innerHTML = html;
}


function loadFavorite(index) {

    const item = favorites[index];

    if (!item) {
        return;
    }

    document.getElementById("msg").value =
        item.question;

    document.getElementById("answer").innerText =
        item.answer;

    currentQuestion =
        item.question;

    currentAnswer =
        item.answer;

    document.getElementById(
        "favoritesPanel"
    ).style.display = "none";

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


function deleteFavorite(index) {

    favorites.splice(index, 1);

    localStorage.setItem(
        "medai_favorites",
        JSON.stringify(favorites)
    );

    renderFavorites();
}


/* Escape HTML */

function escapeHtml(text) {

    const div =
        document.createElement("div");

    div.textContent = text;

    return div.innerHTML;
}

</script>

</body>
</html>
"""


def search_wikimedia_images(search_term):

    api_url = (
        "https://commons.wikimedia.org/"
        "w/api.php"
    )

    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "generator": "search",
        "gsrsearch": search_term,
        "gsrnamespace": "6",
        "gsrlimit": "6",
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": "600"
    }

    headers = {
        "User-Agent":
            "MedAI/1.0 (medical educational application)"
    }

    try:

        response = requests.get(
            api_url,
            params=params,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        pages = (
            data
            .get("query", {})
            .get("pages", [])
        )

        if isinstance(pages, dict):
            pages = pages.values()

        results = []

        for page in pages:

            imageinfo = page.get(
                "imageinfo",
                []
            )

            if not imageinfo:
                continue

            info = imageinfo[0]

            image_url = (
                info.get("thumburl")
                or info.get("url")
            )

            if not image_url:
                continue

            page_url = info.get(
                "descriptionurl"
            )

            title = page.get(
                "title",
                "Medical image"
            )

            if not page_url:

                page_url = (
                    "https://commons.wikimedia.org/wiki/"
                    + urllib.parse.quote(
                        title,
                        safe=""
                    )
                )

            results.append({
                "title":
                    title.replace(
                        "File:",
                        ""
                    ),

                "image_url":
                    image_url,

                "page_url":
                    page_url
            })

        return results

    except Exception as e:

        print(
            "Wikimedia error:",
            str(e)
        )

        return []


@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    message = (
        data
        .get("message", "")
        .strip()
    )

    if not message:

        return jsonify({
            "error":
                "Please enter your question."
        }), 400

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:

        return jsonify({
            "error":
                "GEMINI_API_KEY پیدا نه شو."
        }), 500

    prompt = f"""
You are MedAI, a multilingual educational medical information assistant.

LANGUAGE RULES:

- Automatically detect the language of the user's question.
- Answer in the SAME language as the user's question.
- Support as many languages as possible.
- If the user mixes languages, use the main language.
- Keep medical terminology accurate.
- Explain difficult medical terminology simply.
- Section headings must also be written in the user's language.

MEDICAL SAFETY:

- Provide accurate educational medical information.
- Do not diagnose a person from symptoms alone.
- Do not pretend that you examined the patient.
- Do not invent medical facts.
- Do not give personalized prescription or dosage instructions.
- If emergency warning signs are relevant, advise urgent medical care.
- MedAI is educational and is not a replacement for a doctor.

MEDICAL STRUCTURE:

For medical questions, use these sections when relevant:

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

Translate every section heading into the user's language.

FORMATTING:

- Use clear headings.
- Use bullet points when useful.
- Keep paragraphs short.
- Make the answer easy to read.
- Explain difficult medical words simply.
- Do not include irrelevant sections.
- Give a useful educational explanation.
- Keep important warnings clear.

USER QUESTION:

{message}
"""

    gemini_url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        "gemini-3.5-flash-lite:"
        "generateContent?key="
        + api_key
    )

    try:

        response = requests.post(
            gemini_url,
            headers={
                "Content-Type":
                    "application/json"
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

        gemini_data = response.json()

        if response.status_code != 200:

            print(
                "Gemini API error:",
                gemini_data
            )

            return jsonify({
                "error":
                    "Gemini API خطا ورکړه."
            }), 500

        candidates = (
            gemini_data
            .get("candidates", [])
        )

        if not candidates:

            return jsonify({
                "error":
                    "Gemini هېڅ ځواب رانه کړ."
            }), 500

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )

        if not parts:

            return jsonify({
                "error":
                    "د Gemini ځواب خالي دی."
            }), 500

        answer = (
            parts[0]
            .get("text", "")
        )

        if not answer:

            return jsonify({
                "error":
                    "AI ځواب پیدا نه شو."
            }), 500

        search_term = message

        translations = {
            "بکتریا": "bacteria",
            "باکتریا": "bacteria",
            "bacteria": "bacteria",

            "سینه بغل": "pneumonia",
            "pneumonia": "pneumonia",

            "شکر": "diabetes",
            "ډایبېټس": "diabetes",
            "diabetes": "diabetes",

            "فشار": "hypertension",
            "لوړ فشار": "hypertension",
            "hypertension": "hypertension",

            "زړه": "heart",
            "د زړه": "heart disease",
            "heart": "heart",

            "سږي": "lungs",
            "سږو": "lungs",

            "معده": "stomach",
            "ځیګر": "liver",
            "پښتورګي": "kidney",
            "دماغ": "brain",
            "پوستکی": "skin",
            "هډوکي": "bone",

            "انفلونزا": "influenza",
            "influenza": "influenza",

            "سرطان": "cancer",
            "cancer": "cancer",

            "وینه": "blood",
            "blood": "blood",

            "ویروس": "virus",
            "virus": "virus",

            "coronavirus": "coronavirus",
            "covid": "COVID-19",
            "کووېډ": "COVID-19"
        }

        lower_message = message.lower()

        for word, english in translations.items():

            if word.lower() in lower_message:

                search_term = english
                break

        images = search_wikimedia_images(
            search_term
        )

        return jsonify({
            "answer": answer,
            "images": images
        })

    except requests.exceptions.Timeout:

        return jsonify({
            "error":
                "د AI ځواب ډېر وخت ونیو. بیا هڅه وکړئ."
        }), 504

    except Exception as e:

        print(
            "Chat error:",
            str(e)
        )

        return jsonify({
            "error":
                "د AI سره د اړیکې ستونزه رامنځته شوه."
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
