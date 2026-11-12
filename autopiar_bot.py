import os
import json
import random
import time
import requests
from flask import Flask, request

app = Flask(__name__)

# ================= НАСТРОЙКИ =================
VK_TOKEN = "vk1.a.tjIJ7CqnErXpn4Vq_nzBKQBQMjb_NcJf4kiFaJZTZoEsJ4ZCz8eBu5Z8669wHETxyU6MQ_CwhnHTQfnHLMOG6kWYjzbwap1DhP98OOs8Pj2qurp0hu7u0mDR1Ub4vdGXAq-jcKbaqp9cawQ4QZ_qnSvwwIoXZn1YEcK_c7vAkwPnpW6fc6fd936xb6vF7NAt4yw76BK5X9HHnt3CS6EfxA"
CONFIRMATION_TOKEN = "b7a2dc2e"
MAIN_ADMINS = [897082738, 1108641965]

DATA_FILE = "data.json"
VK_API_URL = "https://api.vk.com/method/"
API_VERSION = "5.199"

DEFAULT_PIAR_TEXT = (
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
            "piar_text": DEFAULT_PIAR_TEXT,
            "is_active": True,
            "admins": list(MAIN_ADMINS),
            "users": [],
            "chats": [],
            "cooldowns": {}
        }
        save_data(default_data)
        return default_data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        for aid in MAIN_ADMINS:
            if aid not in data["admins"]:
                data["admins"].append(aid)
        if "chats" not in data:
            data["chats"] = []
        if "is_active" not in data:
            data["is_active"] = True
        if "cooldowns" not in data:
            data["cooldowns"] = {}
        return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

admin_states = {}

# ================= ОТПРАВКА СООБЩЕНИЙ =================
def send_message(peer_id, text, keyboard=None):
    params = {
        "peer_id": peer_id,
        "message": text,
        "random_id": random.randint(1, 2147483647),
        "access_token": VK_TOKEN,
        "v": API_VERSION
    }
    if keyboard:
        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
    
    response = requests.post(VK_API_URL + "messages.send", data=params).json()
    
    if "error" in response:
        err_code = response["error"].get("error_code")
        if err_code in [901, 902, 917, 7]:
            return False
    return True

# ================= КЛАВИАТУРЫ =================
def get_admin_keyboard(is_active):
    status_text = "🔴 Остановить автопиар" if is_active else "🟢 Запустить автопиар"
    return {
        "one_time": False,
        "buttons": [
            [{"action": {"type": "text", "label": status_text}, "color": "negative" if is_active else "positive"}],
            [
                {"action": {"type": "text", "label": "📊 Статистика чатов"}, "color": "primary"},
                {"action": {"type": "text", "label": "✏️ Изменить текст пиара"}, "color": "primary"}
            ],
            [{"action": {"type": "text", "label": "📢 Сделать рассылку в ЛС"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "🛒 Посмотреть как клиент"}, "color": "positive"}]
        ]
    }

def get_user_keyboard():
    return {
        "one_time": False,
        "buttons": [
            [{"action": {"type": "text", "label": "🛒 Прайс-лист"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "📩 Связь с админом"}, "color": "negative"}],
            [{"action": {"type": "text", "label": "⚙️ Админ-панель"}, "color": "secondary"}]
        ]
    }

# ================= ОБРАБОТКА СОБЫТИЙ =================
@app.route("/", methods=["POST"])
def vk_callback():
    data = request.json
    if not data:
        return "ok"

    if data.get("type") == "confirmation":
        return CONFIRMATION_TOKEN

    if data.get("type") == "chat_invite_user":
        db = load_data()
        peer_id = data["object"].get("peer_id")
        if peer_id and peer_id not in db["chats"]:
            db["chats"].append(peer_id)
            save_data(db)
        return "ok"

    if data.get("type") == "message_new":
        msg = data["object"]["message"]
        from_id = msg["from_id"]
        peer_id = msg["peer_id"]
        text = msg.get("text", "").strip()
        text_lower = text.lower()

        db = load_data()
        
        if peer_id > 0 and peer_id not in db["users"]:
            db["users"].append(peer_id)
            save_data(db)

        if peer_id > 2000000000 and peer_id not in db["chats"]:
            db["chats"].append(peer_id)
            save_data(db)

        is_admin = (from_id in db["admins"]) or (from_id in MAIN_ADMINS)

        # Обработка ввода текстов админом через ЛС
        if is_admin and from_id in admin_states:
            state = admin_states.pop(from_id)
            if text_lower == "отмена":
                send_message(peer_id, "❌ Действие отменено.", get_admin_keyboard(db["is_active"]))
                return "ok"

            if state == "edit_piar":
                db["piar_text"] = text
                save_data(db)
                send_message(peer_id, "✅ Текст пиара успешно изменен! Теперь везде будет отправляться новый текст.", get_admin_keyboard(db["is_active"]))
                return "ok"
            elif state == "broadcast":
                count = 0
                for uid in db["users"]:
                    try:
                        send_message(uid, text)
                        count += 1
                    except:
                        pass
                send_message(peer_id, f"✅ Рассылка завершена! Получили: {count} чел.", get_admin_keyboard(db["is_active"]))
                return "ok"

        # Кнопки и команды админ-панели в ЛС
        if is_admin and peer_id > 0:
            if text == "⚙️ Админ-панель" or text_lower in ["админ", "миню", "меню", "start", "старт"]:
                send_message(peer_id, f"⚙️ АДМИН-ПАНЕЛЬ NEBULA STUDIO\n\n👥 Юзеров в ЛС: {len(db['users'])}\n💬 Чатов с автопиаром: {len(db['chats'])}\n⚡ Статус пиара: {'🟢 Включен' if db['is_active'] else '🔴 Выключен'}", get_admin_keyboard(db["is_active"]))
                return "ok"
            elif text == "🔴 Остановить автопиар":
                db["is_active"] = False
                save_data(db)
                send_message(peer_id, "🔴 Автопиар в беседах остановлен.", get_admin_keyboard(False))
                return "ok"
            elif text == "🟢 Запустить автопиар":
                db["is_active"] = True
                save_data(db)
                send_message(peer_id, "🟢 Автопиар в беседах запущен!", get_admin_keyboard(True))
                return "ok"
            elif text == "📊 Статистика чатов":
                active_chats = []
                for cid in db["chats"]:
                    res = send_message(cid, f"📊 Проверка связи!\n• Чатов в базе: {len(db['chats'])}\n• Юзеров в ЛС: {len(db['users'])}")
                    if res:
                        active_chats.append(cid)
                db["chats"] = active_chats
                save_data(db)
                send_message(peer_id, f"📊 Проверка завершена. Актуальных чатов: {len(active_chats)}", get_admin_keyboard(db["is_active"]))
                return "ok"
            elif text == "✏️ Изменить текст пиара":
                admin_states[from_id] = "edit_piar"
                send_message(peer_id, "✍️ Отправь новый текст для пиара/прайса (или напиши 'Отмена'):")
                return "ok"
            elif text == "📢 Сделать рассылку в ЛС":
                admin_states[from_id] = "broadcast"
                send_message(peer_id, "📣 Напиши текст для рассылки всем пользователям в ЛС:")
                return "ok"
            elif text == "🛒 Посмотреть как клиент":
                send_message(peer_id, db["piar_text"], get_user_keyboard())
                return "ok"

        # Обычные пользователи в ЛС
        if peer_id > 0:
            if text_lower in ["🛒 прайс-лист", "начать", "старт", "start"]:
                send_message(peer_id, db["piar_text"], get_user_keyboard())
            elif text_lower == "📩 связь с админом":
                send_message(peer_id, "📩 Пиши напрямую в ЛС создателям или в Telegram: @NEBULASTUDIO1", get_user_keyboard())
            else:
                send_message(peer_id, db["piar_text"], get_user_keyboard())
            return "ok"

        # Автопиар в беседах/чатах (с кулдауном 30 секунд)
        if peer_id > 2000000000 and db["is_active"]:
            current_time = time.time()
            cooldowns = db.get("cooldowns", {})
            last_time = cooldowns.get(str(peer_id), 0)

            if current_time - last_time >= 30:
                cooldowns[str(peer_id)] = current_time
                db["cooldowns"] = cooldowns
                save_data(db)

                success = send_message(peer_id, db["piar_text"])
                if not success:
                    if peer_id in db["chats"]:
                        db["chats"].remove(peer_id)
                        save_data(db)

    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "NEBULA STUDIO Bot (2 in 1 with Admin Panel) is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
