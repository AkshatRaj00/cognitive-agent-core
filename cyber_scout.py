import hashlib
import re
from typing import Any, Dict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import TRUSTED_HINTS


class CyberScoutEngine:
    def __init__(self):
        self.timeout = (5, 20)
        self.headers = {
            "User-Agent": "MythosCyberScout/2.0",
            "Accept": "text/plain, text/html, application/json, application/xml, text/xml, */*",
        }

    def _is_html(self, content_type: str, text: str) -> bool:
        ct = (content_type or "").lower()
        return "text/html" in ct or "<html" in text[:500].lower()

    def _extract_visible_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "noscript", "svg", "meta", "link", "head"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        return text[:12000]

    def _trust_score(self, url: str) -> int:
        host = urlparse(url).netloc.lower()
        path = urlparse(url).path.lower()
        hay = f"{host} {path}"
        score = 0
        for hint in TRUSTED_HINTS:
            if hint in hay:
                score += 1
        return score

    def fetch_threat_intelligence_feed(self, feed_url: str) -> Dict[str, Any]:
        if not feed_url.startswith(("http://", "https://")):
            return {"source": feed_url, "status": "FAILED", "reason": "INVALID_PROTOCOL"}

        try:
            response = requests.get(feed_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            raw_text = response.text[:30000]
            normalized_text = self._extract_visible_text(raw_text) if self._is_html(content_type, raw_text) else raw_text[:12000]
            digest = hashlib.sha256(normalized_text.encode("utf-8", errors="ignore")).hexdigest()

            return {
                "source": feed_url,
                "status": "SUCCESS",
                "http_status": response.status_code,
                "content_type": content_type,
                "content_sha256": digest,
                "raw_payload": normalized_text,
                "is_html": self._is_html(content_type, raw_text),
                "trust_score": self._trust_score(feed_url),
            }

        except requests.exceptions.Timeout:
            return {"source": feed_url, "status": "FAILED", "reason": "TIMEOUT"}
        except requests.exceptions.RequestException as e:
            return {"source": feed_url, "status": "FAILED", "reason": f"REQUEST_ERROR: {str(e)}"}
        except Exception as e:
            return {"source": feed_url, "status": "FAILED", "reason": f"INTERNAL_ERROR: {str(e)}"}
