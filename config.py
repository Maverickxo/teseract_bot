import os

TOKEN = "6221908613:AAGnOHm7_wz76vspK4Ht7uC-CfMy2I0mTjo"

PTAH_BD = '/root/bot_kraft/tracking_bot/tracking_data.db'



folder_start_path = 'images_in'
folder_out_path = 'images_out'

saved_photos = 0
total_photos = 0
converted_count = 0

folder_path = 'Image_out'

os.makedirs("Image_in", exist_ok=True)
os.makedirs("Image_out", exist_ok=True)