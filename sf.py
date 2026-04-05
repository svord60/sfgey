import os
import asyncio
import nest_asyncio
nest_asyncio.apply()  # ФИКС ОШИБКИ: RuntimeError: no current event loop

import sqlite3
import requests
import re
from bs4 import BeautifulSoup
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError

# ========== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ==========
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "твой_api_hash")
PHONE = os.environ.get("PHONE", "+79998887777")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "токен_бота")
CRYPTO_API_KEY = os.environ.get("CRYPTO_API_KEY", "токен_из_crypto_bot")

# ========== НАСТРОЙКИ ==========
PROXY = None
ADMIN_ID = 123456789  # ТВОЙ Telegram ID (только ты вводишь код)
SEARCH_INTERVAL = 300

# ID каналов для подписки
REQUIRED_CHANNELS = [
    {"id": -1002839409663, "invite_link": "https://t.me/+wBwWF5bz649kM2E6"},
    {"id": -1003391124726, "invite_link": "https://t.me/+jQ4RsEzy6TFhY2I0"}
]

# Анимированные эмодзи
EMOJI_FIND = "5188217332748527444"
EMOJI_PROFILE = "5467480195143310096"
EMOJI_TEMPLATES = "5433982607035474385"
EMOJI_DONATE = "5429190797922696151"

# ========== ВСЕ РУССКИЕ ЖЕНСКИЕ ИМЕНА ==========
FEMALE_NAMES = [
    "Аня", "Анна", "Антонина", "Анжела", "Алиса", "Алина", "Алла", "Альбина", "Анастасия", "Ангелина",
    "Валя", "Валентина", "Варвара", "Вера", "Вероника", "Вика", "Виктория", "Владлена", "Василиса",
    "Галя", "Галина", "Даша", "Дарья", "Диана", "Дина", "Ева", "Евгения", "Екатерина", "Елена",
    "Елизавета", "Жанна", "Женя", "Зина", "Зинаида", "Зоя", "Ира", "Ирина", "Инна", "Ия",
    "Катя", "Кристина", "Ксюша", "Ксения", "Лариса", "Лена", "Лиза", "Лидия", "Люба", "Любовь",
    "Людмила", "Маша", "Мария", "Майя", "Маргарита", "Марина", "Милана", "Милена", "Надя", "Надежда",
    "Настя", "Наташа", "Наталья", "Нелли", "Нина", "Оксана", "Олеся", "Оля", "Ольга", "Полина",
    "Раиса", "Регина", "Рита", "Роза", "Света", "Светлана", "Серафима", "Снежана", "София", "Софья",
    "Тамара", "Таня", "Татьяна", "Ульяна", "Юля", "Юлия", "Яна", "Ярослава", "Агата", "Агафья",
    "Аделаида", "Аза", "Аида", "Алевтина", "Александра", "Алёна", "Амалия", "Амелия", "Анфиса", "Аполлинария",
    "Ариадна", "Арина", "Аэлита", "Белла", "Берта", "Богдана", "Божена", "Бронислава", "Валерия", "Ванда",
    "Веста", "Влада", "Виталина", "Владислава", "Габриэлла", "Гелла", "Генриетта", "Глафира", "Гражина", "Грета",
    "Дана", "Дарина", "Дарьяна", "Дебора", "Динара", "Доминика", "Дора", "Евангелина", "Евдокия", "Екатерина",
    "Елена", "Елизавета", "Есения", "Ефимия", "Ефросинья", "Жозефина", "Забава", "Зарина", "Земфира", "Злата"
]

FEMALE_EMOJIS = ["💅", "✨", "💖", "🌸", "👄", "💋", "👗", "👜", "💎", "👑", "💕", "💞", "💓", "💗", "💝", "🌺", "🌷", "🌹", "🥰", "😘", "💃", "👯‍♀️", "👸"]

TEMPLATES = [
    "Привет! Увидел у тебя NFT-подарок. Не продашь? Готова обсудить цену.",
    "Привет! Твой NFT-подарок очень крутой. Продашь? Могу предложить хорошую сумму.",
    "Привет! Понравился твой коллекционный подарок. Не хочешь продать?",
    "Привет! Скупаю NFT-подарки. Твой интересует. Сколько хочешь?",
    "Привет! У тебя шикарный NFT. Продашь за USDT?",
    "Привет! Твой подарок редкий. Продашь? Договоримся.",
    "Привет! Готов купить твой NFT-подарок. Напиши цену.",
    "Привет! Твой подарок выглядит дорого. Продашь за хорошую цену?",
    "Привет! Скупаю коллекционные подарки. Твой в топе. Сколько просишь?",
    "Привет! NFT-подарок на продажу? Заинтересован."
]

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect("nft_bot.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS girls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        nft_count INTEGER DEFAULT 0,
        issued INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS chats (
        chat_id TEXT PRIMARY KEY,
        title TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        search_count INTEGER DEFAULT 0,
        last_index INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

def add_girl(username, nft_count=1):
    conn = sqlite3.connect("nft_bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO girls (username, nft_count, issued) VALUES (?, ?, 0)", (username, nft_count))
    conn.commit()
    conn.close()

def add_chat(chat_id, title):
    conn = sqlite3.connect("nft_bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO chats (chat_id, title) VALUES (?, ?)", (str(chat_id), title))
    conn.commit()
    conn.close()

def get_all_chats():
    conn = sqlite3.connect("nft_bot.db")
    c = conn.cursor()
    c.execute("SELECT chat_id FROM chats")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def increment_search_count(user_id):
    conn = sqlite3.connect("nft_bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, search_count, last_index) VALUES (?, 0, 0)", (user_id,))
    c.execute("UPDATE users SET search_count = search_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    conn = sqlite3.connect("nft_bot.db")
    c = conn.cursor()
    c.execute("SELECT search_count FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def get_user_index(user_id):
    conn = sqlite3.connect("nft_bot.db")
    c = conn.cursor()
    c.execute("SELECT last_index FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def update_user_index(user_id, new_index):
    conn = sqlite3.connect("nft_bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET last_index = ? WHERE user_id = ?", (new_index, user_id))
    conn.commit()
    conn.close()

def get_girls_batch(user_id, limit=10):
    conn = sqlite3.connect("nft_bot.db")
    c = conn.cursor()
    last_idx = get_user_index(user_id)
    c.execute("SELECT username, nft_count FROM girls WHERE issued = 0 ORDER BY id LIMIT ? OFFSET ?", (limit, last_idx))
    rows = c.fetchall()
    conn.close()
    return rows

def get_girl_info(username):
    conn = sqlite3.connect("nft_bot.db")
    c = conn.cursor()
    c.execute("SELECT nft_count FROM girls WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 1

def count_pending():
    conn = sqlite3.connect("nft_bot.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM girls WHERE issued = 0")
    count = c.fetchone()[0]
    conn.close()
    return count

# ========== ФИЛЬТРАЦИЯ ==========
def is_likely_female(first_name, bio):
    first_name_lower = first_name.lower()
    for name in FEMALE_NAMES:
        if name.lower() in first_name_lower:
            return True
    if bio:
        for emoji in FEMALE_EMOJIS:
            if emoji in bio:
                return True
    return False

# ========== ПАРСИНГ NFT ==========
def get_nft_count(username):
    url = f"https://t.me/{username}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10, proxies=PROXY if PROXY else None)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text().lower()
        nft_matches = re.findall(r'(\d+)\s*nft', text)
        if nft_matches:
            return int(nft_matches[0])
        if "nft" in text or "коллекционный" in text:
            return 1
        return 0
    except:
        return 0

# ========== СБОР УЧАСТНИКОВ ==========
async def collect_participants_from_all_chats(client):
    chats = get_all_chats()
    total_found = 0
    for chat_id in chats:
        try:
            entity = await client.get_entity(int(chat_id))
            async for user in client.iter_participants(entity):
                if user.username and user.first_name:
                    bio = getattr(user, "about", "") or ""
                    if is_likely_female(user.first_name, bio):
                        nft_count = get_nft_count(user.username)
                        if nft_count > 0:
                            add_girl(user.username, nft_count)
                            total_found += 1
                            print(f"👩 @{user.username} | {user.first_name} | NFT: {nft_count}")
        except:
            continue
    return total_found

async def search_and_join_chats(client):
    keywords = ["девушки", "знакомства", "girls", "beauty", "мода", "стиль", "визаж", "флирт"]
    new_chats = 0
    for kw in keywords:
        try:
            async for dialog in client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    if kw.lower() in dialog.title.lower():
                        chat_id = str(dialog.id)
                        if chat_id not in get_all_chats():
                            add_chat(chat_id, dialog.title)
                            new_chats += 1
                            print(f"✅ {dialog.title}")
        except:
            continue
    return new_chats

async def background_searcher(client):
    while True:
        print("🔍 Поиск чатов...")
        new_chats = await search_and_join_chats(client)
        print(f"📢 Новых чатов: {new_chats}")
        print("👥 Сбор девушек...")
        found = await collect_participants_from_all_chats(client)
        print(f"💎 Найдено: {found}")
        await asyncio.sleep(SEARCH_INTERVAL)

# ========== ДОНАТ ==========
def create_crypto_check(amount_usdt):
    url = "https://pay.crypt.bot/api/createCheck"
    params = {"asset": "USDT", "amount": str(amount_usdt), "description": f"Донат ({amount_usdt} USDT)"}
    headers = {"Crypto-Pay-API-Token": CRYPTO_API_KEY}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()
        if data.get("ok"):
            return data["result"]["check_url"]
    except:
        pass
    return None

# ========== БОТ ==========
bot = TelegramClient("bot_session", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Глобальная переменная для ожидания кода
waiting_for_code = False
code_future = None

# ========== ПРОВЕРКА ПОДПИСКИ ==========
async def is_user_subscribed(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_permissions(channel["id"], user_id)
            if not member.is_member:
                return False
        except Exception:
            return False
    return True

def get_subscription_keyboard():
    buttons = []
    for ch in REQUIRED_CHANNELS:
        buttons.append([Button.url(f"📢 Подписаться", ch["invite_link"], style="primary")])
    buttons.append([Button.inline("✅ Проверить подписку", "check_sub", style="success")])
    return buttons

def get_main_menu_inline():
    return [
        [Button.inline(text=" Найти", data="find", icon_custom_emoji_id=EMOJI_FIND, style="primary")],
        [Button.inline(text=" Профиль", data="profile", icon_custom_emoji_id=EMOJI_PROFILE, style="primary"),
         Button.inline(text=" Шаблоны", data="templates", icon_custom_emoji_id=EMOJI_TEMPLATES, style="primary")],
        [Button.inline(text=" Донат автору", data="donate", icon_custom_emoji_id=EMOJI_DONATE, style="success")]
    ]

# ========== ОБРАБОТЧИК КОМАНД ==========
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.sender_id
    if await is_user_subscribed(user_id):
        await event.reply(
            "**👋 Привет! Я бот для поиска девушек с NFT-подарками.**\n\nНажми на кнопку ниже:",
            buttons=get_main_menu_inline(),
            parse_mode="markdown"
        )
    else:
        await event.reply(
            "**🔒 Для доступа к боту необходимо подписаться на каналы:**\n\n"
            "1️⃣ Нажми на кнопку «Подписаться» под каждым каналом\n"
            "2️⃣ После подписки нажми «✅ Проверить подписку»",
            buttons=get_subscription_keyboard(),
            parse_mode="markdown"
        )

@bot.on(events.CallbackQuery(data=b"check_sub"))
async def check_subscription(event):
    user_id = event.sender_id
    if await is_user_subscribed(user_id):
        await event.edit(
            "**✅ Подписка подтверждена!**\n\nДобро пожаловать в бот.",
            buttons=get_main_menu_inline(),
            parse_mode="markdown"
        )
    else:
        await event.answer("❌ Вы не подписаны на все каналы. Подпишитесь и нажмите снова.", alert=True)

# ========== ОБРАБОТЧИК ВВОДА КОДА (ТОЛЬКО ДЛЯ АДМИНА) ==========
@bot.on(events.NewMessage)
async def handle_code_input(event):
    global waiting_for_code, code_future
    user_id = event.sender_id
    
    if user_id != ADMIN_ID:
        return
    
    if not waiting_for_code:
        return
    
    if not event.raw_text.isdigit():
        await event.reply("❌ Неверный формат. Код состоит только из цифр. Попробуй ещё раз.")
        return
    
    if code_future and not code_future.done():
        code_future.set_result(event.raw_text)
        waiting_for_code = False
        await event.reply("✅ Код получен. Выполняю вход...")

# ========== ФУНКЦИЯ ЗАПУСКА USERBOT ==========
async def start_userbot_with_bot_code():
    global waiting_for_code, code_future
    
    user_client = TelegramClient("user_session", API_ID, API_HASH, proxy=PROXY if PROXY else None)
    
    try:
        await user_client.start(PHONE)
        print("🤖 Userbot уже был авторизован")
        return user_client
    except Exception as e:
        print(f"⚠️ Требуется код подтверждения: {e}")
    
    admin_entity = await bot.get_entity(ADMIN_ID)
    await bot.send_message(
        admin_entity,
        "**🔐 Требуется код подтверждения для входа в аккаунт.**\n\n"
        "Введи код, который пришёл в Telegram:",
        parse_mode="markdown"
    )
    
    waiting_for_code = True
    code_future = asyncio.Future()
    
    try:
        code = await asyncio.wait_for(code_future, timeout=120)
        await user_client.sign_in(PHONE, code)
        print("🤖 Userbot успешно авторизован")
        await bot.send_message(admin_entity, "✅ **Аккаунт успешно авторизован!** Бот начал работу.", parse_mode="markdown")
        return user_client
    except asyncio.TimeoutError:
        await bot.send_message(admin_entity, "❌ **Время ожидания кода истекло.** Перезапусти бота.", parse_mode="markdown")
        raise
    except SessionPasswordNeededError:
        await bot.send_message(admin_entity, "❌ **Требуется двухфакторная аутентификация.** Бот пока не поддерживает ввод пароля через чат.", parse_mode="markdown")
        raise
    finally:
        waiting_for_code = False
        code_future = None

# ========== ОСНОВНЫЕ КОМАНДЫ БОТА ==========
@bot.on(events.CallbackQuery(data=b"find"))
async def menu_find(event):
    await event.answer()
    user_id = event.sender_id
    girls = get_girls_batch(user_id, 10)
    
    if not girls:
        pending = count_pending()
        if pending == 0:
            await event.reply("❌ База пуста. Попробуй позже.", buttons=get_main_menu_inline(), parse_mode="markdown")
        else:
            await event.reply("❌ Ты уже получил всех.", buttons=get_main_menu_inline(), parse_mode="markdown")
        return
    
    increment_search_count(user_id)
    update_user_index(user_id, get_user_index(user_id) + len(girls))
    
    buttons = []
    for username, nft_count in girls:
        buttons.append([Button.inline(f"👩 @{username} ({nft_count} NFT)", f"girl_{username}", style="primary")])
    buttons.append([Button.inline("🔄 Искать заново", "refresh_find", style="danger")])
    
    await event.reply(
        f"**🔍 Выбери девушку (10 шт):**\n\n_Нажми на юзернейм, чтобы увидеть детали_",
        buttons=buttons,
        parse_mode="markdown"
    )

@bot.on(events.CallbackQuery(data=b"refresh_find"))
async def refresh_find(event):
    user_id = event.sender_id
    girls = get_girls_batch(user_id, 10)
    if not girls:
        await event.edit("❌ Нет новых девушек.", buttons=get_main_menu_inline())
        return
    update_user_index(user_id, get_user_index(user_id) + len(girls))
    buttons = []
    for username, nft_count in girls:
        buttons.append([Button.inline(f"👩 @{username} ({nft_count} NFT)", f"girl_{username}", style="primary")])
    buttons.append([Button.inline("🔄 Искать заново", "refresh_find", style="danger")])
    await event.edit(
        f"**🔍 Ещё 10 девушек:**\n\n_Нажми на юзернейм_",
        buttons=buttons,
        parse_mode="markdown"
    )

@bot.on(events.CallbackQuery(data=re.compile(b"girl_(.*)")))
async def girl_details(event):
    username = event.data_match.group(1).decode()
    nft_count = get_girl_info(username)
    buttons = [
        [Button.url("✍️ Написать", f"https://t.me/{username}", style="success")],
        [Button.inline("◀️ Назад к поиску", "back_to_find", style="primary")]
    ]
    await event.edit(
        f"**👩‍🦰 @{username}**\n\n💎 **NFT-подарков:** `{nft_count}`\n\n_Нажми «Написать», чтобы предложить купить._",
        buttons=buttons,
        parse_mode="markdown"
    )

@bot.on(events.CallbackQuery(data=b"back_to_find"))
async def back_to_find(event):
    await menu_find(event)

@bot.on(events.CallbackQuery(data=b"profile"))
async def menu_profile(event):
    await event.answer()
    user_id = event.sender_id
    search_count = get_user_stats(user_id)
    pending = count_pending()
    await event.reply(
        f"**👤 Профиль**\n\n🆔 ID: `{user_id}`\n🔍 Поисков: `{search_count}`\n📊 В базе: `{pending}`",
        buttons=get_main_menu_inline(),
        parse_mode="markdown"
    )

@bot.on(events.CallbackQuery(data=b"templates"))
async def menu_templates(event):
    await event.answer()
    text = "**📋 Шаблоны (нажми → копировать):**\n\n"
    buttons = []
    for i, t in enumerate(TEMPLATES, 1):
        text += f"{i}. {t}\n\n"
        buttons.append([Button.inline(f"📋 Копировать #{i}", f"copy_{i-1}")])
    await event.reply(text, buttons=buttons, parse_mode="markdown")

@bot.on(events.CallbackQuery(data=re.compile(b"copy_(\\d+)")))
async def copy_template(event):
    index = int(event.data_match.group(1).decode())
    template = TEMPLATES[index]
    await event.answer(template, alert=True)

@bot.on(events.CallbackQuery(data=b"donate"))
async def menu_donate(event):
    await event.answer()
    buttons = [
        [Button.inline("5 USDT", b"donate_5"), Button.inline("10 USDT", b"donate_10")],
        [Button.inline("25 USDT", b"donate_25"), Button.inline("50 USDT", b"donate_50")],
        [Button.inline("Своя сумма", b"donate_custom")]
    ]
    await event.reply("**💸 Выбери сумму:**", buttons=buttons, parse_mode="markdown")

@bot.on(events.CallbackQuery(data=b"donate_5"))
async def donate_5(e): await create_and_send_check(e, 5)
@bot.on(events.CallbackQuery(data=b"donate_10"))
async def donate_10(e): await create_and_send_check(e, 10)
@bot.on(events.CallbackQuery(data=b"donate_25"))
async def donate_25(e): await create_and_send_check(e, 25)
@bot.on(events.CallbackQuery(data=b"donate_50"))
async def donate_50(e): await create_and_send_check(e, 50)

@bot.on(events.CallbackQuery(data=b"donate_custom"))
async def donate_custom(event):
    async with bot.conversation(event.sender_id, timeout=60) as conv:
        await conv.send_message("**Введи сумму в USDT (1-1000):**", parse_mode="markdown")
        try:
            resp = await conv.get_response()
            amount = float(resp.text)
            if 1 <= amount <= 1000:
                await create_and_send_check(event, amount)
            else:
                await conv.send_message("❌ От 1 до 1000.")
        except:
            await conv.send_message("❌ Ошибка.")

async def create_and_send_check(event, amount):
    url = create_crypto_check(amount)
    if url:
        await event.edit(f"**✅ Чек на {amount} USDT**\n\n[Оплатить]({url})", parse_mode="markdown", buttons=get_main_menu_inline())
    else:
        await event.edit("❌ Ошибка.", buttons=get_main_menu_inline())

# ========== ЗАПУСК ==========
async def main():
    init_db()
    
    await bot.start()
    print("🚀 Бот запущен")
    
    user_client = await start_userbot_with_bot_code()
    
    asyncio.create_task(background_searcher(user_client))
    
    await bot.run_until_disconnected()

if __name__ == "__main__":
    # Фикс для некоторых хостингов
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "no current event loop" in str(e):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(main())
        else:
            raise