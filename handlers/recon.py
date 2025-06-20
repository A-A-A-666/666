# handlers/recon.py

import logging
import subprocess
import shutil
import os
import re
import tempfile
import json
import asyncio

# No instagrapi import here

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode

from utils import escape_markdown_v2, send_long_message

logger = logging.getLogger(__name__)

# --- Helper for Tool Installation ---
async def check_and_install_apt(tool_name: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Checks if a tool is installed and attempts apt install if not and sudo is available."""
    if shutil.which(tool_name):
        return True

    await update.message.reply_text(f"⏳ Tool '{escape_markdown_v2(tool_name)}' not found. Attempting installation via apt...", parse_mode=ParseMode.MARKDOWN_V2)

    if not shutil.which('sudo'):
        await update.message.reply_text(
            f"❌ Cannot install '{escape_markdown_v2(tool_name)}'. 'sudo' command not found. Please install it manually.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return False

    try:
        # Run apt install with sudo
        process = await asyncio.create_subprocess_exec(
            'sudo', 'apt', 'install', '-y', tool_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300) # 5 minute timeout for install

        if process.returncode == 0:
            await update.message.reply_text(f"✅ Tool '{escape_markdown_v2(tool_name)}' installed successfully.", parse_mode=ParseMode.MARKDOWN_V2)
            # Verify installation after apt
            return shutil.which(tool_name) is not None
        else:
            error_output = (stderr or stdout).decode('utf-8', errors='ignore')
            await update.message.reply_text(
                f"❌ Failed to install '{escape_markdown_v2(tool_name)}' via apt. Error:\n```\n{escape_markdown_v2(error_output[:500])}...\n```", # Truncate error
                parse_mode=ParseMode.MARKDOWN_V2
            )
            logger.error(f"Apt install failed for {tool_name}: {error_output}")
            return False
    except asyncio.TimeoutError:
        await update.message.reply_text(f"❌ Installation of '{escape_markdown_v2(tool_name)}' timed out.", parse_mode=ParseMode.MARKDOWN_V2)
        logger.warning(f"Command timed out after {timeout}s: {' '.join(command)}")
        return False
    except Exception as e:
        await update.message.reply_text(f"❌ An unexpected error occurred during installation of '{escape_markdown_v2(tool_name)}': {escape_markdown_v2(str(e))}", parse_mode=ParseMode.MARKDOWN_V2)
        logger.error(f"Exception during apt install for {tool_name}: {e}", exc_info=True)
        return False

# --- Subprocess Execution Helper ---
async def run_subprocess_command(command: list[str], update: Update, context: ContextTypes.DEFAULT_TYPE, timeout: int = 300, description: str = "command") -> Optional[str]:
    """Runs a subprocess command and returns its output or None on error/timeout."""
    try:
        logger.info(f"Running command: {' '.join(command)}")
        # Use asyncio.create_subprocess_exec for non-blocking execution
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

        output = (stdout or stderr).decode('utf-8', errors='ignore')

        if process.returncode != 0:
             logger.error(f"{description} failed with return code {process.returncode}. Command: {' '.join(command)}. Output: {output}")
             await update.message.reply_text(
                 f"❌ The {escape_markdown_v2(description)} failed (exit code {process.returncode}). Output:\n```\n{escape_markdown_v2(output[:1000])}...\n```",
                 parse_mode=ParseMode.MARKDOWN_V2
             )
             return None

        return output

    except FileNotFoundError:
        await update.message.reply_text(
            f"❌ Error: The executable for this {escape_markdown_v2(description)} was not found.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        logger.error(f"Executable not found for command: {' '.join(command)}")
        return None
    except asyncio.TimeoutError:
        await update.message.reply_text(f"⏳ The {escape_markdown_v2(description)} timed out after {timeout} seconds.", parse_mode=ParseMode.MARKDOWN_V2)
        logger.warning(f"Command timed out after {timeout}s: {' '.join(command)}")
        return None
    except Exception as e:
        await update.message.reply_text(f"❌ An unexpected error occurred during the {escape_markdown_v2(description)}: {escape_markdown_v2(str(e))}", parse_mode=ParseMode.MARKDOWN_V2)
        logger.error(f"Exception running command {' '.join(command)}: {e}", exc_info=True)
        return None

# --- Command Handlers ---

async def dirbuster_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /dirbuster command using gobuster."""
    if not context.args:
        await update.message.reply_text(escape_markdown_v2("Usage: /dirbuster <url> [wordlist]\nDefault wordlist: /usr/share/dirb/wordlists/common.txt"), parse_mode=ParseMode.MARKDOWN_V2)
        return

    target_url = context.args[0].strip()
    wordlist_path = context.args[1] if len(context.args) > 1 else "/usr/share/dirb/wordlists/common.txt"

    if not target_url.startswith('http://') and not target_url.startswith('https://'):
         target_url = 'http://' + target_url # Default to http if no scheme

    escaped_url = escape_markdown_v2(target_url)
    escaped_wordlist = escape_markdown_v2(wordlist_path)

    # Check/Install gobuster
    if not await check_and_install_apt('gobuster', update, context):
        await update.message.reply_text("❌ Gobuster is required and could not be installed. Cannot run command.", parse_mode=ParseMode.MARKDOWN_V2)
        return

    # Check if wordlist exists (especially for custom ones)
    if not os.path.exists(wordlist_path):
         await update.message.reply_text(f"❌ Wordlist not found at `{escaped_wordlist}`.", parse_mode=ParseMode.MARKDOWN_V2)
         return

    await update.message.reply_text(f"🚀 Starting directory scan on `{escaped_url}` using wordlist `{escaped_wordlist}`{escape_markdown_v2('...')} This may take some time.", parse_mode=ParseMode.MARKDOWN_V2)

    # Command: gobuster dir -u <url> -w <wordlist> -t 50 (threads) -f (add trailing slash)
    command = ['gobuster', 'dir', '-u', target_url, '-w', wordlist_path, '-t', '50', '-f']

    output = await run_subprocess_command(command, update, context, timeout=600, description="directory scan") # 10 min timeout

    if output:
        # Gobuster output is usually line-based, filter out status/info lines
        results = "\n".join([
            escape_markdown_v2(line.strip()) for line in output.splitlines()
            if line.strip() and not line.startswith('==') and not line.startswith('/') and not line.startswith('___') and not line.startswith('elapsed') and not line.startswith('status') and not line.startswith('Code')
        ])

        if results.strip():
            response_text = f"✅ Directory scan complete for `{escaped_url}`:\n```\n{results}\n```"
            await send_long_message(update, context, response_text, parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text(f"✅ Directory scan complete for `{escaped_url}`, no results found.", parse_mode=ParseMode.MARKDOWN_V2)


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /search command using sherlock."""
    if not context.args:
        await update.message.reply_text(escape_markdown_v2("Usage: /search <username>\nSearches for the username across many social media sites."), parse_mode=ParseMode.MARKDOWN_V2)
        return

    target_username = context.args[0].strip()
    escaped_target_username = escape_markdown_v2(target_username)

    # Sherlock is installed via requirements.txt (pip), no need for apt check
    if not shutil.which('sherlock'):
         # This case should ideally not happen if requirements are installed, but added as fallback
         await update.message.reply_text("❌ The 'sherlock' command was not found. Please ensure requirements.txt are installed correctly.", parse_mode=ParseMode.MARKDOWN_V2)
         return

    await update.message.reply_text(f"🔎 Searching for username `{escaped_target_username}` across social media platforms{escape_markdown_v2('...')} This can take some time.", parse_mode=ParseMode.MARKDOWN_V2)

    # Command: sherlock <username> --timeout 10 (seconds per site) --print-found
    # Set a global timeout for the command itself, e.g., 10 minutes, as it can hit many sites.
    command = ['sherlock', target_username, '--timeout', '5', '--print-found']

    output = await run_subprocess_command(command, update, context, timeout=600, description="username search") # 10 min timeout

    if output:
        # Sherlock output format is usually like:
        # [+] username: URL
        # [-] username: Not Found
        # Filter and format found results
        found_results = []
        not_found_count = 0
        for line in output.splitlines():
            line = line.strip()
            if line.startswith('[+]'):
                # Extract URL assuming format '[+] username: URL'
                parts = line.split(': ', 2)
                if len(parts) == 3:
                    site_url = parts[2]
                    # Format as MarkdownV2 link if possible, else just text
                    site_name_match = re.search(r'\[\+\] ([^:]+):', line)
                    site_name = site_name_match.group(1).strip() if site_name_match else "Link"

                    # Basic URL validation before formatting as link
                    if site_url.startswith('http://') or site_url.startswith('https://'):
                        found_results.append(f"✅ [{escape_markdown_v2(site_name)}]({site_url})")
                    else:
                         found_results.append(f"✅ {escape_markdown_v2(site_name)}: `{escape_markdown_v2(site_url)}`")

            elif line.startswith('[-]'):
                 not_found_count += 1
            # Ignore other lines (e.g., --timeout, --print-found messages)

        response_text = f"🌐 *Social Media Scan Results for `{escaped_target_username}`:*\n\n"

        if found_results:
            response_text += "*Found Accounts:*\n" + "\n".join(found_results)
            if not_found_count > 0:
                 response_text += f"\n\n*Not Found on {not_found_count} other sites checked.*"
        elif not_found_count > 0:
            response_text += f"❌ Username `{escaped_target_username}` was not found on the checked sites ({not_found_count} sites checked)."
        else:
            response_text += "❓ No results were parsed from the sherlock output."


        await send_long_message(update, context, response_text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)

async def wpscan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /wpscan command."""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(escape_markdown_v2("Usage: /wpscan <url> <api_token>\nExample: /wpscan https://example.com YOUR_API_TOKEN"), parse_mode=ParseMode.MARKDOWN_V2)
        return

    target_url = context.args[0].strip()
    api_token = context.args[1].strip()

    if not target_url.startswith('http://') and not target_url.startswith('https://'):
         target_url = 'https://' + target_url # Default to https if no scheme

    escaped_url = escape_markdown_v2(target_url)
    # Avoid escaping the token itself in the reply message, only in the command execution.
    # Do not echo the token back in plaintext or escaped.

    # Check/Install wpscan
    # Note: wpscan is typically a gem. apt install wpscan might work on some distros.
    # The apt installation helper is attempted first.
    if not await check_and_install_apt('wpscan', update, context):
        if not shutil.which('wpscan'):
             await update.message.reply_text("❌ WPScan is required and could not be installed via apt. Please ensure it's installed and in your PATH (e.g., via `gem install wpscan` or apt). Cannot run command.", parse_mode=ParseMode.MARKDOWN_V2)
             return

    await update.message.reply_text(f"🛡️ Starting WPScan on `{escaped_url}`{escape_markdown_v2('...')} This may take some time.", parse_mode=ParseMode.MARKDOWN_V2)

    # Command: wpscan --url <url> --api-token <token> --enumerate vp,vt,dbe (enumerate plugins, themes, db exports)
    # Adding common enumeration flags
    command = ['wpscan', '--url', target_url, '--api-token', api_token, '--enumerate', 'vp,vt,dbe']

    output = await run_subprocess_command(command, update, context, timeout=900, description="WPScan") # 15 min timeout

    if output:
        try:
            # WPScan output is often JSON when using --format json, but default is text.
            # Let's try to parse as JSON first if it looks like JSON, otherwise treat as text.
            # Simple check if it starts with {
            output = output.strip()
            if output.startswith('{'):
                 # Attempt JSON parsing for better formatting
                 scan_results = json.loads(output)
                 response_text = f"✅ WPScan Results for `{escaped_url}` (JSON Output):\n```json\n{escape_markdown_v2(json.dumps(scan_results, indent=2)[:3500])}...\n```" # Truncate JSON

            else:
                 # Plain text output
                 response_text = f"✅ WPScan Results for `{escaped_url}`:\n```\n{escape_markdown_v2(output[:3500])}...\n```" # Truncate text

            await send_long_message(update, context, response_text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)

        except json.JSONDecodeError:
            # Fallback to text if JSON parsing fails
            response_text = f"✅ WPScan Results for `{escaped_url}`:\n```\n{escape_markdown_v2(output[:3800])}...\n```" # Truncate text
            await send_long_message(update, context, response_text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)
        except Exception as e:
            await update.message.reply_text(f"❌ Error processing WPScan output: {escape_markdown_v2(str(e))}", parse_mode=ParseMode.MARKDOWN_V2)


async def searchsploit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /searchsploit command."""
    if not context.args:
        await update.message.reply_text(escape_markdown_v2("Usage: /searchsploit <keyword(s)>\nSearches the Exploit-DB database."), parse_mode=ParseMode.MARKDOWN_V2)
        return

    keywords = " ".join(context.args).strip()
    escaped_keywords = escape_markdown_v2(keywords)

    # Check/Install searchsploit (usually part of exploitdb package via apt)
    if not await check_and_install_apt('searchsploit', update, context):
         await update.message.reply_text("❌ Searchsploit is required and could not be installed via apt. Please ensure it's installed and in your PATH (e.g., via `apt install exploitdb`). Cannot run command.", parse_mode=ParseMode.MARKDOWN_V2)
         return

    await update.message.reply_text(f"📚 Searching Exploit-DB for `{escaped_keywords}`{escape_markdown_v2('...')} This should be quick.", parse_mode=ParseMode.MARKDOWN_V2)

    # Command: searchsploit <keywords>
    command = ['searchsploit'] + context.args # Pass args directly for multi-word search

    output = await run_subprocess_command(command, update, context, timeout=60, description="searchsploit") # 1 min timeout

    if output:
        # Searchsploit output is usually formatted text
        response_text = f"*Exploit-DB Search Results for `{escaped_keywords}`:*\n```\n{escape_markdown_v2(output[:3800])}...\n```" # Truncate output
        await send_long_message(update, context, response_text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)

# List of handlers to be registered in main.py
recon_handlers = [
    CommandHandler("dirbuster", dirbuster_command),
    CommandHandler("search", search_command),
    CommandHandler("wpscan", wpscan_command),
    CommandHandler("searchsploit", searchsploit_command),
]