import logging
import os
import random
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from pymongo import MongoClient

# Logging သတ်မှတ်ခြင်း
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Render Environment Variables ထံမှ Data များကို ယူခြင်း
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN ကို Environment Variable ထဲတွင် မတွေ့ရပါ။")
if not MONGO_URI:
    logger.error("MONGO_URI ကို Environment Variable ထဲတွင် မတွေ့ရပါ။")

BLOCKED_EMOJIS = ["🍆", "🍑", "💦", "🔞"]

# 🍃 MongoDB Database သို့ ချိတ်ဆက်ခြင်း
try:
    client = MongoClient(MONGO_URI)
    db = client["telegram_bot_db"]
    collection = db["group_messages"]
    client.admin.command('ping')
    logger.info("MongoDB သို့ အောင်မြင်စွာ ချိတ်ဆက်ပြီးပါပြီ။")
except Exception as e:
    logger.error(f"MongoDB ချိတ်ဆက်ရာတွင် အမှားဖြစ်ပွားသည်: {e}")

# 🚀 Bot စတင်ချိန် သို့မဟုတ် /start ခေါ်ချိန်
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "🤖 မင်္ဂလာပါ! Bot အသင့်ဖြစ်ပါပြီ။"
    await update.message.reply_text(welcome_text)

# 💬 Group ထဲက မက်ဆေ့ဂျ်များကို ကိုင်တွယ်မည့် Function
async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        if not message:
            return

        # ၁။ စတစ်ကာ စစ်ဆေးခြင်း
        if message.sticker:
            emoji = message.sticker.emoji if message.sticker.emoji else ""
            if any(e in emoji for e in BLOCKED_EMOJIS):
                return
            return

        # ၂။ ပုံ (Photo) ဖြစ်ပါက ကျော်ရန်
        if message.photo:
            return

        # ၃။ စာသား (Text) ဖြစ်ပါက
        if message.text:
            user_text = message.text.strip()
            
            # Slash (/) ဖြင့်စသော Command များကို ကျော်ရန်
            if user_text.startswith("/"):
                return

            # MongoDB ထဲသို့ သိမ်းဆည်းခြင်း (Field နာမည်ကို text ဟု ပုံစံတစ်မျိုးတည်း သတ်မှတ်သည်)
            try:
                collection.insert_one({"text": user_text})
            except Exception as db_err:
                logger.error(f"Database ထဲ သိမ်းရာတွင် အမှားဖြစ်သည်: {db_err}")

            # MongoDB ထဲရှိ စာအားလုံးကို ဆွဲထုတ်ခြင်း
            all_messages = [doc.get("text") or doc.get("user_text") for doc in collection.find({}) if doc.get("text") or doc.get("user_text")]

            if all_messages:
                random_msg = random.choice(all_messages)
                
                try:
                    await context.bot.send_chat_action(
                        chat_id=message.chat_id, 
                        action=ChatAction.TYPING
                    )
                except Exception:
                    pass
                
                await message.reply_text(
                    random_msg, 
                    reply_to_message_id=message.message_id
                )
    except Exception as e:
        logger.error(f"Message ကိုင်တွယ်ရာတွင် Error ဖြစ်သည်: {e}")

def main():
    if not TELEGRAM_TOKEN or not MONGO_URI:
        print("❌ Bot ကို စတင်၍ မရပါ။ Environment Variables များကို စစ်ဆေးပါ။")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    
    chat_filter = filters.TEXT | filters.Sticker.ALL | filters.PHOTO
    app.add_handler(MessageHandler(chat_filter, handle_group_messages))

    logger.info("🤖 Bot သည် အမှားကင်းစင်စွာ အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()

if __name__ == "__main__":
    main()
