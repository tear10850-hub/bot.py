from config import Config
from database import db

def report_command(update, context):
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user = update.effective_user
        if not context.args:
            update.message.reply_text("⚠️ /report [ပြဿနာ]")
            return
        issue = " ".join(context.args)
        admins = db.get_group_admins(chat_id)
        if not admins:
            try:
                chat_admins = context.bot.get_chat_administrators(chat_id)
                admins = [admin.user.id for admin in chat_admins]
                db.save_group_admins(chat_id, admins)
            except:
                update.message.reply_text("❌ Admin ရှာမတွေ့။")
                return
        admin_mentions = []
        for admin_id in admins[:5]:
            try:
                admin = context.bot.get_chat(admin_id)
                admin_mentions.append(f"@{admin.username}" if admin.username else f"[Admin](tg://user?id={admin_id})")
            except:
                admin_mentions.append(f"[Admin](tg://user?id={admin_id})")
        report_msg = (
            f"🚨 **အရေးပေါ်အကြောင်းကြားချက်** 🚨\n\n"
            f"👤 {user.first_name}\n🆔 `{user_id}`\n📝 {issue}\n\n{' '.join(admin_mentions)}"
        )
        update.message.reply_text(report_msg, parse_mode="Markdown")
        update.message.reply_text("✅ Admin တွေဆီပို့ပြီး။")
    except Exception as e:
        pass
