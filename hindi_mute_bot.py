from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler
import asyncio
import nest_asyncio
import time
import random
from datetime import datetime, timedelta

# Fix for environments with existing event loops
nest_asyncio.apply()

# Bot authentication token
TOKEN = "YOUR_BOT_TOKEN_HERE"

# Admin user ID for special permissions
ADMIN_USER_ID = 000000000  # Replace with actual admin ID

# User management storage
user_warnings = {}
approved_users = set()
user_data = {}  
username_to_id = {}  
blessings_data = {}  

# Game configuration
ROMAN_HINDI_WORDS = ["kya", "tum", "hai", "kaise", "nahi", "kyu", "main", "aap", "hum", "ho", "raha", "kar", "mera", "tera"]

# Game economy settings
OCR_COIN_REWARD = 100
OCR_COIN_COOLDOWN = 6 * 3600
HEN_COST = 2000
COW_COST = 4000
SHIELD_COST = 300
EGG_VALUE = 150
MILK_VALUE = 4000
THEFT_PERCENTAGE = 0.8
EGG_COOLDOWN = 30 * 60
MILK_COOLDOWN = 6 * 3600
BLESSING_REWARD = 300
BLESSING_DURATION = 5 * 60

# Helper function to get or create user data
def get_user_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            'ocr_wallet': 100,
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

# Cooldown check functions
def can_claim_ocr_coin(user_id):
    data = get_user_data(user_id)
    return time.time() - data['last_ocr_coin'] >= OCR_COIN_COOLDOWN

def can_collect_eggs(user_id):
    data = get_user_data(user_id)
    return time.time() - data['last_egg_collection'] >= EGG_COOLDOWN

def can_collect_milk(user_id):
    data = get_user_data(user_id)
    return time.time() - data['last_milk_collection'] >= MILK_COOLDOWN

# Hindi language detection
def contains_hindi(text):
    if not text:
        return False, []
    
    detected_words = []
    words = text.lower().split()
    for word in words:
        if word in ROMAN_HINDI_WORDS:
            detected_words.append(word)
    
    return len(detected_words) > 0, detected_words

# Bot initialization command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Hindi Moderator Bot with OCR Game is now active!")

# Status check command
async def ocr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is active with OCR Game features!")

# User approval system
async def approve_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message with /approve to authorize them.")
        return
    
    target_user = update.message.reply_to_message.from_user
    approved_users.add(target_user.id)
    await update.message.reply_text(f"✅ User {target_user.first_name} has been approved!")

async def disapprove_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message with /disapprove to revoke access.")
        return
    
    target_user = update.message.reply_to_message.from_user
    if target_user.id in approved_users:
        approved_users.remove(target_user.id)
    await update.message.reply_text(f"❌ User {target_user.first_name} has been disapproved!")

async def approved_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not approved_users:
        await update.message.reply_text("No approved users currently.")
        return
    
    approved_list = "✅ Approved Users:\n"
    for user_id in approved_users:
        try:
            user = await context.bot.get_chat(user_id)
            approved_list += f"- {user.first_name} (@{user.username})\n" if user.username else f"- {user.first_name}\n"
        except:
            approved_list += f"- Unknown User ({user_id})\n"
    
    await update.message.reply_text(approved_list)

# OCR Game economy commands
async def ocrcoin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if can_claim_ocr_coin(user_id):
        data['ocr_wallet'] += OCR_COIN_REWARD
        data['last_ocr_coin'] = time.time()
        await update.message.reply_text(
            f"🎉 You claimed {OCR_COIN_REWARD} OCR Coins!\n"
            f"💰 New balance: {data['ocr_wallet']} 🪙\n"
            f"⏰ Next claim in {OCR_COIN_COOLDOWN//3600} hours."
        )
    else:
        remaining_time = OCR_COIN_COOLDOWN - (time.time() - data['last_ocr_coin'])
        hours = int(remaining_time // 3600)
        minutes = int((remaining_time % 3600) // 60)
        await update.message.reply_text(
            f"⏳ You can claim coins again in {hours}h {minutes}m.\n"
            f"Use /ocrinfo to check status."
        )

async def ocrwallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    await update.message.reply_text(
        f"💰 Your OCR Coin Balance:\n"
        f"Wallet: {data['ocr_wallet']} 🪙\n"
        f"Bank: {data['ocr_bank']} 🏦\n"
        f"Total: {data['ocr_wallet'] + data['ocr_bank']} 🪙\n"
        f"Shields: {data['shields']} 🛡️\n"
        f"Hens: {data['pets']['hen']} 🐓\n"
        f"Cows: {data['pets']['cow']} 🐄"
    )

async def ocrinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    coin_time_left = max(0, OCR_COIN_COOLDOWN - (time.time() - data['last_ocr_coin']))
    coin_hours = int(coin_time_left // 3600)
    coin_minutes = int((coin_time_left % 3600) // 60)
    
    egg_time_left = max(0, EGG_COOLDOWN - (time.time() - data['last_egg_collection']))
    egg_minutes = int(egg_time_left // 60)
    egg_seconds = int(egg_time_left % 60)
    
    milk_time_left = max(0, MILK_COOLDOWN - (time.time() - data['last_milk_collection']))
    milk_hours = int(milk_time_left // 3600)
    milk_minutes = int((milk_time_left % 3600) // 60)
    
    info_text = (
        f"📊 Your OCR Game Info:\n\n"
        f"💰 Balance: {data['ocr_wallet']} 🪙 (Wallet) + {data['ocr_bank']} 🪙 (Bank)\n"
        f"🛡️ Shields: {data['shields']}\n"
        f"🐓 Hens: {data['pets']['hen']} (Eggs: {egg_minutes}m {egg_seconds}s until next collection)\n"
        f"🐄 Cows: {data['pets']['cow']} (Milk: {milk_hours}h {milk_minutes}m until next collection)\n\n"
        f"⏳ Next OCR Coin: {coin_hours}h {coin_minutes}m\n\n"
        f"Use /ocrwallet, /ocrmarket, /ocrleaderboard"
    )
    
    await update.message.reply_text(info_text)

async def ocrleaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    leaderboard = []
    for user_id, data in user_data.items():
        try:
            user = await context.bot.get_chat(user_id)
            username = user.username or user.first_name
            total_wealth = data['ocr_wallet'] + data['ocr_bank'] + (data['pets']['hen'] * HEN_COST) + (data['pets']['cow'] * COW_COST)
            leaderboard.append((username, total_wealth))
        except:
            continue
    
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    
    leaderboard_text = "🏆 OCR Leaderboard:\n\n"
    for i, (username, wealth) in enumerate(leaderboard[:10], 1):
        leaderboard_text += f"{i}. {username}: {wealth} 🪙\n"
    
    if not leaderboard:
        leaderboard_text = "No players yet! Use /ocrcoin to start."
    
    await update.message.reply_text(leaderboard_text)

async def ocrdeposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if not context.args:
        await update.message.reply_text("Usage: /ocrdeposit <amount>")
        return
    
    try:
        amount = int(context.args[0])
        if amount <= 0:
            await update.message.reply_text("Enter a positive amount.")
            return
        if amount > data['ocr_wallet']:
            await update.message.reply_text("Insufficient wallet balance.")
            return
        
        data['ocr_wallet'] -= amount
        data['ocr_bank'] += amount
        await update.message.reply_text(
            f"✅ Deposited {amount} 🪙 to bank!\n"
            f"💰 Wallet: {data['ocr_wallet']} 🪙\n"
            f"🏦 Bank: {data['ocr_bank']} 🪙"
        )
    except ValueError:
        await update.message.reply_text("Enter a valid number.")

async def ocrwithdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if not context.args:
        await update.message.reply_text("Usage: /ocrwithdraw <amount>")
        return
    
    try:
        amount = int(context.args[0])
        if amount <= 0:
            await update.message.reply_text("Enter a positive amount.")
            return
        if amount > data['ocr_bank']:
            await update.message.reply_text("Insufficient bank balance.")
            return
        
        data['ocr_bank'] -= amount
        data['ocr_wallet'] += amount
        await update.message.reply_text(
            f"✅ Withdrew {amount} 🪙 from bank!\n"
            f"💰 Wallet: {data['ocr_wallet']} 🪙\n"
            f"🏦 Bank: {data['ocr_bank']} 🪙"
        )
    except ValueError:
        await update.message.reply_text("Enter a valid number.")

# Gambling command
async def abhi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if not context.args:
        await update.message.reply_text("Usage: /abhi <amount>\nExample: /abhi 100")
        return
    
    try:
        bet_amount = int(context.args[0])
        if bet_amount <= 0:
            await update.message.reply_text("Enter a positive bet amount.")
            return
        
        if bet_amount > data['ocr_wallet']:
            await update.message.reply_text(
                f"Insufficient balance!\n"
                f"Your balance: {data['ocr_wallet']} 🪙\n"
                f"Bet amount: {bet_amount} 🪙"
            )
            return
        
        if random.random() < 0.7:
            win_amount = bet_amount * 2
            data['ocr_wallet'] += win_amount
            await update.message.reply_text(
                f"🎉 You won! Double payout!\n"
                f"💰 Won: {win_amount} 🪙\n"
                f"💵 New balance: {data['ocr_wallet']} 🪙"
            )
        else:
            data['ocr_wallet'] -= bet_amount
            await update.message.reply_text(
                f"😔 You lost the bet.\n"
                f"💸 Lost: {bet_amount} 🪙\n"
                f"💵 New balance: {data['ocr_wallet']} 🪙"
            )
    except ValueError:
        await update.message.reply_text("Enter a valid number.")

# Theft mechanism
async def chori_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    thief_data = get_user_data(user_id)
    
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to someone's message to attempt theft!")
        return
    
    target_user = update.message.reply_to_message.from_user
    if target_user.id == user_id:
        await update.message.reply_text("Cannot steal from yourself!")
        return
    
    if target_user.id in blessings_data and blessings_data[target_user.id]['expiry'] > time.time():
        await update.message.reply_text("Target is blessed and protected! ✨")
        return
    
    target_data = get_user_data(target_user.id)
    
    if target_data['shields'] > 0:
        target_data['shields'] -= 1
        await update.message.reply_text(
            f"🛡️ {target_user.first_name} blocked your theft with a shield!\n"
            f"They have {target_data['shields']} shields remaining."
        )
        return
    
    current_time = time.time()
    if target_user.id in thief_data['theft_attempts']:
        last_attempt = thief_data['theft_attempts'][target_user.id]
        if current_time - last_attempt < 3600:
            remaining = int(3600 - (current_time - last_attempt))
            minutes = remaining // 60
            await update.message.reply_text(
                f"⏳ Try again in {minutes} minutes."
            )
            return
    
    thief_data['theft_attempts'][target_user.id] = current_time
    
    steal_amount = min(int(target_data['ocr_wallet'] * THEFT_PERCENTAGE), 100)
    
    if steal_amount <= 0:
        await update.message.reply_text(f"{target_user.first_name} has no coins to steal! 💸")
        return
    
    target_data['ocr_wallet'] -= steal_amount
    thief_data['ocr_wallet'] += steal_amount
    
    await update.message.reply_text(
        f"💰 Stole {steal_amount} 🪙 from {target_user.first_name}!\n"
        f"Your wallet: {thief_data['ocr_wallet']} 🪙\n"
        f"Next attempt in 1 hour."
    )

# Defense system
async def buyshield_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if data['shields'] >= 3:
        await update.message.reply_text("Maximum 3 shields allowed!")
        return
    
    if data['ocr_wallet'] < SHIELD_COST:
        await update.message.reply_text(
            f"Need {SHIELD_COST} 🪙 for a shield!\n"
            f"Your balance: {data['ocr_wallet']} 🪙"
        )
        return
    
    data['ocr_wallet'] -= SHIELD_COST
    data['shields'] += 1
    
    await update.message.reply_text(
        f"🛡️ Shield purchased for {SHIELD_COST} 🪙!\n"
        f"Total shields: {data['shields']}/3\n"
        f"Remaining balance: {data['ocr_wallet']} 🪙"
    )

# Marketplace system
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
        "   • Theft protection\n"
        "   • Maximum 3 shields\n\n"
        "Use /buyhen, /buycow, /buyshield"
    )
    await update.message.reply_text(market_text)

async def buyhen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if data['ocr_wallet'] < HEN_COST:
        await update.message.reply_text(
            f"Need {HEN_COST} 🪙 for a hen!\n"
            f"Your balance: {data['ocr_wallet']} 🪙"
        )
        return
    
    data['ocr_wallet'] -= HEN_COST
    data['pets']['hen'] += 1
    
    await update.message.reply_text(
        f"🐓 Hen purchased for {HEN_COST} 🪙!\n"
        f"Total hens: {data['pets']['hen']}\n"
        f"Remaining balance: {data['ocr_wallet']} 🪙\n"
        f"Use /collecteggs every 30 minutes for eggs!"
    )

async def buycow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if data['ocr_wallet'] < COW_COST:
        await update.message.reply_text(
            f"Need {COW_COST} 🪙 for a cow!\n"
            f"Your balance: {data['ocr_wallet']} 🪙"
        )
        return
    
    data['ocr_wallet'] -= COW_COST
    data['pets']['cow'] += 1
    
    await update.message.reply_text(
        f"🐄 Cow purchased for {COW_COST} 🪙!\n"
        f"Total cows: {data['pets']['cow']}\n"
        f"Remaining balance: {data['ocr_wallet']} 🪙\n"
        f"Use /collectmilk every 6 hours for milk!"
    )

# Pet management
async def mypets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    eggs_ready = can_collect_eggs(user_id)
    milk_ready = can_collect_milk(user_id)
    
    pets_text = (
        f"🐓 Hens: {data['pets']['hen']}\n"
        f"🐄 Cows: {data['pets']['cow']}\n\n"
    )
    
    if data['pets']['hen'] > 0:
        if eggs_ready:
            eggs_to_collect = data['pets']['hen'] * 2
            pets_text += f"✅ Eggs ready: {eggs_to_collect} (Use /collecteggs)\n"
        else:
            time_left = EGG_COOLDOWN - (time.time() - data['last_egg_collection'])
            minutes = int(time_left // 60)
            seconds = int(time_left % 60)
            pets_text += f"⏳ Next eggs in: {minutes}m {seconds}s\n"
    
    if data['pets']['cow'] > 0:
        if milk_ready:
            milk_to_collect = data['pets']['cow']
            pets_text += f"✅ Milk ready: {milk_to_collect} (Use /collectmilk)\n"
        else:
            time_left = MILK_COOLDOWN - (time.time() - data['last_milk_collection'])
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            pets_text += f"⏳ Next milk in: {hours}h {minutes}m\n"
    
    if data['pets']['hen'] == 0 and data['pets']['cow'] == 0:
        pets_text += "No pets yet! Visit /ocrmarket to buy."
    
    await update.message.reply_text(pets_text)

async def collecteggs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if data['pets']['hen'] == 0:
        await update.message.reply_text("No hens! Buy from /ocrmarket")
        return
    
    if not can_collect_eggs(user_id):
        time_left = EGG_COOLDOWN - (time.time() - data['last_egg_collection'])
        minutes = int(time_left // 60)
        seconds = int(time_left % 60)
        await update.message.reply_text(f"⏳ Hens resting! Return in {minutes}m {seconds}s.")
        return
    
    eggs = data['pets']['hen'] * 2
    earnings = eggs * EGG_VALUE
    
    blessing_bonus = 1.0
    if user_id in blessings_data and blessings_data[user_id]['expiry'] > time.time():
        blessing_bonus = 2.0
        earnings = int(earnings * blessing_bonus)
    
    data['ocr_wallet'] += earnings
    data['last_egg_collection'] = time.time()
    
    bonus_text = " (Blessing bonus applied!)" if blessing_bonus > 1.0 else ""
    await update.message.reply_text(
        f"🥚 Collected {eggs} eggs{bonus_text}!\n"
        f"💰 Earned: {earnings} 🪙\n"
        f"New balance: {data['ocr_wallet']} 🪙"
    )

async def collectmilk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if data['pets']['cow'] == 0:
        await update.message.reply_text("No cows! Buy from /ocrmarket")
        return
    
    if not can_collect_milk(user_id):
        time_left = MILK_COOLDOWN - (time.time() - data['last_milk_collection'])
        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)
        await update.message.reply_text(f"⏳ Cows resting! Return in {hours}h {minutes}m.")
        return
    
    milk = data['pets']['cow']
    earnings = milk * MILK_VALUE
    
    blessing_bonus = 1.0
    if user_id in blessings_data and blessings_data[user_id]['expiry'] > time.time():
        blessing_bonus = 2.0
        earnings = int(earnings * blessing_bonus)
    
    data['ocr_wallet'] += earnings
    data['last_milk_collection'] = time.time()
    
    bonus_text = " (Blessing bonus applied!)" if blessing_bonus > 1.0 else ""
    await update.message.reply_text(
        f"🥛 Collected {milk} milk{bonus_text}!\n"
        f"💰 Earned: {earnings} 🪙\n"
        f"New balance: {data['ocr_wallet']} 🪙"
    )

# Message handler for Hindi detection
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    user_id = update.message.from_user.id
    message_text = update.message.text
    
    # Allow approved users and admin to speak any language
    if user_id in approved_users or user_id == ADMIN_USER_ID:
        return
    
    # Check for Hindi words
    has_hindi, detected_words = contains_hindi(message_text)
    
    if has_hindi:
        # Warn user
        if user_id not in user_warnings:
            user_warnings[user_id] = 0
        
        user_warnings[user_id] += 1
        warnings = user_warnings[user_id]
        
        warning_message = f"⚠️ Hindi detected: {', '.join(detected_words)}\nWarning #{warnings}/3 - Use only English!"
        
        if warnings >= 3:
            try:
                await update.message.delete()
                warning_message = "❌ Message deleted! 3/3 warnings - You're temporarily muted!"
                
                # Apply temporary restriction
                until_date = datetime.now() + timedelta(hours=1)
                await context.bot.restrict_chat_member(
                    update.message.chat.id,
                    user_id,
                    until_date=until_date,
                    permissions=None
                )
                
                # Reset warnings after mute
                user_warnings[user_id] = 0
            except Exception as e:
                warning_message = "⚠️ Couldn't delete message (insufficient permissions)"
        
        await update.message.reply_text(warning_message)

# Main function to set up the bot
def main():
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ocr", ocr_command))
    application.add_handler(CommandHandler("approve", approve_user_command))
    application.add_handler(CommandHandler("disapprove", disapprove_user_command))
    application.add_handler(CommandHandler("approvedlist", approved_list_command))
    
    # OCR game commands
    application.add_handler(CommandHandler("ocrcoin", ocrcoin_command))
    application.add_handler(CommandHandler("ocrwallet", ocrwallet_command))
    application.add_handler(CommandHandler("ocrinfo", ocrinfo_command))
    application.add_handler(CommandHandler("ocrleaderboard", ocrleaderboard_command))
    application.add_handler(CommandHandler("ocrdeposit", ocrdeposit_command))
    application.add_handler(CommandHandler("ocrwithdraw", ocrwithdraw_command))
    application.add_handler(CommandHandler("abhi", abhi_command))
    application.add_handler(CommandHandler("chori", chori_command))
    application.add_handler(CommandHandler("buyshield", buyshield_command))
    application.add_handler(CommandHandler("ocrmarket", ocrmarket_command))
    application.add_handler(CommandHandler("buyhen", buyhen_command))
    application.add_handler(CommandHandler("buycow", buycow_command))
    application.add_handler(CommandHandler("mypets", mypets_command))
    application.add_handler(CommandHandler("collecteggs", collecteggs_command))
    application.add_handler(CommandHandler("collectmilk", collectmilk_command))
    
    # Message handler for Hindi detection
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
