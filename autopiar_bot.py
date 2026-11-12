import os
import json
import random
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

# Простой веб-сервер для Render (чтобы хостинг не усыплял бота и не ругался на порты)
@app.route("/")
def index():
    return "NEBULA STUDIO Bot is running 24/7!"

# ================= НАСТРОЙКИ =================
VK_TOKEN = "vk1.a.tjIJ7CqnErXpn4Vq_nzBKQBQMjb_NcJf4kiFaJZTZoEsJ4ZCz8eBu5Z8669wHETxyU6MQ_CwhnHTQfnHLMOG6kWYjzbwap1DhP98OOs8Pj2qurp0hu7u0mDR1Ub4vdGXAq-jcKbaqp9cawQ4QZ_qnSvwwIoXZn1YEcK_c7vAkwPnpW6fc6fd936xb6vF7NAt4yw76BK5X9HHnt3CS6EfxA"
MAIN_ADMINS = [897082738, 1108641965]

DATA_FILE = "data.json"
VK_API_URL = "https://api.vk.com/method/"
API_VERSION = "5.199"

DEFAULT_PIAR_TEXT = (
    "🚀 ИЩЕШЬ КАЧЕСТВЕННЫЕ СЛИВЫ И ГОТОВЫЕ ПРОЕКТЫ ДЛЯ CRMP MOBILE?\n\n"
    "Забудь про перекупщиков и кривые моды с багами. В NEBULA STUDIO есть всё для твоего сервера! 🔥\n\n"
    "💎 Что мы предлагаем:\n"
    "• 📱 Моды Mobile (Black Russia, Матрёшка РП)\n"
    "• 💻 ПК Моды (Radmir RP 8.4)\n"
    "• 💬 Форумы XenForo под ключ\n"
    "• 🌐 Готовые сайты и лендинги\n\n"
    "👇 Залетай, прайс и товары здесь:\n"
    "🔗 Telegram: https://t.me/NEBULASTUDIO\n"
    "📩 VK: vk.com/nebulastudio0"
)

DEFAULT_WELCOME_TEXT = (
    "🌌 Добро пожаловать в NEBULA STUDIO!\n\n"
    "Мы создаём и настраиваем проекты CRMP Mobile / PC, сайты и форумы под ключ.\n\n"
    "👇 Выбери нужный раздел в меню ниже, чтобы посмотреть прайс, узнать условия работы или вызвать администратора:"
)

DEFAULT_HELPER_TEXT = (
    "📘 КАК ПРОХОДИТ ПОКУПКА И РАБОТА (ПРАВИЛА):\n\n"
    "1️⃣ Выбор товара: ознакомься с прайсом и нажми кнопку «📩 Вызвать администратора».\n"
    "2️⃣ Оформление: напиши в чат, какой мод, форум или услугу хочешь заказать.\n"
    "3️⃣ Оплата: работаем строго по 100% предоплате. Сначала ты оплачиваешь заказ — сразу после подтверждения оплаты мы начинаем установку/выдачу.\n"
    "4️⃣ Гарантии: быстрая выдача файлов, помощь с заливкой на твой хостинг.\n\n"
    "🔗 Наш Telegram-канал с отзывами и новостями: https://t.me/NEBULASTUDIO\n"
    "📩 Группа ВК: vk.com/nebulastudio0"
)

# ================= БАЗА ДАННЫХ =================
def load_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "piar_text": DEFAULT_PIAR_TEXT,
            "welcome_text": DEFAULT_WELCOME_TEXT,
            "helper_text": DEFAULT_HELPER_TEXT,
            "is_active": True,
            "admins": list(MAIN_ADMINS),
            "users": [],
            "chats": []
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
        if "welcome_text" not in data:
            data["welcome_text"] = DEFAULT_WELCOME_TEXT
        if "helper_text" not in data:
            data["helper_text"] = DEFAULT_HELPER_TEXT
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
    
    try:
        response = requests.post(VK_API_URL + "messages.send", data=params, timeout=10).json()
        if "error" in response:
            err_code = response["error"].get("error_code")
            if err_code in [901, 902, 917, 7, 936]:
                return False
    except:
        pass
    return True

# ================= КЛАВИАТУРЫ =================
def get_admin_keyboard(is_active):
    status_text = "🔴 Остановить автопиар" if is_active else "🟢 Запустить автопиар"
    return {
        "one_time": False,
        "buttons": [
            [{"action": {"type": "text", "label": status_text}, "color": "negative" if is_active else "positive"}],
            [
                {"action": {"type": "text", "label": "✏️ Текст автопиара"}, "color": "primary"},
                {"action": {"type": "text", "label": "✏️ Автоответ в ЛС"}, "color": "primary"}
            ],
            [
                {"action": {"type": "text", "label": "✏️ Текст хелпера"}, "color": "primary"},
                {"action": {"type": "text", "label": "📊 Статистика"}, "color": "secondary"}
            ],
            [{"action": {"type": "text", "label": "📢 Рассылка в ЛС"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "🛒 Меню покупателя"}, "color": "positive"}]
        ]
    }

def get_user_keyboard(is_admin=False):
    buttons = [
        [{"action": {"type": "text", "label": "🛒 Прайс-лист / Товары"}, "color": "primary"}],
        [{"action": {"type": "text", "label": "❓ Как купить / Правила"}, "color": "secondary"}],
        [{"action": {"type": "text", "label": "📩 Вызвать администратора"}, "color": "negative"}]
    ]
    if is_admin:
        buttons.append([{"action": {"type": "text", "label": "⚙️ Админ-панель"}, "color": "secondary"}])
    return {"one_time": False, "buttons": buttons}

# ================= ФОНОВЫЙ ПОТОК АВТОПИАРА (24/7 КАЖДЫЕ 30 СЕК) =================
def background_autopyar():
    print("🚀 Автопиар запущен: рассылка во все чаты каждые 30 секунд без пауз!")
    while True:
        time.sleep(30)
        try:
            db = load_data()
            if not db.get("is_active", True):
                continue
            
            chats = db.get("chats", [])
            if not chats:
                continue

            active_chats = []
            for chat_id in chats:
                success = send_message(chat_id, db["piar_text"])
                if success:
                    active_chats.append(chat_id)
                else:
                    print(f"🗑 Чат {chat_id} удален (бота исключили).")
                time.sleep(0.2)  # Плавная отправка по чатам без банов
            
            if len(active_chats) != len(chats):
                db["chats"] = active_chats
                save_data(db)

        except Exception as e:
            print(f"❌ Ошибка в автопиаре: {e}")

# ================= ПОЛУЧЕНИЕ LONG POLL СЕРВЕРА =================
def get_long_poll_server():
    res = requests.post(VK_API_URL + "groups.getLongPollServer", data={
        "access_token": VK_TOKEN,
        "v": API_VERSION,
        "group_id": 243227412
    }).json()
    return res.get("response")

# ================= ОСНОВНОЙ ЦИКЛ LONG POLL =================
def run_bot():
    print("🚀 Long Poll поток запущен!")
    server_data = get_long_poll_server()
    if not server_data:
        print("❌ Ошибка получения Long Poll сервера! Проверь токен.")
        return

    server = server_data["server"]
    key = server_data["key"]
    ts = server_data["ts"]

    while True:
        try:
            response = requests.get(f"{server}?act=a_check&key={key}&ts={ts}&wait=25", timeout=30).json()
            
            if "failed" in response:
                server_data = get_long_poll_server()
                if server_data:
                    server = server_data["server"]
                    key = server_data["key"]
                    ts = server_data["ts"]
                continue

            ts = response["updates_ts"] if "updates_ts" in response else response.get("ts", ts)

            for event in response.get("updates", []):
                # Если бота добавили в новый чат
                if event.get("type") == "chat_invite_user":
                    db = load_data()
                    peer_id = event["object"].get("peer_id")
                    if peer_id and peer_id not in db["chats"]:
                        db["chats"].append(peer_id)
                        save_data(db)
                    continue

                if event.get("type") == "message_new":
                    msg = event["object"]["message"]
                    from_id = msg["from_id"]
                    peer_id = msg["peer_id"]
                    text = msg.get("text", "").strip()
                    text_lower = text.lower()

                    if from_id < 0:
                        continue

                    db = load_data()

                    # ================= ЖЁСТКИЙ ФИЛЬТР БЕСЕД =================
                    # Если сообщение из беседы (peer_id > 20000
