# Sovereign source reader: 06-argon, part 1

Derived reading aid; original file bytes and rights are authoritative. No functions or file sections have been omitted from the listed files. Cite `original/path:line` using the numbered column. Read at the exact review commit supplied in the user message.

## argon-game/game.py

Original bytes: 8886; SHA256: `102516d3e47409e4b2226db09a8dfb016e10381e67c4fb94aa9f4a8b616e83ca`. Original source line numbers follow.

````text
    1 | """Authoritative, deterministic adventure using the existing durable Store."""
    2 | from copy import deepcopy
    3 | import hashlib
    4 | import json
    5 | from pathlib import Path
    6 | import re
    7 | import sys
    8 |
    9 | ROOT = Path(__file__).resolve().parents[1]
   10 | sys.path.insert(0, str(ROOT / 'simulation-core'))
   11 | from contracts import canonical
   12 | from persistence import Store, atomic_write, digest
   13 |
   14 | WORLD_BYTES = Path(__file__).with_name('world.json').read_bytes()
   15 | WORLD = json.loads(WORLD_BYTES)
   16 | WORLD_HASH = hashlib.sha256(WORLD_BYTES).hexdigest()
   17 | MAX_ACTIONS = 500
   18 |
   19 |
   20 | def initial_state():
   21 |     return {'schema':'argon.game.v1', 'world_hash':WORLD_HASH, 'revision':0, 'sim_time':1122,
   22 |         'location':WORLD['start'], 'energy':70, 'cash_cents':1200, 'items':['prototype'],
   23 |         'flags':[], 'visited':[WORLD['start']], 'ending':None, 'history':[],
   24 |         'note':WORLD['intro'], 'log':[WORLD['intro']]}
   25 |
   26 |
   27 | def disabled_reason(state, action_id):
   28 |     if state['ending']: return 'Пригоду завершено. Можна завантажити збереження або почати знову.'
   29 |     if len(state['history']) >= MAX_ACTIONS: return 'Досягнуто межі цієї пригоди. Збережи її або почни нову.'
   30 |     action = WORLD['actions'][action_id]
   31 |     if action.get('once') in state['flags']: return 'Уже зроблено'
   32 |     if action.get('cost', 0) > state['cash_cents']: return 'Бракує ігрових CHF'
   33 |     if action.get('requires_item') and action['requires_item'] not in state['items']: return 'Потрібно: ' + WORLD['items'][action['requires_item']]['name']
   34 |     if any(flag not in state['flags'] for flag in action.get('requires_flags', [])): return 'Спершу познайомся з Адою та виконай потрібні кроки'
   35 |     if state['energy'] < max(action.get('requires_energy', 0), -action.get('energy', 0)): return 'Бракує сил. Перепочинь біля води або в майстерні.'
   36 |     return None
   37 |
   38 |
   39 | def step(state, action_id, payload=None):
   40 |     payload = {} if payload is None else payload
   41 |     if not isinstance(action_id, str) or not isinstance(payload, dict): raise ValueError('INVALID_ACTION')
   42 |     allowed = {a for spot in WORLD['locations'][state['location']]['hotspots'] for a in spot['actions']}
   43 |     if action_id not in allowed: raise ValueError('ACTION_NOT_IN_LOCATION')
   44 |     reason = disabled_reason(state, action_id)
   45 |     if reason: raise ValueError(reason)
   46 |     action = WORLD['actions'][action_id]
   47 |     if set(payload) - ({'code'} if 'code' in action else set()): raise ValueError('UNKNOWN_PAYLOAD')
   48 |     if 'code' in action and (not isinstance(payload.get('code'), str) or len(payload['code']) > 12): raise ValueError('Потрібен чотиризначний код із квитанції')
   49 |     result = deepcopy(state)
   50 |     if 'code' in action and payload['code'] != action['code']:
   51 |         result['sim_time'] += 1
   52 |         result['note'] = 'Код не підійшов. Поглянь на квитанцію біля табло SBB. Замок не заблоковано.'
   53 |     else:
   54 |         result['sim_time'] += action['minutes']
   55 |         result['energy'] = min(100, max(0, result['energy'] + action['energy']))
   56 |         result['cash_cents'] -= action.get('cost', 0)
   57 |         if action.get('item') and action['item'] not in result['items']: result['items'].append(action['item'])
   58 |         if action.get('item') == 'ticket' and 'ticket_owned' not in result['flags']: result['flags'].append('ticket_owned')
   59 |         if action.get('flag') and action['flag'] not in result['flags']: result['flags'].append(action['flag'])
   60 |         if action.get('to'):
   61 |             result['location'] = action['to']
   62 |             if action['to'] not in result['visited']: result['visited'].append(action['to'])
   63 |         result['note'] = action['note']
   64 |         if action.get('ending'):
   65 |             ending = 'honest' if action['ending'] == 'honest' else 'late' if result['sim_time'] > WORLD['deadline'] else 'prepared'
   66 |             result['ending'] = {'id':ending, 'title':{'honest':'Чесна друга спроба','late':'Місто зачекало','prepared':'Показ, який відбувся'}[ending],
   67 |                 'text':{'honest':'Ти зберіг довіру, визнавши межі готовності. Наступного разу — з перевіреним прототипом.',
   68 |                     'late':'Ти прийшов пізніше, але показав перевірений результат. Ада залишає час для наступної розмови.',
   69 |                     'prepared':'Ти дістався вчасно, перевірив прототип і показав його Аді. Жодних обіцянок мільйонів — одна справжня розмова в цій вигаданій історії.'}[ending]}
   70 |     result['history'].append({'action':action_id, 'payload':deepcopy(payload)})
   71 |     result['log'] = (result['log'] + [result['note']])[-16:]
   72 |     return result
   73 |
   74 |
   75 | def save_packet(state):
   76 |     packet = {'schema':'argon.save.v1', 'world_hash':WORLD_HASH, 'actions':deepcopy(state['history'])}
   77 |     return {**packet, 'sha256':digest(packet)}
   78 |
   79 |
   80 | def restore(packet):
   81 |     if not isinstance(packet, dict) or set(packet) != {'schema','world_hash','actions','sha256'}: raise ValueError('SAVE_SCHEMA_INVALID')
   82 |     if packet['schema'] != 'argon.save.v1' or packet['world_hash'] != WORLD_HASH: raise ValueError('SAVE_VERSION_UNSUPPORTED')
   83 |     if not isinstance(packet['actions'], list) or len(packet['actions']) > MAX_ACTIONS: raise ValueError('SAVE_TOO_LARGE')
   84 |     if digest({k:v for k,v in packet.items() if k != 'sha256'}) != packet['sha256']: raise ValueError('SAVE_INTEGRITY_FAILED')
   85 |     state = initial_state()
   86 |     for entry in packet['actions']:
   87 |         if not isinstance(entry, dict) or set(entry) != {'action','payload'}: raise ValueError('SAVE_ACTION_INVALID')
   88 |         state = step(state, entry['action'], entry['payload'])
   89 |     return state
   90 |
   91 |
   92 | class Game:
   93 |     def __init__(self, directory):
   94 |         self.directory = Path(directory)
   95 |         self.store = Store(self.directory, initial_state())
   96 |         if self.store.state.get('schema') != 'argon.game.v1' or self.store.state.get('world_hash') != WORLD_HASH:
   97 |             self.store.close()
   98 |             raise ValueError('SAVE_WORLD_CHANGED_MIGRATION_REQUIRED')
   99 |
  100 |     def view(self):
  101 |         state = self.store.get()
  102 |         location = deepcopy(WORLD['locations'][state['location']])
  103 |         for spot in location['hotspots']:
  104 |             spot['choices'] = [{**WORLD['actions'][a], 'id':a, 'disabled':disabled_reason(state,a)} for a in spot.pop('actions')]
  105 |             # Lock codes belong in explicit clues, not in interaction metadata.
  106 |             for choice in spot['choices']: choice.pop('code', None)
  107 |         return {'state':state, 'location':location, 'items':WORLD['items'], 'deadline':WORLD['deadline'],
  108 |                 'saved_checkpoint':(self.directory/'checkpoint.json').is_file()}
  109 |
  110 |     def command(self, action, payload, request_id, expected_revision=None):
  111 |         if not isinstance(request_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,80}',request_id): raise ValueError('INVALID_REQUEST_ID')
  112 |         if not isinstance(payload,dict): raise ValueError('INVALID_PAYLOAD')
  113 |         fingerprint = digest([action,payload])
  114 |         with self.store.lock:
  115 |             old = self.store.duplicate(request_id, fingerprint)
  116 |             if old is not None: return old
  117 |             before = self.store.get()
  118 |             if expected_revision is not None and (type(expected_revision) is not int or expected_revision != before['revision']):
  119 |                 raise ValueError('REVISION_CONFLICT')
  120 |             if action == 'new_game':
  121 |                 if payload: raise ValueError('UNKNOWN_PAYLOAD')
  122 |                 after = initial_state()
  123 |             elif action == 'load_checkpoint':
  124 |                 if payload: raise ValueError('UNKNOWN_PAYLOAD')
  125 |                 path = self.directory/'checkpoint.json'
  126 |                 if not path.is_file(): raise ValueError('Ще немає ручного збереження')
  127 |                 if path.stat().st_size > 256000: raise ValueError('SAVE_TOO_LARGE')
  128 |                 after = restore(json.loads(path.read_text(encoding='utf-8')))
  129 |             elif action == 'save_checkpoint':
  130 |                 if payload: raise ValueError('UNKNOWN_PAYLOAD')
  131 |                 atomic_write(self.directory/'checkpoint.json', canonical(save_packet(before)).encode('utf-8'))
  132 |                 after = deepcopy(before)
  133 |             else:
  134 |                 after = step(before,action,payload)
  135 |             result = {'accepted':True, 'revision':before['revision']+1, 'request_id':request_id}
  136 |             self.store.commit('argon.'+action, payload, 'argon-ui', request_id, result, after, fingerprint)
  137 |             return result
  138 |
  139 |     def close(self): self.store.close()
````

## argon-game/world.json

Original bytes: 12896; SHA256: `4c0bf37b5ca8eddec1e35016869aad717604c96399b7f8b5fcf49db6702d8b72`. Original source line numbers follow.

````text
    1 | {
    2 |   "schema": "argon.world.v1",
    3 |   "title": "ARGON · Останній трамвай",
    4 |   "intro": "Цюрих. 18:42. У тебе є прототип, зустріч о 19:30 і кабель, який залишився в камері схову. Дістанься майстерні в Альтштадті та покажи працююче демо. Усі події, люди й гроші тут вигадані.",
    5 |   "start": "stadelhofen",
    6 |   "deadline": 1170,
    7 |   "locations": {
    8 |     "stadelhofen": {
    9 |       "title": "Stadelhofen", "subtitle": "Перон 2 · дощ на бетоні", "chapter": "01 / ПРИБУТТЯ",
   10 |       "description": "Потяг ще не встиг охолонути, а місто вже кудись поспішає. Твій прототип у рюкзаку. Кабелю в ньому немає.",
   11 |       "spawn": [520, 590],
   12 |       "hotspots": [
   13 |         {"id":"board", "title":"Табло SBB", "x":340,"y":430,"description":"Демонстраційне табло станції. На звороті квитанції зберігся код камери схову.","actions":["read_board"]},
   14 |         {"id":"locker", "title":"Камера схову C7", "x":165,"y":535,"description":"Тут ти залишив запасний кабель. Потрібен чотиризначний код із квитанції.","input":"code","actions":["open_locker"]},
   15 |         {"id":"stairs", "title":"Сходи на Bellevue", "x":1000,"y":410,"description":"Арки Калатрави піднімають тебе до світла міста. Звідти можна сісти на трамвай або пройтися пішки.","actions":["to_bellevue"]},
   16 |         {"id":"bench", "title":"Лавка на пероні", "x":740,"y":625,"description":"Перепочинь, якщо сили закінчилися. Кожна зупинка забирає шість ігрових хвилин.","actions":["catch_breath"]}
   17 |       ]
   18 |     },
   19 |     "bellevue": {
   20 |       "title":"Bellevue", "subtitle":"Трамвайне кільце · відблиски озера", "chapter":"02 / ПЕРЕХРЕСТЯ",
   21 |       "description":"Синій трамвай дзвенить на повороті. Можна купити квиток, допомогти музиканту або піти до старого міста вздовж річки.",
   22 |       "spawn":[330,590],
   23 |       "hotspots":[
   24 |         {"id":"ticket","title":"Квитковий автомат","x":950,"y":515,"description":"Ігровий квиток коштує CHF 4.40. Він діятиме на всі поїздки цієї глави.","actions":["buy_ticket"]},
   25 |         {"id":"musician","title":"Музикант біля кіоску","x":525,"y":530,"description":"Вітер розсипав ноти. Допомога забере трохи часу; музикант має зайвий денний квиток.","actions":["help_musician"]},
   26 |         {"id":"tram","title":"Трамвай до Altstadt","x":760,"y":405,"description":"У цій вигаданій маршрутній мережі трамвай довезе до старого міста за п’ять хвилин.","actions":["take_tram"]},
   27 |         {"id":"river","title":"Стежка вздовж Ліммату","x":1110,"y":590,"description":"Безкоштовно, дванадцять хвилин і трохи сил. Місто під дощем заслуговує цієї прогулянки.","actions":["walk_altstadt"]},
   28 |         {"id":"coffee","title":"Кіоск із кавою","x":185,"y":460,"description":"CHF 3.50 у грі. Тепла чашка додасть сил. Один раз за цю пригоду.","actions":["buy_coffee"]},
   29 |         {"id":"station","title":"Назад до станції","x":85,"y":605,"description":"Якщо щось залишилося на пероні, ще можна повернутися.","actions":["back_station"]},
   30 |         {"id":"bench","title":"Лавка біля озера","x":350,"y":625,"description":"Можна перевести подих перед дорогою.","actions":["catch_breath"]}
   31 |       ]
   32 |     },
   33 |     "altstadt": {
   34 |       "title":"Altstadt", "subtitle":"Бруківка · вікна над Лімматом", "chapter":"03 / СТАРЕ МІСТО",
   35 |       "description":"Теплі вікна дивляться на річку. Майстерня Ади — за зеленими дверима. На лавці сидить веломеханік із коробкою кабелів.",
   36 |       "spawn":[290,595],
   37 |       "hotspots":[
   38 |         {"id":"mechanic","title":"Веломеханік Ніко","x":395,"y":515,"description":"Загублений кабель не має зупиняти цілу історію. Ніко може позичити запасний, якщо допомогти прибрати інструменти.","actions":["borrow_cable"]},
   39 |         {"id":"atelier","title":"Зелені двері майстерні","x":925,"y":440,"description":"На дверях маленька табличка: «Ада. Прототипи, які працюють». Зустріч о 19:30.","actions":["enter_atelier"]},
   40 |         {"id":"bridge","title":"Міст до Bellevue","x":120,"y":575,"description":"Пішки назад до трамвайного кільця.","actions":["back_bellevue"]},
   41 |         {"id":"view","title":"Зупинитися біля води","x":650,"y":625,"description":"П’ять хвилин тиші додадуть трохи сил. Зустріч не чекатиме вічно.","actions":["river_rest"]}
   42 |       ]
   43 |     },
   44 |     "atelier": {
   45 |       "title":"Майстерня Ади", "subtitle":"Один стіл · один чесний показ", "chapter":"04 / ЗУСТРІЧ",
   46 |       "description":"Лампа освітлює дерев’яний стіл. Ада закриває блокнот: «Покажи, що вже працює». Можна перевірити прототип і чесно пояснити його межі.",
   47 |       "spawn":[430,600],
   48 |       "hotspots":[
   49 |         {"id":"ada","title":"Ада","x":890,"y":475,"description":"Спершу познайомся, потім покажи демо. Розмова не є продажем; гроші за цей показ не нараховуються.","actions":["meet_ada","present_demo","present_honest"]},
   50 |         {"id":"desk","title":"Робочий стіл","x":580,"y":510,"description":"Під’єднай кабель і перевір прототип перед показом. Потрібно трохи сил.","actions":["test_demo"]},
   51 |         {"id":"chair","title":"Крісло біля лампи","x":230,"y":520,"description":"Можна перевести подих. Відпочинок коштує шість хвилин і повертає сили.","actions":["atelier_rest"]},
   52 |         {"id":"door","title":"Назад у старе місто","x":1110,"y":500,"description":"Можна повернутися за кабелем чи просто ще трохи пройтися.","actions":["leave_atelier"]}
   53 |       ]
   54 |     }
   55 |   },
   56 |   "actions": {
   57 |     "catch_breath":{"label":"Перепочити · 6 хв","minutes":6,"energy":18,"note":"Шість хвилин на лавці. Дощ стихає, сили повертаються. Можна йти далі."},
   58 |     "read_board":{"label":"Прочитати квитанцію · 2 хв","minutes":2,"energy":-1,"once":"board_read","flag":"board_read","note":"Квитанція: камера C7, код 1942. Зустріч в Ади о 19:30. Це сценарні дані, не живий розклад SBB."},
   59 |     "open_locker":{"label":"Відкрити C7","minutes":2,"energy":-1,"once":"locker_open","code":"1942","item":"cable","flag":"locker_open","note":"Замок клацнув. Запасний кабель повернувся до рюкзака."},
   60 |     "to_bellevue":{"label":"Піднятися сходами · 3 хв","minutes":3,"energy":-3,"to":"bellevue","note":"Арки лишилися позаду. Перед тобою Bellevue."},
   61 |     "buy_ticket":{"label":"Купити квиток · CHF 4.40 · 2 хв","minutes":2,"energy":0,"cost":440,"item":"ticket","once":"ticket_owned","flag":"ticket_owned","note":"Квиток у кишені. Це лише ігрова покупка."},
   62 |     "help_musician":{"label":"Допомогти з нотами · 5 хв","minutes":5,"energy":-3,"item":"ticket","once":"helped_musician","flag":"helped_musician","note":"Музикант дякує і віддає запасний денний квиток. Інколи місто відповідає взаємністю."},
   63 |     "take_tram":{"label":"Сісти на трамвай · 5 хв","minutes":5,"energy":-1,"requires_item":"ticket","to":"altstadt","note":"Трамвай ковзає крізь дощ. За вікном — старе місто."},
   64 |     "walk_altstadt":{"label":"Піти пішки · 12 хв","minutes":12,"energy":-10,"to":"altstadt","note":"Ти йдеш уздовж Ліммату. Від води тягне прохолодою, у вікнах запалюються вогні."},
   65 |     "buy_coffee":{"label":"Взяти каву · CHF 3.50 · 3 хв","minutes":3,"energy":18,"cost":350,"once":"coffee_bought","flag":"coffee_bought","note":"Тепла чашка й хвилина без поспіху. Сили трохи повернулися."},
   66 |     "back_station":{"label":"Спуститися до станції · 3 хв","minutes":3,"energy":-2,"to":"stadelhofen","note":"Ти знову на пероні Stadelhofen."},
   67 |     "borrow_cable":{"label":"Допомогти Ніко й позичити кабель · 5 хв","minutes":5,"energy":-2,"item":"cable","once":"borrowed_cable","flag":"borrowed_cable","note":"Інструменти на місці. Ніко позичає кабель: «Повернеш наступного разу»."},
   68 |     "enter_atelier":{"label":"Зайти до майстерні · 2 хв","minutes":2,"energy":-1,"to":"atelier","note":"Зелені двері відчиняються. Ада чекає біля столу."},
   69 |     "back_bellevue":{"label":"Повернутися до Bellevue · 12 хв","minutes":12,"energy":-8,"to":"bellevue","note":"Міст виводить тебе назад до трамвайного кільця."},
   70 |     "river_rest":{"label":"Посидіти біля води · 5 хв","minutes":5,"energy":12,"note":"Кола дощу на воді. Думки стають тихішими."},
   71 |     "meet_ada":{"label":"Познайомитися з Адою · 2 хв","minutes":2,"energy":-1,"once":"met_ada","flag":"met_ada","note":"«Я Ада. Мені цікава твоя ідея. Почнімо з того, що можна перевірити»."},
   72 |     "test_demo":{"label":"Під’єднати й перевірити демо · 4 хв","minutes":4,"energy":-8,"requires_item":"cable","requires_energy":12,"once":"demo_tested","flag":"demo_tested","note":"Кабель під’єднано. Прототип пройшов локальну перевірку. Тепер є що показати."},
   73 |     "present_demo":{"label":"Показати перевірений прототип · 3 хв","minutes":3,"energy":-3,"requires_flags":["met_ada","demo_tested"],"ending":"demo","note":"Ти показуєш працююче демо й називаєш його межі. Ада ставить змістовні запитання."},
   74 |     "present_honest":{"label":"Чесно попросити про другу зустріч · 2 хв","minutes":2,"energy":0,"requires_flags":["met_ada"],"ending":"honest","note":"«Сьогодні я не готовий показати перевірений результат». Ада погоджується перенести розмову. Це теж рішення."},
   75 |     "atelier_rest":{"label":"Перевести подих · 6 хв","minutes":6,"energy":18,"note":"Ти сідаєш біля лампи. Тепло повертається до пальців."},
   76 |     "leave_atelier":{"label":"Вийти в Altstadt · 2 хв","minutes":2,"energy":-1,"to":"altstadt","note":"Ти виходиш на мокру бруківку."}
   77 |   },
   78 |   "items": {
   79 |     "prototype":{"name":"Прототип","description":"Локальне демо в рюкзаку. Для перевірки потрібен кабель."},
   80 |     "cable":{"name":"Кабель USB-C","description":"Підходить до ноутбука в майстерні."},
   81 |     "ticket":{"name":"Денний квиток","description":"Ігровий проїзний цієї глави. Жодних реальних поїздок чи платежів."}
   82 |   }
   83 | }
````

## scripts/serve_argon.py

Original bytes: 6154; SHA256: `f89c93eae2e6268e44fca06bd97ac86a59f1f3e18a64141b2f9923dbec8a7cb9`. Original source line numbers follow.

````text
    1 | """Loopback-only Argon adventure. No model, payment, or shell execution routes."""
    2 | import argparse
    3 | from http.cookies import SimpleCookie
    4 | from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    5 | import hmac
    6 | import json
    7 | from pathlib import Path
    8 | import secrets
    9 | import sys
   10 | from urllib.parse import urlsplit
   11 |
   12 | ROOT = Path(__file__).resolve().parents[1]
   13 | sys.path.insert(0, str(ROOT/'argon-game'))
   14 | from game import Game
   15 |
   16 | STATIC = {'/':'index.html', '/app.mjs':'app.mjs', '/client.mjs':'client.mjs', '/styles.css':'styles.css'}
   17 | ART_NAMES = {'sky.png':'L0_zurich_twilight_sky.png', 'station.png':'L1_stadelhofen_calatrava_arches.png',
   18 |              'train.png':'L2_swiss_sbb_train_parallax.png'}
   19 |
   20 |
   21 | class Handler(BaseHTTPRequestHandler):
   22 |     protocol_version = 'HTTP/1.1'
   23 |
   24 |     def log_message(self, *_): pass
   25 |
   26 |     def setup(self):
   27 |         super().setup()
   28 |         self.connection.settimeout(5)
   29 |
   30 |     def end_headers(self):
   31 |         self.send_header('Cache-Control','no-store')
   32 |         self.send_header('Referrer-Policy','no-referrer')
   33 |         self.send_header('X-Content-Type-Options','nosniff')
   34 |         self.send_header('Content-Security-Policy',"default-src 'self'; connect-src 'self'; img-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
   35 |         super().end_headers()
   36 |
   37 |     def valid_origin(self):
   38 |         host = f'127.0.0.1:{self.server.server_port}'
   39 |         return self.headers.get('Host') == host and self.headers.get('Origin') in {None,'http://'+host} and self.headers.get('Sec-Fetch-Site') != 'cross-site'
   40 |
   41 |     def authenticated(self):
   42 |         return hmac.compare_digest(self.headers.get('Authorization','').removeprefix('Bearer '), self.server.token)
   43 |
   44 |     def send_data(self, status, data, content_type='application/json; charset=utf-8', cookie=False):
   45 |         if not isinstance(data,bytes): data=json.dumps(data,ensure_ascii=False,allow_nan=False).encode('utf-8')
   46 |         self.send_response(status)
   47 |         self.send_header('Content-Type',content_type)
   48 |         self.send_header('Content-Length',str(len(data)))
   49 |         if cookie: self.send_header('Set-Cookie',f'argon={self.server.token}; HttpOnly; SameSite=Strict; Path=/api')
   50 |         self.end_headers()
   51 |         if self.command != 'HEAD': self.wfile.write(data)
   52 |
   53 |     def do_HEAD(self): self.do_GET()
   54 |
   55 |     def do_GET(self):
   56 |         if not self.valid_origin(): self.send_data(403,{'error':'ORIGIN_REJECTED'}); return
   57 |         path=urlsplit(self.path).path
   58 |         if path == '/api/session': self.send_data(200,{'token':self.server.token},cookie=True); return
   59 |         if path == '/api/state':
   60 |             cookie=SimpleCookie()
   61 |             try: cookie.load(self.headers.get('Cookie',''))
   62 |             except Exception: pass
   63 |             valid_cookie = 'argon' in cookie and hmac.compare_digest(cookie['argon'].value,self.server.token)
   64 |             if not self.authenticated() and not valid_cookie: self.send_data(401,{'error':'AUTH_REQUIRED'}); return
   65 |             with self.server.game.store.lock: self.send_data(200,self.server.game.view())
   66 |             return
   67 |         if path in STATIC:
   68 |             file=ROOT/'argon-game'/STATIC[path]
   69 |             self.send_data(200,file.read_bytes(),{'.html':'text/html; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}[file.suffix]); return
   70 |         if path=='/mcp-bridge/command-queue.mjs':
   71 |             self.send_data(200,(ROOT/'mcp-bridge/command-queue.mjs').read_bytes(),'text/javascript; charset=utf-8'); return
   72 |         if path.startswith('/art/') and path[5:] in ART_NAMES and self.server.art_dir:
   73 |             file=self.server.art_dir/ART_NAMES[path[5:]]
   74 |             if file.is_file(): self.send_data(200,file.read_bytes(),'image/png'); return
   75 |         self.send_data(404,{'error':'NOT_FOUND'})
   76 |
   77 |     def do_POST(self):
   78 |         if not self.valid_origin(): self.send_data(403,{'error':'ORIGIN_REJECTED'}); return
   79 |         if not self.authenticated(): self.send_data(401,{'error':'AUTH_REQUIRED'}); return
   80 |         if self.path != '/api/action': self.send_data(404,{'error':'NOT_FOUND'}); return
   81 |         try:
   82 |             length=int(self.headers.get('Content-Length','0'))
   83 |             if not 0 < length <= 8192 or self.headers.get('Content-Type','').split(';')[0] != 'application/json': raise ValueError('JSON_REQUIRED')
   84 |             body=json.loads(self.rfile.read(length))
   85 |             if not isinstance(body,dict) or set(body) not in ({'action','payload','request_id'}, {'action','payload','request_id','expected_revision'}): raise ValueError('INVALID_REQUEST')
   86 |             with self.server.game.store.lock:
   87 |                 result=self.server.game.command(body['action'],body['payload'],body['request_id'],body.get('expected_revision'))
   88 |                 self.send_data(200,{'result':result,**self.server.game.view()})
   89 |         except (ValueError,TypeError,KeyError) as error:
   90 |             if str(error)=='REVISION_CONFLICT':
   91 |                 with self.server.game.store.lock: self.send_data(409,{'error':'REVISION_CONFLICT',**self.server.game.view()})
   92 |             else:self.send_data(400,{'error':str(error)})
   93 |         except OSError: self.send_data(503,{'error':'Збереження недоступне. Дію не підтверджено.'})
   94 |
   95 |
   96 | class Server(ThreadingHTTPServer):
   97 |     daemon_threads=True
   98 |
   99 |     def __init__(self,port=4532,directory=None,art_dir=None):
  100 |         self.token=secrets.token_urlsafe(32)
  101 |         self.art_dir=Path(art_dir).resolve() if art_dir else None
  102 |         self.game=Game(directory or ROOT/'.runtime/argon')
  103 |         try: super().__init__(('127.0.0.1',port),Handler)
  104 |         except Exception: self.game.close(); raise
  105 |
  106 |     def server_close(self):
  107 |         super().server_close(); self.game.close()
  108 |
  109 |
  110 | if __name__ == '__main__':
  111 |     parser=argparse.ArgumentParser()
  112 |     parser.add_argument('--port',type=int,default=4532)
  113 |     parser.add_argument('--state-dir',type=Path)
  114 |     parser.add_argument('--art-dir',type=Path)
  115 |     args=parser.parse_args()
  116 |     server=Server(args.port,args.state_dir,args.art_dir)
  117 |     print(f'Argon: http://127.0.0.1:{server.server_port}/',flush=True)
  118 |     try: server.serve_forever()
  119 |     except KeyboardInterrupt: pass
  120 |     finally: server.server_close()
````

## argon-game/client.mjs

Original bytes: 480; SHA256: `67835067629643d8e87c8e0e0f317417c63368034c33a707e55edb5926bec1cd`. Original source line numbers follow.

````text
    1 | import {createDurableQueue} from '../mcp-bridge/command-queue.mjs';
    2 |
    3 | export function wasDemoShown(state){
    4 |   return state.flags.includes('demo_tested')&&['prepared','late'].includes(state.ending?.id);
    5 | }
    6 |
    7 | export function createCommandQueue({send,storage,uuid=()=>crypto.randomUUID()}){
    8 |   return createDurableQueue({send,storage,uuid,key:'argon.pending.v1',
    9 |     acknowledged:(response,pending)=>response?.result?.accepted===true&&response.result.request_id===pending.request_id});
   10 | }
````
