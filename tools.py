import os
import subprocess, urllib.parse, requests
from typing import Optional
from bs4 import BeautifulSoup
import yfinance as yf, pandas as pd

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


def get_stock_quote(symbol: str) -> str:
    """Return a short summary quote for the given stock symbol using yfinance.

    Example output: "AAPL — 175.23 USD (+1.2%) — Open: 174.00 Prev Close: 173.00"
    """
    if yf is None:
        return "The stock tool requires 'yfinance' and 'pandas'. Install with: pip install yfinance pandas"

    # Try a lightweight public CSV endpoint (Stooq) first to avoid Yahoo rate limits.
    try:
        s_param = symbol.lower()
        if "." not in s_param:
            # assume US ticker if no exchange provided
            s_param = f"{s_param}.us"
        r = requests.get(
            "https://stooq.com/q/l/",
            params={"s": s_param, "f": "sd2t2ohlcv", "h": "", "e": "csv"},
            timeout=5,
        )
        if r.ok:
            lines = [l for l in r.text.splitlines() if l.strip()]
            if len(lines) >= 2:
                # CSV: Symbol,Date,Time,Open,High,Low,Close,Volume
                parts = lines[1].split(',')
                if len(parts) >= 8:
                    close = parts[6]
                    return f"{symbol.upper()} — {close} (source: stooq)"
    except Exception:
        pass

    # Try using yfinance next: fast_info, then Ticker.info, then history as fallback.
    try:
        t = yf.Ticker(symbol)
        price = None
        prev = None

        # fast_info is a lightweight source when available
        try:
            fi = getattr(t, 'fast_info', None)
            if fi:
                price = fi.get('last_price') or fi.get('last_trade_price') or fi.get('last_price')
                prev = fi.get('previous_close') or fi.get('previous_close')
        except Exception:
            price = None

        # Try Ticker.info which may contain regularMarketPrice
        if price is None:
            try:
                info = t.info
                price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose')
                prev = info.get('regularMarketPreviousClose') or info.get('previousClose') or info.get('open')
            except Exception:
                pass

        # Last-resort: fetch recent history and derive last close
        if price is None:
            hist = t.history(period='5d', interval='1m')
            if not hist.empty:
                last = hist['Close'].dropna()
                if not last.empty:
                    price = float(last.iloc[-1])
                    prev = float(last.iloc[-2]) if len(last) >= 2 else None
                else:
                    return f"No recent price data for {symbol}"
            else:
                return f"No recent price data for {symbol}"

        change = None
        pct = None
        if prev:
            change = price - prev
            try:
                pct = (change / prev) * 100
            except Exception:
                pct = None

        out = f"{symbol.upper()} — {price}"
        if pct is not None:
            out += f" ({change:+.2f}, {pct:+.2f}%)"
        if prev:
            out += f" — Prev Close: {prev}"
        return out
    except Exception as e:
        return f"Failed to fetch quote for {symbol}: {e}"


def get_historical(symbol: str, period: str = '1mo', interval: str = '1d', rows: int = 30) -> str:
    """Return recent historical OHLC data for `symbol` as plain text.

    period examples: '1d','5d','1mo','3mo','1y','5y'
    interval examples: '1m','5m','1d','1wk'
    """
    if yf is None or pd is None:
        return "The historical data tool requires 'yfinance' and 'pandas'. Install with: pip install yfinance pandas"

    try:
        t = yf.Ticker(symbol)
        hist = t.history(period=period, interval=interval)
        if hist.empty:
            return f"No historical data for {symbol} with period={period} interval={interval}"
        # Take last `rows` rows
        df = hist[['Open', 'High', 'Low', 'Close', 'Volume']].tail(rows)
        # Format into a compact CSV-style string
        lines = ["Date,Open,High,Low,Close,Volume"]
        for idx, row in df.iterrows():
            date = idx.strftime('%Y-%m-%d %H:%M') if hasattr(idx, 'strftime') else str(idx)
            lines.append(f"{date},{row['Open']:.2f},{row['High']:.2f},{row['Low']:.2f},{row['Close']:.2f},{int(row['Volume'])}")
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to fetch historical data for {symbol}: {e}"


def get_options_chain(symbol: str, date: Optional[str] = None, top_n: int = 10) -> str:
    """Return an options chain summary for `symbol`.

    If `date` is None, uses the nearest expiry. Date should be a string in
    the format returned by yfinance (YYYY-MM-DD).
    """
    if yf is None or pd is None:
        return "The options tool requires 'yfinance' and 'pandas'. Install with: pip install yfinance pandas"

    try:
        t = yf.Ticker(symbol)
        expiries = t.options
        if not expiries:
            return f"No options data available for {symbol}"
        use_date = date or expiries[0]
        if use_date not in expiries:
            # try to find closest
            use_date = expiries[0]

        chain = t.option_chain(use_date)
        calls = chain.calls.head(top_n)
        puts = chain.puts.head(top_n)

        def df_to_text(df):
            lines = []
            for _, r in df.iterrows():
                lines.append(f"{int(r['contractSymbol']) if 'contractSymbol' in r and isinstance(r['contractSymbol'], (int,)) else r.get('contractSymbol', '')}: strike={r.get('strike','')}, last={r.get('lastPrice','')}, bid={r.get('bid','')}, ask={r.get('ask','')}, vol={int(r.get('volume') or 0)}")
            return "\n".join(lines) or "(no rows)"

        out = [f"Options for {symbol} expiry {use_date}", "\nCalls:\n" + df_to_text(calls), "\nPuts:\n" + df_to_text(puts)]
        return "\n\n".join(out)
    except Exception as e:
        return f"Failed to fetch options chain for {symbol}: {e}"


# export new tools
tools.extend([get_stock_quote, get_historical, get_options_chain])


def send_gmail(to_address: str, subject: str, body: str, cc: Optional[str] = None, bcc: Optional[str] = None, html: bool = False) -> str:
    """Send an email via Gmail SMTP.

    Authentication:
    - Provide credentials via environment variables GMAIL_USER and GMAIL_PASS.
      GMAIL_PASS should be an app password if your account has 2FA.
    - Example:
      export GMAIL_USER="you@gmail.com"
      export GMAIL_PASS="your_app_password"

    Returns a status message on success or instructions on missing credentials.
    """
    import smtplib
    from email.message import EmailMessage

    user = os.environ["GMAIL_USER"]
    password = os.environ["GMAIL_PASS"]
    print("user:", user)
    print("password:", password)
    if not user or not password:
        return ("Missing Gmail credentials. Set environment variables GMAIL_USER and GMAIL_PASS.\n"
                "If you use 2FA, create an app password in your Google Account and use it as GMAIL_PASS.")

    msg = EmailMessage()
    msg['From'] = user
    msg['To'] = to_address
    if cc:
        msg['Cc'] = cc
    msg['Subject'] = subject
    if html:
        msg.add_alternative(body, subtype='html')
    else:
        msg.set_content(body)

    recipients = [to_address]
    if cc:
        recipients += [c.strip() for c in cc.split(',') if c.strip()]
    if bcc:
        recipients += [b.strip() for b in bcc.split(',') if b.strip()]

    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg, from_addr=user, to_addrs=recipients)
        return f"Email sent to {to_address} (cc={cc or ''} bcc={bcc or ''})"
    except Exception as e:
        return f"Failed to send email: {e}"


def read_gmail(folder: str = 'INBOX', criteria: str = 'ALL', limit: int = 10) -> str:
    """Read messages from Gmail via IMAP and return a short summary.

    Authentication: same as send_gmail (GMAIL_USER / GMAIL_PASS env vars).
    `criteria` is an IMAP search criteria string, e.g., 'UNSEEN', 'FROM "abc@"', 'SINCE 01-Jan-2025', or 'ALL'.
    """
    import imaplib
    import email

    user = os.environ["GMAIL_USER"]
    password = os.environ["GMAIL_PASS"]
    print("user:", user)
    print("password:", password)
    if not user or not password:
        return ("Missing Gmail credentials. Set environment variables GMAIL_USER and GMAIL_PASS.\n"
                "If you use 2FA, create an app password in your Google Account and use it as GMAIL_PASS.")

    try:
        imap = imaplib.IMAP4_SSL('imap.gmail.com')
        imap.login(user, password)
        imap.select(folder)
        typ, data = imap.search(None, criteria)
        if typ != 'OK':
            imap.logout()
            return f"IMAP search failed: {typ}"
        ids = data[0].split()
        if not ids:
            imap.logout()
            return "No messages found."
        # get last `limit` messages
        ids = ids[-limit:]
        summaries = []
        for num in reversed(ids):
            typ, msg_data = imap.fetch(num, '(RFC822)')
            if typ != 'OK':
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            subj = msg.get('Subject', '(no subject)')
            frm = msg.get('From', '')
            date = msg.get('Date', '')
            # extract a short snippet
            snippet = ''
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    if ctype == 'text/plain' and not part.get('Content-Disposition'):
                        try:
                            snippet = part.get_payload(decode=True).decode(errors='ignore').strip()
                            break
                        except Exception:
                            continue
            else:
                try:
                    snippet = msg.get_payload(decode=True).decode(errors='ignore').strip()
                except Exception:
                    snippet = ''
            snippet = (snippet or '')[:400].replace('\n', ' ')
            summaries.append(f"From: {frm}\nSubject: {subj}\nDate: {date}\nSnippet: {snippet}")
        imap.logout()
        return "\n\n".join(summaries)
    except Exception as e:
        return f"Failed to read Gmail: {e}"


# add gmail tools to exported list
tools.extend([send_gmail, read_gmail])