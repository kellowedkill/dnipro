import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
import random
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Чтение переменных окружения
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("API_TOKEN is not set in environment variables")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8070055531"))

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Хранилища для заказов
user_orders = {}
pending_orders = {}
all_orders = {}
awaiting_photo_to_send = {}

# HTTP-сервер для Render
async def health_check(request):
    return web.Response(text="Bot is running")

app = web.Application()
app.router.add_get('/', health_check)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_orders.pop(message.from_user.id, None)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Днепр", callback_data="city_dnepr"))

    await message.answer(
        f"Ку бро, - {message.from_user.username or message.from_user.first_name}\n\n"
        "Рад тебя видеть в нашем шопе.\n"
        "Оператор: @shmalebanutaya\n"
        "Не забудь подписаться на канал - [ссылка]",
        reply_markup=markup
    )

@dp.callback_query_handler(lambda c: c.data == "city_dnepr")
async def city_selected(callback_query: types.CallbackQuery):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Товар 1 - 1гр - 300 грн", callback_data="product_1"),
        InlineKeyboardButton("Товар 2 - 2гр - 570 грн", callback_data="product_2"),
        InlineKeyboardButton("Товар 3 - 3гр - 820 грн", callback_data="product_3")
    )
    await callback_query.message.edit_text("Вы выбрали город Днепр.\nЧто тебе присмотрелось?", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith("product_"))
async def product_selected(callback_query: types.CallbackQuery):
    product_map = {
        "product_1": "Товар 1 - 1гр - 300 грн",
        "product_2": "Товар 2 - 2гр - 570 грн",
        "product_3": "Товар 3 - 3гр - 820 грн",
    }
    product_name = product_map[callback_query.data]
    price = product_name.split('-')[-1].strip()

    user_orders[callback_query.from_user.id] = {
        "product": product_name,
        "price": price
    }

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Кирова", callback_data="area_kirova"),
        InlineKeyboardButton("Начало пр. Богдана Хмельницкого", callback_data="area_bh")
    )
    await callback_query.message.edit_text(
        f"Избран продукт: {product_name}\n"
        f"Коротко о товаре: (сам изменишь)\n"
        f"Цена: {price}\n"
        "Выберите подходящий район:", reply_markup=markup
    )

@dp.callback_query_handler(lambda c: c.data.startswith("area_"))
async def area_selected(callback_query: types.CallbackQuery):
    data = user_orders.get(callback_query.from_user.id)
    if not data:
        return await callback_query.message.edit_text("Что-то пошло не так. Попробуй снова /start")

    area_map = {
        "area_kirova": "Кирова",
        "area_bh": "Начало пр. Богдана Хмельницкого"
    }
    area = area_map[callback_query.data]

    order_id = random.randint(20000, 99999)
    data.update({
        "order_id": order_id,
        "city": "Днепр",
        "area": area
    })

    full_order = {
        **data,
        "user_id": callback_query.from_user.id,
        "username": callback_query.from_user.username
    }

    user_orders[callback_query.from_user.id] = data
    pending_orders[order_id] = full_order
    all_orders[order_id] = full_order

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(" 💳 Оплата на карту", callback_data="pay_card"))

    await callback_query.message.edit_text(
        f"Заказ создан! Адрес забронирован!\n\n"
        f"Ваш заказ №: {order_id}\n"
        f"Город: {data['city']}\n"
        f"Товар: {data['product']}\n"
        f"Цена: {data['price']}\n"
        "Метод оплаты:", reply_markup=markup
    )

    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(
        InlineKeyboardButton("✅ Подтвердить", callback_data=f"approve_{order_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{order_id}")
    )

    await bot.send_message(
        ADMIN_ID,
        f"📦 Новый заказ #{order_id}\n"
        f"Юзер: @{callback_query.from_user.username}\n"
        f"Товар: {data['product']}\n"
        f"Цена: {data['price']}\n"
        f"Район: {data['area']}",
        reply_markup=admin_markup
    )

# Запуск бота и HTTP-сервера
if __name__ == '__main__':
    from aiogram.utils.executor import start_polling
    import asyncio

    async def start_http_server():
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        logging.info("HTTP server started on port 8080")

    loop = asyncio.get_event_loop()
    loop.create_task(start_http_server())
    executor.start_polling(dp, skip_updates=True)
