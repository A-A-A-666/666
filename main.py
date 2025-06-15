import logging
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
import Web
# Import all command handlers
from handlers.basic import start_command, help_command
from handlers.network import (
    lookup_command, nmap_command, rustscan_command, headers_command,
    methods_command, revip_command
)
from handlers.data import (
    base64_command, base64_button_handler, md5_command, urlencode_command,
    urldecode_command, breach_command, cms_command, analyse_command, extract_command
)
from handlers.subdomain_finder import subdo_command
from utils import BOT_VERSION
from handlers.tool_handlers import tool_handler, tool_callback_handler, tool_args_handler
# --- Configuration ---
# The bot token is fetched from the environment variables.
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7769276879:AAE0nH5jYEYnKMyYFVv3n0JCLgqnL2yuNPU")

def main() -> None:
    """
    This function sets up and runs the bot using polling.
    It is completely independent of any web server.
    """
    if not BOT_TOKEN or "YOUR_BOT_TOKEN" in BOT_TOKEN:
        logging.error("CRITICAL: BOT_TOKEN is not set. The bot cannot start.")
        return

    # Create the Application instance
    application = Application.builder().token(BOT_TOKEN).build()

    # A single list of all handlers for cleaner registration
    all_handlers = [
        # Basic handlers
        CommandHandler("start", start_command),
        CommandHandler("help", help_command),

        # Network handlers
        CommandHandler("subdo", subdo_command),
        CommandHandler("lookup", lookup_command),
        CommandHandler("headers", headers_command),
        CommandHandler("methods", methods_command),
        CommandHandler("revip", revip_command),
        CommandHandler("analyse", analyse_command),
        CommandHandler("cms", cms_command),
        CommandHandler("nmap", nmap_command),
        CommandHandler("rustscan", rustscan_command),
        
        # Data & Security handlers
        CommandHandler("breach", breach_command),
        CommandHandler("extract", extract_command),
        CommandHandler("base64", base64_command),
        CallbackQueryHandler(base64_button_handler, pattern="^b64_"),
        CommandHandler("md5", md5_command),
        CommandHandler("urlencode", urlencode_command),
        CommandHandler("urldecode", urldecode_command),
    ]

    # Register all handlers with the application
    application.add_handlers(all_handlers)
    app.add_handler(tool_handler)
    app.add_handler(tool_callback_handler)
    app.add_handler(tool_args_handler)
    logging.info(f"Doraemon Cyber Team Bot v{BOT_VERSION} is starting in polling mode...")

    # Start the bot. This will run until you stop the script (e.g., with Ctrl+C).
    application.run_polling()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    # Run the main bot function
    main()
    Web.start()
