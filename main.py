import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes
from openai import OpenAI

# Logging သတ်မှတ်ခြင်း
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

if not TELEGRAM_TOKEN or not HF_TOKEN:
    logger.error("Environment Variables (TELEGRAM_TOKEN, HF_TOKEN) များကို မတွေ့ရပါ။")

# Hugging Face Router API Client
ai_client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
) if HF_TOKEN else None

# AI မော်ဒယ်များ (Gemini ကို ဦးစားပေးထိပ်ဆုံးတွင် ထည့်သွင်းထားသည်)
AVAILABLE_MODELS = {
    "gemini": {"name": "✨ Gemini Flash", "id": "google/gemini-2.0-flash-exp"},
    "deepseek": {"name": "🧠 DeepSeek-R1", "id": "deepseek-ai/DeepSeek-R1:fastest"},
    "llama": {"name": "🦙 Llama 3.3 (70B)", "id": "meta-llama/Llama-3.3-70B-Instruct"},
    "qwen": {"name": "🔮 Qwen 2.5 (72B)", "id": "Qwen/Qwen2.5-72B-Instruct"},
    "mistral": {"name": "🌊 Mistral Large", "id": "mistralai/Mistral-Large-Instruct-2407"},
    "gemma": {"name": "💎 Gemma 2 (27B)", "id": "google/gemma-2-27b-it"}
}

# User တစ်ဦးချင်းစီအတွက် မော်ဒယ်မှတ်ဉာဏ် (Gemini ကို ပုံမှန်အစအဖြစ် သတ်မှတ်သည်)
user_selected_model = {}

# 🛠️ /model (AI မော်ဒယ်ရွေးချယ်ရန် ခလုတ်များ - Gemini ဦးစားပေး)
async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "အောက်ပါခလုတ်များကိုနှိပ်၍ AI မော်ဒယ်များကို ပြောင်းလဲနိုင်ပါသည် 👇"
    keyboard = [
        [InlineKeyboardButton("✨ Gemini Flash", callback_data="model_gemini"),
         InlineKeyboardButton("🧠 DeepSeek-R1", callback_data="model_deepseek")],
        [InlineKeyboardButton("🦙 Llama 3.3", callback_data="model_llama"),
         InlineKeyboardButton("🔮 Qwen 2.5", callback_data="model_qwen")],
        [InlineKeyboardButton("🌊 Mistral", callback_data="model_mistral"),
         InlineKeyboardButton("💎 Gemma 2", callback_data="model_gemma")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# 🔘 ခလုတ်နှိပ်၍ Model ပြောင်းလဲခြင်း
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith("model_"):
        model_key = data.replace("model_", "")
        if model_key in AVAILABLE_MODELS:
            user_selected_model[user_id] = model_key
            model_info = AVAILABLE_MODELS[model_key]
            await query.edit_message_text(
                text=f"✅ **AI မော်ဒယ်ကို အောင်မြင်စွာ ပြောင်းလဲလိုက်ပါပြီ!**\n\nရွေးချယ်ထားသော မော်ဒယ်: **{model_info['name']}**",
                reply_markup=query.message.reply_markup
            )

# 🤖 Hugging Face AI မှ ဖြေကြားပေးမည့် Function
async def ask_huggingface_ai(prompt: str, user_id: int) -> str:
    if not ai_client:
        return "❌ HF_TOKEN မရှိပါ။"
        
    # User မရွေးရသေးပါက Gemini ("gemini") ကို ဦးစားပေးသုံးမည်
    model_key = user_selected_model.get(user_id, "gemini")
    model_id = AVAILABLE_MODELS[model_key]["id"]
    
    try:
        response = ai_client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "You are a helpful, smart AI assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"AI API Error: {e}")
        return "AI မော်ဒယ်နှင့် ချိတ်ဆက်ရာတွင် အမှားဖြစ်ပွားသွားပါသည်။"

# 💬 /ai ဖြင့် မေးမြန်းခြင်းစနစ်
async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.from_user:
        return
        
    user_id = message.from_user.id
    text_content = " ".join(context.args)
    
    if not text_content:
        await message.reply_text("ကျေးဇူးပြု၍ မေးလိုသည့် မေးခွန်းကို ထည့်ရေးပေးပါ။ ဥပမာ - `/ai မင်္ဂလာပါ`")
        return
        
    await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.TYPING)
    ai_response = await ask_huggingface_ai(text_content, user_id)
    await message.reply_text(ai_response, reply_to_message_id=message.message_id)

async def main_async():
    if not TELEGRAM_TOKEN or not HF_TOKEN:
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(CommandHandler("ai", ai_command))
    app.add_handler(CallbackQueryHandler(button_callback))

    logger.info("🤖 Gemini ဦးစားပေး AI Telegram Bot စတင်အလုပ်လုပ်နေပါပြီ...")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    stop_event = asyncio.Event()
    await stop_event.wait()

def main():
    try:
        asyncio.run(main_async())
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    main()

