from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

def get_start_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Channel", url=Config.CHANNEL_LINK)],
        [InlineKeyboardButton("🤖 Group သို့ထည့်ရန်", url=Config.BOT_LINK)],
        [InlineKeyboardButton("🧸 Help Mya", callback_data="help_mya")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_welcome_keyboard(bot_username):
    keyboard = [
        [InlineKeyboardButton("➕ Group ထဲထည့်ရန်", url=f"https://t.me/{bot_username}?startgroup=start")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_public_help_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Channel", url=Config.CHANNEL_LINK)],
        [InlineKeyboardButton("🛡️ Admin Help", callback_data="help_admin")],
        [InlineKeyboardButton("❌ ပိတ်ရန်", callback_data="help_close")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_help_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔨 Ban/Mute/Unmute", callback_data="admin_ban"),
         InlineKeyboardButton("🎬 Welcome Video", callback_data="admin_welcome")],
        [InlineKeyboardButton("🔗 Link စနစ်", callback_data="admin_link"),
         InlineKeyboardButton("👥 Admin စီမံ", callback_data="admin_manage")],
        [InlineKeyboardButton("🔙 နောက်သို့", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_owner_help_keyboard():
    keyboard = [
        [InlineKeyboardButton("👑 Owner Commands", callback_data="owner_commands"),
         InlineKeyboardButton("📚 Teach List", callback_data="owner_teachlist")],
        [InlineKeyboardButton("🎬 Video Settings", callback_data="owner_video"),
         InlineKeyboardButton("🏷️ Media Settings", callback_data="owner_media")],
        [InlineKeyboardButton("📊 Stats & Storage", callback_data="owner_stats"),
         InlineKeyboardButton("🧹 Clean Commands", callback_data="owner_clean")],
        [InlineKeyboardButton("🔙 နောက်သို့", callback_data="owner_back")]
    ]
    return InlineKeyboardMarkup(keyboard)
