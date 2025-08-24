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
        f"Total: {data['ocr_wallet'] + data['ocr_bank']} 🪙\n"
        f"Shields: {data['shields']} 🛡️\n"
        f"Hens: {data['pets']['hen']} 🐓\n"
        f"Cows: {data['pets']['cow']} 🐄"
    )

async def ocrinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    # Calculate next collection times
    next_egg = ""
    if data['pets']['hen'] > 0:
        if can_collect_eggs(user_id):
            next_egg = "Ready to collect!"
        else:
            next_collection = data['last_egg_collection'] + EGG_COOLDOWN
            wait_time = next_collection - time.time()
            minutes = int(wait_time // 60)
            next_egg = f"{minutes} minutes"
    
    next_milk = ""
    if data['pets']['cow'] > 0:
        if can_collect_milk(user_id):
            next_milk = "Ready to collect!"
        else:
            next_collection = data['last_milk_collection'] + MILK_COOLDOWN
            wait_time = next_collection - time.time()
            hours = int(wait_time // 3600)
            minutes = int((wait_time % 3600) // 60)
            next_milk = f"{hours}h {minutes}m"
    
    info_text = (
        f"👤 User Info:\n\n"
        f"💰 Wallet: {data['ocr_wallet']} 🪙\n"
        f"🏦 Bank: {data['ocr_bank']} 🪙\n"
        f"🛡️ Shields: {data['shields']}\n\n"
        f"🐓 Hens: {data['pets']['hen']} - Next eggs: {next_egg}\n"
        f"🐄 Cows: {data['pets']['cow']} - Next milk: {next_milk}\n\n"
        f"💎 Total Assets: {data['ocr_wallet'] + data['ocr_bank'] + (data['pets']['hen'] * HEN_COST) + (data['pets']['cow'] * COW_COST)} 🪙"
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
    for i, (username, wealth) in enumerate(leaderboard[:10], 1):  # Top 10
        leaderboard_text += f"{i}. {username}: {wealth} 🪙\n"
    
    if not leaderboard:
        leaderboard_text = "No users found in the leaderboard yet!"
    
    await update.message.reply_text(leaderboard_text)

async def ocrdeposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    # Check if command is a reply to a message with amount
    amount = 0
    if update.message.reply_to_message and context.args and context.args[0].isdigit():
        amount = int(context.args[0])
    elif context.args and context.args[0].isdigit():
        amount = int(context.args[0])
    elif update.message.reply_to_message and update.message.reply_to_message.text:
        # Try to extract amount from replied message
        try:
            amount = int(''.join(filter(str.isdigit, update.message.reply_to_message.text)))
        except:
            pass
    
    if amount <= 0:
        await update.message.reply_text("Usage: /ocrdeposit [amount] or reply to a message with amount")
        return
        
    if amount <= data['ocr_wallet']:
        data['ocr_wallet'] -= amount
        data['ocr_bank'] += amount
        await update.message.reply_text(f"✅ Deposited {amount} OCR Coin to bank! 🏦")
    else:
        await update.message.reply_text("❌ Insufficient funds in wallet!")

async def ocrwithdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    # Check if command is a reply to a message with amount
    amount = 0
    if update.message.reply_to_message and context.args and context.args[0].isdigit():
        amount = int(context.args[0])
    elif context.args and context.args[0].isdigit():
        amount = int(context.args[0])
    elif update.message.reply_to_message and update.message.reply_to_message.text:
        # Try to extract amount from replied message
        try:
            amount = int(''.join(filter(str.isdigit, update.message.reply_to_message.text)))
        except:
            pass
    
    if amount <= 0:
        await update.message.reply_text("Usage: /ocrwithdraw [amount] or reply to a message with amount")
        return
        
    if amount <= data['ocr_bank']:
        data['ocr_bank'] -= amount
        data['ocr_wallet'] += amount
        await update.message.reply_text(f"✅ Withdrew {amount} OCR Coin from bank! 💰")
    else:
        await update.message.reply_text("❌ Insufficient funds in bank!")

async def abhi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    # Check if command is a reply to a message with amount
    amount = 0
    if update.message.reply_to_message and context.args and context.args[0].isdigit():
        amount = int(context.args[0])
    elif context.args and context.args[0].isdigit():
        amount = int(context.args[0])
    elif update.message.reply_to_message and update.message.reply_to_message.text:
        # Try to extract amount from replied message
        try:
            amount = int(''.join(filter(str.isdigit, update.message.reply_to_message.text)))
        except:
            pass
    
    if amount <= 0:
        await update.message.reply_text("Usage: /abhi [amount] or reply to a message with amount")
        return
        
    if amount <= data['ocr_wallet']:
        if random.random() < 0.5:  # 50% chance to win
            data['ocr_wallet'] += amount
            await update.message.reply_text(f"🎊 You won! {amount} OCR Coin doubled! 🪙")
        else:
            data['ocr_wallet'] -= amount
            await update.message.reply_text(f"😢 You lost {amount} OCR Coin. Better luck next time!")
    else:
        await update.message.reply_text("❌ Insufficient funds!")

async def chori_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    thief_data = get_user_data(user_id)
    
    target_user_id = None
    target_username = ""
    
    # Check if command is a reply to a message
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        target_username = update.message.reply_to_message.from_user.username or update.message.reply_to_message.from_user.first_name
    elif context.args:
        target_username = context.args[0].replace('@', '')
        # Try to find the user ID from our mapping
        target_user_id = username_to_id.get(target_username.lower())
    
    if not target_user_id:
        await update.message.reply_text("Usage: /chori [@username] or reply to a user's message")
        return
        
    if target_user_id == user_id:
        await update.message.reply_text("❌ You cannot steal from yourself!")
        return
        
    target_data = get_user_data(target_user_id)
    
    # Check if target has any coins to steal
    if target_data['ocr_wallet'] <= 0:
        await update.message.reply_text("❌ This user has no coins to steal!")
        return
    
    if target_data['shields'] > 0:
        target_data['shields'] -= 1
        await update.message.reply_text("🛡️ Target has shield! Theft blocked, but shield consumed.")
    else:
        steal_amount = min(int(target_data['ocr_wallet'] * THEFT_PERCENTAGE), target_data['ocr_wallet'])
        thief_data['ocr_wallet'] += steal_amount
        target_data['ocr_wallet'] -= steal_amount
        await update.message.reply_text(f"💰 Successfully stole {steal_amount} OCR Coin from {target_username}!")

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
        eggs_ready = "✅" if can_collect_eggs(user_id) else "⏰"
        pets_text += f"🐓 Hens: {data['pets']['hen']} {eggs_ready}\n"
    if data['pets']['cow'] > 0:
        milk_ready = "✅" if can_collect_milk(user_id) else "⏰"
        pets_text += f"🐄 Cows: {data['pets']['cow']} {milk_ready}\n"
    
    if data['pets']['hen'] == 0 and data['pets']['cow'] == 0:
        pets_text += "No pets yet! Visit /ocrmarket"
    else:
        pets_text += "\nUse /collecteggs and /collectmilk to gather resources!"
    
    await update.message.reply_text(pets_text)

async def collecteggs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if data['pets']['hen'] == 0:
        await update.message.reply_text("❌ You don't have any hens!")
        return
        
    if can_collect_eggs(user_id):
        eggs = data['pets']['hen'] * 2  # 2 eggs per hen
        value = eggs * EGG_VALUE
        data['ocr_wallet'] += value
        data['last_egg_collection'] = time.time()
        await update.message.reply_text(f"🥚 Collected {eggs} eggs worth {value} OCR Coin!")
    else:
        next_collection = data['last_egg_collection'] + EGG_COOLDOWN
        wait_time = next_collection - time.time()
        minutes = int(wait_time // 60)
        await update.message.reply_text(f"⏰ Your hens need {minutes} more minutes to produce eggs!")

async def collectmilk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_user_data(user_id)
    
    if data['pets']['cow'] == 0:
        await update.message.reply_text("❌ You don't have any cows!")
        return
        
    if can_collect_milk(user_id):
        milk = data['pets']['cow']  # 1 milk per cow
        value = milk * MILK_VALUE
        data['ocr_wallet'] += value
        data['last_milk_collection'] = time.time()
        await update.message.reply_text(f"🥛 Collected {milk} milk worth {value} OCR Coin!")
    else:
        next_collection = data['last_milk_collection'] + MILK_COOLDOWN
        wait_time = next_collection - time.time()
        hours = int(wait_time // 3600)
        minutes = int((wait_time % 3600) // 60)
        await update.message.reply_text(f"⏰ Your cows need {hours}h {minutes}m more to produce milk!")

async def abhigiveyou_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    giver_data = get_user_data(user_id)
    
    target_user_id = None
    target_username = ""
    amount = 0
    
    # Check if command is a reply to a message
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        target_username = update.message.reply_to_message.from_user.username or update.message.reply_to_message.from_user.first_name
        
        # Try to extract amount from command args
        if context.args and context.args[0].isdigit():
            amount = int(context.args[0])
        elif update.message.reply_to_message.text:
            # Try to extract amount from replied message
            try:
                amount = int(''.join(filter(str.isdigit, update.message.reply_to_message.text)))
            except:
                pass
    elif len(context.args) >= 2 and context.args[0].isdigit():
        amount = int(context.args[0])
        receiver_username = context.args[1].replace('@', '')
        # Try to find the user ID from our mapping
        target_user_id = username_to_id.get(receiver_username.lower())
        target_username = receiver_username
    
    if not target_user_id or amount <= 0:
        await update.message.reply_text("Usage: /abhigiveyou [amount] [@username] or reply to a message with amount")
        return
        
    if target_user_id == user_id:
        await update.message.reply_text("❌ You cannot send coins to yourself!")
        return
    
    if amount <= giver_data['ocr_wallet']:
        giver_data['ocr_wallet'] -= amount
        receiver_data = get_user_data(target_user_id)
        receiver_data['ocr_wallet'] += amount
        
        # Try to notify the receiver
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎁 You received {amount} OCR Coin from {update.message.from_user.first_name}!"
            )
        except:
            pass  # User might have blocked the bot or privacy settings prevent DM
            
        await update.message.reply_text(f"🎁 Gift of {amount} OCR Coin sent to {target_username}!")
    else:
        await update.message.reply_text("❌ Invalid amount or insufficient funds!")

async def abhigiveuarose_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # Check if this is the special user
    if user_id != YOUR_USER_ID:
        await update.message.reply_text("❌ This command is only for special users!")
        return
    
    target_user_id = None
    target_username = ""
    amount = 0
    
    # Check if command is a reply to a message
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        target_username = update.message.reply_to_message.from_user.username or update.message.reply_to_message.from_user.first_name
        
        # Try to extract amount from command args
        if context.args and context.args[0].isdigit():
            amount = int(context.args[0])
        elif update.message.reply_to_message.text:
            # Try to extract amount from replied message
            try:
                amount = int(''.join(filter(str.isdigit, update.message.reply_to_message.text)))
            except:
                pass
    elif len(context.args) >= 2 and context.args[0].isdigit():
        amount = int(context.args[0])
        receiver_username = context.args[1].replace('@', '')
        # Try to find the user ID from our mapping
        target_user_id = username_to_id.get(receiver_username.lower())
        target_username = receiver_username
    
    if not target_user_id or amount <= 0:
        await update.message.reply_text("Usage: /abhigiveuarose [amount] [@username] or reply to a message with amount")
        return
        
    giver_data = get_user_data(user_id)
    
    if amount <= giver_data['ocr_wallet']:
        giver_data['ocr_wallet'] -= amount
        receiver_data = get_user_data(target_user_id)
        receiver_data['ocr_wallet'] += amount
        
        # Try to notify the receiver
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🌹 You received {amount} OCR Coin as a special gift from {update.message.from_user.first_name}!"
            )
        except:
            pass  # User might have blocked the bot or privacy settings prevent DM
            
        await update.message.reply_text(f"🌹 Special gift of {amount} OCR Coin sent to {target_username}!")
    else:
        await update.message.reply_text("❌ Invalid amount or insufficient funds!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🎮 OCR Game Help:\n\n"
        "This is a fun economy game where you can earn OCR coins, buy pets, and interact with other players!\n\n"
        "📋 Available Commands:\n"
        "/ocrcoin - Claim free coins every 6 hours\n"
        "/ocrwallet - Check your balance\n"
        "/ocrinfo - Detailed info about your account\n"
        "/ocrleaderboard - Top players by wealth\n"
        "/ocrdeposit [amount] - Deposit coins to bank\n"
        "/ocrwithdraw [amount] - Withdraw coins from bank\n"
        "/abhi [amount] - Gamble your coins (50% chance to double)\n"
        "/chori [@user] - Steal coins from another player\n"
        "/buyshield - Buy protection against theft\n"
        "/ocrmarket - View available items\n"
        "/buyhen - Buy a hen that produces eggs\n"
        "/buycow - Buy a cow that produces milk\n"
        "/mypets - Check your pets status\n"
        "/collecteggs - Collect eggs from your hens\n"
        "/collectmilk - Collect milk from your cows\n"
        "/abhigiveyou [amount] [@user] - Gift coins to another player\n\n"
        "💡 Tips:\n"
        "• Use shields to protect your coins from theft\n"
        "• Hens produce eggs every 30 minutes\n"
        "• Cows produce milk every 6 hours\n"
        "• Bank your coins to keep them safe from thieves\n"
        "• Reply to messages with commands for easier use"
    )
    await update.message.reply_text(help_text)

# ==================== BLESSINGS FEATURE ====================
async def send_blessing(context: ContextTypes.DEFAULT_TYPE):
    """Send blessing message to all groups the bot is in"""
    for chat_id in context.bot_data.get('group_chats', []):
        try:
            keyboard = [[InlineKeyboardButton("Collect Blessing 🙏", callback_data=f"blessing_{int(time.time())}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = await context.bot.send_message(
                chat_id=chat_id,
                text="🕉️ Jagannath Mahaprabhu ⭕‼️⭕\n\nBlessings to all devotees!",
                reply_markup=reply_markup
            )
            
            # Store blessing data with expiration time
            blessings_data[message.message_id] = {
                'chat_id': chat_id,
                'expires': time.time() + BLESSING_DURATION
            }
        except Exception as e:
            print(f"Failed to send blessing to {chat_id}: {e}")

async def blessing_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    blessing_id = int(query.data.split('_')[1])
    
    # Check if blessing is still valid
    current_time = time.time()
    message_id = query.message.message_id
    
    if message_id in blessings_data and current_time <= blessings_data[message_id]['expires']:
        # Blessing is still valid
        data = get_user_data(user_id)
        data['ocr_wallet'] += BLESSING_REWARD
        
        await query.edit_message_text(
            f"🕉️ {user_name} received Jagannath Mahaprabhu's blessings! +{BLESSING_REWARD} OCR Coin 🪙"
        )
    else:
        # Blessing has expired
        await query.edit_message_text(
            "❌ Sorry, blessings have expired. Better luck next time!"
        )

# ==================== MESSAGE HANDLING ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # Store username to ID mapping for future reference
    user = update.message.from_user
    if user.username:
        username_to_id[user.username.lower()] = user.id

    # Store group chats for blessings
    if update.message.chat.type in ['group', 'supergroup']:
        if 'group_chats' not in context.bot_data:
            context.bot_data['group_chats'] = set()
        context.bot_data['group_chats'].add(update.message.chat.id)

    # Hindi moderation handling
    chat = update.message.chat
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
    elif query.data.startswith("blessing_"):
        await blessing_callback(update, context)

# ==================== JOB QUEUE FOR BLESSINGS ====================
async def start_blessing_job(application):
    """Start the job to send blessings every 6 hours"""
    job_queue = application.job_queue
    job_queue.run_repeating(send_blessing, interval=6*3600, first=10)

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
    app.add_handler(CommandHandler("ocrcoin", ocr
