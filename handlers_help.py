from telegram import InlineKeyboardButton
from config import Config
from helpers import is_group_admin
from keyboards import get_public_help_keyboard

def help_command(update, context):
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        user = update.effective_user
        is_owner = (user_id == Config.OWNER_ID)
        is_admin = is_group_admin(context.bot, chat_id, user_id)
        role = "👑 Owner" if is_owner else "🛡️ Admin" if is_admin else "👤 Member"
        
        help_text = (
            f"🧸 **အသုံးပြုပုံလမ်းညွှန်** 🧸\n\n"
            f"👤 {user.first_name}\n📌 အဆင့်: **{role}**\n🌷🌷🌷\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n📌 **အမြန်အသုံးပြုနည်း**\n"
            f"• `/start` - Bot ကိုစတင်ရန်\n• `/help` - လမ်းညွှန်ကြည့်ရန်\n"
            f"• `/report` - Admin ကိုအကြောင်းကြားရန်\n\n💡 အောက်ပါခလုပ်များကိုနှိပ်ပြီး လေ့လာပါ။"
        )
        keyboard = get_public_help_keyboard()
        if is_owner:
            new_keyboard = [[InlineKeyboardButton("👑 Owner Help", callback_data="help_owner")]]
            new_keyboard.extend(keyboard.inline_keyboard)
            keyboard.inline_keyboard = new_keyboard
        update.message.reply_text(help_text, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        pass
