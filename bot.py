import logging
import os
import random
import threading
import re
import requests
from fastapi import FastAPI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters
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
HF_API_KEY = os.getenv("HF_API_KEY")
PORT = int(os.getenv("PORT", 10000))

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN ကို Environment Variable ထဲတွင် မတွေ့ရပါ။")
if not MONGO_URI:
    logger.error("MONGO_URI ကို Environment Variable ထဲတွင် မတွေ့ရပါ။")

BLOCKED_EMOJIS = ["🍆", "🍑", "💦", "🔞"]
OWNER_ID = 7771663458  # ⚠️ သင့်ရဲ့ Telegram ID
CHANNEL_URL = "https://t.me/BOTUAPTE"

# Hugging Face Inference API Model များ
AVAILABLE_MODELS = {
    "llama": {
        "name": "Meta Llama 3 8B",
        "url": "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
    },
    "mistral": {
        "name": "Mistral 7B Instruct",
        "url": "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    },
    "qwen": {
        "name": "Qwen 2.5 7B Instruct",
        "url": "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"
    }
}

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

# လက်ရှိ သုံးနေသော AI Model ကို ရယူရန်
def get_current_model_key():
    try:
        setting = settings_collection.find_one({"setting_name": "active_ai_model"})
        if setting and "model_key" in setting:
            return setting["model_key"]
    except Exception:
        pass
    return "llama"

# 🚀 1. /start ဝင်လာပါက မူလအချက်အလက်များကို အပေါ်တွင်ပြပြီး အောက်ခြေခလုတ်များ တပ်ဆင်ပေးခြင်း
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
                f"📝 **Bio:** {bio}\n\n"
                f"👇 အောက်ပါခလုတ်များကို အသုံးပြု၍ ID များ ကြည့်ရှုနိုင်ပါသည်။"
            )

            # Bot အောက်ခြေတွင် အမြဲပေါ်နေမည့် Reply Keyboards များ
            reply_keyboard = [
                [KeyboardButton("🆔 My ID"), KeyboardButton("👥 Group ID")],
                [KeyboardButton("📢 Channel ID"), KeyboardButton("👤 User ID စစ်ရန်")]
            ]
            markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

            inline_keyboard = [[InlineKeyboardButton("📢 Channel သို့ဝင်ရန်", url=CHANNEL_URL)]]
            reply_markup = InlineKeyboardMarkup(inline_keyboard)

            saved_video = settings_collection.find_one({"setting_name": "start_video"})
            if saved_video and "file_id" in saved_video:
                await update.message.reply_video(
                    saved_video["file_id"],
                    caption=caption_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                await update.message.reply_text("👇 ID စစ်ဆေးရန် ခလုတ်များကို အသုံးပြုနိုင်ပါပြီ။", reply_markup=markup)
            else:
                await update.message.reply_text(
                    caption_text,
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
    except Exception as e:
        logger.error(f"Start Command Error: {e}")

# 🆔 အောက်ခြေခလုတ်များဖြင့် ID ကြည့်ရှုခြင်းစနစ်
async def handle_keyboard_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat = update.effective_chat
    user = update.effective_user

    if text == "🆔 My ID":
        await update.message.reply_text(f"👤 သင့်ရဲ့ Telegram ID မှာ: `{user.id}` ဖြစ်ပါတယ်။", parse_mode="Markdown")
    elif text == "👥 Group ID":
        if chat.type in ["group", "supergroup"]:
            await update.message.reply_text(f"👥 ဤ Group ရဲ့ ID မှာ: `{chat.id}` ဖြစ်ပါတယ်။", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ ဤခလုတ်ကို Group ထဲတွင်သာ အသုံးပြုနိုင်ပါသည်။")
    elif text == "📢 Channel ID":
        await update.message.reply_text(f"📢 Channel Link / ID: {CHANNEL_URL}", parse_mode="Markdown")
    elif text == "👤 User ID စစ်ရန်":
        await update.message.reply_text("ℹ️ သူငယ်ချင်းတစ်ယောက်၏ User ID (သို့) Profile ကို Reply ထောက်ပြီး စစ်ဆေးနိုင်ပါသည် (သို့မဟုတ် Username ပေးပို့ပါ။)")

# 🚨 Admin Tools: Ban, Mute, Unmute
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Group များတွင်သာ အသုံးပြုနိုင်ပါသည်။")
        return
    member = await chat.get_member(user.id)
    if member.status not in ["administrator", "creator"] and user.id != OWNER_ID:
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")
        return
    
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("⚠️ Ban မည့်သူ့စာကို Reply ထောက်ပြီးမှ `/ban` ဟု ပေးပို့ပါ။")
        return
    try:
        await chat.ban_member(reply.from_user.id)
        await update.message.reply_text(f"✅ အભ્યုဝင် {reply.from_user.full_name} ကို Group မှ Ban လိုက်ပါပြီ။")
    except Exception as e:
        await update.message.reply_text(f"⚠️ မအောင်မြင်ပါ: {e}")

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Group များတွင်သာ အသုံးပြုနိုင်ပါသည်။")
        return
    member = await chat.get_member(user.id)
    if member.status not in ["administrator", "creator"] and user.id != OWNER_ID:
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")
        return
    
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("⚠️ Mute မည့်သူ့စာကို Reply ထောက်ပြီးမှ `/mute` ဟု ပေးပို့ပါ။")
        return
    try:
        from telegram import ChatPermissions
        await chat.restrict_member(reply.from_user.id, permissions=ChatPermissions(can_send_messages=False))
        await update.message.reply_text(f"🔇 {reply.from_user.full_name} ကို စာမရေးနိုင်အောင် Mute လိုက်ပါပြီ။")
    except Exception as e:
        await update.message.reply_text(f"⚠️ မအောင်မြင်ပါ: {e}")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Group များတွင်သာ အသုံးပြုနိုင်ပါသည်။")
        return
    member = await chat.get_member(user.id)
    if member.status not in ["administrator", "creator"] and user.id != OWNER_ID:
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")
        return
    
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("⚠️ Unmute မည့်သူ့စာကို Reply ထောက်ပြီးမှ `/unmute` ဟု ပေးပို့ပါ။")
        return
    try:
        from telegram import ChatPermissions
        await chat.restrict_member(
            reply.from_user.id, 
            permissions=ChatPermissions(
                can_send_messages=True, can_send_media_messages=True, 
                can_send_other_messages=True, can_add_web_page_previews=True
            )
        )
        await update.message.reply_text(f"🔊 {reply.from_user.full_name} ကို Mute မှ ပြန်လည်ဖြေလွှတ်ပေးလိုက်ပါပြီ။")
    except Exception as e:
        await update.message.reply_text(f"⚠️ မအောင်မြင်ပါ: {e}")

# 🎬 TikTok Link ကို Logo မပါဘဲ ဒေါင်းလုပ်ဆွဲသည့်စနစ်
async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    tiktok_pattern = re.compile(r'https?:\/\/(?:www\.)?(?:tiktok\.com\/@[\w.-]+\/video\/|vm\.tiktok\.com\/)([\w-]+)')
    match = tiktok_pattern.search(text)
    
    if match:
        await update.message.reply_text("⏳ TikTok ဗီဒီယိုကို Watermark (Logo) မပါဘဲ ရယူနေပါပြီ...")
        try:
            api_url = f"https://tikwm.com/api/?url={text}"
            res = requests.get(api_url).json()
            
            if res.get("code") == 0:
                data = res["data"]
                video_url = data.get("play")
                title = data.get("title", "TikTok Video")
                
                if video_url:
                    await update.message.reply_video(
                        video_url, 
                        caption=f"✨ **{title}**\n📥 Watermark ကင်းစင်သော TikTok ဗီဒီယို", 
                        parse_mode="Markdown"
                    )
                else:
                    await update.message.reply_text("⚠️ TikTok ဗီဒီယို ဖိုင်လင့်ခ် ရှာမတွေ့ပါ။")
            else:
                await update.message.reply_text("⚠️ TikTok ဗီဒီယို ဒေါင်းလုပ်ဆွဲ၍ မရပါ။")
        except Exception as e:
            logger.error(f"TikTok Download Error: {e}")
            await update.message.reply_text("⚠️ TikTok ဒေါင်းလုပ်ဆွဲရာတွင် အမှားအယွင်း ရှိသွားပါသည်။")

# 🚨 ဝင်လာသော Admin ခေါ်ဆိုမှု
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
            alert_text = f"🚨 **အရေးပေါ် အသိပေးချက်!** 🚨\n\nGroup Admin များ အမြန်ဆုံး လာရောက်ကြည့်ရှုပေးကြပါရန် 📣\n\n{mentions_text}"
            await update.message.reply_text(alert_text, parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ ဤ Group တွင် Admin မတွေ့ရှိပါ။")
    except Exception as e:
        logger.error(f"Call Admins Error: {e}")

# 🎬 Video သတ်မှတ်ခြင်း Commands
async def set_start_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.message.from_user
    if user.id != OWNER_ID:
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Owner သာ အသုံးပြုနိုင်ပါသည်။")
        return
    reply_msg = update.message.reply_to_message
    if reply_msg and reply_msg.video:
        settings_collection.update_one({"setting_name": "start_video"}, {"$set": {"file_id": reply_msg.video.file_id}}, upsert=True)
        await update.message.reply_text("✅ Start Video အသစ် သတ်မှတ်ပြီးပါပြီ!")
    else:
        await update.message.reply_text("⚠️ ဗီဒီယိုကို Reply ထောက်ပြီးမှ `/startvideo` ဟု ပေးပို့ပါ။")

async def set_leave_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.message.from_user
    if user.id != OWNER_ID:
        await update.message.reply_text("⚠️ ဤအမိန့်ကို Owner သာ အသုံးပြုနိုင်ပါသည်။")
        return
    reply_msg = update.message.reply_to_message
    if reply_msg and reply_msg.video:
        settings_collection.update_one({"setting_name": "leave_video"}, {"$set": {"file_id": reply_msg.video.file_id}}, upsert=True)
        await update.message.reply_text("✅ Leave Video အသစ် သတ်မှတ်ပြီးပါပြီ!")
    else:
        await update.message.reply_text("⚠️ ဗီဒီယိုကို Reply ထောက်ပြီးမှ `/Tvideo` ဟု ပေးပို့ပါ။")

async def set_group_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("⚠️ Group ထဲတွင်သာ သုံးရပါမည်။")
        return
    member = await chat.get_member(user.id)
    if member.status not in ["administrator", "creator"] and user.id != OWNER_ID:
        await update.message.reply_text("⚠️ Admin များသာ သုံးနိုင်ပါသည်။")
        return
    reply_msg = update.message.reply_to_message
    if reply_msg and reply_msg.video:
        settings_collection.update_one({"chat_id": chat.id, "setting_name": "group_welcome_video"}, {"$set": {"file_id": reply_msg.video.file_id}}, upsert=True)
        await update.message.reply_text("✅ Group ကြိုဆိုရေးဗီဒီယို သတ်မှတ်ပြီးပါပြီ!")
    else:
        await update.message.reply_text("⚠️ ဗီဒီယိုကို Reply ထောက်ပြီးမှ `/setwelcome` ဟု ပေးပို့ပါ။")

# ⚙️ AI Settings & /ai
async def ai_setting_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.message.from_user
    if user.id != OWNER_ID:
        await update.message.reply_text("⚠️ Owner သသာ ပြောင်းနိုင်ပါသည်။")
        return
    current_key = get_current_model_key()
    current_name = AVAILABLE_MODELS.get(current_key, {}).get("name", "Unknown")
    keyboard = [
        [InlineKeyboardButton("Llama 3 8B", callback_data="model_llama")],
        [InlineKeyboardButton("Mistral 7B", callback_data="model_mistral")],
        [InlineKeyboardButton("Qwen 2.5 7B", callback_data="model_qwen")]
    ]
    await update.message.reply_text(f"🤖 လက်ရှိ AI Model: **{current_name}**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def ai_setting_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != OWNER_ID:
        return
    selected_key = query.data.replace("model_", "")
    if selected_key in AVAILABLE_MODELS:
        settings_collection.update_one({"setting_name": "active_ai_model"}, {"$set": {"model_key": selected_key}}, upsert=True)
        await query.edit_message_text(f"✅ AI Model အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ: {AVAILABLE_MODELS[selected_key]['name']}")

async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user_message = " ".join(context.args)
    if not user_message:
        await update.message.reply_text("ကျေးဇူးပြု၍ မေးခွန်းရေးပါ။ ဥပမာ - `/ai မင်္ဂလာပါ`")
        return
    if not HF_API_KEY:
        await update.message.reply_text("⚠️ HF_API_KEY မရှိပါ။")
        return
    current_key = get_current_model_key()
    hf_api_url = AVAILABLE_MODELS.get(current_key, AVAILABLE_MODELS["llama"])["url"]
    await update.message.reply_text("🤖 စဉ်းစားနေပါတယ်...")
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": f"Answer this in Burmese naturally: {user_message}", "parameters": {"max_new_tokens": 300, "return_full_text": False}}
    try:
        response = requests.post(hf_api_url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            await update.message.reply_text("⚠️ AI ဆာဗာ အလုပ်မလုပ်ပါ။")
            return
        res_json = response.json()
        ai_reply = "အချက်အလက် မရရှိပါ။"
        if isinstance(res_json, list) and len(res_json) > 0:
            ai_reply = res_json[0].get("generated_text", ai_reply)
        elif isinstance(res_json, dict):
            ai_reply = res_json.get("generated_text", ai_reply)
        await update.message.reply_text(ai_reply, reply_to_message_id=update.message.message_id)
    except Exception as e:
        logger.error(f"AI Error: {e}")
        await update.message.reply_text("ချိတ်ဆက်ရာတွင် အမှားရှိသည်။")

# 📢 Broadcast System
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or update.message.from_user.id != OWNER_ID:
        return
    reply_msg = update.message.reply_to_message
    if not reply_msg:
        await update.message.reply_text("⚠️ ကြော်ငြာမက်ဆေ့ဂျ်ကို Reply ပြီးမှ `/bcast` ပို့ပါ။")
        return
    all_chats = list(chats_collection.find({}))
    group_chats = [c for c in all_chats if c.get("type") in ["group", "supergroup"]]
    private_chats = [c for c in all_chats if c.get("type") == "private"]
    
    await update.message.reply_text("စတင် ပို့ဆောင်နေပါပြီ...")
    s_g, f_g, s_p, f_p = 0, 0, 0, 0
    for chat in group_chats:
        try:
            await context.bot.copy_message(chat_id=chat["chat_id"], from_chat_id=reply_msg.chat_id, message_id=reply_msg.message_id)
            s_g += 1
        except: 
            f_g += 1
    for chat in private_chats:
        try:
            await context.bot.copy_message(chat_id=chat["chat_id"], from_chat_id=reply_msg.chat_id, message_id=reply_msg.message_id)
            s_p += 1
        except: 
            f_p += 1
    await update.message.reply_text(f"✅ ပြီးဆုံးပါပြီ။ Groups: {s_g} ရောက်၊ PM: {s_p} ရောက်။")

# 👋 Chat Members (Welcome / Leave)
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
                welcome_setting = settings_collection.find_one({"chat_id": chat.id, "setting_name": "group_welcome_video"})
                caption = f"👋 မင်္ဂလာပါ {new_user.full_name} ရှင့်!"
                if welcome_setting and "file_id" in welcome_setting:
                    await message.reply_video(welcome_setting["file_id"], caption=caption)
                else:
                    await message.reply_text(caption)
                    
        if message.left_chat_member:
            left_user = message.left_chat_member
            if left_user.id == context.bot.id: 
                return
            leave_video = settings_collection.find_one({"setting_name": "leave_video"})
            leave_text = f"လူကြားထဲလဲမငိုချင်တော့ဘူး😔💔 [{left_user.full_name}](tg://user?id={left_user.id})"
            if leave_video and "file_id" in leave_video:
                await message.reply_video(leave_video["file_id"], caption=leave_text, parse_mode="Markdown")
            else:
                await message.reply_text(leave_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Member Error: {e}")

# 💬 Reply Bot & Message Handler
async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        if not message: 
            return
        chat = message.chat
        user = message.from_user

        chats_collection.update_one({"chat_id": chat.id}, {"$set": {"type": chat.type}}, upsert=True)

        # TikTok Link စစ်ဆေးခြင်း
        if message.text and ("tiktok.com" in message.text or "vm.tiktok.com" in message.text):
            await download_tiktok(update, context)
            return

        # အောက်ခြေခလုတ်များ နှိပ်လိုက်ပါက လုပ်ဆောင်ရန်
        if message.text and message.text in ["🆔 My ID", "👥 Group ID", "📢 Channel ID", "👤 User ID စစ်ရန်"]:
            await handle_keyboard_buttons(update, context)
            return

        if message.sticker:
            if user and user.id == OWNER_ID:
                collection.insert_one({"type": "sticker", "content": message.sticker.file_id})
            return

        if message.photo: 
            return

        if message.text:
            user_text = message.text.strip()
            if user_text.startswith("/"): 
                return
            collection.insert_one({"type": "text", "content": user_text})

            all_messages = list(collection.find({}, {"_id": 0}))
            if all_messages:
                chosen = random.choice(all_messages)
                await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
                if chosen.get("type") == "sticker":
                    await message.reply_sticker(chosen["content"], reply_to_message_id=message.message_id)
                elif chosen.get("type") == "text":
                    await message.reply_text(chosen["content"], reply_to_message_id=message.message_id)
    except Exception as e:
        logger.error(f"Message Error: {e}")

# 🌐 FastAPI
app_fastapi = FastAPI()

@app_fastapi.get("/")
def home():
    return {"status": "Bot is running!"}

def run_fastapi():
    uvicorn.run(app_fastapi, host="0.0.0.0", port=PORT)

def main():
    if not TELEGRAM_TOKEN or not MONGO_URI:
        print("❌ Token သို့မဟုတ် MongoDB URI လိုအပ်ပါသည်။")
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
    app.add_handler(CommandHandler("aisetting", ai_setting_command))
    app.add_handler(CommandHandler("bcast", broadcast_message))
    app.add_handler(CommandHandler("ai", ask_ai))
    
    app.add_handler(CallbackQueryHandler(ai_setting_callback, pattern="^model_"))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS | filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_chat_members))
    
    chat_filter = filters.TEXT | filters.Sticker.ALL
    app.add_handler(MessageHandler(chat_filter, handle_group_messages))

    logger.info("🤖 Bot သည် အောက်ခြေခလုတ်များနှင့် အပြည့်အစုံ စတင်အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()

if __name__ == "__main__":
    main()

