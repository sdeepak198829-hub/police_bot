import os
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
    print("START COMMAND RECEIVED")
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

    # Save complaint
    import uuid

with open("complaints.txt", "a", encoding="utf-8") as f:
    f.write(f"Complaint ID: {complaint_id}\n")
    f.write(f"User: {user.first_name} | ID: {user.id}\n")
    f.write(f"Issue: {context.user_data['issue']}\n")
    f.write(f"Location: {context.user_data['location']}\n")
    f.write(f"Details: {context.user_data['details']}\n")
    f.write("-" * 40 + "\n")

    await update.message.reply_text(
    f"✅ Complaint submitted!\nYour Complaint ID: {complaint_id}"
)

    return ConversationHandler.END

# Cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Complaint cancelled.")
    return ConversationHandler.END

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

print("Bot running...")
if __name__ == "__main__":
    app.run_polling(drop_pending_updates=True)
