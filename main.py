import asyncio
import logging
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- ТЕХНИЧЕСКАЯ ЧАСТЬ ---
app = Flask('')
@app.route('/')
def home(): return "Favorit Market is Running! 🛒"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- КОНФИГ ---
TOKEN = "8742664439:AAEzi_ucWeV2t3KrzUUbWr5ngRQLX24HkYc"
ADMIN_ID = 8266529611
PHOTO_URL = "https://cdn-ru.ru/sub/18e79943-e4a8-445c-9271-571f0df51f14"

# Глобальный список товаров (в памяти)
MARKET_DATABASE = []

class SellForm(StatesGroup):
    country = State()
    description = State()
    price = State()

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КЛАВИАТУРЫ ---
def main_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 РЫНОК", callback_data="open_market"))
    builder.row(
        types.InlineKeyboardButton(text="📦 ПРОДАТЬ", callback_data="start_sell"),
        types.InlineKeyboardButton(text="🆘 ПОДДЕРЖКА", url="https://t.me/favorit_shop_humber")
    )
    return builder.as_markup()

# --- ГЛАВНОЕ МЕНЮ ---
@dp.message(CommandStart())
@dp.message(Command("cancel"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer_photo(
        photo=PHOTO_URL,
        caption="👮 **FAVORIT MARKET**\n\nКупля и продажа аккаунтов в одном месте.",
        reply_markup=main_kb(),
        parse_mode="Markdown"
    )

# --- ЛОГИКА ПРОДАЖИ (ДОБАВЛЕНИЕ В РЫНОК) ---
@dp.callback_query(F.data == "start_sell")
async def sell_1(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("🌍 **Шаг 1:** Из какой страны аккаунт?")
    await state.set_state(SellForm.country)
    await call.answer()

@dp.message(SellForm.country)
async def sell_2(message: types.Message, state: FSMContext):
    await state.update_data(country=message.text)
    await message.answer("📝 **Шаг 2:** Напиши описание (что на аккаунте, отлёжка и т.д.):")
    await state.set_state(SellForm.description)

@dp.message(SellForm.description)
async def sell_3(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("💰 **Шаг 3:** Укажи цену в Telegram Stars (только число):")
    await state.set_state(SellForm.price)

@dp.message(SellForm.price)
async def sell_final(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введи число!")
        return
    
    data = await state.get_data()
    new_item = {
        "id": len(MARKET_DATABASE) + 1,
        "seller": message.from_user.username or message.from_user.id,
        "country": data['country'],
        "desc": data['description'],
        "price": int(message.text)
    }
    MARKET_DATABASE.append(new_item)
    
    await message.answer("✅ **Товар выставлен на Рынок!**", reply_markup=main_kb())
    await state.clear()

# --- ЛОГИКА РЫНКА (ПРОСМОТР И ПОКУПКА) ---
@dp.callback_query(F.data == "open_market")
async def show_market(call: types.CallbackQuery):
    if not MARKET_DATABASE:
        await call.answer("Пусто! Будь первым, кто выставит товар.", show_alert=True)
        return

    text = "🚀 **АКТУАЛЬНЫЕ ТОВАРЫ:**\n\n"
    builder = InlineKeyboardBuilder()
    
    for item in MARKET_DATABASE:
        text += f"ID {item['id']} | {item['country']} — {item['price']}⭐\n"
        builder.row(types.InlineKeyboardButton(
            text=f"Купить ID {item['id']} ({item['country']})", 
            callback_data=f"buy_{item['id']}"
        ))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ НАЗАД", callback_data="back_to_menu"))
    await call.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(call: types.CallbackQuery):
    item_id = int(call.data.split("_")[1])
    item = next((i for i in MARKET_DATABASE if i['id'] == item_id), None)
    
    if item:
        await bot.send_invoice(
            chat_id=call.from_user.id,
            title=f"Аккаунт {item['country']}",
            description=f"Описание: {item['desc']}\nПродавец: @{item['seller']}",
            payload=f"pay_{item_id}",
            currency="XTR",
            prices=[types.LabeledPrice(label="Покупка", amount=item['price'])]
        )
    await call.answer()

@dp.pre_checkout_query()
async def checkout(query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def success_pay(message: types.Message):
    item_id = int(message.successful_payment.invoice_payload.split("_")[1])
    # Уведомляем админа
    await bot.send_message(ADMIN_ID, f"💰 **ПРОДАНО!**\nТовар ID: {item_id}\nПокупатель: @{message.from_user.username}")
    await message.answer("✅ Оплата прошла! Свяжитесь с продавцом или админом для получения данных.")

@dp.callback_query(F.data == "back_to_menu")
async def back(call: types.CallbackQuery):
    await call.message.edit_caption(caption="👮 **FAVORIT MARKET**", reply_markup=main_kb())

# --- ЗАПУСК ---
async def main():
    logging.basicConfig(level=logging.INFO)
    keep_alive()
    await bot.delete_webhook(drop_pending_updates=True) # Защита от ConflictError
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
