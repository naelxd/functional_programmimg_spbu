import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command, CommandStart

import python_weather
import translators as ts
from forex_python.converter import CurrencyRates


TOKEN = 'your_token'

form_router = Router()

# настройка логирования
logging.basicConfig(level=logging.INFO)


# определение состояний беседы
class Conversation(StatesGroup):
    name = State()
    age = State()
    weather = State()
    currency = State()
    translate = State()


@form_router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    await state.set_state(Conversation.name)
    await message.answer("Привет! Как тебя зовут?")


@form_router.message(Conversation.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Conversation.age)
    await message.answer("Сколько тебе лет?")


@form_router.message(Conversation.age)
async def process_age_invalid(message: Message, state: FSMContext):
    kb = [
            [KeyboardButton(text='погода')],
            [KeyboardButton(text='валюта')],
            [KeyboardButton(text='переведи')]
            ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb)
    if not message.text.isdigit():
        await message.answer("Возраст должен быть числом. Сколько тебе лет?")
    else:
        data = await state.update_data(age=message.text)
        data['age'] = message.text
        name = data['name']
        age = data['age']
        await state.clear()
        await message.answer(f"Приятно познакомиться, {name}! Тебе {age} лет.", 
                             reply_markup=keyboard)


@form_router.message(F.text.lower() == 'привет')
async def greet(message: Message):
    await message.answer("Привет!")


@form_router.message(F.text.lower() == 'погода')
async def get_weather_message(message: Message, state: FSMContext):
    await state.set_state(Conversation.weather)
    await message.answer("В каком городе хотите узнать?")


@form_router.message(F.text.lower() == 'валюта')
async def get_rate_message(message: Message, state: FSMContext):
    await state.set_state(Conversation.currency)
    ans = '''|EUR - Euro Member Countries |IDR - Indonesia Rupiah |BGN - Bulgaria Lev |ILS - Israel Shekel |GBP - United Kingdom Pound |DKK - Denmark Krone |CAD - Canada Dollar |JPY - Japan Yen |HUF - Hungary Forint |RON - Romania New Leu |MYR - Malaysia Ringgit |SEK - Sweden Krona |SGD - Singapore Dollar |HKD - Hong Kong Dollar |AUD - Australia Dollar |CHF - Switzerland Franc |KRW - Korea (South) Won |CNY - China Yuan Renminbi |TRY - Turkey Lira |HRK - Croatia Kuna |NZD - New Zealand Dollar |THB - Thailand Baht |USD - United States Dollar |NOK - Norway Krone |INR - India Rupee |MXN - Mexico Peso |CZK - Czech Republic Koruna |BRL - Brazil Real |PLN - Poland Zloty |PHP - Philippines Peso |ZAR - South Africa Rand
Введите валюты через пробел и сумму (USD EUR 10)?'''
    await message.answer(ans)

@form_router.message(F.text.lower() == 'переведи')
async def get_translation_message(message: Message, state: FSMContext):
    await state.set_state(Conversation.translate)
    await message.answer("Что перевести?")



@form_router.message(Conversation.weather)
async def answer_weather_message(message: Message, state: FSMContext):
    await state.clear()
    weather = await get_weather(message.text)
    await message.answer(weather)


@form_router.message(Conversation.currency)
async def answer_rate_message(message: Message, state: FSMContext):
    await state.clear()
    cur1, cur2, amount = message.text.split(' ')
    rate = await get_rate(cur1, cur2, int(amount))
    await message.answer(rate)


@form_router.message(Conversation.translate)
async def answer_translation_message(message: Message, state: FSMContext):
    await state.clear()
    text = await get_translation(message.text)
    await message.answer(text)


async def get_weather(city: str):
  async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
    weather = await client.get(city)
    text = f'''Температура: {int((weather.current.temperature - 32) * 5 / 9)} градусов C
Чувствуется температура как: {int((weather.current.feels_like - 32) * 5 / 9)} градусов C
Давление: {weather.current.pressure}
Осадки: {weather.current.precipitation} мм
Влажность: {weather.current.humidity} %
Скорость ветра: {weather.current.wind_speed} км/ч
'''
    return text


async def get_rate(cur1: str, cur2: str, amount: int):
    c = CurrencyRates()
    return f'{c.convert(cur1, cur2, amount)}'

async def get_translation(text: str):
    return ts.translate_text(text, translator='google', to_language='ru')


@form_router.message()
async def unknown_command(message: Message):
    await message.answer("Введите команду.")


async def main():
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(form_router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

