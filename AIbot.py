import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# ==================== ТВОИ НАСТРОЙКИ ====================
# Твой новый, чистый токен бота
BOT_TOKEN = "8535823645:AAHq8uvQWH2xd_VTcMpFsndnOOP7EzdGbV4"

# Твой рабочий токен OpenRouter
OPENROUTER_API_KEY = "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" 

ai_client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY, 
    base_url="https://openrouter.ai/api/v1"
)
AI_MODEL = "deepseek/deepseek-chat" 
# ========================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Купить Подписку", callback_data="buy_sub")],
        [InlineKeyboardButton(text="📊 Мой профиль", callback_data="my_profile")]
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message):
    text = f"👋 Привет, {message.from_user.first_name}!\n\nБот успешно перезапущен и готов к работе.\nНапиши мне любой вопрос, и я отвечу с помощью ИИ!"
    await message.answer(text, reply_markup=main_menu_keyboard())

@dp.callback_query(F.data == "my_profile")
async def process_profile(callback):
    await callback.message.answer("📊 Профиль временно на техобслуживании, но ИИ работает!")
    await callback.answer()

@dp.callback_query(F.data == "buy_sub")
async def process_buy_sub(callback):
    await callback.message.answer("⚙️ Меню оплаты временно на техобслуживании.")
    await callback.answer()

@dp.message(F.text)
async def handle_ai_request(message: Message):
    status_message = await message.answer("🧠 *ИИ генерирует ответ... Пожалуйста, подождите.*")
    
    try:
        response = await ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "Ты — полезный и умный ИИ-ассистент. Отвечай на русском языке."},
                {"role": "user", "content": message.text}
            ],
            max_tokens=1000
        )
        ai_response = response.choices[0].message.content
        await status_message.delete()
        await message.answer(ai_response)
        
    except Exception as e:
        logging.error(f"Ошибка ИИ: {e}")
        await status_message.edit_text("❌ Ошибка OpenRouter. Проверь баланс на сайте openrouter.ai")

async def main():
    # Жесткий сброс зависшего соединения в Telegram
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
