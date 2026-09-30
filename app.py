from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <html>
    <head>
        <meta charset="UTF-8">
        <title>MedAI</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 40px auto;
                padding: 20px;
                background: #f5f7fa;
            }
            h1 { text-align: center; }
            input {
                width: 70%;
                padding: 14px;
                border-radius: 10px;
                border: 1px solid #ccc;
                font-size: 16px;
            }
            button {
                padding: 14px 20px;
                border: 0;
                border-radius: 10px;
                cursor: pointer;
            }
            #answer {
                background: white;
                padding: 20px;
                border-radius: 12px;
                margin-top: 20px;
                white-space: pre-wrap;
            }
        </style>
    </head>

    <body>
        <h1>🩺 MedAI</h1>
        <p style="text-align:center;">ستاسو د طبي زده کړو هوښیار مرستیال</p>

        <input id="msg" placeholder="مثلاً: Bacteria څه شی دی؟">
        <button onclick="send()">پوښتنه</button>

        <div id="answer"></div>

        <script>
        async function send() {
            const msg = document.getElementById("msg").value;
            const answer = document.getElementById("answer");

            if (!msg) return;

            answer.innerText = "ځواب چمتو کېږي...";

            const r = await fetch("/chat", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({message: msg})
            });

            const d = await r.json();
            answer.innerText = d.answer || d.error || "ستونزه رامنځته شوه.";
        }
        </script>
    </body>
    </html>
    """

@app.route("/chat", methods=["POST"])
def chat():
    message = request.json.get("message", "")

    answer = f"""ستاسو پوښتنه:
{message}

MedAI به د دې پوښتنې لپاره طبي معلومات، تعریف، ډولونه، نښې، تشخیص، درملنه، مخنیوی او مهم ټکي وړاندې کړي.

یادونه: دا معلومات د زده کړې لپاره دي او د ډاکټر بدیل نه دي."""

    return jsonify({"answer": answer})


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
