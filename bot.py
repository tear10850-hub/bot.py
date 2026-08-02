import logging
import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters, ChatMemberHandler
from pymongo import MongoClient

# Logging သတ်မှတ်ခြင်း
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Render Environment Variables ထံမှ Data များကို ယူခြင်း
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # Bot Owner ရဲ့ Telegram User ID ထည့်ရန်

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
    settings_collection = db["bot_settings"]
    client.admin.command('ping')
    logger.info("MongoDB သို့ အောင်မြင်စွာ ချိတ်ဆက်ပြီးပါပြီ။")
except Exception as e:
    logger.error(f"MongoDB ချိတ်ဆက်ရာတွင် အမှားဖြစ်ပွားသည်: {e}")

# 🚀 Bot စတင်ချိန် သို့မဟုတ် /start ခေါ်ချိန် (Private Chat တွင် /start video ဖြင့်သတ်မှတ်ထားသည်များကိုပြရန်)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == "private":
        start_video_data = settings_collection.find_one({"type": "start_video"})
        
        try:
            full_user = await context.bot.get_chat(user.id)
            bio = full_user.bio if full_user.bio else "မရှိပါ"
        except Exception:
            bio = "မရှိပါ"

        user_info_text = (
            f"သုံးစွဲသူအချက်အလက်များ.....⏳\n"
            f"Name🎋- {user.full_name}\n"
            f"Id🍃- {user.id}\n"
            f"@🍂- @{user.username if user.username else 'မရှိပါ'}\n"
            f"Bio🍁- {bio}"
        )

        keyboard = [
            [InlineKeyboardButton("Support", url="https://t.me/BOTUAPTE")],
            [InlineKeyboardButton("Group သို့ထည့်ရန်", url="https://t.me/Cupi677Bot")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if start_video_data and "file_id" in start_video_data:
            await update.message.reply_video(
                video=start_video_data["file_id"],
                caption=f"{start_video_data.get('caption', '')}\n\n{user_info_text}",
                reply_markup=reply_markup
            )
        else:
            welcome_text = f"🤖 မင်္ဂလာပါ! ကျွန်တော် Bot စတင် အလုပ်လုပ်နေပါပြီခင်ဗျာ။\n\n{user_info_text}"
            await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text("🤖 မင်္ဂလာပါ! ကျွန်တော် Bot စတင် အလုပ်လုပ်နေပါပြီခင်ဗျာ။")

# 📌 Owner မှ /startvideo, /swecom, /allgpleave သတ်မှတ်ခြင်းနှင့် /bcast ပြုလုပ်ခြင်း
async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.reply_to_message:
        return
    
    command = message.text.split()[0]
    replied_msg = message.reply_to_message

    if command == "/startvideo":
        if replied_msg.video:
            settings_collection.update_one(
                {"type": "start_video"},
                {"$set": {"file_id": replied_msg.video.file_id, "caption": replied_msg.caption or ""}},
                upsert=True
            )
            await message.reply_text("✅ Start Video ကို အောင်မြင်စွာ သတ်မှတ်ပြီးပါပြီ။")
        else:
            await message.reply_text("❌ ကျေးဇူးပြု၍ Video ကို Reply ပေးပြီးမှ /startvideo ဟု ရိုက်ပါ။")

    elif command == "/swecom":
        if replied_msg.video:
            chat_id = message.chat_id
            settings_collection.update_one(
                {"type": "welcome_video", "chat_id": chat_id},
                {"$set": {"file_id": replied_msg.video.file_id, "caption": replied_msg.caption or ""}},
                upsert=True
            )
            await message.reply_text("✅ ဤ Group အတွက် Member အသစ်ကြိုဆိုမည့် Video ကို သတ်မှတ်ပြီးပါပြီ။")
        else:
            await message.reply_text("❌ ကျေးဇူးပြု၍ Video ကို Reply ပေးပြီးမှ /swecom ဟု ရိုက်ပါ။")

    elif command == "/allgpleave":
        if replied_msg.video:
            chat_id = message.chat_id
            settings_collection.update_one(
                {"type": "leave_video", "chat_id": chat_id},
                {"$set": {"file_id": replied_msg.video.file_id, "caption": replied_msg.caption or ""}},
                upsert=True
            )
            await message.reply_text("✅ ဤ Group အတွက် Member ထွက်သွားစဉ်ပြမည့် Video ကို သတ်မှတ်ပြီးပါပြီ။")
        else:
            await message.reply_text("❌ ကျေးဇူးပြု၍ Video ကို Reply ပေးပြီးမှ /allgpleave ဟု ရိုက်ပါ။")

    elif command == "/bcast":
        success_gp = 0
        fail_gp = 0
        success_pm = 0
        fail_pm = 0
        
        all_chats = settings_collection.find({"type": "bot_chat_member"})
        
        for chat_entry in all_chats:
            c_id = chat_entry.get("chat_id")
            c_type = chat_entry.get("chat_type")
            try:
                if replied_msg.photo:
                    await context.bot.send_photo(chat_id=c_id, photo=replied_msg.photo[-1].file_id, caption=replied_msg.caption)
                elif replied_msg.video:
                    await context.bot.send_video(chat_id=c_id, video=replied_msg.video.file_id, caption=replied_msg.caption)
                elif replied_msg.text:
                    await context.bot.send_message(chat_id=c_id, text=replied_msg.text)
                elif replied_msg.sticker:
                    await context.bot.send_sticker(chat_id=c_id, sticker=replied_msg.sticker.file_id)
                
                if c_type in ["group", "supergroup"]:
                    success_gp += 1
                else:
                    success_pm += 1
            except Exception:
                if c_type in ["group", "supergroup"]:
                    fail_gp += 1
                else:
                    fail_pm += 1

        bcast_report = (
            f"စတင်ပို့ဆောင်နေပါပီ 🍃ရှင့်နတ်သားလေး 🌷\n"
            f"⏳.....\n"
            f"Group({success_gp + fail_gp}) mamber chat({success_pm + fail_pm})\n"
            f"({replied_msg.text[:20] if replied_msg.text else 'Media Content'}...)\n"
            f"Group 🌷({success_gp})ရောက် Mamber chat({success_pm})ရောက် 🌷\n"
            f"Group({fail_gp}) mamber chat({fail_pm})\n"
            f"မရောက်ပါရှင့်။ 🌷🌷🌷\n"
            f"ကျေးဇူးတင်ပါသည်ရှင့်။"
        )
        await message.reply_text(bcast_report)

# 👥 Member အသစ်ဝင်လာခြင်းနှင့် ထွက်သွားခြင်းကို ကိုင်တွယ်ရန်
async def handle_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    if not result:
        return
    
    chat = update.effective_chat
    new_member = result.new_chat_member.user
    old_member = result.old_chat_member.user
    
    # ၁။ Member အသစ်ဝင်လာခြင်း
    if result.new_chat_member.status in ["member", "creator", "administrator"] and result.old_chat_member.status in ["left", "banned"]:
        welcome_v = settings_collection.find_one({"type": "welcome_video", "chat_id": chat.id})
        if welcome_v and "file_id" in welcome_v:
            poem_welcome = (
                f"{welcome_v.get('caption', '')}\n\n"
                f"နွေကိုချစ်ရင်💐ပူရတယ်\n"
                f"မိုးခြိမ်းရင် ကြောက်တက်တဲသူကို\n"
                f"သတိရတယ်😪\n"
                f"ဆောင်းမှာအေးလို့...သူနှင့်အတူဆောက်ခဲ့တဲ့\n"
                f"အိမ်လေးကိုသတိရမိတယ်။မိသာစုအိမ်မက်လေး😰🥀🥀\n\n"
                f"လူသစ်အချက်အလက်များ...⌛\n"
                f"Name- {new_member.full_name}\n"
                f"Id- {new_member.id}\n"
                f"@- @{new_member.username if new_member.username else 'မရှိပါ'}\n"
                f"🌷🌷🌷"
            )
            await context.bot.send_video(chat_id=chat.id, video=welcome_v["file_id"], caption=poem_welcome)

    # ၂။ Member ထွက်သွားခြင်း
    elif result.new_chat_member.status == "left":
        leave_v = settings_collection.find_one({"type": "leave_video", "chat_id": chat.id})
        if leave_v and "file_id" in leave_v:
            poem_leave = (
                f"{leave_v.get('caption', '')}\n\n"
                f"💞အချစ်ခံချင်ရုံပါ\n"
                f" အပစ်ခံရမယ်လို့🥺\n"
                f"ဘယ်သူကထင်မှာလည်း....🤥\n"
                f"ချိုသာစွာလဲညာဖူးခဲ့တယ်။\n"
                f"ပြန်လာဖို့လဲမှာခဲ့ဘူးတယ်😔\n"
                f"မုသားတွေလည်းမချိုတော့ဘူး\n"
                f"လူကြားထဲလည်းမငိုချင်တော့ဘူး💔💔\n"
                f"နာကျင်ပါများလာရင်..ကျင့်သား\n"
                f"ရသွားပါလိမ့်မယ်။\n"
                f"တစ်ချို့နာကျင်မှုတွေက😪မျက်ရည်ကျရတာထက်🍁💔\n"
                f"မျက်ရည်မကျအောင် ထိန်းပီပြုံးပြနေရတာမျိုး🎋🥀\n"
                f"   အဆင်ပြေပါစေ(🥺)ရေ......"
            )
            keyboard = [[InlineKeyboardButton("🥺 ထွက်သွားသူ Profile", url=f"tg://user?id={old_member.id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_video(
                chat_id=chat.id, 
                video=leave_v["file_id"], 
                caption=poem_leave,
                reply_markup=reply_markup
            )

# 💬 Group နှင့် Private Bot Chat ထဲက မက်ဆေ့ဂျ်များကို ကိုင်တွယ်မည့် Function
async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        if not message:
            return

        chat = message.chat
        user = message.from_user

        settings_collection.update_one(
            {"chat_id": chat.id},
            {"$set": {"chat_type": chat.type}},
            upsert=True
        )

        if chat.type == "private":
            if message.sticker and user.id == OWNER_ID:
                settings_collection.update_one(
                    {"type": "owner_sticker"},
                    {"$set": {"file_id": message.sticker.file_id, "emoji": message.sticker.emoji or "😊"}},
                    upsert=True
                )
                await message.reply_text("📌 စတစ်ကာကို မှတ်သားပြီးပါပြီ။")
                return

            if user.id != OWNER_ID:
                owner_sticker = settings_collection.find_one({"type": "owner_sticker"})
                if message.text:
                    emoji_choice = owner_sticker.get("emoji", "❤️") if owner_sticker else "❤️"
                    try:
                        await message.reply_text(emoji_choice)
                    except Exception:
                        pass
                elif owner_sticker and owner_sticker.get("file_id"):
                    await message.reply_sticker(sticker=owner_sticker["file_id"], reply_to_message_id=message.message_id)
                return

        if chat.type in ["group", "supergroup"]:
            if message.sticker:
                emoji = message.sticker.emoji if message.sticker.emoji else ""
                if any(e in emoji for e in BLOCKED_EMOJIS):
                    return
                return

            if message.photo:
                return

            if message.text:
                user_text = message.text.strip()
                collection.insert_one({"user_text": user_text})
                all_messages = list(collection.find({}, {"_id": 0, "user_text": 1}))

                if all_messages:
                    random_msg = random.choice(all_messages)["user_text"]
                    await context.bot.send_chat_action(
                        chat_id=message.chat_id, 
                        action=ChatAction.TYPING
                    )
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
    app.add_handler(CommandHandler(["startvideo", "swecom", "allgpleave", "bcast"], admin_commands))
    app.add_handler(ChatMemberHandler(handle_chat_members, ChatMemberHandler.CHAT_MEMBER))

    chat_filter = filters.TEXT | filters.Sticker.ALL | filters.PHOTO
    app.add_handler(MessageHandler(chat_filter, handle_group_messages))

    logger.info("🤖 Bot သည် Render ပေါ်တွင် တည်ငြိမ်စွာ စတင်အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()

if __name__ == "__main__":
    main()

