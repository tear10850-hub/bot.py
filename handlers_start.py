from config import Config
from database import db
from helpers import get_user_info
from keyboards import get_start_keyboard

def start(update, context):
    try:
        user = update.effective_user
        user_info = get_user_info(user)
        if db.start_video:
            try:
                video = db.start_video
                caption = video.get('caption', '') + "\n\n" + Config.START_TEXT.format(**user_info)
                update.message.reply_video(video=video['file_id'], caption=caption, reply_markup=get_start_keyboard())
                return
            except:
                pass
        update.message.reply_text(Config.START_TEXT.format(**user_info), reply_markup=get_start_keyboard())
    except Exception as e:
        pass
