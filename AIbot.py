import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

# === КОНФИГУРАЦИЯ ===
BOT_TOKEN = "8980453196:AAGiMgy8bohMdOM6Z3nGpmos_ysCr2W_-Us"
API_BASE_URL = "https://api.kie.ai" 
API_KEY = "5911714ce3ffbc56f7064a9ad0708e0c" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! Напиши 'Нарисуй [описание]', и я создам картинку.")

@dp.message(F.text.lower().startswith("нарисуй"))
async def image_handler(message: Message):
    prompt = message.text.lower().replace("нарисуй", "").strip()
    if not prompt:
        return await message.answer("Укажи описание картинки!")
    
    msg = await message.answer("⏳ Запускаю Nano Banana 2...")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "nano-banana-2",
        "input": {"prompt": prompt, "aspect_ratio": "auto", "resolution": "1K", "output_format": "png"}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Создаем задачу
            resp = await client.post(f"{API_BASE_URL}/api/v1/jobs/createTask", json=payload, headers=headers)
            if resp.status_code != 200:
                return await msg.edit_text(f"❌ Ошибка API: {resp.status_code}. Проверь токен и баланс на сайте.")
            
            task_id = resp.json()["data"]["taskId"]
            await msg.edit_text("🎨 Задача принята. Ожидаю результат...")
            
            # 2. Опрашиваем статус (Polling)
            for i in range(20):
                await asyncio.sleep(5)
                status_resp = await client.get(f"{API_BASE_URL}/api/v1/jobs/recordInfo?taskId={task_id}", headers=headers)
                data = status_resp.json().get("data", {})
                
                if data.get("status") == "success":
                    image_url = data.get("result", {}).get("url")
                    await message.answer_photo(photo=image_url, caption=f"Готово: {prompt}")
                    return await msg.delete()
                elif data.get("status") == "failed":
                    return await msg.edit_text("❌ Ошибка генерации внутри нейросети.")
            
            await msg.edit_text("⚠️ Истекло время ожидания.")
        except Exception as e:
            await msg.edit_text(f"⚠️ Ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
