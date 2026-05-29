import asyncio
import logging
import httpx
import json
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
            task_id = resp.json().get("taskId") or resp.json().get("data", {}).get("taskId")
            await msg.edit_text(f"🎨 Задача {task_id} принята. Рисую, подожди...")
            
            # Увеличенное время ожидания для медленных генераций
            for i in range(40):
                await asyncio.sleep(15) 
                status_resp = await client.get(f"{API_BASE_URL}/api/v1/jobs/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json()
                
                # Проверяем состояние
                if data.get("state") == "success":
                    res_json = data.get("resultJson")
                    image_url = data.get("result", {}).get("url")
                    if res_json:
                        image_url = json.loads(res_json).get("url")
                    
                    if image_url:
                        await message.answer_photo(photo=image_url, caption="Готово!")
                        return await msg.delete()
                
                # Если state всё еще 'waiting' или 'processing', цикл продолжается
                logging.info(f"Ожидание генерации (попытка {i+1}/40)...")
            
            await msg.edit_text("⚠️ Сервер долго готовит картинку. Попробуй позже.")
        except Exception as e:
            await msg.edit_text(f"⚠️ Ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
