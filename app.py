from flask import Flask, request, jsonify
import os
import requests
from urllib.parse import quote

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
            body {
                font-family: Arial, sans-serif;
                background: #f5f7fa;
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
                padding: 15px;
                box-sizing: border-box;
                border: 1px solid #ccc;
                border-radius: 12px;
                font-size: 17px;
                resize: vertical;
                direction: auto;
            }

            button {
                width: 100%;
                margin-top: 12px;
                padding: 15px;
                background: #1677ff;
                color: white;
                border: none;
                border-radius: 12px;
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
                direction: auto;
                min-height: 50px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }

            #images {
                margin-top: 20px;
            }

            .image-title {
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 12px;
            }

            .image-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 15px;
            }

            .medical-image {
                width: 100%;
                height: 220px;
                object-fit: cover;
                border-radius: 12px;
                background: #eee;
            }

            .image-card {
                background: white;
                padding: 10px;
                border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
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
                margin-top: 20px;
                padding: 15px;
                background: #fff4d6;
                border-radius: 10px;
                color: #6b5200;
                line-height: 1.8;
            }

            .loading {
                text-align: center;
                padding: 15px;
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
                ⚠️ MedAI د طبي زده کړو او معلوماتو لپاره دی.
                دا د ډاکټر بدیل نه دی. د جدي یا بیړنیو نښو په صورت کې
                له روغتیايي مسلکي کس سره اړیکه ونیسئ.
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
                    "مهرباني وکړئ خپله طبي پوښتنه ولیکئ.";

                images.innerHTML = "";

                return;
            }


            answer.innerText =
                "⏳ مهرباني وکړئ، ځواب چمتو کېږي...";

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


                    html += `
                        </div>
                    `;


                    images.innerHTML = html;

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


def search_medical_images(query):

    """
    Search Wikimedia Commons for relevant images.
    """

    url = "https://commons.wikimedia.org/w/api.php"


    params = {

        "action": "query",

        "format": "json",

        "formatversion": "2",

        "generator": "search",

        "gsrsearch": query,

        "gsrnamespace": "6",

        "gsrlimit": "4",

        "prop": "imageinfo",

        "iiprop": "url",

        "iiurlwidth": "500"

    }


    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )


        if response.status_code != 200:
            return []


        data = response.json()

        pages = data.get("query", {}).get("pages", [])

        results = []


        for page in pages:

            image_info = page.get("imageinfo", [])

            if not image_info:
                continue


            info = image_info[0]

            thumbnail = info.get("thumburl")

            original_url = info.get("url")


            if not thumbnail:
                thumbnail = original_url


            if not thumbnail:
                continue


            results.append({

                "title": page.get(
                    "title",
                    "Medical image"
                ).replace("File:", ""),

                "thumbnail": thumbnail,

                "page_url":
                    "https://commons.wikimedia.org/wiki/"
                    + quote(
                        page.get("title", ""),
                        safe=":/"
                    )

            })


        return results


    except Exception:

        return []


@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}

    message = data.get("message", "").strip()


    if not message:

        return jsonify({

            "error":
                "مهرباني وکړئ پوښتنه ولیکئ."

        }), 400


    api_key = os.getenv("GEMINI_API_KEY")


    if not api_key:

        return jsonify({

            "error":
                "GEMINI_API_KEY پیدا نه شو."

        }), 500


    prompt = f"""
You are MedAI, an educational medical information assistant.

Your job is to provide clear, accurate, educational medical information.

IMPORTANT RULES:

1. Support Pashto, Dari, and English.
2. Always answer in the same language as the user's question.
3. Use simple language that students can understand.
4. Do not diagnose a person from symptoms alone.
5. Do not pretend to be a doctor.
6. Do not claim that the answer replaces medical care.
7. Do not invent medical facts.
8. For emergency symptoms, advise the user to seek urgent medical care.
9. Be careful with medicines. Do not give personalized prescription or dosage instructions as if the patient has been examined.

For general medical topics, organize the answer with useful headings when appropriate:

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

If some headings are not relevant, do not force them.

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


        candidates =
            data.get("candidates", [])


        if not candidates:

            return jsonify({

                "error":
                    "Gemini هېڅ ځواب رانه کړ."

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


        # Search for related images.
        #
        # The user's question itself is used as
        # the Wikimedia search query.

        images = search_medical_images(message)


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
