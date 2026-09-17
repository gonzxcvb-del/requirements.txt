import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

TOKEN = "8748882626:AAEqjUaThnzrFvJRTYucKRj757cEmcBD3II"
MY_TELEGRAM_ID = 8652729878

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Расширенная база платформ (около 20 популярных источников)
PLATFORMS = {
    "GitHub": "https://github.com/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "X (Twitter)": "https://x.com/{}",
    "Instagram": "https://www.instagram.com/{}/",
    "Pinterest": "https://www.pinterest.com/{}/",
    "Steam": "https://steamcommunity.com/id/{}",
    "Habr": "https://habr.com/ru/users/{}/",
    "Telegram Channel": "https://t.me/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "Twitch": "https://www.twitch.tv/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Spotify": "https://open.spotify.com/user/{}",
    "Steam Community": "https://steamcommunity.com/id/{}",
    "DeviantArt": "https://www.deviantart.com/{}",
    "VK": "https://vk.com/{}",
    "Pikabu": "https://pikabu.co/@{}"
}

async def check_site(session, name, url_template, query):
    url = url_template.format(query)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        async with session.get(url, headers=headers, timeout=5, allow_redirects=True) as response:
            if response.status == 200:
                return f"• <b>{name}</b>: {url}"
    except Exception:
        pass
    return None

async def get_github_info(session, query):
    api_url = f"https://api.github.com/users/{query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with session.get(api_url, headers=headers, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                return (
                    f"🐙 <b>GitHub API Details:</b>\n"
                    f"  ├ Имя: {data.get('name') or 'Не указано'}\n"
                    f"  ├ О себе: {data.get('bio') or 'Нет'}\n"
                    f"  ├ Компания: {data.get('company') or 'Нет'}\n"
                    f"  ├ Локация: {data.get('location') or 'Не указана'}\n"
                    f"  ├ Публичных репо: {data.get('public_repos', 0)}\n"
                    f"  ├ Подписчики: {data.get('followers', 0)} | Подписки: {data.get('following', 0)}\n"
                    f"  └ Создан: {data.get('created_at', '')[:10]}\n"
                    f"  🔗 <i>{data.get('html_url')}</i>"
                )
    except Exception:
        pass
    return None

@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id != MY_TELEGRAM_ID:
        return
    await message.answer("🔥 OSINT-бот обновлен! Впиши ник для расширенного сканирования.")

@dp.message()
async def handle_search(message: Message):
    if message.from_user.id != MY_TELEGRAM_ID:
        return
    
    query = message.text.strip().lstrip('@')
    if not query:
        await message.answer("⚠️ Введи корректный юзернейм.")
        return

    wait_msg = await message.answer(f"🔍 Запускаю глубокий поиск по базам данных для: <code>{query}</code>...", parse_mode="HTML")
    
    found_sites = []
    github_details = None

    async with aiohttp.ClientSession() as session:
        gh_task = get_github_info(session, query)
        site_tasks = [check_site(session, name, url, query) for name, url in PLATFORMS.items()]
        
        results = await asyncio.gather(*site_tasks)
        github_details = await gh_task
        
        for res in results:
            if res:
                found_sites.append(res)

    response_blocks = [f"🎯 <b>Результаты OSINT для <code>{query}</code>:</b>\n"]
    
    if github_details:
        response_blocks.append(github_details + "\n")
        
    if found_sites:
        response_blocks.append(f"🌐 <b>Найдено профилей ({len(found_sites)}):</b>\n" + "\n".join(found_sites))
    
    if not github_details and not found_sites:
        final_text = f"❌ По нику <code>{query}</code> ничего не найдено."
    else:
        final_text = "\n".join(response_blocks)

    await bot.edit_message_text(final_text, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="HTML", disable_web_page_preview=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
