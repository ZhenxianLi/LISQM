#!/usr/bin/env python3
"""Tell the search engines that take IndexNow submissions about the pages of the website.

IndexNow (https://www.indexnow.org) is a shared protocol: one submission reaches Bing (whose index also serves
DuckDuckGo, Yahoo and the search of ChatGPT and Copilot), Yandex, Naver, Seznam and Yep. Google and Baidu do not
take part; they are reached through their webmaster tools (see CONTRIBUTING.md).

The URLs are read from the published sitemap and the key from `indexnow_key` in data/site.yaml. scripts/build.py
publishes the key as <key>.txt next to the pages; its address is sent as keyLocation, because the website lives
under a path of its host (…/LISQM/), and a key file there vouches for the URLs under that path. The key is public
by design. Before submitting, the script waits until the published key file answers with the key, so that it can
run right after a deployment.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import _common
from _common import DATA_DIR, FetchError, Http, load_yaml, log, user_agent

ENDPOINT = "https://api.indexnow.org/indexnow"
WAIT_TRIES = 10  # attempts to find the published key file
WAIT_SECONDS = 15.0


def payload(site: dict, urls: list[str]) -> dict:
    """The JSON body of an IndexNow submission for the URLs, which must all be under the site's base URL."""
    base, key = site["base_url"], site["indexnow_key"]
    outside = [url for url in urls if not url.startswith(base)]
    if outside:
        raise ValueError(f"not under {base}: {', '.join(outside[:3])}")
    return {"host": urllib.parse.urlsplit(base).hostname, "key": key, "keyLocation": f"{base}{key}.txt",
            "urlList": urls}


def sitemap_urls(xml: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)))


def wait_for_key(http: Http, location: str, key: str) -> bool:
    for attempt in range(1, WAIT_TRIES + 1):
        try:
            if http.get(location).decode("utf-8", "replace").strip() == key:
                return True
            log(f"{location} does not contain the key yet")
        except FetchError as err:
            log(f"{location}: {err}")
        if attempt < WAIT_TRIES:
            time.sleep(WAIT_SECONDS)
    return False


def submit(endpoint: str, body: dict) -> tuple[int, str]:
    """POST the submission; (HTTP status, response text). 200 and 202 mean accepted."""
    request = urllib.request.Request(endpoint, data=json.dumps(body).encode("utf-8"), method="POST",
                                     headers={"Content-Type": "application/json; charset=utf-8",
                                              "User-Agent": user_agent()})
    try:
        with _common._urlopen(request, 60.0) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--endpoint", default=ENDPOINT, help=f"IndexNow endpoint (default: {ENDPOINT})")
    parser.add_argument("--dry-run", action="store_true", help="print the submission instead of sending it")
    args = parser.parse_args(argv)

    site = load_yaml(DATA_DIR / "site.yaml") or {}
    if not site.get("indexnow_key"):
        log("No indexnow_key in data/site.yaml: nothing to submit.")
        return 0
    http = Http()
    try:
        urls = sitemap_urls(http.get(site["base_url"] + "sitemap.xml").decode("utf-8"))
    except FetchError as err:
        log(f"The sitemap could not be read: {err}")
        return 1
    body = payload(site, urls)
    if args.dry_run:
        print(json.dumps(body, indent=1))
        return 0
    if not wait_for_key(http, body["keyLocation"], body["key"]):
        log(f"The key file {body['keyLocation']} is not published; nothing was submitted.")
        return 1
    status, text = submit(args.endpoint, body)
    if status in (200, 202):
        log(f"Submitted {len(urls)} URLs to {args.endpoint}: HTTP {status}"
            + (" (the key is being checked)" if status == 202 else ""))
        return 0
    log(f"{args.endpoint} refused the submission: HTTP {status} {text.strip()[:300]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
