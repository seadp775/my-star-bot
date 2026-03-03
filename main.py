import asyncio
import logging
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# --- БЛОК 24/7 (ДЛЯ RENDER) ---
app = Flask('')
@app.route('/')
def home(): return "Бот «Фаворит шоп» запущен и готов к работе! 👮"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- СОСТОЯНИЯ (FSM) ---
class ShopState(StatesGroup):
    # Покупка
    buying_country = State()
    # Продажа
    selling_data = State()
    # Пополнение
    top_up_amount = State()
    top_up_method = State()

# --- НАСТРОЙКИ (ВСТАВЬ СВОИ ДАННЫЕ!) ---
TOKEN = "8742664439:AAEzi_ucWeV2t3KrzUUbWr5ngRQLX24HkYc" #
ADMIN_ID = 8266529611 #

# ID закрытого канала (начинается на -100)
CHANNEL_ID = -1001859943545 
# Ссылка-приглашение в твой закрытый канал
CHANNEL_URL = "https://t.me/+P5-6K7k3625kNzAy" 

# Ссылки из твоего запроса
SUPPORT_URL = "https://t.me/favorit_shop_humber" #
REVIEWS_URL = "https://t.me/+7awHvRF0hmtmZGRl" #
POST_URL = "https://t.me/c/3780152007/21" #

# ТВОЁ НОВОЕ КРАСИВОЕ ФОТО ДЛЯ МЕНЮ
MENU_PHOTO = "https://cdn-ru.ru/sub/18e79943-e4a8-445c-9271-571f0df51f14"

# Цены в Фофаридках (1Ф = 1₽)
PRICES = {
    "🇮🇳 Индия": 60, "🇨🇦 Канада": 130, "🇧🇩 Бангладеш": 100,
    "🇺🇸 США": 150, "🇿🇦 ЮАР": 150, "🇲🇲 Мьянма": 60,
    "🇮🇩 Индонезия": 100, "🇲🇦 Марокко": 150
}

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

# 1. Проверка подписки
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status != 'left': return True
        return False
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")
        # Если бот не админ в канале, он не сможет проверить. Возвращаем True, чтобы не блокировать.
        return True

# 2. Красивое главное меню
def main_menu():
    kb = [
        [types.InlineKeyboardButton(text="📱 Купить аккаунт", callback_data="buy_list")],
        [types.InlineKeyboardButton(text="💰 Продать аккаунт", callback_data="sell_start")],
        [types.InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
         types.InlineKeyboardButton(text="💎 Пополнить", callback_data="top_up_start")],
        [types.InlineKeyboardButton(text="⭐️ Отзывы", url=REVIEWS_URL),
         types.InlineKeyboardButton(text="🆘 Поддержка", url=SUPPORT_URL)]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

# 3. Кнопка "Назад"
def back_btn(data):
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ Назад", callback_data=data)]
    ])

# --- ОБРАБОТЧИКИ КОМАНД ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear() # Сбрасываем все состояния
    user_id = message.from_user.id
    
    # Сразу проверяем подписку
    if not await check_sub(user_id):
        text = (
            "🔒 **ДОСТУП ОГРАНИЧЕН!**\n\n"
            "Чтобы пользоваться ботом «Фаворит шоп» 👮, необходимо подписаться на наш закрытый канал."
        )
        kb = [
            [types.InlineKeyboardButton(text="✅ Подписаться", url=CHANNEL_URL)],
            [types.InlineKeyboardButton(text="🔄 Проверить", callback_data="check_sub")]
        ]
        await message.answer(text, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))
        return

    # Если подписан - показываем красивое меню с фото
    try:
        await message.answer_photo(
            photo=MENU_PHOTO, 
            caption=(
                "👮 **Добро пожаловать в Фаворит шоп!**\n\n"
                "Здесь ты найдёшь лучшие аккаунты по самым сочным ценам! 🍓\n\n"
                "👇 Выберите действие в меню:"
            ), 
            reply_markup=main_menu(), 
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Ошибка отправки фото: {e}")
        # Если фото не грузится, отправляем просто текст
        await message.answer(
            "👮 **Добро пожаловать в Фаворит шоп!**\n\n👇 Выберите действие в меню:", 
            reply_markup=main_menu(), 
            parse_mode="Markdown"
        )

@dp.callback_query(F.data == "check_sub")
async def callback_check_sub(call: types.CallbackQuery, state: FSMContext):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await cmd_start(call.message, state) # Перезапускаем старт
    else:
        await call.answer("❌ Вы всё еще не подписаны на канал!", show_alert=True)

# --- РАЗДЕЛ: ГЛАВНОЕ МЕНЮ (ОБРАБОТКА НАЗАД) ---
@dp.callback_query(F.data == "main_menu")
async def back_to_main(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await cmd_start(call.message, state)
    await call.answer()

# --- РАЗДЕЛ: ПРОФИЛЬ ---
@dp.callback_query(F.data == "profile")
async def profile(call: types.CallbackQuery):
    # Т.к. базы данных нет, баланс всегда 0. Это для красоты.
    text = (
        f"👤 **ТВОЙ ПРОФИЛЬ:**\n\n"
        f"🆔 Твой ID: `{call.from_user.id}`\n"
        f"💰 Баланс: **0 фофаридок**\n"
        f"⭐ Статус: **Активный клиент**"
    )
    await call.message.answer(text, parse_mode="Markdown", reply_markup=back_btn("main_menu"))
    await call.answer()

# --- РАЗДЕЛ: ПОПОЛНЕНИЕ (ЧЕРЕЗ АДМИНА) ---
@dp.callback_query(F.data == "top_up_start")
async def top_up_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(
        "💎 **ПОПОЛНЕНИЕ БАЛАНСА**\n\n"
        "1 Фофаридка = 1₽.\n\n"
        "👇 **Введите сумму**, на которую хотите пополнить счёт (числом):",
        reply_markup=back_btn("main_menu"),
        parse_mode="Markdown"
    )
    await state.set_state(ShopState.top_up_amount)
    await call.answer()

@dp.message(ShopState.top_up_amount)
async def process_top_up_amount(message: types.Message, state: FSMContext):
    if message.text.isdigit() and int(message.text) > 0:
        await state.update_data(amount=message.text)
        
        kb = [
            [types.InlineKeyboardButton(text="💳 Карта (РФ)", callback_data="method_card")],
            [types.InlineKeyboardButton(text="📲 СБП", callback_data="method_sbp")],
            [types.InlineKeyboardButton(text="⭐ Telegram Stars", callback_data="method_stars")],
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up_start")]
        ]
        await message.answer(
            "💳 **Выберите способ оплаты:**",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
            parse_mode="Markdown"
        )
        await state.set_state(ShopState.top_up_method)
    else:
        await message.answer("❌ **Ошибка!** Введите корректную сумму (только число, больше 0).")

@dp.callback_query(ShopState.top_up_method, F.data.startswith("method_"))
async def process_top_up_method(call: types.CallbackQuery, state: FSMContext):
    method_raw = call.data.replace("method_", "")
    methods = {"card": "💳 Карта", "sbp": "📲 СБП", "stars": "⭐ Stars"}
    method_name = methods.get(method_raw, "Неизвестно")
    
    data = await state.get_data()
    amount = data.get('amount')
    
    # Отправляем заявку Админу
    admin_text = (
        f"💎 **ЗАЯВКА НА ПОПОЛНЕНИЕ!**\n\n"
        f"👤 От: @{call.from_user.username} (🆔 `{call.from_user.id}`)\n"
        f"💰 Сумма: **{amount}₽**\n"
        f"💳 Способ: **{method_name}**\n\n"
        f"👉 Свяжись с клиентом для получения оплаты и начисли баланс!"
    )
    await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    
    # Отвечаем пользователю
    await call.message.answer(
        f"✅ **Заявка на {amount} фофаридок отправлена!**\n\n"
        f"Администратор {SUPPORT_URL} свяжется с вами в ближайшее время и предоставит реквизиты для оплаты ({method_name}).\n\n"
        f"После оплаты баланс будет начислен автоматически.",
        reply_markup=back_btn("main_menu"),
        parse_mode="Markdown"
    )
    await state.clear()
    await call.answer()

# --- РАЗДЕЛ: ПОКУПКА ---
@dp.callback_query(F.data == "buy_list")
async def buy_list(call: types.CallbackQuery):
    kb = []
    # Формируем список кнопок из словаря PRICES
    for country, price in PRICES.items():
        kb.append([types.InlineKeyboardButton(text=f"{country} — {price} фофаридок", callback_data=f"buy_{country}")])
    kb.append([types.InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")])
    
    await call.message.answer(
        "📱 **СПИСОК ДОСТУПНЫХ СТРАН:**\n\nВыбери нужную страну:", 
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), 
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def confirm_buy(call: types.CallbackQuery):
    country = call.data.replace("buy_", "")
    price = PRICES.get(country, 0)
    
    text = (
        f"⚠️ **ВНИМАНИЕ! КРИТИЧЕСКИ ВАЖНО!**\n\n"
        f"Перед покупкой **ОБЯЗАТЕЛЬНО** прочитайте этот пост: {POST_URL}\n\n"
        f"Если вы пропустите это сообщение и не прочитаете правила, то аккаунт может быть утерян! ❌\n\n"
        f"---📜 **Твой заказ** ---\n"
        f"🌍 Страна: **{country}**\n"
        f"💰 Цена: **{price} фофаридок**\n\n"
        f"**Всё верно? У вас достаточно средств?**"
    )
    kb = [
        [types.InlineKeyboardButton(text="✅ Да, купить", callback_data=f"pay_{country}_{price}")],
        [types.InlineKeyboardButton(text="❌ Отмена", callback_data="buy_list")]
    ]
    await call.message.answer(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data.startswith("pay_"))
async def final_pay(call: types.CallbackQuery):
    _, country, price = call.data.split("_")
    
    # Т.к. баланс всегда 0, сразу отправляем заявку Админу, как будто оплата "в процессе"
    await call.message.answer(
        f"✅ **Заявка на покупку {country} отправлена!**\n\n"
        f"Администратор свяжется с вами для проверки баланса и передачи данных.",
        reply_markup=back_btn("main_menu"),
        parse_mode="Markdown"
    )
    
    # Уведомление Админу
    admin_text = (
        f"🛍 **ЗАЯВКА НА ПОКУПКУ!**\n\n"
        f"👤 От: @{call.from_user.username} (🆔 `{call.from_user.id}`)\n"
        f"🌍 Страна: **{country}**\n"
        f"💰 Цена: **{price} Фофаридок**\n\n"
        f"👉 Проверь баланс клиента и свяжись с ним!"
    )
    await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    await call.answer()

# --- РАЗДЕЛ: ПРОДАЖА ---
@dp.callback_query(F.data == "sell_start")
async def sell_start(call: types.CallbackQuery, state: FSMContext):
    text = (
        "💰 **ПРОДАЖА ТВОЕГО АККАУНТА**\n\n"
        "Мы готовы перепродать твой аккаунт! 🤝\n\n"
        "👇 **Пришлите данные** в таком формате:\n"
        "1. Юзернейм (логин) аккаунта\n"
        "2. Какую цену вы хотите (мы возьмём 10% комиссии)\n"
        "3. Страна аккаунта и его тип"
    )
    await call.message.answer(text, reply_markup=back_btn("main_menu"), parse_mode="Markdown")
    await state.set_state(ShopState.selling_data)
    await call.answer()

@dp.message(ShopState.selling_data)
async def sell_end(message: types.Message, state: FSMContext):
    # Отправляем данные Менеджеру
    manager_text = (
        f"💰 **ЗАЯВКА НА ПРОДАЖУ!**\n\n"
        f"👤 От: @{message.from_user.username} (🆔 `{message.from_user.id}`)\n"
        f"📝 **Данные клиента:**\n{message.text}"
    )
    await bot.send_message(ADMIN_ID, manager_text, parse_mode="Markdown") # Менеджер=Админ
    
    await message.answer(
        f"✅ **Ваша заявка успешно отправлена!**\n\n"
        f"Менеджер свяжется с вами в ближайшее время для уточнения деталей и постановки аккаунта на продажу.",
        reply_markup=back_btn("main_menu"),
        parse_mode="Markdown"
    )
    await state.clear()

# --- ЗАПУСК ---
async def main():
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    # Запуск Flask в отдельном потоке (для keep_alive)
    keep_alive()
    # Запуск бота (polling)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
