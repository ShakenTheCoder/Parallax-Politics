"""Collection and cohort privacy policy boundaries."""
from __future__ import annotations

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse


class CollectionPolicyError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedDestination:
    url: str
    hostname: str
    port: int


async def validate_public_destination(url: str) -> ValidatedDestination:
    """Reject credentials, non-web schemes, unusual ports, and non-public IPs.

    DNS is resolved before every outbound request. Redirect destinations must be
    passed through this function separately by the caller.
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise CollectionPolicyError("only http and https sources are supported")
    if not parsed.hostname or parsed.username or parsed.password:
        raise CollectionPolicyError("source URL must contain a public hostname and no credentials")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port not in {80, 443}:
        raise CollectionPolicyError("source URL port is not permitted")

    try:
        records = await asyncio.to_thread(
            socket.getaddrinfo,
            parsed.hostname,
            port,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise CollectionPolicyError("source hostname could not be resolved") from exc
    if not records:
        raise CollectionPolicyError("source hostname has no addresses")

    for record in records:
        address = ipaddress.ip_address(record[4][0])
        if not address.is_global:
            raise CollectionPolicyError("source resolves to a private or reserved network")
    return ValidatedDestination(url=url, hostname=parsed.hostname.lower(), port=port)


def enforce_same_source(url: str, base_url: str, allowed_paths: list[str]) -> None:
    parsed = urlparse(url)
    base = urlparse(base_url)
    if parsed.scheme != base.scheme or parsed.hostname != base.hostname or parsed.port != base.port:
        raise CollectionPolicyError("collection redirects and paths must remain on the registered source")
    if allowed_paths and not any(parsed.path.startswith(prefix) for prefix in allowed_paths):
        raise CollectionPolicyError("requested path is outside the source allowlist")


def enforce_cohort_privacy(sample_size: int, minimum: int = 100) -> None:
    if sample_size < minimum:
        raise CollectionPolicyError(
            f"cohort contains {sample_size} observations; minimum publishable size is {minimum}"
        )

