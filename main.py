import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# Import handlers from our modules
from handlers.basic import start_command, help_command
from handlers.network import (
    lookup_command, nmap_command, rustscan_command, headers_command, 
    methods_command, revip_command
)
from handlers.data import (
    base64_command, base64_button_handler, md5_command, urlencode_command, 
    urldecode_command, breach_command, cms_command, analyse_command, extract_command
)
from utils import BOT_VERSION

# --- IMPORTANT: PASTE YOUR REAL BOT TOKEN HERE ---
BOT_TOKEN = "7769276879:AAE0nH5jYEYnKMyYFVv3n0JCLgqnL2yuNPU"

def main() -> None:
    """Sets up and runs the bot."""
    if not BOT_TOKEN or "YOUR_BOT_TOKEN" in BOT_TOKEN:
        logging.error("CRITICAL: BOT_TOKEN is not set in main.py. Please get one from @BotFather.")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register all command and callback handlers
    handlers = [
        # Basic handlers
        CommandHandler("start", start_command),
        CommandHandler("help", help_command),

        # Network handlers from network.py
        CommandHandler("lookup", lookup_command),
        CommandHandler("nmap", nmap_command),
        CommandHandler("rustscan", rustscan_command),
        CommandHandler("headers", headers_command),
        CommandHandler("methods", methods_command),
        CommandHandler("revip", revip_command),

        # Data handlers from data.py
        CommandHandler("base64", base64_command),
        CallbackQueryHandler(base64_button_handler, pattern="^b64_"),
        CommandHandler("md5", md5_command),
        CommandHandler("urlencode", urlencode_command),
        CommandHandler("urldecode", urldecode_command),
        CommandHandler("breach", breach_command),
        CommandHandler("cms", cms_command),
        CommandHandler("analyse", analyse_command),
        CommandHandler("extract", extract_command),
    ]
    application.add_handlers(handlers)
    
    logging.info(f"Doraemon Cyber Team Bot v{BOT_VERSION} is starting...")
    application.run_polling()
    logging.info("Doraemon Cyber Team Bot has stopped.")

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    main()
