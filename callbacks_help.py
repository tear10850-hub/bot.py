from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from database import db
from helpers import is_group_admin
from keyboards import get_admin_help_keyboard, get_public_help_keyboard

def help_callback(update, context):
    try:
        query = update.callback_query
        query.answer()
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        data = query.data
        is_owner = (user_id == Config.OWNER_ID)
        is_admin = is_group_admin(context.bot, chat_id, user_id)
        
        if data == "help_mya":
            text = Config.HELP_MYA_TEXT + "\n\n"
            keyboard = []
            if is_owner:
                keyboard.append([InlineKeyboardButton("👑 Owner Help", callback_data="help_owner")])
            keyboard.append([InlineKeyboardButton("📢 Channel", url=Config.CHANNEL_LINK)])
            keyboard.append([InlineKeyboardButton("🛡️ Admin Help", callback_data="help_admin")])
            keyboard.append([InlineKeyboardButton("❌ ပိတ်ရန်", callback_data="help_close")])
            query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
        
        elif data == "help_admin":
            query.message.edit_text("🛡️ **Admin Help**\n\nGroup Admin တွေအတွက် သီးသန့်လမ်းညွှန်ပါ။", reply_markup=get_admin_help_keyboard())
            return
        
        elif data == "admin_ban":
            text = "🔨 **Ban / Mute / Unmute**\n\n📌 **သုံးနည်း**\nUser ကို reply ထောက်ပြီး command ရိုက်ပါ။\n\n📌 **Commands**\n• `/ban [အကြောင်း]` - Ban\n• `/unban` - Unban\n• `/mute [မိနစ်]` - Mute\n• `/unmute` - Unmute"
        elif data == "admin_welcome":
            text = "🎬 **Welcome Video**\n\n📌 **Commands**\n• `/setwelcomevideo` (Reply) - သတ်မှတ်\n• `/deletewelcomevideo` - ဖျက်"
        elif data == "admin_link":
            text = "🔗 **Link စနစ်**\n\n📌 **Commands**\n• `/linkon` - ဖွင့်\n• `/linkoff` - ပိတ်\n• `/adddomain domain.com` - Domain ထည့်\n• `/removedomain domain.com` - Domain ဖယ်"
        elif data == "admin_manage":
            text = "👥 **Admin စီမံ**\n\n📌 **Commands**\n• `/addadmin` (Reply) - Admin ထည့်\n• `/removeadmin` (Reply) - Admin ဖယ်"
        elif data == "admin_back":
            query.message.edit_text("🛡️ **Admin Help**\n\nအောက်ပါခလုပ်များကိုနှိပ်ပြီး လေ့လာပါ။", reply_markup=get_admin_help_keyboard())
            return
        elif data == "help_close":
            query.message.delete()
            return
        else:
            text = "အချက်အလက်မရှိပါ။"
        
        query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 နောက်သို့", callback_data="help_back")]]))
    except Exception as e:
        pass

def help_back(update, context):
    try:
        query = update.callback_query
        query.answer()
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        is_owner = (user_id == Config.OWNER_ID)
        keyboard = get_public_help_keyboard()
        if is_owner:
            new_keyboard = [[InlineKeyboardButton("👑 Owner Help", callback_data="help_owner")]]
            new_keyboard.extend(keyboard.inline_keyboard)
            keyboard.inline_keyboard = new_keyboard
        query.message.edit_text("📌 **ဘာကိုလေ့လာချင်လဲ?**\n\nအောက်ပါခလုပ်များကိုနှိပ်ပြီး အသေးစိတ်ကြည့်ပါ။", reply_markup=keyboard)
    except Exception as e:
        pass
