from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return "MedAI is working"


@app.route("/chat", methods=["POST"])
def chat():
    return jsonify({
        "answer": "MedAI is working"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
