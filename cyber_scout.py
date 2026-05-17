import hashlib
import logging
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class CyberScoutEngine:
    def __init__(self):
        self.timeout = (5, 12)
        self.headers = {
            "User-Agent": "MythosCyberScout/1.0",
            "Accept": "text/plain, text/html, application/json, application/xml, text/xml, */*",
        }

    def fetch_threat_intelligence_feed(self, feed_url: str) -> Dict[str, Any]:
        if not feed_url.startswith(("http://", "https://")):
            return {
                "source": feed_url,
                "status": "FAILED",
                "reason": "INVALID_PROTOCOL",
            }

        try:
            response = requests.get(feed_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            raw_text = response.text[:15000]
            digest = hashlib.sha256(raw_text.encode("utf-8", errors="ignore")).hexdigest()

            return {
                "source": feed_url,
                "status": "SUCCESS",
                "http_status": response.status_code,
                "content_type": content_type,
                "content_sha256": digest,
                "raw_payload": raw_text,
            }

        except requests.exceptions.Timeout:
            return {"source": feed_url, "status": "FAILED", "reason": "TIMEOUT"}
        except requests.exceptions.RequestException as e:
            return {"source": feed_url, "status": "FAILED", "reason": f"REQUEST_ERROR: {str(e)}"}
        except Exception as e:
            return {"source": feed_url, "status": "FAILED", "reason": f"INTERNAL_ERROR: {str(e)}"}
