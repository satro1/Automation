import os
import shlex
import subprocess
from typing import List
from typing import Optional
import urllib.parse

try:
    import requests
    from bs4 import BeautifulSoup
except Exception:
    # If these imports fail, the search tool will return a helpful message.
    requests = None
    BeautifulSoup = None


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


def run_cmd(command: str, timeout: int = 30) -> str:
    """Run a shell command and return its stdout/stderr.

    WARNING: All previous safety checks (environment guard and blacklist)
    have been removed. This will execute the provided command directly in
    the system shell. Use with extreme caution.
    """
    try:
        # Execute via the system shell so the agent can run arbitrary commands.
        completed = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        out = completed.stdout.strip()
        err = completed.stderr.strip()
        return (out + ("\n" + err if err else "")).strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Failed to execute command: {e}"


def search_and_scrape(query: str, top_n: int = 3, snippet_len: int = 500, timeout: int = 10) -> str:
    """Search the web for `query` and scrape the top N result pages for up-to-date info.

    This function uses DuckDuckGo's HTML search endpoint to find result links, then
    fetches each result and extracts a short snippet (meta description or first
    paragraph). Returns a plain-text aggregation of titles, URLs and snippets.

    Notes and caveats:
    - Requires `requests` and `beautifulsoup4`. If they're not installed the
      function returns instructions to install them.
    - This is a simple scraper intended for convenience. It does not implement
      advanced politeness (robots.txt parsing), rate limiting, or JS rendering.
      Use responsibly and respect site terms of service.
    """
    if requests is None or BeautifulSoup is None:
        return (
            "The search tool requires the 'requests' and 'beautifulsoup4' packages.\n"
            "Install with: pip install requests beautifulsoup4\n"
        )

    headers = {"User-Agent": "Mozilla/5.0 (compatible; AutomationAgent/1.0)"}
    try:
        resp = requests.get("https://html.duckduckgo.com/html/", params={"q": query}, headers=headers, timeout=timeout)
        resp.raise_for_status()
    except Exception as e:
        return f"Search request failed: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    # Try the DuckDuckGo result selector first
    for a in soup.select("a.result__a"):
        href = a.get("href")
        title = a.get_text().strip()
        if href and href.startswith("/"):
            # DuckDuckGo sometimes uses relative redirect links; try to extract uddg param
            parsed = urllib.parse.urlparse(href)
            q = urllib.parse.parse_qs(parsed.query).get("uddg")
            if q:
                href = q[0]
        if href and href.startswith("http"):
            results.append((title, href))
        if len(results) >= top_n:
            break

    # Fallback: grab any external links
    if not results:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            title = a.get_text().strip() or href
            if href.startswith("http") and "duckduckgo.com" not in href:
                results.append((title, href))
            if len(results) >= top_n:
                break

    if not results:
        return "No search results found."

    aggregated = []
    for title, url in results[:top_n]:
        try:
            page = requests.get(url, headers=headers, timeout=timeout)
            page.raise_for_status()
            page_soup = BeautifulSoup(page.text, "html.parser")
            meta = page_soup.find("meta", attrs={"name": "description"}) or page_soup.find("meta", attrs={"property": "og:description"})
            if meta and meta.get("content"):
                desc = meta["content"].strip()
            else:
                p = page_soup.find("p")
                desc = p.get_text().strip() if p else ""
            snippet = desc[:snippet_len]
            aggregated.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}")
        except Exception as e:
            aggregated.append(f"Title: {title}\nURL: {url}\nError fetching page: {e}")

    return "\n\n".join(aggregated)

tools = [get_weather, run_cmd, search_and_scrape]