import logging
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from flask import Flask
import threading
import os

# ==================== ሚስጥራዊ ቁልፎችዎን እዚህ ያስገቡ ====================
TELEGRAM_TOKEN = "9168291290:AAGGtKKlBgin-UMb3c2DC_kMQ-Ug6jJZ7wU"
GEMINI_API_KEY = "AQ.Ab8RN6IZmuG6wyVe_r8Smq2QLR1lgo9m-oaCzeB3SfvF7678Pw" # የአንተ አዲስ AQ. ቁልፍ
# ==================================================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# አዲሱ የGoogle AI ላይብረሪ አጠቃቀም
client = genai.Client(api_key=GEMINI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሰላም! እኔ በ AI የተጎለበተ ረዳትዎ ነኝ። ማንኛውንም ጥያቄ መጠየቅ ይችላሉ።")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.chat.send_action(action="typing")
    
    try:
        # አዲሱ የGoogle AI ጥያቄ አቀራረብ (ሞዴሉን ወደ gemini-3.8-flash ቀይረነዋል)
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=user_message,
        )
        bot_reply = response.text
        await update.message.reply_text(bot_reply)
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("ይቅርታ፣ መልስ ለመስጠት ስሞክር ስህተት ተፈጥሯል። እባክዎ ቆይተው እንደገና ይሞክሩ።")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("ቦቱ መስራት ጀምሯል...")
    application.run_polling()
