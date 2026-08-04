from database import db
from helpers import is_group_admin

def ban_command(update, context):
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        if not is_group_admin(context.bot, chat_id, user_id):
            update.message.reply_text("⛔ Admin သာသုံးလို့ရပါတယ်။")
            return
        if not update.message.reply_to_message:
            update.message.reply_text("⚠️ User ကို reply ထောက်ပြီး /ban")
            return
        target = update.message.reply_to_message.from_user
        reason = " ".join(context.args) if context.args else "အကြောင်းပြချက်မရှိ"
        db.ban_user(chat_id, target.id, reason)
        update.message.reply_text(f"✅ {target.first_name} ကို Ban လုပ်ပြီး။")
    except Exception as e:
        pass

def unban_command(update, context):
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        if not is_group_admin(context.bot, chat_id, user_id):
            update.message.reply_text("⛔ Admin သာသုံးလို့ရပါတယ်။")
            return
        if not update.message.reply_to_message:
            update.message.reply_text("⚠️ User ကို reply ထောက်ပြီး /unban")
            return
        target = update.message.reply_to_message.from_user
        db.unban_user(chat_id, target.id)
        update.message.reply_text(f"✅ {target.first_name} ကို Unban လုပ်ပြီး။")
    except Exception as e:
        pass

def mute_command(update, context):
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        if not is_group_admin(context.bot, chat_id, user_id):
            update.message.reply_text("⛔ Admin သာသုံးလို့ရပါတယ်။")
            return
        if not update.message.reply_to_message:
            update.message.reply_text("⚠️ User ကို reply ထောက်ပြီး /mute [မိနစ်]")
            return
        target = update.message.reply_to_message.from_user
        duration = 60
        if context.args:
            try:
                duration = int(context.args[0])
            except:
                pass
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "အကြောင်းပြချက်မရှိ"
        db.mute_user(chat_id, target.id, duration, reason)
        update.message.reply_text(f"✅ {target.first_name} ကို {duration} မိနစ် Mute လုပ်ပြီး။")
    except Exception as e:
        pass

def unmute_command(update, context):
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        if not is_group_admin(context.bot, chat_id, user_id):
            update.message.reply_text("⛔ Admin သာသုံးလို့ရပါတယ်။")
            return
        if not update.message.reply_to_message:
            update.message.reply_text("⚠️ User ကို reply ထောက်ပြီး /unmute")
            return
        target = update.message.reply_to_message.from_user
        db.unmute_user(chat_id, target.id)
        update.message.reply_text(f"✅ {target.first_name} ကို Unmute လုပ်ပြီး။")
    except Exception as e:
        pass
