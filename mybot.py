import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from flask import Flask
import threading
import os

# ==================== ሚስጥራዊ ቁልፎችዎን እዚህ ያስገቡ ====================
TELEGRAM_TOKEN = "9161480725:AAGz0-Aewon8hbCdGksMGBU-P8hvh4hrNK4" 
ADMIN_ID = 8776479328  # <--- የእርስዎን የቴሌግራም ID እዚህ ያስገቡ
# ==================================================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

SERVICES = {
    "plan": {
        "name": "📐 ፕላን ስምምነት",
        "docs": "1. Original site plan (ኦሪጅናል ሳይት ፕላን)\n2. ነባር የፀደቀ ፕላን (ካለው)\n3. ክእዳ እና እግዳ ነፃ ስለመሆኑ መረጃ\n4. የመሬት ካርታ (የባለቤትነት ማረጋገጫ)"
    },
    "new_house": {
        "name": "🏠 አዲስ መኖሪያ ቤት ፍቃድ",
        "docs": "1. Original site plan (ኦሪጅናል ሳይት ፕላን)\n2. ነባር የፀደቀ ፕላን (ካለው)\n3. ክእዳ እና እግዳ ነፃ ስለመሆኑ መረጃ\n4. የተረጋገጠ ፕላን (በምህንድስና ባለሙያ የተፈረመ)\n5. የባለቤት መታወቂያ ኮፒ"
    },
    "built_house": {
        "name": "🏡 የተሰራ ቤት ፕላን ማፅደቅ",
        "docs": "1. Original site plan (ኦሪጅናል ሳይት ፕላን)\n2. ነባር የፀደቀ ፕላን (ካለው)\n3. ክእዳ እና እግዳ ነፃ ስለመሆኑ መረጃ\n4. የተጠናቀቀው ቤት ፎቶ\n5. የመሬት ካርታ"
    },
    "fence": {
        "name": "🧱 የአጥር ፍቃድ",
        "docs": "1. Original site plan (ኦሪጅናል ሳይት ፕላን)\n2. ነባር የፀደቀ ፕላን (ካለው)\n3. ክእዳ እና እግዳ ነፃ ስለመሆኑ መረጃ\n4. የመሬት ካርታ\n5. የቀበሌ ደብዳቤ"
    },
    "renovation": {
        "name": "🛠️ የእድሳት ፍቃድ",
        "docs": "1. Original site plan (ኦሪጅናል ሳይት ፕላን)\n2. ነባር የፀደቀ ፕላን (ካለው)\n3. ክእዳ እና እግዳ ነፃ ስለመሆኑ መረጃ\n4. የአሮጌው ቤት ፎቶ\n5. የሚደረገው ማሻሻያ ፕላን/ስዕል"
    }
}

# የታችኛው ቋሚ ሜኑ ቁልፍ
MAIN_MENU_BUTTON = "🏠 ዋና ማውጫ (Main Menu)"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    
    # ቋሚ የሆነ የታችኛው ሜኑ ቁልፍ መፍጠር
    reply_keyboard = [[KeyboardButton(MAIN_MENU_BUTTON)]]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, is_persistent=True)
    
    await update.message.reply_text(
        "እንኳን ወደ ህንፃ ፈቃድ መመሪያ ቦት በደህና መጡ! 🏗️\n\n"
        "አገልግሎቶችን ለማየት ከታች ያለውን '🏠 ዋና ማውጫ' ቁልፍ ይጫኑ ወይም /menu ይጻፉ።",
        reply_markup=markup
    )

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ከበተን (Inline) ወይም ከታችኛው ኪቦርድ ሲመጣ ሁለቱንም ለመቀበል
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
        edit_message = True
    else:
        message = update.message
        edit_message = False
        
    keyboard = []
    for key, service in SERVICES.items():
        keyboard.append([InlineKeyboardButton(service['name'], callback_data=key)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "እባክዎ ማወቅ የሚፈልጉትን አገልግሎት ከታች ይምረጡ፦"
    
    if edit_message:
        await message.edit_text(text, reply_markup=reply_markup)
    else:
        await message.reply_text(text, reply_markup=reply_markup)

async def service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service_key = query.data
    
    if service_key == "back_to_menu":
        # ወደ ማውጫ ሲመለስ ደግሞ በቀጥታ ማሳየት
        keyboard = []
        for key, service in SERVICES.items():
            keyboard.append([InlineKeyboardButton(service['name'], callback_data=key)])
        await query.edit_message_text("እባክዎ ማወቅ የሚፈልጉትን አገልግሎት ከታች ይምረጡ፦", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if service_key in SERVICES:
        service = SERVICES[service_key]
        message_text = f"*{service['name']}*\n\n"
        message_text += f"ለዚህ አገልግሎት የሚያስፈልጉ ሰነዶች፦\n{service['docs']}\n\n"
        message_text += "✅ ሰነዶችዎ ሙሉ ከሆኑ ከታች ያለውን 'ሰነዶቼን ልላክ' የሚለውን ቁልፍ ተጭነው ፎቶ ወይም PDF ይላኩ።\n*(ማሳሰቢያ፦ አንድ በአንድ አድርገው ብዙ ፎቶዎችን ወይም PDF መላክ ይችላሉ)*"
        
        keyboard = [
            [InlineKeyboardButton("📤 ሰነዶቼን ልላክ", callback_data=f"upload_{service_key}")],
            [InlineKeyboardButton("🔙 ወደ ዋናው ማውጫ", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')

async def upload_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service_key = query.data.split("_")[1]
    
    context.user_data['uploading_service'] = service_key
    context.user_data['files'] = []
    
    await query.edit_message_text(
        f"📥 እባክዎ ለ *{SERVICES[service_key]['name']}* የሚያስፈልጉትን ሰነዶች ፎቶ ወይም PDF አድርገው ይላኩ።\n\n"
        "በርካታ ፋይሎች ካሉዎት አንዱን ከሌላው በመቀጠል መላክ ይችላሉ (በማህደረ ትውስታ ይያዛሉ)።\n"
        "ሁሉንም ሰነዶች ልከው ሲጨርሱ የ'✅ አስቀምጥ እና ላክ' ቁልፍን ይጫኑ።",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ አስቀምጥ እና ላክ", callback_data="finish_upload")]
        ])
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'uploading_service' not in context.user_data:
        await update.message.reply_text("እባክዎ መጀመሪያ '🏠 ዋና ማውጫ' በማለት አገልግሎት ይምረጡ።")
        return

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        context.user_data['files'].append({'type': 'photo', 'id': file_id})
    elif update.message.document:
        file_id = update.message.document.file_id
        context.user_data['files'].append({'type': 'document', 'id': file_id})
    else:
        return

    file_num = len(context.user_data['files'])
    await update.message.reply_text(f"✅ ፋይል {file_num} በማህደረ ትውስታ ተቀምጧል! ተጨማሪ ፋይል ካለ ይላኩ ወይም '✅ አስቀምጥ እና ላክ' ይጫኑ።")

async def finish_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    files = context.user_data.get('files', [])
    service_key = context.user_data.get('uploading_service')
    
    if not files or not service_key:
        await query.edit_message_text("⚠️ ምንም ፋይል አልተላከም! እባክዎ መጀመሪያ ፋይል ይላኩ።")
        return
        
    service_name = SERVICES[service_key]['name']
    user_name = query.from_user.first_name
    user_id = query.from_user.id
    
    await query.edit_message_text(f"⏳ በአጠቃላይ {len(files)} ፋይሎች ወደ ቢሮው እየተላኩ ነው... እባክዎ ይጠብቁ።")
    
    success_count = 0
    error_msg = ""
    
    for i, file in enumerate(files, 1):
        try:
            caption = f"📥 አዲስ ሰነድ መጥቷል! (ፋይል {i}/{len(files)})\n\n👤 ከ፦ {user_name} (ID: {user_id})\n📌 አገልግሎት፦ {service_name}"
            
            if file['type'] == 'photo':
                await context.bot.send_photo(chat_id=ADMIN_ID, photo=file['id'], caption=caption)
            elif file['type'] == 'document':
                await context.bot.send_document(chat_id=ADMIN_ID, document=file['id'], caption=caption)
            success_count += 1
        except Exception as e:
            error_msg += f"\n❌ ፋይል {i} መላክ አልተቻለም: {str(e)}"
            print(f"Error sending file {i}: {e}")
            
    context.user_data.clear()
    
    final_message = f"✅ ሂደቱ ተጠናቅቋል! **{success_count}** ከ **{len(files)}** ፋይሎች ተልከዋል።"
    if error_msg:
        final_message += f"\n\n⚠️ አንዳንድ ችግሮች አጋጥመዋል፦{error_msg}"
        
    final_message += "\n\nአዲስ ማመልከቻ ለማድረግ '🏠 ዋና ማውጫ' ን ይጫኑ።"
    
    await query.edit_message_text(final_message, parse_mode='Markdown')

# ==================== የFlask ሰርቨር ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "Building Permit Bot is running"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
# ========================================================

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", show_menu)) # /menu ሲባል ማውጫ ይከፈት
    application.add_handler(MessageHandler(filters.Regex(f"^{MAIN_MENU_BUTTON}$"), show_menu)) # የታችኛው ቁልፍ ሲጫን
    application.add_handler(CallbackQueryHandler(show_menu, pattern="^show_menu$"))
    application.add_handler(CallbackQueryHandler(service_callback, pattern="^(plan|new_house|built_house|fence|renovation|back_to_menu)$"))
    application.add_handler(CallbackQueryHandler(upload_callback, pattern="^upload_"))
    application.add_handler(CallbackQueryHandler(finish_upload, pattern="^finish_upload$"))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_document))
    
    print("የህንፃ ፈቃድ ቦት መስራት ጀምሯል...")
    application.run_polling()
