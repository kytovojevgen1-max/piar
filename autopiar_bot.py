import os
import json
import random
import requests
from flask import Flask, request

app = Flask(__name__)

# ================= НАСТРОЙКИ =================
VK_TOKEN = "vk1.a.tjIJ7CqnErXpn4Vq_nzBKQBQMjb_NcJf4kiFaJZTZoEsJ4ZCz8eBu5Z8669wHETxyU6MQ_CwhnHTQfnHLMOG6kWYjzbwap1DhP98OOs8Pj2qurp0hu7u0mDR1Ub4vdGXAq-jcKbaqp9cawQ4QZ_qnSvwwIoXZn1YEcK_c7vAkwPnpW6fc6fd936xb6vF7NAt4yw76BK5X9HHnt3CS6EfxA"

# Строка подтверждения для ВК со скриншота
CONFIRMATION_TOKEN = "c3bf119d"

# Главные владельцы (админы)
MAIN_ADMINS = [897082738, 1108641965]

DATA_FILE = "data.json"
VK_API_URL = "https://api.vk.com/method/"
API_VERSION = "5.199"

# Текст автопиара (который будет лететь в ЛС и беседы)
AUTOPIAR_TEXT = (
    "🚀 **ИЩЕШЬ КАЧЕСТВЕННЫЕ СЛИВЫ И ГОТОВЫЕ ПРОЕКТЫ ДЛЯ CRMP MOBILE?**\n\n"
    "Забудь про перекупщиков и кривые моды с багами. В **NEBULA STUDIO** есть всё для твоего сервера! 🔥\n\n"
    "💎 **Что мы предлагаем:**\n"
    "• 📱 Моды Mobile (Black Russia, Матрёшка РП)\n"
    "• 💻 ПК Моды (Radmir RP 8.4)\n"
    "• 💬 Форумы XenForo под ключ\n"
    "• 🌐 Готовые сайты и лендинги\n\n"
    "👇 **Залетай, прайс и товары здесь:**\n"
    "🔗 Telegram: t.me/NEBULASTUDIO1\n"
    "📩 VK: vk.ru/NEBULASTUDIO1"
)

# ================= БАЗА ДАННЫХ =================
def load_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "welcome_text": AUTOPIAR_TEXT,
            "admins": list(MAIN_ADMINS),
            "users": []
        }
        save_data(default_data)
        return default_data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        for aid in MAIN_ADMINS:
            if aid not in data["admins"]:
                data["admins"].append(aid)
        return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

admin_states = {}

# ================= ФУНКЦИИ ОТПРАВКИ ВК =================
def send_message(peer_id, text, keyboard=None):
    params = {
        "peer_id": peer_id,  # peer_id работает и для ЛС, и для бесед (чатов)
        "message": text,
        "random_id": random.randint(1, 2147483647),
        "access_token": VK_TOKEN,
        "v": API_VERSION
    }
    if keyboard:
        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
    requests.post(VK_API_URL + "messages.send", data=params)

# ================= КЛАВИАТУРЫ =================
def get_main_keyboard(is_admin=False):
    buttons = [
        [{"action": {"type": "text", "label": "🛒 Прайс-лист"}, "color": "primary"}],
        [
            {"action": {"type": "text", "label": "🔥 Акция / Скидка"}, "color": "positive"},
            {"action": {"type": "text", "label": "❓ FAQ / Инфо"}, "color": "secondary"}
        ],
        [{"action": {"type": "text", "label": "📩 Купить / Связь с админом"}, "color": "negative"}]
    ]
    if is_admin:
        buttons.append([{"action": {"type": "text", "label": "⚙️ Админ-панель"}, "color": "primary"}])
    return {"one_time": False, "buttons": buttons}

def get_admin_keyboard():
    return {
        "one_time": False,
        "buttons": [
            [{"action": {"type": "text", "label": "✏️ Изменить текст автопиара"}, "color": "primary"}],
            [
                {"action": {"type": "text", "label": "➕ Выдать админку"}, "color": "positive"},
                {"action": {"type": "text", "label": "➖ Снять админку"}, "color": "negative"}
            ],
            [{"action": {"type": "text", "label": "📢 Сделать рассылку"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "🔙 В главное меню"}, "color": "secondary"}]
        ]
    }

# ================= ОБРАБОТКА СООБЩЕНИЙ =================
@app.route("/", methods=["POST"])
def vk_callback():
    data = request.json
    if not data:
        return "ok"

    if data.get("type") == "confirmation":
        return CONFIRMATION_TOKEN

    if data.get("type") == "message_new":
        msg = data["object"]["message"]
        from_id = msg["from_id"]
        peer_id = msg["peer_id"] # peer_id уникален для бесед и ЛС
        text = msg.get("text", "").strip()
        text_lower = text.lower()

        db = load_data()
        
        # Если это ЛС (peer_id < 2 billion) и пользователя нет в базе — сохраняем
        if peer_id > 0 and peer_id not in db["users"]:
            db["users"].append(peer_id)
            save_data(db)

        is_admin = (from_id in db["admins"]) or (from_id in MAIN_ADMINS)

        # Обработка ввода текстов админом
        if is_admin and from_id in admin_states:
            state = admin_states.pop(from_id)
            if text_lower == "отмена":
                send_message(peer_id, "❌ Отменено.", get_admin_keyboard())
                return "ok"

            if state == "edit_autopyar":
                db["welcome_text"] = text
                save_data(db)
                send_message(peer_id, "✅ Текст автопиара успешно изменен!", get_admin_keyboard())
                return "ok"
            elif state == "broadcast":
                count = 0
                for uid in db["users"]:
                    try:
                        send_message(uid, text)
                        count += 1
                    except:
                        pass
                send_message(peer_id, f"✅ Рассылка отправлена {count} пользователям в ЛС!", get_admin_keyboard())
                return "ok"

        # Команды админ-панели
        if is_admin and text == "⚙️ Админ-панель":
            send_message(peer_id, f"⚙️ АДМИН-ПАНЕЛЬ\n👥 Юзеров в базе: {len(db['users'])}", get_admin_keyboard())
            return "ok"
        elif is_admin and text == "✏️ Изменить текст автопиара":
            admin_states[from_id] = "edit_autopyar"
            send_message(peer_id, "✍️ Отправь новый текст для автопиара (для отмены напиши 'Отмена'):")
            return "ok"
        elif is_admin and text == "📢 Сделать рассылку":
            admin_states[from_id] = "broadcast"
            send_message(peer_id, "📣 Напиши текст для мгновенной рассылки всем, кто писал в ЛС:")
            return "ok"
        elif text == "🔙 В главное меню":
            send_message(peer_id, "Главное меню:", get_main_keyboard(is_admin))
            return "ok"

        # ================= АВТОПИАР ЛОГИКА =================
        # Если сообщение пришло в беседу (peer_id > 2000000000) ИЛИ в ЛС — кидаем рекламный текст
        # (Бота добавь в беседы, и он будет отвечать рекламой на каждое новое сообщение в чате)
        current_text = db.get("welcome_text", AUTOPIAR_TEXT)
        
        if peer_id > 2000000000:
            # Это беседа (чат): отвечаем рекламой на любое сообщение в чате
            send_message(peer_id, current_text)
        else:
            # Это ЛС: отправляем текст автопиара вместе с кнопками
            send_message(peer_id, current_text, get_main_keyboard(is_admin))

    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "NEBULA STUDIO Autopyar Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
