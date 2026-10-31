import os
import json
import time
import requests
from threading import Thread
from flask import Flask, request

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
    return f"Prince Russia AutoPiar Server: ONLINE | Uptime: {hours}h {minutes}m {seconds}s"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

Thread(target=run_flask, daemon=True).start()


# =====================================================================
# 2. НАСТРОЙКИ И ФАЙЛЫ
# =====================================================================
TOKEN = 'vk1.a.TnKXDAbLse2U20_TT4Zk4ebar69t1320OmNPJCUtZaNNOgVtiUJYXCGblKFccEyc3SKwljisxXghnw1vcPyyEd1McI6Ykbl1zEM3H_surC4Xlq4A-VV86SN4qKCACGepMxSAYMpWtswkRo1FlUgad0YiMjWwzRTm80lwTRdqJ5BUUjcuQ9rZnrLHgBd4LYoaZTwHeKBGzIQWdnPZXxYeLw'
ADMIN_ID = 897082738

CHATS_FILE = 'chats.json'
TEXT_FILE = 'spam_text.txt'
STATE_FILE = 'state.json'

def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return default

def save_json(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения {filename}: {e}")

def send_vk_msg(peer_id, message):
    try:
        url = 'https://api.vk.com/method/messages.send'
        data = {
            'peer_id': peer_id,
            'message': message,
            'access_token': TOKEN,
            'v': '5.199',
            'random_id': int(time.time() * 1000) % 2147483647
        }
        response = requests.post(url, data=data, timeout=3)
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки в {peer_id}: {e}")
        return None


# =====================================================================
# 3. ФОНОВЫЙ ПОТОК АВТО-РАССЫЛКИ (КАЖДЫЕ 60 СЕКУНД)
# =====================================================================
def auto_piar_worker():
    print("🚀 [PYTHON PIAR] Фоновый поток рассылки успешно запущен!")
    while True:
        try:
            state = load_json(STATE_FILE, {'active': False, 'last_run': 0})
            
            if state.get('active', False):
                current_time = time.time()
                interval = 60 # Интервал в секундах
                
                if current_time - state.get('last_run', 0) > interval:
                    state['last_run'] = current_time
                    save_json(STATE_FILE, state)
                    
                    if os.path.exists(TEXT_FILE):
                        with open(TEXT_FILE, 'r', encoding='utf-8') as f:
                            spam_text = f.read().strip()
                    else:
                        spam_text = ""
                        
                    chats = load_json(CHATS_FILE, [])
                    
                    if spam_text and chats:
                        print(f"🚀 [PIAR] Старт рассылки по {len(chats)} чатам...")
                        for chat_id in chats:
                            target_peer = chat_id if chat_id > 2000000000 else 2000000000 + int(chat_id)
                            send_vk_msg(target_peer, spam_text)
                            time.sleep(0.05)
                        print("✅ [PIAR] Круг рассылки завершен.")
        except Exception as e:
            print(f"❌ Ошибка в потоке пиара: {e}")
            
        time.sleep(5)

Thread(target=auto_piar_worker, daemon=True).start()


# =====================================================================
# 4. ВЕБХУК ДЛЯ ПРИЕМА СООБЩЕНИЙ И КОМАНД ОТ ВК
# =====================================================================
@app.route('/', methods=['POST'])
def vk_webhook():
    # Получаем JSON с правильной обработкой запроса Flask
    data = requests.request.get_json(silent=True) if hasattr(requests, 'request') else {}
    from flask import request
    data = request.get_json(silent=True) or {}
    
    if data.get('type') == 'confirmation':
        return '2a390db5'
    
    if data.get('type') == 'message_new':
        msg = data.get('object', {}).get('message', {})
        peer_id = msg.get('peer_id', 0)
        text = msg.get('text', '').strip()
        
        # Автоматический сбор бесед
        if peer_id > 2000000000:
            chats = load_json(CHATS_FILE, [])
            if peer_id not in chats:
                chats.append(peer_id)
                save_json(CHATS_FILE, chats)
                print(f"📥 Добавлен новый чат: {peer_id}")

        # Команды администратора в ЛС
        if peer_id == ADMIN_ID:
            args = text.split(' ')
            cmd = args[0].lower() if args else ''
            
            state = load_json(STATE_FILE, {'active': False, 'last_run': 0})
            
            if cmd == '/статус':
                chats = load_json(CHATS_FILE, [])
                active_str = "🟢 Активен (каждые 60 сек)" if state.get('active') else "🔴 Остановлен"
                cur_text = open(TEXT_FILE, 'r', encoding='utf-8').read() if os.path.exists(TEXT_FILE) else 'Не задан'
                send_vk_msg(peer_id, f"Статус: {active_str}\nБесед в базе: {len(chats)}\n\nТекст:\n{cur_text}")
                
            elif cmd == '/текст':
                new_text = text[len(args[0]):].strip()
                if new_text:
                    with open(TEXT_FILE, 'w', encoding='utf-8') as f:
                        f.write(new_text)
                    state['active'] = True
                    state['last_run'] = time.time()
                    save_json(STATE_FILE, state)
                    send_vk_msg(peer_id, "🚀 Текст сохранен! Авто-рассылка на Python запущена.")
                else:
                    send_vk_msg(peer_id, "⚠️ Напиши текст после команды `/текст`")
                    
            elif cmd == '/старт':
                if not os.path.exists(TEXT_FILE):
                    send_vk_msg(peer_id, "⚠️ Сначала задай текст через `/текст [текст]`")
                else:
                    state['active'] = True
                    state['last_run'] = time.time()
                    save_json(STATE_FILE, state)
                    send_vk_msg(peer_id, "🟢 Авто-рассылка возобновлена!")
                    
            elif cmd == '/стоп':
                state['active'] = False
                save_json(STATE_FILE, state)
                send_vk_msg(peer_id, "🛑 Авто-рассылка остановлена.")
                
            elif cmd == '/список':
                chats = load_json(CHATS_FILE, [])
                send_vk_msg(peer_id, f"📋 Всего бесед в базе: {len(chats)}")

    return 'ok'

if __name__ == '__main__':
    print("🚀 Python AutoPiar Bot с правильным токеном запущен!")
