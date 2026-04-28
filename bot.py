import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# ---------------- TOKEN ----------------
TOKEN = os.getenv("BOT_TOKEN")

# ---------------- GOOGLE SHEETS SETUP ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)

# 👇 IMPORTANT: Your sheet name must match EXACTLY
sheet = client.open("Police Complaints").sheet1

# ---------------- STATES ----------------
ISSUE, LOCATION, DETAILS, STATUS_CHECK = range(4)

# ---------------- SAVE FUNCTION ----------------
def save_to_sheets(data):
    try:
        sheet.append_row(data)
        print("Saved to Google Sheets!")
    except Exception as e:
        print("ERROR saving to sheet:", e)

# ---------------- BOT COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚓 Welcome to Police Bot\n\nUse /complaint to file a complaint."
    )

async def start_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚨 What is your issue?")
    return ISSUE
async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📄 Enter your Complaint ID:")
    return STATUS_CHECK
async def get_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["issue"] = update.message.text
    await update.message.reply_text("📍 Enter location:")
    return LOCATION

async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["location"] = update.message.text
    await update.message.reply_text("📝 Enter details:")
    return DETAILS

async def get_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["details"] = update.message.text

    user = update.message.from_user

    complaint_id = f"CMP{user.id}"
async def get_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    complaint_id = update.message.text.strip()

    records = sheet.get_all_records()

    for row in records:
        if row["Complaint ID"] == complaint_id:
            await update.message.reply_text(
                f"📄 Status: {row['Status']}\n"
                f"🏢 Station: {row['Station']}\n"
                f"👮 Officer: {row['Officer']}"
            )
            return ConversationHandler.END

    await update.message.reply_text("❌ Complaint ID not found.")
    return ConversationHandler.END
    # Save to Google Sheets
    save_to_sheets([
        complaint_id,
        user.first_name,
        context.user_data["issue"],
        context.user_data["location"],
        context.user_data["details"]
    ])

    await update.message.reply_text(
        f"✅ Complaint submitted!\n\n🆔 Your Complaint ID: {complaint_id}"
    )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Complaint cancelled.")
    return ConversationHandler.END

# ---------------- MAIN APP ----------------
app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("complaint", start_complaint)],
    states={
        ISSUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_issue)],
        LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
        DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_details)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

status_handler = ConversationHandler(
    entry_points=[CommandHandler("status", check_status)],
    states={
        STATUS_CHECK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_status)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(CommandHandler("start", start))
app.add_handler(conv_handler)
app.add_handler(status_handler)

print("Bot running...")
app.run_polling()
