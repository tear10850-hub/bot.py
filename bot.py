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
    welcome_text = "🤖 မင်္ဂလာပါ! Bot အသင့်ဖြစ်ပါပြီ။ ဘယ်သူပဲ ဘာပြောပြော အမြန်ဆုံး Reply ပြန်ပေးပါမယ်ခင်ဗျာ။"
    await update.message.reply_text(welcome_text)

# 💬 Group ထဲက မက်ဆေ့ဂျ်များကို ကိုင်တွယ်မည့် Function (အမြန်ဆုံးနှင့် အလွယ်ကူဆုံးပုံစံ)
async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        if not message:
            return

        # ၁။ စတစ်ကာ စစ်ဆေးခြင်း (18+ ရှောင်ရန်)
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

            # MongoDB ထဲသို့ စာသားကို အရင်သိမ်းဆည်းခြင်း
            try:
                collection.insert_one({"user_text": user_text})
            except Exception as db_err:
                logger.error(f"Database ထဲ သိမ်းရာတွင် အမှားဖြစ်သည်: {db_err}")

            # MongoDB ထဲရှိ စာအားလုံးကို ဆွဲထုတ်ခြင်း
            all_messages = [doc["user_text"] for doc in collection.find({}, {"_id": 0, "user_text": 1})]

            if all_messages:
                random_msg = random.choice(all_messages)
                
                # ⌨️ စာရိုက်နေပါသည် (Typing...) ပြခြင်း
                try:
                    await context.bot.send_chat_action(
                        chat_id=message.chat_id, 
                        action=ChatAction.TYPING
                    )
                except Exception:
                    pass
                
                # ဝင်လာတဲ့ စာတိုင်းအတွက် Reply အမြန်ဆုံး ပေးရန်
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
