from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler
import asyncio
import nest_asyncio
import re

# Fix for Pydroid / already running event loop
nest_asyncio.apply()

# Your bot token
TOKEN = "8293084237:AAFIadRPQZLXbiQ0IhYDeWdaxd3nGmuzTX0"

# Store warnings
user_warnings = {}
approved_users = set()
whitelisted_words = set()  # New: Store whitelisted words
detected_hindi_words = {}  # New: Store detected Hindi words for review

# Romanized Hindi words list
ROMAN_HINDI = ["kya", "tum", "hai", "kaise", "nahi", "kyu", "main", "aap", "hum", "ho", "raha", "kar", "mera", "tera"]

# Detect Hindi script or Romanized Hindi
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
        # Skip if word is whitelisted
        if word in whitelisted_words:
            continue
            
        if word in ROMAN_HINDI:
            detected_words.append(word)
    
    return len(detected_words) > 0, detected_words

# Start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Hindi Moderator Bot is now active!")

# OCR command
async def ocr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive and working!")

# Show detected words command
async def show_detected_words_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not detected_hindi_words:
        await update.message.reply_text("📝 No Hindi words detected yet.")
        return
    
    message = "📋 Detected Hindi Words:\n\n"
    for word, count in detected_hindi_words.items():
        message += f"• {word} (detected {count} times)\n"
    
    message += "\n👮 Admins can whitelist words using /whitelist [word]"
    await update.message.reply_text(message)

# Whitelist word command
async def whitelist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    # Check if user is admin
    chat = update.message.chat
    user = update.message.from_user
    user_id = user.id
    
    admins = await context.bot.get_chat_administrators(chat.id)
    admin_ids = [admin.user.id for admin in admins]
    
    if user_id not in admin_ids:
        await update.message.reply_text("❌ Only admins can whitelist words.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /whitelist [word]")
        return
    
    word = context.args[0].lower()
    whitelisted_words.add(word)
    
    # Remove from detected words if it was there
    if word in detected_hindi_words:
        del detected_hindi_words[word]
    
    await update.message.reply_text(f"✅ Word '{word}' has been whitelisted!")

# Show whitelisted words command
async def show_whitelist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not whitelisted_words:
        await update.message.reply_text("📝 No words whitelisted yet.")
        return
    
    message = "✅ Whitelisted Words:\n\n"
    for word in whitelisted_words:
        message += f"• {word}\n"
    
    message += "\n❌ Use /unwhitelist [word] to remove from whitelist"
    await update.message.reply_text(message)

# Unwhitelist word command
async def unwhitelist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    # Check if user is admin
    chat = update.message.chat
    user = update.message.from_user
    user_id = user.id
    
    admins = await context.bot.get_chat_administrators(chat.id)
    admin_ids = [admin.user.id for admin in admins]
    
    if user_id not in admin_ids:
        await update.message.reply_text("❌ Only admins can unwhitelist words.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /unwhitelist [word]")
        return
    
    word = context.args[0].lower()
    if word in whitelisted_words:
        whitelisted_words.remove(word)
        await update.message.reply_text(f"✅ Word '{word}' removed from whitelist!")
    else:
        await update.message.reply_text(f"❌ Word '{word}' is not in whitelist.")

# Handle messages with enhanced detection
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat = update.message.chat
    user = update.message.from_user
    user_id = user.id
    user_name = user.first_name
    username = f"@{user.username}" if user.username else ""
    text = update.message.text or ""

    # Check if user is approved (immune to rules)
    if user_id in approved_users:
        return  # Skip moderation for approved users

    # Detect Hindi with detailed information
    has_hindi, detected_words = contains_hindi(text)
    
    if has_hindi:
        # Track detected words
        for word in detected_words:
            detected_hindi_words[word] = detected_hindi_words.get(word, 0) + 1
        
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
            # Create inline keyboard for whitelisting
            keyboard = []
            for word in detected_words:
                if word not in whitelisted_words:
                    keyboard.append([InlineKeyboardButton(f"✅ Whitelist '{word}'", callback_data=f"whitelist_{word}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"⚠ Warning {warn_count}/3 for [{user_name}](tg://user?id={user_id}) {username}\n"
                     f"Detected Hindi words: {', '.join(detected_words)}\n"
                     f"{chat.title} is a regional group. Please use only regional language.",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        else:
            # Mute user for 15 minutes
            await context.bot.restrict_chat_member(
                chat_id=chat.id,
                user_id=user_id,
                permissions={"can_send_messages": False},
                until_date=int(asyncio.get_event_loop().time()) + 900  # 15 min
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

# Handle inline button callbacks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat.id

    # Check if user is admin
    admins = await context.bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in admins]
    
    if user_id not in admin_ids:
        await query.edit_message_text("❌ Only admins can whitelist words.")
        return

    if query.data.startswith("whitelist_"):
        word = query.data.split("_", 1)[1]
        whitelisted_words.add(word)
        
        # Remove from detected words
        if word in detected_hindi_words:
            del detected_hindi_words[word]
        
        await query.edit_message_text(f"✅ Word '{word}' has been whitelisted by admin!")

    elif query.data.startswith("unmute_"):
        user_id_to_unmute = int(query.data.split("_")[1])
        
        # Unmute user
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id_to_unmute,
            permissions={"can_send_messages": True}
        )

        await query.edit_message_text("✅ User has been unmuted by admin.")

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 Hindi Moderator Bot Commands:

👮 Admin Commands:
/whitelist [word] - Whitelist a Hindi word
/unwhitelist [word] - Remove word from whitelist  
/showwhitelist - Show all whitelisted words
/showdetected - Show detected Hindi words

👥 User Commands:
/start - Start the bot
/ocr - Check if bot is alive
/help - Show this help message

🔧 Features:
- Auto-detects Hindi words
- Warns users (3 warnings = 15min mute)
- Admins can whitelist words
- Word usage tracking
"""
    await update.message.reply_text(help_text)

# --- MAIN BOT RUN ---
def main():
    print("🤖 Starting Enhanced Hindi Bot...")
    print("📝 New Features: Word detection tracking & whitelisting")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Register command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ocr", ocr_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("whitelist", whitelist_command))
    app.add_handler(CommandHandler("unwhitelist", unwhitelist_command))
    app.add_handler(CommandHandler("showwhitelist", show_whitelist_command))
    app.add_handler(CommandHandler("showdetected", show_detected_words_command))
    
    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Bot started with new features!")
    print("📋 New commands available:")
    print("   /whitelist [word] - Whitelist a word")
    print("   /unwhitelist [word] - Remove from whitelist")
    print("   /showwhitelist - Show whitelisted words")
    print("   /showdetected - Show detected Hindi words")
    print("   /help - Show all commands")
    
    app.run_polling()

if __name__ == "__main__":
    main()
