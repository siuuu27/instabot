import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
RAPIDAPI_KEY = "2576f146a5mshc340d75d2142a7ep1bca04jsn70ab9fb10ae7"
RAPIDAPI_HOST = "instagram-scraper-stable-api.p.rapidapi.com"

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! 👋\nНадішли юзернейм Instagram (без @)\nНаприклад: cristiano"
    )

async def get_posts(username, pagination_token=None):
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"username_or_url": f"https://www.instagram.com/{username}/"}
    if pagination_token:
        data["pagination_token"] = pagination_token

    response = requests.post(
        f"https://{RAPIDAPI_HOST}/get_ig_user_posts.php",
        headers=headers,
        data=data
    )
    result = response.json()
    posts = result.get("posts", [])
    next_token = result.get("pagination_token", None)

    videos = []
    for post in posts:
        node = post.get("node", {})
        video_versions = node.get("video_versions", [])
        if video_versions:
            videos.append(video_versions[0]["url"])

    return videos, next_token

async def send_videos(chat_id, context, update=None):
    data = user_data.get(chat_id, {})
    videos = data.get("videos", [])
    index = data.get("index", 0)

    batch = videos[index:index + 10]

    if not batch:
        # Спробуємо завантажити ще
        username = data.get("username")
        pagination_token = data.get("pagination_token")
        if pagination_token:
            new_videos, new_token = await get_posts(username, pagination_token)
            user_data[chat_id]["videos"].extend(new_videos)
            user_data[chat_id]["pagination_token"] = new_token
            batch = user_data[chat_id]["videos"][index:index + 10]

    if not batch:
        await context.bot.send_message(chat_id=chat_id, text="✅ Всі відео надіслано!")
        return

    sent = 0
    for url in batch:
        video_data = requests.get(url).content
        await context.bot.send_video(chat_id=chat_id, video=video_data)
        sent += 1

    user_data[chat_id]["index"] = index + sent
    total = len(user_data[chat_id]["videos"])
    new_index = user_data[chat_id]["index"]
    has_more = user_data[chat_id].get("pagination_token") or new_index < total

    if has_more:
        keyboard = [[InlineKeyboardButton(f"Наступні 10 ▶️", callback_data="next")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=chat_id, text=f"✅ Надіслано {sent} відео!", reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=chat_id, text=f"✅ Всі відео надіслано!")

async def download_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().replace("@", "")
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"⏳ Завантажую відео з @{username}...")

    try:
        videos, pagination_token = await get_posts(username)
        if not videos:
            await update.message.reply_text("❌ Відео не знайдено або акаунт приватний")
            return

        user_data[chat_id] = {
            "videos": videos,
            "index": 0,
            "username": username,
            "pagination_token": pagination_token
        }
        await update.message.reply_text(f"📊 Знайдено {len(videos)}+ відео. Надсилаю перші 10...")
        await send_videos(chat_id, context, update)

    except Exception as e:
        await update.message.reply_text(f"❌ Помилка: {str(e)}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    await query.edit_message_text("⏳ Надсилаю наступні відео...")
    await send_videos(chat_id, context)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_videos))
app.add_handler(CallbackQueryHandler(button_handler))
app.run_polling()
