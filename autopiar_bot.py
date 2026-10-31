import os
import json
import time
import requests
from threading import Thread
from flask import Flask

# =====================================================================
# 1. МИНИ-СЕРВЕР ДЛЯ УДЕРЖАНИЯ ПОРТА НА RENDER
# =====================================================================
app = Flask(__name__)
START_TIME = time.time()

@app.route('/')
def home():
    return "Prince Russia AutoPiar LongPoll Server: ONLINE"

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
                interval = 60  # Интервал рассылки (1 минута)
                
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
# 4. LONG POLL API ЦИКЛ (ЧИТАЕТ СООБЩЕНИЯ И КНОПКИ)
# =====================================================================
def get_group_id():
    try:
        res = requests.post('https://api.vk.com/method/groups.getById', data={
            'access_token': TOKEN, 'v': '5.199'
        }).json()
        return res['response'][0]['id']
    except Exception:
        return None

def vk_longpoll_listener():
    group_id = get_group_id()
    if not group_id:
        return
    
    server, key, ts = None, None, None

    while True:
        try:
            if not server or not key:
                lp_res = requests.post('https://api.vk.com/method/groups.getLongPollServer', data={
                    'group_id': group_id,
                    'access_token': TOKEN,
                    'v': '5.199'
                }).json()
                
                if 'response' in lp_res:
                    server = lp_res['response']['server']
                    key = lp_res['response']['key']
                    ts = lp_res['response']['ts']
                else:
                    time.sleep(5)
                    continue

            resp = requests.get(f"{server}?act=a_check&key={key}&ts={ts}&wait=25", timeout=30).json()
            
            if 'failed' in resp:
                server, key = None, None
                continue
                
            ts = resp.get('ts', ts)
            updates = resp.get('updates', [])

            for event in updates:
                if event.get('type') == 'message_new':
                    msg = event.get('object', {}).get('message', {})
                    peer_id = msg.get('peer_id', 0)
                    text_lower = msg.get('text', '').strip().lower()
                    original_text = msg.get('text', '').strip()
                    
                    # Автоматический сбор бесед
                    if peer_id > 2000000000:
                        chats = load_json(CHATS_FILE, [])
                        if peer_id not in chats:
                            chats.append(peer_id)
                            save_json(CHATS_FILE, chats)

                    # Команды администратора и кнопки в ЛС
                    if peer_id == ADMIN_ID:
                        state = load_json(STATE_FILE, {'active': False, 'last_run': 0})
                        
                        if text_lower in ['/start', 'начать', 'меню', 'главное меню']:
                            send_vk_msg(peer_id, 
                                "👑 **ПАНЕЛЬ АВТОПИАРА (PRINCE RUSSIA)** 👑\n\n"
                                "Режим: **Long Poll API**\n"
                                "• `/статус` или «Статус бота»\n"
                                "• `/текст [текст]` — задать текст\n"
                                "• `/старт` или «🟢 Включить пиар»\n"
                                "• `/стоп` или «🔴 Выключить пиар»\n"
                                "• `/список` — список всех бесед"
                            )
                            
                        elif text_lower in ['/статус', 'статус бота', '📊 статус бота']:
                            chats = load_json(CHATS_FILE, [])
                            active_str = "🟢 Активен (каждые 60 сек)" if state.get('active') else "🔴 Остановлен"
                            cur_text = open(TEXT_FILE, 'r', encoding='utf-8').read() if os.path.exists(TEXT_FILE) else 'Не задан'
                            send_vk_msg(peer_id, f"📊 **СТАТУС:**\n• Пиар: {active_str}\n• Бесед в базе: {len(chats)}\n\n💬 **Текст:**\n{cur_text}")
                            
                        elif text_lower.startswith('/текст'):
                            new_text = original_text[6:].strip()
                            if new_text:
                                with open(TEXT_FILE, 'w', encoding='utf-8') as f:
                                    f.write(new_text)
                                state['active'] = True
                                state['last_run'] = time.time()
                                save_json(STATE_FILE, state)
                                send_vk_msg(peer_id, "🚀 Текст сохранен! Авто-рассылка заведена.")
                            else:
                                send_vk_msg(peer_id, "⚠️ Напиши текст после команды, например: `/текст Привет!`")
                                
                        elif text_lower in ['/старт', 'старт', '🟢 включить пиар']:
                            if not os.path.exists(TEXT_FILE):
                                send_vk_msg(peer_id, "⚠️ Сначала задай текст через `/текст [текст]`")
                            else:
                                state['active'] = True
                                state['last_run'] = time.time()
                                save_json(STATE_FILE, state)
                                send_vk_msg(peer_id, "🟢 Авто-рассылка успешно включена!")
                                
                        elif text_lower in ['/стоп', 'стоп', '🔴 выключить пиар']:
                            state['active'] = False
                            save_json(STATE_FILE, state)
                            send_vk_msg(peer_id, "🛑 Авто-рассылка остановлена.")
                            
                        elif text_lower in ['/список', 'список чатов', '📋 список чатов']:
                            chats = load_json(CHATS_FILE, [])
                            send_vk_msg(peer_id, f"📋 Всего бесед в базе: {len(chats)}")

        except Exception:
            time.sleep(3)

Thread(target=vk_longpoll_listener, daemon=True).start()

# Бесконечный цикл, чтобы главный поток не завершался
while True:
    time.sleep(3600)
