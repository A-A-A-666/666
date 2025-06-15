from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import subprocess, shutil, os

SUPPORTED_TOOLS = {
    "sqlmap": {
        "cmd": "sqlmap",
        "desc": "SQL injection tester"
    },
    "nmap": {
        "cmd": "nmap",
        "desc": "Network scanner"
    },
    "xssstrike": {
        "cmd": "xssstrike",
        "desc": "XSS vulnerability scanner"
    },
    "rustscan": {
        "cmd": "rustscan",
        "desc": "Fast TCP port scanner"
    },
    "ffuf": {
        "cmd": "ffuf",
        "desc": "Directory brute-forcer"
    }
}

tool_args_waiting = {}

async def tool_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(tool, callback_data=f"tool_select:{tool}")]
        for tool in SUPPORTED_TOOLS.keys()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠 Select a tool:", reply_markup=reply_markup)

async def tool_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tool = query.data.split(":")[1]
    tool_args_waiting[query.from_user.id] = tool
    await query.message.reply_text(f"✍️ Send me the arguments for *{tool}* (or say `default`)", parse_mode="Markdown")

async def tool_args_receiver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in tool_args_waiting:
        return

    tool = tool_args_waiting.pop(user_id)
    arg_string = update.message.text.strip()

    args = [] if arg_string == "default" else arg_string.split()
    await run_tool_with_args(update, context, tool, args)

async def run_tool_with_args(update: Update, context: ContextTypes.DEFAULT_TYPE, tool, args):
    tool_cmd = SUPPORTED_TOOLS[tool]["cmd"]
    path = shutil.which(tool_cmd)

    if not path:
        await update.message.reply_text(f"{tool} not installed. Attempting install...")

        installs = {
            "sqlmap": ["git", "clone", "https://github.com/sqlmapproject/sqlmap.git"],
            "xssstrike": ["git", "clone", "https://github.com/s0md3v/XSStrike.git"],
            "nmap": ["apt", "install", "-y", "nmap"],
            "rustscan": ["cargo", "install", "rustscan"],
            "ffuf": ["apt", "install", "-y", "ffuf"]
        }

        if tool in installs:
            try:
                subprocess.run(installs[tool], check=True)
                await update.message.reply_text("✅ Installed.")
            except Exception as e:
                await update.message.reply_text(f"❌ Install failed: {e}")
                return

    try:
        if tool == "sqlmap" and not path:
            path = os.path.join("sqlmap", "sqlmap.py")
            cmd = ["python3", path] + args
        elif tool == "xssstrike" and not path:
            path = os.path.join("XSStrike", "xsstrike.py")
            cmd = ["python3", path] + args
        else:
            cmd = [tool_cmd] + args

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        output = result.stdout + "\n" + result.stderr
        await update.message.reply_text("📤 Output:\n" + (output[:4000] + "\n...truncated" if len(output) > 4000 else output))
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

tool_handler = CommandHandler("tool", tool_menu)
tool_callback_handler = CallbackQueryHandler(tool_select_callback, pattern="^tool_select:")
tool_args_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), tool_args_receiver)
