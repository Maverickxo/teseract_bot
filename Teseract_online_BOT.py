from aiogram.utils import executor
from datetime import date
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import *
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from PIL import Image
import os, logging, re, sqlite3, pytesseract

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['check'])
async def start(message):
    await bot.send_message(message.chat.id, 'Все в норме, работаю !  😎 ')


@dp.message_handler(commands=['info'])
async def start(message):
    with open("output.txt", "r", encoding="utf-8") as file:
        content = file.read()
        await message.answer("Список полученых:\n\n" + content)
        print(content)


def clear_folder(folder_path):
    if os.path.exists(folder_path):
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                os.remove(file_path)
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                os.rmdir(dir_path)
        print(f"Папка {folder_path} успешно очищена.")
    else:
        print(f"Папка {folder_path} не существует.")


def fix_text(text):
    fixed_text = text.replace('0', 'О')
    return fixed_text


async def convert_images_to_png(folder_start_path, folder_out_path, message, bot):
    os.makedirs(folder_out_path, exist_ok=True)
    global converted_count
    for filename in os.listdir(folder_start_path):
        filepath = os.path.join(folder_start_path, filename)
        if os.path.isfile(filepath):
            try:
                image = Image.open(filepath)
                if image.format != 'PNG':
                    new_filepath = os.path.join(folder_out_path, os.path.splitext(filename)[0] + '.png')
                    image.save(new_filepath, 'PNG')
                    print(f"Файл {filename} успешно конвертирован в PNG.")
                    converted_count += 1
                else:
                    print(f"Файл {filename} уже в формате PNG.")
            except IOError:
                print(f"Ошибка при обработке файла {filename}.")

    print(f"Конвертация завершена. Количество сконвертированных изображений: {converted_count}.")
    await bot.send_message(message.chat.id,
                           f"Обработано: ❗️{converted_count}❗️ изображений\n⚠️Наполняю базу, ждите......!⚠️")
    converted_count = 0
    await process_images(message)


@dp.message_handler(content_types=["photo"])
async def get_photo(message):
    global saved_photos, total_photos

    total_photos += 1

    file_info = await bot.get_file(message.photo[-1].file_id)
    file_path = os.path.join("Image_in", f"{file_info.file_id}.jpg")
    await message.photo[-1].download(destination_file=file_path)

    saved_photos += 1

    if saved_photos == total_photos:
        await bot.send_message(message.chat.id,
                               f"Получено: ❗️{total_photos}❗️ изображений😎\nНачинаю обработку, ждите...!")
        saved_photos = 0
        total_photos = 0
        if saved_photos == total_photos:
            await convert_images_to_png("Image_in", "Image_out", message, bot)


log_track = []


async def process_images(message):
    try:
        os.remove('output.txt')
        print("Файл успешно удален.")
    except FileNotFoundError:
        print("Файл не найден.")
    except Exception as e:
        print(f"Ошибка при удалении файла: {e}")
    conn = sqlite3.connect(PTAH_BD)
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS tracking (id INTEGER PRIMARY KEY AUTOINCREMENT, komu TEXT, tracknum TEXT, date DATE)''')

    tracks_added = 0

    for file_name in os.listdir(folder_path):
        if file_name.endswith(('.jpg', '.png')):
            image_path = os.path.join(folder_path, file_name)
            with Image.open(image_path) as image:
                text = pytesseract.image_to_string(image, lang='rus')
                tracknum_match = re.search(r'\d{14}', text)

                if tracknum_match:
                    tracknum = tracknum_match.group()
                    komu_match = re.search(r'Кому:\s+(.+)', text)
                    if komu_match:
                        komu = fix_text(komu_match.group(1))

                        c.execute("SELECT * FROM tracking WHERE tracknum=?", (tracknum,))
                        print('Нет данных для добавления')
                        # tracks_added += 1
                        existing_record = c.fetchone()
                        if not existing_record:
                            current_date = date.today()
                            c.execute("INSERT INTO tracking (komu, tracknum, date) VALUES (?, ?, ?)",
                                      (komu, tracknum, current_date))
                            print('Данные добавлены')
                            tracks_added += 1

                    output_file = 'output.txt'
                    with open(output_file, 'a', encoding='utf-8') as file:
                        file.write(tracknum + ' ' + komu + '\n')

                    print(tracknum, " ", komu)
                    print(f"Извлеченный текст был записан в файл {output_file}.")

    await bot.send_message(message.chat.id, f"Треки добавлены.\nКоличество добавленных треков: ❗️{tracks_added}❗️")
    conn.commit()
    conn.close()
    clear_folder("Image_out")
    clear_folder("Image_in")


if __name__ == '__main__':
    executor.start_polling(dp)
