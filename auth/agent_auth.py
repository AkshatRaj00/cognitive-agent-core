"""agent_auth.py — JWT-based authentication and role-based access control."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """Built-in agent roles."""
    GUEST = "guest"
    USER = "user"
    OPERATOR = "operator"
    ADMIN = "admin"


PERMISSIONS: dict[Role, set[str]] = {
    Role.GUEST:    {"read"},
    Role.USER:     {"read", "write"},
    Role.OPERATOR: {"read", "write", "execute", "sandbox"},
    Role.ADMIN:    {"read", "write", "execute", "sandbox", "admin", "config"},
}


@dataclass
class TokenPayload:
    """Decoded JWT payload."""
    sub: str                    # subject (user id / agent id)
    role: Role
    exp: float                  # expiry epoch
    iat: float                  # issued-at epoch
    jti: str = field(default_factory=lambda: str(uuid4())[:8])
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return time.time() > self.exp

    @property
    def permissions(self) -> set[str]:
        return PERMISSIONS.get(self.role, set())

    def has_permission(self, perm: str) -> bool:
        return perm in self.permissions


class AgentAuth:
    """Minimal HMAC-SHA256 JWT implementation for agent authentication.

    This is an intentionally dependency-free implementation suitable for
    internal agent-to-agent communication and API gateway guards.
    For production internet-facing APIs, use a battle-tested library
    such as ``python-jose`` or ``PyJWT`` backed by RS256 keys.

    Args:
        secret:          HMAC signing secret (keep out of version control).
        access_ttl:      Seconds until an access token expires.
        refresh_ttl:     Seconds until a refresh token expires.
    """

    _HEADER = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()

    def __init__(
        self,
        secret: str,
        *,
        access_ttl: float = 3600,
        refresh_ttl: float = 86_400 * 7,
    ) -> None:
        if not secret:
            raise ValueError("secret must not be empty")
        self._secret = secret.encode()
        self.access_ttl = access_ttl
        self.refresh_ttl = refresh_ttl
        self._revoked: set[str] = set()   # revoked jti values

    # ------------------------------------------------------------------
    # Token creation
    # ------------------------------------------------------------------

    def create_access_token(self, subject: str, role: Role = Role.USER, **meta: Any) -> str:
        """Issue a signed access token for *subject*."""
        payload = TokenPayload(
            sub=subject,
            role=role,
            iat=time.time(),
            exp=time.time() + self.access_ttl,
            metadata=meta,
        )
        return self._sign(payload)

    def create_refresh_token(self, subject: str, role: Role = Role.USER) -> str:
        """Issue a long-lived refresh token."""
        payload = TokenPayload(
            sub=subject,
            role=role,
            iat=time.time(),
            exp=time.time() + self.refresh_ttl,
        )
        return self._sign(payload)

    def refresh(self, refresh_token: str) -> str:
        """Exchange a valid refresh token for a new access token."""
        payload = self.verify(refresh_token)
        return self.create_access_token(payload.sub, payload.role)

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify(self, token: str) -> TokenPayload:
        """Verify signature, expiry, and revocation. Raises ValueError on failure."""
        try:
            header_b64, payload_b64, sig_b64 = token.split(".")
        except ValueError:
            raise ValueError("Malformed token (expected 3 segments).")

        expected_sig = self._compute_sig(f"{header_b64}.{payload_b64}")
        if not hmac.compare_digest(expected_sig, sig_b64):
            raise ValueError("Token signature verification failed.")

        raw = json.loads(base64.urlsafe_b64decode(self._pad(payload_b64)))
        payload = TokenPayload(
            sub=raw["sub"],
            role=Role(raw["role"]),
            exp=raw["exp"],
            iat=raw["iat"],
            jti=raw.get("jti", ""),
            metadata=raw.get("metadata", {}),
        )

        if payload.is_expired:
            raise ValueError("Token has expired.")
        if payload.jti in self._revoked:
            raise ValueError("Token has been revoked.")

        return payload

    def revoke(self, token: str) -> None:
        """Add token's JTI to the revocation list (in-memory only)."""
        try:
            _, payload_b64, _ = token.split(".")
            raw = json.loads(base64.urlsafe_b64decode(self._pad(payload_b64)))
            self._revoked.add(raw.get("jti", ""))
            logger.info("Token %s revoked.", raw.get("jti", "")[:8])
        except Exception:  # noqa: BLE001
            pass

    def require_permission(self, token: str, permission: str) -> TokenPayload:
        """Verify token and assert it has *permission*. Raises ValueError."""
        payload = self.verify(token)
        if not payload.has_permission(permission):
            raise ValueError(
                f"Role '{payload.role}' lacks permission '{permission}'."
            )
        return payload

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sign(self, payload: TokenPayload) -> str:
        raw = {
            "sub": payload.sub,
            "role": payload.role.value,
            "exp": payload.exp,
            "iat": payload.iat,
            "jti": payload.jti,
            "metadata": payload.metadata,
        }
        payload_b64 = base64.urlsafe_b64encode(json.dumps(raw).encode()).rstrip(b"=").decode()
        signing_input = f"{self._HEADER}.{payload_b64}"
        sig = self._compute_sig(signing_input)
        return f"{signing_input}.{sig}"

    def _compute_sig(self, data: str) -> str:
        digest = hmac.new(self._secret, data.encode(), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

    @staticmethod
    def _pad(b64: str) -> bytes:
        padding = 4 - len(b64) % 4
        return (b64 + "=" * padding).encode()
