# bot.py
import telebot
from telebot import types
import json
import os
import time
import traceback

# ==========================
# ⚙️ Настройки — Вставь свой токен
# ==========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
print("TOKEN:", TOKEN)
if not TOKEN or ":" not in TOKEN:
    raise ValueError(f"Неверный токен: {TOKEN}")
ADMIN_ID = 279799183
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
RATES_FILE = os.path.join(BASE_DIR, "rates.json")
ADDRESSES_FILE = os.path.join(BASE_DIR, "addresses.json")
PAYMENTS_FILE = os.path.join(BASE_DIR, "payments.json")

# Карта и дефолтные адреса — использованы твои значения
DEFAULT_CARD = "5232441047703876"
DEFAULT_ADDRESSES = {
    "TRC20": "THakAHrPy5hbF33MSxgRQzYA4mFUj89NVx",
    "BEP20": "0xE3d656aDEf7D344e69F37a08bf535BD5BC8f32B5"
}

# ==========================
# Пути к JSON файлам (относительно скрипта)
# ==========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
RATES_FILE = os.path.join(BASE_DIR, "rates.json")
ADDRESSES_FILE = os.path.join(BASE_DIR, "addresses.json")
PAYMENTS_FILE = os.path.join(BASE_DIR, "payments.json")

# ==========================
# 🗂️ Работа с JSON (с безопасной записью)
# ==========================
def load_json(path, default):
    if not os.path.exists(path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[load_json] Ошибка создания {path}: {e}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default
    except Exception as e:
        print(f"[load_json] Ошибка чтения {path}: {e}")
        return default

def safe_save_json(data, path):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except OSError as e:
        # Если нет места на диске — логируем и продолжаем (чтобы бот не падал)
        print(f"[safe_save_json] Ошибка записи {path}: {e}")
        return False
    except Exception as e:
        print(f"[safe_save_json] Ошибка записи {path}: {e}")
        return False

# Утилиты для конкретных файлов
def load_rates():
    return load_json(RATES_FILE, {"usdt_to_uah": 41.2, "uah_to_usdt": 41.8})

def save_rates(rates):
    return safe_save_json(rates, RATES_FILE)

def load_addresses():
    return load_json(ADDRESSES_FILE, DEFAULT_ADDRESSES)

def save_addresses(addresses):
    return safe_save_json(addresses, ADDRESSES_FILE)

def load_users():
    return load_json(USERS_FILE, {})

def save_users(users):
    return safe_save_json(users, USERS_FILE)

def load_payments():
    return load_json(PAYMENTS_FILE, {})

def save_payments(payments):
    return safe_save_json(payments, PAYMENTS_FILE)

# ==========================
# 🤖 Инициализация бота
# ==========================
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# ==========================
# ✨ Тексты / Меню
# ==========================
WELCOME_TEXT = (
    "💱 *Добро пожаловать в A-Exchange* — быстрый и безопасный обмен USDT ⇄ Гривна 🇺🇦\n\n"
    "🔹 Моментальные выплаты на карту\n"
    "🔹 Надёжность и поддержка 24/7\n"
    "🔹 Лучшие курсы без скрытых комиссий\n\n"
    "Выберите направление обмена 👇"
)

HELP_CONTACT_TEXT = "Если нужна помощь — напиши админу: отправь сообщение сюда, мы ответим."

# Главное меню (Reply)
def main_menu_markup(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("💵 USDT → Гривна", "💳 Гривна → USDT")
    markup.add("📊 Курсы валют", "🆘 Поддержка")
    if user_id == ADMIN_ID:
        markup.add("⚙️ Админка")
    return markup

# Админ меню (Reply)
def admin_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📈 Установить курс (Продажа)", "📉 Установить курс (Покупка)")
    markup.add("💰 Просмотр текущих курсов", "🏦 Изменить адреса кошельков")
    markup.add("📋 Список заявок", "✅ Подтвердить/Отклонить")
    markup.add("🔙 В главное меню")
    return markup

# Кнопки для "я оплатил" у пользователя
def paid_confirm_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, one_time_keyboard=True)
    markup.add("✅ Я оплатил", "⬅️ Назад")
    return markup

# ==========================
# /start
# ==========================
@bot.message_handler(commands=["start"])
def cmd_start(message):
    users = load_users()
    uid = str(message.from_user.id)
    if uid not in users:
        users[uid] = {"username": message.from_user.username}
        save_users(users)
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=main_menu_markup(message.from_user.id))

# ==========================
# 📊 Просмотр курса (пользователь)
# ==========================
@bot.message_handler(func=lambda m: m.text == "📊 Курсы валют")
def user_show_rates(m):
    rates = load_rates()
    txt = f"📈 *Текущие курсы:*\n\n1 USDT → *{rates['usdt_to_uah']}* грн\n1 UAH → *{rates['uah_to_usdt']}* USDT"
    bot.send_message(m.chat.id, txt, reply_markup=main_menu_markup(m.from_user.id))

# ==========================
# 🆘 Поддержка
# ==========================
@bot.message_handler(func=lambda m: m.text == "🆘 Поддержка")
def user_support(m):
    bot.send_message(m.chat.id, HELP_CONTACT_TEXT, reply_markup=main_menu_markup(m.from_user.id))

# ==========================
# 💵 USDT → Гривна (flow)
# ==========================
@bot.message_handler(func=lambda m: m.text == "💵 USDT → Гривна")
def start_usdt_to_uah(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("TRC20", "BEP20", "⬅️ Назад")
    bot.send_message(m.chat.id, "Выберите сеть для перевода USDT:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["TRC20", "BEP20"])
def usdt_chosen_network(m):
    # Запоминаем выбор сети в локальной временной структуре через payments.json creation at amount step
    # Просим ввести карту куда пользователь хочет получить гривны
    bot.send_message(m.chat.id, "Введите номер вашей банковской карты для получения гривен:", reply_markup=types.ReplyKeyboardRemove())
    # Сохраняем network temporarily in file keyed by chat id with timestamp — но проще: we ask next and create payment after amount input.
    # We'll store network and card in short-lived file-less flow by using register_next_step_handler chain.
    bot.register_next_step_handler_by_chat_id(m.chat.id, lambda msg: _process_usdt_card(msg, m.text))

def _process_usdt_card(message, network):
    card = message.text.strip()
    # ask amount
    bot.send_message(message.chat.id, "Введите сумму в USDT для обмена:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler_by_chat_id(message.chat.id, lambda msg: _process_usdt_amount(msg, network, card))

def _process_usdt_amount(message, network, card):
    user_id = message.from_user.id
    text = message.text.strip().replace(",", ".")
    try:
        amount = float(text)
    except:
        bot.send_message(message.chat.id, "⚠️ Неверный формат суммы. Попробуйте ещё раз.", reply_markup=main_menu_markup(user_id))
        return

    rates = load_rates()
    addresses = load_addresses()
    rate = rates.get("usdt_to_uah", 0)
    address = addresses.get(network, "Адрес не найден")
    result = round(amount * rate, 2)

    # Создаём запись платежа
    payments = load_payments()
    payment_id = f"{user_id}_{int(time.time())}"
    payments[payment_id] = {
        "user_id": user_id,
        "username": message.from_user.username,
        "type": "USDT→UAH",
        "amount": amount,
        "result": result,
        "network": network,
        "address": address,
        "card": card,
        "status": "pending",
        "created_at": int(time.time())
    }
    if not save_payments(payments):
        bot.send_message(message.chat.id, "⚠️ Ошибка сохранения заявки (возможно, нет места на диске). Администратор уведомлен.", reply_markup=main_menu_markup(user_id))
    # Отправляем пользователю результат
    txt = (
        f"💵 *Результат конверсии:*\n"
        f"{amount:.2f} USDT = {result:.2f} грн.\n\n"
        f"📩 Отправьте USDT на адрес {network}:\n`{address}`\n\n"
        f"💳 Ваша карта для получения гривен: `{card}`\n\n"
        "После перевода нажмите кнопку *✅ Я оплатил*, чтобы уведомить администратора."
    )
    bot.send_message(message.chat.id, txt, parse_mode="Markdown", reply_markup=paid_confirm_markup())

    # Уведомление админу (кратко)
    admin_txt = (
        f"📢 *Новая заявка* {payment_id}\n"
        f"Пользователь: @{message.from_user.username or user_id} ({user_id})\n"
        f"Направление: USDT → UAH\n"
        f"Сеть: {network}\n"
        f"Сумма: {amount:.2f} USDT → {result:.2f} UAH\n"
        f"Карта: {card}"
    )
    bot.send_message(ADMIN_ID, admin_txt, parse_mode="Markdown")

# ==========================
# 💳 Гривна → USDT (flow)
# ==========================
@bot.message_handler(func=lambda m: m.text == "💳 Гривна → USDT")
def start_uah_to_usdt(m):
    bot.send_message(m.chat.id, f"Введите сумму в гривнах для покупки USDT:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler_by_chat_id(m.chat.id, _process_uah_amount)

def _process_uah_amount(message):
    user_id = message.from_user.id
    txt = message.text.strip().replace(",", ".")
    try:
        uah_amount = float(txt)
    except:
        bot.send_message(message.chat.id, "⚠️ Неверный формат суммы. Попробуйте ещё раз.", reply_markup=main_menu_markup(user_id))
        return

    # Показываем карту администратора (Банк)
    bot.send_message(message.chat.id, f"📤 Отправьте сумму на карту Банк: {DEFAULT_CARD}", reply_markup=types.ReplyKeyboardRemove())
    # Выбор сети
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("TRC20", "BEP20", "⬅️ Назад")
    bot.send_message(message.chat.id, "Выберите сеть для получения USDT:", reply_markup=markup)
    # Следующий шаг — ввод адреса USDT
    bot.register_next_step_handler_by_chat_id(message.chat.id, lambda m: _process_uah_network(m, uah_amount))

def _process_uah_network(message, uah_amount):
    network = message.text.strip()
    user_id = message.from_user.id
    bot.send_message(message.chat.id, "Введите ваш адрес USDT для получения:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler_by_chat_id(message.chat.id, lambda m: _process_uah_final(m, uah_amount, network))

def _process_uah_final(message, uah_amount, network):
    user_id = message.from_user.id
    address = message.text.strip()
    rates = load_rates()
    rate = rates.get("uah_to_usdt", 1)
    result = round(uah_amount / rate, 6)

    payments = load_payments()
    payment_id = f"{user_id}_{int(time.time())}"
    payments[payment_id] = {
        "user_id": user_id,
        "username": message.from_user.username,
        "type": "UAH→USDT",
        "uah_amount": uah_amount,
        "result": result,
        "network": network,
        "address": address,
        "status": "pending",
        "created_at": int(time.time())
    }
    if not save_payments(payments):
        bot.send_message(message.chat.id, "⚠️ Ошибка сохранения заявки (возможно, нет места на диске). Администратор уведомлен.", reply_markup=main_menu_markup(user_id))

    txt = (
        f"💰 *Результат конверсии:*\n"
        f"{uah_amount:.2f} грн = {result:.6f} USDT\n\n"
        f"📤 Отправьте UAH на карту Банк: `{DEFAULT_CARD}`\n\n"
        f"📩 Ваш адрес для получения USDT: `{address}`\n\n"
        "После перевода нажмите кнопку *✅ Я оплатил*, чтобы уведомить администратора."
    )
    bot.send_message(message.chat.id, txt, parse_mode="Markdown", reply_markup=paid_confirm_markup())

    # Уведомление админу
    admin_txt = (
        f"📢 *Новая заявка* {payment_id}\n"
        f"Пользователь: @{message.from_user.username or user_id} ({user_id})\n"
        f"Направление: UAH → USDT\n"
        f"Сеть: {network}\n"
        f"Сумма: {uah_amount:.2f} UAH → {result:.6f} USDT\n"
        f"Адрес: {address}"
    )
    bot.send_message(ADMIN_ID, admin_txt, parse_mode="Markdown")

# ==========================
# ✅ Я оплатил (пользователь) — уведомляем админа о платеже
# ==========================
@bot.message_handler(func=lambda m: m.text == "✅ Я оплатил")
def i_paid_handler(m):
    user_id = str(m.from_user.id)
    payments = load_payments()
    # Найдём последнюю pending заявку пользователя
    pending = [(pid, p) for pid, p in payments.items() if str(p.get("user_id")) == user_id and p.get("status") == "pending"]
    if not pending:
        bot.send_message(m.chat.id, "❗ У вас нет ожидающих заявок. Если вы уже оплатили — свяжитесь с администратором.", reply_markup=main_menu_markup(m.from_user.id))
        return
    # Берём самую последнюю по created_at
    pending.sort(key=lambda x: x[1].get("created_at", 0), reverse=True)
    pid, payment = pending[0]
    # Отправляем админу уведомление с inline-кнопками (подтвердить/отклонить)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{pid}"))
    markup.add(types.InlineKeyboardButton("🚫 Отклонить", callback_data=f"reject_{pid}"))
    admin_text = (
        f"🛎️ Пользователь @{m.from_user.username or m.from_user.id} ({m.from_user.id})\n"
        f"заявил оплату по заявке *{pid}*.\n"
        f"Направление: {payment.get('type')}\n"
        f"Сумма: {payment.get('amount', payment.get('uah_amount',''))}\n"
        f"Сеть: {payment.get('network')}\n"
        f"Адрес/Карта: {payment.get('address','')} / {payment.get('card','')}\n\n"
        f"Подтвердите или отклоните операцию."
    )
    bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown", reply_markup=markup)
    bot.send_message(m.chat.id, "✅ Мы уведомили администратора. После подтверждения вы получите сообщение.", reply_markup=main_menu_markup(m.from_user.id))

# ==========================
# ⚙️ Админ-панель (Reply handlers)
# ==========================
@bot.message_handler(func=lambda m: m.text == "⚙️ Админка")
def open_admin(m):
    if m.from_user.id != ADMIN_ID:
        bot.send_message(m.chat.id, "⛔ У тебя нет доступа.")
        return
    bot.send_message(m.chat.id, "👨‍💼 Панель администратора", reply_markup=admin_menu_markup())

@bot.message_handler(func=lambda m: m.text == "💰 Просмотр текущих курсов")
def admin_view_rates(m):
    if m.from_user.id != ADMIN_ID: return
    rates = load_rates()
    bot.send_message(m.chat.id, f"📈 Текущие курсы:\n1 USDT → {rates['usdt_to_uah']} грн\n1 UAH → {rates['uah_to_usdt']} USDT", reply_markup=admin_menu_markup())

@bot.message_handler(func=lambda m: m.text == "📈 Установить курс (Продажа)")
def admin_set_sell(m):
    if m.from_user.id != ADMIN_ID: return
    msg = bot.send_message(m.chat.id, "Введите новый курс *Продажа USDT* (USDT→UAH):")
    bot.register_next_step_handler(msg, _admin_save_sell_rate)

def _admin_save_sell_rate(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        val = float(message.text.replace(",", "."))
        rates = load_rates()
        rates["usdt_to_uah"] = val
        if save_rates(rates):
            bot.send_message(message.chat.id, f"✅ Курс Продажи обновлён: {val}", reply_markup=admin_menu_markup())
        else:
            bot.send_message(message.chat.id, f"⚠️ Не удалось сохранить курс (возможно, нет места на диске).", reply_markup=admin_menu_markup())
    except:
        bot.send_message(message.chat.id, "⚠️ Неверный формат числа.", reply_markup=admin_menu_markup())

@bot.message_handler(func=lambda m: m.text == "📉 Установить курс (Покупка)")
def admin_set_buy(m):
    if m.from_user.id != ADMIN_ID: return
    msg = bot.send_message(m.chat.id, "Введите новый курс *Покупка USDT* (UAH→USDT):")
    bot.register_next_step_handler(msg, _admin_save_buy_rate)

def _admin_save_buy_rate(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        val = float(message.text.replace(",", "."))
        rates = load_rates()
        rates["uah_to_usdt"] = val
        if save_rates(rates):
            bot.send_message(message.chat.id, f"✅ Курс Покупки обновлён: {val}", reply_markup=admin_menu_markup())
        else:
            bot.send_message(message.chat.id, f"⚠️ Не удалось сохранить курс (возможно, нет места на диске).", reply_markup=admin_menu_markup())
    except:
        bot.send_message(message.chat.id, "⚠️ Неверный формат числа.", reply_markup=admin_menu_markup())

@bot.message_handler(func=lambda m: m.text == "🏦 Изменить адреса кошельков")
def admin_change_addresses(m):
    if m.from_user.id != ADMIN_ID: return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("TRC20", "BEP20", "🔙 Админ меню")
    bot.send_message(m.chat.id, "Выберите сеть для изменения адреса:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(m.chat.id, _admin_receive_network_for_address)

def _admin_receive_network_for_address(message):
    if message.from_user.id != ADMIN_ID: return
    net = message.text.strip()
    if net not in ["TRC20", "BEP20"]:
        bot.send_message(message.chat.id, "Отмена.", reply_markup=admin_menu_markup())
        return
    bot.send_message(message.chat.id, f"Введите новый адрес для сети {net}:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler_by_chat_id(message.chat.id, lambda m: _admin_save_new_address(m, net))

def _admin_save_new_address(message, net):
    if message.from_user.id != ADMIN_ID: return
    new_addr = message.text.strip()
    addrs = load_addresses()
    addrs[net] = new_addr
    if save_addresses(addrs):
        bot.send_message(message.chat.id, f"✅ Адрес для {net} обновлён: `{new_addr}`", parse_mode="Markdown", reply_markup=admin_menu_markup())
    else:
        bot.send_message(message.chat.id, "⚠️ Не удалось сохранить адрес (возможно, нет места на диске).", reply_markup=admin_menu_markup())

@bot.message_handler(func=lambda m: m.text == "📋 Список заявок")
def admin_list_requests(m):
    if m.from_user.id != ADMIN_ID: return
    payments = load_payments()
    if not payments:
        bot.send_message(m.chat.id, "⚠️ Нет заявок.", reply_markup=admin_menu_markup())
        return
    for pid, p in payments.items():
        short = f"ID: {pid}\nType: {p.get('type')}\nAmount: {p.get('amount', p.get('uah_amount',''))}\nNetwork: {p.get('network')}\nStatus: {p.get('status')}"
        bot.send_message(m.chat.id, short)
    bot.send_message(m.chat.id, "Список показан.", reply_markup=admin_menu_markup())

@bot.message_handler(func=lambda m: m.text == "✅ Подтвердить/Отклонить")
def admin_choose_pending(m):
    if m.from_user.id != ADMIN_ID: return
    payments = load_payments()
    if not payments:
        bot.send_message(m.chat.id, "⚠️ Нет ожидающих платежей.", reply_markup=admin_menu_markup())
        return
    markup = types.InlineKeyboardMarkup()
    for pid, p in payments.items():
        # Показываем тип и сумму в кнопке
        label_amt = p.get('amount', p.get('uah_amount', ''))
        label = f"{p.get('type')} {label_amt}"
        markup.add(types.InlineKeyboardButton(label, callback_data=f"admin_action_{pid}"))
    bot.send_message(m.chat.id, "Выберите заявку для действий:", reply_markup=markup)

# ==========================
# 🔔 Callback для подтверждения/отклонения
# ==========================
@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_action_"))
def admin_action_select(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ У тебя нет доступа.")
        return
    pid = call.data.split("_", 2)[2]
    payments = load_payments()
    if pid not in payments:
        bot.answer_callback_query(call.id, "⚠️ Заявка не найдена.")
        return
    p = payments[pid]
    # Показать детали и кнопки подтверждения/отклонения
    text = (
        f"ID: {pid}\n"
        f"Пользователь: @{p.get('username')} ({p.get('user_id')})\n"
        f"Тип: {p.get('type')}\n"
        f"Сумма: {p.get('amount', p.get('uah_amount',''))}\n"
        f"Сеть: {p.get('network')}\n"
        f"Адрес/Карта: {p.get('address','')} / {p.get('card','')}\n"
        f"Статус: {p.get('status')}"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{pid}"))
    markup.add(types.InlineKeyboardButton("🚫 Отклонить", callback_data=f"reject_{pid}"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def handle_confirm_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ У тебя нет доступа.")
        return
    pid = call.data.split("_", 1)[1]
    payments = load_payments()
    if pid not in payments:
        bot.answer_callback_query(call.id, "⚠️ Платеж уже подтверждён или не найден.")
        return
    p = payments.pop(pid)
    # Сохраняем удаление
    if not save_payments(payments):
        bot.send_message(call.message.chat.id, "⚠️ Не удалось удалить запись (возможно нет места на диске).")
    # Уведомляем пользователя
    try:
        user_id = int(p.get("user_id"))
        bot.send_message(user_id, f"✅ Ваш платеж по заявке *{pid}* подтверждён. Операция завершена.", parse_mode="Markdown", reply_markup=main_menu_markup(user_id))
    except Exception as e:
        print(f"[notify user] Ошибка: {e}")
    bot.send_message(call.message.chat.id, f"✅ Платеж {pid} подтверждён.", reply_markup=admin_menu_markup())

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def handle_reject_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ У тебя нет доступа.")
        return
    pid = call.data.split("_", 1)[1]
    payments = load_payments()
    if pid not in payments:
        bot.answer_callback_query(call.id, "⚠️ Платеж уже подтверждён или не найден.")
        return
    p = payments.pop(pid)
    if not save_payments(payments):
        bot.send_message(call.message.chat.id, "⚠️ Не удалось удалить запись (возможно нет места на диске).")
    try:
        user_id = int(p.get("user_id"))
        bot.send_message(user_id, f"❌ Ваш платеж по заявке *{pid}* отклонён. Свяжитесь с администратором для разъяснений.", parse_mode="Markdown", reply_markup=main_menu_markup(user_id))
    except Exception as e:
        print(f"[notify user reject] Ошибка: {e}")
    bot.send_message(call.message.chat.id, f"🚫 Платеж {pid} отклонён.", reply_markup=admin_menu_markup())

# ==========================
# Обработчики возврата в меню
# ==========================
@bot.message_handler(func=lambda m: m.text in ["⬅️ Назад", "🔙 В главное меню"])
def back_to_main(m):
    bot.send_message(m.chat.id, "🏠 Главное меню:", reply_markup=main_menu_markup(m.from_user.id))

# ==========================
# 🚀 Запуск на Render (Web Service)
# ==========================
from flask import Flask
import threading

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ Бот работает на Render!", 200

def run_bot():
    print("🤖 Бот запущен через polling...")
    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print("Ошибка polling:", e)
            traceback.print_exc()
            time.sleep(10)

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Запускаем Flask, чтобы Render видел открытый порт
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Flask-сервер слушает порт {port}")
    app.run(host="0.0.0.0", port=port)

