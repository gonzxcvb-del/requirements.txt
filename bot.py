import asyncio
import aiohttp
import re
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

TOKEN = "8748882626:AAEqjUaThnzrFvJRTYucKRj757cEmcBD3II"
MY_TELEGRAM_ID = 8652729878

bot = Bot(token=TOKEN)
dp = Dispatcher()

IP_REGEX = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')

async def get_ip_info(session, ip):
    """Пробив IP-адреса"""
    url = f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,org,query"
    try:
        async with session.get(url, timeout=5) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("status") == "success":
                    return (
                        f"📍 <b>IP Intelligence Dossier:</b>\n"
                        f"  ├ IP: <code>{data.get('query')}</code>\n"
                        f"  ├ Страна: <b>{data.get('country')}</b>\n"
                        f"  ├ Регион: {data.get('regionName', 'Не указан')}\n"
                        f"  ├ Город: <b>{data.get('city', 'Не указан')}</b>\n"
                        f"  └ Провайдер: {data.get('isp')} ({data.get('org')})"
                    )
    except Exception:
        pass
    return None

async def get_github_deep_info(session, query):
    """Поиск по никнейму (GitHub)"""
    url = f"https://api.github.com/users/{query}"
    headers = {"User-Agent": "OSINT-Bot"}
    try:
        async with session.get(url, headers=headers, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                return (
                    f"🐙 <b>GitHub Dossier:</b>\n"
                    f"  ├ Регистрация: <b>{data.get('created_at', '')[:10]}</b>\n"
                    f"  ├ Локация: <b>{data.get('location') or 'Не указана'}</b>\n"
                    f"  ├ Имя: {data.get('name') or 'Скрыто'}\n"
                    f"  └ Ссылка: {data.get('html_url')}"
                )
    except Exception:
        pass
    return None

async def search_web_profiles(session, query):
    """Поиск профилей по никнейму на сайтах"""
    found = []
    platforms = {
        "Telegram": f"https://t.me/{query}",
        "Steam": f"https://steamcommunity.com/id/{query}",
        "Habr": f"https://habr.com/ru/users/{query}/",
        "Twitch": f"https://www.twitch.tv/{query}",
        "TikTok": f"https://www.tiktok.com/@{query}",
        "X (Twitter)": f"https://x.com/{query}"
    }
    headers = {"User-Agent": "Mozilla/5.0"}
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
    await message.answer("🎯 Бот запущен.\n🔹 Введи **никнейм** для поиска профилей.\n🔹 Введи **IP-адрес** для гео-пробива.")

@dp.message()
async def handle_search(message: Message):
    if message.from_user.id != MY_TELEGRAM_ID:
        return
    
    query = message.text.strip().lstrip('@')
    if not query:
        await message.answer("⚠️ Введи данные для поиска.")
        return

    wait_msg = await message.answer(f"🔍 Анализирую цель: <code>{query}</code>...", parse_mode="HTML")

    async with aiohttp.ClientSession() as session:
        if IP_REGEX.match(query):
            # Если это IP
            ip_data = await get_ip_info(session, query)
            final_text = ip_data if ip_data else f"❌ Не удалось получить данные по IP <code>{query}</code>."
        else:
            # Если это юзернейм
            gh_task = get_github_deep_info(session, query)
            sites_task = search_web_profiles(session, query)
            github_data, site_results = await asyncio.gather(gh_task, sites_task)

            blocks = [f"🎯 <b>Досье по нику: <code>{query}</code></b>\n"]
            if github_data:
                blocks.append(github_data + "\n")
            else:
                blocks.append("🐙 <b>GitHub:</b> Аккаунт не найден\n")

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
