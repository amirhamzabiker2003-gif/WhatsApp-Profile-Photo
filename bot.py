# -*- coding: utf-8 -*-
"""
WhatsApp Profile Picture Retriever Telegram Bot
Language: Python (aiogram v2) + Flask (for keeping alive on Render/Heroku)
Description: This bot generates a QR code to link a user's WhatsApp account via a local/remote gateway,
             and then allows the user to look up any phone number's WhatsApp profile picture.
"""

import os
import asyncio
import logging
import threading
import requests
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ১. লগিং এবং বেসিক কনফিগারেশন সেটআপ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ২. Flask Web Server Setup (Render বা অন্যান্য হোস্টিং সাইটে বট ২৪/৭ সচল রাখার জন্য)
app = Flask(__name__)

@app.route('/')
def home():
    return "🔥 WhatsApp DP Extractor Bot is running smoothly!"

def run_flask():
    # হোস্টিং প্ল্যাটফর্মগুলো ডাইনামিক পোর্ট অ্যাসাইন করে, ডিফল্ট হিসেবে ৫০০0 ব্যবহার করা হয়েছে
    port = int(os.environ.get("PORT", 5000))
    try:
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"Flask সার্ভার চালু করতে সমস্যা হয়েছে: {e}")

# ৩. Telegram Bot ও API কনফিগারেশন
API_TOKEN = '8638614270:AAHXrpYgymcHV-PSuODjuJf9a8DgTByPUjs'

# ব্যাকএন্ড হোয়াটসঅ্যাপ গেটওয়ে ইউআরএল (যেমন: Baileys, WA-Automate, বা নিজস্ব API সার্ভার)
# আপনি লোকালহোস্টে বা রিমোট কোনো সার্ভারে এই এপিআই গেটওয়েটি হোস্ট করতে পারেন
WA_GATEWAY_URL = os.environ.get("WA_GATEWAY_URL", "http://localhost:3000")

# বট এবং ডিসপ্যাচার অবজেক্ট তৈরি
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ৪. হোয়াটসঅ্যাপ গেটওয়ে আমাদের ব্যাকএন্ড এপিআই হ্যান্ডলিং লজিক

def get_whatsapp_qr_code(chat_id: int) -> str:
    """
    ব্যাকএন্ড হোয়াটসঅ্যাপ গেটওয়ে থেকে কিউআর কোড (QR Code) ছবির ইউআরএল নিয়ে আসে।
    """
    endpoint = f"{WA_GATEWAY_URL}/api/session/start"
    payload = {"sessionId": str(chat_id)}
    headers = {"Content-Type": "application/json"}
    
    try:
        logger.info(f"Chat ID {chat_id}-এর জন্য QR কোড রিকোয়েস্ট পাঠানো হচ্ছে...")
        response = requests.post(endpoint, json=payload, headers=headers, timeout=12)
        
        if response.status_code in [200, 201]:
            data = response.json()
            # গেটওয়ে থেকে পাঠানো QR ইমেজের সরাসরি লিঙ্ক বা ডেটা ইউআরএল রিটার্ন করবে
            return data.get("qr_image_url")
        else:
            logger.warning(f"গেটওয়ে থেকে রেসপন্স এরর এসেছে: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"হোয়াটসঅ্যাপ গেটওয়ে সার্ভারে কানেক্ট করা যাচ্ছে না: {e}")
        return None

def get_whatsapp_profile_picture(chat_id: int, target_phone: str) -> dict:
    """
    ইউজারের কানেক্টেড সেশন ব্যবহার করে নির্দিষ্ট নম্বরের প্রোফাইল পিকচার খোঁজে।
    """
    endpoint = f"{WA_GATEWAY_URL}/api/actions/get-profile-pic"
    payload = {
        "sessionId": str(chat_id),
        "targetNumber": target_phone
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        logger.info(f"Target {target_phone}-এর প্রোফাইল পিকচার খোঁজা হচ্ছে...")
        response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return {"status": "success", "url": data.get("profile_picture_url")}
        elif response.status_code == 404:
            return {"status": "error", "message": "এই নম্বরে কোনো প্রোফাইল পিকচার সেট করা নেই বা অ্যাকাউন্টটি সচল নয়।"}
        elif response.status_code == 401:
            return {"status": "unauthorized", "message": "আপনার হোয়াটসঅ্যাপ সেশনটি সক্রিয় নেই। দয়া করে আবার /connect করুন।"}
        else:
            return {"status": "error", "message": f"সার্ভার থেকে অপ্রত্যাশিত রেসপন্স এসেছে (কোড: {response.status_code})"}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"প্রোফাইল পিকচার রিট্রিভ করার সময় এরর: {e}")
        return {"status": "error", "message": "ব্যাকএন্ড সার্ভারের সাথে সংযোগ স্থাপন করা সম্ভব হয়নি।"}

# ৫. Telegram Bot কমান্ড এবং মেসেজ হ্যান্ডলারস

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    welcome_msg = (
        "👋 *হোয়াটসঅ্যাপ প্রোফাইল পিকচার ডাউনলোড ব্যবস্থাপনায় আপনাকে স্বাগতম!*\n\n"
        "এই বটটির মাধ্যমে যেকোনো হোয়াটসঅ্যাপ নম্বরের প্রোফাইল পিকচার সরাসরি আপনার টেলিগ্রামে নিয়ে আসতে পারবেন।\n\n"
        "🎯 *কীভাবে কাজ শুরু করবেন?*\n"
        "১. প্রথমে আপনার হোয়াটসঅ্যাপ অ্যাকাউন্টটি বটের সাথে লিঙ্ক করতে হবে।\n"
        "২. লিঙ্ক করার জন্য নিচে দেওয়া `/connect` কমান্ডটিতে ক্লিক করুন।\n"
        "৩. স্ক্রিনে আসা QR কোডটি আপনার ফোনের WhatsApp অ্যাপ দিয়ে স্ক্যান করুন।\n\n"
        "👉 শুরু করতে এখনই টাইপ করুন বা ক্লিক করুন: /connect"
    )
    await message.reply(welcome_msg, parse_mode="Markdown")

@dp.message_handler(commands=['connect'])
async def cmd_connect(message: types.Message):
    chat_id = message.chat.id
    status_msg = await message.answer("⏳ আপনার অ্যাকাউন্টের জন্য একটি সুরক্ষিত হোয়াটসঅ্যাপ QR কোড তৈরি করা হচ্ছে... অনুগ্রহ করে অপেক্ষা করুন।")
    
    # requests সিঙ্ক্রোনাস হওয়ায় এটিকে ব্যাকগ্রাউন্ড থ্রেড পুলে চালানো হচ্ছে যাতে বট হ্যাং না হয়
    loop = asyncio.get_event_loop()
    qr_url = await loop.run_in_executor(None, get_whatsapp_qr_code, chat_id)
    
    if qr_url:
        caption_text = (
            "📲 *আপনার হোয়াটসঅ্যাপ কিউআর কোড প্রস্তুত!*\n\n"
            "⚠️ *সংযোগ করার নিয়মাবলী:*\n"
            "১. আপনার ফোনের *WhatsApp* অ্যাপটি ওপেন করুন।\n"
            "২. ডানদিকের উপরে থাকা তিনটি ডট (Menu) বা *Settings* আইকনে যান।\n"
            "৩. *Linked Devices* (লিঙ্কড ডিভাইস) অপশনে ক্লিক করুন।\n"
            "৪. *Link a Device* বাটনে চেপে এই কিউআর কোডটি স্ক্যান করুন।\n\n"
            "💡 *নোট:* স্ক্যান সম্পন্ন হওয়ার পর আপনি যেকোনো নম্বর বটের চ্যাটে পাঠিয়ে তার প্রোফাইল পিকচার দেখতে পারবেন।"
        )
        await bot.delete_message(chat_id, status_msg.message_id)
        await bot.send_photo(chat_id=chat_id, photo=qr_url, caption=caption_text, parse_mode="Markdown")
    else:
        await status_msg.edit_text(
            "❌ দুঃখিত ভাই! এই মুহূর্তে কিউআর কোড জেনারেট করা সম্ভব হচ্ছে না।\n"
            "সম্ভাব্য কারণ: ব্যাকএন্ড গেটওয়ে ডাউন আছে অথবা কনফিগারেশন মেলেনি। কিছু সময় পর আবার চেষ্টা করুন।"
        )

@dp.message_handler()
async def handle_phone_lookup(message: types.Message):
    chat_id = message.chat.id
    phone_input = message.text.strip().replace("+", "").replace("-", "").replace(" ", "")
    
    if phone_input.isdigit() and 10 <= len(phone_input) <= 15:
        processing_msg = await message.answer(f"🔍 নম্বরটি (`{phone_input}`) হোয়াটসঅ্যাপ সার্ভারে চেক করা হচ্ছে... অনুগ্রহ করে একটু অপেক্ষা করুন।", parse_mode="Markdown")
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, get_whatsapp_profile_picture, chat_id, phone_input)
        
        if result.get("status") == "success" and result.get("url"):
            await bot.delete_message(chat_id, processing_msg.message_id)
            await bot.send_photo(
                chat_id=chat_id, 
                photo=result["url"], 
                caption=f"✅ *সাফল্য!*\n\n📱 নম্বর: `{phone_input}`\n🖼️ উপরোক্ত নম্বরের প্রোফাইল পিকচারটি নিচে দেওয়া হলো।",
                parse_mode="Markdown"
            )
        elif result.get("status") == "unauthorized":
            await processing_msg.edit_text(f"🔒 {result.get('message')}")
        else:
            await processing_msg.edit_text(f"⚠️ {result.get('message')}")
    else:
        await message.answer(
            "❌ *ভুল ইনপুট!*\n"
            "দয়া করে কান্ট্রি কোডসহ একটি সঠিক ফোন নম্বর দিন।\n"
            "যেমন: `88017XXXXXXXX` অথবা `91XXXXXXXXXX`", 
            parse_mode="Markdown"
        )

# ৬. অ্যাপ্লিকেশন এক্সিকিউশন মেইন ব্লক
if __name__ == '__main__':
    logger.info("⚡ Flask ব্যাকগ্রাউন্ড ওয়েব সার্ভার শুরু করা হচ্ছে...")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    logger.info("🤖 টেলিগ্রাম বট পোলিং (Polling) মোডে রান হচ্ছে...")
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logger.error(f"বট পোলিং চলাকালীন সমস্যা দেখা দিয়েছে: {e}")
