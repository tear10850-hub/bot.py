import logging
import os
import random
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from pymongo import MongoClient

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Render 24/7 Keep Alive Server
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "🤖 Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

OWNER_ID = 7771663458  

try:
    client = MongoClient(MONGO_URI)
    db = client["telegram_bot_db"]
    collection = db["group_messages"]
    chats_col = db["active_chats"]
    client.admin.command('ping')
    logger.info("MongoDB ချိတ်ဆက်မှု အောင်မြင်ပါသည်။")
except Exception as e:
    logger.error(f"MongoDB Error: {e}")

async def track_chat(update: Update):
    chat = update.effective_chat
    if chat:
        chats_col.update_one(
            {"chat_id": chat.id},
            {"$set": {"type": chat.type}},
            upsert=True
        )

async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await track_chat(update)
        message = update.message
        if not message:
            return

        chat = message.chat
        user = message.from_user
        is_owner = user and (user.id == OWNER_ID)

        # Sticker စနစ် (Member တွေပို့တာ ကျော်မယ်၊ Owner ပို့တာ သိမ်းမယ်)
        if message.sticker:
            if is_owner:
                try:
                    collection.insert_one({"type": "sticker", "content": message.sticker.file_id})
                except Exception:
                    pass
            else:
                return  

        elif message.text:
            user_text = message.text.strip()
            if user_text.startswith("/"):
                return
            
            # စာများကို သိမ်းဆည်းမည်
            try:
                collection.insert_one({"type": "text", "content": user_text})
            except Exception:
                pass

        if chat.type == "private":
            return

        # Group ထဲတွင် စာပို့သမျှကို ကျပန်းပြန်ပြောမည့်စနစ်
        if random.random() < 0.20:  
            all_items = list(collection.find({}, {"_id": 0}))
            if all_items:
                chosen = random.choice(all_items)
                try:
                    await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
                except Exception:
                    pass
                
                if chosen.get("type") == "sticker":
                    await message.reply_sticker(chosen["content"], reply_to_message_id=message.message_id)
                elif chosen.get("type") == "text":
                    await message.reply_text(chosen["content"], reply_to_message_id=message.message_id)

    except Exception as e:
        logger.error(f"Message Error: {e}")

def main():
    if not TELEGRAM_TOKEN or not MONGO_URI:
        print("Tokens missing!")
        return

    keep_alive()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    chat_filter = filters.TEXT | filters.Sticker.ALL
    app.add_handler(MessageHandler(chat_filter, handle_group_messages))

    logger.info("🤖 Bot စတင်အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()

if __name__ == "__main__":
    main()

