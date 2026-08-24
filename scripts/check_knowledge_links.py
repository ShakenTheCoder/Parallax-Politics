#!/usr/bin/env python3
"""Check HTTP links in the Philippines knowledge bundle.

Usage: python scripts/check_knowledge_links.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "knowledge" / "philippines"
LINK = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")


def main() -> int:
    urls = sorted({url for path in DOCS.glob("*.md") for url in LINK.findall(path.read_text())})
    failures: list[tuple[str, str]] = []
    blocked: list[tuple[str, str]] = []
    for url in urls:
        if urlsplit(url).scheme not in {"http", "https"}:
            failures.append((url, "unsupported URL scheme"))
            continue
        request = Request(  # noqa: S310 - scheme is restricted above
            url, headers={"User-Agent": "Parallax-Knowledge-Link-Check/1.0"}
        )
        try:
            with urlopen(request, timeout=20) as response:  # noqa: S310 - validated above
                if response.status >= 400:
                    failures.append((url, f"HTTP {response.status}"))
        except HTTPError as exc:
            if exc.code in {401, 403, 429}:
                blocked.append((url, f"HTTP {exc.code}"))
            else:
                failures.append((url, f"HTTP {exc.code}"))
        except (TimeoutError, URLError) as exc:
            failures.append((url, str(exc.reason if isinstance(exc, URLError) else exc)))
    for url, reason in failures:
        print(f"FAIL {reason}: {url}")
    for url, reason in blocked:
        print(f"WARN access controlled ({reason}): {url}")
    print(
        f"Checked {len(urls)} unique knowledge links; "
        f"{len(failures)} failed, {len(blocked)} access-controlled warnings."
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
