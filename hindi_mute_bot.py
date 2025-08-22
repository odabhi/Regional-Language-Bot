from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import asyncio
import nest_asyncio

# Fix for Pydroid / already running event loop
nest_asyncio.apply()

# Your bot token
TOKEN = "8293084237:AAFIadRPQZLXbiQ0IhYDeWdaxd3nGmuzTX0"

# Store warnings
user_warnings = {}

# Romanized Hindi words list
ROMAN_HINDI = ["kya", "tum", "hai", "kaise", "nahi", "kyu", "main", "aap", "hum", "ho", "raha", "kar", "mera", "tera"]

# Detect Hindi script or Romanized Hindi
def contains_hindi(text):
    text_lower = text.lower()
    # Check Devanagari script
    if any('\u0900' <= ch <= '\u097F' for ch in text):
        return True
    # Check Romanized Hindi words
    for word in ROMAN_HINDI:
        if word in text_lower.split():
            return True
    return False

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

    if contains_hindi(text):
        # Get admin IDs
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [admin.user.id for admin in admins]

        # Admin message → delete + warn
        if user_id in admin_ids:
            await update.message.delete()
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
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions={"can_send_messages": True}
        )

        await query.edit_message_text("✅ User has been unmuted by admin.")

# --- MAIN BOT RUN ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Bot is running...")

    # Run polling safely in Pydroid / already running loop
    loop = asyncio.get_event_loop()
    loop.create_task(app.run_polling())
