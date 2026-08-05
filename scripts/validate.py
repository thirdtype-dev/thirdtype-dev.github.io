#!/usr/bin/env python3
"""Deterministic, dependency-free checks for STS-001-r1 static output."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://www.thirdtype.net/"
SOCIAL_IMAGE_URL = BASE_URL + "assets/og.png"
SOCIAL_IMAGE_WIDTH = 1730
SOCIAL_IMAGE_HEIGHT = 909

STORE_LINKS = {
    "https://play.google.com/store/apps/details?id=com.thirdtype.carrotcard": "carrotcard",
    "https://apps.apple.com/kr/app/id6787031350": "carrotcard",
    "https://play.google.com/store/apps/details?id=com.maedo.signal": "maedo-signal",
    "https://play.google.com/store/apps/details?id=com.thirdtype.gpsspeed": "gps-speed-go",
    "https://apps.apple.com/kr/app/gps-speed-go/id6789569473": "gps-speed-go",
    "https://play.google.com/store/apps/details?id=com.thirdtype.ttcal": "ttcal",
    "https://apps.apple.com/kr/app/id6785738560": "ttcal",
    "https://play.google.com/store/apps/details?id=com.thirdtype.retrotimestamp": "retro-timestamp",
    "https://play.google.com/store/apps/details?id=com.thirdtype.carsick": "motion-ease",
}

DETAIL_LINK_COUNTS = {
    "carrotcard": 2,
    "maedo-signal": 1,
    "gps-speed-go": 2,
    "ttcal": 2,
    "retro-timestamp": 1,
    "motion-ease": 1,
}

EXPECTED_ROUTES = [
    "apps/carrotcard/",
    "apps/maedo-signal/",
    "apps/gps-speed-go/",
    "apps/ttcal/",
    "apps/retro-timestamp/",
    "apps/motion-ease/",
]

CANONICAL_PAGE_RELATIVE = [
    Path("index.html"),
    Path("404.html"),
    *(Path(route) / "index.html" for route in EXPECTED_ROUTES),
]

PROHIBITED_TERMS = (
    "평점",
    "별점",
    "다운로드 수",
    "다운로드수",
    "수상 경력",
    "수상경력",
    "고객 후기",
    "고객후기",
    "생년월일",
    "주민등록번호",
    "주민번호",
    "발급번호",
    "검증번호",
    "정부 문서",
    "정부문서",
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.canonical = ""
        self.meta: dict[tuple[str, str], str] = {}
        self.h1: list[str] = []
        self.hrefs: list[tuple[str, dict[str, str]]] = []
        self.srcs: list[str] = []
        self.jsonld: list[str] = []
        self._in_title = False
        self._in_jsonld = False
        self._title_chunks: list[str] = []
        self._jsonld_chunks: list[str] = []
        self._in_h1 = False
        self._h1_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = data.get("name") or data.get("property")
            if key:
                self.meta[(key, "content")] = data.get("content", "")
            if data.get("name") == "description":
                self.description = data.get("content", "")
        elif tag == "link" and data.get("rel", "").lower() == "canonical":
            self.canonical = data.get("href", "")
        elif tag == "h1":
            self._in_h1 = True
            self._h1_chunks = []
        elif tag == "a":
            self.hrefs.append((data.get("href", ""), data))
        elif tag == "img":
            self.srcs.append(data.get("src", ""))
        elif tag == "script" and data.get("type") == "application/ld+json":
            self._in_jsonld = True
            self._jsonld_chunks = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
            self.title = "".join(self._title_chunks).strip()
        elif tag == "h1":
            self._in_h1 = False
            self.h1.append("".join(self._h1_chunks).strip())
        elif tag == "script" and self._in_jsonld:
            self._in_jsonld = False
            self.jsonld.append("".join(self._jsonld_chunks).strip())

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_chunks.append(data)
        if self._in_h1:
            self._h1_chunks.append(data)
        if self._in_jsonld:
            self._jsonld_chunks.append(data)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def page_files() -> list[Path]:
    """Return only the pages owned by this static-site outcome.

    The destination GitHub Pages repository may contain unrelated legacy HTML
    paths. They are intentionally outside this validator's canonical surface.
    """
    return [ROOT / relative for relative in CANONICAL_PAGE_RELATIVE if (ROOT / relative).is_file()]


def route_for(path: Path) -> str:
    relative = path.relative_to(ROOT)
    if relative == Path("index.html"):
        return ""
    if relative == Path("404.html"):
        return "404.html"
    return str(relative.parent).replace("\\", "/") + "/"


def expected_canonical(route: str) -> str:
    return BASE_URL if route == "" else urljoin(BASE_URL, route)


def check_local_target(source: Path, value: str, errors: list[str], kind: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        return
    target = parsed.path or "."
    resolved = (source.parent / target).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        fail(errors, f"{source.relative_to(ROOT)}: {kind} escapes project: {value}")
        return
    if resolved.is_dir():
        resolved = resolved / "index.html"
    if not resolved.exists():
        fail(errors, f"{source.relative_to(ROOT)}: missing local {kind}: {value}")


def check_images(errors: list[str]) -> None:
    icon_dir = ROOT / "assets" / "icons"
    expected = [f"{slug}.webp" for slug in ("carrotcard", "maedo-signal", "gps-speed-go", "ttcal", "retro-timestamp", "motion-ease")]
    for filename in expected:
        path = icon_dir / filename
        if not path.is_file():
            fail(errors, f"missing icon: {path.relative_to(ROOT)}")
            continue
        header = path.read_bytes()[:12]
        if not (header[:4] == b"RIFF" and header[8:12] == b"WEBP"):
            fail(errors, f"icon is not a WebP image: {path.relative_to(ROOT)}")


def check_social_image(errors: list[str]) -> None:
    path = ROOT / "assets" / "og.png"
    if not path.is_file():
        fail(errors, "missing social preview image: assets/og.png")
        return
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        fail(errors, "social preview image is not a valid PNG: assets/og.png")
        return
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (SOCIAL_IMAGE_WIDTH, SOCIAL_IMAGE_HEIGHT):
        fail(errors, f"social preview dimensions should be {SOCIAL_IMAGE_WIDTH}x{SOCIAL_IMAGE_HEIGHT}, got {width}x{height}")


def check_sitemap(errors: list[str]) -> None:
    path = ROOT / "sitemap.xml"
    if not path.is_file():
        fail(errors, "missing sitemap.xml")
        return
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except (ET.ParseError, UnicodeError) as exc:
        fail(errors, f"invalid sitemap.xml: {exc}")
        return
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    locations = [node.text or "" for node in root.findall(f"{namespace}url/{namespace}loc")]
    expected = [BASE_URL] + [urljoin(BASE_URL, route) for route in EXPECTED_ROUTES]
    if locations != expected:
        fail(errors, f"sitemap URLs differ: expected {expected}, got {locations}")


def check_robots(errors: list[str]) -> None:
    path = ROOT / "robots.txt"
    if not path.is_file():
        fail(errors, "missing robots.txt")
        return
    text = path.read_text(encoding="utf-8")
    if "User-agent: *" not in text or "Allow: /" not in text:
        fail(errors, "robots.txt must allow all crawlers")
    if "Sitemap: https://www.thirdtype.net/sitemap.xml" not in text:
        fail(errors, "robots.txt must reference canonical sitemap")


def check_pages(errors: list[str]) -> None:
    pages = page_files()
    missing = [str(relative) for relative in CANONICAL_PAGE_RELATIVE if not (ROOT / relative).is_file()]
    for relative in missing:
        fail(errors, f"missing canonical HTML page: {relative}")
    titles: set[str] = set()
    descriptions: set[str] = set()
    canonicals: set[str] = set()
    for path in pages:
        relative = path.relative_to(ROOT)
        try:
            parser = PageParser()
            parser.feed(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            fail(errors, f"{relative}: cannot parse: {exc}")
            continue
        route = route_for(path)
        if not parser.title:
            fail(errors, f"{relative}: missing title")
        elif parser.title in titles:
            fail(errors, f"{relative}: duplicate title")
        else:
            titles.add(parser.title)
        if not parser.description:
            fail(errors, f"{relative}: missing meta description")
        elif parser.description in descriptions:
            fail(errors, f"{relative}: duplicate meta description")
        else:
            descriptions.add(parser.description)
        expected = expected_canonical(route)
        if parser.canonical != expected:
            fail(errors, f"{relative}: canonical should be {expected}, got {parser.canonical}")
        elif parser.canonical in canonicals:
            fail(errors, f"{relative}: duplicate canonical")
        else:
            canonicals.add(parser.canonical)
        required_meta = ("og:title", "og:description", "og:url", "twitter:card", "twitter:title", "twitter:description")
        for key in required_meta:
            if not parser.meta.get((key, "content")):
                fail(errors, f"{relative}: missing {key}")
        if route == "" or route in EXPECTED_ROUTES:
            social_meta = {
                "og:image": SOCIAL_IMAGE_URL,
                "og:image:width": str(SOCIAL_IMAGE_WIDTH),
                "og:image:height": str(SOCIAL_IMAGE_HEIGHT),
                "twitter:image": SOCIAL_IMAGE_URL,
            }
            for key, expected_value in social_meta.items():
                actual_value = parser.meta.get((key, "content"), "")
                if actual_value != expected_value:
                    fail(errors, f"{relative}: {key} should be {expected_value}, got {actual_value or '<missing>'}")
            for key in ("og:image:alt", "twitter:image:alt"):
                if not parser.meta.get((key, "content")):
                    fail(errors, f"{relative}: missing {key}")
            if parser.meta.get(("twitter:card", "content")) != "summary_large_image":
                fail(errors, f"{relative}: twitter:card must be summary_large_image")
        if len(parser.h1) != 1:
            fail(errors, f"{relative}: expected exactly one H1, found {len(parser.h1)}")
        if route == "":
            if not parser.jsonld:
                fail(errors, f"{relative}: missing Organization JSON-LD")
            else:
                try:
                    data = json.loads(parser.jsonld[0])
                    if data.get("@type") != "Organization":
                        fail(errors, f"{relative}: JSON-LD is not Organization")
                except json.JSONDecodeError as exc:
                    fail(errors, f"{relative}: invalid JSON-LD: {exc}")
        elif route.startswith("apps/"):
            if not parser.jsonld:
                fail(errors, f"{relative}: missing SoftwareApplication JSON-LD")
            else:
                try:
                    data = json.loads(parser.jsonld[0])
                    if data.get("@type") != "SoftwareApplication":
                        fail(errors, f"{relative}: JSON-LD is not SoftwareApplication")
                except json.JSONDecodeError as exc:
                    fail(errors, f"{relative}: invalid JSON-LD: {exc}")
            slug = route.split("/")[1]
            links = [href for href, _ in parser.hrefs if href.split("#", 1)[0] in STORE_LINKS and STORE_LINKS[href.split("#", 1)[0]] == slug]
            expected_count = DETAIL_LINK_COUNTS.get(slug)
            if expected_count is None or len(links) != expected_count:
                fail(errors, f"{relative}: expected {expected_count} official store links, found {len(links)}")
        for href, attrs in parser.hrefs:
            if href in STORE_LINKS:
                if attrs.get("target") != "_blank" or "noopener" not in attrs.get("rel", "") or "noreferrer" not in attrs.get("rel", ""):
                    fail(errors, f"{relative}: store link must use target=_blank and noopener noreferrer: {href}")
            elif href and not href.startswith("#"):
                check_local_target(path, href, errors, "href")
        for src in parser.srcs:
            if src:
                check_local_target(path, src, errors, "asset")
        text = path.read_text(encoding="utf-8").lower()
        for term in PROHIBITED_TERMS:
            if term.lower() in text:
                fail(errors, f"{relative}: prohibited sensitive/unsupported term: {term}")
    home = ROOT / "index.html"
    if home.exists():
        parser = PageParser()
        parser.feed(home.read_text(encoding="utf-8"))
        store_count = sum(1 for href, _ in parser.hrefs if href in STORE_LINKS)
        if store_count != 9:
            fail(errors, f"index.html: expected 9 official store links, found {store_count}")


def check_http(base: str, errors: list[str]) -> None:
    root = base.rstrip("/") + "/"
    routes = [""] + EXPECTED_ROUTES
    for route in routes:
        url = root + route
        try:
            with urlopen(url, timeout=8) as response:
                body = response.read(200)
                if response.status != 200:
                    fail(errors, f"HTTP {response.status}: {url}")
                if b"<!doctype html>" not in body.lower():
                    fail(errors, f"HTTP body is not HTML: {url}")
        except Exception as exc:  # noqa: BLE001 - deterministic report for local smoke test
            fail(errors, f"HTTP smoke failed for {url}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--http-base", help="also request home and all six detail routes from a running local server")
    args = parser.parse_args()
    errors: list[str] = []
    check_pages(errors)
    check_images(errors)
    check_social_image(errors)
    check_sitemap(errors)
    check_robots(errors)
    if not (ROOT / ".nojekyll").exists():
        fail(errors, "missing .nojekyll")
    if (ROOT / "package.json").exists():
        fail(errors, "package.json is not allowed in dependency-free output")
    if args.http_base:
        check_http(args.http_base, errors)
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"VALIDATION PASSED: {len(page_files())} HTML pages, 6 local icons, 7 sitemap URLs")
    if args.http_base:
        print(f"HTTP SMOKE PASSED: {args.http_base.rstrip('/')}/ + 6 detail routes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
