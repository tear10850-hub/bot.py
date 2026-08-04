import re
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

def is_emoji_only(text):
    if not text:
        return False
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+",
        flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub('', text).strip()
    return len(cleaned) == 0 and len(text) > 0

def get_user_info(user):
    bio = user.bio if user.bio else "မရှိပါ"
    return {
        "name": user.first_name or "Unknown",
        "user_id": user.id,
        "username": f"@{user.username}" if user.username else "No username",
        "bio": bio
    }

def extract_links(text):
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+])+|'
        r'(?:www\.)[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+|'
        r't\.me/[a-zA-Z0-9_]+|telegram\.me/[a-zA-Z0-9_]+'
    )
    return url_pattern.findall(text)

def is_allowed_link(link, allowed_domains):
    if not allowed_domains:
        return False
    for domain in allowed_domains:
        if domain in link:
            return True
    return False

def send_typing_action(bot, chat_id):
    try:
        bot.send_chat_action(chat_id=chat_id, action="typing")
    except:
        pass

def is_group_admin(bot, chat_id, user_id):
    try:
        chat_admins = bot.get_chat_administrators(chat_id)
        admin_ids = [admin.user.id for admin in chat_admins]
        return user_id in admin_ids
    except:
        return False
