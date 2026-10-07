"""Tests for scripts/indexnow.py: the submission body, waiting for the key file, and the outcome."""

from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests" / "fixtures"))

import _common  # noqa: E402
import indexnow  # noqa: E402
from fakehttp import FakeWeb, Reply  # noqa: E402

BASE = "https://example.github.io/LIST/"
KEY = "0123456789abcdef0123456789abcdef"
SITE = {"base_url": BASE, "indexnow_key": KEY}
SITEMAP = (f"<urlset><url><loc>{BASE}</loc></url><url><loc> {BASE}about.html </loc></url>"
           f"<url><loc>{BASE}about.html</loc></url></urlset>").encode()


class IndexNowTest(unittest.TestCase):
    def setUp(self) -> None:
        for patcher in (mock.patch("time.sleep"), mock.patch("sys.stderr", new_callable=io.StringIO),
                        mock.patch.object(indexnow, "load_yaml", return_value=SITE)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def serve(self, routes: dict) -> FakeWeb:
        web = FakeWeb(routes)
        patcher = mock.patch.object(_common, "_urlopen", web)
        patcher.start()
        self.addCleanup(patcher.stop)
        return web

    def test_payload_names_the_key_file_under_the_base_path(self) -> None:
        body = indexnow.payload(SITE, [BASE, BASE + "about.html"])
        self.assertEqual(body, {"host": "example.github.io", "key": KEY, "keyLocation": f"{BASE}{KEY}.txt",
                                "urlList": [BASE, BASE + "about.html"]})
        with self.assertRaises(ValueError):
            indexnow.payload(SITE, ["https://example.github.io/other/page.html"])

    def test_sitemap_urls_are_read_once_each(self) -> None:
        self.assertEqual(indexnow.sitemap_urls(SITEMAP.decode()), [BASE, BASE + "about.html"])

    def test_submits_once_the_key_file_is_published(self) -> None:
        web = self.serve({BASE + "sitemap.xml": Reply(body=SITEMAP),
                          f"{BASE}{KEY}.txt": [Reply(404), Reply(body=f"{KEY}\n".encode())],
                          indexnow.ENDPOINT: Reply(202)})
        self.assertEqual(indexnow.main([]), 0)
        post = web.requests[-1]
        self.assertEqual(post.get_method(), "POST")
        self.assertEqual(json.loads(post.data)["urlList"], [BASE, BASE + "about.html"])
        self.assertEqual(web.urls.count(f"{BASE}{KEY}.txt"), 2)

    def test_nothing_is_submitted_without_the_key_file(self) -> None:
        web = self.serve({BASE + "sitemap.xml": Reply(body=SITEMAP), f"{BASE}{KEY}.txt": Reply(404)})
        with mock.patch.object(indexnow, "WAIT_TRIES", 2):
            self.assertEqual(indexnow.main([]), 1)
        self.assertNotIn(indexnow.ENDPOINT, web.urls)

    def test_a_refusal_fails_the_run(self) -> None:
        self.serve({BASE + "sitemap.xml": Reply(body=SITEMAP), f"{BASE}{KEY}.txt": Reply(body=KEY.encode()),
                    indexnow.ENDPOINT: Reply(422, b"URLs don't belong to the host")})
        self.assertEqual(indexnow.main([]), 1)


if __name__ == "__main__":
    unittest.main()
