
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import datetime
import re

app = Flask(__name__)

# --- Configs ---
admin_users = {
    "shop1": {"username": "shop1", "password": "pass123", "menu": {}, "availability": True, "loyalty_enabled": False}
    # Add more shops here
}

user_sessions = {}
order_log = []
default_shop = "shop1"

# --- Helper Functions ---

def parse_menu_update(message_lines):
    menu = {}
    for line in message_lines:
        try:
            item, price = line.rsplit(" ", 1)
            menu[item.strip()] = float(price.strip())
        except ValueError:
            continue
    return menu

def get_user_shop(phone_number):
    return default_shop

def build_menu_response(shop_name):
    menu = admin_users[shop_name]["menu"]
    if not menu:
        return "📭 Menu is currently empty. Please update it first."
    response = """📋 Current Menu:
"""
    for item, price in menu.items():
        response += f"• {item}: {price:.2f} JOD
"
    return response

def confirm_order(order_items):
    response = """🧾 Your Order Summary:
"""
    total = 0
    for item, qty in order_items.items():
        price = admin_users[default_shop]["menu"].get(item, 0)
        total += price * qty
        response += f"{qty} × {item} = {price * qty:.2f} JOD
"
    response += f"
Total: {total:.2f} JOD
✅ Reply '1' to confirm or '2' to edit."
    return response

# --- Routes ---

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.values.get("Body", "").strip()
    from_number = request.values.get("From", "").split(":")[-1]
    resp = MessagingResponse()
    msg = resp.message()

    session = user_sessions.get(from_number, {"step": "start", "order": {}})
    shop = get_user_shop(from_number)

    # Admin login
    if incoming_msg.lower().startswith("#login"):
        parts = incoming_msg.split(" ")
        if len(parts) == 3:
            _, username, password = parts
            if username in admin_users and admin_users[username]["password"] == password:
                session["admin"] = username
                user_sessions[from_number] = session
                msg.body(f"✅ Logged in as {username}.")
                return str(resp)
        msg.body("❌ Login failed. Format: #login username password")
        return str(resp)

    # Admin commands
    if session.get("admin"):
        if incoming_msg.lower().startswith("#menu update"):
            menu_lines = incoming_msg.splitlines()[1:]
            new_menu = parse_menu_update(menu_lines)
            admin_users[session["admin"]]["menu"] = new_menu
            msg.body("✅ Menu updated successfully.")
            return str(resp)
        elif incoming_msg.lower() == "#availability":
            availability = admin_users[session["admin"]]["availability"]
            msg.body(f"📦 Current availability is: {'Available' if availability else 'Closed'}.")
            return str(resp)
        elif incoming_msg.lower() == "#close today":
            admin_users[session["admin"]]["availability"] = False
            msg.body("🔒 Shop marked as closed for today.")
            return str(resp)

    # Customer logic
    if session["step"] == "start":
        if "menu" in incoming_msg.lower() or "شو" in incoming_msg:
            msg.body(build_menu_response(shop))
            session["step"] = "ordering"
            user_sessions[from_number] = session
            return str(resp)
        elif incoming_msg.lower() in ["hi", "مرحبا", "hello"]:
            msg.body("أهلاً فيك 👋 شو حابب تطلب اليوم؟")
            return str(resp)
        else:
            msg.body("👋 أكتب 'menu' أو 'شو في' لعرض المنيو.")
            return str(resp)

    if session["step"] == "ordering":
        match = re.findall(r"(\d+)\s*[x×]?\s*(.+)", incoming_msg)
        if match:
            for qty, item in match:
                item = item.strip()
                qty = int(qty)
                if item in session["order"]:
                    session["order"][item] += qty
                else:
                    session["order"][item] = qty
            msg.body(confirm_order(session["order"]))
            session["step"] = "confirm"
            user_sessions[from_number] = session
            return str(resp)
        else:
            msg.body("❗ الرجاء كتابة الطلب بهالشكل: 2 Shawarma")
            return str(resp)

    if session["step"] == "confirm":
        if incoming_msg == "1":
            order_log.append({"user": from_number, "order": session["order"], "timestamp": str(datetime.datetime.now())})
            msg.body("✅ تم استلام طلبك! بنوصلك بأقرب وقت.")
            user_sessions[from_number] = {"step": "start", "order": {}}
            return str(resp)
        elif incoming_msg == "2":
            msg.body("✏️ رجاء أرسل الطلب من جديد.")
            session["step"] = "ordering"
            session["order"] = {}
            user_sessions[from_number] = session
            return str(resp)

    msg.body("❓ مش قادر أفهم طلبك. جرب تكتب 'menu' أو اسم الوجبة.")
    return str(resp)

# Render-compatible run
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)



# --- Enhancement Features ---

# Static links for menu images
menu_images = [
    "https://yourdomain.com/static/menu1.jpg",
    "https://yourdomain.com/static/menu2.jpg"
]

# Calorie and ingredient database
calories = {
    "burger": 550,
    "pizza": 800,
    "shawarma": 420,
    "cola": 150,
    "water": 0
}

ingredients = {
    "burger": "Beef patty, lettuce, tomato, cheese, bun",
    "pizza": "Cheese, tomato sauce, dough, toppings",
    "shawarma": "Chicken, garlic sauce, pickles, wrap"
}

# Detect Arabic numerals and convert to int
arabic_to_english_digits = {
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
    "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9"
}

def normalize_arabic_numbers(text):
    for ar, en in arabic_to_english_digits.items():
        text = text.replace(ar, en)
    return text
