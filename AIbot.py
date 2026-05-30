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
CHAT_API_URL = "https://api.kie.ai/gemini-3.1-pro/v1/chat/completions"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.startup()
async def on_startup():
    await bot.delete_webhook(drop_pending_updates=True)

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Бот запущен. Напиши 'нарисуй [текст]' или просто общайся со мной.")

@dp.message(F.text)
async def handle_text(message: Message):
    # ЛОГИКА РИСОВАНИЯ
    if message.text.lower().startswith("нарисуй"):
        msg = await message.answer("🎨 Рисую...")
        prompt = message.text.lower().replace("нарисуй", "").strip()
        payload = {"model": "flux-2/pro-text-to-image", "input": {"prompt": prompt, "aspect_ratio": "1:1"}}
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
                if not resp.text: 
                    await msg.edit_text("Ошибка: API вернуло пустой ответ.")
                    return
                data = resp.json()
                
                if not isinstance(data, dict) or "data" not in data:
                    await msg.edit_text(f"Ошибка API: {str(data)[:50]}")
                    return
                
                task_id = data["data"].get("taskId")
                if not task_id: 
                    await msg.edit_text("Ошибка: taskId не найден.")
                    return
                
                await msg.edit_text("Задача принята. Ожидайте...")
                for i in range(20):
                    await asyncio.sleep(10)
                    res = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
                    res_data = res.json()
                    if res_data and isinstance(res_data, dict) and res_data.get("data", {}).get("resultJson"):
                        url = json.loads(res_data["data"]["resultJson"]).get("resultUrls", [None])[0]
                        if url: 
                            await message.answer_photo(photo=url, caption="✨ Готово!")
                            await msg.delete()
                            return
                await msg.edit_text("Время ожидания вышло.")
            except Exception as e:
                await msg.edit_text(f"Ошибка рисования: {str(e)}")

    # ЛОГИКА ОБЩЕНИЯ
    else:
        msg = await message.answer("🤔 Думаю...")
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"messages": [{"role": "user", "content": message.text}]}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(CHAT_API_URL, json=payload, headers=headers)
                if not resp.text: 
                    await msg.edit_text("Ошибка: API вернуло пустоту.")
                    return
                data = resp.json()
                
                if isinstance(data, dict) and "choices" in data:
                    answer = data["choices"][0]["message"]["content"]
                    await msg.delete()
                    await message.answer(answer)
                else:
                    await msg.edit_text(f"Ошибка чата: {str(data)[:50]}")
            except Exception as e:
                await msg.edit_text(f"Ошибка общения: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
