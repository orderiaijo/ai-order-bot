from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import logging

app = Flask(__name__)

@app.route("/", methods=['GET'])
def home():
    return "✅ App is live."

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    incoming_msg = request.form.get('Body', '').strip()
    print(f"Received: {incoming_msg}")  # DEBUG: log message to console

    response = MessagingResponse()
    msg = response.message()

    if "menu" in incoming_msg.lower():
        msg.body("📋 Here’s our menu:\n1. Burger\n2. Pizza\n3. Salad\nReply with your choice.")
    else:
        msg.body("👋 Welcome! Type 'menu' to see our options.")

    return str(response)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=10000)
