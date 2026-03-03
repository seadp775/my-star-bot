import asyncio
import logging
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# --- БЛОК 24/7 ДЛЯ RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Бот «Фаворит шоп» активен! 👮"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- СОСТОЯНИЯ ---
class ShopState(StatesGroup):
    selling = State() # Для анкеты продажи
    top_up = State() # Для ввода суммы звезд

# --- КОНФИГ ---
TOKEN = "8742664439:AAEzi_ucWeV2t3KrzUUbWr5ngRQLX24HkYc"
# Впиши сюда свой ID и ID менеджера (цифрами!)
ADMIN_ID = 8266529611 
MANAGER_ID = 8490517217 # Пока поставлю твой, замени на ID менеджера если нужно

MENU_PHOTO = "https://cdn-ru.ru/sub/18e79943-e4a8-445c-9271-571f0df51f14"
CHANNEL_URL = "https://t.me/+P5-6K7k3625kNzAy"
SUPPORT = "@favorit_shop_humber"

PRICES = {
    "🇮🇳 Индия": 60, "🇨🇦 Канада": 130, "🇧🇩 Бангладеш": 100,
    "🇺🇸 США": 150, "🇿🇦 ЮАР": 150, "🇲🇲 Мьянма": 60,
    "🇮🇩 Индонезия": 100, "🇲🇦 Марокко": 150
}

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КЛАВИАТУРЫ ---
def get_main_kb():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📱 Купить аккаунт", callback_data="buy_list")],
        [types.InlineKeyboardButton(text="💰 Продать аккаунт", callback_data="sell_start")],
        [types.InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
         types.InlineKeyboardButton(text="⭐ Пополнить (Stars)", callback_data="top_up_stars")],
        [types.InlineKeyboardButton(text="🆘 Поддержка", url=f"https://t.me/favorit_shop_humber")]
    ])

def back_to_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ В главное меню", callback_data="to_main")]
    ])

# --- ОБРАБОТЧИКИ ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer_photo(
        photo=MENU_PHOTO,
        caption="👮 **Добро пожаловать в Фаворит шоп!**\n\nВыбирай нужный раздел ниже:",
        reply_markup=get_main_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "to_main")
async def to_main(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    # Удаляем старое и шлем новое меню, чтобы фото всегда было сверху
    await call.message.delete()
    await cmd_start(call.message, state)

# --- ПОКУПКА ---
@dp.callback_query(F.data == "buy_list")
async def buy_list(call: types.CallbackQuery):
    kb = []
    for country, price in PRICES.items():
        kb.append([types.InlineKeyboardButton(text=f"{country} — {price}₽", callback_data=f"order_{country}")])
    kb.append([types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")])
    
    await call.message.edit_caption(
        caption="📱 **ВЫБЕРИТЕ СТРАНУ ДЛЯ ПОКУПКИ:**",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("order_"))
async def order_confirm(call: types.CallbackQuery):
    country = call.data.split("_")[1]
    price = PRICES[country]
    await call.message.edit_caption(
        caption=f"🌍 **Заказ:** {country}\n💰 **Цена:** {price} фофаридок\n\nДля покупки у вас должен быть баланс. Желаете продолжить?",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Оформить заявку", callback_data=f"send_order_{country}")],
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_list")]
        ]),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("send_order_"))
async def send_order(call: types.CallbackQuery):
    country = call.data.split("_")[2]
    await bot.send_message(ADMIN_ID, f"🛍 **НОВЫЙ ЗАКАЗ!**\n👤 От: @{call.from_user.username}\n🌍 Товар: {country}")
    await call.message.edit_caption(
        caption=f"✅ **Заявка на {country} отправлена!**\nАдмин свяжется с тобой для выдачи товара.",
        reply_markup=back_to_menu(),
        parse_mode="Markdown"
    )

# --- ПРОДАЖА ---
@dp.callback_query(F.data == "sell_start")
async def sell_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_caption(
        caption="💰 **ПРОДАЖА АККАУНТА**\n\nПришлите данные (страна, отлёжка, цена) одним сообщением:",
        reply_markup=back_to_menu(),
        parse_mode="Markdown"
    )
    await state.set_state(ShopState.selling)

@dp.message(ShopState.selling)
async def sell_process(message: types.Message, state: FSMContext):
    await bot.send_message(ADMIN_ID, f"💰 **ПРЕДЛОЖЕНИЕ ПРОДАЖИ!**\n👤 От: @{message.from_user.username}\n📝 Данные: {message.text}")
    await bot.send_message(MANAGER_ID, f"💰 **ПРЕДЛОЖЕНИЕ ПРОДАЖИ!**\n👤 От: @{message.from_user.username}\n📝 Данные: {message.text}")
    await message.answer("✅ **Данные переданы менеджеру!** Ожидайте ответа.", reply_markup=back_to_menu())
    await state.clear()

# --- ЗВЕЗДЫ (STARS) ---
@dp.callback_query(F.data == "top_up_stars")
async def top_up_stars(call: types.CallbackQuery):
    await call.message.edit_caption(
        caption="⭐ **ПОПОЛНЕНИЕ ЧЕРЕЗ TELEGRAM STARS**\n\nВыбери сумму пополнения:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⭐ 50 Stars", callback_data="pay_50")],
            [types.InlineKeyboardButton(text="⭐ 100 Stars", callback_data="pay_100")],
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]
        ]),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("pay_"))
async def start_invoice(call: types.CallbackQuery):
    amount = int(call.data.split("_")[1])
    # Создаем счет
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title="Пополнение Фофаридок",
        description=f"Пополнение баланса на {amount} ед.",
        payload="topup",
        currency="XTR", # Код для Telegram Stars
        prices=[types.LabeledPrice(label="Stars", amount=amount)]
    )
    await call.answer()

# --- ЗАПУСК ---
async def main():
    logging.basicConfig(level=logging.INFO)
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
