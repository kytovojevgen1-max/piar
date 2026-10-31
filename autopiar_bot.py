import os
import json
import time
import asyncio
from threading import Thread
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
    return f"Highload AutoPiar Server: ONLINE 24/7 | Uptime: {hours}h {minutes}m {seconds}s"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

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
        "piar_active": True
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
# 3. УЛЬТРА-СБОР ЧАТОВ ЧЕРЕЗ API И ПОТОК РАССЫЛКИ (15 СЕК)
# =====================================================================
async def auto_fetch_chats():
    try:
        # Запрашиваем именно беседы через прямой API-метод
        response = await bot.api.request(
            "messages.getConversations", 
            {"count": 200, "filter": "chat"}
        )
        
        cfg = load_config()
        current_chats = set(cfg.get("chats", []))
        added_count = 0
        
        items = response.get("items", [])
        for item in items:
            peer = item.get("conversation", {}).get("peer", {})
            peer_id = peer.get("id")
            if peer_id and peer_id > 2000000000:
                if peer_id not in current_chats:
                    current_chats.add(peer_id)
                    added_count += 1
        
        if added_count > 0 or len(current_chats) != len(cfg.get("chats", [])):
            cfg["chats"] = list(current_chats)
            save_config(cfg)
            print(f"📥 [AUTO-SYNC] Найдено бесед: {len(cfg['chats'])} (новых: {added_count})")
    except Exception as e:
        print(f"⚠️ Ошибка автосбора чатов через API: {e}")

async def send_to_chat(peer_id, text, attachment):
    try:
        await bot.api.messages.send(
            peer_id=int(peer_id),
            message=text if text else None,
            attachment=attachment if attachment else None,
            random_id=0
        )
        print(f"🔥 [UPPER-PIAR] Успешно отправлено в чат {peer_id}")
    except Exception as e:
        print(f"⚠️ [UPPER-PIAR] Ошибка отправки в чат {peer_id}: {e}")

async def run_mailing():
    await auto_fetch_chats()
    
    cfg = load_config()
    active = cfg.get("piar_active", False)
    chats = cfg.get("chats", [])
    
    print(f"🔄 [ПРОВЕРКА] Пиар активен: {active} | Бесед в базе: {chats}")
    
    if active and chats:
        text = cfg.get("piar_text", "")
        attachment = cfg.get("piar_attachment", "")
        
        print(f"🚀 [UPPER-PIAR] Рассылка полетела по беседам: {chats}")
        for peer_id in chats:
            await send_to_chat(peer_id, text, attachment)
            await asyncio.sleep(0.2)
        print("✅ [UPPER-PIAR] Раунд успешно завершен. Ждем 15 секунд...")
    else:
        print("⚠️ [UPPER-PIAR] Рассылка пропущена: пиар выключен или список бесед пуст!")

async def piar_loop():
    print("🚀 [LOOP] Фоновый поток запущен. Интервал: 15 секунд.")
    while True:
        await asyncio.sleep(15)
        try:
            await run_mailing()
        except Exception as e:
            print(f"❌ Ошибка в потоке пиара: {e}")

def run_piar_thread():
    asyncio.run(piar_loop())

Thread(target=run_piar_thread, daemon=True).start()


# =====================================================================
# 4. ПАНЕЛЬ УПРАВЛЕНИЯ В ЛИЧНЫХ СООБЩЕНИЯХ
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
            "Система работает полностью на максималках:",
            keyboard=get_main_keyboard(uid)
        )

    state = user_states.get(uid)
    if state and is_admin:
        if state == "wait_piar_text":
            del user_states[uid]
            cfg["piar_text"] = text_clean
            save_config(cfg)
            return await message.answer("✅ Текст автопиара успешно изменен!", keyboard=get_main_keyboard(uid))
        elif state == "wait_piar_att":
            del user_states[uid]
            cfg["piar_attachment"] = "" if text_lower in ["нет", "0", "отмена"] else text_clean
            save_config(cfg)
            return await message.answer("✅ Вложение успешно обновлено!", keyboard=get_main_keyboard(uid))
        elif state == "wait_autoresponder":
            del user_states[uid]
            cfg["autoresponder"] = text_clean
            save_config(cfg)
            return await message.answer("✅ Текст автоответчика изменен!", keyboard=get_main_keyboard(uid))
        elif state == "wait_new_admin" and is_main:
            del user_states[uid]
            clean_id = text_clean.replace("id", "").strip()
            if clean_id.isdigit():
                tid = int(clean_id)
                if tid not in cfg["admins"]:
                    cfg["admins"].append(tid)
                    save_config(cfg)
                    return await message.answer(f"✅ Пользователь [id{tid}|ID {tid}] назначен админом.", keyboard=get_main_keyboard(uid))
            return await message.answer("❌ Неверный VK ID.", keyboard=get_main_keyboard(uid))
        elif state == "wait_remove_admin" and is_main:
            del user_states[uid]
            clean_id = text_clean.replace("id", "").strip()
            if clean_id.isdigit():
                tid = int(clean_id)
                if tid == cfg["main_owner"]:
                    return await message.answer("❌ Нельзя снять главного владельца!", keyboard=get_main_keyboard(uid))
                if tid in cfg["admins"]:
                    cfg["admins"].remove(tid)
                    save_config(cfg)
                    return await message.answer(f"✅ Пользователь [id{tid}|ID {tid}] снят с админки.", keyboard=get_main_keyboard(uid))
                return await message.answer("❌ Пользователь не найден в админах.", keyboard=get_main_keyboard(uid))
            return await message.answer("❌ Неверный VK ID.", keyboard=get_main_keyboard(uid))

    if text_clean == "📊 Статус бота":
        uptime_sec = int(time.time() - START_TIME)
        hours, remainder = divmod(uptime_sec, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        status_piar = "АКТИВЕН 🟢" if cfg.get("piar_active") else "ОСТАНОВЛЕН 🔴"
        chats_count = len(cfg.get("chats", []))
        piar_text = cfg.get("piar_text", "") or "Не задан (пусто)"
        piar_att = cfg.get("piar_attachment", "") or "Отсутствует"
        
        return await message.answer(
            f"📊 **СТАТУС СИСТЕМЫ:**\n\n"
            f"• Пиар: {status_piar} (каждые 15 сек 🚀)\n"
            f"• Чатов в базе: `{chats_count}`\n"
            f"• Аптайм: `{hours}ч {minutes}м {seconds}с`\n"
            f"• Медиа: `{piar_att}`\n\n"
            f"💬 **Текст рассылки:**\n{piar_text}",
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
            
            if cfg["piar_active"]:
                asyncio.run_coroutine_threadsafe(run_mailing(), asyncio.get_event_loop())
                
            return await message.answer(f"⚙️ Автопиар теперь: {state_str}", keyboard=get_main_keyboard(uid))
        
        if text_clean == "⚙️ Настроить текст":
            user_states[uid] = "wait_piar_text"
            return await message.answer("✍️ Отправьте новый текст для рассылки:", keyboard=Keyboard(one_time=False, inline=True).add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE).get_json())
        
        if text_clean == "📎 Задать вложение":
            user_states[uid] = "wait_piar_att"
            return await message.answer("✍️ Отправьте код вложения (например `photo123_456`), либо `нет`:", keyboard=Keyboard(one_time=False, inline=True).add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE).get_json())
        
        if text_clean == "🗑 Очистить текст":
            cfg["piar_text"] = ""
            save_config(cfg)
            return await message.answer("🗑 Текст пиара полностью очищен.", keyboard=get_main_keyboard(uid))
        
        if text_clean == "🛑 Очистить чаты":
            cfg["chats"] = []
            save_config(cfg)
            return await message.answer("🛑 Список чатов очищен.", keyboard=get_main_keyboard(uid))
        
        if text_clean == "🤖 Автоответчик":
            user_states[uid] = "wait_autoresponder"
            return await message.answer(f"✍️ Текущий автоответчик:\n`{cfg.get('autoresponder')}`\n\nОтправьте новый текст:", keyboard=Keyboard(one_time=False, inline=True).add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE).get_json())

    if is_main:
        if text_clean == "➕ Добавить админа":
            user_states[uid] = "wait_new_admin"
            return await message.answer("✍️ Введите цифровой VK ID нового администратора:", keyboard=Keyboard(one_time=False, inline=True).add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE).get_json())
        
        if text_clean == "❌ Снять с админки":
            user_states[uid] = "wait_remove_admin"
            return await message.answer("✍️ Введите VK ID администратора для снятия:", keyboard=Keyboard(one_time=False, inline=True).add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE).get_json())

    if not is_admin:
        resp = cfg.get("autoresponder", "Здравствуйте! Сообщение получено.")
        return await message.answer(resp)
    
    await message.answer("❌ Используйте кнопки меню.", keyboard=get_main_keyboard(uid))


# =====================================================================
# 5. РАБОТА В БЕСЕДАХ
# =====================================================================

@bot.on.chat_message()
async def chat_handler(message: Message):
    peer_id = message.peer_id
    cfg = load_config()
    
    if peer_id not in cfg["chats"]:
        cfg["chats"].append(peer_id)
        save_config(cfg)

    text = message.text
    if not text:
        return
    
    clean_text = text.strip().lower()
    if clean_text in ["@all", "все", "всем", "!all"]:
        try:
            members = await bot.api.messages.get_conversation_members(peer_id=peer_id)
            mentions = [f"[id{m.member_id}|•]" for m in members.items if m.member_id > 0][:30]
            await message.answer(f"📢 **ВНИМАНИЕ ВСЕМ!** 📢\n" + " ".join(mentions), random_id=0)
        except Exception:
            await message.answer("📢 **ВНИМАНИЕ ВСЕМ!** @all", random_id=0)


if __name__ == "__main__":
    print("🚀 AutoPiar Bot запущен на 15 секунд с автосбором бесед!")
    bot.run_forever()
