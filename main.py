import asyncio
import logging
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# --- СЕРВЕР ДЛЯ RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Favorit Shop Active! 👮"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- СОСТОЯНИЯ ---
class Form(StatesGroup):
    waiting_for_sell_data = State()

# --- КОНФИГ ---
TOKEN = "8742664439:AAEzi_ucWeV2t3KrzUUbWr5ngRQLX24HkYc"
ADMIN_ID = 8266529611      # Твой ID (для покупок)
MANAGER_ID = 8490517217    # ID Менеджера (для продаж)

MENU_PHOTO = "https://cdn-ru.ru/sub/18e79943-e4a8-445c-9271-571f0df51f14"

PRICES = {
    "🇮🇳 Индия": 60, "🇨🇦 Канада": 130, "🇧🇩 Бангладеш": 100,
    "🇺🇸 США": 150, "🇿🇦 ЮАР": 150, "🇲🇲 Мьянма": 60,
    "🇮🇩 Индонезия": 100, "🇲🇦 Марокко": 150
}

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КЛАВИАТУРЫ ---
def main_kb():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📱 Купить аккаунт", callback_data="buy_list")],
        [types.InlineKeyboardButton(text="💰 Продать аккаунт", callback_data="sell_start")],
        [types.InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
         types.InlineKeyboardButton(text="⭐ Пополнить (Stars)", callback_data="top_up_stars")],
        [types.InlineKeyboardButton(text="🆘 Поддержка", url="https://t.me/favorit_shop_humber")]
    ])

def back_btn():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="to_main")]
    ])

# --- ЛОГИКА ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer_photo(
        photo=MENU_PHOTO,
        caption="👮 **Добро пожаловать в Фаворит шоп!**\n\nВыбирай нужный раздел ниже:",
        reply_markup=main_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "to_main")
async def to_main(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        # Редактируем старое, чтобы не спамить
        await call.message.edit_caption(
            caption="👮 **Главное меню**\n\nВыбирай раздел:",
            reply_markup=main_kb(),
            parse_mode="Markdown"
        )
    except:
        await call.message.delete()
        await cmd_start(call.message, state)

# --- ПРОФИЛЬ ---
@dp.callback_query(F.data == "profile")
async def profile(call: types.CallbackQuery):
    text = f"👤 **ВАШ ПРОФИЛЬ**\n\n🆔 ID: `{call.from_user.id}`\n💰 Баланс: **0 фофаридок**"
    await call.message.edit_caption(caption=text, reply_markup=back_btn(), parse_mode="Markdown")

# --- ПОКУПКА (Уведомление тебе) ---
@dp.callback_query(F.data == "buy_list")
async def buy_list(call: types.CallbackQuery):
    kb = [[types.InlineKeyboardButton(text=f"{c} — {p}₽", callback_data=f"order_{c}")] for c, p in PRICES.items()]
    kb.append([types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")])
    await call.message.edit_caption(caption="📱 **ВЫБЕРИТЕ СТРАНУ:**", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("order_"))
async def order_confirm(call: types.CallbackQuery):
    country = call.data.split("_")[1]
    await call.message.edit_caption(
        caption=f"🌍 **Товар:** {country}\n\nОтправить заявку администратору?",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Купить", callback_data=f"send_order_{country}")],
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_list")]
        ]),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("send_order_"))
async def send_order(call: types.CallbackQuery):
    country = call.data.split("_")[2]
    # УВЕДОМЛЕНИЕ АДМИНУ (ТЕБЕ)
    await bot.send_message(ADMIN_ID, f"🛍 **НОВЫЙ ЗАКАЗ!**\n👤 Клиент: @{call.from_user.username}\n🌍 Товар: {country}")
    await call.message.edit_caption(caption=f"✅ **Заявка на {country} отправлена!**\nАдмин свяжется с тобой.", reply_markup=back_btn(), parse_mode="Markdown")

# --- ПРОДАЖА (Уведомление менеджеру) ---
@dp.callback_query(F.data == "sell_start")
async def sell_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_caption(caption="💰 **ПРОДАЖА**\n\nПришли данные об аккаунте (Страна, отлёжка, цена):", reply_markup=back_btn(), parse_mode="Markdown")
    await state.set_state(Form.waiting_for_sell_data)

@dp.message(Form.waiting_for_sell_data)
async def sell_process(message: types.Message, state: FSMContext):
    # УВЕДОМЛЕНИЕ МЕНЕДЖЕРУ
    report = f"💰 **КЛИЕНТ ХОЧЕТ ПРОДАТЬ!**\n👤 От: @{message.from_user.username}\n📝 Данные: {message.text}"
    await bot.send_message(MANAGER_ID, report)
    await message.answer("✅ **Данные переданы менеджеру!** Ожидайте ответа.", reply_markup=back_btn())
    await state.clear()

# --- ПОПОЛНЕНИЕ (STARS) ---
@dp.callback_query(F.data == "top_up_stars")
async def top_up_stars(call: types.CallbackQuery):
    kb = [[types.InlineKeyboardButton(text="⭐ 50 Stars", callback_data="pay_50")],
          [types.InlineKeyboardButton(text="⭐ 100 Stars", callback_data="pay_100")],
          [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]]
    await call.message.edit_caption(caption="⭐ **ПОПОЛНЕНИЕ STARS**", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("pay_"))
async def start_invoice(call: types.CallbackQuery):
    amount = int(call.data.split("_")[1])
    await bot.send_invoice(chat_id=call.from_user.id, title="Пополнение", description=f"{amount} фофаридок", payload="stars", currency="XTR", prices=[types.LabeledPrice(label="Stars", amount=amount)])
    await call.answer()

# --- ЗАПУСК ---
async def main():
    logging.basicConfig(level=logging.INFO)
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
