import logging
import os
import random
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters
from pymongo import MongoClient

# Logging သတ်မှတ်ခြင်း
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 🌐 Render Free Tier မှာ Bot မရပ်သွားစေရန် Flask Web Server တည်ဆောက်ခြင်း
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "🤖 @Cupi677Bot is alive and running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# Render Environment Variables ထံမှ Data များကို ယူခြင်း
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN ကို Environment Variable ထဲတွင် မတွေ့ရပါ။")
if not MONGO_URI:
    logger.error("MONGO_URI ကို Environment Variable ထဲတွင် မတွေ့ရပါ။")

OWNER_ID = 7771663458  # ⚠️ သင့်ရဲ့ Telegram ID
CHANNEL_LINK = "https://t.me/BOTUAPTE"  # ⚠️ သတ်မှတ်ထားသော Channel Link
GROUP_ADD_LINK = "https://t.me/Cupi677Bot?startgroup=true"  # ⚠️ @Cupi677Bot ဖြင့် Group ထဲထည့်ရန် Link

BLOCKED_EMOJIS = ["🍆", "🍑", "💦", "🔞"]
RANDOM_EMOJIS = ["❤️", "🥺", "🔥", "🤭", "✨", "💔", "😘", "🥰", "👀"]

# 🍃 MongoDB Database သို့ ချိတ်ဆက်ခြင်း
try:
    client = MongoClient(MONGO_URI)
    db = client["telegram_bot_db"]
    collection = db["group_messages"]
    settings_col = db["bot_settings"]
    chats_col = db["active_chats"]
    client.admin.command('ping')
    logger.info("MongoDB သို့ အောင်မြင်စွာ ချိတ်ဆက်ပြီးပါပြီ။")
except Exception as e:
    logger.error(f"MongoDB ချိတ်ဆက်ရာတွင် အမှားဖြစ်ပွားသည်: {e}")

async def track_chat(update: Update):
    chat = update.effective_chat
    if chat:
        chats_col.update_one(
            {"chat_id": chat.id},
            {"$set": {"type": chat.type}},
            upsert=True
        )

# 🚀 /start Command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await track_chat(update)
    message = update.message
    if not message:
        return

    if message.chat.type == "private":
        user = message.from_user
        name = user.first_name if user else "User"
        user_id = user.id if user else ""
        username = f"@{user.username}" if user and user.username else "မရှိပါ"

        bio = "မရှိပါ"
        try:
            chat_full = await context.bot.get_chat(user_id)
            if chat_full and chat_full.bio:
                bio = chat_full.bio
        except Exception:
            pass

        caption = f"mya history\nအမည်🤔- {name}\nId🌷: {user_id}\n@🌸: {username}\nBio🙂: {bio}\n\nBy @Cupi677Bot 🤭🤭"
        
        keyboard = [
            [InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK),
             InlineKeyboardButton("➕ Group ထဲသို့ထည့်ရန်", url=GROUP_ADD_LINK)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        setting = settings_col.find_one({"key": "start_video"})
        if setting and "file_id" in setting:
            try:
                await message.reply_video(
                    video=setting["file_id"],
                    caption=caption,
                    reply_markup=reply_markup
                )
                return
            except Exception as e:
                logger.error(f"Start Video ပို့ရာတွင် Error: {e}")

        await message.reply_text(caption, reply_markup=reply_markup)
    else:
        await message.reply_text("🤖 မင်္ဂလာပါရှင့်! မြနှင်း🤭 အသင့်ဖြစ်ပါပြီရှင့် 🌸။")

# 🧠 /ai Command (မိန်းကလေးဆန်ဆန် ချိုသာစွာ ဖြေပေးမည့် AI စနစ်)
async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    query = message.text[len("/ai"):].strip()
    if not query:
        await message.reply_text("ရှင့်... ဘာများမေးချင်လို့လဲဟင်? /ai နောက်မှာ မေးခွန်းလေး ရေးပေးပါနော် 🥺💕")
        return

    try:
        await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.TYPING)
    except Exception:
        pass

    girl_ai_response = f"ဟင်... ရှင်မေးတဲ့ '{query}' ဆိုတဲ့ မေးခွန်းလေးကိုလေ... "
    if "?" in query or "ဘယ်လို" in query or "ဘာလဲ" in query:
        girl_ai_response += "အဲ့ဒါကတော့ တွေးစရာလေးပေါ့နော်ရှင့်။ ကိုကို့အတွက်ဆိုရင်တော့ အရာရာ အကောင်းဆုံးဖြစ်အောင် လုပ်ပေးချင်တာပေါ့ရှင့် 🤭💕✨"
    else:
        girl_ai_response += "အဲ့ဒီအကြောင်းနဲ့ ပတ်သက်ပြီးလေ... နားလည်ပေးလို့ ကျေးဇူးတင်ပါတယ်ရှင့်။ ကိုကို့အတွက် အမြဲရှိနေပါတယ်။ ဘာများထပ်သိချင်သေးလဲဟင် 🌸😘"

    await message.reply_text(girl_ai_response, reply_to_message_id=message.message_id)

async def set_start_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or message.from_user.id != OWNER_ID:
        return

    reply = message.reply_to_message
    if reply and reply.video:
        file_id = reply.video.file_id
        settings_col.update_one(
            {"key": "start_video"},
            {"$set": {"file_id": file_id}},
            upsert=True
        )
        await message.reply_text("✅ Start Video ကို အောင်မြင်စွာ သတ်မှတ်ပြီးပါပြီရှင့်။")
    else:
        await message.reply_text("⚠️ ကျေးဇူးပြု၍ ဗီဒီယိုကို Reply ထောက်ပြီး /startvideo ဟု ပို့ပေးပါ။")

async def set_group_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    chat = message.chat
    user = message.from_user

    if chat.type not in ["group", "supergroup"]:
        await message.reply_text("⚠️ ဤ Command ကို Group ထဲတွင်သာ အသုံးပြုနိုင်ပါသည်။")
        return

    is_owner = (user.id == OWNER_ID)
    is_admin = False
    if not is_owner:
        try:
            member = await chat.get_member(user.id)
            if member.status in ["creator", "administrator"]:
                is_admin = True
        except Exception:
            pass

    if not (is_owner or is_admin):
        await message.reply_text("⚠️ ဤ Command ကို Group Admin များသာ အသုံးပြုနိုင်ပါသည်။")
        return

    reply = message.reply_to_message
    if reply and reply.video:
        file_id = reply.video.file_id
        settings_col.update_one(
            {"key": f"welcome_{chat.id}"},
            {"$set": {"file_id": file_id}},
            upsert=True
        )
        await message.reply_text("✅ ဤ Group အတွက် Welcome Video ကို အောင်မြင်စွာ သတ်မှတ်ပြီးပါပြီ။")
    else:
        await message.reply_text("⚠️ ကျေးဇူးပြု၍ ဗီဒီယိုကို Reply ထောက်ပြီး /swecome ဟု ပို့ပေးပါ။")

async def set_group_left(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or message.from_user.id != OWNER_ID:
        return

    reply = message.reply_to_message
    if reply and reply.video:
        file_id = reply.video.file_id
        settings_col.update_one(
            {"key": "left_video"},
            {"$set": {"file_id": file_id}},
            upsert=True
        )
        await message.reply_text("✅ လူထွက်လျှင် ပြမည့် Video ကို အောင်မြင်စွာ သတ်မှတ်ပြီးပါပြီရှင့်။")
    else:
        await message.reply_text("⚠️ ကျေးဇူးပြု၍ ဗီဒီယိုကို Reply ထောက်ပြီး /lallgp ဟု ပို့ပေးပါ။")

async def track_group_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if not message:
        return

    if message.new_chat_members:
        for user in message.new_chat_members:
            if user.id == context.bot.id:
                continue
            
            name = user.first_name if user else "User"
            user_id = user.id
            username = f"@{user.username}" if user and user.username else "မရှိပါ"

            bio = "မရှိပါ"
            try:
                chat_full = await context.bot.get_chat(user_id)
                if chat_full and chat_full.bio:
                    bio = chat_full.bio
            except Exception:
                pass

            caption = f"သုံးစွဲသူအချက်အလက်\n\nName: {name}\nId: {user_id}\n@: {username}\nBio: {bio}\nရောက်တုန်းရောက်ခိုက်\"လူလေးထည့်ပေးခဲ့နော်😉🤭\""
            
            setting = settings_col.find_one({"key": f"welcome_{chat.id}"})
            if setting and "file_id" in setting:
                try:
                    await context.bot.send_video(chat_id=chat.id, video=setting["file_id"], caption=caption)
                    continue
                except Exception:
                    pass
            
            await context.bot.send_message(chat_id=chat.id, text=caption)

    if message.left_chat_member:
        user = message.left_chat_member
        if user.id == context.bot.id:
            return

        u_name = user.first_name if user else "Member"
        u_id = user.id
        
        mention_tag = f"[{u_name} 🥺](tg://user?id={u_id})"

        left_caption = (
            f"🥀 ထွက်သွားသောသူ - {mention_tag}\n\n"
            f":အချစ်ခံချင်ရုံပါ🥀🥀\n"
            f"အပစ်ခံရမယ်လို🥺\n"
            f"ဘယ်သူကထင်မှာလဲ😔\n"
            f"ချိုသာစွာလဲညာခဲ့ဖူးတယ်\n"
            f"ပြန်လာဖို့လဲမှာခဲ့ဖူးတယ်\n"
            f"ဒီလောက်ဆိုတော်ပီလေ\n"
            f"မုသားတွေလဲမချိုတော့ဘူး\n"
            f"လူကြားထဲလဲမငိုချင်တော့ဘူး😔💔\n"
            f"နာကျင်ပါများလာရင်ကျင့်သားရသွားပါလိမ့်မယ်🥀\n"
            f"တစ်ချို့နာကျင်မှုတွေကမျက်ရည်ကျပြရတာထက်မျက်ရည်မကျအောင်ထိန်းပြီးပြုံးပြရတာမျိုး💔🥀🥀🥀🥀"
        )

        keyboard = [[InlineKeyboardButton(f"🥺 ပြန်လာခဲ့ပါဦး {u_name} 🏃‍♂️💨", url=f"tg://user?id={u_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        setting = settings_col.find_one({"key": "left_video"})
        if setting and "file_id" in setting:
            try:
                await context.bot.send_video(chat_id=chat.id, video=setting["file_id"], caption=left_caption, reply_markup=reply_markup, parse_mode="Markdown")
                return
            except Exception:
                pass
        
        await context.bot.send_message(chat_id=chat.id, text=left_caption, reply_markup=reply_markup, parse_mode="Markdown")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or message.from_user.id != OWNER_ID:
        return

    reply = message.reply_to_message
    if not reply:
        await message.reply_text("⚠️ ကျေးဇူးပြု၍ ပို့လိုသော မက်ဆေ့ဂျ်ကို Reply ထောက်ပြီး /bcast ဟု ပို့ပါ။")
        return

    all_chats = list(chats_col.find({}))
    group_count = sum(1 for c in all_chats if c.get("type") in ["group", "supergroup"])
    private_count = sum(1 for c in all_chats if c.get("type") == "private")

    status_msg = await message.reply_text(
        f"စတင်ပို့ဆောင်နေပါပီရှင့်\"by @Cupi677Bot\nGroup({group_count}) Mamber chat({private_count})\nသို့ပိုဆောင်နေပီ⏳....."
    )

    success_g = 0
    success_p = 0
    fail_g = 0
    fail_p = 0

    bcast_header = "📢📢ကြော်ငြာလာနေပါပီရှင့်🤫🤫\nဘေးဖယ်(24hrအတွင်ဖျက်မည်)\n\n"
    sent_messages = []

    for chat in all_chats:
        chat_id = chat["chat_id"]
        c_type = chat.get("type")
        try:
            sent_msg = None
            if reply.text:
                full_text = bcast_header + reply.text
                sent_msg = await context.bot.send_message(chat_id=chat_id, text=full_text)
            elif reply.caption:
                full_caption = bcast_header + reply.caption
                sent_msg = await context.bot.copy_message(chat_id=chat_id, from_chat_id=message.chat_id, message_id=reply.message_id, caption=full_caption)
            else:
                sent_msg = await context.bot.copy_message(chat_id=chat_id, from_chat_id=message.chat_id, message_id=reply.message_id)
                await context.bot.send_message(chat_id=chat_id, text=bcast_header.strip())

            if sent_msg:
                sent_messages.append((chat_id, sent_msg.message_id))

            if c_type in ["group", "supergroup"]:
                success_g += 1
            else:
                success_p += 1
        except Exception:
            if c_type in ["group", "supergroup"]:
                fail_g += 1
            else:
                fail_p += 1

    final_text = (
        f"Group({success_g}) Mamber chat({success_p})\nရောက်ပါသည့်ရှင့်⌛.....\n"
        f"စစ်ဆေးနေပါသည့်ရှင့်........🌷🌷🌷\n"
        f"Group({fail_g}) Mamber chat({fail_p})မရောက်ပါရှင့်........\n"
        f"Thank you owner........😘"
    )
    await status_msg.edit_text(final_text)

    async def delete_after_24_hours():
        await asyncio.sleep(86400)
        for c_id, m_id in sent_messages:
            try:
                await context.bot.delete_message(chat_id=c_id, message_id=m_id)
            except Exception:
                pass

    context.application.create_task(delete_after_24_hours())

# 💬 မက်ဆေ့ဂျ်များအတွက် အလိုအလျောက် React ပေးခြင်းနှင့် Sticker စစ်ဆေးခြင်း
async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await track_chat(update)
        message = update.message
        if not message:
            return

        chat = message.chat
        user = message.from_user
        is_owner = user and (user.id == OWNER_ID)

        if chat.type in ["group", "supergroup"] and user and not user.is_bot:
            try:
                chosen_emoji = random.choice(RANDOM_EMOJIS)
                await context.bot.set_message_reaction(
                    chat_id=chat.id,
                    message_id=message.message_id,
                    reaction=chosen_emoji
                )
            except Exception:
                pass

        if chat.type in ["group", "supergroup"] and not is_owner:
            text_to_check = message.text or message.caption or ""
            if "http://" in text_to_check or "https://" in text_to_check or "t.me/" in text_to_check:
                if user.is_bot:
                    async def delete_bot_ad():
                        await asyncio.sleep(120)
                        try:
                            await message.delete()
                        except Exception:
                            pass
                    context.application.create_task(delete_bot_ad())
                else:
                    try:
                        await message.delete()
                        return
                    except Exception:
                        pass

        if message.sticker:
            if is_owner:
                try:
                    collection.insert_one({"type": "sticker", "content": message.sticker.file_id})
                except Exception:
                    pass
            else:
                emoji = message.sticker.emoji if message.sticker.emoji else ""
                if any(e in emoji for e in BLOCKED_EMOJIS):
                    return

                keyboard = [
                    [
                        InlineKeyboardButton("✅ Yes (သိမ်းရန်)", callback_data=f"sticker_yes_{message.sticker.file_id}"),
                        InlineKeyboardButton("❌ No (မသိမ်းရန်)", callback_data="sticker_no")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                try:
                    sender_name = user.first_name if user else "Someone"
                    await context.bot.send_sticker(chat_id=OWNER_ID, sticker=message.sticker.file_id)
                    await context.bot.send_message(
                        chat_id=OWNER_ID, 
                        text=f"📥 Member တစ်ဦး ({sender_name}) ပို့ထားသော ဤ Sticker အသစ်ကို သိမ်းဆည်းမည်လား Owner?", 
                        reply_markup=reply_markup
                    )
                except Exception as e:
                    logger.error(f"Owner ထံ Sticker ပို့ရာတွင် Error: {e}")

        elif message.photo:
            return

        elif message.text:
            user_text = message.text.strip()
            if user_text.startswith("/"):
                return

            try:
                collection.insert_one({"type": "text", "content": user_text})
            except Exception:
                pass

        if chat.type == "private":
            return

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
        logger.error(f"Message ကိုင်တွယ်ရာတွင် Error: {e}")

# 🔘 Callback Query (Yes / No ခလုတ်နှိပ်ခြင်းကို ကိုင်တွယ်ရန်)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("sticker_yes_"):
        file_id = data.replace("sticker_yes_", "")
        try:
            collection.insert_one({"type": "sticker", "content": file_id})
            await query.edit_message_text("✅ ဤ Sticker ကို Database ထဲသို့ အောင်မြင်စွာ သိမ်းဆည်းလိုက်ပါပြီရှင့်။")
        except Exception:
            await query.edit_message_text("⚠️ သိမ်းဆည်းရာတွင် အမှားအယွင်းရှိခဲ့ပါသည်။")
    elif data == "sticker_no":
        await query.edit_message_text("❌ ဤ Sticker ကို သိမ်းဆည်းခြင်း မပြုလုပ်ပါ။")

def main():
    if not TELEGRAM_TOKEN or not MONGO_URI:
        print("❌ Bot ကို စတင်၍ မရပါ။ Environment Variables (TELEGRAM_TOKEN, MONGO_URI) များကို စစ်ဆေးပါ။")
        return

    # Render မရပ်သွားစေရန် Flask Server ကို နောက်ခံတွင် အလုပ်လုပ်စေခြင်း
    keep_alive()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ai", ai_command))
    app.add_handler(CommandHandler("startvideo", set_start_video))
    app.add_handler(CommandHandler("swecome", set_group_welcome))
    app.add_handler(CommandHandler("lallgp", set_group_left))
    app.add_handler(CommandHandler("bcast", broadcast_command))
    
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS | filters.StatusUpdate.LEFT_CHAT_MEMBER, track_group_members))
    
    chat_filter = filters.TEXT | filters.Sticker.ALL | filters.PHOTO
    app.add_handler(MessageHandler(chat_filter, handle_group_messages))
    app.add_handler(CallbackQueryHandler(button_callback))

    logger.info("🤖 @Cupi677Bot အပြည့်အစုံဖြင့် အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()

if __name__ == "__main__":
    main()

