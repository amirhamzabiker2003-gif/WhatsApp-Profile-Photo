import os
import time
import requests
import telebot
import re
from flask import Flask
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# =============================
# CONFIG
# =============================
BOT_TOKEN = "8638614270:AAHXrpYgymcHV-PSuODjuJf9a8DgTByPUjs"

# =============================
# TELEGRAM BOT
# =============================
bot = telebot.TeleBot(BOT_TOKEN)

# =============================
# CHROME OPTIONS
# =============================
chrome_options = Options()

chrome_options.add_argument("--user-data-dir=./chrome-data")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

# =============================
# DRIVER
# =============================
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

# =============================
# OPEN WHATSAPP WEB
# =============================
print("Opening WhatsApp Web...")

driver.get("https://web.whatsapp.com")

print("Scan QR Code...")

# Wait for login
logged_in = False

while not logged_in:
    try:
        driver.find_element(By.ID, "pane-side")
        logged_in = True
    except:
        time.sleep(2)

print("WhatsApp Connected")

# =============================
# START COMMAND
# =============================
@bot.message_handler(commands=['start'])
def start(message):

    bot.reply_to(
        message,
        "Send WhatsApp number\n\nExample:\n8801XXXXXXXXX"
    )

# =============================
# NUMBER HANDLER
# =============================
@bot.message_handler(func=lambda m: True)
def get_profile(message):

    chat_id = message.chat.id

    try:

        number = message.text.strip()

        # Remove spaces and +
        number = re.sub(r'[^0-9]', '', number)

        if len(number) < 8:
            bot.send_message(chat_id, "Invalid Number")
            return

        print(f"Searching: {number}")

        # Open chat
        url = f"https://web.whatsapp.com/send?phone={number}"

        driver.get(url)

        time.sleep(8)

        # =============================
        # CLICK HEADER
        # =============================
        header_found = False

        possible_selectors = [
            'header',
            'div[title]',
            'span[title]'
        ]

        for selector in possible_selectors:
            try:
                el = driver.find_element(By.CSS_SELECTOR, selector)
                el.click()
                header_found = True
                break
            except:
                pass

        if not header_found:
            bot.send_message(chat_id, "Profile not accessible")
            return

        time.sleep(3)

        # =============================
        # FIND PROFILE IMAGE
        # =============================
        images = driver.find_elements(By.TAG_NAME, 'img')

        image_url = None

        for img in images:

            src = img.get_attribute('src')

            if src and 'blob:' not in src:

                if 'whatsapp' in src or 'cdn' in src:
                    image_url = src
                    break

        if not image_url:
            bot.send_message(chat_id, "Photo not found")
            return

        print("Image Found")
        print(image_url)

        # =============================
        # DOWNLOAD IMAGE
        # =============================
        response = requests.get(image_url)

        filename = f"{number}.jpg"

        with open(filename, 'wb') as f:
            f.write(response.content)

        # =============================
        # SEND TO TELEGRAM
        # =============================
        with open(filename, 'rb') as photo:
            bot.send_photo(chat_id, photo)

        os.remove(filename)

    except Exception as e:

        print(e)

        bot.send_message(
            chat_id,
            "Photo unavailable or privacy protected"
        )

# =============================
# START BOT
# =============================
print("Telegram Bot Running...")

bot.infinity_polling()
