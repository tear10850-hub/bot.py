import logging
import random
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# MongoDB Connection with Exception Handling
MONGO_URI = os.getenv("MONGO_URI")
db = None
messages_collection = None

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client["telegram_bot_db"]
    messages_collection = db["saved_messages"]
    logging.info("MongoDB သို့ အောင်မြင်စွာ ချိတ်ဆက်ပြီးပါပြီ။")
except PyMongoError as e:
    logging.error(f"MongoDB ချိတ်ဆက်မှု အမှားအယွင်းရှိပါသည်: {e}")

# Hugging Face API Configuration
HF_API_KEY = os.getenv("HF_API_KEY")
HF_API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"

# Owner ID သတ်မှတ်ခြင်း (စတစ်ကာအတွက် သီးသန့်စစ်ရန်)
OWNER_ID = 7771663458

# --- AI COMMAND HANDLER (/ai) ---
async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_message = " ".join(context.args)
    
    if not user_message:
        await update.message.reply_text("ကျေးဇူးပြု၍ မေးလိုသည့် မေးခွန်းကို ရေးပေးပါ။ ဥပမာ - `/ai မင်္ဂလာပါ`")
        return

    if not HF_API_KEY:
        await update.message.reply_text("⚠️ API Key မရှိသေးပါ သို့မဟုတ် Render တွင် မထည့်ရသေးပါ။")
        return

    await update.message.reply_text("🤖 စဉ်းစားနေပါတယ်...")

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    prompt = f"You are a helpful assistant that is fluent in Burmese (Myanmar). Answer the following question in Burmese naturally.\n\nUser: {user_message}\nAssistant:"
    
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 500, "return_full_text": False}
    }

    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=15)
        
        if response.status_code != 200:
            await update.message.reply_text(f"⚠️ ဆာဗာဘက်မှ တုံ့ပြန်မှု မမှန်ကန်ပါ။ (Status: {response.status_code})")
            return

        res_json = response.json()
        
        ai_reply = "ပြန်လည်ဖြေကြားရန် အချက်အလက် မရရှိပါ။"
        if isinstance(res_json, list) and len(res_json) > 0:
            ai_reply = res_json[0].get("generated_text", ai_reply)
        elif isinstance(res_json, dict) and "error" in res_json:
            ai_reply = f"API Error: {res_json['error']}"

        await update.message.reply_text(ai_reply)
        
    except requests.exceptions.Timeout:
        await update.message.reply_text("⏱️ ဆာဗာမှ အချိန်အကြာကြီး တုံ့ပြန်မှုမရှိပါသဖြင့် ကျေးဇူးပြု၍ ခဏနေမှ ထပ်ကြိုးစားပါ။")
    except Exception as e:
        logging.error(f"AI Error: {e}")
        await update.message.reply_text("ချိတ်ဆက်ရာတွင် အမှားအယွင်းရှိသွားပါသည်။")

# --- MESSAGE HANDLER (Stickers & Chat Learning) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not messages_collection:
        return

    user = update.message.from_user
    chat = update.message.chat
    
    try:
        if update.message.text:
            if not update.message.text.startswith('/'):
                messages_collection.insert_one({
                    "type": "text",
                    "content": update.message.text
                })
        elif update.message.sticker:
            if user and user.id == OWNER_ID:
                messages_collection.insert_one({
                    "type": "sticker",
                    "content": update.message.sticker.file_id
                })
                logging.info("Owner ပို့သော စတစ်ကာကို သိမ်းဆည်းပြီးပါပြီ။")

        if chat.type in ["group", "supergroup"]:
            await context.bot.send_chat_action(chat_id=chat.id, action="typing")
            
            all_saved = list(messages_collection.find({}, {"_id": 0}))
            
            if all_saved:
                chosen = random.choice(all_saved)
                if chosen.get("type") == "text":
                    await update.message.reply_text(chosen["content"])
                elif chosen.get("type") == "sticker":
                    await update.message.reply_sticker(chosen["content"])
                    
    except PyMongoError as e:
        logging.error(f"Database Operation Error: {e}")
    except Exception as e:
        logging.error(f"Message Handling Error: {e}")

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logging.error("Error: TELEGRAM_BOT_TOKEN not found!")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    # Handlers များ ချိတ်ဆက်ခြင်း (Filter Error ကင်းဝေးစေရန် စနစ်တကျ ပြင်ဆင်ထားသည်)
    application.add_handler(CommandHandler("ai", ask_ai))
    application.add_handler(MessageHandler(filters.TEXT | filters.Sticker.ALL, handle_message))

    logging.info("Bot is running securely and stably...")
    application.run_polling()

if __name__ == '__main__':
    main()

