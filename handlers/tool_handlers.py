from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import subprocess
import shutil
import os

# List of supported tools
SUPPORTED_TOOLS = {
    "sqlmap": "sqlmap",
    "nmap": "nmap",
    "xssstrike": "xssstrike",
    "rustscan": "rustscan",
    "ffuf": "ffuf"
}

async def run_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /tool <tool_name> <args>")
        return

    tool = context.args[0]
    args = context.args[1:]

    if tool not in SUPPORTED_TOOLS:
        await update.message.reply_text(f"Unsupported tool: {tool}")
        return

    tool_cmd = SUPPORTED_TOOLS[tool]
    tool_path = shutil.which(tool_cmd)

    if not tool_path:
        await update.message.reply_text(f"{tool} not found. Installing...")

        # Install based on tool name
        install_cmds = {
            "sqlmap": ["git", "clone", "https://github.com/sqlmapproject/sqlmap.git"],
            "nmap": ["apt", "install", "-y", "nmap"],
            "xssstrike": ["git", "clone", "https://github.com/s0md3v/XSStrike.git"],
            "rustscan": ["cargo", "install", "rustscan"],
            "ffuf": ["apt", "install", "-y", "ffuf"]
        }

        install_cmd = install_cmds.get(tool)
        if install_cmd:
            try:
                subprocess.run(install_cmd, check=True)
                await update.message.reply_text(f"{tool} installed successfully.")
            except subprocess.CalledProcessError:
                await update.message.reply_text(f"Failed to install {tool}.")
                return
        else:
            await update.message.reply_text(f"No installer defined for {tool}.")
            return

    try:
        # Special case for sqlmap (if cloned)
        if tool == "sqlmap" and not tool_path:
            tool_path = os.path.join("sqlmap", "sqlmap.py")
            cmd = ["python3", tool_path] + args
        elif tool == "xssstrike" and not tool_path:
            tool_path = os.path.join("XSStrike", "xsstrike.py")
            cmd = ["python3", tool_path] + args
        else:
            cmd = [tool_cmd] + args

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        output = result.stdout + "\n" + result.stderr
        if len(output) > 4000:
            output = output[:4000] + "\n...output truncated..."
        await update.message.reply_text(f"Output:\n{output}")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


tool_handler = CommandHandler("tool", run_tool)
