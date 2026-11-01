import logging
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from flask import Flask
import threading
import os

# ==================== ሚስጥራዊ ቁልፎችዎን እዚህ ያስገቡ ====================
TELEGRAM_TOKEN = "9168291290:AAEgnKEeTQITEmilLKsXeF7_EswrqCMvj7c" 
# ==================================================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# የጨዋታ መረጃ ማስቀመጫ (Memory)
user_cards = {}      # የተጫዋቾችን ካርድ ለማስቀመጥ
drawn_numbers = []   # የወጡ ቁጥሮችን ለማስቀመጥ

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("እንኳን ወደ Bingo ጨዋታ በደህና መጡ! 🎲\n\nካርድ ለማግኘት /play ይጻፉ።\nቁጥር ለማውጣት /draw ይጻፉ።\nለማሸነፍ /bingo ይጻፉ።")

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in user_cards:
        await update.message.reply_text("አስቀድመው ካርድ አለዎት! መጫወት ለመጀመር /draw ይጻፉ።")
        return
        
    # 3x3 ካርድ ማመንጨት (9 የተለያዩ ቁጥሮች ከ1-30)
    card_numbers = random.sample(range(1, 31), 9)
    user_cards[user_id] = card_numbers
    
    # ካርዱን በሚያምር መልኩ ማሳየት
    card_display = f"🎟️ **የእርስዎ የ Bingo ካርድ፦**\n\n"
    card_display += f"[ {card_numbers[0]:02d} ]  [ {card_numbers[1]:02d} ]  [ {card_numbers[2]:02d} ]\n"
    card_display += f"[ {card_numbers[3]:02d} ]  [ {card_numbers[4]:02d} ]  [ {card_numbers[5]:02d} ]\n"
    card_display += f"[ {card_numbers[6]:02d} ]  [ {card_numbers[7]:02d} ]  [ {card_numbers[8]:02d} ]\n"
    
    await update.message.reply_text(card_display, parse_mode='Markdown')

async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global drawn_numbers
    
    if len(drawn_numbers) >= 30:
        await update.message.reply_text("ሁሉም ቁጥሮች ወጥተዋል! አዲስ ጨዋታ ለመጀመር /reset ይጻፉ።")
        return
        
    available_numbers = [n for n in range(1, 31) if n not in drawn_numbers]
    
    if not available_numbers:
        return
        
    new_number = random.choice(available_numbers)
    drawn_numbers.append(new_number)
    
    await update.message.reply_text(f"🎲 **የወጣው ቁጥር፦ {new_number}**\n\nየወጡ ቁጥሮች፦ {', '.join(map(str, drawn_numbers))}", parse_mode='Markdown')

async def bingo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_cards:
        await update.message.reply_text("እባክዎ መጀመሪያ /play በማለት ካርድ ይውሰዱ።")
        return
        
    user_card = user_cards[user_id]
    
    # ሁሉም የተጫዋቹ ቁጥሮች መውጣታቸውን ማረጋገጥ
    if all(num in drawn_numbers for num in user_card):
        await update.message.reply_text(f"🎉 **ቢንጎ!** {update.effective_user.first_name} አሸነፈ! 🏆")
        # ጨዋታውን ማጽዳት
        user_cards.clear()
        drawn_numbers.clear()
    else:
        missing = [num for num in user_card if num not in drawn_numbers]
        await update.message.reply_text(f"❌ ገና አልተጠናቀቀም። ያልወጡልዎ ቁጥሮች፦ {', '.join(map(str, missing))}")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global drawn_numbers
    drawn_numbers.clear()
    user_cards.clear()
    await update.message.reply_text("ጨዋታው ተመልሷል! አዲስ ካርድ ለማግኘት /play ይጻፉ።")

# ==================== የFlask ሰርቨር (ለRender) ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bingo Bot is running"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
# ==================================================================

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # ትዕዛዞችን መመዝገብ
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play", play))
    application.add_handler(CommandHandler("draw", draw))
    application.add_handler(CommandHandler("bingo", bingo))
    application.add_handler(CommandHandler("reset", reset))
    
    print("Bingo ቡት መስራት ጀምሯል...")
    application.run_polling()
