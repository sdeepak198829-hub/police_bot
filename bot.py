import os
import uuid
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

TOKEN = os.getenv("BOT_TOKEN")

# Steps
ISSUE, LOCATION, DETAILS = range(3)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚓 Welcome to Police Bot\n\nUse /complaint to file a complaint."
    )

# Start complaint
async def start_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚨 What is your issue?")
    return ISSUE

# Step 1
async def get_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["issue"] = update.message.text
    await update.message.reply_text("📍 Enter location:")
    return LOCATION

# Step 2
async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["location"] = update.message.text
    await update.message.reply_text("📝 Enter details:")
    return DETAILS

# Step 3 (Final)
async def get_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["details"] = update.message.text

    user = update.message.from_user

    # Generate Complaint ID
    complaint_id = str(uuid.uuid4())[:8]

    # Save complaint
    with open("complaints.txt", "a", encoding="utf-8") as f:
        f.write(f"Complaint ID: {complaint_id}\n")
        f.write(f"User: {user.first_name} | ID: {user.id}\n")
        f.write(f"Issue: {context.user_data['issue']}\n")
        f.write(f"Location: {context.user_data['location']}\n")
        f.write(f"Details: {context.user_data['details']}\n")
        f.write("Status: Pending\n")
        f.write("-" * 40 + "\n")

    await update.message.reply_text(
        f"✅ Complaint submitted!\nYour Complaint ID: {complaint_id}"
    )

    return ConversationHandler.END

# Cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Complaint cancelled.")
    return ConversationHandler.END

# Check status
async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        complaint_id = context.args[0]
    except:
        await update.message.reply_text("❌ Usage: /status <complaint_id>")
        return

    try:
        with open("complaints.txt", "r", encoding="utf-8") as f:
            data = f.read()

        if complaint_id in data:
            await update.message.reply_text(
                f"📄 Complaint {complaint_id} found.\nStatus: Pending"
            )
        else:
            await update.message.reply_text("❌ Complaint not found.")

    except:
        await update.message.reply_text("Error checking complaint.")

# Main app
app = ApplicationBuilder().token(TOKEN).build()

# Conversation handler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("complaint", start_complaint)],
    states={
        ISSUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_issue)],
        LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
        DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_details)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# Add handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(conv_handler)
app.add_handler(CommandHandler("status", check_status))

print("Bot running...")

# Run bot safely (prevents conflict issues)
if __name__ == "__main__":
    import asyncio
from telegram.ext import Application

PORT = int(os.environ.get("PORT", 8000))
WEBHOOK_URL = os.environ.get("RAILWAY_STATIC_URL")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("status", check_status))

    await app.initialize()
    await app.start()

    await app.bot.set_webhook(url=f"{WEBHOOK_URL}")

    print("Webhook set. Bot running...")

    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    asyncio.run(main())
