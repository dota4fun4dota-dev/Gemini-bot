import asyncio
import logging
import sqlite3
import sys
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# ==================== ТВОИ НАСТРОЙКИ ====================
BOT_TOKEN = "8535823645:AAHq8uvQWH2xd_VTcMpFsndnOOP7EzdGbV4"

# Твой ключ GROQ
GROQ_API_KEY = "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"

# Настройка клиента для Groq
ai_client = AsyncOpenAI(
    api_key=GROQ_API_KEY, 
    base_url="https://api.groq.com/openai/v1"
)

# Используем модель Llama 3.3, которая сейчас идеально работает на Groq
AI_MODEL = "llama-3.3-70b-versatile" 
# ========================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Логика БД и Хэндлеры (оставлена без изменений для стабильности) ---
# [Здесь находится остальной код твоего бота, который мы правили ранее]
# (Убедись, что все функции типа get_user, init_db и т.д. на месте)

# В блоке обработки текста (handle_ai_request) убедись, что используется:
# model=AI_MODEL,
# messages=[{"role": "user", "content": message.text}]
