from flask import Flask, request, jsonify
import os
import requests
import urllib.parse

app = Flask(__name__)


# =========================================================
# HOME
# =========================================================

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
}

button {
    width: 100%;
    margin-top: 12px;
    padding: 14px;
    border: none;
    border-radius: 12px;
    background: #1677ff;
    color: white;
    font-size: 17px;
    cursor: pointer;
}

button:disabled {
    background: #999;
}

.actions {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
}

.actions button {
    margin-top: 10px;
}

.history-btn {
    background: #555;
}

.favorite-btn {
    background: #e09b00;
}

.save-btn {
    background: #f5a623;
}

.dark-btn {
    background: #222;
}

#answer {
    margin-top: 20px;
    padding: 20px;
    background: white;
    border-radius: 12px;
    line-height: 2;
    white-space: pre-wrap;
    min-height: 100px;
}

.panel {
    display: none;
    margin-top: 20px;
    padding: 18px;
    background: white;
    border-radius: 12px;
}

.panel-title {
    font-size: 22px;
    font-weight: bold;
    margin-bottom: 15px;
}

.item {
    padding: 14px;
    margin-bottom: 10px;
    border: 1px solid #ddd;
    border-radius: 10px;
    background: #fafafa;
}

.question {
    font-weight: bold;
    color: #1677ff;
    margin-bottom: 8px;
}

.favorite-question {
    color: #e09b00;
}

.date {
    font-size: 12px;
    color: #888;
}

.item-buttons {
    display: flex;
    gap: 8px;
}

.item-buttons button {
    margin-top: 10px;
    padding: 9px;
}

.delete {
    background: #dc3545;
}

.clear {
    background: #777;
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
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 15px;
}

.image-card {
    background: white;
    padding: 10px;
    border-radius: 12px;
}

.image-card img {
    width: 100%;
    height: 220px;
    object-fit: contain;
    background: #eee;
    border-radius: 10px;
}

.warning {
    margin-top: 25px;
    padding: 15px;
    background: #fff4d6;
    color: #6b5200;
    border-radius: 10px;
    line-height: 1.8;
}


/* DARK MODE */

body.dark {
    background: #121212;
    color: white;
}

body.dark textarea {
    background: #1e1e1e;
    color: white;
    border-color: #444;
}

body.dark #answer,
body.dark .panel,
body.dark .image-card {
    background: #1e1e1e;
    color: white;
}

body.dark .item {
    background: #252525;
    border-color: #444;
}

body.dark .warning {
    background: #3b3215;
    color: #ffe99a;
}


/* MOBILE */

@media (max-width: 700px) {

    body {
        padding: 10px;
    }

    .actions {
        grid-template-columns: 1fr 1fr;
    }

    .image-grid {
        grid-template-columns: 1fr;
    }

    textarea {
        font-size: 16px;
    }
}

@media (max-width: 400px) {

    .actions {
        grid-template-columns: 1fr;
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
    id="question"
    placeholder="Ask any medical question..."
></textarea>


<button
    id="askButton"
    onclick="askQuestion()"
>
پوښتنه
</button>


<div class="actions">

<button
    class="history-btn"
    onclick="toggleHistory()"
>
📜 History
</button>

<button
    class="favorite-btn"
    onclick="toggleFavorites()"
>
⭐ Favorites
</button>

<button
    class="save-btn"
    onclick="saveAnswer()"
>
💾 Save
</button>

<button
    class="dark-btn"
    id="darkButton"
    onclick="toggleDarkMode()"
>
🌙 Dark Mode
</button>

</div>


<div id="answer">
ستاسو ځواب به دلته ښکاره شي.
</div>


<div id="images"></div>


<!-- HISTORY -->

<div
    id="historyPanel"
    class="panel"
>

<div class="panel-title">
📜 د پخوانیو پوښتنو تاریخ
</div>

<div id="historyList"></div>

<button
    class="clear"
    onclick="clearHistory()"
>
🗑️ Clear History
</button>

</div>


<!-- FAVORITES -->

<div
    id="favoritesPanel"
    class="panel"
>

<div class="panel-title">
⭐ خوندي شوي ځوابونه
</div>

<div id="favoritesList"></div>

</div>


<div class="warning">

⚠️ MedAI د طبي زده کړو او معلوماتو لپاره دی.

دا د ډاکټر بدیل نه دی.

که بیړنۍ یا جدي نښې موجودې وي،
له روغتیايي مسلکي کس سره ژر اړیکه ونیسئ.

</div>

</div>


<script>


// =========================================================
// DATA
// =========================================================

let currentQuestion = "";
let currentAnswer = "";


let history = JSON.parse(
    localStorage.getItem("medai_history") || "[]"
);


let favorites = JSON.parse(
    localStorage.getItem("medai_favorites") || "[]"
);


// =========================================================
// ASK QUESTION
// =========================================================

async function askQuestion() {

    const input =
        document.getElementById("question");

    const answer =
        document.getElementById("answer");

    const button =
        document.getElementById("askButton");

    const images =
        document.getElementById("images");


    const message =
        input.value.trim();


    if (!message) {

        answer.innerText =
            "Please enter your question.";

        return;
    }


    currentQuestion =
        message;


    currentAnswer =
        "";


    answer.innerText =
        "⏳ ځواب چمتو کېږي...";


    images.innerHTML =
        "";


    button.disabled =
        true;


    button.innerText =
        "⏳ انتظار وکړئ";


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


        if (data.answer) {

            currentAnswer =
                data.answer;


            answer.innerText =
                data.answer;


            addHistory(
                message,
                data.answer
            );


        } else {

            answer.innerText =
                data.error ||
                "یوه ستونزه رامنځته شوه.";

        }


        showImages(
            data.images || []
        );


    } catch (error) {

        answer.innerText =
            "❌ د سرور سره د اړیکې ستونزه رامنځته شوه.";

    }


    button.disabled =
        false;


    button.innerText =
        "پوښتنه";
}


// =========================================================
// SHOW IMAGES
// =========================================================

function showImages(images) {

    const container =
        document.getElementById("images");


    if (!images.length) {

        container.innerHTML =
            "";

        return;
    }


    let html = `
        <div class="image-title">
            🖼️ Related Medical Images
        </div>

        <div class="image-grid">
    `;


    images.forEach(
        function(image) {

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

                    <div>
                        ${escapeHtml(image.title)}
                    </div>

                </div>

            `;
        }
    );


    html += `
        </div>
    `;


    container.innerHTML =
        html;
}


// =========================================================
// HISTORY ADD
// =========================================================

function addHistory(
    question,
    answer
) {

    history.unshift({

        question: question,

        answer: answer,

        date:
            new Date().toLocaleString()

    });


    history =
        history.slice(0, 50);


    localStorage.setItem(
        "medai_history",
        JSON.stringify(history)
    );


    renderHistory();
}


// =========================================================
// HISTORY TOGGLE
// =========================================================

function toggleHistory() {

    const panel =
        document.getElementById(
            "historyPanel"
        );


    const favoritesPanel =
        document.getElementById(
            "favoritesPanel"
        );


    favoritesPanel.style.display =
        "none";


    if (
        panel.style.display === "none" ||
        panel.style.display === ""
    ) {

        panel.style.display =
            "block";

        renderHistory();

    } else {

        panel.style.display =
            "none";
    }
}


// =========================================================
// HISTORY RENDER
// =========================================================

function renderHistory() {

    const list =
        document.getElementById(
            "historyList"
        );


    if (!history.length) {

        list.innerHTML =
            "<p>تراوسه History نشته.</p>";

        return;
    }


    let html = "";


    history.forEach(
        function(item, index) {

            html += `

                <div class="item">

                    <div class="question">

                        ${escapeHtml(
                            item.question
                        )}

                    </div>

                    <div class="date">

                        ${escapeHtml(
                            item.date
                        )}

                    </div>

                    <div class="item-buttons">

                        <button
                            onclick="openHistory(${index})"
                        >
                            📖 Open
                        </button>

                        <button
                            class="delete"
                            onclick="deleteHistory(${index})"
                        >
                            🗑️ Delete
                        </button>

                    </div>

                </div>

            `;
        }
    );


    list.innerHTML =
        html;
}


// =========================================================
// HISTORY OPEN
// =========================================================

function openHistory(index) {

    const item =
        history[index];


    if (!item) {
        return;
    }


    document.getElementById(
        "question"
    ).value =
        item.question;


    document.getElementById(
        "answer"
    ).innerText =
        item.answer;


    currentQuestion =
        item.question;


    currentAnswer =
        item.answer;


    document.getElementById(
        "historyPanel"
    ).style.display =
        "none";
}


// =========================================================
// HISTORY DELETE
// =========================================================

function deleteHistory(index) {

    history.splice(
        index,
        1
    );


    localStorage.setItem(
        "medai_history",
        JSON.stringify(history)
    );


    renderHistory();
}


// =========================================================
// HISTORY CLEAR
// =========================================================

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


// =========================================================
// SAVE FAVORITE
// =========================================================

function saveAnswer() {

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
        favorites.some(
            function(item) {

                return (
                    item.question ===
                    currentQuestion
                );

            }
        );


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


    renderFavorites();


    alert(
        "⭐ ځواب خوندي شو."
    );
}


// =========================================================
// FAVORITES TOGGLE
// =========================================================

function toggleFavorites() {

    const panel =
        document.getElementById(
            "favoritesPanel"
        );


    const historyPanel =
        document.getElementById(
            "historyPanel"
        );


    historyPanel.style.display =
        "none";


    if (
        panel.style.display === "none" ||
        panel.style.display === ""
    ) {

        panel.style.display =
            "block";

        renderFavorites();

    } else {

        panel.style.display =
            "none";
    }
}


// =========================================================
// FAVORITES RENDER
// =========================================================

function renderFavorites() {

    const list =
        document.getElementById(
            "favoritesList"
        );


    if (!favorites.length) {

        list.innerHTML =
            "<p>تراوسه خوندي شوي ځوابونه نشته.</p>";

        return;
    }


    let html = "";


    favorites.forEach(
        function(item, index) {

            html += `

                <div class="item">

                    <div
                        class="question favorite-question"
                    >

                        ⭐ ${escapeHtml(
                            item.question
                        )}

                    </div>


                    <div>

                        ${escapeHtml(
                            item.answer
                        )}

                    </div>


                    <div class="date">

                        ${escapeHtml(
                            item.date
                        )}

                    </div>


                    <div class="item-buttons">

                        <button
                            onclick="openFavorite(${index})"
                        >
                            📖 Open
                        </button>

                        <button
                            class="delete"
                            onclick="deleteFavorite(${index})"
                        >
                            🗑️ Delete
                        </button>

                    </div>

                </div>

            `;
        }
    );


    list.innerHTML =
        html;
}


// =========================================================
// FAVORITE OPEN
// =========================================================

function openFavorite(index) {

    const item =
        favorites[index];


    if (!item) {
        return;
    }


    document.getElementById(
        "question"
    ).value =
        item.question;


    document.getElementById(
        "answer"
    ).innerText =
        item.answer;


    currentQuestion =
        item.question;


    currentAnswer =
        item.answer;


    document.getElementById(
        "favoritesPanel"
    ).style.display =
        "none";
}


// =========================================================
// FAVORITE DELETE
// =========================================================

function deleteFavorite(index) {

    favorites.splice(
        index,
        1
    );


    localStorage.setItem(
        "medai_favorites",
        JSON.stringify(favorites)
    );


    renderFavorites();
}


// =========================================================
// ESCAPE HTML
// =========================================================

function escapeHtml(text) {

    const div =
        document.createElement("div");


    div.textContent =
        text;


    return div.innerHTML;
}


// =========================================================
// DARK MODE
// =========================================================

function toggleDarkMode() {

    document.body.classList.toggle(
        "dark"
    );


    const enabled =
        document.body.classList.contains(
            "dark"
        );


    localStorage.setItem(
        "medai_dark",
        enabled
        ? "on"
        : "off"
    );


    updateDarkButton();
}


// =========================================================
// DARK BUTTON
// =========================================================

function updateDarkButton() {

    const button =
        document.getElementById(
            "darkButton"
        );


    if (!button) {
        return;
    }


    if (
        document.body.classList.contains(
            "dark"
        )
    ) {

        button.innerText =
            "☀️ Light Mode";

    } else {

        button.innerText =
            "🌙 Dark Mode";
    }
}


// =========================================================
// LOAD DARK MODE
// =========================================================

if (
    localStorage.getItem(
        "medai_dark"
    ) === "on"
) {

    document.body.classList.add(
        "dark"
    );
}


updateDarkButton();

renderHistory();

renderFavorites();

</script>

</body>
</html>
"""


# =========================================================
# WIKIMEDIA IMAGES
# =========================================================

def search_wikimedia_images(search_term):

    api_url = (
        "https://commons.wikimedia.org/w/api.php"
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
            "MedAI/1.0 medical educational application"

    }


    try:

        response = requests.get(
            api_url,
            params=params,
            headers=headers,
            timeout=20
        )


        response.raise_for_status()


        data =
            response.json()


        pages =
            data.get(
                "query",
                {}
            ).get(
                "pages",
                []
            )


        if isinstance(pages, dict):
            pages = pages.values()


        results = []


        for page in pages:

            imageinfo =
                page.get(
                    "imageinfo",
                    []
                )


            if not imageinfo:
                continue


            info =
                imageinfo[0]


            image_url =
                info.get(
                    "thumburl"
                ) or info.get(
                    "url"
                )


            if not image_url:
                continue


            title =
                page.get(
                    "title",
                    "Medical image"
                )


            page_url =
                info.get(
                    "descriptionurl"
                )


            if not page_url:

                page_url = (
                    "https://commons.wikimedia.org/wiki/"
                    +
                    urllib.parse.quote(
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


    except Exception as error:

        print(
            "Wikimedia error:",
            error
        )

        return []


# =========================================================
# CHAT
# =========================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    data =
        request.get_json(
            silent=True
        ) or {}


    message =
        data.get(
            "message",
            ""
        ).strip()


    if not message:

        return jsonify({

            "error":
                "Please enter your question."

        }), 400


    api_key =
        os.getenv(
            "GEMINI_API_KEY"
        )


    if not api_key:

        return jsonify({

            "error":
                "GEMINI_API_KEY پیدا نه شو."

        }), 500


    prompt = f"""
You are MedAI, a multilingual educational medical information assistant.

Answer in the SAME language as the user's question.

Support many languages.

Translate section headings into the user's language.

Give accurate educational medical information.

Do not diagnose a person from symptoms alone.

Do not pretend to examine the patient.

Do not invent medical facts.

Do not give personalized prescription or dosage instructions.

If emergency warning signs are relevant, advise urgent medical care.

MedAI is educational and is not a replacement for a doctor.

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

Use clear headings and bullet points.

Keep paragraphs short.

Explain difficult medical terms simply.

USER QUESTION:

{message}
"""


    gemini_url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        "gemini-3.5-flash-lite:generateContent?key="
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

                                "text":
                                    prompt

                            }

                        ]

                    }

                ]

            },

            timeout=60
        )


        gemini_data =
            response.json()


        if response.status_code != 200:

            return jsonify({

                "error":
                    "Gemini API خطا ورکړه: "
                    +
                    str(gemini_data)

            }), 500


        candidates =
            gemini_data.get(
                "candidates",
                []
            )


        if not candidates:

            return jsonify({

                "error":
                    "Gemini هېڅ ځواب رانه کړ."

            }), 500


        parts =
            candidates[0].get(
                "content",
                {}
            ).get(
                "parts",
                []
            )


        if not parts:

            return jsonify({

                "error":
                    "د Gemini ځواب خالي دی."

            }), 500


        answer =
            parts[0].get(
                "text",
                ""
            )


        if not answer:

            return jsonify({

                "error":
                    "AI ځواب پیدا نه شو."

            }), 500


        # =================================================
        # IMAGE SEARCH TERM
        # =================================================

        search_term =
            message


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


        lower_message =
            message.lower()


        for word, english in translations.items():

            if word.lower() in lower_message:

                search_term =
                    english

                break


        images =
            search_wikimedia_images(
                search_term
            )


        return jsonify({

            "answer":
                answer,

            "images":
                images

        })


    except requests.exceptions.Timeout:

        return jsonify({

            "error":
                "د AI ځواب ډېر وخت ونیو. بیا هڅه وکړئ."

        }), 504


    except Exception as error:

        print(
            "Chat error:",
            error
        )


        return jsonify({

            "error":
                "د AI سره د اړیکې ستونزه: "
                +
                str(error)

        }), 500


# =========================================================
# LOCAL RUN
# =========================================================

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
