# 666-main/handlers/bot_templates.py

from utils import escape_markdown_v2

# Import tool definitions to build the help text dynamically
from Web import ENDPOINTS, LOCAL_TOOLS

def get_recondora_help_text() -> str:
    """Generates the detailed help message for the /recondora command."""
    
    api_tool_list = escape_markdown_v2(", ".join(ENDPOINTS.keys()))
    local_tool_list = escape_markdown_v2(", ".join(LOCAL_TOOLS.keys()))

    usage_text = (
        "Perform multi\\-tool reconnaissance on a domain\\.\n\n"
        "*Usage:* `/recondora <domain> [tool1] [tool2] ...`\n\n"
        "*Example:* `/recondora example.com whois local_ping`\n\n"
        "If no tools are specified, a basic API scan is run by default\\.\n\n"
        f"*Available API Tools:*\n`{api_tool_list}`\n\n"
        f"*Available Local Tools:*\n`{local_tool_list}`"
    )
    return usage_text

def get_status_message(domain: str, tools: list[str]) -> str:
    """Generates the 'in-progress' status message."""
    escaped_domain = escape_markdown_v2(domain)
    escaped_tools = escape_markdown_v2(", ".join(tools))
    return f"🔎 Running recon on `{escaped_domain}` with tools: `{escaped_tools}`{escape_markdown_v2('...')} this may take a moment\\."

def format_report_header(domain: str) -> str:
    """Formats the main header of the report."""
    escaped_domain = escape_markdown_v2(domain)
    return f">_ *Recon Report for `{escaped_domain}`*"

def format_report_section(tool_name: str, result_text: str) -> str:
    """Formats a single tool's section in the report."""
    # The result_text is inside a code block, so it doesn't need escaping.
    return f"\n\n*{escape_markdown_v2(f'[{tool_name.upper()}]')}*\n```\n{result_text}\n```"
