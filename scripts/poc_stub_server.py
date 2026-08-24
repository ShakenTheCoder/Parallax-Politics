#!/usr/bin/env python3
"""Local HTTP stub used only by the CLI browser smoke test."""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.intelligence.poc import analysis_center, compare_variants  # noqa: E402

USER = {
    "id": "00000000-0000-0000-0000-000000000001",
    "username": "poc-reviewer",
    "display_name": "POC Reviewer",
    "role": "principal",
    "has_profile": True,
}

BRIEF_VIEW = {
    "identity": {
        "name": "Maria Santos",
        "position": "Mayor of San Isidro",
        "portrait_url": None,
    },
    "score": {
        "value": 64.2,
        "delta": 2.7,
        "updated_at": "2026-08-24T12:00:00+00:00",
    },
    "watchlist": [
        {
            "is_principal": True,
            "rank": 1,
            "name": "Maria Santos",
            "position": "Mayor of San Isidro",
            "portrait_url": None,
            "score": 64.2,
            "delta": 2.7,
        },
        {
            "is_principal": False,
            "rank": 2,
            "name": "Andres Reyes",
            "position": "Senator",
            "portrait_url": None,
            "score": 60.8,
            "delta": -0.9,
        },
    ],
    "appearances_window_hours": 36,
    "appearances": [
        {
            "id": "appearance-test-1",
            "caption": "Answered questions on the city flood-control program.",
            "source_name": "Public broadcaster",
            "source_url": "https://example.com/source",
            "appeared_at": "2026-08-24T09:30:00+00:00",
        }
    ],
    "latest_opinion": {
        "id": "opinion-test-1",
        "summary": "Coverage focused on implementation details and the timetable for delivery.",
        "importance": "high",
        "generated_at": "2026-08-24T12:00:00+00:00",
        "source_count": 4,
    },
    "previous_opinions": [
        {
            "id": "opinion-test-2",
            "summary": "Regional coverage emphasized the program's expected reach.",
            "importance": "medium",
            "generated_at": "2026-08-23T12:00:00+00:00",
            "source_count": 3,
        },
        {
            "id": "opinion-test-3",
            "summary": "Commentary questioned whether the published timeline was realistic.",
            "importance": "critical",
            "generated_at": "2026-08-22T12:00:00+00:00",
            "source_count": 5,
        },
        {
            "id": "opinion-test-4",
            "summary": "Earlier reports treated the announcement as routine local policy news.",
            "importance": "low",
            "generated_at": "2026-08-21T12:00:00+00:00",
            "source_count": 2,
        },
    ],
    "data_status": "live",
    "notice": "Browser-test fixture; production Brief reads provenance-bearing database snapshots.",
}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/api/v1/auth/me":
            self.send_json(USER)
        elif self.path == "/api/v1/intelligence/brief":
            self.send_json(BRIEF_VIEW)
        elif self.path == "/api/v1/intelligence/analysis":
            self.send_json(analysis_center())
        else:
            self.send_json({"detail": "Not found"}, 404)

    def do_POST(self) -> None:
        if self.path != "/api/v1/intelligence/scenario-comparison":
            self.send_json({"detail": "Not found"}, 404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        self.send_json(compare_variants(payload.get("variants", [])))

    def log_message(self, _format: str, *args: object) -> None:
        return


if __name__ == "__main__":
    port = int(os.environ.get("POC_STUB_PORT", "8011"))
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
