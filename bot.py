import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = "8748882626:AAEqjUaThnzrFvJRTYucKRj757cEmcBD3II"
MY_TELEGRAM_ID = 8652729878

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id != MY_TELEGRAM_ID:
        return
    await message.answer("⚡ Бот на связи, хозяин. Работаю 24/7 в облаке!")

@dp.message()
async def handle_search(message: types.Message):
    if message.from_user.id != MY_TELEGRAM_ID:
        return
    await message.answer(f"🔍 Запрос принят: <code>{message.text}</code>", parse_mode="HTML")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
