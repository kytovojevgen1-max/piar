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

# ================= РАБОТА С БАЗОЙ ДАННЫХ (JSON) =================
def load_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "welcome_text": "🌌 Добро пожаловать в NEBULA STUDIO!\n\nМы создаём и настраиваем проекты CRMP Mobile / PC, сайты и форумы под ключ.\n\nВыбери нужный раздел в меню ниже 👇",
            "price_mobile": "📱 МОБИЛЬНЫЕ МОДЫ (CRMP):\n• Black Russia 2025–26 (планшет): 110 ⭐ | 80 ₽ (без PWN) / 120 ₽ (с PWN)\n• Black Russia 2025 (без планшета): 95 ⭐ | 50 ₽ (без PWN) / 75 ₽ (с PWN)\n• Black Russia 2025 (без планшета, работы фулл): 85 ⭐ | 65 ₽ (без PWN) / 100 ₽ (с PWN)\n• Матрёшка РП: 100 ⭐ | 80 ₽ (AMX) / 120 ₽ (PWN)",
            "price_pc": "💻 ПК МОДЫ:\n• Radmir RP 8.4: 85 ⭐ | 70 ₽ (без PWN) / 120 ₽ (с PWN)",
            "price_web": "💬 ФОРУМЫ И САЙТЫ:\n• Любой форум (XenForo): 40 ⭐ | 30 ₽\n• Любой сайт / лендинг: 40 ⭐ | 29 ₽",
            "price_services": "🛠 УСЛУГИ:\n• Установка вашего стиля на форум: 40 ⭐ | 30 ₽\n• Заливка мода на сервер: 40 ⭐ | 30 ₽\n• Создание/подключение лаунчера: 40 ⭐ | 30 ₽",
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
def send_message(user_id, text, keyboard=None):
    params = {
        "user_id": user_id,
        "message": text,
        "random_id": random.randint(1, 2147483647),
        "access_token": VK_TOKEN,
        "v": API_VERSION
    }
    if keyboard:
        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
    requests.post(VK_API_URL + "messages.send", data=params)

# ================= КЛАВИАТУРЫ (КНОПКИ) =================
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

def get_price_keyboard():
    return {
        "one_time": False,
        "buttons": [
            [
                {"action": {"type": "text", "label": "📱 Моды Mobile"}, "color": "primary"},
                {"action": {"type": "text", "label": "💻 Моды ПК"}, "color": "primary"}
            ],
            [
                {"action": {"type": "text", "label": "🌐 Сайты и Форумы"}, "color": "primary"},
                {"action": {"type": "text", "label": "🛠 Услуги"}, "color": "primary"}
            ],
            [{"action": {"type": "text", "label": "🔙 В главное меню"}, "color": "secondary"}]
        ]
    }

def get_admin_keyboard():
    return {
        "one_time": False,
        "buttons": [
            [{"action": {"type": "text", "label": "✏️ Изменить приветствие (Старт)"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "💰 Изменить прайс"}, "color": "primary"}],
            [
                {"action": {"type": "text", "label": "➕ Выдать админку"}, "color": "positive"},
                {"action": {"type": "text", "label": "➖ Снять админку"}, "color": "negative"}
            ],
            [
                {"action": {"type": "text", "label": "📢 Рассылка всем"}, "color": "primary"},
                {"action": {"type": "text", "label": "📊 Статистика"}, "color": "secondary"}
            ],
            [{"action": {"type": "text", "label": "🔙 В главное меню"}, "color": "secondary"}]
        ]
    }

# ================= ОБРАБОТКА ВХОДЯЩИХ СООБЩЕНИЙ =================
@app.route("/", methods=["POST"])
def vk_callback():
    data = request.json
    if not data:
        return "ok"

    # Подтверждение сервера ВК
    if data.get("type") == "confirmation":
        return CONFIRMATION_TOKEN

    # Новое сообщение
    if data.get("type") == "message_new":
        msg = data["object"]["message"]
        user_id = msg["from_id"]
        text = msg.get("text", "").strip()
        text_lower = text.lower()

        db = load_data()
        
        if user_id not in db["users"] and user_id > 0:
            db["users"].append(user_id)
            save_data(db)

        is_admin = (user_id in db["admins"]) or (user_id in MAIN_ADMINS)

        # --- ПРОВЕРКА СОСТОЯНИЙ АДМИНА ---
        if is_admin and user_id in admin_states:
            state = admin_states.pop(user_id)
            
            if text_lower == "отмена":
                send_message(user_id, "❌ Действие отменено.", get_admin_keyboard())
                return "ok"

            if state == "edit_welcome":
                db["welcome_text"] = text
                save_data(db)
                send_message(user_id, "✅ Приветственное сообщение успешно обновлено!", get_admin_keyboard())
                return "ok"

            elif state == "add_admin":
                if text.isdigit():
                    new_admin = int(text)
                    if new_admin not in db["admins"]:
                        db["admins"].append(new_admin)
                        save_data(db)
                        send_message(user_id, f"✅ Пользователю ID {new_admin} выдан доступ к админ-панели!", get_admin_keyboard())
                    else:
                        send_message(user_id, "⚠️ Этот пользователь уже админ.", get_admin_keyboard())
                else:
                    send_message(user_id, "❌ Ошибка! Введите только цифровой ID.", get_admin_keyboard())
                return "ok"

            elif state == "del_admin":
                if text.isdigit():
                    rem_admin = int(text)
                    if rem_admin in MAIN_ADMINS:
                        send_message(user_id, "⛔ Нельзя снять главного владельца!", get_admin_keyboard())
                    elif rem_admin in db["admins"]:
                        db["admins"].remove(rem_admin)
                        save_data(db)
                        send_message(user_id, f"✅ Админка у ID {rem_admin} забрана.", get_admin_keyboard())
                    else:
                        send_message(user_id, "⚠️ Такого ID нет в списке админов.", get_admin_keyboard())
                else:
                    send_message(user_id, "❌ Ошибка! Введите цифровой ID.", get_admin_keyboard())
                return "ok"

            elif state == "broadcast":
                count = 0
                for uid in db["users"]:
                    try:
                        send_message(uid, f"📢 НОВОСТИ NEBULA STUDIO:\n\n{text}")
                        count += 1
                    except:
                        pass
                send_message(user_id, f"✅ Рассылка завершена! Получили: {count} чел.", get_admin_keyboard())
                return "ok"

            elif state.startswith("edit_price_"):
                key = state.replace("edit_", "")
                db[key] = text
                save_data(db)
                send_message(user_id, "✅ Раздел прайса обновлён!", get_admin_keyboard())
                return "ok"

        # --- ОБЫЧНЫЕ КОМАНДЫ ---
        if text_lower in ["начать", "старт", "start", "меню", "🔙 в главное меню"]:
            send_message(user_id, db["welcome_text"], get_main_keyboard(is_admin))

        elif text == "🛒 Прайс-лист":
            send_message(user_id, "Выберите категорию:", get_price_keyboard())

        elif text == "📱 Моды Mobile":
            send_message(user_id, db["price_mobile"], get_price_keyboard())

        elif text == "💻 Моды ПК":
            send_message(user_id, db["price_pc"], get_price_keyboard())

        elif text == "🌐 Сайты и Форумы":
            send_message(user_id, db["price_web"], get_price_keyboard())

        elif text == "🛠 Услуги":
            send_message(user_id, db["price_services"], get_price_keyboard())

        elif text == "🔥 Акция / Скидка":
            send_message(user_id, "🔥 ГОРЯЧЕЕ ПРЕДЛОЖЕНИЕ!\n\nПервому покупателю скидка на любой товар!\nЖми «📩 Купить / Связь с админом».", get_main_keyboard(is_admin))

        elif text == "❓ FAQ / Инфо":
            faq = (
                "⚠️ ВАЖНАЯ ИНФОРМАЦИЯ:\n\n"
                "1️⃣ Хостинг: установка только на ваш хостинг.\n"
                "2️⃣ Оплата: рубли напрямую или Telegram Stars.\n"
                "3️⃣ Гарантии: быстрая выдача и помощь."
            )
            send_message(user_id, faq, get_main_keyboard(is_admin))

        elif text == "📩 Купить / Связь с админом":
            send_message(user_id, "📩 Напишите сюда, что хотите купить и есть ли хостинг. Админы уже получили уведомление!\nТГ: @NEBULASTUDIO1", get_main_keyboard(is_admin))
            for adm in db["admins"]:
                send_message(adm, f"🔔 НОВЫЙ ЗАКАЗ!\nПользователь: vk.com/id{user_id}")

        # --- АДМИН-ПАНЕЛЬ ---
        elif is_admin and text == "⚙️ Админ-панель":
            admins_list = ", ".join([str(a) for a in db["admins"]])
            send_message(user_id, f"⚙️ АДМИН-ПАНЕЛЬ NEBULA STUDIO\n\n👥 База юзеров: {len(db['users'])}\n👑 Админы: {admins_list}", get_admin_keyboard())

        elif is_admin and text == "✏️ Изменить приветствие (Старт)":
            admin_states[user_id] = "edit_welcome"
            send_message(user_id, "✍️ Отправьте новый текст для команды «Начать»:\n(Для отмены: Отмена)")

        elif is_admin and text == "➕ Выдать админку":
            admin_states[user_id] = "add_admin"
            send_message(user_id, "👑 Введите цифровой VK ID нового админа:\n(Для отмены: Отмена)")

        elif is_admin and text == "➖ Снять админку":
            admin_states[user_id] = "del_admin"
            send_message(user_id, "🗑 Введите цифровой VK ID для удаления из админов:\n(Для отмены: Отмена)")

        elif is_admin and text == "📢 Рассылка всем":
            admin_states[user_id] = "broadcast"
            send_message(user_id, "📣 Введите текст рассылки для всех пользователей:\n(Для отмены: Отмена)")

        elif is_admin and text == "📊 Статистика":
            send_message(user_id, f"📊 Статистика:\n• Пользователей: {len(db['users'])}\n• Админов: {len(db['admins'])}", get_admin_keyboard())

        elif is_admin and text == "💰 Изменить прайс":
            kb = {
                "one_time": True,
                "buttons": [
                    [{"action": {"type": "text", "label": "/edit_mobile"}, "color": "primary"}, {"action": {"type": "text", "label": "/edit_pc"}, "color": "primary"}],
                    [{"action": {"type": "text", "label": "/edit_web"}, "color": "primary"}, {"action": {"type": "text", "label": "/edit_services"}, "color": "primary"}],
                    [{"action": {"type": "text", "label": "⚙️ Админ-панель"}, "color": "secondary"}]
                ]
            }
            send_message(user_id, "Выберите раздел для изменения:", kb)

        elif is_admin and text in ["/edit_mobile", "/edit_pc", "/edit_web", "/edit_services"]:
            section = text.replace("/edit_", "price_")
            admin_states[user_id] = f"edit_{section}"
            send_message(user_id, f"✍️ Введите новый текст для прайса ({section}):\n(Для отмены: Отмена)")

    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "NEBULA STUDIO VK Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
