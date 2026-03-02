import asyncio
import logging
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# --- БЛОК ДЛЯ РАБОТЫ В РЕЖИМЕ 24/7 ---
app = Flask('')

@app.route('/')
def home():
    return "Бот запущен и работает!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- СОСТОЯНИЯ ДЛЯ АНКЕТЫ ПРОДАЖИ ---
class SellAccount(StatesGroup):
    account_type = State()
    minus_info = State()

# --- НАСТРОЙКИ БОТА ---
TOKEN = "8742664439:AAEzi_ucWeV2t3KrzUUbWr5ngRQLX24HkYc" 
ADMIN_ID = 8266529611
SUPPORT_URL = "https://t.me/favorit_shop_humber"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Главное меню
def main_menu():
    kb = [
        [types.InlineKeyboardButton(text="📱 Купить номер", callback_data="buy_number")],
        [types.InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [types.InlineKeyboardButton(text="💰 Продать аккаунт", callback_data="sell_account")],
        [types.InlineKeyboardButton(text="🆘 Поддержка", url=SUPPORT_URL)]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(CommandStart())
async def start_command(message: types.Message):
    await message.answer(f"Привет, {message.from_user.first_name}! Это магазин «Фаворит шоп» 👮. Выбери действие:", reply_markup=main_menu())

# Обработка кнопки Профиль
@dp.callback_query(F.data == "profile")
async def profile_handler(callback: types.CallbackQuery):
    text = (f"👤 **Ваш профиль:**\n\n"
            f"🆔 Ваш ID: `{callback.from_user.id}`\n"
            f"👤 Имя: {callback.from_user.first_name}\n"
            f"⭐ Статус: Клиент")
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu())

# Начало продажи аккаунта
@dp.callback_query(F.data == "sell_account")
async def sell_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Вы выбрали продажу аккаунта. Ваш номер — это **дроп** или **визуальный**?")
    await state.set_state(SellAccount.account_type)

@dp.message(SellAccount.account_type)
async def process_type(message: types.Message, state: FSMContext):
    await state.update_data(type=message.text)
    await message.answer("Какие минусы есть на вашем аккаунте? Опишите кратко.")
    await state.set_state(SellAccount.minus_info)

@dp.message(SellAccount.minus_info)
async def process_finish(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    # Отправка данных админу
    admin_msg = (f"🚀 **Новая заявка на продажу!**\n\n"
                 f"От: @{message.from_user.username} (ID: {message.from_user.id})\n"
                 f"Тип номера: {user_data['type']}\n"
                 f"Минусы: {message.text}")
    
    await bot.send_message(ADMIN_ID, admin_msg)
    await message.answer("Данные приняты! Администратор свяжется с вами в ближайшее время. ✅", reply_markup=main_menu())
    await state.clear()

async def main():
    logging.basicConfig(level=logging.INFO)
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
