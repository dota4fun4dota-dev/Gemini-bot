import asyncio
import logging
import sqlite3
import requests
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# === НАСТРОЙКИ ===
BOT_TOKEN = "8535823645:AAHq8uvQWH2xd_VTcMpFsndnOOP7EzdGbV4"
GROQ_API_KEY = "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"
HF_TOKEN = "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" # Использую твой токен

ai_client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
AI_MODEL = "llama-3.3-70b-versatile"
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"

FREE_LIMIT = 10
RESET_HOURS = 2

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# [Здесь должны быть твои функции init_db, get_status и increment_count из прошлого сообщения]
# Чтобы не перегружать сообщение, убедись, что они у тебя в коде есть!

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("👋 Привет! Я умею отвечать на вопросы и рисовать.\n\nТекст: просто напиши что-то.\nКартинки: используй `/draw описание`")

@dp.message(F.text.startswith("/draw"))
async def handle_draw(message: Message):
    # Логика проверки лимитов (как в get_status)
    # ...
    prompt = message.text.replace("/draw", "").strip()
    status = await message.answer("🎨 Генерирую...")
    
    try:
        def request_hf():
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            return requests.post(HF_API_URL, headers=headers, json={"inputs": prompt}).content
            
        loop = asyncio.get_event_loop()
        image_bytes = await loop.run_in_executor(None, request_hf)
        
        await bot.send_photo(message.chat.id, photo=BufferedInputFile(image_bytes, filename="img.png"))
        await status.delete()
    except Exception as e:
        await status.edit_text(f"❌ Ошибка: {e}")

@dp.message(F.text)
async def handle_text(message: Message):
    # Логика обработки текста через Groq
    # ...
