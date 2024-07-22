from aiogram.types import Message
from aiogram.types.message import ContentType
import aiogram
from aiogram import Dispatcher, Bot, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher.filters import Command
import sqlite3
from aiogram.types import CallbackQuery
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncio

storage = MemoryStorage()
TOKEN = '6193615325:AAF-oc9mPq62YnVVMD9uTIapX-ikDhXpu6I'
loop = asyncio.new_event_loop()
bot = Bot(TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, loop=loop, storage=storage)


class DataBase:
    def __init__(self, db_file):
        self.connect = sqlite3.connect(db_file)
        self.cursor = self.connect.cursor()

    async def add_itog(self, user_id, ocen, pred):
        with self.connect:
            return self.cursor.execute("""INSERT INTO itog (user_id,ocen,pred) VALUES (?,?,?)""", [user_id, ocen, pred])

    async def get_itog(self, user_id):
        with self.connect:
            return self.cursor.execute("""SELECT * FROM itog WHERE user_id=(?)""", [user_id]).fetchall()

    async def add_norm(self, user_id, pod, time100, time3):
        with self.connect:
            return self.cursor.execute("""INSERT INTO norm (user_id,pod,time100,time3) VALUES (?,?,?,?)""",
                                       [user_id, pod, time100, time3])

    async def get_norm(self, user_id):
        with self.connect:
            return self.cursor.execute("""SELECT * FROM norm WHERE user_id=(?)""", [user_id]).fetchall()


db = DataBase('mrbeast.db')


@dp.message_handler(Command('start'))
async def start(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(text='Добавить итоговую оценку за предмет'))
    markup.add(KeyboardButton(text='Добавить результаты нормативов'))
    markup.add(KeyboardButton(text='Узнать среднюю успеваемость'))
    markup.add(KeyboardButton(text='Узнать оценку за нормативы'))
    markup.add(KeyboardButton(text='Попаду ли на военку?'))
    await message.answer('Привет, чем я могу тебе помочь?', reply_markup=markup)


class helo1(StatesGroup):
    ocen = State()
    pred = State()


@dp.message_handler(Text('Добавить итоговую оценку за предмет'))
async def additog(message: Message):
    await message.answer('Введите название предмета')
    await helo1.ocen.set()


@dp.message_handler(state=helo1.ocen)
async def adress(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['pred'] = message.text
    await message.answer('Введите вашу оценку')
    await helo1.next()


@dp.message_handler(state=helo1.pred)
async def adress(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['ocen'] = message.text
    if int(message.text) >= 4:
        await db.add_itog(message.chat.id, data["ocen"], data["pred"])
        await message.answer(
            f'Итоговая оценка добавлена \n<b>Предмет</b> - {data["pred"]} \n<b>Оценка</b> - {data["ocen"]} \n')
    else:
        await message.answer('За этот предмет у вас незачёт')
    await state.finish()


@dp.message_handler(Text('Узнать среднюю успеваемость'))
async def srusp(message: Message):
    data = await db.get_itog(message.chat.id)
    if not data:
        await message.answer('Вы ввели не все данные')
    else:
        count = 0
        sum = 0
        for i in data:
            count += 1
            sum += i[1]
        itog = sum / count
        await message.answer(f'Ваша средняя успеваемость - {itog}')


class helo2(StatesGroup):
    pod = State()
    time100 = State()
    time3 = State()


@dp.message_handler(Text('Добавить результаты нормативов'))
async def addnorm(message: Message):
    await message.answer('Введите количество подтягиваний')
    await helo2.pod.set()


@dp.message_handler(state=helo2.pod)
async def podtg(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['pod'] = message.text
    await message.answer('Введите время бега на 100 метров \n<b>В секундах</b>')
    await helo2.next()


@dp.message_handler(state=helo2.time100)
async def beg100(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['time100'] = message.text
    await message.answer('Введите время бега на 3 километра \n<b>В секундах</b>')
    await helo2.next()


@dp.message_handler(state=helo2.time3)
async def beg3(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['time3'] = message.text
    await db.add_norm(message.chat.id, data["pod"], data["time100"], data["time3"])
    await message.answer(
        f'Нормативы внесены \n<b>Подтягивания</b> - {data["pod"]} \n<b>Бег на 100 метров</b> - {data["time100"]} \n<b>Бег на 3 километра</b> - {data["time3"]} \n')
    await state.finish()


@dp.message_handler(Text('Узнать оценку за нормативы'))
async def addnorm(message: Message):
    data = await db.get_norm(message.chat.id)
    if not data:
        await message.answer('Вы ввели не все данные')
    else:
        pod = data[0][1]
        time100 = data[0][2]
        time3 = data[0][3]
        if pod >= 4 and time100 <= 15.4 and time3 <= 896:
            await message.answer('Ваша оценка - <b>зачёт</b>')
        else:
            await message.answer('Ваша оценка - <b>незачёт</b>')


@dp.message_handler(Text('Попаду ли на военку?'))
async def voenka(message: Message):
    data1 = await db.get_itog(message.chat.id)
    data2 = await db.get_norm(message.chat.id)
    if not data1 or not data2:
        await message.answer('Вы ввели не все данные')
    else:
        pod = data2[0][1]
        time100 = data2[0][2]
        time3 = data2[0][3]
        count = 0
        sum = 0
        for i in data1:
            count += 1
            sum += i[1]
        itog = sum / count
        if pod >= 4 and time100 <= 15.4 and time3 <= 896 and itog >= 4:
            await message.answer('<b>Да</b>')
        else:
            await message.answer('<b>Нет</b>')


if __name__ == '__main__':
    executor.start_polling(dp, loop=loop)
