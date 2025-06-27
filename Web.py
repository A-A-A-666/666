from flask import Flask, request, render_template
import os
import json
import asyncio
import aiohttp
import re
import subprocess

# --- START of ReconDora Logic (Centralized for Web & Bot) ---

# ==============================================================================
# 1. API-BASED TOOLS (HackerTarget)
# ==============================================================================
ENDPOINTS = {
    "hostsearch": "https://api.hackertarget.com/hostsearch/?q=",
    "dnslookup": "https://api.hackertarget.com/dnslookup/?q=",
    "whois": "https://api.hackertarget.com/whois/?q=",
    "geoip": "https://api.hackertarget.com/geoip/?q=",
    "reverseiplookup": "https://api.hackertarget.com/reverseiplookup/?q=",
    "findshareddns": "https://api.hackertarget.com/findshareddns/?q=",
    "zonetransfer": "https://api.hackertarget.com/zonetransfer/?q=",
    "httpheaders": "https://api.hackertarget.com/httpheaders/?q=",
    "pagelinks": "https://api.hackertarget.com/pagelinks/?q=",
    "nmap": "https://api.hackertarget.com/nmap/?q=",
    "mtr": "https://api.hackertarget.com/mtr/?q=",
    "aslookup": "https://api.hackertarget.com/aslookup/?q="
}

TOOL_DESCRIPTIONS = {
    "hostsearch": "Finds hostnames and subdomains using the same name server.",
    "dnslookup": "Performs a standard DNS lookup for the target.",
    "whois": "Retrieves WHOIS registration data for a domain.",
    "geoip": "Finds the geographical location of an IP address.",
    "reverseiplookup": "Finds hostnames sharing the same IP address.",
    "findshareddns": "Finds hosts that share the same DNS servers.",
    "zonetransfer": "Attempts a DNS zone transfer for the domain.",
    "httpheaders": "Retrieves the HTTP response headers from the target.",
    "pagelinks": "Scrapes a page for all links, both internal and external.",
    "nmap": "Runs a quick Nmap port scan on the target.",
    "mtr": "Performs an MTR traceroute to the target.",
    "aslookup": "Looks up the Autonomous System (AS) number for the target."
}

TOOL_GROUPS = {
    "basic": ["hostsearch", "dnslookup", "whois"],
    "network": ["nmap", "mtr", "geoip", "aslookup"],
    "web": ["httpheaders", "pagelinks"],
    "dns": ["hostsearch", "dnslookup", "findshareddns", "zonetransfer", "reverseiplookup"],
    "all": list(ENDPOINTS.keys())
}

# ==============================================================================
# 2. LOCAL COMMAND-LINE TOOLS
# ==============================================================================
LOCAL_TOOLS = {
    "local_ping": {
        "name": "Ping",
        "description": "Sends 4 ICMP packets to the target to check for reachability.",
        "command": ["ping", "-c", "4", "{target}"]
    },
    "local_curl_headers": {
        "name": "Curl Headers",
        "description": "Fetches HTTP headers using the curl command.",
        "command": ["curl", "-I", "--silent", "{target}"]
    },
}

# ==============================================================================
# 3. CORE EXECUTOR LOGIC
# ==============================================================================

# --- API Tool Executor ---
async def fetch_tool(session: aiohttp.ClientSession, domain: str, tool: str) -> tuple[str, str]:
    try:
        url = ENDPOINTS[tool] + domain
        headers = {'User-Agent': 'Doraemon-Cyber-Tool/1.0'}
        async with session.get(url, timeout=45, headers=headers) as resp:
            resp.raise_for_status()
            text_content = await resp.text()
            if "error check your search query" in text_content:
                return tool, "API Error: Invalid domain or query."
            return tool.strip(), text_content.strip()
    except aiohttp.ClientError as e:
        return tool, f"[API Request Error] {e}"
    except asyncio.TimeoutError:
        return tool, "[API Request Error] Request timed out after 45 seconds."
    except Exception as e:
        return tool, f"[Unexpected Error] {e}"

# --- Local Tool Executor ---
async def run_local_tool(target: str, tool_key: str) -> tuple[str, str]:
    tool_config = LOCAL_TOOLS.get(tool_key)
    tool_name = tool_config.get("name", tool_key)

    if not re.match(r"^[a-zA-Z0-9.-]+$", target):
        return tool_name, f"[Validation Error] Invalid target format: {target}"

    try:
        command_to_run = [arg.replace("{target}", target) for arg in tool_config["command"]]
        process = await asyncio.create_subprocess_exec(
            *command_to_run,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
        output = (stdout.decode('utf-8', errors='ignore') + stderr.decode('utf-8', errors='ignore')).strip()
        
        if not output:
            output = "[No output from command]"
        return tool_name, output
    except FileNotFoundError:
        return tool_name, f"[Execution Error] Command not found: '{tool_config['command'][0]}'. Is it installed and in your PATH?"
    except asyncio.TimeoutError:
        return tool_name, "[Execution Error] Command timed out after 60 seconds."
    except Exception as e:
        return tool_name, f"[Unexpected Execution Error] {str(e)}"

# --- END of Core Logic ---

# Create a Flask app instance
app = Flask(__name__)

@app.route('/')
def home():
    """Renders the main page with a form to run recon."""
    default_tools = TOOL_GROUPS.get('basic', [])
    return render_template(
        "index.html", 
        tool_descriptions=TOOL_DESCRIPTIONS,
        local_tools=LOCAL_TOOLS,
        default_tools=default_tools
    )

@app.route('/recondora')
async def run_recondora_web():
    """API endpoint to run recon and display results in HTML."""
    domain = request.args.get('domain')
    selected_tools = request.args.getlist('tools')

    if not domain:
        return render_template("results.html", domain="Error", results=[("Error", "A 'domain' query parameter is required.")])
    
    if not selected_tools:
        selected_tools = TOOL_GROUPS['basic']

    api_tasks = []
    local_tasks = []

    for tool_key in selected_tools:
        if tool_key in ENDPOINTS:
            api_tasks.append(tool_key)
        elif tool_key in LOCAL_TOOLS:
            local_tasks.append(tool_key)

    async with aiohttp.ClientSession() as session:
        api_coroutines = [fetch_tool(session, domain, tool) for tool in api_tasks]
        local_coroutines = [run_local_tool(domain, tool_key) for tool_key in local_tasks]
        results = await asyncio.gather(*api_coroutines, *local_coroutines)
    
    return render_template("results.html", domain=domain, results=results)


def start():
    """This function starts the simple web server."""
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    start()
