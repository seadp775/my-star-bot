import asyncio
import logging
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# --- БЛОК 24/7 ---
app = Flask('')
@app.route('/')
def home(): return "Бот работает!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- СОСТОЯНИЯ АНКЕТЫ ---
class SellAccount(StatesGroup):
    account_type = State()
    country = State()
    minus_info = State()
    confirm = State()

# --- НАСТРОЙКИ (ВСТАВЬ СВОИ ДАННЫЕ) ---
TOKEN = "8742664439:AAEzi_ucWeV2t3KrzUUbWr5ngRQLX24HkYc" # Твой полный токен
ADMIN_ID = 8266529611
SUPPORT_URL = "https://t.me/favorit_shop_humber"
REVIEWS_URL = "https://t.me/favorit_shop_humber" # СЮДА ССЫЛКУ НА ОТЗЫВЫ!
MENU_PHOTO_URL = "https://raw.githubusercontent.com/seadp775/my-star-bot/main/1000036915.jpg"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Главное меню
def main_menu():
    kb = [
        [types.InlineKeyboardButton(text="📱 Купить аккаунт", callback_data="buy_account")],
        [types.InlineKeyboardButton(text="💰 Продать аккаунт", callback_data="sell_account")],
        [types.InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
         types.InlineKeyboardButton(text="⭐️ Отзывы", url=REVIEWS_URL)],
        [types.InlineKeyboardButton(text="🆘 Поддержка", url=SUPPORT_URL)]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    try:
        await message.answer_photo(
            photo=MENU_PHOTO_URL,
            caption=f"Добро пожаловать в **«Фаворит шоп»** 👮\n\nЛучшие аккаунты и быстрая скупка только у нас!",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )
    except:
        await message.answer(f"Привет! Это «Фаворит шоп» 👮. Выберите действие:", reply_markup=main_menu())

@dp.callback_query(F.data == "buy_account")
async def buy_handler(callback: types.CallbackQuery):
    await callback.message.answer("👷‍♂️ **Раздел покупок в разработке.**\nСкоро здесь появятся лучшие предложения!", reply_markup=main_menu(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "profile")
async def profile_handler(callback: types.CallbackQuery):
    text = (f"👤 **Ваш профиль:**\n\n"
            f"🆔 Ваш ID: `{callback.from_user.id}`\n"
            f"💰 Баланс: **0 ₽**\n"
            f"⭐️ Статус: **Активный клиент**\n"
            f"🤝 Сделок: **0**")
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=main_menu())
    await callback.answer()

# --- ЛОГИКА ПРОДАЖИ ---
@dp.callback_query(F.data == "sell_account")
async def sell_start(callback: types.CallbackQuery, state: FSMContext):
    kb = [[types.InlineKeyboardButton(text="🛡️ Дроп", callback_data="type_drop"), 
           types.InlineKeyboardButton(text="🌐 Визуальный", callback_data="type_visual")]]
    await callback.message.answer("💳 **Начинаем оформление заявки**\n\nКакой тип вашего номера?", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")
    await state.set_state(SellAccount.account_type)
    await callback.answer()

@dp.callback_query(SellAccount.account_type)
async def process_type(callback: types.CallbackQuery, state: FSMContext):
    acc_type = "Дроп" if callback.data == "type_drop" else "Визуальный"
    await state.update_data(type=acc_type)
    await callback.message.answer("🚩 **Укажите страну номера**\n(Пришлите флаг или название страны)")
    await state.set_state(SellAccount.country)
    await callback.answer()

@dp.message(SellAccount.country)
async def process_country(message: types.Message, state: FSMContext):
    await state.update_data(country=message.text)
    await message.answer("❌ **Есть ли минусы на аккаунте?**\nОпишите кратко (если нет, пишите: нет)")
    await state.set_state(SellAccount.minus_info)

@dp.message(SellAccount.minus_info)
async def process_verify(message: types.Message, state: FSMContext):
    await state.update_data(minuses=message.text)
    data = await state.get_data()
    verify_text = (f"🔍 **ПРОВЕРКА ДАННЫХ:**\n\n"
                   f"📍 **Тип:** {data['type']}\n"
                   f"🚩 **Страна:** {data['country']}\n"
                   f"❌ **Минусы:** {data['minuses']}\n\n"
                   f"**Всё верно? Отправляем админу?**")
    kb = [[types.InlineKeyboardButton(text="✅ Да, отправить", callback_data="confirm_yes"),
           types.InlineKeyboardButton(text="❌ Нет, заново", callback_data="confirm_no")]]
    await message.answer(verify_text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")
    await state.set_state(SellAccount.confirm)

@dp.callback_query(SellAccount.confirm)
async def process_finish(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "confirm_yes":
        data = await state.get_data()
        admin_msg = f"🚀 **НОВАЯ ЗАЯВКА!**\n\n👤 От: @{callback.from_user.username}\n🆔 ID: {callback.from_user.id}\n📍 Тип: {data['type']}\n🚩 Страна: {data['country']}\n❌ Минусы: {data['minuses']}"
        await bot.send_message(ADMIN_ID, admin_msg)
        await callback.message.answer("✅ **Заявка успешно отправлена!**\n\nАдминистратор свяжется с вами. Если ответа нет более 10 часов — напишите в поддержку.", reply_markup=main_menu(), parse_mode="Markdown")
        await state.clear()
    else:
        await callback.message.answer("🔄 Сброс анкеты. Начнем заново.")
        await state.clear()
        await sell_start(callback, state)
    await callback.answer()

async def main():
    logging.basicConfig(level=logging.INFO)
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
