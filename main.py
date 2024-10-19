from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
import gspread
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datetime import date
import os
from aiogram import executor
import sqlite3 as sq
from urllib.parse import quote

API_TOKEN = '6593390936:AAFvqgeBd3WndujrT55P4pSIK79T4otbXss'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


def get_current_row():
    current_list = worksheet.col_values(1)
    current_list.append(' ')
    count = 0
    for item in current_list:
        count += 1
        if item == " ":
            break
    return count


def last_index_of_element(lst, target):
    last_index = None
    for i in range(len(lst)):
        if lst[i] == target:
            last_index = i
    return last_index


gc = gspread.service_account(filename='bd-equipment-fd140c172d25.json')
table = gc.open_by_key('1maXmL6TizRyoPDhlmCv19M0T776eHG6VJ9Zbx-KZ3mU')
worksheet = table.worksheet("История")
equipment_list = table.worksheet("Список оборудования")
helper_list = table.worksheet('Helper')


def db_get_user_login_turple():
    with sq.connect("equipment_bd.db") as con:
        cur = con.cursor()
        user_login_res = cur.execute("SELECT login, password FROM users")
        user_login_password = user_login_res.fetchall()
    cur.close()
    return user_login_password


def db_get_user_logins(param: bool):
    with sq.connect("equipment_bd.db") as con:
        cur = con.cursor()
        user_login_res = cur.execute("SELECT login, password FROM users")
        user_login_password = user_login_res.fetchall()
        users_list = []
        if param is True:
            for users in user_login_password:
                users_list.append(users[0])
            cur.close()
            return users_list
        else:
            for users in user_login_password:
                users_list.append(users[1])
            return users_list


def db_get_user_password_str(user):
    with sq.connect("equipment_bd.db") as con:
        cur = con.cursor()
        user_login_res = cur.execute("SELECT login, password FROM users")
        user_login_password = user_login_res.fetchall()
        for users in user_login_password:
            if users[0] == user:
                cur.close()
                return users[1]


def db_add_user(username, password):
    with sq.connect("equipment_bd.db") as con3:
        cur3 = con3.cursor()
        sq_insert_with_param = """INSERT INTO users (login, password) VALUES (?, ?);"""
        data_turple = (username, password)
        cur3.execute(sq_insert_with_param, data_turple)


def db_delete_user(username):
    with sq.connect("equipment_bd.db") as con4:
        cur4 = con4.cursor()
        sq_insert_with_param = """DELETE from users where login = ?"""
        cur4.execute(sq_insert_with_param, (username,))
        cur4.close()


def get_last_processed_row(filename):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return int(file.read())
    return 1  # Если файл не существует, начни с первой строки


def update_last_processed_row(row, filename):
    with open(filename, "w") as file:
        file.write(str(row))


LAST_PROCESSED_ROW_FILE = "last_row.txt"
last_row_list = 'last_row_equipment.txt'

global current_equipment


def get_last_row_from_table():
    current_data = equipment_list.col_values(2)
    count = 1
    for i in current_data:
        count += 1
    return count


@dp.message_handler(commands=['see_users'], state='*')
async def see_users_command_handler(message: types.Message, state=FSMContext):
    try:
        async with state.proxy() as data:
            user = data['authorized_user']
            if user in db_get_user_logins(True):
                users_text = "Список пользователей:\n"
                user_login_password1 = db_get_user_login_turple()
                for username, password in user_login_password1:
                    users_text += f"Логин: {username}, Пароль: {password}\n"
                await message.reply(users_text)
            else:
                await message.reply("Команда недоступна")
    except Exception:
        await message.answer("Команда недоступна, сначала нужно авторизоваться")


@dp.message_handler(commands=['users'], state='*')
async def users_command_handler(message: types.Message, state: FSMContext):
    try:
        user_actions_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Добавить пользователя"),
                    KeyboardButton(text="Удалить пользователя"),
                ],
                [KeyboardButton(text="Отмена")],
            ],
            resize_keyboard=True,
        )
        async with state.proxy() as data:
            user = data['authorized_user']
            if user in db_get_user_logins(True):
                await message.reply("Выбери действие:", reply_markup=user_actions_keyboard)
                await state.set_state("user_action")
            else:
                await message.reply("Команда недоступна")
    except Exception:
        await message.reply("Команда недоступна, сначала нужно авторизоваться")


@dp.message_handler(state="user_action")
async def user_action_handler(message: types.Message, state: FSMContext):
    action = message.text
    if action == "Добавить пользователя":
        await message.reply("Введи логин пользователя:")
        await state.set_state("add_username")
    elif action == "Удалить пользователя":
        await message.reply("Введи логин пользователя для удаления:")
        await state.set_state("delete_username")
    elif action == "Отмена":
        await message.reply("Команда отменена.")
        await state.reset_state(with_data=False)
    else:
        await message.reply(
            "Некорректный ввод. Пожалуйста, выбери действие:\n1. Добавить пользователя\n2. Удалить пользователя"
            "\n3. Отмена")


@dp.message_handler(state="add_username")
async def add_username_handler(message: types.Message, state: FSMContext):
    username = message.text
    if username == "Отмена":
        await state.reset_state(with_data=False)
        await message.reply("Команда отменена")
    else:
        await state.update_data(username=username)
        await message.reply("Введи пароль пользователя:")
        await state.set_state("add_password")


@dp.message_handler(state="add_password")
async def add_password_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    username = data.get("username")
    password = message.text
    if password == "Отмена":
        await state.reset_state(with_data=False)
        await message.reply("Команда отменена")
    else:
        if username and password:
            db_add_user(username, password)

            await message.reply("Пользователь успешно добавлен.")
        else:
            await message.reply("Произошла ошибка. Пользователь не добавлен.")
        await state.reset_state(with_data=False)


@dp.message_handler(state="delete_username")
async def delete_username_handler(message: types.Message, state: FSMContext):
    username = message.text
    if username in db_get_user_logins(True):
        db_delete_user(username)
        await message.reply("Пользователь успешно удален.")
    else:
        await message.reply("Пользователь не найден.")
    await state.reset_state(with_data=False)


@dp.message_handler(commands=['auth'])
async def auth(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        authorized_user = data.get('authorized_user')
        if authorized_user:
            await message.reply("Ты уже авторизован, друг, можешь пользоваться ботом!👍")
        else:
            await state.set_state("login")
            await message.reply("Введи свой логин:")


@dp.message_handler(state="login")
async def login_handler(message: types.Message, state: FSMContext):
    global authtorizer_user_find
    login = message.text.strip()
    if login in db_get_user_logins(True):
        async with state.proxy() as data:
            # Сохраняем логин пользователя
            data['login'] = login
            data['auth'] = login
            authtorizer_user_find = data['login']
        await state.set_state("password")
        await message.reply("Введи свой пароль:")
    else:
        await message.reply("Неверный логин. Попробуй снова.")


@dp.message_handler(state="password")
async def password_handler(message: types.Message, state: FSMContext):
    password = message.text.strip()
    async with state.proxy() as data:
        login = data.get('login')  # Получаем сохраненный логин пользователя
        user_data = str(db_get_user_password_str(login))
        if login and password == user_data:
            # Пользователь успешно авторизован, сохраняем его идентификатор
            data['authorized_user'] = login
            await state.reset_state(with_data=False)
            await message.reply(f"Ты успешно авторизован как {login}!")
        else:
            await message.reply("Неверный пароль. Попробуй снова, друг.")


@dp.message_handler(commands=['start'])
async def start(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        authorized_user = data.get('authorized_user')
        if authorized_user:
            await state.update_data(authorized_user=authorized_user)
            command = message.get_args()  # Получаем параметр команды
            equipments = equipment_list.col_values(5)
            del equipments[0]

            global current_equipment
            for equipment in equipments:
                # Далее, в зависимости от значения параметра (например, номера оборудования), выполняйте необходимые действия
                if command:
                    # Используем quote для кодирования параметра
                    if command == quote(equipment):
                        global current_equipment
                        current_equipment = equipment
                        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
                        keyboard.add(KeyboardButton("Посмотреть историю"), KeyboardButton("Внести изменения"))
                        await message.reply(f"Вы выбрали {equipment}. Что вы хотите с ним сделать?",
                                            reply_markup=keyboard)
                        break
                else:
                    await message.reply(
                        "Привет друг, отсканируй пожалуйста QR код на оборудовании для того, что бы внести "
                        "или посмотреть изменения, либо воспользуйся таблицей")
                    break
        else:
            await message.reply("Ты не авторизован. Введи свой логин и пароль с помощью команды /auth")


@dp.message_handler(commands='add_equipment')
async def add_equipment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        current_equipment_list = helper_list.col_values(3)
        del current_equipment_list[0]
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for i in current_equipment_list:
            keyboard.add(i)
        await message.answer("Выбери оборудование из списка: ", reply_markup=keyboard)
        await state.set_state("equipment_name")


@dp.message_handler(state="equipment_name")
async def equipment_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        current_equipment_list = helper_list.col_values(3)
        del current_equipment_list[0]
        name = message.text
        if name in current_equipment_list:
            data['equipment_name'] = name
            await message.reply("Введи марку и модель оборудования: ")
            await state.set_state("model")
        else:
            await message.answer("Выбери оборудование из списка или добавь его в таблицу")


@dp.message_handler(state='model')
async def model_change(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        model = message.text
        data['model'] = model
        await message.answer("Введи SN заводской: ")
        await state.set_state("SN_output")


@dp.message_handler(state="SN_output")
async def sn_output_change(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        sn_output = message.text
        data['sn_output'] = sn_output
        await message.answer("Введи SN внутренний")
        await state.set_state('SN_input')


@dp.message_handler(state="SN_input")
async def sn_input_change(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        today = date.today()
        timestamp = today.strftime("%m/%d/%Y")

        data['timestamp'] = timestamp
        sn_input = message.text
        data['sn_input'] = sn_input
        await message.answer("Введи дату начала эксплуатации")
        await state.set_state('exp_date')


@dp.message_handler(state="exp_date")
async def exp_date_change(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        exp_date = message.text
        data['exp_date'] = exp_date
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add("Далее")
        await message.answer("Введи комментарий(если не нужно жми кнопку далее)", reply_markup=keyboard)
        await state.set_state('comment')


@dp.message_handler(state="comment")
async def comment_change(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        comment = message.text
        if comment != "Далее":
            data['comment'] = comment
        name = data.get('equipment_name')
        model = data.get('model')
        sn_output = data.get('sn_output')
        sn_input = data.get('sn_input')
        timestamp = data.get('timestamp')
        exp_date = data.get('exp_date')
        comment = data.get('comment')

        last_row = get_last_row_from_table()

        await message.answer("Оборудование добавляется, подожди")
        equipment_list.update(f"B{last_row}", name)
        equipment_list.update(f"C{last_row}", model)
        equipment_list.update(f'D{last_row}', sn_output)
        equipment_list.update(f'E{last_row}', sn_input)
        equipment_list.update(f'F{last_row}', timestamp)
        equipment_list.update(f'G{last_row}', exp_date)
        equipment_list.update(f"H{last_row}", comment)
        await state.reset_state(with_data=False)
        await message.answer("Оборудование добавлено успешно")


@dp.message_handler(text="Посмотреть историю")
async def history_command_handler(message: types.Message, state: FSMContext):
    try:
        global current_equipment
        history = worksheet.get_all_values()
        del history[0]

        max_message_length = 4096  # Максимальная длина сообщения в Telegram

        response = f"История действий по выбранному оборудованию:\n"
        message_parts = []

        for item in history:
            if item[0] == current_equipment:
                event_info = (f"Событие (ремонт, перемещение) - {item[1]}\n"
                              f"Дата - {item[2]}\n"
                              f"Кто делал - {item[3]}\n"
                              f"Место установки - {item[4]}\n"
                              f"Текущий статус - {item[5]}\n\n")

                if len(response + event_info) > max_message_length:
                    message_parts.append(response)
                    response = f"Продолжение истории действий:\n"
                response += event_info

        message_parts.append(response)
        for part in message_parts:
            await message.answer(part)
    except Exception:
        await message.reply("Ошибка, для начала отканируй QR-код")


@dp.message_handler(text="Внести изменения")
async def change_command_handler(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            authorized_user = data.get('authorized_user')
            global current_equipment
            if authorized_user and current_equipment is not None:
                await state.update_data(authorized_user=authorized_user)
                await message.reply("Введите действие, которое происходило с оборудованием:")
                await state.set_state("change_timestamp")
            else:
                await message.reply("Ты не авторизован, воспользуйся командой /auth")
    except Exception:
        await message.reply("Ошибка, для начала отканируй QR-код")


@dp.message_handler(state="change_timestamp")
async def change_timestamp_handler(message: types.Message, state: FSMContext):
    try:
        if message.text == "Отмена":
            await state.reset_state(with_data=False)
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(KeyboardButton("Посмотреть историю"), KeyboardButton("Внести изменения"))
            await message.reply("Команда отменена. Выбери новое действие или отсканируй другой QR-код",
                                reply_markup=keyboard)
        else:
            async with state.proxy() as data:
                action = message.text
                data['action'] = action
                data['current_equipment'] = current_equipment
                today = date.today()
                timestamp = today.strftime("%m/%d/%Y")

                data['timestamp'] = timestamp
                user = data.get('authorized_user')
                data['who_do'] = user
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            keyboard.add(KeyboardButton("Склад"), KeyboardButton("Офис"), KeyboardButton("Ленина"),
                         KeyboardButton("Оникс"), KeyboardButton("Билайн"), KeyboardButton("Факел"),
                         KeyboardButton("Карусель"),
                         KeyboardButton("Самбери"), KeyboardButton("Радуга"), KeyboardButton("Дикопольцева"),
                         KeyboardButton("Аврора"), KeyboardButton("Драм"), KeyboardButton("Кирова"))
            keyboard.insert(KeyboardButton("Отмена"))
            await message.reply("Выбери место установки оборудования", reply_markup=keyboard)
            await state.set_state("status")
    except Exception:
        await message.answer("Ошибка, для начала отсканиуй QR-код")


@dp.message_handler(state="status")
async def current_status(message: types.Message, state: FSMContext):
    if message.text == "Отмена":
        await state.reset_state(with_data=False)
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("Посмотреть историю"), KeyboardButton("Внести изменения"))
        await message.reply("Команда отменена. Выбери новое действие или отсканируй другой QR-код",
                            reply_markup=keyboard)
    else:
        async with state.proxy() as data:
            place = message.text
            data['place'] = place
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add(KeyboardButton("в работе"), KeyboardButton("в ремонте"), KeyboardButton("готов к работе"),
                     KeyboardButton("новое"), KeyboardButton("списано"), KeyboardButton("утилизировано"))
        keyboard.row(KeyboardButton("Отмена"))
        await message.reply("Выбери текущий статус оборудования: ", reply_markup=keyboard)
        await state.set_state("end_change")


@dp.message_handler(state="end_change")
async def end_change_handler(message: types.Message, state: FSMContext):
    if message.text == "Отмена":
        await state.reset_state(with_data=False)
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("Посмотреть историю"), KeyboardButton("Внести изменения"))
        await message.reply("Команда отменена. Выбери новое действие или отсканируй другой QR-код",
                            reply_markup=keyboard)
    else:
        async with state.proxy() as data:
            last_row = get_current_row()
            data['status'] = message.text
            equipment = data.get('current_equipment')
            action = data.get('action')
            timestamp = data.get('timestamp')
            who_do = data.get('who_do')
            place = data.get('place')
            status = data.get('status')
            await message.reply("Одну минуту, данные вносятся")
            # current_list = worksheet.col_values(1)
            # count = last_index_of_element(current_list, equipment)
            # count += 1
            # print(count)
            # for item in current_list:
            #     if item == equipment:
            #         new_row_values = [equipment, action, timestamp, who_do, place, status]
            #         worksheet.insert_row(new_row_values, index=count+1)
            #         break

            worksheet.update(f"A{last_row}", equipment)
            worksheet.update(f"B{last_row}", action)
            worksheet.update(f"C{last_row}", timestamp)
            worksheet.update(f"D{last_row}", who_do)
            worksheet.update(f"E{last_row}", place)
            worksheet.update(f"F{last_row}", status)
            await state.reset_state(with_data=False)
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(KeyboardButton("Посмотреть историю"), KeyboardButton("Внести изменения"))
            await message.answer("Данные внесены. Выбери новое действие или отсканируй другой QR-код",
                                 reply_markup=keyboard)


@dp.message_handler(commands='find_by_name')
async def find_equipment_by_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        authorized_user = data.get('authorized_user')
    if authorized_user:
        await message.answer("Введи SN внутренний: ")
        await state.set_state("find_sn")
    else:
        await message.answer("Ты не авторизован, воспользуйся командой /auth")


@dp.message_handler(state='find_sn')
async def find_sn(message: types.Message, state: FSMContext):
    equipment = table.worksheet("Список оборудования")
    current_data = equipment.col_values(5)
    del current_data[0]
    current_sn = message.text
    for item in current_data:
        if item == current_sn:
            await state.reset_state(with_data=False)
            global current_equipment
            current_equipment = item
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(KeyboardButton("Посмотреть историю"), KeyboardButton("Внести изменения"))
            await message.reply(f"Вы выбрали {item}. Что вы хотите с ним сделать?",
                                reply_markup=keyboard)


@dp.message_handler(commands='send_db')
async def send_db(message: types.Message):
    with open('equipment_bd.db', 'rb') as f:
        await message.answer_document(types.InputFile(f, filename='equipment_bd.db'), caption="Вот тебе бд")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
