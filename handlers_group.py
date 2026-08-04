import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from database import db
from helpers import get_user_info
from keyboards import get_welcome_keyboard

def handle_group_members(update, context):
    try:
        chat_id = update.effective_chat.id
        
        try:
            chat_admins = context.bot.get_chat_administrators(chat_id)
            admin_ids = [admin.user.id for admin in chat_admins]
            db.save_group_admins(chat_id, admin_ids)
        except:
            pass
        
        if update.message.new_chat_members:
            for member in update.message.new_chat_members:
                if member.is_bot:
                    continue
                user_info = get_user_info(member)
                welcome_msg = Config.WELCOME_TEXT.format(**user_info)
                if db.welcome_video:
                    try:
                        video = db.welcome_video
                        caption = video.get('caption', '') + "\n\n" + welcome_msg
                        update.message.reply_video(video=video['file_id'], caption=caption, reply_markup=get_welcome_keyboard(context.bot.username))
                        return
                    except:
                        pass
                update.message.reply_text(welcome_msg, reply_markup=get_welcome_keyboard(context.bot.username))
        
        if update.message.left_chat_member:
            for member in update.message.left_chat_member:
                if member.is_bot:
                    continue
                user_info = get_user_info(member)
                leave_msg = Config.LEAVE_TEXT.format(**user_info)
                emojis = db.get_reaction_emojis()
                random_emoji = random.choice(emojis) if emojis else "🧸"
                if db.leave_video:
                    try:
                        video = db.leave_video
                        caption = video.get('caption', '') + "\n\n" + leave_msg
                        update.message.reply_video(video=video['file_id'], caption=caption, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{random_emoji} Profile", url=f"tg://user?id={member.id}")]]))
                        return
                    except:
                        pass
                update.message.reply_text(leave_msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{random_emoji} Profile", url=f"tg://user?id={member.id}")]]))
    except Exception as e:
        pass
