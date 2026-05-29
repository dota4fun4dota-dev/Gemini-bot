import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

BOT_TOKEN = "8980453196:AAGiMgy8bohMdOM6Z3nGpmos_ysCr2W_-Us"
API_BASE_URL = "https://api.kie.ai" 
API_KEY = "5911714ce3ffbc56f7064a9ad0708e0c" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Я готов! Напиши 'Нарисуй [описание]'.")

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    msg = await message.answer("⏳ Создаю задачу...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "nano-banana-2", "input": {"prompt": prompt}}
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/api/v1/jobs/createTask", json=payload, headers=headers)
            task_id = resp.json()["data"]["taskId"]
            await msg.edit_text(f"🎨 Задача {task_id} принята. Жду завершения...")
            
            # Увеличил время до 300 секунд (30 раз по 10 сек)
            for i in range(30):
                await asyncio.sleep(10)
                status_resp = await client.get(f"{API_BASE_URL}/api/v1/jobs/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json().get("data", {})
                
                # ВАЖНО: это выведет в логи ВСЕ поля, которые прислал сервер
                logging.info(f"СЕРВЕР ОТВЕТИЛ: {data}")
                
                if data.get("state") == "success":
                    image_url = data.get("result", {}).get("url")
                    await message.answer_photo(photo=image_url, caption="Готово!")
                    return await msg.delete()
                
            await msg.edit_text("⚠️ Сервер всё ещё 'в процессе'. Проверь логи Railway!")
        except Exception as e:
            await msg.edit_text(f"⚠️ Ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
