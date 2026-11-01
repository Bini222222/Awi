import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from flask import Flask
import threading
import os

# ==================== ሚስጥራዊ ቁልፎችዎን እዚህ ያስገቡ ====================
TELEGRAM_TOKEN = "9168291290:AAGBsZipR-V9ZQeY5Hb2sZpDBLG4B45aN6U"
GROQ_API_KEY = "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" # በ gsk_ የሚጀምረውን ቁልፍ
# ==================================================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሰላም! እኔ በ AI የተጎለበተ ረዳትዎ ነኝ። ማንኛውንም ጥያቄ መጠየቅ ይችላሉ።")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.chat.send_action(action="typing")
    
    try:
        response = requests.post(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant", # ፈጣኑ እና ነፃው የGroq ሞዴል
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant. Always reply in Amharic."},
                    {"role": "user", "content": user_message}
                ]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            bot_reply = response.json()["choices"][0]["message"]["content"]
            await update.message.reply_text(bot_reply)
        else:
            print(f"Groq Error: {response.status_code} - {response.text}")
            await update.message.reply_text("ይቅርታ፣ መልስ ለመስጠት ስሞክር ስህተት ተፈጥሯል።")
            
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("ይቅርታ፣ መልስ ለመስጠት ስሞክር ስህተት ተፈጥሯል።")

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
