from flask import Flask, request, render_template_string
import os
import asyncio
import aiohttp

# --- START of ReconDora Logic (Centralized for Web & Bot) ---

# === API TARGETS ===
ENDPOINTS = {
    "hostsearch": "https://api.hackertarget.com/hostsearch/?q=",
    "dnslookup": "https://api.hackertarget.com/dnslookup/?q=",
    "findshareddns": "https://api.hackertarget.com/findshareddns/?q=",
    "reverseiplookup": "https://api.hackertarget.com/reverseiplookup/?q=",
    "zonetransfer": "https://api.hackertarget.com/zonetransfer/?q=",
    "httpheaders": "https://api.hackertarget.com/httpheaders/?q=",
    "nmap": "https://api.hackertarget.com/nmap/?q=",
    "pagelinks": "https://api.hackertarget.com/pagelinks/?q=",
    "whois": "https://api.hackertarget.com/whois/?q=",
    "mtr": "https://api.hackertarget.com/mtr/?q=",
    "geoip": "https://api.hackertarget.com/geoip/?q=",
    "aslookup": "https://api.hackertarget.com/aslookup/?q="
}

TOOL_GROUPS = {
    "basic": ["hostsearch", "dnslookup", "whois"],
    "network": ["nmap", "mtr", "geoip", "aslookup"],
    "web": ["httpheaders", "pagelinks"],
    "dns": ["hostsearch", "dnslookup", "findshareddns", "zonetransfer", "reverseiplookup"],
    "all": list(ENDPOINTS.keys())
}

# === Helper Functions (Centralized) ===
def parse_tool_input(tool_inputs: list[str]) -> list[str]:
    """Parses user input into a final list of tools to run, defaulting to 'basic'."""
    final_tools = set()
    if not tool_inputs:
        tool_inputs = ['basic']
    for item in tool_inputs:
        item = item.lower()
        if item in ENDPOINTS:
            final_tools.add(item)
        elif item in TOOL_GROUPS:
            final_tools.update(TOOL_GROUPS[item])
    return sorted(list(final_tools))

async def fetch_tool(session: aiohttp.ClientSession, domain: str, tool: str) -> tuple[str, str]:
    """Fetches data from a single HackerTarget API endpoint."""
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

# --- END of ReconDora Logic ---

# --- HTML Templates ---
HOME_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Doraemon Recon Tool</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: #f4f7f6; color: #333; line-height: 1.6; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: auto; background: #fff; padding: 20px 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #0056b3; text-align: center; }
        form { display: flex; flex-direction: column; gap: 15px; }
        input[type="text"] { padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 16px; }
        .tool-groups { display: flex; flex-wrap: wrap; gap: 15px; border: 1px solid #eee; padding: 15px; border-radius: 4px; }
        .tool-groups label { cursor: pointer; }
        button { background-color: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; transition: background-color 0.3s; }
        button:hover { background-color: #0056b3; }
        .footer { text-align: center; margin-top: 20px; font-size: 14px; color: #777; }
    </style>
</head>
<body>
    <div class="container">
        <h1> Doraemon Recon Tool</h1>
        <form action="/recondora" method="GET">
            <label for="domain"><b>Domain or IP Address:</b></label>
            <input type="text" id="domain" name="domain" placeholder="e.g., example.com" required>
            
            <label><b>Select Tool Groups (defaults to 'basic' if none selected):</b></label>
            <div class="tool-groups">
                {% for group in tool_groups %}
                <label>
                    <input type="checkbox" name="tools" value="{{ group }}"> {{ group.title() }}
                </label>
                {% endfor %}
            </div>

            <button type="submit">Run Scan</button>
        </form>
        <p class="footer">Doraemon Cyber Team Bot - Web Interface</p>
    </div>
</body>
</html>
"""

RESULTS_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recon Results for {{ domain }}</title>
    <style>
        body { font-family: monospace; background-color: #1e1e1e; color: #d4d4d4; margin: 0; padding: 20px; }
        .container { max-width: 90%; margin: auto; }
        h1 { color: #569cd6; border-bottom: 1px solid #569cd6; padding-bottom: 10px; }
        h2 { color: #4ec9b0; margin-top: 30px; }
        pre { background-color: #252526; padding: 15px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; font-size: 14px; }
        a { color: #9cdcfe; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Recon Report for: <a href="http://{{ domain }}" target="_blank">{{ domain }}</a></h1>
        <p><a href="/">← Back to scanner</a></p>
        {% for tool, result in results %}
        <h2>[{{ tool.upper() }}]</h2>
        <pre>{{ result }}</pre>
        {% endfor %}
    </div>
</body>
</html>
"""

# Create a Flask app instance
app = Flask(__name__)

@app.route('/')
def home():
    """Renders the main page with a form to run recon."""
    return render_template_string(HOME_PAGE_TEMPLATE, tool_groups=TOOL_GROUPS.keys())

@app.route('/recondora')
async def run_recondora_web():
    """API endpoint to run recon and display results in HTML."""
    domain = request.args.get('domain')
    tool_inputs = request.args.getlist('tools')

    if not domain:
        return "<h1>Error</h1><p>A 'domain' query parameter is required.</p><a href='/'>Go back</a>", 400

    tools_to_run = parse_tool_input(tool_inputs)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_tool(session, domain, tool) for tool in tools_to_run]
        results = await asyncio.gather(*tasks)
    
    return render_template_string(RESULTS_PAGE_TEMPLATE, domain=domain, results=results)


def start():
    """This function starts the simple web server."""
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    start()
