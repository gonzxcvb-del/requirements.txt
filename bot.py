import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

TOKEN = "8748882626:AAEqjUaThnzrFvJRTYucKRj757cEmcBD3II"
MY_TELEGRAM_ID = 8652729878

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Список сайтов для проверки по шаблону
PLATFORMS = {
    "TikTok": "https://www.tiktok.com/@{}",
    "X (Twitter)": "https://x.com/{}",
    "Instagram": "https://www.instagram.com/{}/",
    "Pinterest": "https://www.pinterest.com/{}/",
    "Steam": "https://steamcommunity.com/id/{}",
    "Habr": "https://habr.com/ru/users/{}/",
    "Telegram Channel": "https://t.me/{}"
}

async def check_site(session, name, url_template, query):
    url = url_template.format(query)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        async with session.get(url, headers=headers, timeout=5, allow_redirects=True) as response:
            # Если страница отдала 200 OK, профиль с высокой вероятностью существует
            if response.status == 200:
                return f"• <b>{name}</b>: {url}"
    except Exception:
        pass
    return None

async def get_github_info(session, query):
    """Специальный модуль для мощной инфы по GitHub API"""
    api_url = f"https://api.github.com/users/{query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with session.get(api_url, headers=headers, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                name = data.get("name") or "Не указано"
                bio = data.get("bio") or "Нет"
                company = data.get("company") or "Нет"
                location = data.get("location") or "Не указана"
                repos = data.get("public_repos", 0)
                created = data.get("created_at", "")[:10]
                
                return (
                    f"🐙 <b>GitHub (API Profile):</b>\n"
                    f"  ├ Имя: {name}\n"
                    f"  ├ О себе: {bio}\n"
                    f"  ├ Компания: {company}\n"
                    f"  ├ Локация: {location}\n"
                    f"  ├ Репозиториев: {repos}\n"
                    f"  └ Создан: {created}\n"
                    f"  🔗 <i>{data.get('html_url')}</i>"
                )
    except Exception:
        pass
    return None

@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id != MY_TELEGRAM_ID:
        return
    await message.answer("🔥 OSINT-бот заряжен! Впиши ник, чтобы начать глубокий поиск.")

@dp.message()
async def handle_search(message: Message):
    if message.from_user.id != MY_TELEGRAM_ID:
        return
    
    query = message.text.strip().lstrip('@')
    if not query:
        await message.answer("⚠️ Введи корректный юзернейм.")
        return

    wait_msg = await message.answer(f"🔍 Запускаю глубокий сбор данных по нику: <code>{query}</code>...", parse_mode="HTML")
    
    found_sites = []
    github_details = None

    async with aiohttp.ClientSession() as session:
        # Запускаем параллельно запрос к GitHub API и сканирование сайтов
        gh_task = get_github_info(session, query)
        site_tasks = [check_site(session, name, url, query) for name, url in PLATFORMS.items()]
        
        results = await asyncio.gather(*site_tasks)
        github_details = await gh_task
        
        for res in results:
            if res:
                found_sites.append(res)

    # Собираем итоговое сообщение
    response_blocks = [f"🎯 <b>Результаты анализа для <code>{query}</code>:</b>\n"]
    
    if github_details:
        response_blocks.append(github_details + "\n")
        
    if found_sites:
        response_blocks.append("🌐 <b>Найденные профили на сайтах:</b>\n" + "\n".join(found_sites))
    
    if not github_details and not found_sites:
        final_text = f"❌ По нику <code>{query}</code> ничего толкового не обнаружено."
    else:
        final_text = "\n".join(response_blocks)

    await bot.edit_message_text(final_text, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="HTML", disable_web_page_preview=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
