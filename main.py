import logging
import os
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler, # Keep import if other conversations exist or for structure
    PersistenceInput, # Import PersistenceInput if using persistence
    PicklePersistence, # Example: Import PicklePersistence
)
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
from handlers.autoupload import autoupload_command # Assuming this was intended to be used
from handlers.tool_handlers import (
    tool_command,
    tool_callback_handler,
    tool_args_handler,
)
# Import new recon handlers - ONLY the list, not the conversation handler
from handlers.recon import recon_handlers
# Import fuzzer handlers and job registration
from handlers.fuzzer import register_handlers as register_fuzzer_handlers
from handlers.recondora import recon_doraemon_command # ADDED THIS LINE


from utils import BOT_VERSION

# --- Configuration ---
# The bot token is fetched from the environment variables.
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE") # Use a default placeholder

# Configure logging before application creation
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
# Set logging level for specific libraries if needed
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING) # Reduce verbosity for asyncio


logger = logging.getLogger(__name__) # Get logger for main script

def main() -> None:
    """
    This function sets up and runs the bot using polling.
    It is completely independent of any web server.
    """
    if not BOT_TOKEN or "YOUR_BOT_TOKEN_HERE" in BOT_TOKEN:
        logger.critical("CRITICAL: BOT_TOKEN is not set or is using the default placeholder. The bot cannot start.")
        print("Please set the BOT_TOKEN environment variable.")
        return

    # Setup persistence
    # Make sure the directory for the persistence file exists
    persistence_dir = "persistence_data"
    os.makedirs(persistence_dir, exist_ok=True)
    persistence_file = os.path.join(persistence_dir, "bot_persistence.pkl")
    persistence = PicklePersistence(filepath=persistence_file)


    # Create the Application instance
    # Use persistence to save conversation states and bot_data (like wordlist usage)
    application = Application.builder().token(BOT_TOKEN).persistence(persistence).build()


    # A single list of standard command/callback handlers
    standard_handlers = [
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
        CommandHandler("recondora", recon_doraemon_command), # ADDED THIS LINE

        # Data & Security handlers
        CommandHandler("breach", breach_command),
        CommandHandler("extract", extract_command),
        CommandHandler("base64", base64_command),
        CallbackQueryHandler(base64_button_handler, pattern="^b64_"),
        CommandHandler("md5", md5_command),
        CommandHandler("urlencode", urlencode_command),
        CommandHandler("urldecode", urldecode_command),

        # Autoupload handler
        CommandHandler("autoupload", autoupload_command),

        # Tool handlers (/tool command and callback)
        CommandHandler("tool", tool_command),
        CallbackQueryHandler(tool_callback_handler, pattern="^tool_"),

        # New recon handlers (dirbuster, search, wpscan, searchsploit)
        *recon_handlers # Use the list created in handlers/recon.py
    ]

    # Add all standard handlers
    application.add_handlers(standard_handlers)

    # Note: The Instagram login conversation handler (login_conv_handler) is NOT imported or added here.
    # If other ConversationHandlers existed, they would be added here.

     # This message handler MUST come AFTER all command handlers to avoid
     # intercepting command arguments for the /tool command or conversation messages.
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), tool_args_handler))


    # --- Schedule jobs (like cleanup from fuzzer.py) ---
    # Register fuzzer handlers which also schedules the cleanup job
    register_fuzzer_handlers(application)


    logger.info(f"Doraemon Cyber Team Bot v{BOT_VERSION} is starting in polling mode...")
    logger.info("Registered Handlers:")
    # List handlers for debugging/verification
    # Note: Getting a clean list of all registered handlers can be complex
    # across different handler types and groups. This is a simplified view.
    for handler in application.handlers.get(0, []): # Get handlers in group 0 (default)
        if hasattr(handler, 'callback'):
            if hasattr(handler.callback, '__name__'):
                 logger.info(f"- {type(handler).__name__}: {handler.callback.__name__}")
            elif isinstance(handler, ConversationHandler): # Check explicitly for ConversationHandler if any are added
                logger.info(f"- ConversationHandler: {handler.name}")
            else:
                 logger.info(f"- {type(handler).__name__}: {handler.callback}")
        elif isinstance(handler, ConversationHandler): # Check explicitly for ConversationHandler if any are added
             logger.info(f"- ConversationHandler: {handler.name}")
        elif isinstance(handler, MessageHandler):
             logger.info(f"- MessageHandler (Filters: {handler.filters})")


    # Start the bot polling loop
    # The Web.start() call is outside this loop and won't be reached in polling mode.
    application.run_polling(poll_interval=3.0) # Add poll_interval


if __name__ == "__main__":
    # This Web.start() call will only run if main() exits, which it won't in polling mode.
    # Consider removing or refactoring for a proper web/webhook deployment.
    #Web.start() # Commenting out as it won't be reached in polling mode
    main()
    Web.start()
