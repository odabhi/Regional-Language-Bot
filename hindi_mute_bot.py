from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler
import asyncio
import nest_asyncio

# Fix for Pydroid / already running event loop
nest_asyncio.apply()

# Your bot token
TOKEN = "8293084237:AAFIadRPQZLXbiQ0IhYDeWdaxd3nGmuzTX0"

# Store warnings
user_warnings = {}
approved_users = set()
ROMAN_HINDI = ["kya", "tum", "hai", "kaise", "nahi", "kyu", "main", "aap", "hum", "ho", "raha", "kar", "mera", "tera"]

# Debug function
async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🔍 DEBUG: Received command: {update.message.text}")
    print(f"🔍 DEBUG: Chat type: {update.message.chat.type}")
    print(f"🔍 DEBUG: Chat ID: {update.message.chat.id}")
    await update.message.reply_text(
        "🤖 Bot Debug Info:\n\n"
        f"Command: {update.message.text}\n"
        f"Chat Type: {update.message.chat.type}\n"
        f"Chat ID: {update.message.chat.id}\n\n"
        "If you see this, commands are working!"
    )

# Start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /start command received")
    await update.message.reply_text("✅ Hindi Moderator Bot is now active!")

# OCR command
async def ocr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /ocr command received")
    await update.message.reply_text("✅ Bot is alive and working!")

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        print(f"📝 Message: {update.message.text}")
    
    # Your existing message handling code here

# --- MAIN BOT RUN ---
def main():
    print("🤖 Starting bot with debug mode...")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Register command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ocr", ocr_command))
    app.add_handler(CommandHandler("debug", debug_command))
    
    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bot started! Testing commands:")
    print("   /start - Test basic command")
    print("   /ocr - Test OCR command") 
    print("   /debug - Debug information")
    print("")
    print("📋 Please try these commands and check Termux for output")
    
    app.run_polling()

if __name__ == "__main__":
    main()
