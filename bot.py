import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import datetime

TOKEN = "8748882626:AAEqjUaThnzrFvJRTYucKRj757cEmcBD3II"
MY_TELEGRAM_ID = 8652729878

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def get_github_deep_info(session, query):
    """Надежный сбор данных с GitHub с отладкой"""
    url = f"https://api.github.com/users/{query}"
    headers = {"User-Agent": "OSINT-Bot"}
    try:
        async with session.get(url, headers=headers, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                created_raw = data.get('created_at', '')
                created_date = created_raw[:10] if created_raw else "Не указано"
                location = data.get('location') or 'Не указана'
                name = data.get('name') or 'Не указано'
                
                return (
                    f"🐙 <b>GitHub Dossier:</b>\n"
                    f"  ├ 📅 Дата регистрации: <b>{created_date}</b>\n"
                    f"  ├ 📍 Локация: <b>{location}</b>\n"
                    f"  ├ Имя: {name}\n"
                    f"  ├ Репозитории: {data.get('public_repos', 0)}\n"
                    f"  ├ Подписчики: {data.get('followers', 0)}\n"
                    f"  └ Ссылка: {data.get('html_url')}"
                )
    except Exception as e:
        print(f"GitHub Error: {e}")
    return None

async def search_web_profiles(session, query):
    """Проверка платформ с точным статусом"""
    found = []
    platforms = {
        "Telegram": f"https://t.me/{query}",
        "Steam": f"https://steamcommunity.com/id/{query}",
        "Habr": f"https://habr.com/ru/users/{query}/",
        "Twitch": f"https://www.twitch.tv/{query}",
        "SoundCloud": f"https://soundcloud.com/{query}",
        "Pinterest": f"https://www.pinterest.com/{query}/",
        "TikTok": f"https://www.tiktok.com/@{query}",
        "X (Twitter)": f"https://x.com/{query}"
    }

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for name, url in platforms.items():
        try:
            async with session.get(url, headers=headers, timeout=4, allow_redirects=True) as resp:
                if resp.status == 200:
                    found.append(f"• <b>{name}</b>: {url}")
        except Exception:
            pass
            
    return found

@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id != MY_TELEGRAM_ID:
        return
    await message.answer("🎯 OSINT-модуль активен. Введи ник для поиска даты регистрации и профилей:")

@dp.message()
async def handle_search(message: Message):
    if message.from_user.id != MY_TELEGRAM_ID:
        return
    
    query = message.text.strip().lstrip('@')
    if not query:
        await message.answer("⚠️ Введи корректный никнейм.")
        return

    wait_msg = await message.answer(f"🔍 Сканирую открытые источники для: <code>{query}</code>...", parse_mode="HTML")

    async with aiohttp.ClientSession() as session:
        gh_task = get_github_deep_info(session, query)
        sites_task = search_web_profiles(session, query)

        github_data, site_results = await asyncio.gather(gh_task, sites_task)

    blocks = [f"🎯 <b>Досье по цели: <code>{query}</code></b>\n"]

    if github_data:
        blocks.append(github_data + "\n")
    else:
        blocks.append(f"🐙 <b>GitHub:</b> Аккаунт не найден или заблокирован API\n")

    if site_results:
        blocks.append(f"🌐 <b>Активные платформы ({len(site_results)}):</b>\n" + "\n".join(site_results))
    else:
        blocks.append("🌐 <b>Активные платформы:</b> Ничего не найдено")

    final_text = "\n".join(blocks)
    await bot.edit_message_text(final_text, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="HTML", disable_web_page_preview=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
