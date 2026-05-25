from urllib.parse import urlparse


def endpoint_domain(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.netloc:
        return parsed.netloc
    return base_url.rstrip("/")
