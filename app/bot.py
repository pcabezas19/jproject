from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from .handlers import start, info, set_hoja_handler, handle_message
from .config import BOT_TOKEN

def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("hoja", set_hoja_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot corriendo...")
    app.run_polling()
