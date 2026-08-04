from config import Config
from database import db
from helpers import is_group_admin

def set_start_video(update, context):
    try:
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            update.message.reply_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        if not update.message.reply_to_message:
            update.message.reply_text("⚠️ Video ကို reply ထောက်ပြီး /setstartvideo")
            return
        video = update.message.reply_to_message.video
        if not video:
            update.message.reply_text("⚠️ Video ကိုပဲ reply ထောက်ပေးပါ။")
            return
        caption = update.message.reply_to_message.caption or ""
        db.set_start_video(video.file_id, caption)
        update.message.reply_text("✅ Start Video သတ်မှတ်ပြီး။")
    except Exception as e:
        pass

def delete_start_video(update, context):
    try:
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            update.message.reply_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        db.delete_start_video()
        update.message.reply_text("✅ Start Video ဖျက်ပြီး။")
    except Exception as e:
        pass

def set_welcome_video(update, context):
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        if not is_group_admin(context.bot, chat_id, user_id):
            update.message.reply_text("⛔ Admin သာသုံးလို့ရပါတယ်။")
            return
        if not update.message.reply_to_message:
            update.message.reply_text("⚠️ Video ကို reply ထောက်ပြီး /setwelcomevideo")
            return
        video = update.message.reply_to_message.video
        if not video:
            update.message.reply_text("⚠️ Video ကိုပဲ reply ထောက်ပေးပါ။")
            return
        caption = update.message.reply_to_message.caption or ""
        db.set_welcome_video(video.file_id, caption)
        update.message.reply_text("✅ Welcome Video သတ်မှတ်ပြီး။")
        db.add_group_admin(chat_id, user_id)
    except Exception as e:
        pass

def delete_welcome_video(update, context):
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        if not is_group_admin(context.bot, chat_id, user_id):
            update.message.reply_text("⛔ Admin သာသုံးလို့ရပါတယ်။")
            return
        db.delete_welcome_video()
        update.message.reply_text("✅ Welcome Video ဖျက်ပြီး။")
    except Exception as e:
        pass

def set_leave_video(update, context):
    try:
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            update.message.reply_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        if not update.message.reply_to_message:
            update.message.reply_text("⚠️ Video ကို reply ထောက်ပြီး /setleavevideo")
            return
        video = update.message.reply_to_message.video
        if not video:
            update.message.reply_text("⚠️ Video ကိုပဲ reply ထောက်ပေးပါ။")
            return
        caption = update.message.reply_to_message.caption or ""
        db.set_leave_video(video.file_id, caption)
        update.message.reply_text("✅ Leave Video သတ်မှတ်ပြီး။")
    except Exception as e:
        pass

def delete_leave_video(update, context):
    try:
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            update.message.reply_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        db.delete_leave_video()
        update.message.reply_text("✅ Leave Video ဖျက်ပြီး။")
    except Exception as e:
        pass
