import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

# === КОНФИГУРАЦИЯ ===
BOT_TOKEN = "8980453196:AAGiMgy8bohMdOM6Z3nGpmos_ysCr2W_-Us"
API_BASE_URL = "https://api.kie.ai" 
API_KEY = "5911714ce3ffbc56f7064a9ad0708e0c" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Кнопка для удобства
keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Пример: Нарисуй киберпанк город")]],
    resize_keyboard=True
)

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Привет! Я готов рисовать. Напиши 'Нарисуй [описание]' и я создам для тебя изображение.",
        reply_markup=keyboard
    )

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    if not prompt:
        return await message.answer("Пожалуйста, напиши что именно нарисовать. Например: 'Нарисуй кота в скафандре'.")
    
    msg = await message.answer("⏳ Отправляю запрос в нейросеть...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "nano-banana-2",
        "input": {
            "prompt": prompt,
            "image_input": [],
            "aspect_ratio": "auto",
            "resolution": "1K",
            "output_format": "png"
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Создаем задачу
            resp = await client.post(f"{API_BASE_URL}/api/v1/jobs/createTask", json=payload, headers=headers)
            if resp.status_code != 200:
                return await msg.edit_text(f"❌ Ошибка API: {resp.status_code}. Проверь баланс на kie.ai.")
            
            task_id = resp.json()["data"]["taskId"]
            await msg.edit_text("🎨 Задача принята! Рисую... (обычно это занимает 15-30 секунд)")
            
            # 2. Опрашиваем статус
            for i in range(20):
                await asyncio.sleep(5)
                status_resp = await client.get(f"{API_BASE_URL}/api/v1/jobs/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json().get("data", {})
                
                status = data.get("status")
                if status == "success":
                    image_url = data.get("result", {}).get("url")
                    await message.answer_photo(photo=image_url, caption=f"Готово: {prompt}")
                    return await msg.delete()
                elif status == "failed":
                    return await msg.edit_text("❌ Генерация не удалась (ошибка нейросети).")
            
            await msg.edit_text("⚠️ Время ожидания вышло. Попробуй позже.")
        except Exception as e:
            await msg.edit_text(f"⚠️ Ошибка выполнения: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
