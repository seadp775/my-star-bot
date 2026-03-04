import asyncio
import logging
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- 1. СЕРВЕР ДЛЯ RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Favorit Market Engine: LIVE 🟢"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- 2. НАСТРОЙКИ ---
TOKEN = "8742664439:AAEzi_ucWeV2t3KrzUUbWr5ngRQLX24HkYc"
ADMIN_ID = 8266529611  # Сюда придут отчеты о продажах
PHOTO_URL = "https://cdn-ru.ru/sub/18e79943-e4a8-445c-9271-571f0df51f14"

# Временная база данных (очищается при перезагрузке Render)
MARKET_ITEMS = []

class SellFlow(StatesGroup):
    country = State()
    desc = State()
    price = State()

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- 3. КЛАВИАТУРЫ ---
def main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 РЫНОК", callback_data="market_view"))
    builder.row(
        types.InlineKeyboardButton(text="📦 ПРОДАТЬ", callback_data="market_sell"),
        types.InlineKeyboardButton(text="🆘 ПОДДЕРЖКА", url="https://t.me/favorit_shop_humber")
    )
    return builder.as_markup()

# --- 4. ОБРАБОТКА КОМАНД ---
@dp.message(CommandStart())
@dp.message(Command("cancel"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer_photo(
        photo=PHOTO_URL,
        caption="👮 **FAVORIT MARKET**\n\nПлощадка для купли и продажи аккаунтов.",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

# --- 5. ЛОГИКА ПРОДАЖИ (ДОБАВЛЕНИЕ) ---
@dp.callback_query(F.data == "market_sell")
async def sell_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("🌍 **Шаг 1:** Укажите страну аккаунта:")
    await state.set_state(SellFlow.country)
    await call.answer()

@dp.message(SellFlow.country)
async def sell_desc(message: types.Message, state: FSMContext):
    await state.update_data(country=message.text)
    await message.answer("📝 **Шаг 2:** Напишите описание товара (отлёжка, формат и т.д.):")
    await state.set_state(SellFlow.desc)

@dp.message(SellFlow.desc)
async def sell_price(message: types.Message, state: FSMContext):
    await state.update_data(desc=message.text)
    await message.answer("💰 **Шаг 3:** Укажите цену в Stars (только число):")
    await state.set_state(SellFlow.price)

@dp.message(SellFlow.price)
async def sell_finish(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Нужно ввести только число (количество звезд)!")
        return
    
    data = await state.get_data()
    item_id = len(MARKET_ITEMS) + 1
    
    new_item = {
        "id": item_id,
        "seller_name": message.from_user.username or "Anon",
        "country": data['country'],
        "desc": data['desc'],
        "price": int(message.text)
    }
    MARKET_ITEMS.append(new_item)
    
    await message.answer(f"✅ **Успешно!**\nВаш товар (ID: {item_id}) выставлен на Рынок.", reply_markup=main_menu_kb())
    await state.clear()

# --- 6. ЛОГИКА РЫНКА (ПОКУПКА) ---
@dp.callback_query(F.data == "market_view")
async def show_market(call: types.CallbackQuery):
    if not MARKET_ITEMS:
        await call.answer("Рынок пока пуст! Выставьте товар первым.", show_alert=True)
        return

    text = "🚀 **ДОСТУПНЫЕ ТОВАРЫ:**\n\n"
    builder = InlineKeyboardBuilder()
    
    for item in MARKET_ITEMS:
        text += f"🔹 ID {item['id']} | {item['country']} — {item['price']}⭐\n"
        builder.row(types.InlineKeyboardButton(text=f"Купить ID {item['id']}", callback_data=f"buy_{item['id']}"))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ НАЗАД", callback_data="to_main"))
    await call.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(call: types.CallbackQuery):
    idx = int(call.data.split("_")[1])
    item = next((i for i in MARKET_ITEMS if i['id'] == idx), None)
    
    if item:
        await bot.send_invoice(
            chat_id=call.from_user.id,
            title=f"Аккаунт {item['country']}",
            description=f"Описание: {item['desc']}\nПродавец: @{item['seller_name']}",
            payload=f"pay_{idx}",
            currency="XTR",
            prices=[types.LabeledPrice(label="Покупка", amount=item['price'])]
        )
    await call.answer()

@dp.pre_checkout_query()
async def pre_checkout(query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def success_payment(message: types.Message):
    # Уведомляем админа о сделке
    await bot.send_message(ADMIN_ID, f"💰 **ПРОДАЖА!**\nПокупатель: @{message.from_user.username}\n")
    await message.answer("✅ **Оплата принята!**\nСвяжитесь с админом или продавцом для получения данных.")

@dp.callback_query(F.data == "to_main")
async def back_home(call: types.CallbackQuery):
    await call.message.edit_caption(caption="👮 **ГЛАВНОЕ МЕНЮ**", reply_markup=main_menu_kb())

# --- 7. ЗАПУСК ---
async def main():
    logging.basicConfig(level=logging.INFO)
    keep_alive()
    # Чистим старые «запросы», чтобы не было ConflictError
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
