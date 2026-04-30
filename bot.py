import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
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
ISSUE, STATION, LOCATION, DETAILS, PHONE = range(5)

# =========================
# POLICE STATION LIST
# =========================
POLICE_STATIONS = [
    ["Boko PS", "Goroimari PS"],
    ["Nagarbera PS", "Chaygaon PS"],
    ["Palashbari PS", "North-Guwahati PS"],
    ["Changsari PS", "Hajo PS"],
    ["Sualkuchi PS", "Sualkuchi River PS"],
    ["Baihata Chariali PS", "Kamalpur PS"],
    ["Rangia PS", "Koya PS"]
]

# Flat list for validation
VALID_STATIONS = [
    "Boko PS", "Goroimari PS",
    "Nagarbera PS", "Chaygaon PS",
    "Palashbari PS", "North-Guwahati PS",
    "Changsari PS", "Hajo PS",
    "Sualkuchi PS", "Sualkuchi River PS",
    "Baihata Chariali PS", "Kamalpur PS",
    "Rangia PS", "Koya PS"
]

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
    context.user_data.clear()

    await update.message.reply_text(
        "🚨 What is your issue?",
        reply_markup=ReplyKeyboardRemove()
    )

    return ISSUE


# =========================
# ISSUE
# =========================
async def get_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        await update.message.reply_text("❌ Please type your issue.")
        return ISSUE

    context.user_data["issue"] = update.message.text

    reply_markup = ReplyKeyboardMarkup(
        POLICE_STATIONS,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await update.message.reply_text(
        "🏢 Select Concerned Police Station:",
        reply_markup=reply_markup
    )

    return STATION


# =========================
# STATION
# =========================
async def get_station(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        await update.message.reply_text("❌ Please select a police station.")
        return STATION

    selected_station = update.message.text.strip()

    if selected_station not in VALID_STATIONS:
        await update.message.reply_text("❌ Please select a valid police station from the keyboard.")
        return STATION

    context.user_data["selected_station"] = selected_station

    await update.message.reply_text(
        "📍 Enter exact place of occurrence:",
        reply_markup=ReplyKeyboardRemove()
    )

    return LOCATION


# =========================
# LOCATION
# =========================
async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        await update.message.reply_text("❌ Please type location.")
        return LOCATION

    context.user_data["location"] = update.message.text

    await update.message.reply_text("📝 Enter details:")
    return DETAILS


# =========================
# DETAILS
# =========================
async def get_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        await update.message.reply_text("❌ Please type complaint details.")
        return DETAILS

    context.user_data["details"] = update.message.text

    contact_button = KeyboardButton(
        text="📞 Share Phone Number",
        request_contact=True
    )

    reply_markup = ReplyKeyboardMarkup(
        [[contact_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await update.message.reply_text(
        "📱 Please share your phone number using the button below:",
        reply_markup=reply_markup
    )

    return PHONE


# =========================
# PHONE + FINAL SAVE
# =========================
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.contact:
            await update.message.reply_text(
                "❌ Please use the '📞 Share Phone Number' button."
            )
            return PHONE

        user = update.message.from_user
        phone_number = update.message.contact.phone_number

        # Unique complaint ID
        complaint_id = f"CMP{user.id}{int(datetime.now().timestamp())}"

        # Default fields
        status = "Pending"
        assigned_station = context.user_data.get("selected_station", "Not Assigned")
        officer = "Not Assigned"

        # Current time
        complaint_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Google Sheet Column Order:
        # Complaint ID | Name | Telegram ID | Phone | Police Station | Issue | Location | Details | Status | Station | Officer | Time
        save_to_sheets([
            complaint_id,
            user.first_name,
            user.id,
            phone_number,
            context.user_data.get("selected_station", ""),
            context.user_data.get("issue", ""),
            context.user_data.get("location", ""),
            context.user_data.get("details", ""),
            status,
            assigned_station,
            officer,
            complaint_time
        ])

        await update.message.reply_text(
            f"✅ Complaint submitted successfully!\n\n"
            f"🆔 Your Complaint ID: {complaint_id}\n"
            f"🏢 Police Station: {context.user_data.get('selected_station', '')}\n"
            f"🕒 Time: {complaint_time}\n\n"
            f"NB:- Information about a cognizable offence can be given electronically, but it must be signed within three days to be formally taken on record.\n\n"
            f"Use:\n/status {complaint_id}\n\nto check complaint progress.",
            reply_markup=ReplyKeyboardRemove()
        )

        context.user_data.clear()

        return ConversationHandler.END

    except Exception as e:
        print("PHONE SAVE ERROR:", e)

        await update.message.reply_text(
            "❌ Error submitting complaint.",
            reply_markup=ReplyKeyboardRemove()
        )

        return ConversationHandler.END


# =========================
# /status COMMAND
# =========================
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
                    f"🏢 Selected PS: {row.get('Police Station', 'N/A')}\n"
                    f"📄 Status: {row.get('Status', 'Pending')}\n"
                    f"🏛 Assigned Station: {row.get('Station', 'Not Assigned')}\n"
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
    context.user_data.clear()

    await update.message.reply_text(
        "❌ Complaint cancelled.",
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


# =========================
# MAIN APP
# =========================
app = ApplicationBuilder().token(TOKEN).build()


# =========================
# COMPLAINT CONVERSATION
# =========================
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("complaint", start_complaint)],
    states={
        ISSUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_issue)],
        STATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_station)],
        LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
        DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_details)],
        PHONE: [
            MessageHandler(filters.CONTACT, get_phone),
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True,
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
app.run_polling(drop_pending_updates=True)
