import asyncio
import logging
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery

# --- БЛОК ДЛЯ РАБОТЫ 24/7 (Flask сервер) ---
app = Flask('')

@app.route('/')
def home():
    return "Бот запущен и работает!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- НАСТРОЙКИ БОТА (Твои данные) ---
TOKEN = "8742664439:AAGxT7wIlKiU-V3xA-zEyYUQmPRE70LPqXs"
ADMIN_ID = 8266529611
CHANNEL_ID = "-1003780152007"
CHANNEL_LINK = "https://t.me/+9QT9M5dnINUwNGU1"
SUPPORT_LINK = "https://t.me/favorit_shop_humber"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Список стран
COUNTRIES = {
    "india": {"name": "🇮🇳 Индия", "price": 60},
    "canada": {"name": "🇨🇦 Канада", "price": 130},
    "bangladesh": {"name": "🇧🇩 Бангладеш", "price": 100},
    "usa": {"name": "🇺🇸 США", "price": 150},
    "south_africa": {"name": "🇿🇦 ЮАР", "price": 150},
}

# Клавиатура главного меню
def main_menu():
    kb = [
        [InlineKeyboardButton(text="📱 Купить номер", callback_data="buy")],
        [InlineKeyboardButton(text="🆘 Поддержка", url=SUPPORT_LINK)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Команда /start
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! Это магазин номеров.\nВыбери действие:",
        reply_markup=main_menu()
    )

# Выбор страны
@dp.callback_query(F.data == "buy")
async def show_countries(call: types.CallbackQuery):
    kb = []
    for code, info in COUNTRIES.items():
        kb.append([InlineKeyboardButton(text=f"{info['name']} - {info['price']} ⭐️", callback_data=f"pay_{code}")])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back")])
    await call.message.edit_text("Выберите страну:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# Кнопка назад
@dp.callback_query(F.data == "back")
async def back_to_menu(call: types.CallbackQuery):
    await call.message.edit_text("Главное меню:", reply_markup=main_menu())

# Создание счета на оплату Звездами
@dp.callback_query(F.data.startswith("pay_"))
async def create_invoice(call: types.CallbackQuery):
    country_code = call.data.split("_")[1]
    country = COUNTRIES[country_code]
    
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title=f"Номер: {country['name']}",
        description=f"Покупка виртуального номера страны {country['name']}",
        payload=f"stars_pay_{country_code}",
        currency="XTR", # Код для Telegram Stars
        prices=[LabeledPrice(label="Звёзды", amount=country['price'])],
        provider_token="" # Для звезд должно быть пустым
    )
    await call.answer()

# Подтверждение возможности оплаты
@dp.pre_checkout_query()
async def process_pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

# Успешная оплата
@dp.message(F.successful_payment)
async def on_successful_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    country_code = payload.split("_")[-1]
    country_name = COUNTRIES[country_code]['name']
    
    await message.answer(f"✅ Оплата прошла успешно!\nСтрана: {country_name}\n\nАдмин скоро свяжется с вами.")
    
    # Уведомление админу
    await bot.send_message(
        ADMIN_ID, 
        f"💰 НОВАЯ ПОКУПКА!\nЮзер: @{message.from_user.username}\nID: {message.from_user.id}\nТовар: {country_name}"
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    keep_alive() # Запускаем веб-сервер для Render
    asyncio.run(main())
