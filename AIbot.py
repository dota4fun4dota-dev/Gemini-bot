import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

# ВСТАВЬ СЮДА СВОЙ ТОКЕН И КЛЮЧ
BOT_TOKEN = "8980453196:AAGiMgy8bohMdOM6Z3nGpmos_ysCr2W_-Us"
API_KEY = "5911714ce3ffbc56f7064a9ad0708e0c" 
API_BASE = "https://api.kie.ai/api/v1/jobs"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! Напиши 'Нарисуй [описание]'")

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    msg = await message.answer("🎨 Принимаю задачу...")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 1. Создаем задачу
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{API_BASE}/createTask", 
                json={"model": "nano-banana-2", "input": {"prompt": prompt}},
                headers=headers
            )
            
            if resp.status_code != 200:
                return await msg.edit_text(f"Ошибка API: {resp.text}")
            
            task_id = resp.json().get("data", {}).get("taskId")
            await msg.edit_text(f"Задача принята ({task_id}). Жду результат...")

            # 2. Опрашиваем статус (polling)
            for _ in range(15):
                await asyncio.sleep(5)
                status_resp = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json().get("data", {})
                
                if data.get("status") == "success":
                    await message.answer_photo(photo=data["result"]["url"], caption="Готово!")
                    return await msg.delete()
                elif data.get("status") == "failed":
                    return await msg.edit_text("Генерация не удалась.")
            
            await msg.edit_text("Время вышло. Попробуй еще раз.")
            
        except Exception as e:
            await msg.edit_text(f"Ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
