import os
import asyncio
import logging

# 1. Сначала удаляем прокси, чтобы OpenAI не выдавал ошибку 'proxies'
for env_var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    if env_var in os.environ:
        del os.environ[env_var]

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# 2. Настройка логов для Railway
logging.basicConfig(level=logging.INFO)

# Получаем переменные
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Я готов к работе. Пиши текст или /draw [описание] для картинки.")

@dp.message(F.text.startswith("/draw"))
async def draw_handler(message: Message):
    prompt = message.text.replace("/draw", "").strip()
    if not prompt:
        await message.answer("Пожалуйста, укажите описание для рисунка.")
        return
    
    msg = await message.answer("🎨 Генерирую изображение, подожди...")
    try:
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="102
