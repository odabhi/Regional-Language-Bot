from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler, ConversationHandler
import asyncio
import re
import time
from pymongo import MongoClient

# Your bot token
TOKEN = "8293084237:AAFIadRPQZLXbiQ0IhYDeWdaxd3nGmuzTX0"

# Your MongoDB connection string
# Your MongoDB connection string
MONGODB_URI = "mongodb+srv://Abhi001962:prince69pass@cluster0.me9wqzi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Initialize MongoDB with better error handling
try:
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000,  # 5 second timeout
        connectTimeoutMS=30000,         # 30 second connection timeout
        socketTimeoutMS=30000           # 30 second socket timeout
    )
    # Test the connection
    client.admin.command('ping')
    db = client.hindi_bot_db
    chats_collection = db.chats
    approved_collection = db.approved_users
    warnings_collection = db.warnings
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
    print("⚠️  Using in-memory storage as fallback")
    chats_collection = None
    approved_collection = None
    warnings_collection = None

# In-memory storage as fallback
user_warnings = {}
approved_users = set()
chats_memory = []

# Your Telegram User ID (for broadcast feature)
BOT_OWNER_ID = 8144093870

# Conversation states for broadcast
BROADCAST_MESSAGE = 1

# Romanized Hindi words list
ROMAN_HINDI = ["kya", "tum", "hai", "kaise", "nahi", "kyu", "main", "aap", "hum", "ho", "raha", "kar", "mera", "tera"]

# Database functions
def add_chat_to_db(chat_id, title):
    if chats_collection:
        chats_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id, "title": title, "added_date": time.strftime("%Y-%m-%d %H:%M:%S")}},
            upsert=True
        )
    else:
        # Fallback to memory
        for chat in chats_memory:
            if chat["chat_id"] == chat_id:
                return
        chats_memory.append({"chat_id": chat_id, "title": title, "added_date": time.strftime("%Y-%m-%d %H:%M:%S")})

def get_all_chats():
    if chats_collection:
        return list(chats_collection.find({}, {"_id": 0, "chat_id": 1, "title": 1}))
    else:
        return chats_memory

def add_approved_user(user_id):
    if approved_collection:
        approved_collection.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id}},
            upsert=True
        )
    approved_users.add(user_id)

def remove_approved_user(user_id):
    if approved_collection:
        approved_collection.delete_one({"user_id": user_id})
    if user_id in approved_users:
        approved_users.remove(user_id)

def get_approved_users():
    if approved_collection:
        return [user["user_id"] for user in approved_collection.find({}, {"_id": 0, "user_id": 1})]
    return list(approved_users)

def add_warning(user_id):
    if warnings_collection:
        warnings_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"warnings": 1}},
            upsert=True
        )
    user_warnings[user_id] = user_warnings.get(user_id, 0) + 1

def get_warnings(user_id):
    if warnings_collection:
        user = warnings_collection.find_one({"user_id": user_id})
        return user["warnings"] if user else 0
    return user_warnings.get(user_id, 0)

def reset_warnings(user_id):
    if warnings_collection:
        warnings_collection.delete_one({"user_id": user_id})
    if user_id in user_warnings:
        user_warnings[user_id] = 0

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
            
            if target_user_id in get_approved_users():
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
        
    approved_users_list = get_approved_users()
    
    if not approved_users_list:
        await update.message.reply_text("No users are currently approved.")
        return
        
    # Get usernames for approved users
    user_list = []
    for user_id in approved_users_list:
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
        f"Total: {len(approved_users_list)} users"
    )

# Track when bot is added to groups
async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:  # Bot itself was added
                chat_id = update.message.chat.id
                chat_title = update.message.chat.title
                
                # Store in database
                add_chat_to_db(chat_id, chat_title)
                
                await update.message.reply_text(
                    "✅ Thanks for adding me! I'll help moderate Hindi language in this group."
                )

# Broadcast command - only for bot owner
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != BOT_OWNER_ID:
        await update.message.reply_text("❌ This command is only for bot owner.")
        return ConversationHandler.END
        
    await update.message.reply_text(
        "📢 Please send the message you want to broadcast to all groups.\n\n"
        "Type /cancel to cancel the broadcast."
    )
    return BROADCAST_MESSAGE

# Handle broadcast message
async def receive_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    broadcast_text = update.message.text
    
    # Get chats from database
    chats = get_all_chats()
    
    total_chats = len(chats)
    
    if total_chats == 0:
        await update.message.reply_text("❌ No groups found in database. Add the bot to groups first!")
        return ConversationHandler.END
    
    successful = 0
    failed = 0
    
    progress_msg = await update.message.reply_text(f"📤 Starting broadcast to {total_chats} chats...")
    
    for i, chat in enumerate(chats):
        chat_id = chat["chat_id"]
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📢 Announcement from Bot Owner:\n\n{broadcast_text}"
            )
            successful += 1
            
            # Update progress every 5 messages
            if (i + 1) % 5 == 0:
                await progress_msg.edit_text(
                    f"📤 Broadcasting... {i+1}/{total_chats} chats\n"
                    f"✅ Successful: {successful}\n"
                    f"❌ Failed: {failed}"
                )
                
        except Exception as e:
            print(f"Failed to send to chat {chat_id}: {e}")
            failed += 1
            
        await asyncio.sleep(0.3)  # Rate limiting
    
    await progress_msg.edit_text(
        f"✅ Broadcast completed!\n\n"
        f"✅ Successful: {successful}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total: {total_chats}"
    )
    return ConversationHandler.END

# Cancel broadcast
async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Broadcast cancelled.")
    return ConversationHandler.END

# Command to list all chats where bot is added
async def list_chats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != BOT_OWNER_ID:
        await update.message.reply_text("❌ This command is only for bot owner.")
        return
        
    chats = get_all_chats()
    
    if not chats:
        await update.message.reply_text("No chats found in database.")
        return
        
    message = "📋 Chats where bot is added:\n\n"
    for i, chat in enumerate(chats, 1):
        message += f"{i}. {chat.get('title', 'Unknown')} (ID: {chat['chat_id']})\n"
        message += f"   Added: {chat.get('added_date', 'Unknown')}\n\n"
    
    # Telegram has a message length limit
    if len(message) > 4096:
        for x in range(0, len(message), 4096):
            await update.message.reply_text(message[x:x+4096])
            await asyncio.sleep(1)
    else:
        await update.message.reply_text(message)

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
    if user_id in get_approved_users():
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
        warn_count = get_warnings(user_id) + 1
        add_warning(user_id)

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
            reset_warnings(user_id)

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
    app.add_handler(CommandHandler("listchats", list_chats_command))
    
    # Add broadcast conversation handler
    broadcast_handler = ConversationHandler(
        entry_points=[CommandHandler('broadcast', broadcast_command)],
        states={
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_broadcast_message)]
        },
        fallbacks=[CommandHandler('cancel', cancel_broadcast)]
    )
    app.add_handler(broadcast_handler)
    
    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_chats))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Bot is running with MongoDB and broadcast feature...")
    print("🌐 MongoDB Connected:", MONGODB_URI)
    app.run_polling()

if __name__ == "__main__":
    main()
