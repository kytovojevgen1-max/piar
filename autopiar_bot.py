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
    return "Prince Russia AutoPiar Server: ONLINE"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

Thread(target=run_flask, daemon=True).start()


# =====================================================================
# 2. НАСТРОЙКИ И ФАЙЛЫ
# =====================================================================
TOKEN = 'vk1.a.q9RtV2818QWiCSFGgHLzR4gQr2xQ2fSIQKFbsrcoEudGaNSukxF_w-BSKNVvpWJhE6hON3wI9NBU5i96-0GVe0LTJ3so3jVMTfM6gQSZyWHkMO0187j0xC3ymyobpNhdxOUEAq5XsVnAdij_c9plT0lBdW-qD9cWxVw-Cp5ip7pCSkXvWBmAeJZ13rY2llgn3IczHjaPXOadwgLarLb96Q'
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
    except Exception:
        pass

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
        requests.post(url, data=data, timeout=3)
    except Exception:
        pass


# =====================================================================
# 3. ФОНОВЫЙ ПОТОК АВТО-РАССЫЛКИ (КАЖДЫЕ 60 СЕКУНД)
# =====================================================================
def auto_piar_worker():
    while True:
        try:
            state = load_json(STATE_FILE, {'active': False, 'last_run': 0})
            if state.get('active', False):
                current_time = time.time()
                interval = 60  # Интервал рассылки в секундах (1 минута)
                
                if current_time - state.get('last_run', 0) > interval:
                    state['last_run'] = current_time
                    save_json(STATE_FILE, state)
                    
                    spam_text = ""
                    if os.path.exists(TEXT_FILE):
                        with open(TEXT_FILE, 'r', encoding='utf-8') as f:
                            spam_text = f.read().strip()
                            
                    chats = load_json(CHATS_FILE, [])
                    if spam_text and chats:
                        for chat_id in chats:
                            target_peer = chat_id if chat_id > 2000000000 else 2000000000 + int(chat_id)
                            send_vk_msg(target_peer, spam_text)
                            time.sleep(0.03)
        except Exception:
            pass
            
        time.sleep(5)

Thread(target=auto_piar_worker, daemon=True).start()


# =====================================================================
# 4. ВЕБХУК ДЛЯ ПРИЕМА СООБЩЕНИЙ И КОМАНД ОТ ВК
# =====================================================================
@app.route('/', methods=['POST'])
def vk_webhook():
    data = request.get_json(silent=True) or {}
    
    # Подтверждение сервера для Callback API ВК
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

        # Команды администратора в ЛС
        if peer_id == ADMIN_ID:
            args = text.split(' ')
            cmd = args[0].lower() if args else ''
            
            state = load_json(STATE_FILE, {'active': False, 'last_run': 0})
            
            if cmd == '/статус':
                chats = load_json(CHATS_FILE, [])
                active_str = "🟢 Активен (каждые 60 сек)" if state.get('active') else "🔴 Остановлен"
                cur_text = open(TEXT_FILE, 'r', encoding='utf-8').read() if os.path.exists(TEXT_FILE) else 'Не задан'
                send_vk_msg(peer_id, f"Статус: {active_str}\nБесед в базе: {len(chats)}\n\nТекущий текст:\n{cur_text}")
                
            elif cmd == '/текст':
                new_text = text[len(args[0]):].strip()
                if new_text:
                    with open(TEXT_FILE, 'w', encoding='utf-8') as f:
                        f.write(new_text)
                    state['active'] = True
                    state['last_run'] = time.time()
                    save_json(STATE_FILE, state)
                    send_vk_msg(peer_id, "🚀 Текст сохранен! Авто-рассылка запущена и работает каждую минуту.")
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
