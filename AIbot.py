@dp.message(F.text)
async def handle_text(message: Message):
    # 1. ЛОГИКА РИСОВАНИЯ
    if message.text.lower().startswith("нарисуй"):
        msg = await message.answer("🎨 Рисую...")
        prompt = message.text.lower().replace("нарисуй", "").strip()
        payload = {"model": "flux-2/pro-text-to-image", "input": {"prompt": prompt, "aspect_ratio": "1:1"}}
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{API_BASE}/createTask", json=payload, headers=headers)
                data = resp.json()
                
                # ЖЕСТКАЯ ПРОВЕРКА: если data - это None или нет ключа 'data', выходим
                if data is None or not isinstance(data, dict) or "data" not in data:
                    return await msg.edit_text(f"Ошибка API: ответ пуст или некорректен. {resp.text[:50]}")
                
                task_id = data["data"].get("taskId")
                if not task_id:
                    return await msg.edit_text("Ошибка: не удалось получить taskId.")
                
                await msg.edit_text("Задача принята. Ожидайте...")
                
                for i in range(20):
                    await asyncio.sleep(10)
                    res = await client.get(f"{API_BASE}/recordInfo?taskId={task_id}", headers=headers)
                    res_data = res.json()
                    if res_data and isinstance(res_data, dict) and res_data.get("data", {}).get("resultJson"):
                        url = json.loads(res_data["data"]["resultJson"]).get("resultUrls", [None])[0]
                        if url: await message.answer_photo(photo=url, caption="✨ Готово!"); return await msg.delete()
                await msg.edit_text("Время ожидания вышло.")
            except Exception as e:
                await msg.edit_text(f"Ошибка обработки: {str(e)}")

    # 2. ЛОГИКА ОБЩЕНИЯ
    else:
        msg = await message.answer("🤔 Думаю...")
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"messages": [{"role": "user", "content": message.text}]}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(CHAT_API_URL, json=payload, headers=headers)
                data = resp.json()
                if data and isinstance(data, dict) and "choices" in data:
                    answer = data["choices"][0]["message"]["content"]
                    await msg.delete()
                    await send_long_message(message, answer)
                else:
                    await msg.edit_text("Ошибка ответа от ИИ.")
            except Exception as e:
                await msg.edit_text(f"Ошибка: {str(e)}")
