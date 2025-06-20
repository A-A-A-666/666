import asyncio
import concurrent.futures
import requests
import os
import logging
import hashlib
from datetime import datetime, timedelta, time

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
)

# --- Constants ---
UPLOAD_DIR = 'uploads'
AWAIT_FILE = 0
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
FILE_LIFETIME_DAYS = 30  # Auto-delete files not used for this many days

logger = logging.getLogger(__name__)

# --- Core Fuzzer Logic (Unchanged) ---
def check_url(session, target_url):
    try:
        with session.get(target_url, timeout=10, allow_redirects=False, stream=True) as response:
            if response.status_code != 404:
                return (target_url, response.status_code)
    except requests.exceptions.RequestException:
        pass
    return None

def run_directory_fuzzer(base_url, wordlist_path, threads=50):
    if not os.path.exists(wordlist_path):
        raise FileNotFoundError(f"Wordlist not found at: {wordlist_path}")
    with open(wordlist_path, 'r', errors='ignore') as f:
        words = [line.strip() for line in f if line.strip()]
    found_results = []
    with requests.Session() as session:
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(check_url, session, f"{base_url}/{word}"): word for word in words}
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    found_results.append(result)
    return sorted(found_results)

# --- Telegram Handler Logic ---

# UPDATED: fuzz_command now tracks file usage
async def fuzz_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (existing fuzz_command logic) ...
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        # ... (show usage) ...
        return
        
    target_url = args[0].rstrip('/')
    wordlist_file = args[1] if len(args) > 1 else 'wordlists/common.txt'

    # NEW: Track usage of uploaded files for the cleanup job
    if wordlist_file.startswith(UPLOAD_DIR):
        if not os.path.exists(wordlist_file):
            await context.bot.send_message(chat_id, f"❌ Error: Wordlist '{wordlist_file}' not found. It may have been deleted for inactivity.")
            return
        # Initialize dictionary if it doesn't exist
        context.bot_data.setdefault('wordlist_last_used', {})
        # Record the current time as the last used time for this file
        context.bot_data['wordlist_last_used'][wordlist_file] = datetime.now()
        logger.info(f"Updated last-used time for {wordlist_file}")

    try:
        status_message = await context.bot.send_message(chat_id, f"🚀 Starting fuzzer on {target_url}...")
        found_paths = await asyncio.to_thread(run_directory_fuzzer, target_url, wordlist_file)
        # ... (reporting logic remains the same) ...
        if not found_paths:
            result_text = f"✅ Fuzzing complete on {target_url}.\n\nNo directories or files found."
        else:
            result_text = f"✅ Fuzzing complete on {target_url}.\n\n<b>Found Paths:</b>\n"
            result_text += "<code>"
            for path, status in found_paths:
                result_text += f"[{status}] - {path}\n"
            result_text += "</code>"
        await status_message.edit_text(result_text, parse_mode='HTML')
    except FileNotFoundError as e:
        await status_message.edit_text(f"❌ Error: {e}")
    except Exception as e:
        await status_message.edit_text(f"❌ An unexpected error occurred: {e}")
        logger.error(f"Fuzzer error: {e}", exc_info=True)


# --- Wordlist Upload Conversation Handler ---

async def upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        f"Please send your wordlist as a .txt file (max {MAX_FILE_SIZE_BYTES // 1024 // 1024}MB).\n"
        "Send /cancel to stop."
    )
    return AWAIT_FILE

# UPDATED: receive_wordlist now checks size and hashes the file
async def receive_wordlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    document = update.message.document
    
    # 1. Check file type
    if not document.file_name.endswith('.txt'):
        await update.message.reply_text("❌ That's not a .txt file. Please try again or /cancel.")
        return AWAIT_FILE

    # 2. Check file size BEFORE downloading
    if document.file_size > MAX_FILE_SIZE_BYTES:
        await update.message.reply_text(
            f"❌ File is too large ({document.file_size // 1024 // 1024}MB). "
            f"The maximum allowed size is {MAX_FILE_SIZE_BYTES // 1024 // 1024}MB."
        )
        return AWAIT_FILE

    # Initialize data stores in bot_data if they don't exist
    context.bot_data.setdefault('hash_to_path', {})
    
    # Download file to memory to calculate hash
    file = await document.get_file()
    file_content = await file.download_as_bytearray()
    
    # 3. Check for duplicates using SHA-256 hash
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    if file_hash in context.bot_data['hash_to_path']:
        existing_path = context.bot_data['hash_to_path'][file_hash]
        # Check if the linked file still exists, in case it was cleaned up
        if os.path.exists(existing_path):
            await update.message.reply_text(
                "ℹ️ This exact file has been uploaded before.\n\n"
                f"You can use it at: <code>{existing_path}</code>",
                parse_mode='HTML'
            )
            # Update its last-used time to prevent it from being cleaned up soon
            context.bot_data.setdefault('wordlist_last_used', {})
            context.bot_data['wordlist_last_used'][existing_path] = datetime.now()
            return ConversationHandler.END

    # 4. Save new file if it's not a duplicate
    unique_filename = f"{user.id}_{document.file_name}"
    save_path = os.path.join(UPLOAD_DIR, unique_filename)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    with open(save_path, 'wb') as f:
        f.write(file_content)

    # Store the hash and path for future duplicate checks
    context.bot_data['hash_to_path'][file_hash] = save_path
    
    logger.info(f"User {user.id} uploaded new wordlist to {save_path} (hash: {file_hash[:8]})")
    await update.message.reply_text(
        "✅ File uploaded successfully!\n\n"
        f"Use it with: <code>/fuzz https://example.com {save_path}</code>",
        parse_mode='HTML'
    )
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Upload operation cancelled.")
    return ConversationHandler.END

# --- NEW: Automatic Cleanup Job ---
async def cleanup_job(context: ContextTypes.DEFAULT_TYPE):
    """Periodically cleans up old, unused wordlists."""
    logger.info("Running daily cleanup job...")
    now = datetime.now()
    lifetime_delta = timedelta(days=FILE_LIFETIME_DAYS)
    
    # Get the data from bot_data, providing empty dicts as defaults
    last_used_times = context.bot_data.get('wordlist_last_used', {})
    hash_to_path = context.bot_data.get('hash_to_path', {})
    
    paths_to_delete = set()
    
    for path in os.listdir(UPLOAD_DIR):
        full_path = os.path.join(UPLOAD_DIR, path)
        if not os.path.isfile(full_path):
            continue
            
        last_used = last_used_times.get(full_path)
        # Check if the file was never used or if it was last used too long ago
        if not last_used or (now - last_used > lifetime_delta):
            # As a safeguard, also check file creation time
            try:
                creation_time = datetime.fromtimestamp(os.path.getctime(full_path))
                if (now - creation_time) > lifetime_delta:
                    paths_to_delete.add(full_path)
            except FileNotFoundError:
                continue

    if not paths_to_delete:
        logger.info("Cleanup job finished. No files to delete.")
        return

    # Delete files and clean up metadata
    hashes_to_remove = []
    for h, p in list(hash_to_path.items()):
        if p in paths_to_delete:
            hashes_to_remove.append(h)

    for h in hashes_to_remove:
        del hash_to_path[h]

    for path in paths_to_delete:
        try:
            os.remove(path)
            # Remove from last-used tracker
            if path in last_used_times:
                del last_used_times[path]
            logger.info(f"Cleaned up unused file: {path}")
        except OSError as e:
            logger.error(f"Error deleting file {path}: {e}")

# UPDATED: register_handlers now schedules the cleanup job
def register_handlers(application: Application):
    """Adds all handlers and schedules jobs."""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("upload", upload_start)],
        states={AWAIT_FILE: [MessageHandler(filters.Document.TEXT, receive_wordlist)]},
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        conversation_timeout=300,
        persistent=True, # Make the conversation persistent across restarts
        name="upload_conversation" # Give it a name for persistence
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("fuzz", fuzz_command))
    
    # --- Schedule the daily cleanup job ---
    job_queue = application.job_queue
    # **FIX APPLIED HERE**: Check if job_queue exists before using it.
    if job_queue:
        # Run once a day at 3:00 AM bot's local time
        job_queue.run_daily(cleanup_job, time=time(hour=3, minute=0), name="daily_cleanup")
        logger.info("Fuzzer, Upload handlers, and Daily Cleanup Job have been registered.")
    else:
        logger.warning("JobQueue not found. Daily cleanup job not scheduled. Install 'python-telegram-bot[job-queue]' to enable it.")
        logger.info("Fuzzer and Upload handlers have been registered (without cleanup job).")
