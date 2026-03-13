import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_url(url: str, max_pages: int = 10) -> Dict[str, str]:
    """Scrape content from a URL and optionally crawl internal links."""
    results = {}
    visited = set()
    to_visit = [url]
    base_domain = urlparse(url).netloc

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)

        if current_url in visited:
            continue

        try:
            logger.info(f"Scraping: {current_url}")
            response = requests.get(current_url, timeout=10, verify=False)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text(separator="\n", strip=True)
            text = "\n".join(line for line in text.split("\n") if line.strip())

            if text:
                results[current_url] = text

            visited.add(current_url)

            if len(visited) < max_pages:
                for link in soup.find_all("a", href=True):
                    full_url = urljoin(current_url, link["href"])
                    parsed = urlparse(full_url)

                    if parsed.netloc == base_domain and full_url not in visited:
                        to_visit.append(full_url)

        except Exception as e:
            logger.error(f"Error scraping {current_url}: {e}")
            continue

    return results


if __name__ == "__main__":
    test_url = "https://example.com"
    content = scrape_url(test_url, max_pages=2)
    for url, text in content.items():
        print(f"\n=== {url} ===")
        print(text[:500])
