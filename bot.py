import logging
import os
import random
import threading
from fastapi import FastAPI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from pymongo import MongoClient
import uvicorn

# Logging သတ်မှတ်ခြင်း
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Render Environment Variables ထံမှ Data များကို ယူခြင်း
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 10000))

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN ကို Environment Variable ထဲတွင် မတွေ့ရပါ။")
if not MONGO_URI:
    logger.error("MONGO_URI ကို Environment Variable ထဲတွင် မတွေ့ရပါ။")

OWNER_ID = 7771663458  # ⚠️ သင့်ရဲ့ Telegram ID
CHANNEL_URL = "https://t.me/BOTUAPTE"

# 🍃 MongoDB Database သို့ ချိတ်ဆက်ခြင်း
try:
    client = MongoClient(MONGO_URI)
    db = client["telegram_bot_db"]
    collection = db["group_messages"]
    settings_collection = db["bot_settings"]
    chats_collection = db["all_chats"]
    client.admin.command('ping')
    logger.info("MongoDB သို့ အောင်မြင်စွာ ချိတ်ဆက်ပြီးပါပြီ။")
except Exception as e:
    logger.error(f"MongoDB ချိတ်ဆက်ရာတွင် အမှားဖြစ်ပွားသည်: {e}")

# 🚀 1. /start ဝင်လာပါက အချက်အလက်များနှင့် ဗီဒီယို၊ Channel ခလုတ်ပြမည်
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat = update.effective_chat
        user = update.effective_user
        if chat and user:
            chats_collection.update_one(
                {"chat_id": chat.id},
                {"$set": {"type": chat.type}},
                upsert=True
            )

            name = user.full_name
            user_id = user.id
            username = f"@{user.username}" if user.username else "မရှိပါ"
            
            try:
                user_profile = await context.bot.get_chat(user.id)
                bio = user_profile.bio if user_profile.bio else "မရှိပါ"
            except Exception:
                bio = "မရှိပါ"

            caption_text = (
                f"👤 **အမည်:** {name}\n"
                f"🆔 **ID:** `{user_id}`\n"
                f"🔗 **Username:** {username}\n"
                f"📝 **Bio:** {bio}"
            )

            keyboard = [[InlineKeyboardButton("📢 Channel သို့ဝင်ရန်", url=CHANNEL_URL)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            saved_video = settings_collection.find_one({"setting_name": "start_video"})
            if saved_video and "file_id" in saved_video:
                await update.message.reply_video(
                    saved_video["file_id"],
                    caption=caption_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    caption_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
    except Exception as e:
        logger.error(f"Start Command Error: {e}")

# 🚨 2. Group ထဲတွင် Admin များကို အရေးပေါ်ခေါ်ဆိုခြင်း (/admin)
async def call_admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat = update.effective_chat
        if not chat or chat.type == "private":
            if update.message:
                await update.message.reply_text("⚠️ ဤအမိန့်ကို Group များတွင်သာ အသုံးပြုနိုင်ပါသည်။")
            return

        admins = await chat.get_administrators()
        admin_mentions = []

        for admin in admins:
            if admin.user.is_bot:
                continue
            
            admin_user = admin.user
            name = admin_user.full_name
            if admin_user.username:
                admin_mentions.append(f"@{admin_user.username}")
            else:
                admin_mentions.append(f"[{name}](tg://user?id={admin_user.id})")

        if admin_mentions:
            mentions_text = " ".join(admin_mentions)
            alert_text = (
                f"🚨 **အရေးပေါ် အသိပေးချက်!** 🚨\n\n"
                f"Group Admin များ အမြန်ဆုံး လာရောက်ကြည့်ရှုပေးကြပါရန် 📣\n\n"
                f"{mentions_text}"
            )
            if update.message:
                await update.message.reply_text(alert_text, parse_mode="Markdown")
        else:
            if update.message:
                await update.message.reply_text("⚠️ ဤ Group တွင် Admin မတွေ့ရှိပါ။")
    except Exception as e:
        logger.error(f"Call Admins Error: {e}")

# 🛠️ 3. Group သီးသန့် Ban, Mute, Unmute စနစ်များ
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not chat or chat.type == "private":
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Group များတွင်သာ အသုံးပြုနိုင်ပါသည်။")
        return
    
    member = await chat.get_member(user.id)
    if member.status not in ["administrator", "creator"] and user.id != OWNER_ID:
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")
        return
    
    reply_msg = update.message.reply_to_message
    if not reply_msg:
        await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ Ban မည့်သူ့စာကို Reply ထောက်ပြီးမှ `/ban` ဟု ပေးပို့ပါ။")
        return
    
    target_user = reply_msg.from_user
    if target_user.id == context.bot.id:
        await update.message.reply_text("⚠️ ကျွန်ုပ်ကို ကျွန်ုပ် ဘန်း၍မရပါ။")
        return
    
    try:
        await chat.ban_member(target_user.id)
        await update.message.reply_text(f"✅ [{target_user.full_name}](tg://user?id={target_user.id}) ကို Group မှ အောင်မြင်စွာ Ban လိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ban Error: {e}")
        await update.message.reply_text("⚠️ Ban လုပ်ရာတွင် အမှားအယွင်းရှိသွားပါသည်။")

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not chat or chat.type == "private":
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Group များတွင်သာ အသုံးပြုနိုင်ပါသည်။")
        return
    
    member = await chat.get_member(user.id)
    if member.status not in ["administrator", "creator"] and user.id != OWNER_ID:
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")
        return
    
    reply_msg = update.message.reply_to_message
    if not reply_msg:
        await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ Mute မည့်သူ့စာကို Reply ထောက်ပြီးမှ `/mute` ဟု ပေးပို့ပါ။")
        return
    
    target_user = reply_msg.from_user
    if target_user.id == context.bot.id:
        return

    try:
        await chat.restrict_member(target_user.id, permissions=ChatPermissions(can_send_messages=False))
        await update.message.reply_text(f"🔇 [{target_user.full_name}](tg://user?id={target_user.id}) ကို စာမပို့နိုင်အောင် Mute လိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Mute Error: {e}")
        await update.message.reply_text("⚠️ Mute လုပ်ရာတွင် အမှားအယွင်းရှိသွားပါသည်။")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not chat or chat.type == "private":
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Group များတွင်သာ အသုံးပြုနိုင်ပါသည်။")
        return
    
    member = await chat.get_member(user.id)
    if member.status not in ["administrator", "creator"] and user.id != OWNER_ID:
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")
        return
    
    reply_msg = update.message.reply_to_message
    if not reply_msg:
        await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ Unmute လုပ်မည့်သူ့စာကို Reply ထောက်ပြီးမှ `/unmute` ဟု ပေးပို့ပါ။")
        return
    
    target_user = reply_msg.from_user
    try:
        await chat.restrict_member(
            target_user.id, 
            permissions=ChatPermissions(
                can_send_messages=True, 
                can_send_media_messages=True, 
                can_send_other_messages=True, 
                can_add_web_page_previews=True
            )
        )
        await update.message.reply_text(f"🔊 [{target_user.full_name}](tg://user?id={target_user.id}) ကို Unmute ပြန်လုပ်ပေးလိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Unmute Error: {e}")
        await update.message.reply_text("⚠️ Unmute လုပ်ရာတွင် အမှားအယွင်းရှိသွားပါသည်။")

# 🎬 4. ဗီဒီယိုနှင့် ကြိုဆိုရေး သတ်မှတ်ချက်များ (Owner နှင့် Group Admin သီးသန့်)
async def set_start_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.message.from_user
    if user.id != OWNER_ID:
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Owner သာ အသုံးပြုနိုင်ပါသည်။")
        return

    reply_msg = update.message.reply_to_message
    if reply_msg and reply_msg.video:
        video_file_id = reply_msg.video.file_id
        settings_collection.update_one(
            {"setting_name": "start_video"},
            {"$set": {"file_id": video_file_id}},
            upsert=True
        )
        await update.message.reply_text("✅ /start လုပ်လျှင် ပြမည့် Video အသစ်ကို အောင်မြင်စွာ သတ်မှတ်ပြီးပါပြီ!")
    else:
        await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ ဗီဒီယိုတစ်ခုကို Reply ထောက်ပြီးမှ `/startvideo` ဟု ပေးပို့ပါ။")

async def set_leave_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.message.from_user
    if user.id != OWNER_ID:
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Owner သာ အသုံးပြုနိုင်ပါသည်။")
        return

    reply_msg = update.message.reply_to_message
    if reply_msg and reply_msg.video:
        video_file_id = reply_msg.video.file_id
        settings_collection.update_one(
            {"setting_name": "leave_video"},
            {"$set": {"file_id": video_file_id}},
            upsert=True
        )
        await update.message.reply_text("✅ နှုတ်ဆက်ဗီဒီယိုအသစ်ကို အောင်မြင်စွာ သတ်မှတ်ပြီးပါပြီ!")
    else:
        await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ ဗီဒီယိုတစ်ခုကို Reply ထောက်ပြီးမှ `/Tvideo` ဟု ပေးပို့ပါ။")

async def set_group_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Group ထဲတွင်သာ အသုံးပြုရပါမည်။")
        return

    member = await chat.get_member(user.id)
    if member.status not in ["administrator", "creator"] and user.id != OWNER_ID:
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Group Admin များသာ အသုံးပြုနိုင်ပါသည်။")
        return

    reply_msg = update.message.reply_to_message
    if reply_msg and reply_msg.video:
        video_file_id = reply_msg.video.file_id
        settings_collection.update_one(
            {"chat_id": chat.id, "setting_name": "group_welcome_video"},
            {"$set": {"file_id": video_file_id}},
            upsert=True
        )
        await update.message.reply_text("✅ ဤ Group အတွက် ကြိုဆိုရေးဗီဒီယို အောင်မြင်စွာ သတ်မှတ်ပြီးပါပြီ!")
    else:
        await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ ဗီဒီယိုတစ်ခုကို Reply ထောက်ပြီးမှ `/setwelcome` ဟု ပေးပို့ပါ။")

# 📢 5. BROADCAST SYSTEM (Owner သီးသန့်လုပ်ဆောင်ချက်)
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.message.from_user
    if user.id != OWNER_ID:
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Owner သာ အသုံးပြုနိုင်ပါသည်။")
        return

    reply_msg = update.message.reply_to_message
    if not reply_msg:
        await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ ပို့လိုသော ကြော်ငြာမက်ဆေ့ဂျ်ကို Reply ပြီးမှ `/bcast` ဟု ပေးပို့ပါ။")
        return

    all_chats = list(chats_collection.find({}))
    group_chats = [c for c in all_chats if c.get("type") in ["group", "supergroup"]]
    private_chats = [c for c in all_chats if c.get("type") == "private"]

    total_groups = len(group_chats)
    total_pm = len(private_chats)

    await update.message.reply_text(
        f"စတင်ပိုဆောင်နေပါပီရှင့်🌷🌷 နတ်သားလေး\n"
        f"Group({total_groups})ခု member chat({total_pm})ခု💐🌾သို့.........\n"
        f"ပို့တဲဟာပြန်ပို့\n"
        f"ရောက်ရှိသွားပါပီရှင့်🌹🌹"
    )

    group_success, group_failed, pm_success, pm_failed = 0, 0, 0, 0

    for chat in group_chats:
        try:
            await context.bot.copy_message(chat_id=chat["chat_id"], from_chat_id=reply_msg.chat_id, message_id=reply_msg.message_id)
            group_success += 1
        except Exception:
            group_failed += 1

    for chat in private_chats:
        try:
            await context.bot.copy_message(chat_id=chat["chat_id"], from_chat_id=reply_msg.chat_id, message_id=reply_msg.message_id)
            pm_success += 1
        except Exception:
            pm_failed += 1

    result_text = (
        f"Group({total_groups})မှာ Group({group_success})ရောက်။ Group({group_failed})မရောက်ပါ🥺🥀🥀\n"
        f"Mamber caht({total_pm})မှာ caht({pm_success})ရောက်။ chat({pm_failed})မရောက်ပါရှင့်😓😓\n\n"
        f"ကျေးဇူးတင်ပါတယ် by mya🍃🍂"
    )
    await update.message.reply_text(result_text)

# 👋 6. Group ထဲသို့ လူအသစ်ဝင်လာခြင်း နှင့် ထွက်သွားခြင်းကို ကိုင်တွယ်ရန်
async def handle_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        if not message:
            return

        chat = message.effective_chat

        if message.new_chat_members:
            for new_user in message.new_chat_members:
                if new_user.id == context.bot.id:
                    continue

                name = new_user.full_name
                user_id = new_user.id
                username = f"@{new_user.username}" if new_user.username else name

                welcome_setting = settings_collection.find_one({"chat_id": chat.id, "setting_name": "group_welcome_video"})
                
                caption_text = (
                    f"👋 မင်္ဂလာပါ {name} ({username}) ရှင့်!\n"
                    f"🆔 ID: `{user_id}`\n"
                    f"ဤ Group လေးသို့ ဖိတ်ခေါ်ပါတယ်ခင်ဗျာ။"
                )

                if welcome_setting and "file_id" in welcome_setting:
                    await message.reply_video(
                        welcome_setting["file_id"],
                        caption=caption_text,
                        parse_mode="Markdown"
                    )
                else:
                    try:
                        photos = await context.bot.get_user_profile_photos(new_user.id, limit=1)
                        if photos.total_count > 0:
                            photo_file_id = photos.photos[0][0].file_id
                            await message.reply_photo(
                                photo_file_id,
                                caption=caption_text,
                                parse_mode="Markdown"
                            )
                        else:
                            await message.reply_text(caption_text, parse_mode="Markdown")
                    except Exception:
                        await message.reply_text(caption_text, parse_mode="Markdown")

        if message.left_chat_member:
            left_user = message.left_chat_member
            if left_user.id == context.bot.id:
                return

            user_id = left_user.id
            username = f"@{left_user.username}" if left_user.username else left_user.full_name

            leave_text = (
                f":အချစ်ခံချင်ရုံပါ🥀🥀\n"
                f"အပစ်ခံရမယ်လို🥺\n"
                f"ဘယ်သူကထင်မှာလဲ😔\n"
                f"ချိုသာစွာလဲညာခဲ့ဖူးတယ်\n"
                f"ပြန်လာဖို့လဲမှာခဲ့ဖူးတယ်\n"
                f"ဒီလောက်ဆိုတော်ပီလေ\n"
                f"မုသားတွေလဲမချိုတော့ဘူး\n"
                f"လူကြားထဲလဲမငိုချင်တော့ဘူး😔💔\n"
                f"နာကျင်ပါများလာရင်ကျင့်သားရသွားပါလိမ့်မယ်🥀\n"
                f"တစ်ချို့နာကျင်မှုတွေကမျက်ရည်ကျပြရတာထက်မျက်ရည်မကျအောင်ထိန်းပြီးပြုံးပြရတာမျိုး💔🥀🥀🥀🥀\n"
                f"(🤕)ရေ..... [{username}](tg://user?id={user_id})"
            )

            leave_video_setting = settings_collection.find_one({"setting_name": "leave_video"})

            if leave_video_setting and "file_id" in leave_video_setting:
                await message.reply_video(
                    leave_video_setting["file_id"],
                    caption=leave_text,
                    parse_mode="Markdown"
                )
            else:
                await message.reply_text(
                    leave_text,
                    parse_mode="Markdown"
                )

    except Exception as e:
        logger.error(f"Chat Member Error: {e}")

# 💬 7. မက်ဆေ့ဂျ်များကို ကိုင်တွယ်ခြင်း (Owner ပို့သော စတစ်ကာများကို လုံးဝမစစ်ဘဲ အကုန်သိမ်းမည်)
async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        if not message:
            return

        chat = message.chat
        user = message.from_user

        chats_collection.update_one(
            {"chat_id": chat.id},
            {"$set": {"type": chat.type}},
            upsert=True
        )

        # 1. စတစ်ကာ ဖြစ်ပါက (Owner ပို့လျှင် ဘာမှမစစ်ဘဲ အကုန်သိမ်းမည်)
        if message.sticker:
            if user and user.id == OWNER_ID:
                collection.insert_one({"type": "sticker", "content": message.sticker.file_id})
            return

        # 2. ပုံ (Photo) ဖြစ်ပါက ကျော်ရန်
        if message.photo:
            return

        # 3. စာသား (Text) ဖြစ်ပါက
        if message.text:
            user_text = message.text.strip()
            if user_text.startswith("/"):
                return
                
            # စာသားများကို MongoDB ထဲ သိမ်းဆည်းခြင်း
            collection.insert_one({"type": "text", "content": user_text})

            # MongoDB ထဲရှိ သိမ်းထားသမျှ စာများ/စတစ်ကာများထဲမှ ကျပန်းရွေးထုတ်ရန်
            all_messages = list(collection.find({}, {"_id": 0}))

            if all_messages:
                chosen = random.choice(all_messages)
                
                # ⌨️ စာရိုက်နေပါသည် (Typing...) ပြခြင်း
                await context.bot.send_chat_action(
                    chat_id=message.chat_id, 
                    action=ChatAction.TYPING
                )
                
                if chosen.get("type") == "sticker":
                    await message.reply_sticker(chosen["content"], reply_to_message_id=message.message_id)
                elif chosen.get("type") == "text":
                    await message.reply_text(chosen["content"], reply_to_message_id=message.message_id)

    except Exception as e:
        logger.error(f"Message ကိုင်တွယ်ရာတွင် Error ဖြစ်သည်: {e}")

# 🌐 FastAPI (Render Port ဖွင့်ရန်အတွက်)
app_fastapi = FastAPI()

@app_fastapi.get("/")
def home():
    return {"status": "Bot is running!"}

def run_fastapi():
    uvicorn.run(app_fastapi, host="0.0.0.0", port=PORT)

def main():
    if not TELEGRAM_TOKEN or not MONGO_URI:
        print("❌ Bot ကို စတင်၍ မရပါ။ Environment Variables များကို စစ်ဆေးပါ။")
        return

    t = threading.Thread(target=run_fastapi)
    t.daemon = True
    t.start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", call_admins_command))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))
    app.add_handler(CommandHandler("startvideo", set_start_video))
    app.add_handler(CommandHandler("Tvideo", set_leave_video))
    app.add_handler(CommandHandler("setwelcome", set_group_welcome))
    app.add_handler(CommandHandler("bcast", broadcast_message))
    
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS | filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_chat_members))
    
    chat_filter = filters.TEXT | filters.Sticker.ALL | filters.PHOTO
    app.add_handler(MessageHandler(chat_filter, handle_group_messages))

    logger.info("🤖 Bot သည် အောင်မြင်စွာ အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()

if __name__ == "__main__":
    main()
