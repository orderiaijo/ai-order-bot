
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import re
import difflib
import string

app = Flask(__name__)

# Arabic translations
TRANSLATIONS = {
    "welcome": {
        "en": "👋 Welcome! You're now browsing the {} menu.",
        "ar": "👋 مرحباً! أنت الآن تتصفح قائمة {}"
    },
    "order_prompt": {
        "en": "📋 Type item name and quantity to order, e.g. 2 shawarma.",
        "ar": "📋 اكتب اسم المنتج والكمية للطلب، مثال: ٢ شاورما"
    },
    "restart": {
        "en": "🔄 Restarting your session. What would you like to order today?",
        "ar": "🔄 تم إعادة تشغيل الجلسة. ماذا تريد أن تطلب اليوم؟"
    },
    "calories": {
        "en": "🔍 {} has ~{} calories.",
        "ar": "🔍 {} يحتوي على ~{} سعرة حرارية"
    },
    "ingredients": {
        "en": "📦 {} contains: {}",
        "ar": "📦 {} يحتوي على: {}"
    },
    "order_help": {
        "en": "🤖 I'm here to take your order. Type 'menu' to begin or item names like '2 shawarma'.",
        "ar": "🤖 أنا هنا لأخذ طلبك. اكتب 'منيو' للبدء أو اسم المنتج مثل '٢ شاورما'"
    },
    "order_summary": {
        "en": "🧾 Order Summary:",
        "ar": "🧾 ملخص الطلب:"
    },
    "subtotal": {
        "en": "💰 Subtotal: {} JOD",
        "ar": "💰 المجموع: {} دينار"
    },
    "delivery_fee": {
        "en": "🚚 Delivery Fee: {} JOD",
        "ar": "🚚 رسوم التوصيل: {} دينار"
    },
    "total": {
        "en": "💳 Total: {} JOD",
        "ar": "💳 المجموع الكلي: {} دينار"
    },
    "send_details": {
        "en": "📍 Send location + name + pickup or delivery",
        "ar": "📍 أرسل موقعك + اسمك + استلام أو توصيل"
    },
    "rate_request": {
        "en": "🌟 Please rate your experience from 1 to 5, and share any feedback.",
        "ar": "🌟 الرجاء تقييم تجربتك من ١ إلى ٥، وشاركنا رأيك."
    },
    "menu_prompt": {
        "en": "📋 Here's our menu. Type what you'd like.",
        "ar": "📋 هذه قائمتنا. اكتب ما تريد طلبه."
    }
}

def detect_language(text):
    # Check if text contains Arabic characters
    if any(ord(char) in range(0x0600, 0x06FF) for char in text):
        return "ar"
    return "en"

def get_translation(key, lang, *args):
    translation = TRANSLATIONS.get(key, {}).get(lang, TRANSLATIONS[key]["en"])
    return translation.format(*args) if args else translation

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
    try:
        from_number = request.form.get("From", "")
        incoming_msg = normalize_arabic_numbers(request.form.get("Body", "").strip().lower())
        print(f"Received message: {incoming_msg} from {from_number}")  # Debug log
        
        response = MessagingResponse()
        msg = response.message()

    session = users.get(from_number, {"type": None, "order": {}, "lang": None})

    # Always detect language from current message
    current_lang = detect_language(incoming_msg)
    session["lang"] = current_lang
    
    if session["type"] is None:
        session["type"] = detect_business_type(incoming_msg)
        msg.body(get_translation("welcome", current_lang, session["type"]))
        for img in menu_images.get(session["type"], []):
            msg.media(img)
        msg.body(get_translation("order_prompt", session["lang"]))
        users[from_number] = session
        return str(response)

    # Reset session after order
    if any(word in incoming_msg for word in ["done", "restart", "جديد", "ابدأ"]):
        users[from_number] = {"type": None, "order": {}, "lang": current_lang}
        msg.body(get_translation("restart", current_lang))
        return str(response)

    # Handle calorie and ingredients
    for item in menus[session["type"]]:
        if item in incoming_msg:
            if "calorie" in incoming_msg or "كالوري" in incoming_msg:
                msg.body(get_translation("calories", current_lang, item.title(), calories.get(item, 'N/A')))
                return str(response)
            if "مكونات" in incoming_msg or "ingredients" in incoming_msg:
                msg.body(get_translation("ingredients", current_lang, item.title(), ingredients.get(item, 'Unknown')))
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
        summary = get_translation("order_summary", current_lang) + "\n"
        total = 0
        for item, qty in session["order"].items():
            price = menus[session["type"]][item] * qty
            summary += f"• {qty} × {item.title()} = {price:.2f} {'دينار' if current_lang == 'ar' else 'JOD'}\n"
            total += price
        delivery_fee = 2.00 if total < 10 else 1.00
        summary += get_translation("subtotal", current_lang, f"{total:.2f}") + "\n"
        summary += get_translation("delivery_fee", current_lang, f"{delivery_fee:.2f}") + "\n"
        summary += get_translation("total", current_lang, f"{(total + delivery_fee):.2f}") + "\n"
        summary += get_translation("send_details", current_lang)
        
        # Add quick reply suggestions where supported
        msg.body(summary)
        msg.options([
            "Send Location 📍",
            "Pickup 🏃",
            "Delivery 🚚",
            "Add More Items ➕",
            "Start Over 🔄"
        ])
        return str(response)

    if "rate" in incoming_msg or "قيمنا" in incoming_msg:
        msg.body(get_translation("rate_request", current_lang))
        return str(response)

    # Admin commands (simplified)
    if "#menu update" in incoming_msg:
        msg.body("📤 Please send the new menu in the format: item=price, one per line.")
        return str(response)

    if "شو حابب تطلب" in incoming_msg or "menu" in incoming_msg:
        for img in menu_images.get(session["type"], []):
            msg.media(img)
        msg.body(get_translation("menu_prompt", current_lang))
        return str(response)

    msg.body(get_translation("order_help", current_lang))
        return str(response)
    except Exception as e:
        print(f"Error processing request: {e}")  # Debug log
        response = MessagingResponse()
        response.message("An error occurred. Please try again.")
        return str(response)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
