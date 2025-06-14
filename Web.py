import logging
import os
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application

# --- Flask App Initialization ---
# The app object is created here, and routes will be added inside the start function.
app = Flask(__name__)

def start(application: Application) -> None:
    """
    Starts the web server, sets the Telegram webhook, and handles incoming updates.
    This function is called by main.py and is the entry point for the web service.
    
    Args:
        application: The fully configured PTB Application object.
    """
    # Get environment variables required for the web server and webhook
    port = int(os.environ.get("PORT", 8443))
    webhook_url = os.environ.get("WEBHOOK_URL")
    bot_token = application.bot.token

    if not webhook_url:
        logging.critical("CRITICAL: WEBHOOK_URL environment variable is not set. Cannot start webhook bot.")
        return

    # --- Flask Route Definitions ---
    # We define the routes inside start() so they have access to the 'application' object.

    @app.route("/")
    def status() -> str:
        """A simple health-check endpoint for the deployment platform."""
        logging.info("Health check endpoint was hit.")
        return "OK", 200

    @app.route(f"/{bot_token}", methods=["POST"])
    async def webhook() -> str:
        """This endpoint receives the updates from Telegram and processes them."""
        try:
            update_data = request.get_json()
            update = Update.de_json(data=update_data, bot=application.bot)
            await application.process_update(update)
        except Exception as e:
            logging.error(f"Error processing update: {e}")
        return "ok", 200

    # --- Asynchronous Server Execution ---
    # This async function sets the webhook and then starts the web server.
    async def run_server():
        # Set the webhook URL with Telegram
        full_webhook_url = f"{webhook_url}/{bot_token}"
        logging.info(f"Setting webhook to: {full_webhook_url}")
        await application.bot.set_webhook(url=full_webhook_url)

        # Use a production-ready ASGI server like hypercorn to run our Flask app.
        # This is necessary because our webhook handler is an async function.
        try:
            from hypercorn.config import Config
            from hypercorn.asyncio import serve

            config = Config()
            config.bind = [f"0.0.0.0:{port}"]
            
            logging.info(f"Starting web server on http://0.0.0.0:{port}...")
            await serve(app, config)

        except ImportError:
            logging.critical("Hypercorn is not installed. Please add 'hypercorn' to requirements.txt.")
            return
            
    # Run the entire async setup
    try:
        logging.info("Starting asyncio event loop for the server.")
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logging.info("Server startup interrupted by user.")
    except Exception as e:
        logging.critical(f"An error occurred during server startup: {e}")
