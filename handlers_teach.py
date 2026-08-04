from config import Config
from database import db

def teach_command(update, context):
    try:
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            update.message.reply_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        if not update.message.reply_to_message:
            update.message.reply_text("⚠️ အဖြေစာသားကို reply ထောက်ပြီး `/teach မေးခွန်း` လုပ်ပါ။")
            return
        if not context.args:
            update.message.reply_text("⚠️ မေးခွန်းထည့်ပါ။")
            return
        question = " ".join(context.args)
        answer = update.message.reply_to_message.text
        if not answer:
            update.message.reply_text("⚠️ Reply ထောက်ထားတာက စာသားမဟုတ်ပါဘူး။")
            return
        db.save_qa(question, answer, user_id)
        count = db.get_qa_count()
        update.message.reply_text(
            f"✅ **သင်ပြီးပါပြီ!**\n\n📝 **မေးခွန်း:** {question}\n"
            f"📝 **အဖြေ:** {answer[:100]}{'...' if len(answer) > 100 else ''}\n\n📊 စုစုပေါင်း: {count} ခု"
        )
    except Exception as e:
        pass
