import logging
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from flask import Flask
import threading
import os

# ==================== ሚስጥራዊ ቁልፎችዎን እዚህ ያስገቡ ====================
TELEGRAM_TOKEN = "9168291290:AAGyRH_NDKeRgY1ksIpgKpK0WGbgVCuz80o"
GEMINI_API_KEY = "AQ.Ab8RN6Jco2c96ahxnHR9V-2FTV8RNgqCNkwpt2o74fTRre8BPA"
# ==================================================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

client = genai.Client(api_key=GEMINI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሰላም! እኔ በ AI የተጎለበተ ረዳትዎ ነኝ። ማንኛውንም ጥያቄ መጠየቅ ይችላሉ።")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.chat.send_action(action="typing")
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction="You are a helpful assistant. Always reply in Amharic."
            )
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
