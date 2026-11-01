import logging
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, filters
from flask import Flask
import threading
import os

# ==================== ሚስጥራዊ ቁልፎችዎን እዚህ ያስገቡ ====================
TELEGRAM_TOKEN = "9168291290:AAFYfrBrGmwj3IJBJGSjb-L4qKcXauqw9pM" 
ADMIN_ID = 8776479328  # <--- የእርስዎን ID እዚህ ያስገቡ
# ==================================================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# የጨዋታ መረጃ ማስቀመጫ
user_cards = {}        
drawn_numbers = []     
eliminated_users = set() 
banned_users = set()     
game_active = False    
game_joining = False  # አዲስ፦ ሰዎች እየተቀላቀሉ መሆኑን ለማወቅ
game_chat_id = None    

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in banned_users:
        await update.message.reply_text("🚫 እርስዎ በአስተዳዳሪው ከBingo ጨዋታ ተከልክለዋል!")
        return

    keyboard = [[InlineKeyboardButton("🎮 PLAY BINGO", callback_data="play_action")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "እንኳን ወደ Bingo ጨዋታ በደህና መጡ! 🎲\n\n"
        "ጨዋታውን ለመጀመር እና ካርድ ለማግኘት ከታች ያለውን ቁልፍ ይጫኑ።\n"
        "⚠️ ሁሉም ሰው ካርድ እንዲያገኝ 30 ሰከንድ የመጠበቂያ ጊዜ ይሰጣል።",
        reply_markup=reply_markup
    )

async def start_countdown(context: ContextTypes.DEFAULT_TYPE):
    global game_active, game_joining, game_chat_id, drawn_numbers
    
    # 30 ሰከንድ መጠበቅ
    await asyncio.sleep(30) 
    
    game_joining = False
    game_active = True
    drawn_numbers.clear()
    
    await context.bot.send_message(
        chat_id=game_chat_id, 
        text="⏰ **ጊዜው አልቋል!** ቁጥሮች መውጣት ይጀምራሉ... (በየ 5 ሰከንዱ)"
    )
    
    # Auto-draw ን ማስጀመር
    asyncio.create_task(auto_draw_loop(context))

async def play_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_active, game_joining, game_chat_id
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    if user_id in banned_users:
        await query.answer("🚫 እርስዎ ከጨዋታው ተከልክለዋል!", show_alert=True)
        return

    if user_id in eliminated_users:
        await query.message.reply_text(f"🚫 {user_name}፣ ሐሰተኛ ቢንጎ ስለጫኑ ከጨዋታው ተሰርዘዋል!")
        return

    if user_id in user_cards:
        await query.message.reply_text(f"⚠️ {user_name}፣ አስቀድመው ካርድ አለዎት!")
        return

    # ካርድ ማመንጨት
    card_numbers = random.sample(range(1, 31), 9)
    user_cards[user_id] = card_numbers
    
    keyboard = [[InlineKeyboardButton("🎉 BINGO!", callback_data=f"bingo_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    card_display = f"🎟️ **{user_name}፣ ይህ የእርስዎ ካርድ ነው፦**\n\n"
    card_display += f"[ {card_numbers[0]:02d} ]  [ {card_numbers[1]:02d} ]  [ {card_numbers[2]:02d} ]\n"
    card_display += f"[ {card_numbers[3]:02d} ]  [ {card_numbers[4]:02d} ]  [ {card_numbers[5]:02d} ]\n"
    card_display += f"[ {card_numbers[6]:02d} ]  [ {card_numbers[7]:02d} ]  [ {card_numbers[8]:02d} ]\n\n"
    card_display += "👉 ቁጥሮችዎ ሁሉ ሲወጡ የ BINGO ቁልፉን ይጫኑ!"
    
    await query.message.reply_text(card_display, reply_markup=reply_markup, parse_mode='Markdown')
    
    # ጨዋታው ገና ካልተጀመረ (መጀመሪያው ሰው ካርድ ሲወስድ) የመጠበቂያ ጊዜውን ጀምር
    if not game_active and not game_joining:
        game_joining = True
        game_chat_id = query.message.chat_id
        await context.bot.send_message(
            chat_id=game_chat_id, 
            text="🚀 **ጨዋታው ተጀምሯል!** ሁሉም ሰው ካርድ እንዲያገኝ **30 ሰከንድ** አለው። አሁን ይቀላቀሉ!"
        )
        asyncio.create_task(start_countdown(context))

async def auto_draw_loop(context: ContextTypes.DEFAULT_TYPE):
    global game_active, drawn_numbers
    
    while game_active and len(drawn_numbers) < 30:
        await asyncio.sleep(5) 
        
        if not game_active: break
        
        available = [n for n in range(1, 31) if n not in drawn_numbers]
        if not available: 
            game_active = False
            await context.bot.send_message(chat_id=game_chat_id, text="ሁሉም ቁጥሮች ወጥተዋል! አዲስ ጨዋታ ለመጀመር /reset ይጻፉ።")
            break
            
        num = random.choice(available)
        drawn_numbers.append(num)
        
        text = f"🎲 **የወጣው ቁጥር፦ {num}**\n\n"
        text += f"የወጡ ቁጥሮች፦ {', '.join(map(str, drawn_numbers))}"
        
        await context.bot.send_message(chat_id=game_chat_id, text=text, parse_mode='Markdown')

async def bingo_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_active
    
    query = update.callback_query
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    if user_id not in user_cards:
        await query.answer("እባክዎ መጀመሪያ ጨዋታውን ይቀላቀሉ!", show_alert=True)
        return
        
    if all(num in drawn_numbers for num in user_cards[user_id]):
        game_active = False 
        await query.answer("🎉 እንኳን ደስ አለዎት!", show_alert=True)
        await query.message.reply_text(f"🏆 **ቢንጎ!** {user_name} አሸነፈ! 🎉\n\nአዲስ ጨዋታ ለመጀመር /reset ይጻፉ።")
    else:
        eliminated_users.add(user_id)
        if user_id in user_cards:
            del user_cards[user_id]
            
        await query.answer("❌ ሐሰተኛ ቢንጎ! ከጨዋታው ተሰርዘዋል።", show_alert=True)
        await query.message.reply_text(f"🚫 **{user_name}** ሐሰተኛ ቢንጎ ስለጫኑ ከጨዋታው ተሰርዘዋል!")

# ==================== የአስተዳዳሪ ትዕዛዞች ====================
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 ይህን ትዕዛዝ ለመጠቀም አስተዳዳሪ መሆን አለብዎት!")
        return
    try:
        user_to_ban = int(context.args[0])
        banned_users.add(user_to_ban)
        await update.message.reply_text(f"✅ ተጠቃሚው (ID: {user_to_ban}) ከBingo ጨዋታ ተከልክሏል።")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ አጠቃቀም፦ /ban <የተጠቃሚው_ID>")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_to_unban = int(context.args[0])
        banned_users.discard(user_to_unban)
        await update.message.reply_text(f"✅ ተጠቃሚው (ID: {user_to_unban}) ወደ ጨዋታው ተመልሷል።")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ አጠቃቀም፦ /unban <የተጠቃሚው_ID>")

async def reset_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_active, game_joining, drawn_numbers, user_cards, eliminated_users
    game_active = False
    game_joining = False
    drawn_numbers.clear()
    user_cards.clear()
    eliminated_users.clear()
    await update.message.reply_text("🔄 ጨዋታው አዲስ ሆኗል! አዲስ ካርድ ለማግኘት /start ይጻፉ።")

# ==================== የFlask ሰርቨር ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bingo Bot is running"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
# ========================================================

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset_game))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CallbackQueryHandler(play_game, pattern="^play_action$"))
    application.add_handler(CallbackQueryHandler(bingo_claim, pattern="^bingo_"))
    
    print("Bingo ቡት መስራት ጀምሯል...")
    application.run_polling()
