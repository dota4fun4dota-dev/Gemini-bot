import asyncio
import logging
import httpx
import json
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
    await message.answer("Привет! Напиши 'Нарисуй [описание]'.")

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    msg = await message.answer("⏳ Создаю задачу...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "imagen4-fast", "input": {"prompt": prompt}}
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
            
            # Безопасная проверка JSON ответа
            task_data = resp.json() if resp.text else {}
            # Извлекаем taskId, учитывая возможные варианты структуры
            task_id = task_data.get("taskId") or (task_data.get("data") or {}).get("taskId")
            
            if not task_id:
                await msg.edit_text(f"❌ Не удалось создать задачу. Ответ сервера: {resp.text}")
                return
            
            await msg.edit_text(f"🎨 Задача принята ({task_id}). Ожидание...")

            # Опрос статуса с защитой от None
            for i in range(30):
                await asyncio.sleep(10)
                status_resp = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json() if status_resp.text else {}
                
                # Если data пустая или произошла ошибка
                if not data:
                    continue
                
                # Безопасно получаем state
                state = data.get("state")
                logging.info(f"Статус (попытка {i+1}): {state}")
                
                if state == "success":
                    # Безопасно пытаемся достать URL
                    result = data.get("result") or {}
                    image_url = result.get("url")
                    
                    if not image_url and data.get("resultJson"):
                        try:
                            image_url = json.loads(data["resultJson"]).get("url")
                        except:
                            pass
                    
                    if image_url:
                        await message.answer_photo(photo=image_url, caption=f"Готово: {prompt}")
                        return await msg.delete()
                    else:
                        await msg.edit_text("❌ Задача выполнена, но ссылка на фото отсутствует.")
                        return
                
                elif state == "failed":
                    await msg.edit_text("❌ Генерация завершилась с ошибкой.")
                    return
            
            await msg.edit_text("⚠️ Время вышло. Сервер не успел сгенерировать картинку.")
            
        except Exception as e:
            logging.error(f"Ошибка в коде: {e}")
            await msg.edit_text(f"⚠️ Ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
