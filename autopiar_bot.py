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
        "chats": [], # Сюда автоматически соберутся чаты
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
# 3. HIGHLOAD АСИНХРОННЫЙ ПОТОК АВТОПИАРА
# =====================================================================
async def send_to_chat(peer_id, text, attachment):
    try:
        res = await bot.api.messages.send(
            peer_id=int(peer_id),
            message=text if text else None,
            attachment=attachment if attachment else None,
            random_id=0
        )
        print(f"✅ Успешно отправлено в чат {peer_id} (res: {res})")
    except Exception as e:
        print(f"❌ Ошибка отправки в чат {peer_id}: {e}")

async def piar_loop():
    while True:
        try:
            cfg = load_config()
            active = cfg.get("piar_active", False)
            chats = cfg.get("chats", [])
            print(f"🔄 Проверка пиара: активен={active}, бесед в базе={len(chats)}")
            
            if active and chats:
                text = cfg.get("piar_text", "")
                attachment = cfg.get("piar_attachment", "")
                
                print(f"🚀 Запуск рассылки по беседам...")
                for peer_id in chats:
                    await send_to_chat(peer_id, text, attachment)
                    await asyncio.sleep(0.2)
                print(f"🏁 Рассылка завершена.")
        except Exception as e:
            print(f"⚠️ Ошибка в потоке пиара: {e}")
        
        await asyncio.sleep(60)


# =====================================================================
# 4. ПАНЕЛЬ УПРАВЛЕНИЯ В ЛИЧНЫХ СООБЩЕНИЯХ
# =====================================================================

@bot.on.private_message(text=["/start", "Начать", "начать", "Меню", "меню", "🔙 Главное меню", "❌ Отмена"])
async def private_start(message: Message):
    uid = message.from_id
    if uid in user_states: del user_states[uid]
    cfg = load_config()
    
    is_main = (uid == cfg["main_owner"])
    is_admin = (is_main or uid in cfg["admins"])
    
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("📊 Статус бота"), color=KeyboardButtonColor.PRIMARY)
    
    if is_admin:
        kb.row()
        kb.add(Text("⚙️ Настроить пиар-текст"), color=KeyboardButtonColor.PRIMARY)
        kb.add(Text("📎 Задать вложение"), color=KeyboardButtonColor.PRIMARY)
        kb.row()
        status_text = "🟢 Выключить автопиар" if cfg.get("piar_active") else "🔴 Включить автопиар"
        kb.add(Text(status_text), color=KeyboardButtonColor.NEGATIVE)
        kb.add(Text("🗑 Очистить пиар-текст"), color=KeyboardButtonColor.PRIMARY)
        kb.row()
        kb.add(Text("🤖 Автоответчик"), color=KeyboardButtonColor.POSITIVE)
        kb.add(Text("🛑 Выключить пиар-чаты"), color=KeyboardButtonColor.NEGATIVE)
        
    if is_main:
        kb.row()
        kb.add(Text("➕ Добавить админа"), color=KeyboardButtonColor.PRIMARY)
        kb.add(Text("❌ Снять с админки"), color=KeyboardButtonColor.NEGATIVE)

    await message.answer(
        "👑 **ULTIMATE AUTO-PIAR CONTROL PANEL** 👑\n\n"
        "Панель управления активна.",
        keyboard=kb.get_json()
    )

@bot.on.private_message(text="📊 Статус бота")
async def private_status(message: Message):
    cfg = load_config()
    uptime_sec = int(time.time() - START_TIME)
    hours, remainder = divmod(uptime_sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    status_piar = "АКТИВЕН 🟢" if cfg.get("piar_active") else "ОСТАНОВЛЕН 🔴"
    chats_list = cfg.get("chats", [])
    
    await message.answer(
        f"📊 **СТАТУС:**\n"
        f"• Пиар: {status_piar}\n"
        f"• Чатов в базе: {len(chats_list)}\n"
        f"• Список чатов: `{chats_list}`\n"
        f"• Аптайм: {hours}ч {minutes}м"
    )

@bot.on.private_message(text=["🔴 Включить автопиар", "🟢 Выключить автопиар"])
async def private_toggle_piar(message: Message):
    uid = message.from_id
    cfg = load_config()
    if uid != cfg["main_owner"] and uid not in cfg["admins"]: return
    
    cfg["piar_active"] = not cfg.get("piar_active", False)
    save_config(cfg)
    await message.answer(f"⚙️ Пиар теперь: {'АКТИВЕН 🟢' if cfg['piar_active'] else 'ОСТАНОВЛЕН 🔴'}")

@bot.on.private_message(text="🛑 Выключить пиар-чаты")
async def private_clear_chats(message: Message):
    cfg = load_config()
    cfg["chats"] = []
    save_config(cfg)
    await message.answer("🛑 Список чатов очищен.")

@bot.on.private_message(text="🗑 Очистить пиар-текст")
async def private_clear_text(message: Message):
    cfg = load_config()
    cfg["piar_text"] = ""
    save_config(cfg)
    await message.answer("🗑 Текст очищен.")

@bot.on.private_message(text="⚙️ Настроить пиар-текст")
async def private_set_text(message: Message):
    user_states[message.from_id] = "wait_piar_text"
    await message.answer("✍️ Отправьте новый текст:")

@bot.on.private_message(text="📎 Задать вложение")
async def private_set_att(message: Message):
    user_states[message.from_id] = "wait_piar_att"
    await message.answer("✍️ Отправьте код вложения (например `photo123_456`):")

@bot.on.private_message(text="🤖 Автоответчик")
async def private_set_resp(message: Message):
    user_states[message.from_id] = "wait_autoresponder"
    await message.answer("✍️ Отправьте текст автоответчика:")

@bot.on.private_message()
async def private_states_handler(message: Message):
    uid = message.from_id
    text = message.text
    if not text: return
    state = user_states.get(uid)
    cfg = load_config()

    if state == "wait_piar_text":
        del user_states[uid]
        cfg["piar_text"] = text
        save_config(cfg)
        return await message.answer("✅ Текст обновлен!")

    if state == "wait_piar_att":
        del user_states[uid]
        cfg["piar_attachment"] = "" if text.lower() in ["нет", "отмена"] else text.strip()
        save_config(cfg)
        return await message.answer("✅ Вложение обновлено!")

    if state == "wait_autoresponder":
        del user_states[uid]
        cfg["autoresponder"] = text
        save_config(cfg)
        return await message.answer("✅ Автоответчик обновлен!")

    if uid in cfg["admins"] or uid == cfg["main_owner"]:
        await message.answer("❌ Используйте кнопки меню.")
    else:
        await message.answer(cfg.get("autoresponder", "Здравствуйте!"))


# =====================================================================
# 5. СБОР ЧАТОВ И ИХ ПЕРЕХВАТ
# =====================================================================

@bot.on.chat_message()
async def chat_handler(message: Message):
    peer_id = message.peer_id
    cfg = load_config()
    
    if peer_id not in cfg["chats"]:
        cfg["chats"].append(peer_id)
        save_config(cfg)
        print(f"📥 НОВЫЙ ЧАТ ДОБАВЛЕН В БАЗУ: {peer_id}")

    text = message.text
    if text and text.strip().lower() in ["@all", "все", "всем", "!all"]:
        try:
            members = await bot.api.messages.get_conversation_members(peer_id=peer_id)
            mentions = [f"[id{m.member_id}|•]" for m in members.items if m.member_id > 0][:30]
            await message.answer(f"📢 **УПОВЕЩЕНИЕ ВСЕМ**\n" + " ".join(mentions), random_id=0)
        except Exception:
            await message.answer("📢 **ВНИМАНИЕ ВСЕМ!** @all", random_id=0)


if __name__ == "__main__":
    print("🚀 AutoPiar Bot запущен и готов к работе!")
    loop = asyncio.get_event_loop()
    loop.create_task(piar_loop())
    bot.run_forever()
