import asyncio
import logging
import sqlite3
import sys
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, PreCheckoutQuery, LabeledPrice
from aiogram.filters import CommandStart
from google import genai # Переходим на официальный и самый стабильный клиент Google

# ==================== ТВОИ НАСТРОЙКИ ====================
BOT_TOKEN = "8535823645:AAEnS_30By0LIIZtOAx220JNZ5bkXf90aJU"
PROVIDER_TOKEN = "" # Для Telegram Stars оставляем пустым

# Твой ключ Gemini
GEMINI_API_KEY = "AQ.Ab8RN6JwMmDezUD89qOCCfzgUriAeoB6_vw9FnyQsYNvhNV2AQ"
# ========================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализируем официальный клиент Google AI
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# === РАБОТА С БАЗОЙ ДАННЫХ ===
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            sub_until TEXT,
            free_requests_date TEXT,
            requests_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT sub_until, free_requests_date, requests_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        today = datetime.today().strftime('%Y-%m-%d')
        cursor.execute("INSERT INTO users (user_id, sub_until, free_requests_date, requests_count) VALUES (?, ?, ?, ?)",
                       (user_id, None, today, 0))
        conn.commit()
        conn.close()
        return None, today, 0
    conn.close()
    return row

def update_user_sub(user_id, days):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    until_date = datetime.now() + timedelta(days=days)
    cursor.execute("UPDATE users SET sub_until = ? WHERE user_id = ?", (until_date.strftime('%Y-%m-%d %H:%M:%S'), user_id))
    conn.commit()
    conn.close()

def increment_request(user_id, current_count):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    today = datetime.today().strftime('%Y-%m-%d')
    cursor.execute("UPDATE users SET free_requests_date = ?, requests_count = ? WHERE user_id = ?", (today, current_count + 1, user_id))
    conn.commit()
    conn.close()

# === КЛАВИАТУРЫ ===
def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Купить Подписку", callback_data="buy_sub")],
        [InlineKeyboardButton(text="📊 Мой профиль", callback_data="my_profile")]
    ])

def prices_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌱 Неделя — 50 Stars", callback_data="pay_7")],
        [InlineKeyboardButton(text="🔥 Месяц — 150 Stars", callback_data="pay_30")],
        [InlineKeyboardButton(text="👑 Год — 500 Stars", callback_data="pay_365")]
    ])

# === ХЭНДЛЕРЫ ===
@dp.message(CommandStart())
async def cmd_start(message: Message):
    get_user(message.from_user.id)
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я твой личный умный ИИ-помощник нового поколения.\n"
        "Ты можешь отправить мне любой вопрос, попросить написать реферат или код.\n\n"
        "⚠️ Без подписки тебе доступно **3 запроса в сутки**.\n"
        "Используй кнопки ниже, чтобы проверить баланс или снять ограничения 👇",
        reply_markup=main_menu_keyboard()
    )

@dp.callback_query(F.data == "my_profile")
async def process_profile(callback):
    sub_until, req_date, req_count = get_user(callback.from_user.id)
    today = datetime.today().strftime('%Y-%m-%d')
    
    left_reqs = 3 - req_count if req_date == today else 3
    if left_reqs < 0: left_reqs = 0
        
    status = "❌ Нет подписки"
    if sub_until:
        until_dt = datetime.strptime(sub_until, '%Y-%m-%d %H:%M:%S')
        if until_dt > datetime.now():
            status = f"🟢 Активна до {until_dt.strftime('%d.%m.%Y %H:%M')}"
            left_reqs = "♾ Безлимит"

    await callback.message.answer(
        f"📊 **Твой профиль:**\n\n"
        f"👤 ID: `{callback.from_user.id}`\n"
        f"👑 Статус подписки: {status}\n"
        f"⏳ Доступно ИИ-запросов на сегодня: **{left_reqs}**"
    )
    await callback.answer()

@dp.callback_query(F.data == "buy_sub")
async def process_buy_sub(callback):
    await callback.message.answer("⚙️ Выбери подходящий тарифный план подписки:", reply_markup=prices_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("pay_"))
async def send_sub_invoice(callback):
    days = int(callback.data.split("_")[1])
    tariff_data = {
        7: {"title": "Подписка на 7 дней", "price": 50},
        30: {"title": "Подписка на 30 дней", "price": 150},
        365: {"title": "Подписка на 365 дней", "price": 500}
    }
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=tariff_data[days]["title"],
        description="Полный безлимитный доступ к ИИ-помощнику без ограничений по скорости и количеству запросов.",
        payload=f"sub_{days}",
        provider_token=PROVIDER_TOKEN,
        currency="XTR",
        prices=[LabeledPrice(label="Цена", amount=tariff_data[days]["price"])]
    )
    await callback.answer()

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    days = int(payload.split("_")[1])
    update_user_sub(message.from_user.id, days)
    await message.answer(
        f"🎉 **Ура! Оплата прошла успешно!**\n\n"
        f"Вам начислен безлимитный доступ на **{days} дней**. "
        "Задавайте мне любые вопросы! 🚀"
    )

# === ОБРАБОТКА НАСТОЯЩИХ ТЕКСТОВЫХ ЗАПРОСОВ К ИИ ===
@dp.message(F.text)
async def handle_ai_request(message: Message):
    user_id = message.from_user.id
    sub_until, req_date, req_count = get_user(user_id)
    
    has_sub = False
    if sub_until:
        until_dt = datetime.strptime(sub_until, '%Y-%m-%d %H:%M:%S')
        if until_dt > datetime.now():
            has_sub = True

    if not has_sub:
        today = datetime.today().strftime('%Y-%m-%d')
        current_count = req_count if req_date == today else 0
        
        if current_count >= 3:
            await message.answer(
                "⚠️ **Лимит бесплатных запросов на сегодня исчерпан (3 из 3).**\n\n"
                "Чтобы продолжить общаться с ИИ без ограничений, оформите подписку. Это стоит копейки!",
                reply_markup=main_menu_keyboard()
            )
            return
        else:
            increment_request(user_id, current_count)

    status_message = await message.answer("🧠 *ИИ генерирует ответ... Пожалуйста, подождите.*")
    
    try:
        # Официальный вызов модели Gemini 1.5 Flash через родной SDK
        response = ai_client.models.generate_content(
            model='gemini-1.5-flash',
            contents=message.text,
            config=genai.types.GenerateContentConfig(
                system_instruction="Ты — опытный, полезный и умный ИИ-ассистент. Отвечай четко, структурировано и на русском языке."
            )
        )
        ai_response = response.text
        
        await status_message.delete()
        await message.answer(ai_response)
        
    except Exception as e:
        logging.error(f"Ошибка ИИ: {e}")
        await status_message.edit_text("❌ Произошла ошибка при обращении к ИИ. Попробуйте позже.")

# === ЗАПУСК БОТА ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    init_db()
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
