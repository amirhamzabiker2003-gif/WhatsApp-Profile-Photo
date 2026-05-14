import os
import asyncio
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ১. Flask Setup (বটকে সচল রাখার জন্য)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Alive!"

def run_flask():
    # Render বা অন্য প্ল্যাটফর্মে পোর্ট ডাইনামিক থাকে
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# ২. Telegram Bot Setup
# আপনার রিকোয়েস্ট অনুযায়ী টোকেনটি অটোমেটিক বসানো হয়েছে
API_TOKEN = '8638614270:AAHXrpYgymcHV-PSuODjuJf9a8DgTByPUjs'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("বটটি এখন Flask-এর মাধ্যমে সচল আছে! নম্বর পাঠান (যেমন: 88017XXXXXXXX)।")

@dp.message_handler()
async def handle_message(message: types.Message):
    phone = message.text.strip().replace("+", "")
    
    if phone.isdigit():
        await message.answer(f"আপনার নম্বরটি ({phone}) প্রসেস করা হচ্ছে...")
        # নোট: অ্যান্ড্রয়েডে Playwright সাপোর্ট না করায় এখানে আপনার কাস্টম স্ক্র্যাপিং লজিক বসাতে হবে
        await message.answer("সার্ভার সীমাবদ্ধতার কারণে বর্তমানে ইমেজ রিট্রিভাল আপডেট হচ্ছে।")
    else:
        await message.answer("দয়া করে সঠিক নম্বর দিন।")

# ৩. Main Execution
if __name__ == '__main__':
    # ফ্লাস্ককে আলাদা থ্রেডে চালানো যাতে বট এবং সার্ভার একসাথে চলে
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # টেলিগ্রাম বট পোলিং শুরু
    executor.start_polling(dp, skip_updates=True)
