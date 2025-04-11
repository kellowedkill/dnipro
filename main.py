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
