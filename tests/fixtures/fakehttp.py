"""A stand-in for scripts/_common._urlopen that serves canned responses, so that tests never use the network.

    web = FakeWeb({url: Reply(200, body), other_url: [Reply(503), Reply(200, body)]})
    with mock.patch.object(_common, "_urlopen", web):
        ...

A list of replies is served in order (the last one is repeated); an unexpected URL fails the test.
"""

from __future__ import annotations

import email.message
import http
import io
import json
import urllib.error
import urllib.request
import urllib.response
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).resolve().parent


@dataclass
class Reply:
    status: int = 200
    body: bytes = b""
    headers: dict[str, str] = field(default_factory=dict)
    url: str | None = None  # final URL after redirects, if different from the requested one


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def fixture_json(name: str) -> Any:
    return json.loads(fixture_bytes(name))


def json_reply(data: Any, status: int = 200, headers: dict[str, str] | None = None) -> Reply:
    return Reply(status, json.dumps(data).encode(), {"Content-Type": "application/json", **(headers or {})})


class FakeWeb:
    def __init__(self, routes: dict[str, Reply | list[Reply]]) -> None:
        self.routes = {url: list(reply) if isinstance(reply, list) else [reply] for url, reply in routes.items()}
        self.requests: list[urllib.request.Request] = []

    def __call__(self, request: urllib.request.Request, timeout: float | None = None) -> Any:
        url = request.full_url
        self.requests.append(request)
        if url not in self.routes:
            raise AssertionError(f"unexpected request: {url}")
        queue = self.routes[url]
        reply = queue.pop(0) if len(queue) > 1 else queue[0]
        headers = email.message.Message()
        for name, value in reply.headers.items():
            headers[name] = value
        if reply.status >= 400:
            raise urllib.error.HTTPError(url, reply.status, http.HTTPStatus(reply.status).phrase, headers,
                                         io.BytesIO(reply.body))
        return urllib.response.addinfourl(io.BytesIO(reply.body), headers, reply.url or url, reply.status)

    @property
    def urls(self) -> list[str]:
        return [request.full_url for request in self.requests]
