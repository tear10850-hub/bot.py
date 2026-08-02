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

# ⚠️ သင့်ရဲ့ (Owner ရဲ့) Telegram User ID ကို ဤနေရာတွင် ထည့်ပါ
OWNER_ID = 7771663458  # ⬅️ ဒီနေရာမှာ သင့်အမှန်တကယ် ID ကို ထည့်ပါ

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
    welcome_text = "🤖 မင်္ဂလာပါ! အဖွဲ့ဝင်တွေရဲ့ စာနဲ့ အီမုတ်တွေအပြင် Owner ပို့တဲ့ စတစ်ကာတွေကိုပါ အကုန်မှတ်ပြီး ပြန်ပြောပေးသွားပါမယ်ခင်ဗျာ။"
    await update.message.reply_text(welcome_text)

# 💬 Group ထဲက မက်ဆေ့ဂျ်များကို ကိုင်တွယ်မည့် Function
async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        if not message or not message.from_user:
            return

        user_id = message.from_user.id
        content_to_save = None

        # ၁။ စတစ်ကာ (Sticker) ဖြစ်လာခဲ့လျှင်
        if message.sticker:
            # ပို့တဲ့သူက Owner ဟုတ်မဟုတ် စစ်မယ် (Owner ဖြစ်မှသာ Sticker ကို ယူမယ်)
            if user_id == OWNER_ID:
                emoji = message.sticker.emoji if message.sticker.emoji else ""
                if not any(e in emoji for e in BLOCKED_EMOJIS):
                    content_to_save = f"[Sticker] {emoji}" if emoji else "[Sticker]"
            else:
                # Owner မဟုတ်ရင် သူတို့ပို့တဲ့ Sticker တွေကို လုံးဝမယူဘဲ ကျော်မယ်
                return

        # ၂။ ပုံ (Photo) ဖြစ်ပါက ကျော်ရန်
        elif message.photo:
            return

        # ၃။ စာသား (Text) သို့မဟုတ် အီမုတ်များ ဖြစ်ပါက (ဘယ်သူမဆို ပို့တာကို အကုန်မှတ်မယ်)
        elif message.text:
            content_to_save = message.text.strip()

        # သိမ်းဆည်းစရာ Content ရှိပါက MongoDB ထဲ ထည့်ပြီး ပြန်ဖြေမည်
        if content_to_save:
            collection.insert_one({"user_text": content_to_save})

            all_messages = list(collection.find({}, {"_id": 0, "user_text": 1}))

            if all_messages:
                random_msg = random.choice(all_messages)["user_text"]
                
                # ⌨️ စာရိုက်နေပါသည် (Typing...) ပြခြင်း
                await context.bot.send_chat_action(
                    chat_id=message.chat_id, 
                    action=ChatAction.TYPING
                )
                
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
    
    app.add_handler(CommandHandler("start", start_command))
    
    chat_filter = filters.TEXT | filters.Sticker.ALL | filters.PHOTO
    app.add_handler(MessageHandler(chat_filter, handle_group_messages))

    logger.info("🤖 Bot သည် Render ပေါ်တွင် တည်ငြိမ်စွာ စတင်အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()

if __name__ == "__main__":
    main()

