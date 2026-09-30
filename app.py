from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "MedAI is working"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        question = data.get("question", "").strip()

        if not question:
            return jsonify({
                "answer": "Please enter a medical question."
            })

        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            return jsonify({
                "answer": "GEMINI_API_KEY is not configured."
            }), 500

        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-3.5-flash-lite:generateContent"
            f"?key={api_key}"
        )

        prompt = f"""
You are MedAI, a medical education AI.

Answer the user's medical question in the same language
the user used.

Give clear educational information using these sections when relevant:
1. Definition
2. Causes
3. Types
4. Risk Factors
5. Signs and Symptoms
6. Diagnosis
7. Treatment
8. Prevention
9. Complications
10. Important Points

Do not diagnose the user from symptoms alone.
Do not pretend to examine the patient.
Do not invent medical facts.
For emergency symptoms, advise urgent medical care.

User question:
{question}
"""

        response = requests.post(
            url,
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

        if response.status_code != 200:
            return jsonify({
                "answer": "Gemini AI request failed.",
                "details": response.text
            }), 500

        gemini_data = response.json()

        answer = (
            gemini_data["candidates"][0]
            ["content"]["parts"][0]["text"]
        )

        return jsonify({
            "answer": answer
        })

    except Exception as e:
        return jsonify({
            "answer": "An error occurred.",
            "details": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
