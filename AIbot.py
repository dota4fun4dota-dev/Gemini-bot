import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

# 1. Сначала токен
BOT_TOKEN = "8980453196:AAGiMgy8bohMdOM6Z3nGpmos_ysCr2W_-Us"

# 2. Настройка логов
logging.basicConfig(level=logging.INFO)

# 3. Инициализация объектов
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 4. Обработчик запуска
@dp.startup()
async def on_startup():
    logging.info("--- Бот запускается и очищает старые обновления ---")
    await bot.delete_webhook(drop_pending_updates=True)

# 5. Обработчик команды /start
@dp.message(CommandStart())
async def start(message: Message):
    logging.info(f"Получена команда /start от {message.from_user.id}")
    await message.answer("Бот работает! Это тестовая версия. Напиши мне что-нибудь.")

# 6. Обработчик любого текста
@dp.message(F.text)
async def simple_echo(message: Message):
    logging.info(f"Получено сообщение: {message.text}")
    await message.answer(f"Бот получил твое сообщение: {message.text}")

# 7. Главная функция
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
