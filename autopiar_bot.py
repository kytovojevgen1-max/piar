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
        "main_owner": 897082738,  # Твой главный VK ID
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
# 3. HIGHLOAD АСИНХРОННЫЙ ПОТОК АВТОПИАРА
# =====================================================================
async def send_to_chat(peer_id, text, attachment):
    try:
        await bot.api.messages.send(
            peer_id=int(peer_id),
            message=text if text else None,
            attachment=attachment if attachment else None,
            random_id=0
        )
    except Exception as e:
        print(f"Не удалось отправить в чат {peer_id}: {e}")

async def piar_loop():
    while True:
        try:
            cfg = load_config()
            if cfg.get("piar_active", False) and cfg.get("chats"):
                text = cfg.get("piar_text", "")
                attachment = cfg.get("piar_attachment", "")
                chats = cfg["chats"]
                
                print(f"🚀 Запуск рассылки по {len(chats)} чатам...")
                batch_size = 30
                for i in range(0, len(chats), batch_size):
                    batch = chats[i:i + batch_size]
                    tasks = [send_to_chat(peer_id, text, attachment) for peer_id in batch]
                    await asyncio.gather(*tasks)
                    await asyncio.sleep(0.3)
                print("✅ Рассылка круга завершена.")
        except Exception as e:
            print(f"Ошибка в потоке автопиаpa: {e}")
        
        await asyncio.sleep(60)


# =====================================================================
# 4. ЛИЧНЫЕ СООБЩЕНИЯ И ПАНЕЛЬ УПРАВЛЕНИЯ
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
        "Добро пожаловать в центр управления рассылкой.\n"
        "Используйте кнопки меню ниже:",
        keyboard=kb.get_json()
    )

@bot.on.private_message(text="📊 Статус бота")
async def private_status(message: Message):
    cfg = load_config()
    uptime_sec = int(time.time() - START_TIME)
    hours, remainder = divmod(uptime_sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    status_piar = "АКТИВЕН (каждую 1 мин) 🟢" if cfg.get("piar_active") else "ОСТАНОВЛЕН 🔴"
    chats_count = len(cfg.get("chats", []))
    piar_text = cfg.get("piar_text", "") or "Не задан (пусто)"
    piar_att = cfg.get("piar_attachment", "") or "Отсутствует"
    
    await message.answer(
        f"📊 **ПОЛНЫЙ СТАТУС СИСТЕМЫ:**\n\n"
        f"• Статус пиара: {status_piar}\n"
        f"• Активных бесед в базе: `{chats_count}`\n"
        f"• Аптайм ядра: `{hours}ч {minutes}м {seconds}с`\n"
        f"• Прикрепленное медиа: `{piar_att}`\n\n"
        f"💬 **Текущий текст рассылки вместе с медиа:**\n"
        f"────────────────────────\n"
        f"{piar_text}\n"
        f"────────────────────────"
    )

@bot.on.private_message(text=["🔴 Включить автопиар", "🟢 Выключить автопиар"])
async def private_toggle_piar(message: Message):
    uid = message.from_id
    cfg = load_config()
    if uid != cfg["main_owner"] and uid not in cfg["admins"]: return
    
    current = cfg.get("piar_active", False)
    cfg["piar_active"] = not current
    save_config(cfg)
    
    state_str = "УСПЕШНО ВКЛЮЧЕН (рассылка каждую минуту) 🟢" if cfg["piar_active"] else "ОСТАНОВЛЕН 🔴"
    await message.answer(f"⚙️ Автопиар теперь: {state_str}")

@bot.on.private_message(text="🛑 Выключить пиар-чаты")
async def private_clear_chats(message: Message):
    uid = message.from_id
    cfg = load_config()
    if uid != cfg["main_owner"] and uid not in cfg["admins"]: return
    cfg["chats"] = []
    save_config(cfg)
    await message.answer("🛑 Список пиар-чатов полностью очищен!")

@bot.on.private_message(text="🗑 Очистить пиар-текст")
async def private_clear_text(message: Message):
    uid = message.from_id
    cfg = load_config()
    if uid != cfg["main_owner"] and uid not in cfg["admins"]: return
    cfg["piar_text"] = ""
    save_config(cfg)
    await message.answer("🗑 Текст пиара успешно очищен.")

@bot.on.private_message(text="⚙️ Настроить пиар-текст")
async def private_set_text(message: Message):
    uid = message.from_id
    cfg = load_config()
    if uid != cfg["main_owner"] and uid not in cfg["admins"]: return
    user_states[uid] = "wait_piar_text"
    await message.answer("✍️ Отправьте новый текст для автопиара:", keyboard=Keyboard(one_time=False, inline=True).add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE).get_json())

@bot.on.private_message(text="📎 Задать вложение")
async def private_set_att(message: Message):
    uid = message.from_id
    cfg = load_config()
    if uid != cfg["main_owner"] and uid not in cfg["admins"]: return
    user_states[uid] = "wait_piar_att"
    await message.answer("✍️ Отправьте код вложения (например: `photo12345_67890`), либо `нет` для удаления:", keyboard=Keyboard(one_time=False, inline=True).add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE).get_json())

@bot.on.private_message(text="🤖 Автоответчик")
async def private_set_resp(message: Message):
    uid = message.from_id
    cfg = load_config()
    if uid != cfg["main_owner"] and uid not in cfg["admins"]: return
    user_states[uid] = "wait_autoresponder"
    await message.answer(f"✍️ Текущий текст автоответчика:\n`{cfg.get('autoresponder')}`\n\nОтправьте новый текст:", keyboard=Keyboard(one_time=False, inline=True).add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE).get_json())

@bot.on.private_message(text="➕ Добавить админа")
async def private_add_admin(message: Message):
    uid = message.from_id
    cfg = load_config()
    if uid != cfg["main_owner"]: return
    user_states[uid] = "wait_new_admin"
    await message.answer("✍️ Введите цифровой VK ID нового администратора бота:", keyboard=Keyboard(one_time=False, inline=True).add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE).get_json())

@bot.on.private_message(text="❌ Снять с админки")
async def private_remove_admin(message: Message):
    uid = message.from_id
    cfg = load_config()
    if uid != cfg["main_owner"]: return
    user_states[uid] = "wait_remove_admin"
    await message.answer(f"✍️ Текущие админы: `{cfg['admins']}`\n\nВведите VK ID администратора для снятия:", keyboard=Keyboard(one_time=False, inline=True).add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE).get_json())


@bot.on.private_message()
async def private_states_handler(message: Message):
    uid = message.from_id
    text = message.text
    if not text: return
    state = user_states.get(uid)
    cfg = load_config()

    if state == "wait_piar_text" and (uid == cfg["main_owner"] or uid in cfg["admins"]):
        del user_states[uid]
        cfg["piar_text"] = text
        save_config(cfg)
        return await message.answer("✅ Текст автопиара успешно обновлен!")

    if state == "wait_piar_att" and (uid == cfg["main_owner"] or uid in cfg["admins"]):
        del user_states[uid]
        cfg["piar_attachment"] = "" if text.lower() in ["нет", "0", "отмена"] else text.strip()
        save_config(cfg)
        return await message.answer("✅ Вложение для автопиара обновлено!")

    if state == "wait_autoresponder" and (uid == cfg["main_owner"] or uid in cfg["admins"]):
        del user_states[uid]
        cfg["autoresponder"] = text
        save_config(cfg)
        return await message.answer("✅ Текст автоответчика успешно изменен!")

    if state == "wait_new_admin" and uid == cfg["main_owner"]:
        del user_states[uid]
        clean = text.strip().replace("id", "")
        if clean.isdigit():
            tid = int(clean)
            if tid not in cfg["admins"]:
                cfg["admins"].append(tid)
                save_config(cfg)
                return await message.answer(f"✅ Пользователь [id{tid}|ID {tid}] назначен администратором бота.")
        return await message.answer("❌ Неверный VK ID.")

    if state == "wait_remove_admin" and uid == cfg["main_owner"]:
        del user_states[uid]
        clean = text.strip().replace("id", "")
        if clean.isdigit():
            tid = int(clean)
            if tid == cfg["main_owner"]:
                return await message.answer("❌ Нельзя снять главного владельца!")
            if tid in cfg["admins"]:
                cfg["admins"].remove(tid)
                save_config(cfg)
                return await message.answer(f"✅ Пользователь [id{tid}|ID {tid}] снят с админки бота.")
            return await message.answer("❌ Этот пользователь не найден в списке админов.")
        return await message.answer("❌ Неверный VK ID.")

    is_admin = (uid == cfg["main_owner"] or uid in cfg["admins"])
    if not is_admin:
        resp = cfg.get("autoresponder", "Здравствуйте! Сообщение получено.")
        return await message.answer(resp)

    await message.answer("❌ Используйте кнопки меню.")


# =====================================================================
# 5. РАБОТА В БЕСЕДАХ (МОМЕНТАЛЬНЫЙ СТАРТ ПИАРА ПРИ ДОБАВЛЕНИИ + @all)
# =====================================================================

@bot.on.chat_message()
async def chat_handler(message: Message):
    peer_id = message.peer_id
    cfg = load_config()
    
    # 1. Если бота только что добавили в беседу
    if message.action and message.action.type == "chat_invite_user":
        if peer_id not in cfg["chats"]:
            cfg["chats"].append(peer_id)
            save_config(cfg)
            
        # ЕСЛИ ПИАР ВКЛЮЧЕН — СРАЗУ ЖЕ КИДАЕМ РАССЫЛКУ В ЭТОТ ЧАТ!
        if cfg.get("piar_active", False):
            await send_to_chat(peer_id, cfg.get("piar_text", ""), cfg.get("piar_attachment", ""))
        return

    # 2. Обычный сбор чатов при активности
    if peer_id not in cfg["chats"]:
        cfg["chats"].append(peer_id)
        save_config(cfg)

    text = message.text
    if not text: return
    
    clean_text = text.strip().lower()

    if clean_text in ["@all", "все", "всем", "!all"]:
        try:
            members = await bot.api.messages.get_conversation_members(peer_id=peer_id)
            mentions = []
            
            for m in members.items:
                if m.member_id > 0 and len(mentions) < 30:
                    mentions.append(f"[id{m.member_id}|•]")
            
            tag_string = " ".join(mentions)
            
            await message.answer(
                f"📢 **ВНИМАНИЕ! ОБЩЕЕ УПОВЕЩЕНИЕ ОТ УЧАСТНИКА** 📢\n\n"
                f"👤 Вызвал: [id{message.from_id}|Пользователь]\n"
                f"═══════════════════════════\n"
                f"{tag_string} (Все на связи!)"
            )
        except Exception:
            await message.answer(
                f"📢 **ВНИМАНИЕ ВСЕМ!** 📢\n"
                f"👤 Вызвал: [id{message.from_id}|Пользователь]\n"
                f"@all"
            )


if __name__ == "__main__":
    print("🚀 Highload AutoPiar Bot успешно запущен!")
    loop = asyncio.get_event_loop()
    loop.create_task(piar_loop())
    bot.run_forever()
