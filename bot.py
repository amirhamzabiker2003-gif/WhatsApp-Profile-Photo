import os
import time
import requests
import telebot
import re
from flask import Flask
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# =============================
# FLASK SERVER (Keep-Alive)
# =============================
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# =============================
# CONFIG & BOT SETUP
# =============================
# আপনার টেস্টিং এপিআই টোকেন
BOT_TOKEN = "8638614270:AAHXrpYgymcHV-PSuODjuJf9a8DgTByPUjs"
bot = telebot.TeleBot(BOT_TOKEN)

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # ডিসপ্লে ছাড়া চলার জন্য
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # সেশন ধরে রাখার পাথ
    chrome_options.add_argument("--user-data-dir=/etc/chrome-data") 
    
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

driver = get_driver()

# =============================
# TELEGRAM HANDLERS
# =============================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "WhatsApp নম্বর দিন (যেমন: 8801XXXXXXXXX)")

@bot.message_handler(func=lambda m: True)
def get_profile(message):
    chat_id = message.chat.id
    number = re.sub(r'[^0-9]', '', message.text.strip())

    if len(number) < 10:
        bot.send_message(chat_id, "সঠিক নম্বর দিন।")
        return

    bot.send_message(chat_id, f"🔍 {number} এর ছবি খোঁজা হচ্ছে...")

    try:
        driver.get(f"https://web.whatsapp.com/send?phone={number}")
        
        # এলিমেন্ট লোড হওয়ার জন্য অপেক্ষা
        time.sleep(15) 

        # প্রোফাইল পিকচার এলিমেন্ট খোঁজা (48357.jpg লজিক অনুযায়ী)
        img_element = driver.find_element(By.XPATH, '//header//img')
        image_url = img_element.get_attribute('src')

        if image_url:
            img_data = requests.get(image_url).content
            filename = f"{number}.jpg"
            with open(filename, 'wb') as f:
                f.write(img_data)
            
            with open(filename, 'rb') as photo:
                bot.send_photo(chat_id, photo, caption=f"✅ {number} এর প্রোফাইল ছবি।")
            os.remove(filename)
        else:
            bot.send_message(chat_id, "❌ ছবি পাওয়া যায়নি।")

    except Exception as e:
        bot.send_message(chat_id, "⚠️ এই মুহূর্তে প্রোফাইলটি দেখা যাচ্ছে না।")

if __name__ == "__main__":
    keep_alive()  # ফ্লাস্ক স্টার্ট
    print("WhatsApp Bot is starting...")
    bot.infinity_polling()
