from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8616569156:AAH0o8yrFXnNshadmNWlx4ewGYvdFIbUjf4"

# Dictionary to store user data temporarily
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {}
    await update.message.reply_text("Welcome to Complaint Bot\n\nEnter your Name:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_data:
        await update.message.reply_text("Type /start to begin")
        return

    user = user_data[user_id]

    if "name" not in user:
        user["name"] = text
        await update.message.reply_text("Enter your Phone Number:")
    
    elif "phone" not in user:
        user["phone"] = text
        await update.message.reply_text("Enter your Complaint:")
    
    elif "complaint" not in user:
        user["complaint"] = text
        
        await update.message.reply_text(
            f"Complaint Registered ✅\n\n"
            f"Name: {user['name']}\n"
            f"Phone: {user['phone']}\n"
            f"Complaint: {user['complaint']}"
        )

        # Reset after submission
        user_data.pop(user_id)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle_message))

print("Bot running...")
app.run_polling()

