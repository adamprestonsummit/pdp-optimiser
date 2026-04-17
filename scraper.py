import requests
from bs4 import BeautifulSoup
import re


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TIMEOUT = 15


def clean_text(text: str) -> str:
    """Strip excess whitespace and newlines."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def scrape_page(url: str) -> tuple[dict, str | None]:
    """
    Scrape a product page and return structured content.
    Returns (page_data dict, error_message or None).
    """
    page_data = {
        "url": url,
        "page_title": "",
        "meta_description": "",
        "h1": "",
        "h2s": [],
        "price": "",
        "bullets": [],
        "body_text": "",
        "product_name": "",
        "breadcrumb": "",
        "structured_data": "",
    }

    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return page_data, f"Could not fetch page: {str(e)}"

    try:
        soup = BeautifulSoup(response.text, "html.parser")

        # Meta title
        title_tag = soup.find("title")
        if title_tag:
            page_data["page_title"] = clean_text(title_tag.text)

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if not meta_desc:
            meta_desc = soup.find("meta", attrs={"property": "og:description"})
        if meta_desc:
            page_data["meta_description"] = clean_text(meta_desc.get("content", ""))

        # H1
        h1 = soup.find("h1")
        if h1:
            page_data["h1"] = clean_text(h1.text)
            page_data["product_name"] = page_data["h1"]

        # H2s
        h2s = soup.find_all("h2")
        page_data["h2s"] = [clean_text(h.text) for h in h2s[:10] if h.text.strip()]

        # Price (common patterns)
        price_candidates = soup.select(
            "[class*='price'], [class*='Price'], [data-price], [itemprop='price']"
        )
        if price_candidates:
            page_data["price"] = clean_text(price_candidates[0].text)

        # Bullet points / feature lists
        bullet_candidates = []
        for ul in soup.find_all("ul"):
            items = ul.find_all("li")
            # Heuristic: lists with 3-15 short items are likely product features
            if 2 <= len(items) <= 20:
                texts = [clean_text(li.text) for li in items if clean_text(li.text)]
                if texts and all(len(t) < 300 for t in texts):
                    bullet_candidates.extend(texts)
        page_data["bullets"] = bullet_candidates[:20]

        # Breadcrumb
        breadcrumb = soup.find(
            lambda tag: tag.get("aria-label") in ["breadcrumb", "Breadcrumb"]
            or "breadcrumb" in (tag.get("class") or [])
            or "breadcrumb" in (tag.get("id") or "")
        )
        if breadcrumb:
            page_data["breadcrumb"] = clean_text(breadcrumb.text)

        # Structured data (JSON-LD)
        json_ld = soup.find("script", attrs={"type": "application/ld+json"})
        if json_ld and json_ld.string:
            page_data["structured_data"] = json_ld.string[:2000]

        # Main body text - remove nav, header, footer, script, style
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        # Try to find main content area
        main_content = (
            soup.find("main")
            or soup.find(id="main")
            or soup.find(id="content")
            or soup.find(class_=re.compile(r"(product|pdp|content|description)", re.I))
            or soup.body
        )

        if main_content:
            raw_text = main_content.get_text(separator=" ")
            page_data["body_text"] = clean_text(raw_text)[:5000]

    except Exception as e:
        return page_data, f"Parse error: {str(e)}"

    return page_data, None
