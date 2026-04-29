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
    ConversationHandler,
)

# =========================
# BOT TOKEN
# =========================
TOKEN = os.getenv("BOT_TOKEN")

# =========================
# GOOGLE SHEETS SETUP
# =========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)

# Your Google Sheet name (MUST MATCH EXACTLY)
sheet = client.open("Police Complaints").sheet1

# =========================
# STATES
# =========================
ISSUE, LOCATION, DETAILS = range(3)

# =========================
# SAVE TO GOOGLE SHEETS
# =========================
def save_to_sheets(data):
    try:
        sheet.append_row(data)
        print("Saved to Google Sheets!")
    except Exception as e:
        print("ERROR saving to sheet:", e)

# =========================
# /start COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚓 Welcome to Police Bot\n\n"
        "Use /complaint to file a complaint.\n"
        "Use /status COMPLAINT_ID to check complaint status."
    )

# =========================
# /complaint START
# =========================
async def start_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚨 What is your issue?")
    return ISSUE

# =========================
# ISSUE
# =========================
async def get_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["issue"] = update.message.text
    await update.message.reply_text("📍 Enter location:")
    return LOCATION

# =========================
# LOCATION
# =========================
async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["location"] = update.message.text
    await update.message.reply_text("📝 Enter details:")
    return DETAILS

# =========================
# DETAILS + SAVE
# =========================
async def get_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["details"] = update.message.text

    user = update.message.from_user

    # Unique complaint ID
    complaint_id = f"CMP{user.id}{int(datetime.now().timestamp())}"

    # Default fields
    status = "Pending"
    station = "Not Assigned"
    officer = "Not Assigned"

    # Current time
    complaint_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save to Google Sheets
    save_to_sheets([
        complaint_id,
        user.first_name,
        context.user_data["issue"],
        context.user_data["location"],
        context.user_data["details"],
        status,
        station,
        officer,
        complaint_time
    ])

    # Reply to user
    await update.message.reply_text(
        f"✅ Complaint submitted!\n\n"
        f"🆔 Your Complaint ID: {complaint_id}\n\n"
        f"Use:\n/status {complaint_id}\n\nto check complaint progress."
    )

    return ConversationHandler.END

# =========================
# /status COMMAND
# Example:
/status CMP123456
# =========================
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Check if complaint ID provided
        if not context.args:
            await update.message.reply_text(
                "❌ Please use correct format:\n/status YOUR_COMPLAINT_ID"
            )
            return

        complaint_id = context.args[0].strip()

        records = sheet.get_all_records()

        for row in records:
            if str(row["Complaint ID"]).strip() == complaint_id:
                await update.message.reply_text(
                    f"🆔 Complaint ID: {complaint_id}\n"
                    f"📄 Status: {row.get('Status', 'Pending')}\n"
                    f"🏢 Station: {row.get('Station', 'Not Assigned')}\n"
                    f"👮 Officer: {row.get('Officer', 'Not Assigned')}\n"
                    f"🕒 Time: {row.get('Time', 'N/A')}"
                )
                return

        await update.message.reply_text("❌ Complaint ID not found.")

    except Exception as e:
        print("STATUS ERROR:", e)
        await update.message.reply_text("❌ Error checking complaint status.")

# =========================
# /cancel COMMAND
# =========================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Complaint cancelled.")
    return ConversationHandler.END

# =========================
# MAIN APP
# =========================
app = ApplicationBuilder().token(TOKEN).build()

# Complaint conversation
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("complaint", start_complaint)],
    states={
        ISSUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_issue)],
        LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
        DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_details)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# =========================
# HANDLERS
# =========================
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status_command))
app.add_handler(conv_handler)

# =========================
# RUN BOT
# =========================
print("Bot running...")
app.run_polling()
