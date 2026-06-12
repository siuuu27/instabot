import os
import instaloader
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = "7554272410:AAGF2nKQ89C5OU3ePo86yGduj2ZVumZKpMQ"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! 👋\nНадішли юзернейм Instagram (без @)\nНаприклад: cristiano"
    )

async def download_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().replace("@", "")
    await update.message.reply_text(f"⏳ Завантажую відео з @{username}...")

    L = instaloader.Instaloader(
        download_pictures=False,
        download_video_thumbnails=False,
        save_metadata=False,
        post_metadata_txt_pattern=""
    )

    try:
        profile = instaloader.Profile.from_username(L.context, username)
        os.makedirs(f"downloads/{username}", exist_ok=True)
        count = 0

        for post in profile.get_posts():
            if post.is_video:
                L.download_post(post, target=f"downloads/{username}")
                count += 1
                if count >= 10:
                    break

        folder = f"downloads/{username}"
        sent = 0
        for file in os.listdir(folder):
            if file.endswith(".mp4"):
                with open(f"{folder}/{file}", "rb") as video:
                    await update.message.reply_video(video)
                    sent += 1

        if sent == 0:
            await update.message.reply_text("❌ Відео не знайдено або акаунт приватний")
        else:
            await update.message.reply_text(f"✅ Готово! Надіслано {sent} відео!")

    except Exception as e:
        await update.message.reply_text(f"❌ Помилка: {str(e)}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_videos))
app.run_polling()
