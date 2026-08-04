import logging
import asyncio
import time
from datetime import datetime, timedelta
from collections import defaultdict

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from config import Config
from database import db
from helpers import *
from keyboards import *
from handlers_start import *
from handlers_help import *
from handlers_teach import *
from handlers_report import *
from handlers_ban import *
from handlers_video import *
from handlers_media import *
from handlers_stats import *
from handlers_group import *
from callbacks_help import *
from callbacks_owner import *

# ==================== SETUP ====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== RATE LIMITER ====================
class RateLimiter:
    def __init__(self):
        self.user_limits = defaultdict(list)
        self.MAX_REQUESTS = 10
        self.TIME_WINDOW = 60
    
    def is_allowed(self, user_id):
        now = datetime.now().timestamp()
        self.user_limits[user_id] = [t for t in self.user_limits[user_id] if now - t < self.TIME_WINDOW]
        if len(self.user_limits[user_id]) >= self.MAX_REQUESTS:
            return False
        self.user_limits[user_id].append(now)
        return True

rate_limiter = RateLimiter()

# ==================== MESSAGE HANDLER ====================
def handle_messages(update, context):
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if db.is_user_banned(chat_id, user_id):
            update.message.reply_text("⛔ သင်သည် Ban ခံထားရပါသည်။")
            return
        if db.is_user_muted(chat_id, user_id):
            update.message.reply_text("🔇 သင်သည် Mute ခံထားရပါသည်။")
            return
        
        send_typing_action(context.bot, chat_id)
        if not rate_limiter.is_allowed(user_id):
            update.message.reply_text("⏳ ခေတ္တခဏစောင့်ပါ။")
            return
        
        if update.message.sticker:
            handle_sticker(update, context)
            return
        if update.message.photo:
            handle_photo(update, context)
            return
        if update.message.video:
            handle_video_message(update, context)
            return
        if update.message.document:
            update.message.reply_text("📄 Document")
            return
        if update.message.audio or update.message.voice:
            handle_audio_message(update, context)
            return
        
        if update.message.text:
            handle_text_message(update, context)
    except Exception as e:
        pass

# ==================== AUTO CLEAN LOOP ====================
def auto_clean_loop():
    while True:
        try:
            db.check_and_clean_if_full()
        except Exception as e:
            pass
        time.sleep(600)

# ==================== MAIN ====================
def main():
    try:
        Config.validate()
        asyncio.run(db.connect())
        
        updater = Updater(token=Config.TELEGRAM_BOT_TOKEN, use_context=True)
        dp = updater.dispatcher
        db.bot = updater.bot
        
        # ===== Commands =====
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("teach", teach_command))
        dp.add_handler(CommandHandler("report", report_command))
        dp.add_handler(CommandHandler("ban", ban_command))
        dp.add_handler(CommandHandler("unban", unban_command))
        dp.add_handler(CommandHandler("mute", mute_command))
        dp.add_handler(CommandHandler("unmute", unmute_command))
        
        dp.add_handler(CommandHandler("setstartvideo", set_start_video))
        dp.add_handler(CommandHandler("deletestartvideo", delete_start_video))
        dp.add_handler(CommandHandler("setwelcomevideo", set_welcome_video))
        dp.add_handler(CommandHandler("deletewelcomevideo", delete_welcome_video))
        dp.add_handler(CommandHandler("setleavevideo", set_leave_video))
        dp.add_handler(CommandHandler("deleteleavevideo", delete_leave_video))
        
        dp.add_handler(CommandHandler("liststickers", list_stickers))
        dp.add_handler(CommandHandler("clearstickers", clear_stickers))
        dp.add_handler(CommandHandler("listphotos", list_photos))
        dp.add_handler(CommandHandler("clearphotos", clear_photos))
        
        dp.add_handler(CommandHandler("todaystats", today_stats))
        dp.add_handler(CommandHandler("weekstats", week_stats))
        dp.add_handler(CommandHandler("monthstats", month_stats))
        dp.add_handler(CommandHandler("allstats", all_stats))
        dp.add_handler(CommandHandler("storage", storage_status))
        dp.add_handler(CommandHandler("forceclean", force_clean))
        
        # ===== Callbacks =====
        dp.add_handler(CallbackQueryHandler(help_callback, pattern="^help_"))
        dp.add_handler(CallbackQueryHandler(help_back, pattern="^help_back$"))
        dp.add_handler(CallbackQueryHandler(owner_callback, pattern="^owner_"))
        
        # ===== Handlers =====
        dp.add_handler(MessageHandler(Filters.status_update.NEW_CHAT_MEMBERS | Filters.status_update.LEFT_CHAT_MEMBER, handle_group_members))
        dp.add_handler(MessageHandler(Filters.all & ~Filters.command, handle_messages))
        
        logger.info("🤖 Bot started!")
        updater.start_polling()
        updater.idle()
    except Exception as e:
        logger.error(f"Main error: {e}")
        raise

if __name__ == "__main__":
    main()
