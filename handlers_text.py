from datetime import datetime
from config import Config
from database import db
from helpers import is_emoji_only, extract_links, is_allowed_link, is_group_admin
from handlers_media import handle_emoji

def handle_text_message(update, context):
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        user_message = update.message.text
        
        # ===== Check Links =====
        links = extract_links(user_message)
        if links:
            is_admin = is_group_admin(context.bot, chat_id, user_id)
            if not is_admin:
                settings = db.get_link_settings(chat_id)
                allowed_domains = settings.get('allowed_domains', [])
                blocked_links = [l for l in links if not is_allowed_link(l, allowed_domains)]
                if blocked_links and settings.get('delete_links', True):
                    update.message.delete()
                    update.message.reply_text(f"🚫 **လင့်ပို့ခွင့်မရှိပါ**\n\n👤 {update.message.from_user.first_name}")
                    return
        
        # ===== Emoji =====
        if is_emoji_only(user_message):
            handle_emoji(update, context)
            return
        
        # ===== Teach System =====
        qa_answer = db.get_answer(user_message)
        if qa_answer:
            update.message.reply_text(qa_answer)
            return
        
        # ===== Save & Reply =====
        db.save_message(user_id, user_message)
        msg = db.get_random_message()
        update.message.reply_text(msg['message'] + " 😊") if msg else update.message.reply_text(
            "😅 စာမရှိသေးဘူး။\n\n💡 Owner ကို ဆက်သွယ်ပါ။"
        )
    except Exception as e:
        pass
