import os
import requests
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
RAPIDAPI_KEY = "2576f146a5mshc340d75d2142a7ep1bca04jsn70ab9fb10ae7"
RAPIDAPI_HOST = "instagram-scraper-stable-api.p.rapidapi.com"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! 👋\nНадішли юзернейм Instagram (без @)\nНаприклад: cristiano"
    )

async def download_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().replace("@", "")
    await update.message.reply_text(f"⏳ Завантажую відео з @{username}...")

    try:
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "username_or_url": f"https://www.instagram.com/{username}/",
            "data": "posts",
            "amount": "10"
        }
        response = requests.post(
            f"https://{RAPIDAPI_HOST}/get_ig_user_posts_v2.php",
            headers=headers,
            data=data
        )
        posts = response.json()

        sent = 0
        for post in posts.get("posts", []):
            if post.get("is_video") and post.get("video_url"):
                video_url = post["video_url"]
                video_data = requests.get(video_url).content
                await update.message.reply_video(video_data)
                sent += 1
                if sent >= 10:
                    break

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
