import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

BOT_TOKEN = "8980453196:AAGiMgy8bohMdOM6Z3nGpmos_ysCr2W_-Us"
API_KEY = "5911714ce3ffbc56f7064a9ad0708e0c" 
API_BASE = "https://api.kie.ai/api/v1/jobs"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Бот готов. Напиши 'Нарисуй [описание]'.")

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    msg = await message.answer("⏳ Запускаю...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "google/imagen4-fast", "input": {"prompt": prompt}}
    
    async with httpx.AsyncClient() as client:
        try:
            # Создание
            resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
            task_json = resp.json()
            task_id = task_json.get("data", {}).get("taskId")
            
            if not task_id:
                return await msg.edit_text(f"Ошибка создания: {task_json}")
            
            await msg.edit_text(f"ID задачи: {task_id}. Ожидание...")

            # Опрос
            for i in range(20):
                await asyncio.sleep(15)
                status_resp = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json()
                
                # ЛОГИРУЕМ СЫРОЙ ОТВЕТ
                logging.info(f"СЫРОЙ ОТВЕТ СЕРВЕРА: {data}")
                
                # Пытаемся найти результат в любом поле
                if data and "data" in data and "result" in data["data"]:
                    url = data["data"]["result"].get("url")
                    if url:
                        await message.answer_photo(photo=url, caption="Готово!")
                        return await msg.delete()
            
            await msg.edit_text("Не дождался ответа от сервера.")
        except Exception as e:
            await msg.edit_text(f"Ошибка: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
