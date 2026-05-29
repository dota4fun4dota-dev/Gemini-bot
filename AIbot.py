import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

BOT_TOKEN = "8980453196:AAGiMgy8bohMdOM6Z3nGpmos_ysCr2W_-Us"
API_BASE_URL = "https://api.kie.ai" 
# Используем полный ключ, который ты копировал
API_KEY = "5911714ce3ffbc56f7064a9ad0708e0c" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Готов к работе. Напиши 'Нарисуй [описание]'.")

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    msg = await message.answer("⏳ Создаю задачу...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "nano-banana-2",
        "input": {"prompt": prompt, "aspect_ratio": "1:1", "resolution": "1K"}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Создание
            resp = await client.post(f"{API_BASE_URL}/api/v1/jobs/createTask", json=payload, headers=headers)
            task_id = resp.json().get("data", {}).get("taskId")
            await msg.edit_text(f"🎨 Задача {task_id} принята. Жду результат (это может занять время)...")
            
            # 2. Опрос статуса
            for i in range(20):
                await asyncio.sleep(10)
                status_resp = await client.get(f"{API_BASE_URL}/api/v1/jobs/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json()
                
                # ВАЖНО: СМОТРИ ЛОГИ RAILWAY ПОСЛЕ ЭТОЙ СТРОКИ
                logging.info(f"DEBUG_STATUS: {data}")
                
                job_data = data.get("data", {})
                status = job_data.get("status")
                
                if status == "success":
                    image_url = job_data.get("result", {}).get("url")
                    return await message.answer_photo(photo=image_url, caption="Готово!")
                
            await msg.edit_text("⚠️ Сервер долго отвечает. Проверь логи Railway для отладки.")
        except Exception as e:
            await msg.edit_text(f"⚠️ Ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
