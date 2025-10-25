

import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command

# 🔑 Укажи токен своего бота
BOT_TOKEN = "7987484184:AAE6t7YiCDpb7dhyY4pugJdrh9KRCdq-IQk"

# 📊 Список доступных криптовалют
CRYPTO_LIST = ["BTCUSDT", "TONUSDT", "ETHUSDT", "SOLUSDT", "USDTUSDT"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🧠 Хранилища данных
user_choices = {}        # user_id → "BTCUSDT"
previous_prices = {}     # user_id → последняя цена отслеживаемой крипты


# 🧾 Команда /start
@dp.message(Command("start"))
async def start_cmd(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Аналитика", callback_data="analytics")],
            [InlineKeyboardButton(text="💰 Выбрать криптовалюту для отслеживания", callback_data="choose_crypto")]
        ]
    )
    await message.answer(
        "👋 Привет! Я крипто-аналитик.\n\n"
        "🔹 Нажми *Аналитика*, чтобы посмотреть текущие цены.\n"
        "🔹 Или выбери криптовалюту, которую я буду отслеживать 📈",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


# ⚙️ Клавиатура выбора криптовалюты
def get_crypto_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="₿ Bitcoin (BTC)", callback_data="BTCUSDT")],
        [InlineKeyboardButton(text="💎 Toncoin (TON)", callback_data="TONUSDT")],
        [InlineKeyboardButton(text="Ξ Ethereum (ETH)", callback_data="ETHUSDT")],
        [InlineKeyboardButton(text="🌞 Solana (SOL)", callback_data="SOLUSDT")],
        [InlineKeyboardButton(text="💵 Tether (USDT)", callback_data="USDTUSDT")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# 🔘 Кнопка "Выбрать крипту"
@dp.callback_query(F.data == "choose_crypto")
async def choose_crypto(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Выбери криптовалюту, которую хочешь отслеживать 👇",
        reply_markup=get_crypto_keyboard()
    )


# ⚡ Обработка выбора криптовалюты
@dp.callback_query(F.data.in_(CRYPTO_LIST))
async def select_crypto(callback: CallbackQuery):
    user_id = callback.from_user.id
    crypto = callback.data

    user_choices[user_id] = crypto
    previous_prices[user_id] = None

    await callback.answer()
    await callback.message.edit_text(
        f"✅ Теперь я отслеживаю *{crypto.replace('USDT', '')}*.\n"
        "Буду уведомлять, если цена изменится больше чем на 1% 📈📉",
        parse_mode="Markdown"
    )


# 📈 Получение всех цен
async def get_all_prices():
    url = "https://api.binance.com/api/v3/ticker/price"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    result = {}
    for item in data:
        if item["symbol"] in CRYPTO_LIST:
            result[item["symbol"]] = float(item["price"])
    return result


# 🔹 Получение цены одной крипты
async def get_price(symbol: str):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
    return float(data["price"])


# 📊 Кнопка "Аналитика"
@dp.callback_query(F.data == "analytics")
async def analytics_callback(callback: CallbackQuery):
    await callback.answer()
    prices = await get_all_prices()

    text = "📊 *Текущие цены криптовалют:*\n\n"
    for symbol, price in prices.items():
        name = symbol.replace("USDT", "")
        text += f"• {name}: `{price:.2f}$`\n"

    text += "\n🔄 Нажми кнопку ещё раз, чтобы обновить данные."

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Обновить", callback_data="analytics")],
            [InlineKeyboardButton(text="💰 Отслеживать криптовалюту", callback_data="choose_crypto")]
        ]
    )

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)


# 🔔 Фоновая задача — отслеживание изменений
async def price_monitor():
    print("🔁 Мониторинг запущен...")
    while True:
        for user_id, symbol in list(user_choices.items()):
            try:
                current_price = await get_price(symbol)
                old_price = previous_prices.get(user_id)

                if old_price is not None:
                    change = ((current_price - old_price) / old_price) * 100
                    if abs(change) >= 1:
                        direction = "📈 выросла" if change > 0 else "📉 упала"
                        msg = (
                            f"💰 *{symbol.replace('USDT', '')}* {direction} на {abs(change):.2f}%\n"
                            f"Текущая цена: `{current_price:.2f}$`"
                        )
                        await bot.send_message(user_id, msg, parse_mode="Markdown")

                previous_prices[user_id] = current_price
            except Exception as e:
                print(f"Ошибка при обновлении {symbol}: {e}")

        await asyncio.sleep(60)  # проверка каждую минуту


# ▶️ Запуск бота
async def main():
    print("✅ Бот запущен...")
    asyncio.create_task(price_monitor())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
