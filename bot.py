import os
import re
import time
import threading
import requests
import telebot

from flask import Flask

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# =====================================
# FLASK APP
# =====================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running"

# =====================================
# CONFIG
# =====================================
BOT_TOKEN = os.getenv("8638614270:AAHXrpYgymcHV-PSuODjuJf9a8DgTByPUjs")

# =====================================
# TELEGRAM BOT
# =====================================
bot = telebot.TeleBot(BOT_TOKEN)

# =====================================
# CHROME OPTIONS
# =====================================
chrome_options = Options()

chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--user-data-dir=/tmp/chrome-data")

# =====================================
# DRIVER
# =====================================
print("Starting Chrome...")

try:

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

except Exception as e:

    print("Chrome Error:")
    print(e)
    exit()

# =====================================
# OPEN WHATSAPP WEB
# =====================================
print("Opening WhatsApp Web...")

driver.get("https://web.whatsapp.com")

print("Scan QR Manually From Browser Session")

# =====================================
# START COMMAND
# =====================================
@bot.message_handler(commands=['start'])
def start(message):

    bot.reply_to(
        message,
        "Send WhatsApp Number

Example:
8801XXXXXXXXX"
    )

# =====================================
# NUMBER HANDLER
# =====================================
@bot.message_handler(func=lambda m: True)
def get_profile(message):

    chat_id = message.chat.id

    try:

        number = message.text.strip()

        number = re.sub(r'[^0-9]', '', number)

        if len(number) < 8:
            bot.send_message(chat_id, "Invalid Number")
            return

        url = f"https://web.whatsapp.com/send?phone={number}"

        driver.get(url)

        time.sleep(8)

        images = driver.find_elements(By.TAG_NAME, 'img')

        image_url = None

        for img in images:

            src = img.get_attribute('src')

            if src and 'cdn' in src:
                image_url = src
                break

        if not image_url:

            bot.send_message(
                chat_id,
                "Photo not found or privacy protected"
            )

            return

        response = requests.get(image_url)

        filename = f"{number}.jpg"

        with open(filename, 'wb') as f:
            f.write(response.content)

        with open(filename, 'rb') as photo:
            bot.send_photo(chat_id, photo)

        os.remove(filename)

    except Exception as e:

        print(e)

        bot.send_message(
            chat_id,
            "Error fetching photo"
        )

# =====================================
# BOT THREAD
# =====================================
def run_bot():
    bot.infinity_polling()

threading.Thread(target=run_bot).start()

# =====================================
# RUN FLASK
# =====================================
if __name__ == '__main__':

    port = int(os.environ.get("PORT", 10000))

    app.run(host='0.0.0.0', port=port)
