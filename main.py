from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
import logging
import random

API_TOKEN = '7740691105:AAG5bIBaN4lLGesxlFDlzW1LU0T8Ka0LRO4'
ADMIN_ID = 8070055531

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

user_orders = {}
pending_orders = {}
all_orders = {}
awaiting_photo_to_send = {}

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
    markup.add(InlineKeyboardButton("\ud83d\udcb3 Оплата на карту", callback_data="pay_card"))

    await callback_query.message.edit_text(
        f"Заказ создан! Адрес забронирован!\n\n"
        f"Ваш заказ №: {order_id}\n"
        f"Город: {data['city']}\n"
        f"Товар: {data['product']}\n"
        f"Цена: {data['price']}\n"
        f"Метод оплаты:", reply_markup=markup
    )

    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(
        InlineKeyboardButton("\u2705 Подтвердить", callback_data=f"approve_{order_id}"),
        InlineKeyboardButton("\u274c Отклонить", callback_data=f"reject_{order_id}")
    )

    await bot.send_message(ADMIN_ID,
        f"\ud83d\udce6 Новый заказ #{order_id}\n"
        f"Юзер: @{callback_query.from_user.username}\n"
        f"Товар: {data['product']}\n"
        f"Цена: {data['price']}\n"
        f"Район: {data['area']}",
        reply_markup=admin_markup
    )

@dp.callback_query_handler(lambda c: c.data == "pay_card")
async def payment_selected(callback_query: types.CallbackQuery):
    data = user_orders.get(callback_query.from_user.id)
    if not data:
        return await callback_query.message.edit_text("Сначала выбери товар /start")

    await callback_query.message.edit_text(
        f"Ваш заказ №: {data['order_id']}\n"
        f"Город: {data['city']}\n"
        f"Товар: {data['product']}\n"
        f"Цена: {data['price']}\n\n"
        "Выбран метод оплаты на банковскую карту.\n"
        "Для получения товара, оплатите на карту: 0000 0000 0000 0000 (вставь сам)\n"
        f"Сумма: {data['price']}\n\n"
        "После оплаты скинь скрин сюда."
    )

@dp.message_handler(commands=["admin"])
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("У тебя нет доступа к этой команде.")

    if not pending_orders:
        return await message.reply("Нет новых заказов.")

    for order_id, order in pending_orders.items():
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("\u2705 Подтвердить", callback_data=f"approve_{order_id}"),
            InlineKeyboardButton("\u274c Отклонить", callback_data=f"reject_{order_id}")
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
        await bot.send_message(order["user_id"], f"\u2705 Заказ #{order_id} подтвержден! Скоро с тобой свяжется оператор.")
        await callback_query.message.edit_text(f"\u2705 Заказ #{order_id} подтвержден.")
    else:
        await bot.send_message(order["user_id"], f"\u274c Заказ #{order_id} был отклонён. Свяжись с оператором.")
        await callback_query.message.edit_text(f"\u274c Заказ #{order_id} отклонён.")

@dp.message_handler(commands=["send"])
async def send_photo_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("Нет доступа.")

    args = message.text.split()
    if len(args) < 2:
        return await message.reply("Укажи номер заказа. Пример: /send 70214")

    order_id = int(args[1])
    order = all_orders.get(order_id)

    if not order:
        return await message.reply("Заказ с таким номером не найден.")

    awaiting_photo_to_send[message.from_user.id] = order_id
    await message.reply(f"Жду фото для отправки пользователю заказа #{order_id}.")

@dp.message_handler(content_types=[types.ContentType.PHOTO, types.ContentType.DOCUMENT])
async def handle_photo_uploads(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        if message.from_user.id not in awaiting_photo_to_send:
            return

        order_id = awaiting_photo_to_send.pop(message.from_user.id)
        order = all_orders.get(order_id)
        if not order:
            return await message.reply("Пользователь не найден.")

        await bot.send_message(order["user_id"], f"\ud83d\udce6 Фото по заказу #{order_id}")
        await bot.forward_message(order["user_id"], message.chat.id, message.message_id)
        return await message.reply(f"Фото успешно отправлено пользователю заказа #{order_id}.")

    if message.from_user.id not in user_orders:
        return await message.reply("Сначала выбери товар /start")

    await bot.send_message(ADMIN_ID, f"\ud83d\udcc4 Скрин оплаты от @{message.from_user.username} для заказа #{user_orders[message.from_user.id]['order_id']}")
    await bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    await message.reply("Скрин получен! Ожидай подтверждение от оператора.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
