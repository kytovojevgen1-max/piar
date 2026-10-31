import time
import requests

TOKEN = 'vk1.a.q9RtV2818QWiCSFGgHLzR4gQr2xQ2fSIQKFbsrcoEudGaNSukxF_w-BSKNVvpWJhE6hON3wI9NBU5i96-0GVe0LTJ3so3jVMTfM6gQSZyWHkMO0187j0xC3ymyobpNhdxOUEAq5XsVnAdij_c9plT0lBdW-qD9cWxVw-Cp5ip7pCSkXvWBmAeJZ13rY2llgn3IczHjaPXuAdij_c9plT0lBdW-qD9cWxVw-Cp5ip7pCSkXvWBmAeJZ13rY2llgn3IczHjaPXOadwgLarLb96Q'

# 1. Проверяем ID группы и валидность токена
res = requests.post('https://api.vk.com/method/groups.getById', data={
    'access_token': TOKEN, 'v': '5.199'
}).json()

print("Результат проверки токена:", res)

if 'response' in res:
    group_id = res['response'][0]['id']
    print(f"✅ Токен рабочий! ID группы: {group_id}")
    
    # 2. Получаем Long Poll сервер
    lp = requests.post('https://api.vk.com/method/groups.getLongPollServer', data={
        'group_id': group_id, 'access_token': TOKEN, 'v': '5.199'
    }).json()
    
    if 'response' in lp:
        server = lp['response']['server']
        key = lp['response']['key']
        ts = lp['response']['ts']
        print(f"✅ Long Poll сервер получен успешно. Слушаем сообщения...")
        
        # 3. Слушаем одно событие для теста
        while True:
            resp = requests.get(f"{server}?act=a_check&key={key}&ts={ts}&wait=25").json()
            if 'updates' in resp:
                for event in resp['updates']:
                    print("📥 Пришло событие от ВК:", event)
            ts = resp.get('ts', ts)
            time.sleep(1)
else:
    print("❌ ОШИБКА: Токен недействителен или у него нет прав!")
