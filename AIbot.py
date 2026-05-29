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
    await message.answer("Готов! Напиши 'Нарисуй [описание]'.")

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    msg = await message.answer("⏳ Создаю задачу...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "nano-banana-2", "input": {"prompt": prompt}}
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Создание
            resp = await client.post(f"{API_BASE_URL}/api/v1/jobs/createTask", json=payload, headers=headers)
            # Извлекаем taskId прямо из корня или из data, если есть
            resp_data = resp.json()
            task_id = resp_data.get("taskId") or resp_data.get("data", {}).get("taskId")
            
            await msg.edit_text(f"🎨 Задача {task_id} принята. Жду завершения...")
            
            # 2. Опрос статуса
            for i in range(30):
                await asyncio.sleep(10)
                status_resp = await client.get(f"{API_BASE_URL}/api/v1/jobs/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json() # Берем весь JSON целиком
                
                logging.info(f"СЕРВЕР ОТВЕТИЛ: {data}")
                
                # ИСПРАВЛЕНИЕ: ищем state в корне ответа
                if data.get("state") == "success":
                    # Ссылка обычно приходит в resultJson или result
                    import json
                    res_json = data.get("resultJson")
                    image_url = data.get("result", {}).get("url")
                    
                    if res_json:
                        image_url = json.loads(res_json).get("url")
                    
                    await message.answer_photo(photo=image_url, caption="Готово!")
                    return await msg.delete()
                
                elif data.get("state") == "failed":
                    return await msg.edit_text("❌ Ошибка: Сервер вернул failed.")
            
            await msg.edit_text("⚠️ Время вышло. Сервер всё ещё в статусе 'waiting'.")
        except Exception as e:
            await msg.edit_text(f"⚠️ Ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
