from flask import Flask, request, render_template_string
import os
import json
import asyncio
import aiohttp

# --- START of ReconDora Logic (Centralized for Web & Bot) ---

# === API TARGETS & DESCRIPTIONS ===
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

# --- HTML Templates (Hacker Theme) ---
HOME_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Doraemon Recon Terminal</title>
    <style>
        :root {
            --background-color: #0d1117;
            --text-color: #c9d1d9;
            --accent-color: #58a6ff;
            --border-color: #30363d;
            --input-bg: #010409;
            --glow-color: rgba(88, 166, 255, 0.5);
        }
        @keyframes typing { from { width: 0 } to { width: 100% } }
        @keyframes blink-caret { from, to { border-color: transparent } 50% { border-color: var(--accent-color); } }
        
        body { font-family: 'Courier New', Courier, monospace; background-color: var(--background-color); color: var(--text-color); margin: 0; padding: 2rem; }
        .container { max-width: 900px; margin: auto; background: var(--background-color); border: 1px solid var(--border-color); padding: 2rem; border-radius: 8px; box-shadow: 0 0 15px rgba(0,0,0,0.2); }
        h1 { 
            color: var(--accent-color);
            display: inline-block;
            overflow: hidden;
            white-space: nowrap;
            border-right: .15em solid var(--accent-color);
            animation: typing 2.5s steps(30, end), blink-caret .75s step-end infinite;
        }
        form { display: flex; flex-direction: column; gap: 20px; }
        .input-group { display: flex; flex-direction: column; gap: 8px; }
        label { font-weight: bold; color: #8b949e; }
        input[type="text"] { background: var(--input-bg); border: 1px solid var(--border-color); color: var(--text-color); padding: 12px; border-radius: 6px; font-size: 16px; font-family: inherit; transition: all 0.3s ease; }
        input[type="text"]:focus { border-color: var(--accent-color); box-shadow: 0 0 8px var(--glow-color); outline: none; }
        .tools-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }
        .tool-item { display: flex; align-items: center; }
        .tool-item label { cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 14px; }
        .tool-item input[type="checkbox"] { accent-color: var(--accent-color); }
        .quick-select { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; border-top: 1px solid var(--border-color); padding-top: 20px; }
        .quick-select button { background-color: var(--border-color); color: var(--text-color); border: 1px solid #4a5058; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-family: inherit; transition: all 0.3s ease; }
        .quick-select button:hover { background-color: var(--accent-color); color: var(--input-bg); border-color: var(--accent-color); }
        .run-button { background-color: var(--accent-color); color: var(--input-bg); padding: 14px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; font-family: inherit; transition: all 0.3s ease; }
        .run-button:hover { box-shadow: 0 0 10px var(--glow-color); }
        .footer { text-align: center; margin-top: 2rem; font-size: 12px; color: #4a5058; }
    </style>
</head>
<body>
    <div class="container">
        <h1>>_ Doraemon Recon Terminal</h1>
        <form action="/recondora" method="GET">
            <div class="input-group">
                <label for="domain">Target Domain / IP:</label>
                <input type="text" id="domain" name="domain" placeholder="example.com" required>
            </div>
            
            <div class="input-group">
                <label>Select Tools (hover for info):</label>
                <div class="tools-grid">
                    {% for tool, description in tool_descriptions.items() %}
                    <div class="tool-item">
                        <label title="{{ description }}">
                            <input type="checkbox" name="tools" value="{{ tool }}"> {{ tool }}
                        </label>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="input-group">
                <label>Quick Select Groups (Optional):</label>
                <div class="quick-select">
                    {% for group_name in tool_groups.keys() %}
                    <button type="button" onclick="selectGroup('{{ group_name }}')">{{ group_name.title() }}</button>
                    {% endfor %}
                </div>
            </div>

            <button class="run-button" type="submit">Execute Scan</button>
        </form>
        <p class="footer">Doraemon Cyber Team</p>
    </div>

    <script>
        const toolGroups = {{ tool_groups_json|safe }};
        const allToolCheckboxes = document.querySelectorAll('input[name="tools"]');

        function selectGroup(groupName) {
            const toolsInGroup = toolGroups[groupName];
            // First, uncheck all boxes
            allToolCheckboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            // Then, check the ones in the selected group
            if (toolsInGroup) {
                toolsInGroup.forEach(toolName => {
                    const checkbox = document.querySelector(`input[value="${toolName}"]`);
                    if (checkbox) {
                        checkbox.checked = true;
                    }
                });
            }
        }
        // Set the 'basic' group as the default selection on page load
        document.addEventListener('DOMContentLoaded', () => {
            selectGroup('basic');
        });
    </script>
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
        :root { --background-color: #0d1117; --text-color: #c9d1d9; --accent-color: #58a6ff; --border-color: #30363d; --pre-bg: #010409; }
        body { font-family: 'Courier New', Courier, monospace; background-color: var(--background-color); color: var(--text-color); margin: 0; padding: 2rem; }
        .container { max-width: 80%; margin: auto; }
        h1 { color: var(--accent-color); border-bottom: 1px solid var(--border-color); padding-bottom: 10px; }
        h2 { color: #39d353; margin-top: 30px; } /* Hacker green for headers */
        pre { background-color: var(--pre-bg); border: 1px solid var(--border-color); padding: 15px; border-radius: 6px; white-space: pre-wrap; word-wrap: break-word; font-size: 14px; line-height: 1.5; }
        a { color: var(--accent-color); text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>>_ Recon Report for: <a href="http://{{ domain }}" target="_blank">{{ domain }}</a></h1>
        <p><a href="/">← New Scan</a></p>
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
    return render_template_string(
        HOME_PAGE_TEMPLATE, 
        tool_descriptions=TOOL_DESCRIPTIONS,
        tool_groups=TOOL_GROUPS,
        tool_groups_json=json.dumps(TOOL_GROUPS)
    )

@app.route('/recondora')
async def run_recondora_web():
    """API endpoint to run recon and display results in HTML."""
    domain = request.args.get('domain')
    # This now gets a list of individual tools selected by the user
    tool_inputs = request.args.getlist('tools')

    if not domain:
        return "<h1>Error</h1><p>A 'domain' query parameter is required.</p><a href='/'>Go back</a>", 400

    # If no tools are selected, the list will be empty. `parse_tool_input` will handle this.
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
