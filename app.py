from flask import Flask, request, jsonify
import os
import requests
from urllib.parse import quote

app = Flask(__name__)


# -----------------------------
# HOME PAGE
# -----------------------------
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

body {
    font-family: Arial, sans-serif;
    background: #f4f7fb;
    margin: 0;
    padding: 20px;
}

.container {
    max-width: 850px;
    margin: auto;
}

h1 {
    text-align: center;
    color: #1677ff;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #555;
    margin-bottom: 25px;
}

textarea {
    width: 100%;
    height: 130px;
    box-sizing: border-box;
    padding: 15px;
    border: 1px solid #ccc;
    border-radius: 12px;
    font-size: 17px;
    resize: vertical;
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
    background: #0f5dcc;
}

#answer {
    background: white;
    margin-top: 20px;
    padding: 22px;
    border-radius: 12px;
    line-height: 2;
    white-space: pre-wrap;
    min-height: 50px;
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
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}

.medical-image {
    width: 100%;
    height: 220px;
    object-fit: cover;
    border-radius: 10px;
}

.image-caption {
    margin-top: 8px;
    font-size: 14px;
    line-height: 1.5;
}

.image-link {
    color: #1677ff;
    text-decoration: none;
}

.warning {
    margin-top: 25px;
    padding: 15px;
    background: #fff4d6;
    border-radius: 10px;
    color: #6b5200;
    line-height: 1.8;
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
placeholder="مثلاً: Bacteria څه شی دی؟">
</textarea>


<button onclick="sendQuestion()">
پوښتنه
</button>


<div id="answer">
ستاسو ځواب به دلته ښکاره شي.
</div>


<div id="images"></div>


<div class="warning">
⚠️ MedAI د طبي زده کړو لپاره دی.
دا د ډاکټر بدیل نه دی.
د جدي یا بیړنیو نښو په صورت کې له روغتیايي مسلکي کس سره اړیکه ونیسئ.
</div>

</div>


<script>

async function sendQuestion() {

    const message =
        document.getElementById("msg").value.trim();

    const answer =
        document.getElementById("answer");

    const images =
        document.getElementById("images");


    if (!message) {

        answer.innerText =
            "مهرباني وکړئ خپله پوښتنه ولیکئ.";

        images.innerHTML = "";

        return;
    }


    answer.innerText =
        "⏳ ځواب چمتو کېږي...";

    images.innerHTML = "";


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


        if (data.answer) {

            answer.innerText = data.answer;

        } else {

            answer.innerText =
                data.error || "یوه ستونزه رامنځته شوه.";

        }


        if (data.images && data.images.length > 0) {

            let html = `
                <div class="image-title">
                    🖼️ اړوند طبي انځورونه
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
                                class="medical-image"
                                src="${image.thumbnail}"
                                alt="${image.title}"
                                loading="lazy"
                            >

                        </a>

                        <div class="image-caption">

                            <a
                                class="image-link"
                                href="${image.page_url}"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                ${image.title}
                            </a>

                        </div>

                    </div>
                `;

            });


            html += "</div>";

            images.innerHTML = html;

        } else {

            images.innerHTML = `
                <div class="image-title">
                    🖼️ د دې موضوع لپاره مناسب انځور ونه موندل شو.
                </div>
            `;

        }


    } catch (error) {

        answer.innerText =
            "❌ د سرور سره د اړیکې ستونزه رامنځته شوه.";

        images.innerHTML = "";

    }

}

</script>

</body>
</html>
"""


# -----------------------------
# WIKIMEDIA IMAGE SEARCH
# -----------------------------
def search_wikimedia_images(search_term):

    api_url = "https://commons.wikimedia.org/w/api.php"

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
        "iiurlwidth": "500"
    }

    try:

        response = requests.get(
            api_url,
            params=params,
            timeout=15
        )

        if response.status_code != 200:
            return []

        data = response.json()

        pages = data.get(
            "query",
            {}
        ).get(
            "pages",
            []
        )

        results = []


        for page in pages:

            title = page.get("title", "")

            imageinfo = page.get(
                "imageinfo",
                []
            )

            if not imageinfo:
                continue


            info = imageinfo[0]

            thumbnail = info.get("thumburl")

            original_url = info.get("url")


            if not thumbnail:
                thumbnail = original_url


            if not thumbnail:
                continue


            page_url = (
                "https://commons.wikimedia.org/wiki/"
                + quote(
                    title,
                    safe=""
                )
            )


            results.append({

                "title": title.replace(
                    "File:",
                    ""
                ),

                "thumbnail": thumbnail,

                "page_url": page_url

            })


        return results


    except Exception:

        return []


# -----------------------------
# GEMINI
# -----------------------------
@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json(
        silent=True
    ) or {}


    message = data.get(
        "message",
        ""
    ).strip()


    if not message:

        return jsonify({
            "error": "مهرباني وکړئ پوښتنه ولیکئ."
        }), 400


    api_key = os.getenv(
        "GEMINI_API_KEY"
    )


    if not api_key:

        return jsonify({
            "error": "GEMINI_API_KEY پیدا نه شو."
        }), 500


    prompt = f"""
You are MedAI, an educational medical information assistant.

Answer the user's question accurately and safely.

IMPORTANT:

- Support Pashto, Dari and English.
- Reply in the same language as the user.
- Use simple language.
- Do not diagnose a person from symptoms alone.
- Do not pretend to be a doctor.
- Do not invent medical facts.
- Do not replace emergency medical care.
- For urgent symptoms, advise appropriate medical care.
- Do not give personalized prescription or dosage instructions.

For medical topics, use these headings when relevant:

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

User question:

{message}
"""


    gemini_url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
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
                                "text": prompt
                            }

                        ]

                    }

                ]

            },

            timeout=60

        )


        data = response.json()


        if response.status_code != 200:

            return jsonify({

                "error":
                "Gemini API خطا ورکړه: "
                + str(data)

            }), 500


        candidates = data.get(
            "candidates",
            []
        )


        if not candidates:

            return jsonify({

                "error":
                "Gemini هېڅ ځواب رانه کړ."

            }), 500


        parts = candidates[0] \
            .get("content", {}) \
            .get("parts", [])


        if not parts:

            return jsonify({

                "error":
                "د Gemini ځواب خالي دی."

            }), 500


        answer = parts[0].get(
            "text",
            ""
        )


        if not answer:

            return jsonify({

                "error":
                "AI ځواب پیدا نه شو."

            }), 500


        # --------------------------------
        # IMAGE SEARCH
        # --------------------------------

        # English medical keywords improve
        # Wikimedia search results.

        image_search_term = message


        # Common Pashto medical words
        # translated to better search terms.

        replacements = {

            "بکتریا": "bacteria",

            "باکتریا": "bacteria",

            "میکروب": "microorganism",

            "میکروبونه": "microorganisms",

            "سینه بغل": "pneumonia",

            "د زړه ناروغي": "heart disease",

            "شکر": "diabetes",

            "ډایبېټس": "diabetes",

            "فشار": "hypertension",

            "وینه": "blood",

            "سږي": "lungs",

            "زړه": "heart",

            "معده": "stomach",

            "ځیګر": "liver",

            "پښتورګي": "kidney",

            "دماغ": "brain",

            "هډوکي": "bone",

            "پوستکی": "skin",

            "انفلونزا": "influenza",

            "سرطان": "cancer"

        }


        for word, english in replacements.items():

            if word.lower() in message.lower():

                image_search_term = english

                break


        images = search_wikimedia_images(
            image_search_term
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

        return jsonify({

            "error":
            "د AI سره د اړیکې ستونزه: "
            + str(e)

        }), 500


# -----------------------------
# RUN
# -----------------------------
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
