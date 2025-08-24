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

# Your special user ID (replace with your actual Telegram user ID)
YOUR_USER_ID = 123456789  # Change this to your actual user ID

# ==================== STORAGE ====================
user_warnings = {}
approved_users = set()
user_data = {}  # OCR Game data
username_to_id = {}  # Mapping usernames to user IDs
blessings_data = {}  # Store blessings messages and their expiration

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
EGG_COOLDOWN = 30 * 60  # 30 minutes
MILK_COOLDOWN = 6 * 3600  # 6 hours
BLESSING_REWARD = 300  # OCR coins for blessing
BLESSING_DURATION = 5 * 60  # 5 minutes in seconds

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

def can_collect_eggs(user_id):
    data = get_user_data(user_id)
    return time.time() - data['last_egg_collection'] >= EGG_COOLDOWN

def can_collect_milk(user_id):
    data = get_user_data(user_id)
    return time.time() - data['last_milk_collection'] >= MILK_COOLDOWN

# ==================== HINDI DETECTION ====================
def contains_hindi(text):
    if not text:
        return False, []
    
    # Simple detection for Romanized Hindi words
    detected_words = []
    words = text.lower().split()
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

async def approved_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not approved_users:
        await update.message.reply_text("No users are currently approved.")
        return
    
    approved_list = "✅ Approved Users:\n"
    for user_id in approved_users:
        try:
            user = await context.bot.get_chat(user_id)
            approved_list += f"- {user.first_name} (@{user.username})\n" if user.username else f"- {user.first_name}\n"
        except:
            approved_list += f"- Unknown User ({user_id})\n"
    
    await update.message.reply_text(approved_list)

# ==================== OCR GAME COMMANDS ====================
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
            f"Use /ocrinfo to check your status."
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
    
    # Calculate time until next coin claim
    coin_time_left = max(0, OCR_COIN_COOLDOWN - (time.time() - data['last_ocr_coin']))
    coin_hours = int(coin_time_left // 3600)
    coin_minutes = int((coin_time_left % 3600) // 60)
    
    # Calculate time until next egg collection
    egg_time_left = max(0, EGG_COOLDOWN - (time.time() - data['last_egg_collection']))
    egg_minutes = int(egg_time_left // 60)
    egg_seconds = int(egg_time_left % 60)
    
    # Calculate time until next milk collection
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
    # Create a list of users with their total wealth
    leaderboard = []
    for user_id, data in user_data.items():
        try:
            # Try to get username
            user = await context.bot.get_chat(user_id)
            username = user.username or user.first_name
            total_wealth = data['ocr_wallet'] + data['ocr_bank'] + (data['pets']['hen'] * HEN_COST) + (data['pets']['cow'] * COW_COST)
            leaderboard.append((username, total_wealth))
        except:
            continue
    
    # Sort by wealth (descending)
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    
    # Create leaderboard text
    leaderboard_text = "🏆 OCR Leaderboard:\n\n"
    for i, (username, wealth) in enumerate(leaderboard[:10], 1):
        leaderboard_text += f"{i}. {username}: {wealth} 🪙\n"
    
    if not leaderboard:
        leaderboard_text = "No players yet! Use /ocrcoin to get started."
    
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
            await update.message.reply_text("Please enter a positive amount.")
            return
        if amount > data['ocr_wallet']:
            await update.message.reply_text("You don't have enough coins in your wallet.")
            return
        
        data['ocr_wallet'] -= amount
        data['ocr_bank'] += amount
        await update.message.reply_text(
            f"✅ Deposited {amount} 🪙 to your bank!\n"
            f"💰 Wallet: {data['ocr_wallet']} 🪙\n"
            f"🏦 Bank: {data['ocr_bank']} 🪙"
        )
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")

async def ocrwithdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if not context.args:
        await update.message.reply_text("Usage: /ocrwithdraw <amount>")
        return
    
    try:
        amount = int(context.args[0])
        if amount <= 0:
            await update.message.reply_text("Please enter a positive amount.")
            return
        if amount > data['ocr_bank']:
            await update.message.reply_text("You don't have enough coins in your bank.")
            return
        
        data['ocr_bank'] -= amount
        data['ocr_wallet'] += amount
        await update.message.reply_text(
            f"✅ Withdrew {amount} 🪙 from your bank!\n"
            f"💰 Wallet: {data['ocr_wallet']} 🪙\n"
            f"🏦 Bank: {data['ocr_bank']} 🪙"
        )
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")

async def abhi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if not context.args:
        await update.message.reply_text("Usage: /abhi <amount>\nExample: /abhi 100")
        return
    
    try:
        bet_amount = int(context.args[0])
        if bet_amount <= 0:
            await update.message.reply_text("Please enter a positive amount to bet.")
            return
        
        if bet_amount > data['ocr_wallet']:
            await update.message.reply_text(
                f"You don't have enough coins in your wallet!\n"
                f"Your balance: {data['ocr_wallet']} 🪙\n"
                f"Bet amount: {bet_amount} 🪙"
            )
            return
        
        # 70% chance to win, 30% chance to lose
        if random.random() < 0.7:  # 70% win chance
            # Win double the bet amount
            win_amount = bet_amount * 2
            data['ocr_wallet'] += win_amount
            await update.message.reply_text(
                f"🎉 You won! Abhi blessed you with double the amount!\n"
                f"💰 Won: {win_amount} 🪙\n"
                f"💵 New balance: {data['ocr_wallet']} 🪙"
            )
        else:  # 30% lose chance
            # Lose the bet amount
            data['ocr_wallet'] -= bet_amount
            await update.message.reply_text(
                f"😔 You lost! Abhi took your bet amount.\n"
                f"💸 Lost: {bet_amount} 🪙\n"
                f"💵 New balance: {data['ocr_wallet']} 🪙"
            )
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")

async def chori_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    thief_data = get_user_data(user_id)
    
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to someone's message to steal from them!")
        return
    
    target_user = update.message.reply_to_message.from_user
    if target_user.id == user_id:
        await update.message.reply_text("You can't steal from yourself!")
        return
    
    # Check if target has blessing protection
    if target_user.id in blessings_data and blessings_data[target_user.id]['expiry'] > time.time():
        await update.message.reply_text("This user is blessed and protected from theft! ✨")
        return
    
    target_data = get_user_data(target_user.id)
    
    # Check if target has shields
    if target_data['shields'] > 0:
        target_data['shields'] -= 1
        await update.message.reply_text(
            f"🛡️ {target_user.first_name} had a shield and blocked your theft!\n"
            f"They now have {target_data['shields']} shields remaining."
        )
        return
    
    # Check theft cooldown
    current_time = time.time()
    if target_user.id in thief_data['theft_attempts']:
        last_attempt = thief_data['theft_attempts'][target_user.id]
        if current_time - last_attempt < 3600:  # 1 hour cooldown per user
            remaining = int(3600 - (current_time - last_attempt))
            minutes = remaining // 60
            await update.message.reply_text(
                f"⏳ You can try to steal from {target_user.first_name} again in {minutes} minutes."
            )
            return
    
    # Record theft attempt
    thief_data['theft_attempts'][target_user.id] = current_time
    
    # Calculate steal amount (80% of target's wallet or 100 coins, whichever is smaller)
    steal_amount = min(int(target_data['ocr_wallet'] * THEFT_PERCENTAGE), 100)
    
    if steal_amount <= 0:
        await update.message.reply_text(f"{target_user.first_name} has no coins to steal! 💸")
        return
    
    # Perform theft
    target_data['ocr_wallet'] -= steal_amount
    thief_data['ocr_wallet'] += steal_amount
    
    await update.message.reply_text(
        f"💰 You stole {steal_amount} 🪙 from {target_user.first_name}!\n"
        f"Your wallet: {thief_data['ocr_wallet']} 🪙\n"
        f"You can try again in 1 hour."
    )

async def buyshield_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if data['shields'] >= 3:
        await update.message.reply_text("You can only have a maximum of 3 shields!")
        return
    
    if data['ocr_wallet'] < SHIELD_COST:
        await update.message.reply_text(
            f"You need {SHIELD_COST} 🪙 to buy a shield!\n"
            f"Your balance: {data['ocr_wallet']} 🪙"
        )
        return
    
    data['ocr_wallet'] -= SHIELD_COST
    data['shields'] += 1
    
    await update.message.reply_text(
        f"🛡️ You bought a shield for {SHIELD_COST} 🪙!\n"
        f"Total shields: {data['shields']}/3\n"
        f"Remaining balance: {data['ocr_wallet']} 🪙"
    )

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
    
    if data['ocr_wallet'] < HEN_COST:
        await update.message.reply_text(
            f"You need {HEN_COST} 🪙 to buy a hen!\n"
            f"Your balance: {data['ocr_wallet']} 🪙"
        )
        return
    
    data['ocr_wallet'] -= HEN_COST
    data['pets']['hen'] += 1
    
    await update.message.reply_text(
        f"🐓 You bought a hen for {HEN_COST} 🪙!\n"
        f"Total hens: {data['pets']['hen']}\n"
        f"Remaining balance: {data['ocr_wallet']} 🪙\n"
        f"Use /collecteggs every 30 minutes to collect eggs!"
    )

async def buycow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if data['ocr_wallet'] < COW_COST:
        await update.message.reply_text(
            f"You need {COW_COST} 🪙 to buy a cow!\n"
            f"Your balance: {data['ocr_wallet']} 🪙"
        )
        return
    
    data['ocr_wallet'] -= COW_COST
    data['pets']['cow'] += 1
    
    await update.message.reply_text(
        f"🐄 You bought a cow for {COW_COST} 🪙!\n"
        f"Total cows: {data['pets']['cow']}\n"
        f"Remaining balance: {data['ocr_wallet']} 🪙\n"
        f"Use /collectmilk every 6 hours to collect milk!"
    )

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
        pets_text += "You don't have any pets yet! Visit /ocrmarket to buy some."
    
    await update.message.reply_text(pets_text)

async def collecteggs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if data['pets']['hen'] == 0:
        await update.message.reply_text("You don't have any hens! Buy some from /ocrmarket")
        return
    
    if not can_collect_eggs(user_id):
        time_left = EGG_COOLDOWN - (time.time() - data['last_egg_collection'])
        minutes = int(time_left // 60)
        seconds = int(time_left % 60)
        await update.message.reply_text(f"⏳ Your hens need rest! Come back in {minutes}m {seconds}s.")
        return
    
    # Calculate earnings (2 eggs per hen)
    eggs = data['pets']['hen'] * 2
    earnings = eggs * EGG_VALUE
    
    # Apply blessing bonus if active
    blessing_bonus = 1.0
    if user_id in blessings_data and blessings_data[user_id]['expiry'] > time.time():
        blessing_bonus = 2.0
        earnings = int(earnings * blessing_bonus)
    
    data['ocr_wallet'] += earnings
    data['last_egg_collection'] = time.time()
    
    bonus_text = " (2x blessing bonus! ✨)" if blessing_bonus > 1.0 else ""
    
    await update.message.reply_text(
        f"🥚 Collected {eggs} eggs from your {data['pets']['hen']} hens{bonus_text}!\n"
        f"💰 Earned: {earnings} 🪙\n"
        f"💵 New balance: {data['ocr_wallet']} 🪙\n"
        f"⏳ Next collection in 30 minutes."
    )

async def collectmilk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if data['pets']['cow'] == 0:
        await update.message.reply_text("You don't have any cows! Buy some from /ocrmarket")
        return
    
    if not can_collect_milk(user_id):
        time_left = MILK_COOLDOWN - (time.time() - data['last_milk_collection'])
        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)
        await update.message.reply_text(f"⏳ Your cows need rest! Come back in {hours}h {minutes}m.")
        return
    
    # Calculate earnings (1 milk per cow)
    milk = data['pets']['cow']
    earnings = milk * MILK_VALUE
    
    # Apply blessing bonus if active
    blessing_bonus = 1.0
    if user_id in blessings_data and blessings_data[user_id]['expiry'] > time.time():
        blessing_bonus = 2.0
        earnings = int(earnings * blessing_bonus)
    
    data['ocr_wallet'] += earnings
    data['last_milk_collection'] = time.time()
    
    bonus_text = " (2x blessing bonus! ✨)" if blessing_bonus > 1.0 else ""
    
    await update.message.reply_text(
        f"🥛 Collected {milk} milk from your {data['pets']['cow']} cows{bonus_text}!\n"
        f"💰 Earned: {earnings} 🪙\n"
        f"💵 New balance: {data['ocr_wallet']} 🪙\n"
        f"⏳ Next collection in 6 hours."
    )

async def abhigiveyou_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    giver_data = get_user_data(user_id)
    
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to someone's message to give them coins!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /abhigiveyou <amount>")
        return
    
    try:
        amount = int(context.args[0])
        if amount <= 0:
            await update.message.reply_text("Please enter a positive amount.")
            return
        
        if amount > giver_data['ocr_wallet']:
            await update.message.reply_text("You don't have enough coins to give.")
            return
        
        target_user = update.message.reply_to_message.from_user
        target_data = get_user_data(target_user.id)
        
        giver_data['ocr_wallet'] -= amount
        target_data['ocr_wallet'] += amount
        
        await update.message.reply_text(
            f"🎁 You gave {amount} 🪙 to {target_user.first_name}!\n"
            f"Your new balance: {giver_data['ocr_wallet']} 🪙"
        )
        
        # Notify the recipient
        await context.bot.send_message(
            chat_id=target_user.id,
            text=f"🎁 {update.message.from_user.first_name} gave you {amount} 🪙!\n"
                 f"Your new balance: {target_data['ocr_wallet']} 🪙"
        )
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")

# ==================== MESSAGE HANDLER ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    user_id = update.message.from_user.id
    text = update.message.text
    
    # Check if user is approved or is the bot owner
    if user_id in approved_users or user_id == YOUR_USER_ID:
        return
    
    # Check for Hindi words
    has_hindi, words = contains_hindi(text)
    
    if has_hindi:
        # Warn user
        if user_id not in user_warnings:
            user_warnings[user_id] = 0
        
        user_warnings[user_id] += 1
        warnings = user_warnings[user_id]
        
        if warnings == 1:
            await update.message.reply_text(
                f"⚠️ Warning {warnings}/3: Please use English in this group.\n"
                f"Detected words: {', '.join(words)}"
            )
        elif warnings == 2:
            await update.message.reply_text(
                f"⚠️ Warning {warnings}/3: Final warning! Use English only.\n"
                f"Detected words: {', '.join(words)}"
            )
        else:
            # Mute or take action on third warning
            try:
                # Try to restrict user (mute for 10 minutes)
                until_date = datetime.now() + timedelta(minutes=10)
                await context.bot.restrict_chat_member(
                    chat_id=update.message.chat_id,
                    user_id=user_id,
                    permissions=None,
                    until_date=until_date
                )
                await update.message.reply_text(
                    f"🔇 User muted for 10 minutes due to Hindi usage.\n"
                    f"Detected words: {', '.join(words)}"
                )
                # Reset warnings after mute
                user_warnings[user_id] = 0
            except Exception as e:
                await update.message.reply_text(
                    f"❌ Could not mute user. Please make me an admin with restriction permissions.\n"
                    f"Error: {str(e)}"
                )

# ==================== MAIN FUNCTION ====================
def main():
    # Create application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ocr", ocr_command))
    application.add_handler(CommandHandler("abhiloveu", approve_user_command))
    application.add_handler(CommandHandler("abhihateu", disapprove_user_command))
    application.add_handler(CommandHandler("approvedlist", approved_list_command))
    
    # OCR Game commands
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
    application.add_handler(CommandHandler("abhigiveyou", abhigiveyou_command))
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
