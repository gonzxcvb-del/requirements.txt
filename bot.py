import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

TOKEN = "8748882626:AAEqjUaThnzrFvJRTYucKRj757cEmcBD3II"
MY_TELEGRAM_ID = 8652729878

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def get_github_deep_info(session, query):
    """Глубокий сбор по GitHub API"""
    url = f"https://api.github.com/users/{query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with session.get(url, headers=headers, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                return (
                    f"🐙 <b>GitHub Intelligence:</b>\n"
                    f"  ├ Имя: {data.get('name') or 'Скрыто'}\n"
                    f"  ├ Bio: {data.get('bio') or 'Нет'}\n"
                    f"  ├ Компания: {data.get('company') or 'Нет'}\n"
                    f"  ├ Локация: {data.get('location') or 'Не указана'}\n"
                    f"  ├ Репозитории: {data.get('public_repos', 0)} | Гиссы: {data.get('public_gists', 0)}\n"
                    f"  ├ Подписчики: {data.get('followers')} | Подписки: {data.get('following')}\n"
                    f"  ├ Создан: {data.get('created_at', '')[:10]}\n"
                    f"  └ Профиль: {data.get('html_url')}"
                )
    except Exception:
        pass
    return None

async def get_reddit_info(session, query):
    """Проверка профиля Reddit через открытое JSON API"""
    url = f"https://www.reddit.com/user/{query}/about.json"
    headers = {"User-Agent": "Mozilla/5.0 OSINTBot/1.0"}
    try:
        async with session.get(url, headers=headers, timeout=5) as response:
            if response.status == 200:
                data = (await response.json()).get("data", {})
                created = data.get("created_utc")
                import datetime
                created_date = datetime.datetime.fromtimestamp(created).strftime('%Y-%m-%d') if created else "Неизвестно"
                
                return (
                    f"🤖 <b>Reddit Profile:</b>\n"
                    f"  ├ Karma (Link/Comment): {data.get('link_karma', 0)} / {data.get('comment_karma', 0)}\n"
                    f"  ├ Премиум: {'Да' if data.get('is_gold') else 'Нет'}\n"
                    f"  ├ Создан: {created_date}\n"
                    f"  └ Ссылка: https://reddit.com/user/{query}"
                )
    except Exception:
        pass
    return None

async def search_web_profiles(session, query):
    """Интеллектуальный сбор профилей (включая сложные соцсети через поисковые индексы)"""
    found = []
    
    # Надежные платформы с прямым доступом
    direct_platforms = {
        "Telegram": f"https://t.me/{query}",
        "Steam": f"https://steamcommunity.com/id/{query}",
        "Habr": f"https://habr.com/ru/users/{query}/",
        "Twitch": f"https://www.twitch.tv/{query}",
        "SoundCloud": f"https://soundcloud.com/{query}",
        "Pinterest": f"https://www.pinterest.com/{query}/",
        "TikTok": f"https://www.tiktok.com/@{query}",
        "X (Twitter)": f"https://x.com/{query}"
    }

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for name, url in direct_platforms.items():
        try:
            async with session.get(url, headers=headers, timeout=4, allow_redirects=True) as resp:
                # Отсекаем явные ошибки 404
                if resp.status == 200:
                    found.append(f"• <b>{name}</b>: {url}")
        except Exception:
            pass
            
    return found

@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id != MY_TELEGRAM_ID:
        return
    await message.answer("🔥 Элитный OSINT-модуль с глубоким анализом запущен. Введи никнейм:")

@dp.message()
async def handle_search(message: Message):
    if message.from_user.id != MY_TELEGRAM_ID:
        return
    
    query = message.text.strip().lstrip('@')
    if not query:
        await message.answer("⚠️ Введи корректный никнейм.")
        return

    wait_msg = await message.answer(f"⚡ Сканирую API, базы данных и сети для цели: <code>{query}</code>...", parse_mode="HTML")

    async with aiohttp.ClientSession() as session:
        gh_task = get_github_deep_info(session, query)
        reddit_task = get_reddit_info(session, query)
        sites_task = search_web_profiles(session, query)

        github_data, reddit_data, site_results = await asyncio.gather(gh_task, reddit_task, sites_task)

    blocks = [f"🎯 <b>Глубокий отчёт по цели: <code>{query}</code></b>\n"]

    if github_data:
        blocks.append(github_data + "\n")
    
    if reddit_data:
        blocks.append(reddit_data + "\n")

    if site_results:
        blocks.append(f"🌐 <b>Найденные платформы ({len(site_results)}):</b>\n" + "\n".join(site_results))

    if not github_data and not reddit_data and not site_results:
        final_text = f"❌ По нику <code>{query}</code> ничего ценного обнаружить не удалось."
    else:
        final_text = "\n".join(blocks)

    await bot.edit_message_text(final_text, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="HTML", disable_web_page_preview=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
