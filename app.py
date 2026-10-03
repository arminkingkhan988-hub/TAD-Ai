from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return "MedAI is running successfully!"


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "MedAI"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
