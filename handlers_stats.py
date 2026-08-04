from datetime import datetime
from config import Config
from database import db

def today_stats(update, context):
    try:
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            update.message.reply_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        stats = db.get_today_stats()
        update.message.reply_text(f"📊 **ဒီနေ့စာရင်း**\n📅 {datetime.now().strftime('%Y-%m-%d')}\n\n📝 စာ: {stats['total']} ကြောင်း")
    except Exception as e:
        pass

def week_stats(update, context):
    try:
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            update.message.reply_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        stats = db.get_week_stats()
        update.message.reply_text(f"📊 **ဒီတစ်ပတ်စာရင်း**\n📆 {datetime.now().strftime('%Y-%m-%d')} ထိ\n\n📝 စာ: {stats['total']} ကြောင်း")
    except Exception as e:
        pass

def month_stats(update, context):
    try:
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            update.message.reply_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        stats = db.get_month_stats()
        update.message.reply_text(f"📊 **ဒီတစ်လစာရင်း**\n📆 {datetime.now().strftime('%Y-%m-%d')} ထိ\n\n📝 စာ: {stats['total']} ကြောင်း\n📊 ပျမ်းမျှ: {stats['total']/30:.0f} ကြောင်း/နေ့")
    except Exception as e:
        pass

def all_stats(update, context):
    try:
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            update.message.reply_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        stats = db.get_all_stats()
        total_mb = (stats['total'] * 500) / 1024 / 1024
        update.message.reply_text(
            f"📊 **စုစုပေါင်းစာရင်း**\n\n📝 စာ: {stats['total']:,} ကြောင်း\n"
            f"✅ သုံးပြီး: {stats['used']:,} ကြောင်း\n⏳ မသုံးရသေး: {stats['unused']:,} ကြောင်း\n"
            f"💾 နေရာ: {total_mb:.2f} MB"
        )
    except Exception as e:
        pass

def storage_status(update, context):
    try:
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            update.message.reply_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        total = db.messages.count_documents({})
        estimated_mb = (total * 500) / 1024 / 1024
        status = "🟢 အန္တရာယ်ကင်း" if estimated_mb < 300 else "🟡 စောင့်ကြည့်ရမယ်" if estimated_mb < 400 else "🟠 နေရာကျပ်လာပြီ" if estimated_mb < 480 else "🔴 နေရာပြည့်တော့မယ်!"
        update.message.reply_text(f"📊 **Storage Status**\n\n📝 စာ: {total:,} ကြောင်း\n💾 နေရာ: {estimated_mb:.2f} MB / 512 MB\n📊 အခြေ: {status}")
    except Exception as e:
        pass

def force_clean(update, context):
    try:
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            update.message.reply_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        result = db.messages.delete_many({"usage_count": {"$lt": 2}, "timestamp": {"$lt": datetime.now() - timedelta(days=7)}})
        update.message.reply_text(f"🧹 ဖျက်လိုက်တာ: {result.deleted_count} ကြောင်း")
    except Exception as e:
        pass
