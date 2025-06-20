# handlers/recon.py

import logging
import subprocess
import shutil
import os
import re
import tempfile
import json
import asyncio
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ParseMode

from utils import escape_markdown_v2, send_long_message

logger = logging.getLogger(__name__)

# --- Helper for Tool Installation (Corrected) ---
async def check_and_install_tool(tool_name: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Checks if a tool is installed and attempts installation using the install_tool.sh script
    if not found.
    """
    if shutil.which(tool_name):
        logger.info(f"Tool '{tool_name}' already found in PATH.")
        return True

    # **FIX APPLIED HERE**: Escape the entire message string
    install_message = f"⏳ Tool '{tool_name}' not found. Attempting installation..."
    await update.message.reply_text(escape_markdown_v2(install_message), parse_mode=ParseMode.MARKDOWN_V2)

    script_dir = os.path.dirname(__file__)
    install_script_path = os.path.join(script_dir, '..', 'install_tool.sh')

    if not os.path.exists(install_script_path):
        error_msg = f"❌ Installation script not found at: `{install_script_path}`."
        logger.error(f"Installation script not found at {install_script_path}")
        await update.message.reply_text(escape_markdown_v2(error_msg), parse_mode=ParseMode.MARKDOWN_V2)
        return False
    if not os.access(install_script_path, os.X_OK):
        error_msg = f"❌ Installation script at `{install_script_path}` is not executable. Please run `chmod +x {install_script_path}` on the server."
        logger.error(f"Installation script not executable at {install_script_path}")
        await update.message.reply_text(escape_markdown_v2(error_msg), parse_mode=ParseMode.MARKDOWN_V2)
        return False

    try:
        logger.info(f"Running installation script for {tool_name}: {install_script_path} {tool_name}")
        process = await asyncio.create_subprocess_exec(
            install_script_path, tool_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)
        output = (stdout + stderr).decode('utf-8', errors='ignore')

        if process.returncode == 0 and shutil.which(tool_name):
            success_msg = f"✅ Tool '{tool_name}' installed successfully."
            await update.message.reply_text(escape_markdown_v2(success_msg), parse_mode=ParseMode.MARKDOWN_V2)
            return True
        else:
            error_msg = f"❌ Failed to install '{tool_name}'. Installation script output:\n```\n{output[:1000]}...\n```"
            logger.error(f"Installation script failed for {tool_name} (exit code {process.returncode}): {output}")
            await update.message.reply_text(escape_markdown_v2(error_msg), parse_mode=ParseMode.MARKDOWN_V2)
            return False
    except asyncio.TimeoutError:
        error_msg = f"❌ Installation script for '{tool_name}' timed out."
        logger.warning(f"Installation script timed out after 600s for {tool_name}")
        await update.message.reply_text(escape_markdown_v2(error_msg), parse_mode=ParseMode.MARKDOWN_V2)
        return False
    except Exception as e:
        error_msg = f"❌ An unexpected error occurred while running the installation script for '{tool_name}': {str(e)}"
        logger.error(f"Exception running installation script for {tool_name}: {e}", exc_info=True)
        await update.message.reply_text(escape_markdown_v2(error_msg), parse_mode=ParseMode.MARKDOWN_V2)
        return False


# --- Subprocess Execution Helper (No changes needed here) ---
async def run_subprocess_command(command: list[str], update: Update, context: ContextTypes.DEFAULT_TYPE, timeout: int = 300, description: str = "command") -> Optional[str]:
    try:
        logger.info(f"Running command: {' '.join(command)}")
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        output = (stdout or stderr).decode('utf-8', errors='ignore')
        if process.returncode != 0:
             logger.error(f"{description} failed with return code {process.returncode}. Command: {' '.join(command)}. Output: {output}")
             response_text = f"❌ The {description} failed (exit code {process.returncode}). Output:\n```\n{output[:1000]}...\n```"
             await update.message.reply_text(escape_markdown_v2(response_text), parse_mode=ParseMode.MARKDOWN_V2)
             return None
        return output
    except FileNotFoundError:
        response_text = f"❌ Error: The executable for this {description} was not found in PATH."
        await update.message.reply_text(escape_markdown_v2(response_text), parse_mode=ParseMode.MARKDOWN_V2)
        logger.error(f"Executable not found for command: {' '.join(command)}")
        return None
    except asyncio.TimeoutError:
        response_text = f"⏳ The {description} timed out after {timeout} seconds."
        await update.message.reply_text(escape_markdown_v2(response_text), parse_mode=ParseMode.MARKDOWN_V2)
        logger.warning(f"Command timed out after {timeout}s: {' '.join(command)}")
        return None
    except Exception as e:
        response_text = f"❌ An unexpected error occurred during the {description}: {str(e)}"
        await update.message.reply_text(escape_markdown_v2(response_text), parse_mode=ParseMode.MARKDOWN_V2)
        logger.error(f"Exception running command {' '.join(command)}: {e}", exc_info=True)
        return None


# --- Command Handlers (Corrected) ---

async def dirbuster_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        usage_text = "Usage: /dirbuster <url> [wordlist]\nDefault wordlist: /usr/share/dirb/wordlists/common.txt"
        await update.message.reply_text(escape_markdown_v2(usage_text), parse_mode=ParseMode.MARKDOWN_V2)
        return

    target_url = context.args[0].strip()
    wordlist_path = context.args[1] if len(context.args) > 1 else "/usr/share/dirb/wordlists/common.txt"
    if not target_url.startswith(('http://', 'https://')):
         target_url = 'http://' + target_url

    if not await check_and_install_tool('gobuster', update, context):
        return

    if not os.path.exists(wordlist_path):
         error_msg = f"❌ Wordlist not found at `{wordlist_path}`."
         await update.message.reply_text(escape_markdown_v2(error_msg), parse_mode=ParseMode.MARKDOWN_V2)
         return

    # **FIX APPLIED HERE**: Escape the entire message string
    status_msg = f"🚀 Starting directory scan on `{target_url}` using wordlist `{wordlist_path}`... This may take some time."
    await update.message.reply_text(escape_markdown_v2(status_msg), parse_mode=ParseMode.MARKDOWN_V2)

    command = ['gobuster', 'dir', '-u', target_url, '-w', wordlist_path, '-t', '50', '-f']
    output = await run_subprocess_command(command, update, context, timeout=600, description="directory scan")

    if output:
        results = "\n".join([
            line.strip() for line in output.splitlines()
            if line.strip() and not line.startswith('==') and 'Progress' not in line
        ])
        if results.strip():
            response_text = f"✅ Directory scan complete for `{target_url}`:\n```\n{results}\n```"
            await update.message.reply_text(escape_markdown_v2(response_text), parse_mode=ParseMode.MARKDOWN_V2)
        else:
            response_text = f"✅ Directory scan complete for `{target_url}`, no results found."
            await update.message.reply_text(escape_markdown_v2(response_text), parse_mode=ParseMode.MARKDOWN_V2)


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        usage_text = "Usage: /search <username>\nSearches for the username across many social media sites."
        await update.message.reply_text(escape_markdown_v2(usage_text), parse_mode=ParseMode.MARKDOWN_V2)
        return

    target_username = context.args[0].strip()
    if not await check_and_install_tool('sherlock', update, context):
        return

    # **FIX APPLIED HERE**: Escape the entire message string
    status_msg = f"🔎 Searching for username `{target_username}` across social media platforms... This can take some time."
    await update.message.reply_text(escape_markdown_v2(status_msg), parse_mode=ParseMode.MARKDOWN_V2)

    command = ['sherlock', target_username, '--timeout', '5', '--print-found']
    output = await run_subprocess_command(command, update, context, timeout=600, description="username search")

    if output:
        found_results = []
        not_found_count = 0
        for line in output.splitlines():
            line = line.strip()
            if line.startswith('[+]'):
                found_results.append(line)
            elif line.startswith('[-]'):
                not_found_count += 1
        
        response_text = f"🌐 *Social Media Scan Results for `{target_username}`:*\n\n"
        if found_results:
            response_text += "*Found Accounts:*\n" + "\n".join(found_results)
            if not_found_count > 0:
                 response_text += f"\n\n*Not Found on {not_found_count} other sites checked.*"
        elif not_found_count > 0:
            response_text += f"❌ Username `{target_username}` was not found on the checked sites ({not_found_count} sites checked)."
        else:
            response_text += "❓ No results were parsed from the sherlock output."
        
        # Note: Sherlock output already contains URLs, so we don't escape it for MarkdownV2 to preserve links.
        # This is a trade-off. A safer method would be to parse and reconstruct.
        # For simplicity here, we send it as plain text.
        await send_long_message(update, context, response_text, parse_mode=None, disable_web_page_preview=True)


async def wpscan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or len(context.args) < 2:
        usage_text = "Usage: /wpscan <url> <api_token>\nExample: /wpscan https://example.com YOUR_API_TOKEN"
        await update.message.reply_text(escape_markdown_v2(usage_text), parse_mode=ParseMode.MARKDOWN_V2)
        return

    target_url = context.args[0].strip()
    api_token = context.args[1].strip()
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url

    if not await check_and_install_tool('wpscan', update, context):
        return

    # **FIX APPLIED HERE**: Escape the entire message string
    status_msg = f"🛡️ Starting WPScan on `{target_url}`... This may take some time."
    await update.message.reply_text(escape_markdown_v2(status_msg), parse_mode=ParseMode.MARKDOWN_V2)

    command = ['wpscan', '--url', target_url, '--api-token', api_token, '--enumerate', 'vp,vt,dbe', '--format', 'json']
    output = await run_subprocess_command(command, update, context, timeout=900, description="WPScan")

    if output:
        try:
            scan_results = json.loads(output)
            response_text = f"✅ WPScan Results for `{target_url}` (JSON Output):\n```json\n{json.dumps(scan_results, indent=2)[:3500]}...\n```"
            await update.message.reply_text(escape_markdown_v2(response_text), parse_mode=ParseMode.MARKDOWN_V2)
        except json.JSONDecodeError:
            response_text = f"✅ WPScan Results for `{target_url}` (raw output):\n```\n{output[:3800]}...\n```"
            await update.message.reply_text(escape_markdown_v2(response_text), parse_mode=ParseMode.MARKDOWN_V2)


async def searchsploit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        usage_text = "Usage: /searchsploit <keyword(s)>\nSearches the Exploit-DB database."
        await update.message.reply_text(escape_markdown_v2(usage_text), parse_mode=ParseMode.MARKDOWN_V2)
        return

    keywords = " ".join(context.args).strip()
    if not await check_and_install_tool('searchsploit', update, context):
        return

    # **FIX APPLIED HERE**: Escape the entire message string
    status_msg = f"📚 Searching Exploit-DB for `{keywords}`... This should be quick."
    await update.message.reply_text(escape_markdown_v2(status_msg), parse_mode=ParseMode.MARKDOWN_V2)

    command = ['searchsploit'] + context.args
    output = await run_subprocess_command(command, update, context, timeout=60, description="searchsploit")

    if output:
        response_text = f"*Exploit-DB Search Results for `{keywords}`:*\n```\n{output[:3800]}...\n```"
        await update.message.reply_text(escape_markdown_v2(response_text), parse_mode=ParseMode.MARKDOWN_V2)


# List of handlers to be registered in main.py
recon_handlers = [
    CommandHandler("dirbuster", dirbuster_command),
    CommandHandler("search", search_command),
    CommandHandler("wpscan", wpscan_command),
    CommandHandler("searchsploit", searchsploit_command),
    ]
