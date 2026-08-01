import logging
import os
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from pymongo import MongoClient

# Logging သတ်မှတ်ခြင်း (Render Log မှာ ကြည့်လို့ကောင်းအောင်)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Render Environment Variables ထံမှ Data များကို ယူခြင်း
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# အကယ်၍ Environment Variables တွေ မပါလာရင် Error တက်မယ့်အစား သတိပေးချက်ထုတ်ရန်
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
    # Connection မှန်မမှန် စစ်ဆေးခြင်း
    client.admin.command('ping')
    logger.info("MongoDB သို့ အောင်မြင်စွာ ချိတ်ဆက်ပြီးပါပြီ။")
except Exception as e:
    logger.error(f"MongoDB ချိတ်ဆက်ရာတွင် အမှားဖြစ်ပွားသည်: {e}")

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
            
            # အက္ခရာ ၂ လုံးအောက်ဆိုရင် မမှတ်ဘူး
            if len(user_text) < 2:  
                return

            # MongoDB ထဲသို့ သိမ်းဆည်းခြင်း
            collection.insert_one({"user_text": user_text})

            # MongoDB ထဲရှိ စာများထဲမှ တစ်ခုကို ကျပန်းရွေးထုတ်ရန်
            all_messages = list(collection.find({}, {"_id": 0, "user_text": 1}))

            if all_messages:
                random_msg = random.choice(all_messages)["user_text"]
                
                # Reply ပေးခြင်း
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
    app.add_handler(MessageHandler(filters.TEXT | filters.Sticker | filters.PHOTO, handle_group_messages))

    logger.info("🤖 Bot သည် Render ပေါ်တွင် တည်ငြိမ်စွာ စတင်အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()

if __name__ == "__main__":
    main()
