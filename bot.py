import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
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
# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)

sheet = client.open("Police Complaints").sheet1

ISSUE, LOCATION, DETAILS = range(3)
def save_to_sheets(data):
    try:
        print("Connecting to Google Sheets...")

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open("PoliceComplaints").sheet1

        sheet.append_row(data)

        print("Saved to Google Sheets!")

    except Exception as e:
        print("ERROR:", e)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚓 Welcome to Police Bot\n\nUse /complaint to file a complaint."
    )

async def start_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚨 What is your issue?")
    return ISSUE

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

    complaint_id = f"CMP{user.id}{len(context.user_data)}"

    # Save to local file
    with open("complaints.txt", "a", encoding="utf-8") as f:
        f.write(f"Complaint ID: {complaint_id}\n")
        f.write(f"User: {user.first_name} | ID: {user.id}\n")
        f.write(f"Issue: {context.user_data['issue']}\n")
        f.write(f"Location: {context.user_data['location']}\n")
        f.write(f"Details: {context.user_data['details']}\n")
        f.write("-" * 40 + "\n")

    # ✅ ADD THIS EXACTLY HERE
    save_to_sheets([
        complaint_id,
        user.first_name,
        context.user_data["issue"],
        context.user_data["location"],
        context.user_data["details"]
    ])

    # Reply to user
    await update.message.reply_text(
        f"✅ Complaint submitted!\n\n🆔 Your Complaint ID: {complaint_id}"
    )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Complaint cancelled.")
    return ConversationHandler.END

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

app.add_handler(CommandHandler("start", start))
app.add_handler(conv_handler)

print("Bot running...")
app.run_polling()
