import asyncio
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from collections import deque

class AdvancedCrawler:
    def __init__(self, base_url, max_depth=2, max_pages=10):
        self.base_url = base_url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited = set()
        self.discovered_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TelegramBotCrawler/1.0"
        })
    
    async def crawl(self):
        queue = deque([(self.base_url, 0)])
        
        while queue and len(self.visited) < self.max_pages:
            url, depth = queue.popleft()
            
            if depth > self.max_depth:
                continue
                
            if url in self.visited:
                continue
                
            try:
                response = await asyncio.to_thread(
                    self.session.get,
                    url,
                    timeout=5
                )
                response.raise_for_status()
                
                self.visited.add(url)
                self.discovered_urls.add(url)
                
                if "text/html" in response.headers.get("Content-Type", ""):
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # Extract all possible endpoints
                    for element in soup.find_all(["a", "form", "link"]):
                        new_url = None
                        
                        if element.name == "a" and element.get("href"):
                            new_url = urljoin(url, element["href"])
                        elif element.name == "form" and element.get("action"):
                            new_url = urljoin(url, element["action"])
                        elif element.name == "link" and element.get("href"):
                            new_url = urljoin(url, element["href"])
                            
                        if new_url and self._is_valid_url(new_url):
                            if new_url not in self.visited:
                                queue.append((new_url, depth + 1))
                                
                await asyncio.sleep(0.5)  # Be polite
                
            except Exception:
                continue
    
    def _is_valid_url(self, url):
        parsed = urlparse(url)
        base_parsed = urlparse(self.base_url)
        return (
            parsed.scheme in ["http", "https"]
            and parsed.netloc == base_parsed.netloc
            and not parsed.path.endswith((".jpg", ".png", ".pdf"))  # Skip static files
        )
    
    def get_discovered_urls(self):
        return list(self.discovered_urls)