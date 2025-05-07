from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ AI Order Bot is running."

@app.route("/order", methods=["POST"])
def order():
    data = request.get_json()
    message = data.get("message", "").lower()

    if "shawarma" in message:
        return jsonify({"reply": "👍 You ordered Shawarma. Confirm with 'yes' or type again."})
    elif "menu" in message:
        return jsonify({"reply": "🍽️ Our menu: Shawarma, Burger, Salad"})
    else:
        return jsonify({"reply": "👋 Welcome! Please tell me what you'd like to order."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
