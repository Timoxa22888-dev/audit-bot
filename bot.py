import requests
import sys
import json
import datetime
import random
from urllib.parse import quote
from flask import Flask, request

# ================== НАСТРОЙКИ ==================
TOKEN = "8740332033:AAHXnZCgloGusWCfYL1zGcvnJ53qKCYGX6Y"
DEEPSEEK_API_KEY = "sk-or-vv-062b0f07999bd3e3cb63eeccd14126b29f15a3db67c6d1d65f52c55bd8947c9b"
DEEPSEEK_API_URL = "https://api.vsegpt.ru/v1/chat/completions"

# ================== НАСТРОЙКИ ЮMONEY ==================
YOMONEY_WALLET = "4100119525696193"
YOMONEY_TOKEN = "EA6F3B9DB57E37786624F962477F79D06F32148DFFF66EF7D241637B718CA1968F10CAB9FD5D6062E43A2F7AB61AA8072C6ED0C217EE8C5FE30ECE5F4EA7E854FBAD04AAC15DFEF138BD1A3B105CA662A62BE629E419C48FB6CF5F0DB7E7639545BEE3EFD9B13DFB579E1D4AEB043E64B7D56AA8B25DABC4955C37489C6015B2"
YOMONEY_PRICE_BASIC = 1500
YOMONEY_PRICE_PREMIUM = 3000
SUCCESS_URL = "https://t.me/auditsforypubot"

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"
USERNAME = "t1mmyyyy"

# ================== ХРАНИЛИЩА ==================
user_tariffs = {}
user_orders = {}
referral_discounts = {}
used_tips = set()  # отслеживание выданных советов

# Загрузка данных
for fname, container in [
    ("orders.txt", user_orders),
    ("referral_discounts.txt", referral_discounts),
]:
    try:
        with open(f"/home/{USERNAME}/{fname}", "r") as f:
            for line in f:
                k, v = line.strip().split(":")
                container[int(k)] = int(v)
    except:
        pass

subscribers = set()
try:
    with open(f"/home/{USERNAME}/subscribers.txt", "r") as f:
        for line in f:
            subscribers.add(int(line.strip()))
except:
    pass

referrals = {}
try:
    with open(f"/home/{USERNAME}/referrals.txt", "r") as f:
        for line in f:
            a, b = line.strip().split(":")
            referrals[int(a)] = int(b)
except:
    pass

# Загружаем историю выданных советов
try:
    with open(f"/home/{USERNAME}/used_tips.txt", "r") as f:
        for line in f:
            used_tips.add(int(line.strip()))
except:
    pass

# ================== ПРОМТЫ ==================
SYSTEM_PROMPT_TEST = """Представь, что ты опытный контент-маркетолог и психолог. Проведи краткий аудит визуала блога по ссылке ниже.

Дай 3 конкретных совета:
- Что улучшить в цветах и шрифтах
- Как сделать обложки заметнее
- Как повысить качество фото

Пиши коротко, без воды, с одним примером к каждому совету."""

SYSTEM_PROMPT_BASIC = """Представь, что ты опытный контент-маркетолог и психолог. Проведи профессиональный аудит блога по ссылке ниже.

Проанализируй строго по этой структуре и дай конкретные рекомендации с примерами:

1. Визуал: 3 быстрых совета, как улучшить визуальное оформление.
2. Контент: 3 конкретные темы постов с примерами заголовков.
3. Продажи: 2 идеи, как мягко подвести подписчиков к покупке консультации.
4. Сторис: 2 идеи для интерактивных сторис.
5. Короткий итог: самое слабое место блога и главная точка роста.

Формат: каждый пункт с заголовком, без общих фраз, только применимое на практике."""

SYSTEM_PROMPT_PREMIUM = """Представь, что ты опытный контент-маркетолог и психолог. Проведи углубленный аудит блога по ссылке ниже.

Проанализируй строго по этой структуре и дай конкретные рекомендации с примерами:

1. Визуал: 3 совета по улучшению визуала. Плюс одна личная рекомендация по стилю (палитра, настроение, референс).
2. Контент: 5 тем постов с примерами заголовков. Плюс 3 идеи для Reels с кратким сценарием каждой.
3. Продажи: 3 идеи для мягкого прогрева к покупке консультации с примерами. Плюс пример продающего поста.
4. Сторис: 3 идеи для интерактивных сторис с конкретными темами опросов и викторин.
5. Контент-план на 5 дней: темы постов с описанием и целью каждого.
6. Бонус: 5 идей для видео Reels с примерами сценариев.
7. Итог: главная точка роста и пошаговый план действий на 14 дней.

Формат: каждый пункт с заголовком, без воды, с практическими примерами."""

# ================== БАНК СОВЕТОВ (30 штук) ==================
ALL_TIPS = [
    "💡 Постите сторис с вопросом — вовлечённость +30%.",
    "💡 Используйте 2-3 цвета в визуале — блог выглядит профессионально.",
    "💡 Публикуйте кейсы клиентов — это лучший способ продавать.",
    "💡 В Reels показывайте процесс работы — это вызывает доверие.",
    "💡 Отвечайте на комментарии в первый час — алгоритмы это любят.",
    "💡 Делайте анонсы в сторис перед выходом поста.",
    "💡 Хештеги по теме: не более 5-7 штук на пост.",
    "💡 Видео длиной 7-15 секунд залетают лучше всего.",
    "💡 Задавайте вопросы в конце поста — комментарии растут.",
    "💡 Публикуйте фото себя — люди покупают у людей.",
    "💡 Делитесь личными историями — это сближает.",
    "💡 Используйте Reels для ответов на вопросы подписчиков.",
    "💡 Один пост = одна мысль. Не перегружайте.",
    "💡 Заголовок должен цеплять за 2 секунды.",
    "💡 Публикуйте «закулисье» — подписчики это обожают.",
    "💡 Проводите прямые эфиры раз в неделю.",
    "💡 Делитесь списками: «10 книг», «5 техник», «3 ошибки».",
    "💡 Используйте эмодзи, но не перебарщивайте.",
    "💡 Сторис с текстом работают лучше, чем просто фото.",
    "💡 Публикуйте отзывы клиентов в разных форматах.",
    "💡 Визуал должен быть единым: шрифты, цвета, фильтры.",
    "💡 Используйте CTA в конце каждого поста.",
    "💡 Тестируйте время публикаций — найдите своё окно.",
    "💡 Подкасты и голосовые сообщения набирают популярность.",
    "💡 Не бойтесь показывать неудачи — это делает вас живым.",
    "💡 Используйте UGC-контент (контент от подписчиков).",
    "💡 Обложки Reels должны быть яркими и контрастными.",
    "💡 Делайте коллаборации с коллегами.",
    "💡 Публикуйте регулярно, но не жертвуйте качеством.",
    "💡 Следите за трендами, но сохраняйте свой стиль.",
]


def get_unique_tip(chat_id):
    """Выдаёт совет, который ещё не получал этот пользователь."""
    available = [t for i, t in enumerate(ALL_TIPS) if i not in used_tips]
    if not available:
        # Если все советы кончились — сбрасываем
        used_tips.clear()
        available = ALL_TIPS[:]
    tip = random.choice(available)
    tip_index = ALL_TIPS.index(tip)
    used_tips.add(tip_index)
    # Сохраняем
    with open(f"/home/{USERNAME}/used_tips.txt", "w") as f:
        for idx in used_tips:
            f.write(f"{idx}\n")
    return tip


# ================== ОТПРАВКА СООБЩЕНИЙ ==================

def api_call(method, data):
    try:
        r = requests.post(f"{TELEGRAM_API}/{method}", data=data, timeout=10)
        return r.json()
    except Exception as e:
        print(f"Ошибка API {method}: {e}")
        return {"ok": False}


def send_message(chat_id, text, **kwargs):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", **kwargs}
    return api_call("sendMessage", data)


def edit_message(chat_id, message_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    return api_call("editMessageText", data)


def answer_callback(callback_id):
    api_call("answerCallbackQuery", {"callback_query_id": callback_id})


# ================== КЛАВИАТУРЫ ==================

def main_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "💰 Цены и тарифы", "callback_data": "menu_price"}],
            [{"text": "🎁 Реферальная программа", "callback_data": "menu_ref"}],
            [{"text": "💡 Совет дня", "callback_data": "menu_tips"}],
            [{"text": "ℹ️ О сервисе", "callback_data": "menu_about"}],
        ]
    }


def back_button():
    return {"inline_keyboard": [[{"text": "◀️ Назад в меню", "callback_data": "menu_back"}]]}


# ================== БИЗНЕС-ЛОГИКА ==================

def analyze_with_deepseek(blog_link, tariff):
    prompts = {"test": SYSTEM_PROMPT_TEST, "basic": SYSTEM_PROMPT_BASIC, "premium": SYSTEM_PROMPT_PREMIUM}
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "system", "content": prompts.get(tariff, SYSTEM_PROMPT_BASIC)},
            {"role": "user", "content": f"Проанализируй этот блог: {blog_link}"}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }
    r = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=90)
    if r.status_code != 200:
        raise Exception(f"DeepSeek вернул {r.status_code}: {r.text}")
    return r.json()["choices"][0]["message"]["content"]


def generate_payment_link(chat_id, amount, description="Аудит блога"):
    params = {
        "receiver": YOMONEY_WALLET, "quickpay-form": "shop",
        "targets": description, "sum": amount,
        "label": str(chat_id), "successURL": SUCCESS_URL
    }
    return "https://yoomoney.ru/quickpay/confirm.xml?" + "&".join(f"{k}={quote(str(v))}" for k, v in params.items())


def check_payment(chat_id, amount):
    try:
        r = requests.get("https://yoomoney.ru/api/operation-history", headers={
            "Authorization": f"Bearer {YOMONEY_TOKEN}", "Content-Type": "application/json"
        }, params={"records": 10, "type": "deposition", "label": str(chat_id)}, timeout=10)
        for op in r.json().get("operations", []):
            if op.get("amount", 0) == amount and str(chat_id) in str(op.get("label", "")):
                return True
    except Exception as e:
        print(f"Ошибка проверки платежа: {e}")
    return False


def generate_referral_link(chat_id):
    return f"https://t.me/auditsforypubot?start=ref{str(chat_id).encode('utf-8').hex()}"


def save_audit_date(chat_id):
    with open(f"/home/{USERNAME}/audit_dates.txt", "a") as f:
        f.write(f"{chat_id}:{datetime.date.today()}\n")


def save_data(fname, container):
    with open(f"/home/{USERNAME}/{fname}", "w") as f:
        for k, v in container.items():
            f.write(f"{k}:{v}\n")


def calculate_discount(chat_id, price):
    # Реферальная скидка (20% — одноразовая)
    if referral_discounts.get(chat_id, 0) > 0:
        referral_discounts[chat_id] -= 1
        save_data("referral_discounts.txt", referral_discounts)
        return int(price * 0.2), "реферальная (20%)"
    # Скидка постоянного клиента (10% — после 2-й покупки)
    if user_orders.get(chat_id, 0) >= 2:
        return int(price * 0.1), "постоянного клиента (10%)"
    return 0, ""


# ================== ОБРАБОТЧИК СООБЩЕНИЙ ==================

def handle_message(chat_id, text):
    print(f"\n📩 Сообщение от {chat_id}: {text}")

    # --- START ----------------------------------------------------------------
    if text == "/start":
        subscribers.add(chat_id)
        save_data("subscribers.txt", {s: 1 for s in subscribers})
        send_message(chat_id,
            "👋 <b>Привет! Я «ТочкаРоста» — AI-аудитор блогов.</b>\n\n"
            "Я анализирую блоги экспертов с помощью нейросетей "
            "и даю конкретные рекомендации по улучшению.\n\n"
            "🔹 <b>Что я умею:</b>\n"
            "• Анализировать визуал и оформление\n"
            "• Подбирать темы для постов и сторис\n"
            "• Находить слабые места и точки роста\n"
            "• Составлять контент-план и сценарии для Reels\n\n"
            "Нажмите кнопку ниже, чтобы открыть меню и выбрать тариф 👇",
            reply_markup=json.dumps({"inline_keyboard": [[{"text": "📋 Главное меню", "callback_data": "menu_back"}]]})
        )
        return

    # --- /menu ----------------------------------------------------------------
    if text == "/menu":
        send_message(chat_id, "📋 <b>Главное меню</b>\n\nВыберите раздел:", reply_markup=json.dumps(main_menu_keyboard()))
        return

    # --- Тестовый deep‑link --------------------------------------------------
    if text and ("/start test" in text or "?start=test" in text):
        user_tariffs[chat_id] = "test"
        send_message(chat_id, "🆓 <b>Тестовый тариф активирован!</b>\n\nОтправьте ссылку на блог — проанализирую визуал.")
        return

    # --- Реферальный deep‑link -----------------------------------------------
    if text and "?start=ref" in text:
        try:
            inviter = int(bytes.fromhex(text.split("ref")[-1]).decode('utf-8'))
            if inviter != chat_id:
                referrals[chat_id] = inviter
                save_data("referrals.txt", referrals)
                referral_discounts[inviter] = referral_discounts.get(inviter, 0) + 1
                save_data("referral_discounts.txt", referral_discounts)
                send_message(chat_id, "🎉 <b>Вы перешли по реферальной ссылке!</b>\n\nВы и ваш друг получите скидку 20% на следующий аудит.")
                send_message(inviter, "🎉 <b>По вашей ссылке перешёл новый пользователь!</b>\n\nВы получили скидку 20%.")
        except:
            pass
        send_message(chat_id, "👋 <b>Добро пожаловать в «ТочкаРоста»!</b>\n\nНажмите кнопку ниже, чтобы открыть меню.",
                     reply_markup=json.dumps({"inline_keyboard": [[{"text": "📋 Главное меню", "callback_data": "menu_back"}]]}))
        return

    # --- /ref -----------------------------------------------------------------
    if text == "/ref":
        send_message(chat_id,
            f"🎁 <b>Реферальная программа</b>\n\n"
            f"Пригласите друга — оба получите скидку 20%!\n\n"
            f"🔗 Ваша ссылка: {generate_referral_link(chat_id)}",
            reply_markup=json.dumps(back_button()))
        return

    # --- Только ссылки -------------------------------------------------------
    if not text.startswith("http"):
        if "yoomoney.ru" not in text:
            send_message(chat_id, "❌ Отправьте ссылку на блог, начинающуюся с http:// или https://\n\n/menu — главное меню.")
        return

    # --- АНАЛИЗ --------------------------------------------------------------
    tariff = user_tariffs.pop(chat_id, "basic")

    if tariff == "test":
        send_message(chat_id, "⏳ Анализирую (тестовый тариф)...")
        try:
            answer = analyze_with_deepseek(text, "test")
            for part in [answer[i:i+4000] for i in range(0, len(answer), 4000)]:
                send_message(chat_id, part)
            save_audit_date(chat_id)
            link = generate_payment_link(chat_id, YOMONEY_PRICE_BASIC, "Базовый аудит блога")
            send_message(chat_id, "✨ <b>Понравился результат?</b>\n\nВ полном аудите — разбор по 5 пунктам.",
                         reply_markup=json.dumps({"inline_keyboard": [[{"text": f"📋 Базовый за {YOMONEY_PRICE_BASIC} ₽", "url": link}]]}))
        except Exception as e:
            send_message(chat_id, f"❌ Ошибка: {e}")
        return

    # Платные тарифы
    t_name = {"basic": ("Базовый", YOMONEY_PRICE_BASIC), "premium": ("Расширенный", YOMONEY_PRICE_PREMIUM)}.get(tariff, ("Базовый", YOMONEY_PRICE_BASIC))
    price = t_name[1]
    discount, reason = calculate_discount(chat_id, price)
    final_price = price - discount

    if discount:
        send_message(chat_id, f"🎉 Скидка ({reason}): <b>{discount} ₽</b>")

    send_message(chat_id, f"⏳ Проверяю оплату (тариф: {t_name[0]})...")
    if check_payment(chat_id, final_price):
        send_message(chat_id, "✅ Оплата найдена! Начинаю анализ...")
        try:
            answer = analyze_with_deepseek(text, tariff)
            for part in [answer[i:i+4000] for i in range(0, len(answer), 4000)]:
                send_message(chat_id, part)

            user_orders[chat_id] = user_orders.get(chat_id, 0) + 1
            save_data("orders.txt", user_orders)
            save_audit_date(chat_id)

            # Информируем о статусе скидки
            orders_count = user_orders[chat_id]
            if orders_count == 1:
                send_message(chat_id, "📊 <b>Статус скидки:</b> у вас 1 покупка. После второй покупки вы получите скидку 10% как постоянный клиент!")
            elif orders_count == 2:
                send_message(chat_id, "🎉 <b>Поздравляем!</b> Вы достигли статуса постоянного клиента! Со следующей покупки действует скидка 10%.")
            else:
                send_message(chat_id, f"🎉 <b>Вы постоянный клиент!</b> У вас {orders_count} покупок. Скидка 10% действует на все последующие аудиты.")

            send_message(chat_id, "💡 Через 14 дней после внедрения рекомендаций стоит провести повторный аудит.")
        except Exception as e:
            send_message(chat_id, f"❌ Ошибка: {e}")
    else:
        link = generate_payment_link(chat_id, final_price, f"{t_name[0]} аудит блога")
        send_message(chat_id, f"❌ Оплата не найдена.\nОплатите {final_price} ₽ по кнопке ниже и снова отправьте ссылку.",
                     reply_markup=json.dumps({"inline_keyboard": [[{"text": f"💳 Оплатить {final_price} ₽", "url": link}]]}))


# ================== FLASK-ВЕБХУК ==================

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        data = request.get_json()

        # --- CALLBACK-QUERY --------------------------------------------------
        if "callback_query" in data:
            cb = data["callback_query"]
            chat_id = cb["message"]["chat"]["id"]
            msg_id = cb["message"]["message_id"]
            d = cb["data"]
            answer_callback(cb["id"])

            if d == "menu_price":
                text = (
                    "💰 <b>Цены и тарифы</b>\n\n"
                    "Выберите подходящий вариант:\n\n"
                    f"🆓 <b>Тестовый</b> — <b>бесплатно</b>\n"
                    "• Анализ визуала: цвета, шрифты, обложки\n"
                    "• 3 конкретных совета\n\n"
                    f"📋 <b>Базовый</b> — <b>{YOMONEY_PRICE_BASIC} ₽</b>\n"
                    "• Полный аудит по 5 пунктам\n"
                    "• Темы для постов и сторис\n"
                    "• Стратегия продаж\n\n"
                    f"🚀 <b>Расширенный</b> — <b>{YOMONEY_PRICE_PREMIUM} ₽</b>\n"
                    "• Всё из базового\n"
                    "• Контент-план на 5 дней\n"
                    "• 5 идей для Reels со сценариями\n"
                    "• План действий на 14 дней\n\n"
                    "Выберите тариф:"
                )
                kb = {
                    "inline_keyboard": [
                        [{"text": f"🆓 Тестовый — бесплатно", "callback_data": "menu_test"}],
                        [{"text": f"📋 Базовый — {YOMONEY_PRICE_BASIC} ₽", "callback_data": "menu_basic"}],
                        [{"text": f"🚀 Расширенный — {YOMONEY_PRICE_PREMIUM} ₽", "callback_data": "menu_premium"}],
                        [{"text": "◀️ Назад в меню", "callback_data": "menu_back"}],
                    ]
                }
                edit_message(chat_id, msg_id, text, kb)
                return 'OK', 200

            if d == "menu_test":
                user_tariffs[chat_id] = "test"
                edit_message(chat_id, msg_id, "🆓 <b>Тестовый тариф активирован!</b>\n\nОтправьте ссылку на блог — проанализирую визуал.\n\n/menu — вернуться в меню.")
                return 'OK', 200

            if d == "menu_basic":
                text = (
                    f"📋 <b>Базовый аудит — {YOMONEY_PRICE_BASIC} ₽</b>\n\n"
                    "<b>Что входит:</b>\n"
                    "🔹 Аудит визуала (цвета, шрифты, обложки)\n"
                    "🔹 3 темы для постов с примерами заголовков\n"
                    "🔹 2 продающие механики для сторис\n"
                    "🔹 2 идеи для интерактивных сторис\n"
                    "🔹 Итог: слабое место и точка роста\n\n"
                    "<b>Как получить:</b>\n"
                    "1. Оплатите по кнопке ниже\n"
                    "2. Отправьте ссылку на блог\n"
                    "3. Получите полный разбор"
                )
                link = generate_payment_link(chat_id, YOMONEY_PRICE_BASIC, "Базовый аудит блога")
                kb = {
                    "inline_keyboard": [
                        [{"text": f"💳 Оплатить {YOMONEY_PRICE_BASIC} ₽", "url": link}],
                        [{"text": "◀️ Назад к тарифам", "callback_data": "menu_price"}],
                    ]
                }
                edit_message(chat_id, msg_id, text, kb)
                return 'OK', 200

            if d == "menu_premium":
                text = (
                    f"🚀 <b>Расширенный аудит — {YOMONEY_PRICE_PREMIUM} ₽</b>\n\n"
                    "<b>Всё из базового плюс:</b>\n"
                    "🔹 Личная рекомендация по стилю\n"
                    "🔹 5 тем для постов + 3 идеи для Reels\n"
                    "🔹 3 продающие механики + пример поста\n"
                    "🔹 Контент-план на 5 дней\n"
                    "🔹 5 идей для Reels со сценариями\n"
                    "🔹 Пошаговый план действий на 14 дней\n\n"
                    "<b>Как получить:</b>\n"
                    "1. Оплатите по кнопке ниже\n"
                    "2. Отправьте ссылку на блог\n"
                    "3. Получите расширенный разбор"
                )
                link = generate_payment_link(chat_id, YOMONEY_PRICE_PREMIUM, "Расширенный аудит блога")
                kb = {
                    "inline_keyboard": [
                        [{"text": f"💳 Оплатить {YOMONEY_PRICE_PREMIUM} ₽", "url": link}],
                        [{"text": "◀️ Назад к тарифам", "callback_data": "menu_price"}],
                    ]
                }
                edit_message(chat_id, msg_id, text, kb)
                return 'OK', 200

            if d == "menu_ref":
                text = (
                    "🎁 <b>Реферальная программа</b>\n\n"
                    "Пригласите друга — и вы оба получите <b>скидку 20%</b> на следующий аудит!\n\n"
                    f"🔗 <b>Ваша персональная ссылка:</b>\n{generate_referral_link(chat_id)}\n\n"
                    "Просто отправьте её другу. Когда он перейдёт по ссылке и запустит бота, "
                    "вы оба получите скидку."
                )
                edit_message(chat_id, msg_id, text, reply_markup=back_button())
                return 'OK', 200

            if d == "menu_tips":
                tip = get_unique_tip(chat_id)
                edit_message(chat_id, msg_id, f"💡 <b>Совет дня</b>\n\n{tip}", reply_markup=back_button())
                return 'OK', 200

            if d == "menu_about":
                text = (
                    "🤖 <b>О сервисе «ТочкаРоста»</b>\n\n"
                    "<b>Как это работает:</b>\n"
                    "1. Вы отправляете ссылку на свой блог\n"
                    "2. Нейросеть анализирует контент по десяткам параметров\n"
                    "3. Я формирую персональный отчёт с рекомендациями\n"
                    "4. Вы внедряете советы и растёте\n\n"
                    "<b>Почему это эффективно:</b>\n"
                    "• Нейросеть видит то, что упускает человеческий глаз\n"
                    "• Вы получаете объективный взгляд «со стороны»\n"
                    "• Рекомендации основаны на данных, а не на догадках\n"
                    "• Экономия времени: не нужно нанимать маркетолога\n\n"
                    "<b>Что анализируем:</b>\n"
                    "• Визуальное оформление и стиль\n"
                    "• Темы и качество контента\n"
                    "• Вовлечённость и активность подписчиков\n"
                    "• Продающие механики и прогрев\n\n"
                    "<b>Для кого:</b>\n"
                    "Психологов, коучей, репетиторов, экспертов и всех, "
                    "кто ведёт блог и хочет расти быстрее.\n\n"
                    "Используйте /menu для вызова главного меню."
                )
                edit_message(chat_id, msg_id, text, reply_markup=back_button())
                return 'OK', 200

            if d == "menu_back":
                edit_message(chat_id, msg_id,
                    "📋 <b>Главное меню</b>\n\nВыберите раздел:",
                    reply_markup=main_menu_keyboard())
                return 'OK', 200

            return 'OK', 200

        # --- ОБЫЧНЫЕ СООБЩЕНИЯ ------------------------------------------------
        if "message" in data:
            handle_message(data["message"]["chat"]["id"], data["message"].get("text", ""))
            return 'OK', 200

    return 'OK', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)