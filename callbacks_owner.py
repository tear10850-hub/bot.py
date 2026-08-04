from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from database import db
from keyboards import get_owner_help_keyboard

def owner_callback(update, context):
    try:
        query = update.callback_query
        query.answer()
        user_id = update.effective_user.id
        data = query.data
        
        if user_id != Config.OWNER_ID:
            query.message.edit_text("⛔ Owner သာသုံးလို့ရပါတယ်။")
            return
        
        if data == "owner_commands":
            text = "👑 **Owner Commands**\n\n📌 **Video**\n• `/setstartvideo` (Reply) - Start Video\n• `/deletestartvideo` - ဖျက်\n• `/setleavevideo` (Reply) - Leave Video\n• `/deleteleavevideo` - ဖျက်\n\n📌 **Media**\n• Sticker/Photo ပို့ရင် အလိုအလျောက်သိမ်း\n• `/liststickers` - Sticker စာရင်း\n• `/clearstickers` - အကုန်ဖျက်\n\n📌 **Teach**\n• `/teach` (Reply) - စာသင်ပေး\n• `/listqa` - စာရင်း\n• `/deleteqa` - ဖျက်\n• `/clearqa` - အကုန်ဖျက်\n\n📌 **Stats**\n• `/todaystats` - ဒီနေ့\n• `/weekstats` - တစ်ပတ်\n• `/monthstats` - တစ်လ\n• `/allstats` - စုစုပေါင်း\n• `/storage` - Storage\n• `/forceclean` - နေရာရှင်း"
        elif data == "owner_teachlist":
            qa_list = db.get_all_qa()
            text = "📚 သင်ပေးထားတာမရှိသေးပါဘူး။" if not qa_list else "📚 **သင်ပေးထားတဲ့စာရင်း**\n\n" + "\n".join([f"{i}. {q['question'][:40]}..." for i, q in enumerate(qa_list[:30], 1)]) + (f"\n\n... နောက်ထပ် {len(qa_list)-30} ခုရှိပါသေးတယ်。" if len(qa_list) > 30 else "") + f"\n\n📊 စုစုပေါင်း: {len(qa_list)} ခု"
        elif data == "owner_video":
            text = f"🎬 **Video Settings**\n\n• Start Video: {'✅ ရှိ' if db.start_video else '❌ မရှိ'}\n• Welcome Video: {'✅ ရှိ' if db.welcome_video else '❌ မရှိ'}\n• Leave Video: {'✅ ရှိ' if db.leave_video else '❌ မရှိ'}"
        elif data == "owner_media":
            text = f"🏷️ **Media Settings**\n\n• Sticker: {db.get_all_stickers()} ခု\n• Photo: {db.get_all_photos()} ခု"
        elif data == "owner_stats":
            stats = db.get_all_stats()
            total = db.messages.count_documents({})
            text = f"📊 **Stats & Storage**\n\n📝 စာ: {stats['total']:,} ကြောင်း\n💾 နေရာ: {(total*500)/1024/1024:.2f} MB / 512 MB"
        elif data == "owner_clean":
            text = "🧹 **Clean Commands**\n\n• `/forceclean` - နေရာရှင်း\n• `/clearmessages` - အကုန်ဖျက်\n• `/cleanmessages` - သန့်ရှင်းပေး"
        elif data == "owner_back":
            query.message.edit_text("👑 **Owner Help**\n\nအောက်ပါခလုပ်များကိုနှိပ်ပြီး လေ့လာပါ။", reply_markup=get_owner_help_keyboard())
            return
        else:
            text = "အချက်အလက်မရှိပါ။"
        
        query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 နောက်သို့", callback_data="owner_back")]]))
    except Exception as e:
        pass
