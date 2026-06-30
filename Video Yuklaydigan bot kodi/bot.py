import os
import logging
import asyncio
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from database import Database

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",")]

db = Database("bot_data.db")


# ─────────────────────────────────────────────
# YORDAMCHI FUNKSIYALAR
# ─────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> list:
    """Foydalanuvchi obuna bo'lmagan kanallarni qaytaradi"""
    channels = db.get_channels()
    not_subscribed = []
    for channel in channels:
        try:
            member = await context.bot.get_chat_member(channel["channel_id"], user_id)
            if member.status in [ChatMember.LEFT, ChatMember.BANNED]:
                not_subscribed.append(channel)
        except Exception:
            not_subscribed.append(channel)
    return not_subscribed


def get_subscription_keyboard(not_subscribed: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in not_subscribed:
        buttons.append([InlineKeyboardButton(
            text=f"📢 {ch['channel_name']}",
            url=ch["channel_link"]
        )])
    buttons.append([InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(buttons)


# ─────────────────────────────────────────────
# ASOSIY KOMANDALAR
# ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username or "", user.full_name or "")

    not_subscribed = await check_subscription(user.id, context)
    if not_subscribed:
        await update.message.reply_text(
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
            reply_markup=get_subscription_keyboard(not_subscribed)
        )
        return

    await update.message.reply_text(
        f"👋 Salom, <b>{user.first_name}</b>!\n\n"
        "🎬 Menga video linkini yuboring, men uni yuklab beraman.\n\n"
        "<b>Qo'llab-quvvatlanadigan saytlar:</b>\n"
        "• YouTube\n• TikTok\n• Instagram\n• Twitter/X\n• Facebook\n"
        "• VK va 1000+ boshqa saytlar\n\n"
        "📎 Linkni yuboring va videoni oling!",
        parse_mode="HTML"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ <b>Yordam</b>\n\n"
        "• Video linkini yuboring — bot yuklab beradi\n"
        "• /start — Botni qayta ishga tushirish\n"
        "• /help — Yordam\n\n"
        "Admin: /admin",
        parse_mode="HTML"
    )


# ─────────────────────────────────────────────
# VIDEO YUKLAB OLISH
# ─────────────────────────────────────────────

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    url = update.message.text.strip()

    # Obuna tekshirish
    not_subscribed = await check_subscription(user.id, context)
    if not_subscribed:
        await update.message.reply_text(
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
            reply_markup=get_subscription_keyboard(not_subscribed)
        )
        return

    # URL ekanligini tekshirish
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("❌ Iltimos, to'g'ri link yuboring (http:// yoki https:// bilan boshlangan).")
        return

    status_msg = await update.message.reply_text("⏳ Video yuklanmoqda, iltimos kuting...")

    output_path = f"downloads/{user.id}_video.mp4"
    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        "outtmpl": output_path,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "max_filesize": 50 * 1024 * 1024,  # 50 MB limit (Telegram limit)
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: _download(url, ydl_opts))

        await status_msg.edit_text("📤 Video yuborilmoqda...")

        with open(output_path, "rb") as video_file:
            await update.message.reply_video(
                video=video_file,
                caption="✅ Mana sizning videongiz!\n\n🤖 @YourBotUsername",
                supports_streaming=True
            )
        await status_msg.delete()

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Download error: {error_msg}")
        if "File is larger than max-filesize" in error_msg:
            await status_msg.edit_text("❌ Video hajmi 50 MB dan katta. Telegram cheklovi sababli yuborib bo'lmaydi.")
        elif "Unsupported URL" in error_msg:
            await status_msg.edit_text("❌ Bu link qo'llab-quvvatlanmaydi. Iltimos, boshqa link kiriting.")
        else:
            await status_msg.edit_text("❌ Video yuklab bo'lmadi. Link to'g'ri ekanligini tekshiring.")
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def _download(url: str, opts: dict):
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])


# ─────────────────────────────────────────────
# OBUNA TEKSHIRISH CALLBACK
# ─────────────────────────────────────────────

async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    not_subscribed = await check_subscription(user.id, context)
    if not_subscribed:
        await query.edit_message_text(
            "❌ Siz hali barcha kanallarga obuna bo'lmadingiz!\n\nObuna bo'lib, qayta tekshiring:",
            reply_markup=get_subscription_keyboard(not_subscribed)
        )
    else:
        await query.edit_message_text(
            "✅ Rahmat! Endi botdan foydalanishingiz mumkin.\n\n"
            "🎬 Video linkini yuboring!"
        )


# ─────────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────────

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return

    stats = db.get_stats()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Broadcast yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton("➕ Kanal qo'shish", callback_data="admin_add_channel")],
        [InlineKeyboardButton("📋 Kanallar ro'yxati", callback_data="admin_list_channels")],
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
    ])

    await update.message.reply_text(
        f"🔧 <b>Admin Panel</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n"
        f"📢 Kanallar soni: <b>{stats['total_channels']}</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ Siz admin emassiz!")
        return

    data = query.data

    if data == "admin_stats":
        stats = db.get_stats()
        await query.edit_message_text(
            f"📊 <b>Statistika</b>\n\n"
            f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n"
            f"📢 Kanallar soni: <b>{stats['total_channels']}</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")
            ]])
        )

    elif data == "admin_broadcast":
        context.user_data["state"] = "waiting_broadcast"
        await query.edit_message_text(
            "📢 <b>Broadcast</b>\n\nBarcha foydalanuvchilarga yuboriladigan xabarni yozing:\n\n"
            "(Matn, rasm yoki video yuborish mumkin)\n\n"
            "Bekor qilish: /cancel",
            parse_mode="HTML"
        )

    elif data == "admin_add_channel":
        context.user_data["state"] = "waiting_channel"
        await query.edit_message_text(
            "➕ <b>Kanal qo'shish</b>\n\n"
            "Quyidagi formatda yuboring:\n"
            "<code>@kanalusername | Kanal nomi | https://t.me/kanalusername</code>\n\n"
            "Misol:\n"
            "<code>@mychannel | Mening kanalim | https://t.me/mychannel</code>\n\n"
            "Bekor qilish: /cancel",
            parse_mode="HTML"
        )

    elif data == "admin_list_channels":
        channels = db.get_channels()
        if not channels:
            text = "📋 Hozircha hech qanday kanal qo'shilmagan."
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]])
        else:
            text = "📋 <b>Qo'shilgan kanallar:</b>\n\n"
            buttons = []
            for ch in channels:
                text += f"• {ch['channel_name']} ({ch['channel_id']})\n"
                buttons.append([InlineKeyboardButton(
                    f"🗑 {ch['channel_name']} ni o'chirish",
                    callback_data=f"del_channel_{ch['id']}"
                )])
            buttons.append([InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")])
            keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)

    elif data.startswith("del_channel_"):
        channel_db_id = int(data.replace("del_channel_", ""))
        db.remove_channel(channel_db_id)
        await query.edit_message_text(
            "✅ Kanal o'chirildi!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_back")
            ]])
        )

    elif data == "admin_back":
        stats = db.get_stats()
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Broadcast yuborish", callback_data="admin_broadcast")],
            [InlineKeyboardButton("➕ Kanal qo'shish", callback_data="admin_add_channel")],
            [InlineKeyboardButton("📋 Kanallar ro'yxati", callback_data="admin_list_channels")],
            [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        ])
        await query.edit_message_text(
            f"🔧 <b>Admin Panel</b>\n\n"
            f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n"
            f"📢 Kanallar soni: <b>{stats['total_channels']}</b>",
            parse_mode="HTML",
            reply_markup=keyboard
        )


async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin holatiga qarab kiritilgan ma'lumotni qayta ishlash"""
    if not is_admin(update.effective_user.id):
        return

    state = context.user_data.get("state")

    if state == "waiting_channel":
        text = update.message.text.strip()
        parts = [p.strip() for p in text.split("|")]
        if len(parts) != 3:
            await update.message.reply_text(
                "❌ Format noto'g'ri! Quyidagi formatda kiriting:\n"
                "<code>@kanalusername | Kanal nomi | https://t.me/kanalusername</code>",
                parse_mode="HTML"
            )
            return

        channel_id, channel_name, channel_link = parts
        db.add_channel(channel_id, channel_name, channel_link)
        context.user_data["state"] = None
        await update.message.reply_text(
            f"✅ Kanal muvaffaqiyatli qo'shildi!\n\n"
            f"📢 Nom: {channel_name}\n"
            f"🔗 ID: {channel_id}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_back")
            ]])
        )

    elif state == "waiting_broadcast":
        users = db.get_all_users()
        success = 0
        failed = 0

        status_msg = await update.message.reply_text(f"📤 Xabar yuborilmoqda... 0/{len(users)}")

        for i, user in enumerate(users):
            try:
                await context.bot.copy_message(
                    chat_id=user["user_id"],
                    from_chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )
                success += 1
            except Exception:
                failed += 1

            if (i + 1) % 20 == 0:
                try:
                    await status_msg.edit_text(f"📤 Xabar yuborilmoqda... {i+1}/{len(users)}")
                except Exception:
                    pass
            await asyncio.sleep(0.05)

        context.user_data["state"] = None
        await status_msg.edit_text(
            f"✅ Broadcast yakunlandi!\n\n"
            f"✔️ Muvaffaqiyatli: {success}\n"
            f"❌ Xatolik: {failed}"
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["state"] = None
    await update.message.reply_text("❌ Bekor qilindi.")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Komandalar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("cancel", cancel))

    # Callback
    app.add_handler(CallbackQueryHandler(check_sub_callback, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^del_channel_"))

    # Matn xabarlari
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_IDS),
        handle_admin_input_or_link
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_link
    ))

    logger.info("Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)


async def handle_admin_input_or_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin uchun: holatga qarab admin inputni yoki link ni qayta ishlash"""
    state = context.user_data.get("state")
    if state in ("waiting_channel", "waiting_broadcast"):
        await handle_admin_input(update, context)
    else:
        await handle_link(update, context)


if __name__ == "__main__":
    main()
