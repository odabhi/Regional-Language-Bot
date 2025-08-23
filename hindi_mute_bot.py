from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler
import asyncio
import re
import sqlite3
import time

# Your bot token
TOKEN = "8293084237:AAFIadRPQZLXbiQ0IhYDeWdaxd3nGmuzTX0"

# Database name
DB_NAME = "bot_database.db"

# Store warnings
user_warnings = {}

# Store approved users (immune to rules)
approved_users = set()

# Romanized Hindi words list
ROMAN_HINDI = ["kya", "tum", "hai", "kaise", "nahi", "kyu", "main", "aap", "hum", "ho", "raha", "kar", "mera", "tera"]

# Initialize SQLite database
def init_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS approved_users
                 (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

# Initialize the database
init_database()

# Database functions for SQLite
def add_approved_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO approved_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    approved_users.add(user_id)

def remove_approved_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM approved_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    if user_id in approved_users:
        approved_users.remove(user_id)

def load_approved_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id FROM approved_users")
    approved_users_list = [row[0] for row in c.fetchall()]
    conn.close()
    return approved_users_list

# Load approved users on startup
approved_users = set(load_approved_users())

# Detect Hindi script or Romanized Hindi
def contains_hindi(text):
    if not text:
        return False
        
    text_lower = text.lower()
    # Check Devanagari script
    if any('\u0900' <= ch <= '\u097F' for ch in text):
        return True
    # Check Romanized Hindi words
    for word in ROMAN_HINDI:
        if word in text_lower.split():
            return True
    return False

# Detect links in text
def contains_links(text):
    if not text:
        return False
        
    # Common URL patterns
    url_patterns = [
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        r't\.me/',
        r'telegram\.me/'
    ]
    
    for pattern in url_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

# Start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Hindi Moderator Bot is now active!")

# OCR command to check if bot is alive
async def ocr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Don't worry, I'm alive and 100% active! \n\n"
        "Thanks to my developer Abhishek Mohapatra for creating me. "
        "I'm working perfectly to maintain this group's language rules."
    )

# Approve user command
async def approve_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    chat = update.message.chat
    user = update.message.from_user
    user_id = user.id
    
    # Check if user is admin
    admins = await context.bot.get_chat_administrators(chat.id)
    admin_ids = [admin.user.id for admin in admins]
    
    if user_id in admin_ids:
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
            target_user_id = target_user.id
            target_user_name = target_user.first_name
            
            add_approved_user(target_user_id)
            await update.message.reply_text(
                f"✅ User {target_user_name} has been approved! "
                f"They can now use Hindi and links without restrictions."
            )
        else:
            await update.message.reply_text(
                "Please reply to a user's message with /abhiloveu to approve them."
            )
    else:
        await update.message.reply_text("❌ You need to be an admin to use this command.")

# Disapprove user command
async def disapprove_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    chat = update.message.chat
    user = update.message.from_user
    user_id = user.id
    
    # Check if user is admin
    admins = await context.bot.get_chat_administrators(chat.id)
    admin_ids = [admin.user.id for admin in admins]
    
    if user_id in admin_ids:
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
            target_user_id = target_user.id
            target_user_name = target_user.first_name
            
            if target_user_id in approved_users:
                remove_approved_user(target_user_id)
                await update.message.reply_text(
                    f"❌ User {target_user_name} has been disapproved! "
                    f"They will now be monitored for Hindi and links."
                )
            else:
                await update.message.reply_text(
                    f"User {target_user_name} was not in the approved list."
                )
        else:
            await update.message.reply_text(
                "Please reply to a user's message with /abhihateu to disapprove them."
            )
    else:
        await update.message.reply_text("❌ You need to be an admin to use this command.")

# Show approved users list
async def approved_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    if not approved_users:
        await update.message.reply_text("No users are currently approved.")
        return
        
    # Get usernames for approved users
    user_list = []
    for user_id in approved_users:
        try:
            chat_member = await context.bot.get_chat_member(update.message.chat.id, user_id)
            user_name = chat_member.user.first_name
            username = f"@{chat_member.user.username}" if chat_member.user.username else ""
            user_list.append(f"{user_name} {username} (ID: {user_id})")
        except:
            user_list.append(f"Unknown User (ID: {user_id})")
    
    user_list_text = "\n".join(user_list)
    await update.message.reply_text(
        f"✅ Approved Users List:\n\n{user_list_text}\n\n"
        f"Total: {len(approved_users)} users"
    )

# Handle messages
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

    # Check for links
    if contains_links(text):
        # Get admin IDs
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [admin.user.id for admin in admins]

        # Delete message and notify
        try:
            await update.message.delete()
        except:
            pass  # Ignore if we can't delete
        
        if user_id in admin_ids:
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"Admin {user_name} {username} message deleted. Links are not allowed."
            )
        else:
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"Message from {user_name} {username} deleted. Links are not allowed."
            )
        return

    # Check for Hindi
    if contains_hindi(text):
        # Get admin IDs
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [admin.user.id for admin in admins]

        # Admin message → delete + warn
        if user_id in admin_ids:
            try:
                await update.message.delete()
            except:
                pass
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"Admin {user_name} {username} message deleted. Please avoid Hindi text."
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
                text=f"⚠ Warning {warn_count}/3 for [{user_name}](tg://user?id={user_id}) {username}\n{chat.title} is a regional group. Please use only regional language.",
                parse_mode="Markdown"
            )
        else:
            # Mute user for 15 minutes
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=user_id,
                    permissions={"can_send_messages": False},
                    until_date=int(asyncio.get_event_loop().time()) + 900  # 15 min
                )
            except:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=f"❌ Could not mute user {user_name}. Bot needs admin permissions!"
                )
                return

            # Reset warning
            user_warnings[user_id] = 0

            # Inline button to unmute
            keyboard = [[InlineKeyboardButton("✅ Unmute", callback_data=f"unmute_{user_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=chat.id,
                text=f"🚫 [{user_name}](tg://user?id={user_id}) {username} has been muted for 15 minutes.",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

# Handle inline button callback
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("unmute_"):
        user_id = int(query.data.split("_")[1])
        chat_id = query.message.chat.id

        # Unmute user
        try:
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions={"can_send_messages": True}
            )
            await query.edit_message_text("✅ User has been unmuted by admin.")
        except:
            await query.edit_message_text("❌ Could not unmute user. Bot needs admin permissions!")

# Main function to run the bot
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ocr", ocr_command))
    app.add_handler(CommandHandler("abhiloveu", approve_user_command))
    app.add_handler(CommandHandler("abhihateu", disapprove_user_command))
    app.add_handler(CommandHandler("abhilovelist", approved_list_command))
    
    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Hindi Moderator Bot is running...")
    print("✅ Approved users loaded:", len(approved_users))
    app.run_polling()

if __name__ == "__main__":
    main()
