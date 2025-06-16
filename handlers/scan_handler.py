import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.injection_scanner import scan_for_injections

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("⚠️ Usage: /scan <url>")
            return
            
        target_url = context.args[0].strip()
        msg = await update.message.reply_text(f"🔍 Scanning {target_url}...")
        
        vulnerabilities = await scan_for_injections([target_url])
        
        if vulnerabilities:
            response = ["🚨 Vulnerabilities Found:", ""]
            for vuln in vulnerabilities:
                response.append(f"• {vuln['type']} in parameter '{vuln['param']}'")
                response.append(f"  Payload: {vuln['payload']}")
                response.append(f"  URL: {vuln['url']}\n")
            await msg.edit_text("\n".join(response))
        else:
            await msg.edit_text("✅ No vulnerabilities found!")
            
    except Exception as e:
        logger.error(f"Scan error: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
