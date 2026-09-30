from flask import Flask, request, jsonify
import os
import requests
import urllib.parse

app = Flask(__name__)


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html lang="ps" dir="rtl">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>MedAI</title>

<style>

/* =========================================================
   GENERAL
   ========================================================= */

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 20px;
    font-family: Arial, sans-serif;
    background: #f4f7fb;
    color: #222;
    transition: background 0.3s, color 0.3s;
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


/* =========================================================
   INPUT
   ========================================================= */

textarea {
    width: 100%;
    height: 130px;
    padding: 15px;
    border: 1px solid #ccc;
    border-radius: 12px;
    font-size: 18px;
    resize: vertical;
    font-family: Arial, sans-serif;
    background: white;
    color: #222;
}


/* =========================================================
   BUTTONS
   ========================================================= */

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
    transition: 0.2s;
}

button:hover {
    opacity: 0.9;
}

button:disabled {
    background: #999;
    cursor: not-allowed;
}


/* =========================================================
   ACTION BUTTONS
   ========================================================= */

.action-buttons {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-top: 12px;
}

.action-buttons button {
    margin-top: 0;
}

.history-button {
    background: #555;
}

.favorite-button {
    background: #e09b00;
}

.save-button {
    background: #f5a623;
}

.dark-button {
    background: #222;
}


/* =========================================================
   ANSWER
   ========================================================= */

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


/* =========================================================
   HISTORY
   ========================================================= */

#historyPanel {
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

.history-item {
    padding: 14px;
    border: 1px solid #ddd;
    border-radius: 10px;
    margin-bottom: 10px;
    background: #fafafa;
}

.history-question {
    font-weight: bold;
    color: #1677ff;
    margin-bottom: 6px;
}

.history-date {
    font-size: 12px;
    color: #888;
}

.history-actions {
    display: flex;
    gap: 8px;
    margin-top: 10px;
}

.history-actions button {
    margin-top: 0;
    padding: 8px;
    font-size: 14px;
}

.delete-button {
    background: #dc3545;
}

.clear-button {
    background: #777;
}


/* =========================================================
   FAVORITES
   ========================================================= */

#favoritesPanel {
    display: none;
    margin-top: 20px;
    background: white;
    padding: 18px;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}

.favorite-item {
    padding: 14px;
    border: 1px solid #ddd;
    border-radius: 10px;
    margin-bottom: 10px;
    background: #fffdf5;
}

.favorite-question {
    font-weight: bold;
    color: #e09b00;
    margin-bottom: 8px;
}

.favorite-answer {
    white-space: pre-wrap;
    line-height: 1.8;
    margin-bottom: 10px;
}

.favorite-actions {
    display: flex;
    gap: 8px;
}

.favorite-actions button {
    margin-top: 0;
    padding: 8px;
    font-size: 14px;
}


/* =========================================================
   IMAGES
   ========================================================= */

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


/* =========================================================
   WARNING
   ========================================================= */

.warning {
    margin-top: 25px;
    padding: 15px;
    background: #fff4d6;
    border-radius: 10px;
    color: #6b5200;
    line-height: 1.8;
}


/* =========================================================
   DARK MODE
   ========================================================= */

body.dark-mode {
    background: #121212;
    color: #eeeeee;
}

body.dark-mode .subtitle {
    color: #bbbbbb;
}

body.dark-mode textarea {
    background: #1e1e1e;
    color: #ffffff;
    border-color: #444;
}

body.dark-mode #answer,
body.dark-mode #historyPanel,
body.dark-mode #favoritesPanel,
body.dark-mode .image-card {
    background: #1e1e1e;
    color: #eeeeee;
}

body.dark-mode .history-item {
    background: #252525;
    border-color: #444;
}

body.dark-mode .favorite-item {
    background: #292510;
    border-color: #554d25;
}

body.dark-mode .warning {
    background: #3b3215;
    color: #ffe99a;
}

body.dark-mode .no-image {
    background: #3b3215;
    color: #ffe99a;
}

body.dark-mode .history-date {
    color: #aaa;
}

body.dark-mode .image-card img {
    background: #111;
}


/* =========================================================
   MOBILE
   ========================================================= */

@media (max-width: 700px) {

    body {
        padding: 10px;
    }

    h1 {
        font-size: 28px;
    }

    .subtitle {
        font-size: 14px;
    }

    textarea {
        height: 120px;
        font-size: 16px;
    }

    #answer {
        padding: 16px;
        font-size: 15px;
        line-height: 1.9;
    }

    .action-buttons {
        grid-template-columns: 1fr 1fr;
    }

    .history-actions,
    .favorite-actions {
        flex-direction: column;
    }

    .image-grid {
        grid-template-columns: 1fr;
    }

    .image-card img {
        height: 240px;
    }
}


@media (max-width: 400px) {

    .action-buttons {
        grid-template-columns: 1fr;
    }

    h1 {
        font-size: 25px;
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
    id="askButton"
    onclick="sendQuestion()"
>
پوښتنه
</button>


<!-- =====================================================
     MAIN ACTION BUTTONS
     ===================================================== -->

<div class="action-buttons">

    <button
        class="history-button"
        onclick="toggleHistory()"
    >
        📜 History
    </button>


    <button
        class="favorite-button"
        onclick="toggleFavorites()"
    >
        ⭐ Favorites
    </button>


    <button
        class="save-button"
        onclick="saveCurrentAnswer()"
    >
        💾 Save
    </button>


    <button
        class="dark-button"
        id="darkModeButton"
        onclick="toggleDarkMode()"
    >
        🌙 Dark Mode
    </button>

</div>


<!-- =====================================================
     ANSWER
     ===================================================== -->

<div id="answer">
ستاسو ځواب به دلته ښکاره شي.
</div>


<!-- =====================================================
     IMAGES
     ===================================================== -->

<div id="images"></div>


<!-- =====================================================
     HISTORY PANEL
     ===================================================== -->

<div id="historyPanel">

    <div class="history-title">
        📜 د پخوانیو پوښتنو تاریخ
    </div>

    <div id="historyList"></div>

    <button
        class="clear-button"
        onclick="clearHistory()"
    >
        🗑️ Clear History
    </button>

</div>


<!-- =====================================================
     FAVORITES PANEL
     ===================================================== -->

<div id="favoritesPanel">

    <div class="history-title">
        ⭐ خوندي شوي ځوابونه
    </div>

    <div id="favoritesList"></div>

</div>


<!-- =====================================================
     WARNING
     ===================================================== -->

<div class="warning">

⚠️ MedAI د طبي زده کړو او معلوماتو لپاره دی.

دا د ډاکټر بدیل نه دی.

د جدي یا بیړنیو نښو په صورت کې
له روغتیايي مسلکي کس سره اړیکه ونیسئ.

</div>


</div>


<script>


// =========================================================
// CURRENT DATA
// =========================================================

let currentQuestion = "";

let currentAnswer = "";


let history = JSON.parse(
    localStorage.getItem(
        "medai_history"
    ) || "[]"
);


let favorites = JSON.parse(
    localStorage.getItem(
        "medai_favorites"
    ) || "[]"
);


// =========================================================
// SEND QUESTION
// =========================================================

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


    currentQuestion = message;


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


        // =================================================
        // DISPLAY IMAGES
        // =================================================

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


            data.images.forEach(
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
                                    alt="${image.title}"
                                    loading="lazy"
                                >

                            </a>

                            <div
                                class="image-caption"
                            >

                                <a
                                    href="${image.page_url}"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    ${escapeHtml(
                                        image.title
                                    )}
                                </a>

                            </div>

                        </div>

                    `;

                }
            );


            html += `
                </div>
            `;


            images.innerHTML = html;


        } else {

            images.innerHTML = `

                <div class="no-image">

                    🖼️ No suitable image
                    was found for this topic.

                </div>

            `;

        }


    } catch (error) {

        answer.innerText =
            "❌ د سرور سره د اړیکې ستونزه رامنځته شوه.";

        images.innerHTML = "";

    }


    button.disabled = false;

    button.innerText =
        "پوښتنه";
}


// =========================================================
// HISTORY - ADD
// =========================================================

function addToHistory(
    question,
    answer
) {

    const item = {

        question: question,

        answer: answer,

        date:
            new Date().toLocaleString()

    };


    history.unshift(item);


    history =
        history.slice(0, 50);


    localStorage.setItem(
        "medai_history",
        JSON.stringify(history)
    );


    renderHistory();
}


// =========================================================
// HISTORY - TOGGLE
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
// HISTORY - RENDER
// =========================================================

function renderHistory() {

    const list =
        document.getElementById(
            "historyList"
        );


    if (history.length === 0) {

        list.innerHTML = `

            <div class="no-image">

                تراوسه هېڅ History نشته.

            </div>

        `;

        return;
    }


    let html = "";


    history.forEach(
        function(item, index) {

            html += `

                <div class="history-item">

                    <div class="history-question">

                        ${escapeHtml(
                            item.question
                        )}

                    </div>


                    <div class="history-date">

                        ${escapeHtml(
                            item.date
                        )}

                    </div>


                    <div class="history-actions">

                        <button
                            onclick="
                                loadHistory(
                                    ${index}
                                )
                            "
                        >
                            📖 Open
                        </button>


                        <button
                            class="delete-button"
                            onclick="
                                deleteHistory(
                                    ${index}
                                )
                            "
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
// HISTORY - LOAD
// =========================================================

function loadHistory(index) {

    const item =
        history[index];


    if (!item) {
        return;
    }


    document.getElementById(
        "msg"
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


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


// =========================================================
// HISTORY - DELETE
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
// HISTORY - CLEAR
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
// FAVORITES - SAVE
// =========================================================

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
        JSON.stringify(
            favorites
        )
    );


    alert(
        "⭐ ځواب خوندي شو."
    );


    renderFavorites();
}


// =========================================================
// FAVORITES - TOGGLE
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
// FAVORITES - RENDER
// =========================================================

function renderFavorites() {

    const list =
        document.getElementById(
            "favoritesList"
        );


    if (favorites.length === 0) {

        list.innerHTML = `

            <div class="no-image">

                تراوسه هېڅ خوندي شوی
                ځواب نشته.

            </div>

        `;

        return;
    }


    let html = "";


    favorites.forEach(
        function(item, index) {

            html += `

                <div class="favorite-item">

                    <div class="favorite-question">

                        ⭐ ${escapeHtml(
                            item.question
                        )}

                    </div>


                    <div class="favorite-answer">

                        ${escapeHtml(
                            item.answer
                        )}

                    </div>


                    <div class="history-date">

                        ${escapeHtml(
                            item.date
                        )}

                    </div>


                    <div class="favorite-actions">

                        <button
                            onclick="
                                loadFavorite(
                                    ${index}
                                )
                            "
                        >
                            📖 Open
                        </button>


                        <button
                            class="delete-button"
                            onclick="
                                deleteFavorite(
                                    ${index}
                                )
                            "
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
// FAVORITES - LOAD
// =========================================================

function loadFavorite(index) {

    const item =
        favorites[index];


    if (!item) {
        return;
    }


    document.getElementById(
        "msg"
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


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


// =========================================================
// FAVORITES - DELETE
// =========================================================

function deleteFavorite(index) {

    favorites.splice(
        index,
        1
    );


    localStorage.setItem(
        "medai_favorites",
        JSON.stringify(
            favorites
        )
    );


    renderFavorites();
}


// =========================================================
// ESCAPE HTML
// =========================================================

function escapeHtml(text) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        text;


    return div.innerHTML;
}


// =========================================================
// DARK MODE
// =========================================================

function toggleDarkMode() {

    document.body.classList.toggle(
        "dark-mode"
    );


    const darkMode =
        document.body.classList.contains(
            "dark-mode"
        );


    localStorage.setItem(
        "medai_dark_mode",
        darkMode
        ? "on"
        : "off"
    );


    updateDarkModeButton();
}


// =========================================================
// DARK MODE BUTTON
// =========================================================

function updateDarkModeButton() {

    const button =
        document.getElementById(
            "darkModeButton"
        );


    if (!button) {
        return;
    }


    const darkMode =
        document.body.classList.contains(
            "dark-mode"
        );


    button.innerText =
        darkMode
        ? "☀️ Light Mode"
        : "🌙 Dark Mode";
}


// =========================================================
// LOAD DARK MODE
// =========================================================

if (
    localStorage.getItem(
        "medai_dark_mode"
    ) === "on"
) {

    document.body.classList.add(
        "dark-mode"
    );
}


updateDarkModeButton();


</script>

</body>

</html>
"""


# =========================================================
# WIKIMEDIA IMAGE SEARCH
# =========================================================

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
        "MedAI/1.0 "
        "(medical educational application)"

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


        results = []


        if isinstance(
            pages,
            dict
        ):

            pages = pages.values()


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
                or
                info.get("url")
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


    except Exception as e:

        print(
            "Wikimedia error:",
            str(e)
        )


        return []


# =========================================================
# GEMINI AI
# =========================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    data = (
        request
        .get_json(
            silent=True
        )
        or {}
    )


    message = (
        data
        .get(
            "message",
            ""
        )
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


    # =====================================================
    # MEDICAL PROMPT
    # =====================================================

    prompt = f"""
You are MedAI, a multilingual educational medical information assistant.

LANGUAGE RULES:

- Automatically detect the language of the user's question.
- Answer in the SAME language as the user's question.
- Support as many languages as possible.
- Do not force the user to select a language.
- If the user mixes languages, use the main language.
- Keep medical terminology accurate.
- Explain difficult medical terminology in simple language.
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

For medical questions, use the following sections when relevant:

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

Translate every section heading into
the user's language.

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


    # =====================================================
    # GEMINI API
    # =====================================================

    gemini_url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        "gemini-3.5-flash-lite:"
        "generateContent?key="
        +
        api_key
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


        gemini_data = response.json()


        if response.status_code != 200:

            return jsonify({

                "error":
                "Gemini API خطا ورکړه: "
                +
                str(gemini_data)

            }), 500


        candidates = (
            gemini_data
            .get(
                "candidates",
                []
            )
        )


        if not candidates:

            return jsonify({

                "error":
                "Gemini هېڅ ځواب رانه کړ."

            }), 500


        parts = (

            candidates[0]

            .get(
                "content",
                {}
            )

            .get(
                "parts",
                []
            )

        )


        if not parts:

            return jsonify({

                "error":
                "د Gemini ځواب خالي دی."

            }), 500


        answer = (
            parts[0]
            .get(
                "text",
                ""
            )
        )


        if not answer:

            return jsonify({

                "error":
                "AI ځواب پیدا نه شو."

            }), 500


        # =================================================
        # IMAGE SEARCH
        # =================================================

        search_term = message


        translations = {

            "بکتریا":
                "bacteria",

            "باکتریا":
                "bacteria",

            "bacteria":
                "bacteria",

            "سینه بغل":
                "pneumonia",

            "pneumonia":
                "pneumonia",

            "شکر":
                "diabetes",

            "ډایبېټس":
                "diabetes",

            "diabetes":
                "diabetes",

            "فشار":
                "hypertension",

            "لوړ فشار":
                "hypertension",

            "hypertension":
                "hypertension",

            "زړه":
                "heart",

            "د زړه":
                "heart disease",

            "heart":
                "heart",

            "سږي":
                "lungs",

            "سږو":
                "lungs",

            "معده":
                "stomach",

            "ځیګر":
                "liver",

            "پښتورګي":
                "kidney",

            "دماغ":
                "brain",

            "پوستکی":
                "skin",

            "هډوکي":
                "bone",

            "انفلونزا":
                "influenza",

            "influenza":
                "influenza",

            "سرطان":
                "cancer",

            "cancer":
                "cancer",

            "وینه":
                "blood",

            "blood":
                "blood",

            "ویروس":
                "virus",

            "virus":
                "virus",

            "coronavirus":
                "coronavirus",

            "covid":
                "COVID-19",

            "کووېډ":
                "COVID-19"

        }


        lower_message =
            message.lower()


        for word, english in (
            translations.items()
        ):

            if (
                word.lower()
                in lower_message
            ):

                search_term =
                    english

                break


        images =
            search_wikimedia_images(
                search_term
            )


        # =================================================
        # FINAL RESPONSE
        # =================================================

        return jsonify({

            "answer":
                answer,

            "images":
                images

        })


    except requests.exceptions.Timeout:

        return jsonify({

            "error":
            "د AI ځواب ډېر وخت ونیو. "
            "بیا هڅه وکړئ."

        }), 504


    except Exception as e:

        print(
            "Chat error:",
            str(e)
        )


        return jsonify({

            "error":
            "د AI سره د اړیکې ستونزه: "
            +
            str(e)

        }), 500


# =========================================================
# RUN
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
