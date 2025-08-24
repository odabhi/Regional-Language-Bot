from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler
import asyncio
import nest_asyncio
import time
import random
from datetime import datetime, timedelta

# Fix for Pydroid / already running event loop
nest_asyncio.apply()

# Your bot token
TOKEN = "8293084237:AAFIadRPQZLXbiQ0IhYDeWdaxd3nGmuzTX0"

# ==================== STORAGE ====================
user_warnings = {}
approved_users = set()
user_data = {}  # OCR Game data

# ==================== GAME CONFIG ====================
ROMAN_HINDI = ["kya", "tum", "hai", "kaise", "nahi", "kyu", "main", "aap", "hum", "ho", "raha", "kar", "mera", "tera"]

# OCR Game Settings
OCR_COIN_REWARD = 100
OCR_COIN_COOLDOWN = 6 * 3600  # 6 hours
HEN_COST = 2000
COW_COST = 4000
SHIELD_COST = 300
EGG_VALUE = 150
MILK_VALUE = 4000
THEFT_PERCENTAGE = 0.8  # 80%

# ==================== HELPER FUNCTIONS ====================
def get_user_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            'ocr_wallet': 100,  # Starting coins
            'ocr_bank': 0,
            'shields': 0,
            'pets': {'hen': 0, 'cow': 0},
            'last_ocr_coin': 0,
            'last_egg_collection': 0,
            'last_milk_collection': 0,
            'theft_attempts': {},
            'pet_attacks': {}
        }
    return user_data[user_id]

def can_claim_ocr_coin(user_id):
    data = get_user_data(user_id)
    return time.time() - data['last_ocr_coin'] >= OCR_COIN_COOLDOWN

# ==================== HINDI DETECTION ====================
def contains_hindi(text):
    if not text:
        return False, []
        
    text_lower = text.lower()
    detected_words = []
    
    # Check Devanagari script
    devanagari_chars = [ch for ch in text if '\u0900' <= ch <= '\u097F']
    if devanagari_chars:
        detected_words.extend(devanagari_chars)
    
    # Check Romanized Hindi words
    words = text_lower.split()
    for word in words:
        if word in ROMAN_HINDI:
            detected_words.append(word)
    
    return len(detected_words) > 0, detected_words

# ==================== MODERATION COMMANDS ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Hindi Moderator Bot + OCR Game is now active!")

async def ocr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive and working with OCR Game features!")

async def approve_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a user's message with /abhiloveu to approve them.")
        return
        
    target_user = update.message.reply_to_message.from_user
    approved_users.add(target_user.id)
    await update.message.reply_text(f"✅ User {target_user.first_name} has been approved!")

async def disapprove_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a user's message with /abhihateu to disapprove them.")
        return
        
    target_user = update.message.reply_to_message.from_user
    if target_user.id in approved_users:
        approved_users.remove(target_user.id)
        await update.message.reply_text(f"❌ User {target_user.first_name} has been disapproved!")
    else:
        await update.message.reply_text(f"User {target_user.first_name} was not approved.")

async def approved_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not approved_users:
        await update.message.reply_text("No users are currently approved.")
        return
        
    user_list = []
    for user_id in approved_users:
        try:
            chat_member = await context.bot.get_chat_member(update.message.chat.id, user_id)
            user_name = chat_member.user.first_name
            user_list.append(f"{user_name} (ID: {user_id})")
        except:
            user_list.append(f"Unknown User (ID: {user_id})")
    
    await update.message.reply_text(f"✅ Approved Users:\n" + "\n".join(user_list))

# ==================== OCR GAME COMMANDS ====================
async def ocrcoin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if can_claim_ocr_coin(user_id):
        data['ocr_wallet'] += OCR_COIN_REWARD
        data['last_ocr_coin'] = time.time()
        await update.message.reply_text(f"🎉 You received {OCR_COIN_REWARD} OCR Coin! 🪙\nTotal: {data['ocr_wallet']} OCR Coin")
    else:
        next_claim = data['last_ocr_coin'] + OCR_COIN_COOLDOWN
        wait_time = next_claim - time.time()
        hours = int(wait_time // 3600)
        minutes = int((wait_time % 3600) // 60)
        await update.message.reply_text(f"⏰ Come back in {hours}h {minutes}m to claim more OCR Coin!")

async def ocrwallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    await update.message.reply_text(
        f"💰 Your OCR Coin Balance:\n"
        f"Wallet: {data['ocr_wallet']} 🪙\n"
        f"Bank: {data['ocr_bank']} 🏦\n"
        f"Total: {data['ocr_wallet'] + data['ocr_bank']} 🪙"
    )

async def ocrdeposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if context.args and context.args[0].isdigit():
        amount = int(context.args[0])
        if amount <= data['ocr_wallet'] and amount > 0:
            data['ocr_wallet'] -= amount
            data['ocr_bank'] += amount
            await update.message.reply_text(f"✅ Deposited {amount} OCR Coin to bank! 🏦")
        else:
            await update.message.reply_text("❌ Invalid amount or insufficient funds!")
    else:
        await update.message.reply_text("Usage: /ocrdeposit [amount]")

async def ocrwithdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if context.args and context.args[0].isdigit():
        amount = int(context.args[0])
        if amount <= data['ocr_bank'] and amount > 0:
            data['ocr_bank'] -= amount
            data['ocr_wallet'] += amount
            await update.message.reply_text(f"✅ Withdrew {amount} OCR Coin from bank! 💰")
        else:
            await update.message.reply_text("❌ Invalid amount or insufficient bank balance!")
    else:
        await update.message.reply_text("Usage: /ocrwithdraw [amount]")

async def abhi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if context.args and context.args[0].isdigit():
        amount = int(context.args[0])
        if amount <= data['ocr_wallet'] and amount > 0:
            if random.random() < 0.5:  # 50% chance to win
                data['ocr_wallet'] += amount
                await update.message.reply_text(f"🎊 You won! {amount} OCR Coin doubled! 🪙")
            else:
                data['ocr_wallet'] -= amount
                await update.message.reply_text(f"😢 You lost {amount} OCR Coin. Better luck next time!")
        else:
            await update.message.reply_text("❌ Invalid amount or insufficient funds!")
    else:
        await update.message.reply_text("Usage: /abhi [amount]")

async def chori_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    thief_data = get_user_data(user_id)
    
    if not context.args:
        await update.message.reply_text("Usage: /chori [@username]")
        return
    
    target_username = context.args[0].replace('@', '')
    try:
        # This would need actual user resolution - simplified for example
        target_data = get_user_data(12345)  # Placeholder
        if target_data['shields'] > 0:
            target_data['shields'] -= 1
            await update.message.reply_text("🛡️ Target has shield! Theft blocked, but shield consumed.")
        else:
            steal_amount = int(target_data['ocr_wallet'] * THEFT_PERCENTAGE)
            thief_data['ocr_wallet'] += steal_amount
            target_data['ocr_wallet'] -= steal_amount
            await update.message.reply_text(f"💰 Successfully stole {steal_amount} OCR Coin!")
    except:
        await update.message.reply_text("❌ Could not find user or steal coins")

async def buyshield_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if data['shields'] >= 3:
        await update.message.reply_text("❌ Maximum 3 shields already purchased!")
        return
        
    if data['ocr_wallet'] >= SHIELD_COST:
        data['ocr_wallet'] -= SHIELD_COST
        data['shields'] += 1
        await update.message.reply_text(f"🛡️ Shield purchased! You now have {data['shields']} shields.")
    else:
        await update.message.reply_text(f"❌ Need {SHIELD_COST} OCR Coin to buy a shield!")

async def ocrmarket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    market_text = (
        "🛒 OCR Market Place:\n\n"
        f"🐓 Hen - {HEN_COST} OCR Coin\n"
        "   • Produces 2 eggs every 30min\n"
        "   • Each egg: 150 OCR Coin\n\n"
        f"🐄 Cow - {COW_COST} OCR Coin\n"
        "   • Produces milk every 6 hours\n"
        "   • Each milk: 4000 OCR Coin\n\n"
        "🛡️ Shield - 300 OCR Coin\n"
        "   • Protects against theft\n"
        "   • Max 3 shields\n\n"
        "Use /buyhen, /buycow, /buyshield"
    )
    await update.message.reply_text(market_text)

async def buyhen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if data['ocr_wallet'] >= HEN_COST:
        data['ocr_wallet'] -= HEN_COST
        data['pets']['hen'] += 1
        await update.message.reply_text(f"🐓 Hen purchased! You now have {data['pets']['hen']} hens.")
    else:
        await update.message.reply_text(f"❌ Need {HEN_COST} OCR Coin to buy a hen!")

async def buycow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if data['ocr_wallet'] >= COW_COST:
        data['ocr_wallet'] -= COW_COST
        data['pets']['cow'] += 1
        await update.message.reply_text(f"🐄 Cow purchased! You now have {data['pets']['cow']} cows.")
    else:
        await update.message.reply_text(f"❌ Need {COW_COST} OCR Coin to buy a cow!")

async def mypets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    pets_text = f"🐾 Your Pets:\n\n"
    if data['pets']['hen'] > 0:
        pets_text += f"🐓 Hens: {data['pets']['hen']}\n"
    if data['pets']['cow'] > 0:
        pets_text += f"🐄 Cows: {data['pets']['cow']}\n"
    
    if data['pets']['hen'] == 0 and data['pets']['cow'] == 0:
        pets_text += "No pets yet! Visit /ocrmarket"
    
    await update.message.reply_text(pets_text)

async def abhigiveyou_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    giver_data = get_user_data(user_id)
    
    if len(context.args) >= 2 and context.args[0].isdigit():
        amount = int(context.args[0])
        receiver_username = context.args[1].replace('@', '')
        
        if amount <= giver_data['ocr_wallet'] and amount > 0:
            giver_data['ocr_wallet'] -= amount
            # In real implementation, you'd get receiver's user_id from username
            await update.message.reply_text(f"🎁 Gift of {amount} OCR Coin sent to {receiver_username}!")
        else:
            await update.message.reply_text("❌ Invalid amount or insufficient funds!")
    else:
        await update.message.reply_text("Usage: /abhigiveyou [amount] [@username]")

# ==================== MESSAGE HANDLING ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # Hindi moderation handling
    chat = update.message.chat
    user = update.message.from_user
    user_id = user.id
    user_name = user.first_name
    username = f"@{user.username}" if user.username else ""
    text = update.message.text or ""

    # Check if user is approved (immune to rules)
    if user_id in approved_users:
        return  # Skip moderation for approved users

    # Hindi detection
    has_hindi, detected_words = contains_hindi(text)
    
    if has_hindi:
        # Get admin IDs
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [admin.user.id for admin in admins]

        # Admin message → delete + warn
        if user_id in admin_ids:
            await update.message.delete()
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"Admin {user_name} {username} message deleted. Detected Hindi: {', '.join(detected_words)}"
            )
            return

        # Count warnings for normal users
        if user_id not in user_warnings:
            user_warnings[user_id] = 0
        user_warnings[user_id] += 1
        warn_count = user_warnings[user_id]

        if warn_count < 3:
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"⚠ Warning {warn_count}/3 for [{user_name}](tg://user?id={user_id}) {username}\n"
                     f"Detected Hindi words: {', '.join(detected_words)}\n"
                     f"{chat.title} is a regional group. Please use only regional language.",
                parse_mode="Markdown"
            )
        else:
            # Mute user for 15 minutes
            await context.bot.restrict_chat_member(
                chat_id=chat.id,
                user_id=user_id,
                permissions={"can_send_messages": False},
                until_date=int(time.time()) + 900  # 15 min
            )

            # Reset warning
            user_warnings[user_id] = 0

            # Inline button to unmute
            keyboard = [[InlineKeyboardButton("✅ Unmute", callback_data=f"unmute_{user_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=chat.id,
                text=f"🚫 [{user_name}](tg://user?id={user_id}) {username} has been muted for 15 minutes.\n"
                     f"Detected Hindi words: {', '.join(detected_words)}",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("unmute_"):
        user_id = int(query.data.split("_")[1])
        chat_id = query.message.chat.id

        # Unmute user
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions={"can_send_messages": True}
        )

        await query.edit_message_text("✅ User has been unmuted by admin.")

# ==================== MAIN BOT SETUP ====================
def main():
    print("🤖 Starting Hindi Moderator + OCR Game Bot...")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Moderation commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ocr", ocr_command))
    app.add_handler(CommandHandler("abhiloveu", approve_user_command))
    app.add_handler(CommandHandler("abhihateu", disapprove_user_command))
    app.add_handler(CommandHandler("abhilovelist", approved_list_command))
    
    # OCR Game commands
    app.add_handler(CommandHandler("ocrcoin", ocrcoin_command))
    app.add_handler(CommandHandler("ocrwallet", ocrwallet_command))
    app.add_handler(CommandHandler("ocrdeposit", ocrdeposit_command))
    app.add_handler(CommandHandler("ocrwithdraw", ocrwithdraw_command))
    app.add_handler(CommandHandler("abhi", abhi_command))
    app.add_handler(CommandHandler("chori", chori_command))
    app.add_handler(CommandHandler("buyshield", buyshield_command))
    app.add_handler(CommandHandler("ocrmarket", ocrmarket_command))
    app.add_handler(CommandHandler("buyhen", buyhen_command))
    app.add_handler(CommandHandler("buycow", buycow_command))
    app.add_handler(CommandHandler("mypets", mypets_command))
    app.add_handler(CommandHandler("abhigiveyou", abhigiveyou_command))
    
    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Bot started with Hindi moderation + OCR Game features!")
    print("🎮 Game features: /ocrcoin, /ocrwallet, /ocrmarket, /abhi, /chori")
    print("🛡️ Moderation: Hindi detection, warnings, approval system")
    
    app.run_polling()

if __name__ == "__main__":
    main()
