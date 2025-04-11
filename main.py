
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
import logging
import random

# === CONFIG ===
API_TOKEN = '7596145421:AAFMkGYtjaJRxwP-G5sl-t3lj7jxQaPboqE'
ADMIN_ID = 8070055531  # Telegram ID админа

# === SETUP ===
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)
user_orders = {}  # Словарь для хранения заказов по user_id
pending_orders = {}  # Заказы, ожидающие подтверждения

# === HANDLERS ===

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Днепр"))
    
  await message.answer(f"Ку бро, - {message.from_user.username or message.from_user.first_name}")

"
        "Рад тебя видеть в нашем шопе.
"
        "Оператор: @shmalebanutaya
"
        "Не забудь подписаться на канал - [ссылка]",
        reply_markup=markup
    )

@dp.message_handler(lambda message: message.text == "Днепр")
async def city_selected(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        "Товар 1 - 1гр - 300 грн",
        "Товар 2 - 2гр - 570 грн",
        "Товар 3 - 3гр - 820 грн"
    )
    await message.answer("Вы выбрали город Днепр.\nЧто тебе присмотрелось?", reply_markup=markup)

@dp.message_handler(lambda message: "Товар" in message.text)
async def product_selected(message: types.Message):
    product_name = message.text
    price = product_name.split('-')[-1].strip()

    user_orders[message.from_user.id] = {
        "product": product_name,
        "price": price
    }

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Кирова", "Начало пр. Богдана Хмельницкого")
    await message.answer(
        f"Избран продукт: {product_name}\n"
        f"Коротко о товаре: (сам изменишь)\n"
        f"Цена: {price}\n"
        "Выберите подходящий район:", reply_markup=markup
    )

@dp.message_handler(lambda message: message.text in ["Кирова", "Начало пр. Богдана Хмельницкого"])
async def area_selected(message: types.Message):
    data = user_orders.get(message.from_user.id)
    if not data:
        return await message.answer("Что-то пошло не так. Попробуй снова /start")

    order_id = random.randint(20000, 99999)
    data["order_id"] = order_id
    data["city"] = "Днепр"
    data["area"] = message.text

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Оплата на карту", "/start")

    await message.answer(
        f"Заказ создан! Адрес забронирован!\n\n"
        f"Ваш заказ №: {order_id}\n"
        f"Город: {data['city']}\n"
        f"Товар: {data['product']}\n"
        f"Цена: {data['price']}\n"
        f"Выберите удобный метод платы:", reply_markup=markup
    )

    pending_orders[order_id] = {
        **data,
        "user_id": message.from_user.id,
        "username": message.from_user.username
    }

    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(
        InlineKeyboardButton("✅ Подтвердить", callback_data=f"approve_{order_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{order_id}")
    )

    await bot.send_message(ADMIN_ID,
        f"📦 Новый заказ #{order_id}\n"
        f"Юзер: @{message.from_user.username}\n"
        f"Товар: {data['product']}\n"
        f"Цена: {data['price']}\n"
        f"Район: {data['area']}",
        reply_markup=admin_markup
    )

@dp.message_handler(lambda message: message.text == "Оплата на карту")
async def payment_selected(message: types.Message):
    data = user_orders.get(message.from_user.id)
    if not data:
        return await message.answer("Сначала выбери товар /start")

    await message.answer(
        f"Ваш заказ №: {data['order_id']}\n"
        f"Город: {data['city']}\n"
        f"Товар: {data['product']}\n"
        f"Цена: {data['price']}\n\n"
        "Выбран метод оплаты на банковскую карту.\n"
        "Для получения товара, оплатите на карту: 0000 0000 0000 0000 (вставь сам)\n"
        f"Сумма: {data['price']}\n\n"
        "После оплаты скинь скрин сюда."
    )

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    await bot.send_message(ADMIN_ID, f"📤 Скрин оплаты от @{message.from_user.username} для заказа #{user_orders[message.from_user.id]['order_id']}")
    await bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    await message.reply("Скрин получен! Ожидай подтверждение от оператора.")

@dp.message_handler(commands=["admin"])
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("У тебя нет доступа к этой команде.")

    if not pending_orders:
        return await message.reply("Нет новых заказов.")

    for order_id, order in pending_orders.items():
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"approve_{order_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{order_id}")
        )
        await message.answer(
            f"Заказ #{order_id}\nЮзер: @{order['username']}\nТовар: {order['product']}\nЦена: {order['price']}",
            reply_markup=markup
        )

@dp.callback_query_handler(lambda c: c.data.startswith("approve_") or c.data.startswith("reject_"))
async def process_admin_action(callback_query: types.CallbackQuery):
    action, order_id_str = callback_query.data.split("_")
    order_id = int(order_id_str)
    order = pending_orders.pop(order_id, None)

    if not order:
        return await callback_query.answer("Заказ уже обработан.")

    if action == "approve":
        await bot.send_message(order["user_id"], f"✅ Заказ #{order_id} подтвержден! Скоро с тобой свяжется оператор.")
        await callback_query.message.edit_text(f"✅ Заказ #{order_id} подтвержден.")
    else:
        await bot.send_message(order["user_id"], f"❌ Заказ #{order_id} был отклонён. Свяжись с оператором.")
        await callback_query.message.edit_text(f"❌ Заказ #{order_id} отклонён.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
