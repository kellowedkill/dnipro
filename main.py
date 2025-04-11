import os
import logging
import json
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Чтение переменных окружения
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("API_TOKEN is not set in environment variables")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8070055531"))

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Хранилища для заказов и состояний
user_orders = {}
pending_orders = {}
all_orders = {}
awaiting_payment = {}
awaiting_admin_response = {}

# Файлы для сохранения данных
USER_ORDERS_FILE = "user_orders.json"
PENDING_ORDERS_FILE = "pending_orders.json"
ALL_ORDERS_FILE = "all_orders.json"
AWAITING_PAYMENT_FILE = "awaiting_payment.json"
AWAITING_ADMIN_RESPONSE_FILE = "awaiting_admin_response.json"

# Функции для сохранения и загрузки данных
def save_user_orders():
    with open(USER_ORDERS_FILE, "w") as f:
        json.dump({str(k): v for k, v in user_orders.items()}, f)
    logger.info("Saved user_orders")

def load_user_orders():
    global user_orders
    try:
        with open(USER_ORDERS_FILE, "r") as f:
            data = json.load(f)
            user_orders = {int(k): v for k, v in data.items()}
        logger.info("Loaded user_orders")
    except FileNotFoundError:
        user_orders = {}

def save_pending_orders():
    with open(PENDING_ORDERS_FILE, "w") as f:
        json.dump({str(k): v for k, v in pending_orders.items()}, f)
    logger.info("Saved pending_orders")

def load_pending_orders():
    global pending_orders
    try:
        with open(PENDING_ORDERS_FILE, "r") as f:
            data = json.load(f)
            pending_orders = {int(k): v for k, v in data.items()}
        logger.info("Loaded pending_orders")
    except FileNotFoundError:
        pending_orders = {}

def save_all_orders():
    with open(ALL_ORDERS_FILE, "w") as f:
        json.dump({str(k): v for k, v in all_orders.items()}, f)
    logger.info("Saved all_orders")

def load_all_orders():
    global all_orders
    try:
        with open(ALL_ORDERS_FILE, "r") as f:
            data = json.load(f)
            all_orders = {int(k): v for k, v in data.items()}
        logger.info("Loaded all_orders")
    except FileNotFoundError:
        all_orders = {}

def save_awaiting_payment():
    with open(AWAITING_PAYMENT_FILE, "w") as f:
        json.dump({str(k): v for k, v in awaiting_payment.items()}, f)
    logger.info(f"Saved awaiting_payment: {awaiting_payment}")

def load_awaiting_payment():
    global awaiting_payment
    try:
        with open(AWAITING_PAYMENT_FILE, "r") as f:
            data = json.load(f)
            awaiting_payment = {int(k): v for k, v in data.items()}
        logger.info(f"Loaded awaiting_payment: {awaiting_payment}")
    except FileNotFoundError:
        awaiting_payment = {}

def save_awaiting_admin_response():
    with open(AWAITING_ADMIN_RESPONSE_FILE, "w") as f:
        json.dump({str(k): v for k, v in awaiting_admin_response.items()}, f)
    logger.info("Saved awaiting_admin_response")

def load_awaiting_admin_response():
    global awaiting_admin_response
    try:
        with open(AWAITING_ADMIN_RESPONSE_FILE, "r") as f:
            data = json.load(f)
            awaiting_admin_response = {int(k): v for k, v in data.items()}
        logger.info("Loaded awaiting_admin_response")
    except FileNotFoundError:
        awaiting_admin_response = {}

# Загружаем данные при старте
load_user_orders()
load_pending_orders()
load_all_orders()
load_awaiting_payment()
load_awaiting_admin_response()

# HTTP-сервер для Render
async def health_check(request):
    return web.Response(text="Bot is running")

app = web.Application()
app.router.add_get('/', health_check)

# Обработчик ошибок
@dp.errors_handler()
async def errors_handler(update, exception):
    logger.error(f"Update {update} caused error {exception}")
    return True

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_orders and user_id in awaiting_payment:
        order_id = user_orders[user_id].get("order_id")
        if order_id and all_orders.get(order_id, {}).get("status") in ["ожидает оплаты", "ожидает подтверждения оплаты"]:
            await message.answer(
                f"У вас уже есть активный заказ №{order_id}. "
                "Пожалуйста, завершите оплату или отмените заказ, чтобы начать новый."
            )
            return

    user_orders.pop(message.from_user.id, None)
    save_user_orders()
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Днепр", callback_data="city_dnepr"))

    await bot.send_photo(
        chat_id=message.chat.id,
        photo="https://i.imgur.com/qYhLQhY.png",
        caption=(
            f"Ку бро, - {message.from_user.username or message.from_user.first_name}\n\n"
            "Рад тебя видеть в нашем шопе.\n"
            "Оператор: @shmalebanutaya\n"
            "Не забудь подписаться на канал - [ссылка]"
        ),
        reply_markup=markup
    )

@dp.callback_query_handler(lambda c: c.data == "city_dnepr")
async def city_selected(callback_query: types.CallbackQuery):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Hindu Kush - 1гр - 300 грн", callback_data="product_1"),
        InlineKeyboardButton("Hindu Kush - 2гр - 570 грн", callback_data="product_2"),
        InlineKeyboardButton("Hindu Kush - 3гр - 820 грн", callback_data="product_3")
    )
    
    # Удаляем старое сообщение с фото
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    
    # Отправляем новое сообщение с текстом и кнопками
    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text="Вы выбрали город Днепр.\nЧто тебе присмотрелось?",
        reply_markup=markup
    )
    
    # Подтверждаем обработку callback
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("product_"))
async def product_selected(callback_query: types.CallbackQuery):
    product_map = {
        "product_1": "Hindu Kush - 1гр - 300 грн",
        "product_2": "Hindu Kush - 2гр - 570 грн",
        "product_3": "Hindu Kush - 3гр - 820 грн",
    }
    product_name = product_map[callback_query.data]
    price = product_name.split('-')[-1].strip()

    user_orders[callback_query.from_user.id] = {
        "product": product_name,
        "price": price
    }
    save_user_orders()

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Кирова", callback_data="area_kirova"),
        InlineKeyboardButton("Начало пр. Богдана Хмельницкого", callback_data="area_bh")
    )

    # Удаляем старое сообщение
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )

    # Отправляем новое сообщение с фото, описанием и кнопками
    await bot.send_photo(
        chat_id=callback_query.message.chat.id,
        photo="https://i.imgur.com/GuEGQGw.png",
        caption=(
            f"Избран продукт: {product_name}\n"
            f"Коротко о товаре: Hindu Kush — легенда прямо с гор!\n"
            f"Чистая индика, которая расслабит тело и вынесет мозг в дзен. Густой пряно-земляной аромат, мягкий вкус и мощный эффект 'всё по кайфу'. Идеален для вечеров, чилла и сладкого сна.\n\n"
            f"100% качество — без суеты, только кайф.\n"
            f"Попробуй классику, с которой всё начиналось.\n"
            f"Цена: {price}\n"
            "Выберите подходящий район:"
        ),
        reply_markup=markup
    )

    # Подтверждаем обработку callback
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("area_"))
async def area_selected(callback_query: types.CallbackQuery):
    data = user_orders.get(callback_query.from_user.id)
    if not data:
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text="Что-то пошло не так. Попробуй снова /start"
        )
        return

    area_map = {
        "area_kirova": "Кирова",
        "area_bh": "Начало пр. Богдана Хмельницкого"
    }
    area = area_map[callback_query.data]

    order_id = random.randint(20000, 99999)
    data.update({
        "order_id": order_id,
        "city": "Днепр",
        "area": area,
        "status": "ожидает оплаты"
    })

    full_order = {
        **data,
        "user_id": callback_query.from_user.id,
        "username": callback_query.from_user.username
    }

    user_orders[callback_query.from_user.id] = data
    pending_orders[order_id] = full_order
    all_orders[order_id] = full_order
    save_user_orders()
    save_pending_orders()
    save_all_orders()

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(" 💳 Оплата на карту", callback_data="pay_card"))

    # Удаляем старое сообщение с фото
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )

    # Отправляем новое текстовое сообщение
    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=(
            f"Заказ создан! Адрес забронирован!\n\n"
            f"Ваш заказ №: {order_id}\n"
            f"Город: {data['city']}\n"
            f"Товар: {data['product']}\n"
            f"Цена: {data['price']}\n"
            "Метод оплаты:"
        ),
        reply_markup=markup
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
        f"Район: {data['area']}\n"
        f"Статус: {data['status']}",
        reply_markup=admin_markup
    )

    # Подтверждаем обработку callback
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "pay_card")
async def payment_selected(callback_query: types.CallbackQuery):
    order_id = user_orders.get(callback_query.from_user.id, {}).get("order_id")
    if not order_id:
        await callback_query.message.edit_text("Что-то пошло не так. Попробуй снова /start")
        return

    all_orders[order_id]["status"] = "ожидает подтверждения оплаты"
    pending_orders[order_id]["status"] = "ожидает подтверждения оплаты"
    save_all_orders()
    save_pending_orders()

    await callback_query.message.edit_text(
        f"Ваш заказ №: {order_id}\n"
        "Для оплаты переведите указанную сумму на карту:\n"
        "💳 Номер карты: 1234 5678 9012 3456\n"
        "После оплаты отправьте скриншот или сообщение с подтверждением ниже."
    )

    awaiting_payment[callback_query.from_user.id] = {
        "order_id": order_id,
        "message_id": callback_query.message.message_id
    }
    save_awaiting_payment()

@dp.message_handler(lambda message: message.from_user.id == ADMIN_ID, content_types=['photo', 'text'])
async def handle_admin_response(message: types.Message):
    if message.from_user.id not in awaiting_admin_response:
        await message.answer("Пожалуйста, выберите действие через кнопку.")
        return

    response_info = awaiting_admin_response[message.from_user.id]
    user_id = response_info["user_id"]
    order_id = response_info["order_id"]

    logger.info(f"Admin response for user_id={user_id}, order_id={order_id}")

    try:
        if message.photo:
            photo = message.photo[-1].file_id
            caption = message.caption or f"Ответ от админа по заказу #{order_id}"
            await bot.send_photo(user_id, photo, caption=caption)
        else:
            await bot.send_message(user_id, f"Ответ от админа по заказу #{order_id}:\n{message.text}")

        await message.answer(f"Ответ отправлен пользователю (заказ #{order_id}).")
    except Exception as e:
        logger.error(f"Error sending response to user {user_id}: {e}")
        await message.answer("Ошибка при отправке ответа пользователю.")

    awaiting_admin_response.pop(message.from_user.id, None)
    save_awaiting_admin_response()

@dp.message_handler(content_types=['photo', 'text'])
async def handle_payment_proof(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"Handling payment proof for user_id={user_id}, awaiting_payment={awaiting_payment}, user_orders={user_orders}, all_orders={all_orders}")

    # Проверяем, ожидает ли пользователь отправки подтверждения
    order_id = None
    if user_id in awaiting_payment:
        order_id = awaiting_payment[user_id]["order_id"]
    elif user_id in user_orders and "order_id" in user_orders[user_id]:
        order_id = user_orders[user_id]["order_id"]
        order_status = all_orders.get(order_id, {}).get("status")
        logger.info(f"User {user_id} not in awaiting_payment, but found order_id={order_id}, status={order_status}")
        if order_status == "ожидает подтверждения оплаты":
            awaiting_payment[user_id] = {
                "order_id": order_id,
                "message_id": message.message_id
            }
            save_awaiting_payment()
        else:
            logger.warning(f"User {user_id} has order, but status is {order_status}")
            await message.answer("Пожалуйста, начните с команды /start")
            return
    else:
        logger.warning(f"User {user_id} not in awaiting_payment or user_orders")
        await message.answer("Пожалуйста, начните с команды /start")
        return

    # Проверяем, что заказ существует и имеет правильный статус
    if order_id not in all_orders:
        logger.warning(f"Order {order_id} not in all_orders")
        await message.answer("Что-то пошло не так. Попробуйте снова /start")
        return

    all_orders[order_id]["status"] = "оплачено"
    pending_orders[order_id]["status"] = "оплачено"
    save_all_orders()
    save_pending_orders()

    admin_message = (
        f"📸 Пользователь @{message.from_user.username} отправил подтверждение оплаты для заказа #{order_id}\n"
        f"Статус: {all_orders[order_id]['status']}"
    )
    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(
        InlineKeyboardButton("📩 Ответить", callback_data=f"reply_{user_id}_{order_id}")
    )

    logger.info(f"Sending to admin: {admin_message}, callback_data=reply_{user_id}_{order_id}")

    if message.photo:
        photo = message.photo[-1].file_id
        await bot.send_photo(ADMIN_ID, photo, caption=admin_message, reply_markup=admin_markup)
    else:
        await bot.send_message(ADMIN_ID, f"{admin_message}\nСообщение: {message.text}", reply_markup=admin_markup)

    await message.answer("Ваш скриншот/сообщение отправлено. Ожидайте ответа от админа.")
    awaiting_payment.pop(user_id, None)
    save_awaiting_payment()

@dp.callback_query_handler(lambda c: c.data.startswith("approve_"))
async def approve_order(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split("_")[1])
    if order_id not in all_orders:
        await callback_query.message.edit_text("Заказ не найден.")
        return

    order = all_orders[order_id]
    order["status"] = "подтверждён"
    pending_orders.pop(order_id, None)
    save_all_orders()
    save_pending_orders()

    await bot.send_message(
        order["user_id"],
        f"Ваш заказ #{order_id} подтверждён! Спасибо за покупку."
    )

    await callback_query.message.edit_text(
        f"📦 Заказ #{order_id}\n"
        f"Юзер: @{order['username']}\n"
        f"Товар: {order['product']}\n"
        f"Цена: {order['price']}\n"
        f"Район: {order['area']}\n"
        f"Статус: {order['status']}"
    )

@dp.callback_query_handler(lambda c: c.data.startswith("reject_"))
async def reject_order(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split("_")[1])
    if order_id not in all_orders:
        await callback_query.message.edit_text("Заказ не найден.")
        return

    order = all_orders[order_id]
    order["status"] = "отклонён"
    pending_orders.pop(order_id, None)
    user_orders.pop(order["user_id"], None)
    save_all_orders()
    save_pending_orders()
    save_user_orders()

    await bot.send_message(
        order["user_id"],
        f"Ваш заказ #{order_id} был отклонён. Для уточнения деталей свяжитесь с оператором: @shmalebanutaya"
    )

    await callback_query.message.edit_text(
        f"📦 Заказ #{order_id}\n"
        f"Юзер: @{order['username']}\n"
        f"Товар: {order['product']}\n"
        f"Цена: {order['price']}\n"
        f"Район: {order['area']}\n"
        f"Статус: {order['status']}"
    )

@dp.callback_query_handler(lambda c: c.data.startswith("reply_"))
async def reply_to_user(callback_query: types.CallbackQuery):
    logger.info(f"Received reply callback: {callback_query.data}")
    try:
        parts = callback_query.data.split("_")
        if len(parts) != 3:
            raise ValueError(f"Invalid callback_data format: {callback_query.data}")
        _, user_id, order_id = parts
        user_id = int(user_id)
        order_id = int(order_id)
        logger.info(f"Parsed reply: user_id={user_id}, order_id={order_id}")

        if callback_query.from_user.id != ADMIN_ID:
            logger.warning(f"Non-admin tried to reply: {callback_query.from_user.id}")
            await callback_query.answer("Только админ может отвечать.")
            return

        awaiting_admin_response[callback_query.from_user.id] = {
            "user_id": user_id,
            "order_id": order_id
        }
        save_awaiting_admin_response()

        await bot.send_message(
            callback_query.from_user.id,
            f"Отправьте ответ для пользователя (заказ #{order_id}). Это может быть текст, фото или фото с текстом."
        )
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in reply_to_user: {e}")
        await bot.send_message(
            callback_query.from_user.id,
            "Произошла ошибка. Попробуйте снова."
        )
        await callback_query.answer()

# Запуск бота и HTTP-сервера
if __name__ == '__main__':
    from aiogram.utils.executor import start_polling
    import asyncio

    async def start_http_server():
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        logger.info("HTTP server started on port 8080")

    loop = asyncio.get_event_loop()
    loop.create_task(start_http_server())
    executor.start_polling(dp, skip_updates=True)
