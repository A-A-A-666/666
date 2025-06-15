from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import subprocess
import shutil

# List of tools
TOOL_LIST = ["sqlmap", "nmap", "rustscan", "xssstrike", "ffuf"]

# For storing user tool selections
user_tool_context = {}

# GitHub fallback repos
GITHUB_INSTALL = {
    "xssstrike": "https://github.com/UltimateHackers/XSS-Strike.git",
    "ffuf": "https://github.com/ffuf/ffuf.git",
}

# Escape text for MarkdownV2
def escape_md(text):
    for ch in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        text = text.replace(ch, f'\\{ch}')
    return text

# Safe reply function
async def safe_reply(target, text):
    try:
        await target.reply_text(escape_md(text), parse_mode="MarkdownV2")
    except Exception:
        await target.reply_text(text)

# GitHub fallback installer
async def install_tool(tool: str) -> bool:
    try:
        subprocess.run(["apt", "install", "-y", tool], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        print(f"[!] Apt install failed for {tool}")

    repo_url = GITHUB_INSTALL.get(tool)
    if not repo_url:
        return False

    try:
        path = f"/tmp/{tool}"
        subprocess.run(["rm", "-rf", path])
        subprocess.run(["git", "clone", repo_url, path], check=True)

        if tool == "xssstrike":
            subprocess.run(["chmod", "+x", f"{path}/xssstrike.py"])
            subprocess.run(["ln", "-s", f"{path}/xssstrike.py", "/usr/local/bin/xssstrike"], check=True)

        elif tool == "ffuf":
            subprocess.run(["apt", "install", "-y", "golang"])
            subprocess.run(["go", "install", "github.com/ffuf/ffuf@latest"], check=True)

        return shutil.which(tool) is not None
    except Exception as e:
        print(f"[!] GitHub install failed for {tool}: {e}")
        return False

# /tool command
async def tool_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(tool, callback_data=f"tool_{tool}")] for tool in TOOL_LIST]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠 *Select a tool to run:*", reply_markup=reply_markup, parse_mode="MarkdownV2")

# Button selection
async def tool_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tool = query.data.split("_", 1)[1]
    user_tool_context[query.from_user.id] = tool
    await safe_reply(query.message, f"✍️ Send me arguments for *{tool}* (or type `default`)")

# User replies with arguments
async def tool_args_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    tool = user_tool_context.get(user_id)

    if not tool:
        await safe_reply(update.message, "❗ Use /tool first.")
        return

    args = update.message.text.strip()
    if args.lower() == "default":
        args = "-h"

    full_cmd = [tool] + args.split()

    if not shutil.which(tool):
        await safe_reply(update.message, f"🔄 {tool} not installed. Installing...")
        installed = await install_tool(tool)
        if not installed:
            await safe_reply(update.message, f"❌ Could not install *{tool}*.")
            return
        else:
            await safe_reply(update.message, f"✅ *{tool}* installed successfully.")

    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout or result.stderr or "No output."
        output = escape_md(output[:3900]) + ("\n\n...truncated" if len(output) > 3900 else "")
        await update.message.reply_text(f"```\n{output}\n```", parse_mode="MarkdownV2")
    except Exception as e:
        await safe_reply(update.message, f"⚠️ Error running *{tool}*:\n`{str(e)}`")
