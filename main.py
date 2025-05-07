from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import re

app = Flask(__name__)

# Example dynamic menu (admin can update it)
menu = {
    "burger": 3.5,
    "pizza": 4.0,
    "shawarma": 2.5
}

# Calorie and ingredient info
calories = {
    "burger": 550,
    "pizza": 800,
    "shawarma": 420
}

ingredients = {
    "burger": "Beef patty, lettuce, tomato, cheese, bun",
    "pizza": "Cheese, tomato sauce, dough, toppings",
    "shawarma": "Chicken, garlic sauce, pickles, wrap"
}

# Menu images
menu_images = [
    "https://yourdomain.com/static/menu1.jpg",
    "https://yourdomain.com/static/menu2.jpg"
]

# Arabic numerals
arabic_to_english_digits = {
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
    "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9"
}

def normalize_arabic_numbers(text):
    for ar, en in arabic_to_english_digits.items():
        text = text.replace(ar, en)
    return text

@app.route("/", methods=["GET"])
def index():
    return "✅ App is live."

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = normalize_arabic_numbers(request.form.get("Body", "").strip().lower())
    response = MessagingResponse()
    msg = response.message()

    # Menu image trigger
    if any(word in incoming_msg for word in ["menu", "قائمة", "شو حابب تطلب"]):
        for img in menu_images:
            msg.media(img)
        msg.body("📋 Here's our full menu. Type your order when ready.")
        return str(response)

    # Calorie check
    for item in calories:
        if item in incoming_msg and "calorie" in incoming_msg:
            msg.body(f"{item.title()} has around {calories[item]} calories.")
            return str(response)

    # Ingredients
    for item in ingredients:
        if item in incoming_msg and any(k in incoming_msg for k in ["ingredients", "مكونات", "what's in"]):
            msg.body(f"{item.title()} contains: {ingredients[item]}")
            return str(response)

    # Order logic
    order = {}
    for item in menu:
        match = re.search(rf"(\d+)\s*({item})", incoming_msg)
        if match:
            qty = int(match.group(1))
            order[item] = qty

    if order:
        total = sum(menu[i] * q for i, q in order.items())
        summary = "🧾 Your Order Summary:\n"
        for i, q in order.items():
            summary += f"• {q} × {i.title()} = {menu[i]*q:.2f} JOD\n"
        summary += f"💰 Total: {total:.2f} JOD\n📍 Please share your location to continue."
        msg.body(summary)
        return str(response)

    msg.body("🤖 Welcome! Type 'menu' to view our dishes, or order directly (e.g. 2 shawarma).")
    return str(response)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)