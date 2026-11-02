import logging
import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import os

# ==================== ሚስጥራዊ ቁልፎችዎን እዚህ ያስገቡ ====================
TELEGRAM_TOKEN = "9168291290:AAGyRH_NDKeRgY1kslpgKpK0WGbgVCuz80o" 
ADMIN_ID = 8776479328  # <--- የእርስዎ የቴሌግራም ID
# ==================================================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

SERVICES = {
    "plan": {"name": "📐 ፕላን ስምምነት", "docs": "1. Original site plan (ኦሪጅናል ሳይት ፕላን)\n2. ነባር የፀደቀ ፕላን (ካለው)\n3. ክእዳ እና እግዳ ነፃ ስለመሆኑ መረጃ\n4. የመሬት ካርታ (የባለቤትነት ማረጋገጫ)"},
    "new_house": {"name": "🏠 አዲስ መኖሪያ ቤት ፍቃድ", "docs": "1. Original site plan (ኦሪጅናል ሳይት ፕላን)\n2. ነባር የፀደቀ ፕላን (ካለው)\n3. ክእዳ እና እግዳ ነፃ ስለመሆኑ መረጃ\n4. የተረጋገጠ ፕላን (በምህንድስና ባለሙያ የተፈረመ)\n5. የባለቤት መታወቂያ ኮፒ"},
    "built_house": {"name": "🏡 የተሰራ ቤት ፕላን ማፅደቅ", "docs": "1. Original site plan (ኦሪጅናል ሳይት ፕላን)\n2. ነባር የፀደቀ ፕላን (ካለው)\n3. ክእዳ እና እግዳ ነፃ ስለመሆኑ መረጃ\n4. የተጠናቀቀው ቤት ፎቶ\n5. የመሬት ካርታ"},
    "fence": {"name": "🧱 የአጥር ፍቃድ", "docs": "1. Original site plan (ኦሪጅናል ሳይት ፕላን)\n2. ነባር የፀደቀ ፕላን (ካለው)\n3. ክእዳ እና እግዳ ነፃ ስለመሆኑ መረጃ\n4. የመሬት ካርታ\n5. የቀበሌ ደብዳቤ"},
    "renovation": {"name": "🛠️ የእድሳት ፍቃድ", "docs": "1. Original site plan (ኦሪጅናል ሳይት ፕላን)\n2. ነባር የፀደቀ ፕላን (ካለው)\n3. ክእዳ እና እግዳ ነፃ ስለመሆኑ መረጃ\n4. የአሮጌው ቤት ፎቶ\n5. የሚደረገው ማሻሻያ ፕላን/ስዕል"}
}

MAIN_MENU_BUTTON = "🏠 ዋና ማውጫ (Main Menu)"

# ==================== የቴሌግራም ቦት ኮድ ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    reply_keyboard = [[KeyboardButton(MAIN_MENU_BUTTON)]]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, is_persistent=True)
    await update.message.reply_text(
        "እንኳን ወደ ህንፃ ፈቃድ መመሪያ ቦት በደህና መጡ! 🏗️\n\n"
        "አገልግሎቶችን ለማየት ከታች ያለውን '🏠 ዋና ማውጫ' ቁልፍ ይጫኑ ወይም /menu ይጻፉ።",
        reply_markup=markup
    )

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
        edit_message = True
    else:
        message = update.message
        edit_message = False
        
    keyboard = [[InlineKeyboardButton(service['name'], callback_data=key)] for key, service in SERVICES.items()]
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
        keyboard = [[InlineKeyboardButton(service['name'], callback_data=key)] for key, service in SERVICES.items()]
        await query.edit_message_text("እባክዎ ማወቅ የሚፈልጉትን አገልግሎት ከታች ይምረጡ፦", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if service_key in SERVICES:
        service = SERVICES[service_key]
        message_text = f"*{service['name']}*\n\nለዚህ አገልግሎት የሚያስፈልጉ ሰነዶች፦\n{service['docs']}\n\n✅ ሰነዶችዎ ሙሉ ከሆኑ ከታች ያለውን 'ሰነዶቼን ልላክ' የሚለውን ቁልፍ ተጭነው ፎቶ ወይም PDF ይላኩ።"
        keyboard = [[InlineKeyboardButton("📤 ሰነዶቼን ልላክ", callback_data=f"upload_{service_key}")], [InlineKeyboardButton("🔙 ወደ ዋናው ማውጫ", callback_data="back_to_menu")]]
        await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def upload_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service_key = query.data.split("_")[1]
    context.user_data['uploading_service'] = service_key
    context.user_data['files'] = []
    
    await query.edit_message_text(
        f"📥 እባክዎ ለ *{SERVICES[service_key]['name']}* የሚያስፈልጉትን ሰነዶች ፎቶ ወይም PDF አድርገው ይላኩ።\n\nሁሉንም ሰነዶች ልከው ሲጨርሱ የ'✅ አስቀምጥ እና ላክ' ቁልፍን ይጫኑ።",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ አስቀምጥ እና ላክ", callback_data="finish_upload")]])
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'uploading_service' not in context.user_data:
        await update.message.reply_text("እባክዎ መጀመሪያ '🏠 ዋና ማውጫ' በማለት አገልግሎት ይምረጡ።")
        return

    if update.message.photo:
        context.user_data['files'].append({'type': 'photo', 'id': update.message.photo[-1].file_id})
    elif update.message.document:
        context.user_data['files'].append({'type': 'document', 'id': update.message.document.file_id})
    else:
        return

    await update.message.reply_text(f"✅ ፋይል {len(context.user_data['files'])} ተቀምጧል! ተጨማሪ ፋይል ካለ ይላኩ ወይም '✅ አስቀምጥ እና ላክ' ይጫኑ።")

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
    await query.edit_message_text(f"⏳ በአጠቃላይ {len(files)} ፋይሎች ወደ ቢሮው እየተላኩ ነው...")
    
    for i, file in enumerate(files, 1):
        try:
            caption = f"📥 አዲስ ሰነድ መጥቷል! (ፋይል {i}/{len(files)})\n\n👤 ከ፦ {user_name} (ID: {user_id})\n📌 አገልግሎት፦ {service_name}"
            if file['type'] == 'photo':
                await context.bot.send_photo(chat_id=ADMIN_ID, photo=file['id'], caption=caption)
            elif file['type'] == 'document':
                await context.bot.send_document(chat_id=ADMIN_ID, document=file['id'], caption=caption)
        except Exception as e:
            print(f"Error: {e}")
            
    context.user_data.clear()
    await query.edit_message_text("✅ ሂደቱ ተጠናቅቋል! ሰነዶችዎ ተልከዋል። አዲስ ማመልከቻ ለማድረግ '🏠 ዋና ማውጫ' ን ይጫኑ።")

# ==================== የFlask ሰርቨር (ለዌብሳይት ትዕዛዞች) ====================
app = Flask(__name__)
CORS(app)  # 👈 ይህ ዌብሳይቱ እንዲያገኘው ይፈቅዳል

@app.route('/')
def home():
    return "Combined Bot is running"

@app.route('/api/order', methods=['POST'])
def receive_order():
    data = request.json
    item = data.get('item')
    price = data.get('price')
    phone = data.get('phone')
    
    # የትዕዛዙን መልእክት ወደ ቴሌግራም መላክ
    msg = f"🛒 **አዲስ የሱቅ ትዕዛዝ መጥቷል!**\n\n📦 እቃ፦ {item}\n💰 ዋጋ፦ {price} ብር\n📞 የደንበኛው ስልክ፦ {phone}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    try:
        requests.post(url, json={"chat_id": ADMIN_ID, "text": msg, "parse_mode": "Markdown"})
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error sending order to telegram: {e}")
        return jsonify({"status": "error"}), 500

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
# ========================================================

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", show_menu))
    application.add_handler(MessageHandler(filters.Regex(f"^{re.escape(MAIN_MENU_BUTTON)}$"), show_menu))
    application.add_handler(CallbackQueryHandler(show_menu, pattern="^show_menu$"))
    application.add_handler(CallbackQueryHandler(service_callback, pattern="^(plan|new_house|built_house|fence|renovation|back_to_menu)$"))
    application.add_handler(CallbackQueryHandler(upload_callback, pattern="^upload_"))
    application.add_handler(CallbackQueryHandler(finish_upload, pattern="^finish_upload$"))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_document))
    
    print("የተዋሃደ ቦት መስራት ጀምሯል...")
    application.run_polling()
