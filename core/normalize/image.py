from bs4 import BeautifulSoup
from typing import Optional

# Placeholder for missing images
PLACEHOLDER = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2Y0ZjRmNCIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTIiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4="

def verify_image(url: str, timeout: float = 4.0) -> bool:
    """Verify if image URL is accessible without downloading the full file."""
    try:
        # ленивый импорт, чтобы не требовать requests без нужды
        import requests  # type: ignore
        resp = requests.head(url, timeout=timeout)
        # многие бэкенды режут HEAD → fallback на GET (стримим, чтобы не качать тело)
        if resp.status_code >= 400 or resp.status_code == 405:
            resp = requests.get(url, timeout=timeout, stream=True)
        return 200 <= resp.status_code < 300
    except Exception:
        return False

def choose_image(html: str, jsonld_image: Optional[str] = None) -> Optional[str]:
    """
    Smart image selection with priority:
    1. og:image (highest priority - SEO best practice)
    2. JSON-LD image (structured data)
    3. CSS img src (DOM fallback)
    """
    if not html:
        return jsonld_image
    
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. og:image (highest priority)
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        return og_image["content"]
    
    # 2. JSON-LD image (if provided)
    if jsonld_image:
        return jsonld_image
    
    # 3. CSS img src (DOM fallback)
    img = soup.find("img")
    if img and img.get("src"):
        return img["src"]
    
    return None

def normalize_image_url(url: str, base_url: str = "") -> str:
    """Normalize relative image URLs to absolute."""
    if not url:
        return ""
    
    if url.startswith(("http://", "https://")):
        return url
    
    if url.startswith("//"):
        return f"https:{url}"
    
    if url.startswith("/"):
        # Remove protocol and domain from base_url
        if base_url:
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{url}"
        return url
    
    # Relative URL - assume same directory
    if base_url:
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        # Remove filename from path, keep directory
        path_parts = parsed.path.split('/')
        if path_parts[-1] and '.' in path_parts[-1]:  # Has filename
            path_parts = path_parts[:-1]  # Remove filename
        path = '/'.join(path_parts)
        # Clean up path and avoid double slashes
        clean_path = path.rstrip('/')
        return f"{parsed.scheme}://{parsed.netloc}{clean_path}/{url}"
    
    return url
