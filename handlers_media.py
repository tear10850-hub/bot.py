from config import Config
from database import db

def handle_sticker(update, context):
    try:
        user_id = update.effective_user.id
        sticker = update.message.sticker
        if user_id == Config.OWNER_ID:
            db.save_sticker(sticker.file_id, sticker.emoji or "")
            update.message.reply_text(f"✅ Sticker သိမ်းပြီး! 📊 {db.get_all_stickers()} ခုရှိပြီ။")
            return
        random_sticker = db.get_random_sticker()
        update.message.reply_sticker(random_sticker) if random_sticker else update.message.reply_text("😅 Sticker မရှိသေးဘူး။")
    except Exception as e:
        pass

def handle_photo(update, context):
    try:
        user_id = update.effective_user.id
        photo = update.message.photo[-1]
        if user_id == Config.OWNER_ID:
            caption = update.message.caption or ""
            db.save_photo(photo.file_id, caption)
            update.message.reply_text(f"✅ Photo သိမ်းပြီး! 📊 {db.get_all_photos()} ခုရှိပြီ။")
            return
        random_photo = db.get_random_photo()
        update.message.reply_photo(random_photo) if random_photo else update.message.reply_text("📸 Photo မရှိသေးဘူး။")
    except Exception as e:
        pass

def handle_video_message(update, context):
    try:
        user_id = update.effective_user.id
        video = update.message.video
        if user_id == Config.OWNER_ID:
            caption = update.message.caption or ""
            db.save_video(video.file_id, caption)
            update.message.reply_text(f"✅ Video သိမ်းပြီး! 📊 {db.get_all_videos()} ခုရှိပြီ။")
            return
        random_video = db.get_random_video()
        update.message.reply_video(random_video) if random_video else update.message.reply_text("🎬 Video မရှိသေးဘူး။")
    except Exception as e:
        pass

def handle_audio_message(update, context):
    try:
        user_id = update.effective_user.id
        audio = update.message.audio or update.message.voice
        if user_id == Config.OWNER_ID:
            caption = update.message.caption or ""
            db.save_audio(audio.file_id, caption)
            update.message.reply_text(f"✅ Audio သိမ်းပြီး! 📊 {db.get_all_audios()} ခုရှိပြီ။")
            return
        random_audio = db.get_random_audio()
        if random_audio:
            update.message.reply_audio(random_audio) if update.message.audio else update.message.reply_voice(random_audio)
        else:
            update.message.reply_text("🎵 Audio မရှိသေးဘူး။")
    except Exception as e:
        pass

def handle_emoji(update, context):
    try:
        user_id = update.effective_user.id
        emoji = update.message.text
        db.save_emoji(user_id, emoji)
        random_emoji = db.get_random_emoji()
        update.message.reply_text(random_emoji) if random_emoji else update.message.reply_text("😊")
    except Exception as e:
        pass

def list_stickers(update, context):
    try:
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            update.message.reply_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        update.message.reply_text(f"📊 Sticker: {db.get_all_stickers()} ခု")
    except Exception as e:
        pass

def clear_stickers(update, context):
    try:
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            update.message.reply_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        db.clear_all_stickers()
        update.message.reply_text("🗑️ Sticker အကုန်ဖျက်ပြီး။")
    except Exception as e:
        pass

def list_photos(update, context):
    try:
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            update.message.reply_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        update.message.reply_text(f"📊 Photo: {db.get_all_photos()} ခု")
    except Exception as e:
        pass

def clear_photos(update, context):
    try:
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            update.message.reply_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        db.clear_all_photos()
        update.message.reply_text("🗑️ Photo အကုန်ဖျက်ပြီး။")
    except Exception as e:
        pass
