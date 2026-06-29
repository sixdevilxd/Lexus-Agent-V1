"""Internet research helpers for Lexus-Agent.
Free & Termux-friendly: DuckDuckGo HTML search + Reddit public JSON.
Only dependency beyond requests is beautifulsoup4 (pure-Python parser)."""
import requests
from urllib.parse import urlparse, parse_qs, unquote

HEADERS = {"User-Agent": "Mozilla/5.0 (Lexus-Agent; +https://t.me)"}


def _clean_ddg(href):
    if not href:
        return href
    if "duckduckgo.com/l/" in href:
        q = parse_qs(urlparse(href).query)
        if "uddg" in q:
            return unquote(q["uddg"][0])
    if href.startswith("//"):
        return "https:" + href
    return href


def web_search(query, max_results=6):
    """Search the web via DuckDuckGo HTML. Returns list of {title,url,snippet}."""
    from bs4 import BeautifulSoup
    r = requests.post("https://html.duckduckgo.com/html/",
                      data={"q": query}, headers=HEADERS, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for res in soup.select(".result"):
        a = res.select_one(".result__a")
        if not a:
            continue
        url = _clean_ddg(a.get("href"))
        # skip DuckDuckGo ad/redirect noise
        if not url or "duckduckgo.com/y.js" in url or "ad_domain=" in url:
            continue
        snip = res.select_one(".result__snippet")
        out.append({
            "title": a.get_text(strip=True),
            "url": url,
            "snippet": snip.get_text(" ", strip=True) if snip else "",
        })
        if len(out) >= max_results:
            break
    return out or [{"title": "No results", "url": "", "snippet": ""}]


def fetch_url(url, max_chars=3500):
    """Fetch a URL and return cleaned readable text."""
    from bs4 import BeautifulSoup
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "form"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    title = soup.title.get_text(strip=True) if soup.title else ""
    return {"title": title, "url": url, "text": text[:max_chars]}


def reddit_search(query, max_results=8):
    """Search Reddit posts via public JSON (no auth).
    Falls back to a web search scoped to reddit.com if the JSON API is blocked."""
    try:
        r = requests.get("https://www.reddit.com/search.json",
                         params={"q": query, "limit": max_results, "sort": "relevance"},
                         headers=HEADERS, timeout=25)
        r.raise_for_status()
        out = []
        for child in r.json().get("data", {}).get("children", []):
            d = child.get("data", {})
            out.append({
                "title": d.get("title"),
                "subreddit": d.get("subreddit_name_prefixed"),
                "score": d.get("score"),
                "comments": d.get("num_comments"),
                "url": "https://reddit.com" + (d.get("permalink") or ""),
                "text": (d.get("selftext") or "")[:300],
            })
        if out:
            return out
    except Exception:
        pass
    # fallback: web search scoped to reddit
    return web_search(f"{query} site:reddit.com", max_results)


_SITES = {
    "x": "x.com OR twitter.com", "twitter": "twitter.com OR x.com",
    "facebook": "facebook.com", "fb": "facebook.com",
    "instagram": "instagram.com", "ig": "instagram.com",
    "reddit": "reddit.com", "tiktok": "tiktok.com",
    "youtube": "youtube.com", "linkedin": "linkedin.com",
}


def social_search(query, platform="x", max_results=6):
    """Research a social platform by scoping a web search to its domain(s)."""
    site = _SITES.get(platform.lower(), platform)
    if " OR " in site:
        scope = "(" + " OR ".join("site:" + s.strip() for s in site.split("OR")) + ")"
    else:
        scope = "site:" + site
    return web_search(f"{query} {scope}", max_results)
