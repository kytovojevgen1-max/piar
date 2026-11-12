import os
import json
import random
import time
import threading
import requests

# ================= НАСТРОЙКИ =================
VK_TOKEN = "vk1.a.tjIJ7CqnErXpn4Vq_nzBKQBQMjb_NcJf4kiFaJZTZoEsJ4ZCz8eBu5Z8669wHETxyU6MQ_CwhnHTQfnHLMOG6kWYjzbwap1DhP98OOs8Pj2qurp0hu7u0mDR1Ub4vdGXAq-jcKbaqp9cawQ4QZ_qnSvwwIoXZn1YEcK_c7vAkwPnpW6fc6fd936xb6vF7NAt4yw76BK5X9HHnt3CS6EfxA"
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
            if err_code in [901, 902, 917, 7, 936]:  # Ошибки (бот исключен или нет доступа)
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
            [{"action": {"type": "text", "label": "📩 Вызвать администратора"}, "color": "negative"}],
            [{"action": {"type": "text", "label": "⚙️ Админ-панель"}, "color": "secondary"}]
        ]
    }

# ================= МОЩНЫЙ ФОНОВЫЙ ПОТОК АВТОПИАРА (СТРОГО КАЖДЫЕ 30 СЕК) =================
def background_autopyar():
    print("🚀 Автопиар-машина запущена: шпарит во все чаты каждые 30 секунд 24/7!")
    while True:
        time.sleep(30)  # Ровно 30 секунд пауза
        try:
            db = load_data()
            if not db.get("is_active", True):
                continue  # Если админ выключил автопиар — ждем следующего круга
            
            chats = db.get("chats", [])
            if not chats:
                continue

            active_chats = []
            for chat_id in chats:
                # Отправляем сообщение без задержек в каждый чат
                success = send_message(chat_id, db["piar_text"])
                if success:
                    active_chats.append(chat_id)
                else:
                    print(f"🗑 Бот удален из чата {chat_id}, убираем из базы.")
            
            # Чистим мертвые чаты
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

# ================= ОСНОВНОЙ ЦИКЛ БОТА =================
def main():
    print("🚀 NEBULA STUDIO Long Poll Bot запущен!")
    
    # Запускаем автопиар в фоновом режиме
    piar_thread = threading.Thread(target=background_autopyar, daemon=True)
    piar_thread.start()

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
                # Если бота добавили в новый чат — сразу фиксируем
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

                    db = load_data()
                    
                    if peer_id > 0 and peer_id not in db["users"]:
                        db["users"].append(peer_id)
                        save_data(db)

                    if peer_id > 2000000000 and peer_id not in db["chats"]:
                        db["chats"].append(peer_id)
                        save_data(db)

                    is_admin = (from_id in db["admins"]) or (from_id in MAIN_ADMINS)

                    # Состояния админа
                    if is_admin and from_id in admin_states:
                        state = admin_states.pop(from_id)
                        if text_lower == "отмена":
                            send_message(peer_id, "❌ Отменено.", get_admin_keyboard(db["is_active"]))
                            continue

                        if state == "edit_piar":
                            db["piar_text"] = text
                            save_data(db)
                            send_message(peer_id, "✅ Текст пиара успешно изменен!", get_admin_keyboard(db["is_active"]))
                            continue
                        elif state == "broadcast":
                            count = 0
                            for uid in db["users"]:
                                try:
                                    send_message(uid, text)
                                    count += 1
                                except:
                                    pass
                            send_message(peer_id, f"✅ Рассылка отправлена {count} пользователям в ЛС!", get_admin_keyboard(db["is_active"]))
                            continue

                    # Админ-панель в ЛС
                    if is_admin and peer_id > 0:
                        if text == "⚙️ Админ-панель" or text_lower in ["админ", "миню", "меню", "start", "старт"]:
                            send_message(peer_id, f"⚙️ АДМИН-ПАНЕЛЬ NEBULA STUDIO\n\n👥 Юзеров в ЛС: {len(db['users'])}\n💬 Чатов с автопиаром: {len(db['chats'])}\n⚡ Статус пиара: {'🟢 Включен' if db['is_active'] else '🔴 Выключен'}", get_admin_keyboard(db["is_active"]))
                            continue
                        elif text == "🔴 Остановить автопиар":
                            db["is_active"] = False
                            save_data(db)
                            send_message(peer_id, "🔴 Автопиар в беседах остановлен.", get_admin_keyboard(False))
                            continue
                        elif text == "🟢 Запустить автопиар":
                            db["is_active"] = True
                            save_data(db)
                            send_message(peer_id, "🟢 Автопиар в беседах запущен!", get_admin_keyboard(True))
                            continue
                        elif text == "📊 Статистика чатов":
                            send_message(peer_id, f"📊 Статистика:\n• Активных чатов в базе: {len(db['chats'])}\n• Юзеров в ЛС: {len(db['users'])}\n• Автопиар каждые 30 сек: {'Вкл' if db['is_active'] else 'Выкл'}", get_admin_keyboard(db["is_active"]))
                            continue
                        elif text == "✏️ Изменить текст пиара":
                            admin_states[from_id] = "edit_piar"
                            send_message(peer_id, "✍️ Отправь новый текст для автопиара (или напиши 'Отмена'):")
                            continue
                        elif text == "📢 Сделать рассылку в ЛС":
                            admin_states[from_id] = "broadcast"
                            send_message(peer_id, "📣 Напиши текст рассылки для личных сообщений:")
                            continue
                        elif text == "🛒 Посмотреть как клиент":
                            send_message(peer_id, db["piar_text"], get_user_keyboard())
                            continue

                    # Вызов администратора клиентом в ЛС
                    if peer_id > 0 and text_lower == "📩 вызвать администратора":
                        send_message(peer_id, "📩 Запрос отправлен администраторам! Ожидайте ответа в ЛС.", get_user_keyboard())
                        for admin_id in db["admins"]:
                            send_message(admin_id, f"🚨 **ВНИМАНИЕ! КЛИЕНТ ВЫЗЫВАЕТ АДМИНА!**\n\n👤 Пользователь: vk.com/id{peer_id}\n💬 Перейдите в сообщения сообщества, чтобы ответить ему!")
                        continue

                    # Обычные пользователи в ЛС
                    if peer_id > 0:
                        send_message(peer_id, db["piar_text"], get_user_keyboard())
                        continue

        except Exception as e:
            print(f"Ошибка в цикле: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
