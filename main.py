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
def home(): return "Market Live!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- СКЛАД (ДАННЫЕ РЫНКА) ---
STOCK = {
    "🇺🇸 США": ["+1 34678234", "+1 30566788", "+1 21245677"],
    "🇧🇩 Бангладеш": ["+880 171234567"],
    "🇮🇳 Индия": ["+91 987654321", "+91 998877665"],
    "🇨🇦 Канада": ["+1 416555019"]
}

TOKEN = "8742664439:AAEzi_ucWeV2t3KrzUUbWr5ngRQLX24HkYc"
ADMIN_ID = 8266529611
MANAGER_ID = 8490517217
PHOTO = "https://cdn-ru.ru/sub/18e79943-e4a8-445c-9271-571f0df51f14"

class Form(StatesGroup):
    waiting_for_sell = State()

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КЛАВИАТУРЫ ---
def main_kb():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🛒 Купить аккаунт", callback_data="market_buy")],
        [types.InlineKeyboardButton(text="📦 Продать (Стать поставщиком)", callback_data="market_sell")],
        [types.InlineKeyboardButton(text="🆘 Поддержка", url="https://t.me/favorit_shop_humber")]
    ])

# --- ЛОГИКА ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer_photo(
        photo=PHOTO,
        caption="👮 **ДОБРО ПОЖАЛОВАТЬ НА РЫНОК!**\n\nЗдесь ты можешь купить готовые аккаунты или продать свои.",
        reply_markup=main_kb(),
        parse_mode="Markdown"
    )

# --- РАЗДЕЛ КУПИТЬ ---
@dp.callback_query(F.data == "market_buy")
async def show_market(call: types.CallbackQuery):
    buttons = []
    for country, items in STOCK.items():
        count = len(items)
        buttons.append([types.InlineKeyboardButton(text=f"{country} ({count} шт.)", callback_data=f"list_{country}")])
    
    buttons.append([types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")])
    await call.message.edit_caption(caption="🌍 **ВЫБЕРИ СТРАНУ:**", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("list_"))
async def show_numbers(call: types.CallbackQuery):
    country = call.data.split("_")[1]
    numbers = STOCK.get(country, [])
    
    if not numbers:
        await call.answer("Товара временно нет!", show_alert=True)
        return

    text = f"📍 **Доступные номера ({country}):**\n\n"
    kb = []
    for num in numbers:
        text += f"• `{num}`\n"
        kb.append([types.InlineKeyboardButton(text=f"Купить {num}", callback_data=f"buy_final_{country}_{num}")])
    
    kb.append([types.InlineKeyboardButton(text="⬅️ К списку стран", callback_data="market_buy")])
    await call.message.edit_caption(caption=text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_final_"))
async def buy_final(call: types.CallbackQuery):
    _, _, country, num = call.data.split("_")
    # Уведомление тебе
    await bot.send_message(ADMIN_ID, f"🛍 **ЗАКАЗ!**\n👤 Покупатель: @{call.from_user.username}\n📱 Номер: `{num}` ({country})")
    await call.answer("Заявка отправлена админу! Ожидайте связи.", show_alert=True)

# --- РАЗДЕЛ ПРОДАТЬ ---
@dp.callback_query(F.data == "market_sell")
async def sell_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("💰 **ПРОДАЖА**\nОтправь данные аккаунта (Страна, номер, цена):")
    await state.set_state(Form.waiting_for_sell)
    await call.answer()

@dp.message(Form.waiting_for_sell)
async def sell_done(message: types.Message, state: FSMContext):
    # Уведомление менеджеру
    await bot.send_message(MANAGER_ID, f"💰 **ПРЕДЛОЖЕНИЕ ОТ ПОСТАВЩИКА!**\n👤 От: @{message.from_user.username}\n📝 Данные: {message.text}")
    await message.answer("✅ **Твоя заявка на рынке!** Менеджер проверит её и свяжется с тобой.")
    await state.clear()

@dp.callback_query(F.data == "to_main")
async def back(call: types.CallbackQuery):
    await call.message.edit_caption(caption="👮 **ГЛАВНОЕ МЕНЮ**", reply_markup=main_kb())

async def main():
    logging.basicConfig(level=logging.INFO)
    keep_alive()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
