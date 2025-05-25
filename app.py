from parser import parse
from parse_email import extract_email_from_notary_page
from docx_replacer import fill_doc
from gpt import extract_notary_data
from config import ADMIN_ID
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command, BaseFilter
from aiogram.types import Message, FSInputFile, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from config import BOT_TOKEN, ALLOWED_USERS
import asyncio
import os
import json
import keyboards as kb
from datetime import datetime
from utils import add_user, is_user_allowed, get_user_list, remove_user







bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


class Data(StatesGroup):
    user_folder = State()
    text = State()
    file_type = State()

class AccessRequestCallback:
    APPROVE = "approve"
    REJECT = "reject"


def is_authorized(func):
    async def wrapper(message: Message, *args, **kwargs):
        if is_user_allowed(message.from_user.id):
            return await func(message, *args, **kwargs)
        else:
            await message.answer("⛔ У вас нет доступа к этому боту.\n\nЧтобы запросить доступ, напишите \n/request")
    return wrapper


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("👋 Добро пожаловать! Пришлите PDF-файл(ы)")


@dp.message(Command("users"))
async def list_users(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    users = get_user_list()
    if not users:
        await message.answer("📭 Список пользователей пуст.")
        return

    text = "📋 <b>Список пользователей:</b>\n\n"
    for uid, info in users.items():
        name = f"{info.get('first_name', '')} {info.get('last_name', '')}".strip()
        username = f"@{info.get('username')}" if info.get('username') else "—"
        text += f"• <b>{name}</b> {username} — <code>{uid}</code>\n/remove_{uid}\n\n"

    await message.answer(text, parse_mode="HTML")


@dp.message(F.text.startswith("/remove_"))
async def remove_user_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    user_id = int(message.text.split("_")[1])
    remove_user(user_id)
    await message.answer(f"❌ Пользователь {user_id} удалён.")
    try:
        await bot.send_message(user_id, "⚠️ Ваш доступ к боту был удалён администратором.")
    except:
        pass  # если пользователь заблокировал бота






@dp.message(Command("request"))
async def handle_request(message: Message):
    user = message.from_user
    text = (
        f"👤 Запрос на доступ к боту\n\n"
        f"ID: {user.id}\n"
        f"Имя: {user.first_name} {user.last_name or ''}\n"
        f"Юзернейм: @{user.username or 'нет'}\n\n"
        f"Ниже кнопки для одобрения или отказа:"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Одобрить",
                callback_data=f"{AccessRequestCallback.APPROVE}:{user.id}"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"{AccessRequestCallback.REJECT}:{user.id}"
            ),
        ]
    ])
    await bot.send_message(ADMIN_ID, text, reply_markup=keyboard)
    await message.answer("📩 Запрос отправлен администратору. Ожидайте одобрения.")





@dp.callback_query(F.data.startswith((AccessRequestCallback.APPROVE, AccessRequestCallback.REJECT)))
async def process_access_request_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ У вас нет прав для этого действия.", show_alert=True)
        return

    action, user_id_str = callback.data.split(":")
    user_id = int(user_id_str)

    if action == AccessRequestCallback.APPROVE:
        try:
            chat_member = await bot.get_chat_member(chat_id=user_id, user_id=user_id)
            user = chat_member.user
            add_user(
                user_id,
                first_name=user.first_name or "",
                last_name=user.last_name or "",
                username=user.username or ""
            )
            await callback.message.edit_text(f"✅ Пользователь {user_id} одобрен.")
            await bot.send_message(user_id, "🎉 Ваш доступ к боту одобрен. Можете начать работу!")
        except Exception as e:
            await callback.message.answer(f"Ошибка при одобрении: {e}")

    elif action == AccessRequestCallback.REJECT:
        await callback.message.edit_text(f"❌ Пользователь {user_id} отклонён.")
        try:
            await bot.send_message(user_id, "❌ Ваш запрос на доступ к боту отклонён.")
        except:
            pass

    await callback.answer()  # чтобы убрать "часики" у кнопки










@dp.message(F.document)
@is_authorized
async def handle_pdf(message: Message, state: FSMContext, **kwargs):
    document = message.document

    if document.mime_type != "application/pdf":
        await message.answer("❌ Пожалуйста, отправьте PDF-файл(ы)")
        return

    user_folder = f"temp/{message.from_user.id}"
    os.makedirs(user_folder, exist_ok=True)

    # Удаляем старые файлы в папке
    for f in os.listdir(user_folder):
        file_path = os.path.join(user_folder, f)
        if os.path.isfile(file_path):
            os.remove(file_path)


    file_path = f"{user_folder}/{document.file_name}"



    file = await bot.get_file(document.file_id)
    await bot.download_file(file.file_path, destination=file_path)

    await state.update_data(user_folder=user_folder)
    await state.set_state(Data.file_type)

    await message.answer("Выберите тип файла", reply_markup=kb.select_file_type)

@dp.message(Data.file_type)
async def handle_file_type(message: Message, state: FSMContext):
    if message.text not in ["Айсоип", "Енис"]:
        await message.answer("Нет такого варианта", reply_markup=ReplyKeyboardRemove())
        return
    
    await state.update_data(file_type = message.text)
    await state.set_state(Data.text)

    await message.answer("Введите данные о клиенте", reply_markup=ReplyKeyboardRemove())



@dp.message(Data.text)
async def handle_text(message: Message, state: FSMContext):

    # try:
    await state.update_data(text = message.text)

    data = await state.get_data()
    await state.clear()

    user_data = extract_notary_data(data["text"])
    
    date_notification = user_data["date_notification"]
    if date_notification == "сегодня":
        date_notification = datetime.today().strftime("%d.%m.%Y")
    

    pdf_files = [f for f in os.listdir(data["user_folder"]) if f.lower().endswith(".pdf")]

    for filename in pdf_files:
        try:
            full_path = os.path.join(data["user_folder"], filename)
            file_data = parse(full_path)
            

            email = extract_email_from_notary_page(file_data["ФИО нотариуса"])

            if email == "Деятельность прекращена!":
                await message.answer(f"ФИО: {file_data['ФИО нотариуса']}. Деятельность прекращена!")
            elif email:
                pass  # всё ок, email найден
            else:
                await message.answer(f"Почта нотариуса не найдена. ФИО: {file_data['ФИО нотариуса']}")


            

            replacements = {
                "ФИО_нотариуса": file_data["ФИО нотариуса"],
                "Лицензия_нотариуса": file_data["Лицензия нотариуса"],
                "Почта_нотариуса": email,
                "ФИО_заёмщика": file_data["ФИО заёмщика"],
                "ИИН": file_data["ИИН"],
                "Адрес": user_data["address"],
                "Телефон": user_data["phone"],
                "Почта_клиента": user_data["email"],
                "Уникальный_номер": file_data["Уникальный номер"],
                "Дата_составления": file_data["Дата составления"],
                "Юр_лицо": file_data["Юр. лицо"],
                "Итого_к_взысканию": file_data["Итого к взысканию"],
                "Юр_лицо_с_представителем": file_data["Юр. лицо с представителем/руководителем"],
                "БИН": file_data["БИН"],
                "Адрес_компании": file_data["Адрес компании"],
                "Сумма_долга": file_data["Сумма долга"],
                "Сумма_расходов": file_data["Сумма расходов"],
                "ФИО_заёмщика_инициалы": file_data["ФИО заёмщика (инициалы)"],
                "Дата_уведомления": date_notification,
                "Дата_сегодня": datetime.today().strftime("%d.%m.%Y"),
                "получил": "получил" if user_data["isMale"] == True else "получила",
                "согласен": "согласен" if user_data["isMale"] == True else "согласна"
            }

            if data["file_type"] == "Айсоип":
                if file_data["Тип юр. лица"] == "Акционерное общество":
                    fill_doc("templates/aisoip/bvu.docx", data["user_folder"] + "/output.docx", replacements)
                    
                elif file_data["Тип юр. лица"] == "Товарищество с ограниченной ответственностью":
                    fill_doc("templates/aisoip/mfo.docx", data["user_folder"] + "/output.docx", replacements)
                    

            elif data["file_type"] == "Енис":
                if file_data["Тип юр. лица"] == "Акционерное общество":
                    fill_doc("templates/enis/bvu.docx", data["user_folder"] + "/output.docx", replacements)
                    
                elif file_data["Тип юр. лица"] == "Товарищество с ограниченной ответственностью":
                    fill_doc("templates/enis/mfo.docx", data["user_folder"] + "/output.docx", replacements)
                    

            original_file = FSInputFile(full_path, filename=filename)
            generated_file = FSInputFile(data["user_folder"] + "/output.docx", filename=file_data["ФИО заёмщика (инициалы)"] + " " + file_data["Название компании"] + ".docx")

            await bot.send_document("-4628190626", original_file, caption=data["text"])
            await message.answer_document(original_file, caption="📄 Оригинальный PDF")
            await message.answer_document(generated_file, caption="📝 Сгенерированный документ")
            await message.answer("🔻🔻🔻🔻🔻🔻🔻🔻🔻🔻🔻🔻🔻")
        except Exception as e:
            await message.answer(f"⚠️ Ошибка при обработке файла {filename}:\n{str(e)}")
    # except Exception as e:
    #     await message.answer(f"❌ Произошла ошибка:\n{str(e)}")
    








async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())




























