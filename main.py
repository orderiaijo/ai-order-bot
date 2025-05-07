
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import re
import difflib

app = Flask(__name__)

# Sample menus for multiple business types
menus = {
    "restaurant": {
        "shawarma": 2.5,
        "burger": 3.5,
        "pizza": 4.0
    },
    "supermarket": {
        "water": 0.5,
        "cigarettes": 3.0,
        "bread": 0.8
    },
    "pharmacy": {
        "panadol": 1.5,
        "vitamin c": 2.0
    }
}

calories = {
    "shawarma": 420,
    "burger": 550,
    "pizza": 800,
    "water": 0,
    "bread": 250,
    "panadol": 0
}

ingredients = {
    "shawarma": "Chicken, garlic sauce, pickles, wrap",
    "burger": "Beef patty, lettuce, tomato, cheese, bun",
    "pizza": "Cheese, tomato sauce, dough, toppings"
}

menu_images = {
    "restaurant": ["https://yourdomain.com/static/restaurant_menu1.jpg"],
    "supermarket": ["https://yourdomain.com/static/supermarket.jpg"],
    "pharmacy": ["https://yourdomain.com/static/pharmacy.jpg"]
}

arabic_to_english_digits = {
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
    "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9"
}

users = {}  # session store

def normalize_arabic_numbers(text):
    for ar, en in arabic_to_english_digits.items():
        text = text.replace(ar, en)
    return text

def detect_business_type(text):
    if any(word in text for word in ["restaurant", "مطعم", "shawarma", "burger", "بيتزا"]):
        return "restaurant"
    elif any(word in text for word in ["pharmacy", "صيدلية", "panadol"]):
        return "pharmacy"
    elif any(word in text for word in ["supermarket", "سوبر", "دخان", "مي", "ماء", "water"]):
        return "supermarket"
    return "restaurant"

@app.route("/", methods=["GET"])
def index():
    return "✅ AI WhatsApp Ordering Bot is live."

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    from_number = request.form.get("From", "")
    incoming_msg = normalize_arabic_numbers(request.form.get("Body", "").strip().lower())
    response = MessagingResponse()
    msg = response.message()

    session = users.get(from_number, {"type": None, "order": {}})

    if session["type"] is None:
        session["type"] = detect_business_type(incoming_msg)
        msg.body(f"👋 Welcome! You're now browsing the {session['type']} menu.")
        for img in menu_images.get(session["type"], []):
            msg.media(img)
        msg.body("📋 Type item name and quantity to order, e.g. 2 shawarma.")
        users[from_number] = session
        return str(response)

    # Reset session after order
    if "done" in incoming_msg or "restart" in incoming_msg:
        users[from_number] = {"type": None, "order": {}}
        msg.body("🔄 Restarting your session. What would you like to order today?")
        return str(response)

    # Handle calorie and ingredients
    for item in menus[session["type"]]:
        if item in incoming_msg:
            if "calorie" in incoming_msg or "كالوري" in incoming_msg:
                msg.body(f"🔍 {item.title()} has ~{calories.get(item, 'N/A')} calories.")
                return str(response)
            if "مكونات" in incoming_msg or "ingredients" in incoming_msg:
                msg.body(f"📦 {item.title()} contains: {ingredients.get(item, 'Unknown')}")
                return str(response)

    # Fuzzy matching for item recognition
    detected_order = {}
    for word in incoming_msg.split():
        close_matches = difflib.get_close_matches(word, menus[session["type"]].keys(), n=1, cutoff=0.6)
        if close_matches:
            qty_match = re.search(r"(\d+)", incoming_msg)
            qty = int(qty_match.group(1)) if qty_match else 1
            detected_order[close_matches[0]] = qty

    if detected_order:
        session["order"].update(detected_order)
        users[from_number] = session
        summary = "🧾 Order Summary:\n"
        total = 0
        for item, qty in session["order"].items():
            price = menus[session["type"]][item] * qty
            summary += f"• {qty} × {item.title()} = {price:.2f} JOD\n"
            total += price
        summary += f"💰 Total: {total:.2f} JOD\n📍 Send location + name + pickup or delivery."
        msg.body(summary)
        return str(response)

    if "rate" in incoming_msg or "قيمنا" in incoming_msg:
        msg.body("🌟 Please rate your experience from 1 to 5, and share any feedback.")
        return str(response)

    # Admin commands (simplified)
    if "#menu update" in incoming_msg:
        msg.body("📤 Please send the new menu in the format: item=price, one per line.")
        return str(response)

    if "شو حابب تطلب" in incoming_msg or "menu" in incoming_msg:
        for img in menu_images.get(session["type"], []):
            msg.media(img)
        msg.body("📋 Here's our menu. Type what you'd like.")
        return str(response)

    msg.body("🤖 I'm here to take your order. Type 'menu' to begin or item names like '2 shawarma'.")
    return str(response)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
