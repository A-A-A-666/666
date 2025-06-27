# 666-main/handlers/bot_helpers.py

from typing import Set
# Import tool definitions for argument processing
from Web import TOOL_GROUPS, ENDPOINTS, LOCAL_TOOLS
# Import templates for report formatting
from . import bot_templates

def resolve_tools_from_args(args: list[str]) -> Set[str]:
    """
    Resolves a list of user-provided arguments into a final set of tools to run.
    Handles tool groups and individual tool keys.
    """
    # If no tools are specified, default to the 'basic' group.
    selected_keys = args if args else ['basic']
    
    tools_to_run = set()
    for key in selected_keys:
        key = key.lower()
        if key in TOOL_GROUPS:
            tools_to_run.update(TOOL_GROUPS[key])
        elif key in ENDPOINTS or key in LOCAL_TOOLS:
            tools_to_run.add(key)
            
    return tools_to_run

def format_telegram_report(domain: str, results: list[tuple[str, str]]) -> str:
    """
    Builds the final, formatted report string to be sent to Telegram.
    """
    report_parts = [bot_templates.format_report_header(domain)]
    
    for tool_name, result_text in results:
        report_parts.append(
            bot_templates.format_report_section(tool_name, result_text)
        )
        
    return "".join(report_parts)
