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

# --- СОСТОЯНИЯ ---
class ShopState(StatesGroup):
    waiting_for_sub = State()
    buying_country = State()
    selling_process = State()
    top_up_stars = State()

# --- НАСТРОЙКИ ---
TOKEN = "8742664439:AAEzi_ucWeV2t3KrzUUbWr5ngRQLX24HkYc"
ADMIN_ID = 8266529611
CHANNEL_ID = "-1003780152007"  
CHANNEL_URL = "https://t.me/твой_канал" # ССЫЛКА НА КАНАЛ
SUPPORT_URL = "https://t.me/favorit_shop_humber"
REVIEWS_URL = "https://t.me/+7awHvRF0hmtmZGRl"
POST_URL = "https://t.me/c/3780152007/21"
# Ссылка на фото (проверь, чтобы файл лежал в GitHub)
MENU_PHOTO = "https://raw.githubusercontent.com/seadp775/my-star-bot/main/1000036915.jpg"

PRICES = {
    "🇮🇳 Индия": 60, "🇨🇦 Канада": 130, "🇧🇩 Бангладеш": 100,
    "🇺🇸 США": 150, "🇿🇦 ЮАР": 150, "🇲🇲 Мьянма": 60,
    "🇮🇩 Индонезия": 100, "🇲🇦 Марокко": 150
}

bot = Bot(token=TOKEN)
dp = Dispatcher()
user_balances = {} # Временное хранение баланса

# Проверка подписки
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status != 'left'
    except: return True # Если бот не админ в канале

def main_menu():
    kb = [
        [types.InlineKeyboardButton(text="📱 Купить аккаунт", callback_data="buy_list")],
        [types.InlineKeyboardButton(text="💰 Продать аккаунт", callback_data="sell_start")],
        [types.InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
         types.InlineKeyboardButton(text="💎 Пополнить", callback_data="top_up")],
        [types.InlineKeyboardButton(text="⭐️ Отзывы", url=REVIEWS_URL),
         types.InlineKeyboardButton(text="🆘 Поддержка", url=SUPPORT_URL)]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    if not await check_sub(message.from_user.id):
        kb = [[types.InlineKeyboardButton(text="✅ Подписаться", url=CHANNEL_URL)],
              [types.InlineKeyboardButton(text="🔄 Проверить", callback_data="check_sub")]]
        await message.answer("❌ Чтобы пользоваться ботом, подпишитесь на канал!", 
                           reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))
        return
    
    try:
        await message.answer_photo(photo=MENU_PHOTO, caption="👮 Добро пожаловать в **Фаворит шоп**!", 
                                 reply_markup=main_menu(), parse_mode="Markdown")
    except:
        await message.answer("👮 Добро пожаловать в **Фаворит шоп**!", reply_markup=main_menu())

@dp.callback_query(F.data == "check_sub")
async def callback_check_sub(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await cmd_start(call.message)
    else:
        await call.answer("❌ Вы всё еще не подписаны!", show_alert=True)

# --- ПРОФИЛЬ И ПОПОЛНЕНИЕ ---
@dp.callback_query(F.data == "profile")
async def profile(call: types.CallbackQuery):
    bal = user_balances.get(call.from_user.id, 0)
    await call.message.answer(f"👤 **Профиль**\n🆔 ID: `{call.from_user.id}`\n💰 Баланс: **{bal} фофаридок**", 
                            parse_mode="Markdown", reply_markup=main_menu())
    await call.answer()

@dp.callback_query(F.data == "top_up")
async def top_up(call: types.CallbackQuery):
    await call.message.answer("💎 **Пополнение через Telegram Stars**\n1 Звезда = 1 Фофаридка.\n\nВведите сумму (число):")
    await dp.fsm.set_state(ShopState.top_up_stars)
    await call.answer()

@dp.message(ShopState.top_up_stars)
async def process_stars(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        amount = int(message.text)
        await message.answer_invoice(
            title="Пополнение баланса", description=f"{amount} фофаридок",
            payload="topup", currency="XTR", prices=[types.LabeledPrice(label="XTR", amount=amount)]
        )
        await state.clear()
    else: await message.answer("Введите число!")

@dp.pre_checkout_query()
async def pre_checkout(query: types.PreCheckoutQuery):
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def success_pay(message: types.Message):
    amount = message.successful_payment.total_amount
    user_balances[message.from_user.id] = user_balances.get(message.from_user.id, 0) + amount
    await message.answer(f"✅ Баланс пополнен на {amount} фофаридок!")

# --- ПОКУПКА ---
@dp.callback_query(F.data == "buy_list")
async def buy_list(call: types.CallbackQuery):
    kb = []
    for country, price in PRICES.items():
        kb.append([types.InlineKeyboardButton(text=f"{country} — {price}₽", callback_data=f"buy_{country}")])
    kb.append([types.InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")])
    await call.message.answer("📱 **Выберите страну аккаунта:**", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def confirm_buy(call: types.CallbackQuery):
    country = call.data.replace("buy_", "")
    price = PRICES.get(country, 0)
    text = (f"⚠️ **ВНИМАНИЕ!**\nПрочитайте этот пост: {POST_URL}\n\n"
            f"Если пропустите это сообщение, то - аккаунт!\n\n"
            f"Цена: **{price} фофаридок**\nВы уверены?")
    kb = [[types.InlineKeyboardButton(text="✅ Купить", callback_data=f"pay_{country}_{price}"),
           types.InlineKeyboardButton(text="❌ Отмена", callback_data="buy_list")]]
    await call.message.answer(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data.startswith("pay_"))
async def final_pay(call: types.CallbackQuery):
    _, country, price = call.data.split("_")
    price = int(price)
    user_id = call.from_user.id
    
    if user_balances.get(user_id, 0) >= price:
        user_balances[user_id] -= price
        await call.message.answer("✅ Оплата прошла! Админ свяжется с вами для передачи данных.")
        await bot.send_message(ADMIN_ID, f"🛍 **ПОКУПКА АККАУНТА**\n👤 Юзер: @{call.from_user.username}\n🌍 Страна: {country}\n💰 Списано: {price} фофаридок")
    else:
        await call.answer("❌ Недостаточно фофаридок! Пополните баланс.", show_alert=True)

# --- ПРОДАЖА ---
@dp.callback_query(F.data == "sell_start")
async def sell_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📝 **Продажа аккаунта**\nВведите юзернейм вашего аккаунта (мы возьмём 10% комиссии):")
    await state.set_state(ShopState.selling_process)
    await call.answer()

@dp.message(ShopState.selling_process)
async def sell_end(message: types.Message, state: FSMContext):
    await bot.send_message(ADMIN_ID, f"💰 **ПРОДАЖА АККАУНТА**\n👤 От: @{message.from_user.username}\nℹ️ Данные: {message.text}")
    await message.answer("✅ Информация отправлена менеджеру @favorit_shop_humber2. Ожидайте ответа!")
    await state.clear()

async def main():
    logging.basicConfig(level=logging.INFO)
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
