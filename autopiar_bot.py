import os
import json
import time
import asyncio
from flask import Flask
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text

# =====================================================================
# 1. ВЕБ-СЕРВЕР ДЛЯ РАБОТЫ 24/7 (RENDER)
# =====================================================================
app = Flask(__name__)
START_TIME = time.time()

@app.route('/')
def home():
    uptime_sec = int(time.time() - START_TIME)
    hours, remainder = divmod(uptime_sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"AutoPiar Server: ONLINE | Uptime: {hours}h {minutes}m {seconds}s"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

from threading import Thread
Thread(target=run_flask, daemon=True).start()


# =====================================================================
# 2. КОНФИГУРАЦИЯ И БАЗА ДАННЫХ
# =====================================================================
CONFIG_FILE = "autopiar_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "token": "vk1.a.q9RtV2818QWiCSFGgHLzR4gQr2xQ2fSIQKFbsrcoEudGaNSukxF_w-BSKNVvpWJhE6hON3wI9NBU5i96-0GVe0LTJ3so3jVMTfM6gQSZyWHkMO0187j0xC3ymyobpNhdxOUEAq5XsVnAdij_c9plT0lBdW-qD9cWxVw-Cp5ip7pCSkXvWBmAeJZ13rY2llgn3IczHjaPXOadwgLarLb96Q",
        "main_owner": 897082738,
        "admins": [897082738],
        "chats": [],
        "piar_text": "📢 Привет! Это ультимативный автопиар-бот.\n🌐 Максимальный охват бесед!",
        "piar_attachment": "", 
        "autoresponder": "🤖 Здравствуйте! Сообщение получено. Администратор ответит вам в ближайшее время.",
        "piar_active": False
    }

def save_config(data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения конфига: {e}")

config = load_config()
bot = Bot(token=config["token"])
user_states = {}


# =====================================================================
# 3. АВТОСБОР И ФОНОВЫЙ ЦИКЛ РАССЫЛКИ (15 СЕКУНД)
# =====================================================================
async def auto_fetch_chats():
    try:
        response = await bot.api.request(
            "messages.getConversations", 
            {"count": 200, "filter": "chat"}
        )
        cfg = load_config()
        current_chats = set(cfg.get("chats", []))
        added = 0
        
        for item in response.get("items", []):
            peer_id = item.get("conversation", {}).get("peer", {}).get("id")
            if peer_id and peer_id > 2000000000:
                if peer_id not in current_chats:
                    current_chats.add(peer_id)
                    added += 1
        
        if added > 0 or len(current_chats) != len(cfg.get("chats", [])):
            cfg["chats"] = list(current_chats)
            save_config(cfg)
            print(f"📥 [AUTO-SYNC] Автоматически найдено бесед: {len(cfg['chats'])} (новых: {added})")
    except Exception as e:
        print(f"⚠️ Ошибка автосбора чатов: {e}")

async def send_to_chat(peer_id, text, attachment):
    try:
        await bot.api.messages.send(
            peer_id=int(peer_id),
            message=text if text else None,
            attachment=attachment if attachment else None,
            random_id=0
        )
        print(f"🔥 [PIAR] Отправлено в чат {peer_id}")
    except Exception as e:
        print(f"⚠️ [PIAR] Ошибка отправки в чат {peer_id}: {e}")

async def background_piar_loop():
    print("🚀 [LOOP] Цикл автопиара запущен (интервал 15 секунд).")
    await asyncio.sleep(5)
    while True:
        await asyncio.sleep(15)
        try:
            # Перед каждым кругом сканируем новые беседы
            await auto_fetch_chats()
            
            cfg = load_config()
            if cfg.get("piar_active", False) and cfg.get("chats"):
                text = cfg.get("piar_text", "")
                attachment = cfg.get("piar_attachment", "")
                chats = cfg["chats"]
                
                print(f"🚀 [PIAR] Старт рассылки по {len(chats)} чатам...")
                for peer_id in chats:
                    await send_to_chat(peer_id, text, attachment)
                    await asyncio.sleep(0.1)
                print("✅ [PIAR] Раунд завершен.")
        except Exception as e:
            print(f"❌ Ошибка в фоновом цикле пиара: {e}")


# =====================================================================
# 4. КЛАВИАТУРА И МЕНЕДЖЕР УПРАВЛЕНИЯ
# =====================================================================
def get_main_keyboard(uid):
    cfg = load_config()
    is_main = (uid == cfg["main_owner"])
    is_admin = (is_main or uid in cfg["admins"])
    
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("📊 Статус бота"), color=KeyboardButtonColor.PRIMARY)
    kb.add(Text("📋 Список чатов"), color=KeyboardButtonColor.PRIMARY)
    
    if is_admin:
        kb.row()
        kb.add(Text("⚙️ Настроить текст"), color=KeyboardButtonColor.PRIMARY)
        kb.add(Text("📎 Задать вложение"), color=KeyboardButtonColor.PRIMARY)
        kb.row()
        status_btn = "🔴 Выключить пиар" if cfg.get("piar_active") else "🟢 Включить пиар"
        kb.add(Text(status_btn), color=KeyboardButtonColor.NEGATIVE if cfg.get("piar_active") else KeyboardButtonColor.POSITIVE)
        kb.add(Text("🗑 Очистить текст"), color=KeyboardButtonColor.SECONDARY)
        kb.row()
        kb.add(Text("🔄 Обновить чаты"), color=KeyboardButtonColor.POSITIVE)
        kb.add(Text("🛑 Очистить чаты"), color=KeyboardButtonColor.NEGATIVE)
        
    if is_main:
        kb.row()
        kb.add(Text("➕ Добавить админа"), color=KeyboardButtonColor.PRIMARY)
        kb.add(Text("❌ Снять с админки"), color=KeyboardButtonColor.NEGATIVE)
        
    return kb.get_json()

@bot.on.private_message()
async def private_handler(message: Message):
    uid = message.from_id
    text = message.text
    if not text:
        return

    text_clean = text.strip()
    text_lower = text_clean.lower()
    cfg = load_config()
    
    is_main = (uid == cfg["main_owner"])
    is_admin = (is_main or uid in cfg["admins"])

    if text_lower in ["/start", "начать", "меню", "главное меню", "❌ отмена"]:
        if uid in user_states:
            del user_states[uid]
        return await message.answer(
            "👑 **УЛЬТИМАТИВНЫЙ АВТОПИАР (15 СЕК)** 👑\n\n"
            "Бот работает полностью автоматически:",
            keyboard=get_main_keyboard(uid)
        )

    state = user_states.get(uid)
    if state and is_admin:
        if state == "wait_piar_text":
            del user_states[uid]
            cfg["piar_text"] = text_clean
            save_config(cfg)
            return await message.answer("✅ Текст успешно изменен!", keyboard=get_main_keyboard(uid))
        elif state == "wait_piar_att":
            del user_states[uid]
            cfg["piar_attachment"] = "" if text_lower in ["нет", "0", "отмена"] else text_clean
            save_config(cfg)
            return await message.answer("✅ Вложение обновлено!", keyboard=get_main_keyboard(uid))
        elif state == "wait_autoresponder":
            del user_states[uid]
            cfg["autoresponder"] = text_clean
            save_config(cfg)
            return await message.answer("✅ Автоответчик изменен!", keyboard=get_main_keyboard(uid))
        elif state == "wait_new_admin" and is_main:
            del user_states[uid]
            clean_id = text_clean.replace("id", "").strip()
            if clean_id.isdigit():
                tid = int(clean_id)
                if tid not in cfg["admins"]:
                    cfg["admins"].append(tid)
                    save_config(cfg)
                    return await message.answer(f"✅ Администратор [id{tid}|ID {tid}] добавлен.", keyboard=get_main_keyboard(uid))
            return await message.answer("❌ Неверный VK ID.", keyboard=get_main_keyboard(uid))
        elif state == "wait_remove_admin" and is_main:
            del user_states[uid]
            clean_id = text_clean.replace("id", "").strip()
            if clean_id.isdigit():
                tid = int(clean_id)
                if tid == cfg["main_owner"]:
                    return await message.answer("❌ Нельзя снять владельца!", keyboard=get_main_keyboard(uid))
                if tid in cfg["admins"]:
                    cfg["admins"].remove(tid)
                    save_config(cfg)
                    return await message.answer(f"✅ Администратор [id{tid}|ID {tid}] снят.", keyboard=get_main_keyboard(uid))
                return await message.answer("❌ Не найден в админах.", keyboard=get_main_keyboard(uid))
            return await message.answer("❌ Неверный VK ID.", keyboard=get_main_keyboard(uid))

    if text_clean == "📊 Статус бота":
        uptime_sec = int(time.time() - START_TIME)
        hours, remainder = divmod(uptime_sec, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        status_piar = "АКТИВЕН 🟢" if cfg.get("piar_active") else "ОСТАНОВЛЕН 🔴"
        chats_count = len(cfg.get("chats", []))
        piar_text = cfg.get("piar_text", "") or "Не задан"
        piar_att = cfg.get("piar_attachment", "") or "Нет"
        
        return await message.answer(
            f"📊 **СТАТУС:**\n\n"
            f"• Пиар: {status_piar} (каждые 15 сек)\n"
            f"• Чатов в базе: `{chats_count}`\n"
            f"• Аптайм: `{hours}ч {minutes}м`\n"
            f"• Медиа: `{piar_att}`\n\n"
            f"💬 **Текст:**\n{piar_text}",
            keyboard=get_main_keyboard(uid)
        )

    if text_clean == "📋 Список чатов":
        chats = cfg.get("chats", [])
        return await message.answer(f"📋 **Чаты в базе ({len(chats)}):**\n`{chats}`", keyboard=get_main_keyboard(uid))

    if text_clean == "🔄 Обновить чаты":
        await auto_fetch_chats()
        cfg = load_config()
        return await message.answer(f"🔄 Чаты обновлены! Найдено бесед: `{len(cfg.get('chats', []))}`", keyboard=get_main_keyboard(uid))

    if is_admin:
        if text_clean in ["🟢 Включить пиар", "🔴 Выключить пиар"]:
            cfg["piar_active"] = not cfg.get("piar_active", False)
            save_config(cfg)
            state_str = "АКТИВЕН 🟢" if cfg["piar_active"] else "ОСТАНОВЛЕН 🔴"
            return await message.answer(f"⚙️ Пиар теперь: {state_str}", keyboard=get_main_keyboard(uid))
        
        if text_clean == "⚙️ Настроить текст":
            user_states[uid] = "wait_piar_text"
            return await message.answer("✍️ Отправьте новый текст:", keyboard=Keyboard(one_time=False, inline=True).add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE).get_json())
        
        if text_clean == "📎 Задать вложение":
            user_states[uid] = "wait_piar_att"
            return await message.answer("✍️ Отправьте вложение (например `photo123_456`):", keyboard=Keyboard(one_time=False, inline=True).add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE).get_json())
        
        if text_clean == "🗑 Очистить текст":
            cfg["piar_text"] = ""
            save_config(cfg)
            return await message.answer("🗑 Текст очищен.", keyboard=get_main_keyboard(uid))
        
        if text_clean == "🛑 Очистить чаты":
            cfg["chats"] = []
            save_config(cfg)
            return await message.answer("🛑 Список чатов очищен.", keyboard=get_main_keyboard(uid))
        
        if text_clean == "🤖 Автоответчик":
            user_states[uid] = "wait_autoresponder"
            return await message.answer("✍️ Отправьте текст автоответчика:", keyboard=Keyboard(one_time=False, inline=True).add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE).get_json())

    if is_main:
        if text_clean == "➕ Добавить админа":
            user_states[uid] = "wait_new_admin"
            return await message.answer("✍️ Введите ID админа:", keyboard=Keyboard(one_time=False, inline=True).add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE).get_json())
        
        if text_clean == "❌ Снять с админки":
            user_states[uid] = "wait_remove_admin"
            return await message.answer("✍️ Введите ID для снятия:", keyboard=Keyboard(one_time=False, inline=True).add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE).get_json())

    if not is_admin:
        resp = cfg.get("autoresponder", "Здравствуйте!")
        return await message.answer(resp)
    
    await message.answer("❌ Используйте кнопки меню.", keyboard=get_main_keyboard(uid))

# Автосохранение чатов при любых сообщениях
@bot.on.chat_message()
async def chat_handler(message: Message):
    peer_id = message.peer_id
    cfg = load_config()
    if peer_id not in cfg["chats"]:
        cfg["chats"].append(peer_id)
        save_config(cfg)
        print(f"📥 Автоматически пойман и добавлен чат: {peer_id}")


if __name__ == "__main__":
    print("🚀 Запуск автономного автопиара...")
    loop = asyncio.get_event_loop()
    loop.create_task(background_piar_loop())
    bot.run_forever()
