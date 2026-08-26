#!/usr/bin/env python3
"""Deterministic, dependency-free checks for the static company-site output."""

from __future__ import annotations

import argparse
import hashlib
from html import unescape
import json
import re
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
SOCIAL_IMAGE_WIDTH = 1728
SOCIAL_IMAGE_HEIGHT = 910
NAVER_VERIFICATION_TOKEN = "b0c48fbbc7ceb316a04883d1f114d1a497ecca96"

SCREENSHOT_ROOT = ROOT / "assets" / "screenshots"
SCREENSHOT_DIMENSIONS = {
    "carrotcard/01.png": (1080, 2400),
    "carrotcard/02.png": (1080, 2400),
    "carrotcard/03.png": (1080, 2400),
    "maedo-signal/01.png": (1080, 2206),
    "maedo-signal/02.png": (1080, 2206),
    "maedo-signal/03.png": (1080, 2206),
    "gps-speed-go/01.png": (1080, 2400),
    "gps-speed-go/02.png": (1080, 2400),
    "gps-speed-go/03.png": (1080, 2400),
    "ttcal/01.png": (1080, 2400),
    "ttcal/02.png": (1080, 2400),
    "ttcal/03.png": (1080, 2400),
    "retro-timestamp/01.jpg": (1080, 2400),
    "retro-timestamp/02.jpg": (922, 2048),
    "retro-timestamp/03.jpg": (1080, 2400),
    "motion-ease/01.png": (1080, 1920),
    "motion-ease/02.png": (1080, 1920),
    "motion-ease/03.png": (1080, 1920),
    "business-news/01.png": (1080, 1920),
    "business-news/02.png": (1080, 1920),
    "business-news/03.png": (1080, 1920),
}

SCREENSHOT_SLUGS = tuple(slug for slug in ("carrotcard", "maedo-signal", "gps-speed-go", "ttcal", "retro-timestamp", "motion-ease", "business-news"))

PROHIBITED_MOTIFS = (
    ".app-card",
    ".app-grid",
    ".detail-hero",
    "box-shadow",
    "gradient(",
    "store-button",
    "<button",
    "brand-mark",
)

BUSINESS_NEWS_ANDROID_POLICY_URL = "https://www.thirdtype.net/privacy-policy/business-news-android.html"
BUSINESS_NEWS_IPHONE_POLICY_URL = "https://www.thirdtype.net/business-news/privacy-policy.html"
SEOULROLL_ANDROID_POLICY_URL = "https://www.thirdtype.net/privacy-policy/seoulroll-android.html"
SEOULROLL_IOS_POLICY_URL = "https://www.thirdtype.net/privacy-policy/seoulroll-ios.html"
SEOULROLL_SUPPORT_URL = "https://www.thirdtype.net/seoulroll/support.html"
SEOULROLL_IOS_POLICY_ROUTE = "privacy-policy/seoulroll-ios.html"
SEOULROLL_SUPPORT_ROUTE = "seoulroll/support.html"
SEOULROLL_IOS_POLICY_PAGE = Path(SEOULROLL_IOS_POLICY_ROUTE)
SEOULROLL_SUPPORT_PAGE = Path(SEOULROLL_SUPPORT_ROUTE)
APPLE_SUBSCRIPTION_MANAGEMENT_URL = "https://apps.apple.com/account/subscriptions"
GOOGLE_PRIVACY_URL = "https://policies.google.com/privacy"
GOOGLE_ADS_TECHNOLOGY_URL = "https://policies.google.com/technologies/ads"
APPLE_PRIVACY_URL = "https://www.apple.com/legal/privacy/"
BUSINESS_NEWS_PLAY_URL = "https://play.google.com/store/apps/details?id=com.thirdtype.businessnews"
BUSINESS_NEWS_APPLE_URL = "https://apps.apple.com/kr/app/id6797872683"
BUSINESS_NEWS_DETAIL_POLICY_HREF = "../../privacy-policy/#business-news"
BUSINESS_NEWS_FORBIDDEN_POLICY_HOSTS = ("htmlpreview.github.io", "gist.githubusercontent.com", "thirdtype-dev.github.io")

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
    BUSINESS_NEWS_PLAY_URL: "business-news",
    BUSINESS_NEWS_APPLE_URL: "business-news",
}

DETAIL_LINK_COUNTS = {
    "carrotcard": 2,
    "maedo-signal": 1,
    "gps-speed-go": 2,
    "ttcal": 2,
    "retro-timestamp": 1,
    "motion-ease": 1,
    "business-news": 2,
}

HOME_FEATURES = [
    {
        "slug": "carrotcard",
        "number": "01",
        "name": "총명함",
        "lede": "명함을 스캔해 정리하고, 필요한 순간에 다시 떠올릴 수 있도록 돕는 기록 도구입니다.",
        "platform": "Android · iPhone",
        "detail": "apps/carrotcard/",
        "screenshots": ("assets/screenshots/carrotcard/01.png", "assets/screenshots/carrotcard/02.png"),
        "stores": ("https://play.google.com/store/apps/details?id=com.thirdtype.carrotcard", "https://apps.apple.com/kr/app/id6787031350"),
    },
    {
        "slug": "maedo-signal",
        "number": "02",
        "name": "주식 매도신호등",
        "lede": "장 시작 전 일곱 가지 위험 지표를 신호등 색으로 간결하게 요약합니다.",
        "platform": "Android",
        "detail": "apps/maedo-signal/",
        "screenshots": ("assets/screenshots/maedo-signal/01.png", "assets/screenshots/maedo-signal/02.png"),
        "stores": ("https://play.google.com/store/apps/details?id=com.maedo.signal",),
    },
    {
        "slug": "gps-speed-go",
        "number": "03",
        "name": "GPS Speed Go",
        "lede": "현재 속도를 크게 보여주는, 인터넷 연결 없이도 사용할 수 있는 GPS 속도계입니다.",
        "platform": "Android · iPhone",
        "detail": "apps/gps-speed-go/",
        "screenshots": ("assets/screenshots/gps-speed-go/01.png", "assets/screenshots/gps-speed-go/02.png"),
        "stores": ("https://play.google.com/store/apps/details?id=com.thirdtype.gpsspeed", "https://apps.apple.com/kr/app/gps-speed-go/id6789569473"),
    },
    {
        "slug": "ttcal",
        "number": "04",
        "name": "오늘내일모레",
        "lede": "오늘, 내일, 모레에 집중할 수 있도록 만든 간결한 세 칸 캘린더입니다.",
        "platform": "Android · iPhone",
        "detail": "apps/ttcal/",
        "screenshots": ("assets/screenshots/ttcal/01.png", "assets/screenshots/ttcal/02.png"),
        "stores": ("https://play.google.com/store/apps/details?id=com.thirdtype.ttcal", "https://apps.apple.com/kr/app/id6785738560"),
    },
    {
        "slug": "retro-timestamp",
        "number": "05",
        "name": "레트로 타임스탬프",
        "lede": "사진의 EXIF 날짜를 바탕으로 추억을 닮은 레트로 스탬프를 더합니다.",
        "platform": "Android",
        "detail": "apps/retro-timestamp/",
        "screenshots": ("assets/screenshots/retro-timestamp/01.jpg", "assets/screenshots/retro-timestamp/02.jpg"),
        "stores": ("https://play.google.com/store/apps/details?id=com.thirdtype.retrotimestamp",),
    },
    {
        "slug": "motion-ease",
        "number": "06",
        "name": "디지털 멀미 치료제",
        "lede": "움직임에 반응하는 가장자리 점과 선택형 헤드폰 전용 100Hz 톤을 제공하는 화면 도구입니다.",
        "platform": "Android",
        "detail": "apps/motion-ease/",
        "screenshots": ("assets/screenshots/motion-ease/01.png", "assets/screenshots/motion-ease/02.png"),
        "stores": ("https://play.google.com/store/apps/details?id=com.thirdtype.carsick",),
    },
    {
        "slug": "business-news",
        "number": "07",
        "name": "경제신문",
        "lede": "여러 경제 매체의 뉴스를 한곳에서 읽는 올인원 경제 뉴스 리더입니다.",
        "platform": "Android · iPhone",
        "detail": "apps/business-news/",
        "screenshots": ("assets/screenshots/business-news/01.png", "assets/screenshots/business-news/02.png"),
        "stores": (BUSINESS_NEWS_PLAY_URL, BUSINESS_NEWS_APPLE_URL),
    },
]

PHILOSOPHY_PARAGRAPHS = (
    "슬기로운 생활은 시각적인 화려함이나 복잡한 기능을 경쟁력으로 삼지 않습니다. 우리가 중요하게 생각하는 것은 사용자가 불편을 느끼는 순간, 망설이지 않고 바로 꺼내 쓸 수 있는 도구를 만드는 일입니다.",
    "명함을 다시 찾을 때, 현재 속도를 확인하고 싶을 때, 가까운 일정에 집중하고 싶을 때처럼 일상에는 작지만 반복되는 문제들이 있습니다. 거대한 서비스가 필요할 만큼 복잡하진 않지만, 마땅한 도구가 없으면 계속 불편함을 남기는 일들입니다. 우리는 바로 그 지점을 찾아 하나씩 해결합니다.",
    "하나의 앱에는 하나의 분명한 목적만 담습니다. 필요 이상의 기능을 늘리거나 사용자의 시간을 끌기보다, 필요한 일을 빠르게 마치고 일상으로 돌아갈 수 있도록 설계합니다.",
    "디자인 역시 눈에 띄기 위한 장식보다 정보의 명확성과 편의성에 집중합니다. 처음 실행해도 설명 없이 이해할 수 있고, 자주 사용해도 피로하지 않은 화면을 지향합니다.",
    "모든 사람을 위한 거대한 플랫폼보다, 누군가에게 꼭 필요한 작고 구체적인 도구를 꾸준히 만들고 관리합니다.",
)

PHILOSOPHY_PRINCIPLES = (
    ("문제를 작고 명확하게 정의합니다.", "여러 기능을 섞기보다, 사용자가 해결하려는 단 하나의 본질적 문제에 집중합니다."),
    ("설명 없이 바로 쓰게 만듭니다.", "번거로운 가입이나 복잡한 학습 과정 없이, 필요한 순간 즉시 사용할 수 있어야 합니다."),
    ("사용자의 시간을 빼앗지 않습니다.", "앱에 오래 머물게 하기보다, 할 일을 가장 빠르게 끝내주는 것이 우리의 역할입니다."),
    ("화려함보다 실제 쓰임에 집중합니다.", "유행하는 수식어나 과장된 약속 대신, 앱이 무엇을 해결하는지 분명하게 전달합니다."),
    ("작은 앱도 꾸준히 관리합니다.", "기능이 단순하더라도 오래 안심하고 사용할 수 있도록 호환성과 안정성을 지속적으로 점검합니다."),
)

PHILOSOPHY_CLOSING = "슬기로운 생활은 거창한 변화를 약속하지 않습니다. 대신 오늘의 작은 불편 하나를 확실하게 줄이는 앱을 만듭니다."

EXPECTED_ROUTES = [
    "apps/carrotcard/",
    "apps/maedo-signal/",
    "apps/gps-speed-go/",
    "apps/ttcal/",
    "apps/retro-timestamp/",
    "apps/motion-ease/",
    "apps/business-news/",
]

PRIVACY_POLICY_ROUTE = "privacy-policy/"
BUSINESS_NEWS_CONTACT_ROUTE = "apps/business-news/contact/"
BUSINESS_NEWS_CONTACT_PAGE = Path(BUSINESS_NEWS_CONTACT_ROUTE) / "index.html"

PRIVACY_POLICY_MAP = (
    (
        "carrotcard",
        "총명함",
        (
            ("Android", "https://www.thirdtype.net/privacy-policy/carrotcard-android.html"),
            ("iPhone", "https://www.thirdtype.net/privacy-policy/carrotcard-ios.html"),
        ),
    ),
    (
        "maedo-signal",
        "주식 매도신호등",
        (
            ("Android", "https://htmlpreview.github.io/?https://gist.githubusercontent.com/thirdtype-dev/0e7cb056ebff04515f145966d1938d5a/raw/3e7201ab8b368b55047cd695dd301be46d0dbf50/privacy-policy.html"),
        ),
    ),
    (
        "gps-speed-go",
        "GPS Speed Go",
        (
            ("Android", "https://www.thirdtype.net/privacy-policy/gps-speed-go-android.html"),
            ("iPhone", "https://www.thirdtype.net/gps-speed-go/privacy-policy.html"),
        ),
    ),
    (
        "ttcal",
        "오늘내일모레",
        (
            ("Android", "https://htmlpreview.github.io/?https://gist.githubusercontent.com/thirdtype-dev/a7f3f6cb702c554439702e175cb97841/raw/privacy-policy.html"),
            ("iPhone", "https://htmlpreview.github.io/?https://gist.githubusercontent.com/thirdtype-dev/60fd421c2a0feb05ff5818a63b1914d4/raw/privacy-policy.html"),
        ),
    ),
    (
        "retro-timestamp",
        "레트로 타임스탬프",
        (
            ("Android", "https://htmlpreview.github.io/?https://gist.githubusercontent.com/thirdtype-dev/ecb0b9655ab0c8f83f1e45f2513bde0d/raw/6010de3b2b35907993fe71a4d92fb7676f8c68c5/privacy-policy.html"),
        ),
    ),
    (
        "motion-ease",
        "디지털 멀미 치료제",
        (
            ("Android", "https://htmlpreview.github.io/?https://gist.githubusercontent.com/thirdtype-dev/9ece73632af6c079b17ebf09cc7471e7/raw/motionease-privacy-policy.html"),
        ),
    ),
    (
        "business-news",
        "경제신문",
        (
            ("Android", BUSINESS_NEWS_ANDROID_POLICY_URL),
            ("iPhone", BUSINESS_NEWS_IPHONE_POLICY_URL),
        ),
    ),
    (
        "seoulroll",
        "서울롤",
        (
            ("Android", SEOULROLL_ANDROID_POLICY_URL),
            ("iPhone", SEOULROLL_IOS_POLICY_URL),
        ),
    ),
)

FROZEN_POLICY_HASHES = {
    Path("privacy-policy.html"): "712d5f5391a211c9a7545dfeb790a09ff773f56a774e31202cd44e77238b1b28",
    Path("privacy-policy/carrotcard-android.html"): "75f9deec30a0414848e872aa1059036064eb904d47b0d96d6dbb8d89ecbb3554",
    Path("privacy-policy/carrotcard-ios.html"): "672888ce32fcba2d5ba3650699f7ae4aee4bc87e2b543fe054a4959b6b34fed9",
    Path("privacy-policy/gps-speed-go-android.html"): "eee21b5dccf8667e1b44c5e2685c089c40bbdd5c7aacf9eb24478b2a39442f57",
    Path("privacy-policy/maedo-signal.html"): "a737c97d56b67f230f90dd1b3d6a026103c63cde4935e71ad7df7f4381d2805c",
    Path("privacy-policy/retro-timestamp.html"): "5f714b044140ba8d1d3a984b2295c07bfb4619d63c04db8d13e0a65679708080",
    Path("gps-speed-go/privacy-policy.html"): "310eb4d98e36442707a7a472589ac60ffd615f487ffd9ef5180722e01f7c8ec1",
    Path("privacy-policy/business-news-android.html"): "8443b09ba48dbc3a17218496c1c5c23c98dd985c1165314964ce057708553e76",
    Path("business-news/privacy-policy.html"): "c3b698050e33e76c37985e97e107ac32efa0c4a504c80bf1df8c339837628a58",
    Path("privacy-policy/seoulroll-android.html"): "e633090cc28aa64f1ff0a721e91cd61bdb0c99d853a43df3365dde388ae7645e",
    SEOULROLL_IOS_POLICY_PAGE: "8bb7fd0791b2c37dd1c89fa234aaa68e80efcd6631685af947782f3849f2506b",
}

CANONICAL_PAGE_RELATIVE = [
    Path("index.html"),
    Path("404.html"),
    Path("privacy-policy/index.html"),
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
        self.images: list[dict[str, str]] = []
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
            self.images.append(data)
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


class NaverVerificationParser(HTMLParser):
    """Collect Naver verification metadata and whether it is inside <head>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._head_depth = 0
        self.records: list[tuple[bool, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "head":
            self._head_depth += 1
            return
        if tag.lower() != "meta":
            return
        data = {key.lower(): value or "" for key, value in attrs}
        if data.get("name", "").lower() == "naver-site-verification":
            self.records.append((self._head_depth > 0, data.get("content", "")))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "head" and self._head_depth:
            self._head_depth -= 1


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def check_naver_verification(errors: list[str]) -> None:
    path = ROOT / "index.html"
    if not path.is_file():
        return
    parser = NaverVerificationParser()
    try:
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
    except (OSError, UnicodeError) as exc:
        fail(errors, f"index.html: cannot inspect Naver verification metadata: {exc}")
        return

    if len(parser.records) != 1:
        fail(errors, f"index.html: expected exactly one Naver verification meta tag, found {len(parser.records)}")
        return
    in_head, token = parser.records[0]
    if not in_head:
        fail(errors, "index.html: Naver verification meta tag must be inside homepage <head>")
    if token != NAVER_VERIFICATION_TOKEN:
        fail(errors, "index.html: Naver verification token does not match the locked value")


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


def image_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            while index < len(data) and data[index] == 0xFF:
                index += 1
            if index >= len(data):
                break
            marker = data[index]
            index += 1
            if marker in (0xD8, 0xD9):
                continue
            if index + 2 > len(data):
                break
            length = struct.unpack(">H", data[index:index + 2])[0]
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                if index + 7 <= len(data):
                    height, width = struct.unpack(">HH", data[index + 3:index + 7])
                    return width, height
            index += length
    return None


def check_screenshot_assets(errors: list[str]) -> None:
    attribution = SCREENSHOT_ROOT / "SOURCES.tsv"
    if not attribution.is_file():
        fail(errors, "missing screenshot attribution: assets/screenshots/SOURCES.tsv")
    else:
        rows = attribution.read_text(encoding="utf-8").splitlines()
        if not rows or rows[0] != "slug\tindex\tsource_url\tlocal_file\tformat\twidth\theight":
            fail(errors, "screenshot attribution header is not the staged SOURCES.tsv header")
        if len(rows) - 1 != len(SCREENSHOT_DIMENSIONS):
            fail(errors, f"screenshot attribution should contain {len(SCREENSHOT_DIMENSIONS)} rows, found {len(rows) - 1}")
        seen: set[str] = set()
        for row in rows[1:]:
            fields = row.split("\t")
            if len(fields) != 7:
                fail(errors, f"malformed screenshot attribution row: {row}")
                continue
            slug, index, source_url, local_file, image_format, width, height = fields
            relative = local_file.removeprefix("assets/screenshots/")
            seen.add(relative)
            expected = SCREENSHOT_DIMENSIONS.get(relative)
            if expected is None:
                fail(errors, f"unexpected screenshot attribution path: {local_file}")
                continue
            if slug not in SCREENSHOT_SLUGS or index not in {"01", "02", "03"}:
                fail(errors, f"invalid screenshot attribution identity: {row}")
            if not source_url.startswith("https://play-lh.googleusercontent.com/"):
                fail(errors, f"screenshot source is not an official Play image URL: {source_url}")
            if image_format not in {"PNG", "JPEG"} or (int(width), int(height)) != expected:
                fail(errors, f"screenshot attribution dimensions/format mismatch: {row}")
        missing_attribution = sorted(set(SCREENSHOT_DIMENSIONS) - seen)
        for relative in missing_attribution:
            fail(errors, f"missing screenshot attribution row: {relative}")
    for relative, expected in SCREENSHOT_DIMENSIONS.items():
        path = SCREENSHOT_ROOT / relative
        if not path.is_file():
            fail(errors, f"missing official screenshot: assets/screenshots/{relative}")
            continue
        dimensions = image_dimensions(path)
        if dimensions != expected:
            fail(errors, f"screenshot dimensions differ for assets/screenshots/{relative}: expected {expected}, got {dimensions}")


def check_radius_guard(css: str, errors: list[str]) -> None:
    """Allow rounded corners only on the two established screenshot selectors."""
    declaration_pattern = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)
    radius_rules: list[tuple[str, str]] = []
    for match in declaration_pattern.finditer(css):
        selector = " ".join(match.group(1).split())
        body = match.group(2)
        if re.search(r"\bborder-radius\s*:", body):
            radius_rules.append((selector, body))
    allowed = {".app-feature-shot img", ".detail-shot img"}
    if len(radius_rules) != 2:
        fail(errors, f"assets/site.css: expected exactly two radius declarations, found {len(radius_rules)}")
    selectors = {selector for selector, _ in radius_rules}
    if selectors != allowed:
        fail(errors, f"assets/site.css: radius selectors must be exactly {sorted(allowed)}, got {sorted(selectors)}")
    for selector, body in radius_rules:
        if not re.search(r"border-radius\s*:\s*var\(--screenshot-radius\)\s*;", body):
            fail(errors, f"assets/site.css: {selector} must use var(--screenshot-radius)")
    if not re.search(r"--screenshot-radius\s*:\s*clamp\(\s*12px\s*,\s*2vw\s*,\s*28px\s*\)\s*;", css):
        fail(errors, "assets/site.css: missing capped --screenshot-radius clamp(12px, 2vw, 28px)")


def css_rule_body(css: str, selector: str) -> str:
    match = re.search(rf"(?m)^[ \t]*{re.escape(selector)}\s*\{{", css)
    if not match:
        return ""
    opening = css.find("{", match.start())
    depth = 0
    for index in range(opening, len(css)):
        if css[index] == "{":
            depth += 1
        elif css[index] == "}":
            depth -= 1
            if depth == 0:
                return css[opening + 1:index]
    return ""


def css_media_body(css: str, query: str) -> str:
    match = re.search(rf"@media\s*\(\s*{re.escape(query)}\s*\)\s*\{{", css)
    if not match:
        return ""
    opening = css.find("{", match.start())
    depth = 0
    for index in range(opening, len(css)):
        if css[index] == "{":
            depth += 1
        elif css[index] == "}":
            depth -= 1
            if depth == 0:
                return css[opening + 1:index]
    return ""


def check_detail_shot_sizes(css: str, errors: list[str]) -> None:
    expected_widths = {
        "base": (css_rule_body(css, ".detail-shot"), r"clamp\(\s*280px\s*,\s*34vw\s*,\s*420px\s*\)"),
        "max-width: 850px": (css_rule_body(css_media_body(css, "max-width: 850px"), ".detail-shot"), r"clamp\(\s*260px\s*,\s*54vw\s*,\s*380px\s*\)"),
        "max-width: 560px": (css_rule_body(css_media_body(css, "max-width: 560px"), ".detail-shot"), r"min\(\s*82vw\s*,\s*340px\s*\)"),
    }
    for scope, (body, width_pattern) in expected_widths.items():
        if not body or not re.search(rf"\bwidth\s*:\s*{width_pattern}\s*;", body):
            fail(errors, f"assets/site.css: .detail-shot {scope} width contract is missing or changed")
    if "min(72vw, 930px)" in css or "min(78vw, 720px)" in css:
        fail(errors, "assets/site.css: legacy 930px/720px detail-shot width remains")
    if re.search(r"(?s)\.detail-shot\s*\{[^}]*\bwidth\s*:\s*90vw\s*;", css):
        fail(errors, "assets/site.css: legacy 90vw detail-shot width remains")
    if not re.search(r"\.detail-shot:nth-child\(even\)\s*\{[^}]*margin-left\s*:\s*auto\s*;", css, re.DOTALL):
        fail(errors, "assets/site.css: second detail screenshot must remain right-aligned")
    if re.search(r"\.detail-shot:nth-child\(even\)\s*\{[^}]*margin-left\s*:\s*10vw\s*;", css, re.DOTALL):
        fail(errors, "assets/site.css: mobile detail screenshot alignment must not use the legacy 10vw offset")
    feature_body = css_rule_body(css, ".app-feature-shot img")
    if not re.search(r"\bwidth\s*:\s*100%\s*;", feature_body):
        fail(errors, "assets/site.css: homepage app-feature screenshot width contract changed")


def check_editorial_structure(errors: list[str]) -> None:
    home_path = ROOT / "index.html"
    not_found_path = ROOT / "404.html"
    css_path = ROOT / "assets" / "site.css"
    if not home_path.is_file() or not css_path.is_file():
        return
    home = home_path.read_text(encoding="utf-8")
    not_found = not_found_path.read_text(encoding="utf-8") if not_found_path.is_file() else ""
    css = css_path.read_text(encoding="utf-8")
    if "작은 불편 하나도 가볍게 넘기지 않습니다" not in home:
        fail(errors, "index.html: missing homepage hero heading")
    if "#f5f3ee" not in css.lower() or "#0a0a0a" not in css.lower():
        fail(errors, "assets/site.css: r2 warm-white/black palette is missing")
    check_radius_guard(css, errors)
    check_detail_shot_sizes(css, errors)
    for motif in PROHIBITED_MOTIFS:
        if motif in css or motif in home or motif in not_found:
            fail(errors, f"r1 prohibited motif remains in canonical page/CSS: {motif}")
    for legacy in ("work-wall", "wall-item", "wall-kicker", "app-index", "app-row"):
        if legacy in home or legacy in css:
            fail(errors, f"index.html/assets/site.css: former disconnected structure remains: {legacy}")
    if "app-feature:nth-child(even)" not in css or "grid-template-columns: 1fr" not in css:
        fail(errors, "assets/site.css: paired feature sections lack responsive alternating/single-column rules")
    if "about-band" in home or "about-band" in css:
        fail(errors, "index.html/assets/site.css: former about-band remains")
    if ".company-philosophy" not in css or ".principle-list" not in css:
        fail(errors, "assets/site.css: company philosophy editorial styles are missing")

    philosophy_matches = re.findall(
        r'<section class="company-philosophy"[^>]*>(.*?)</section>',
        home,
        re.DOTALL,
    )
    if len(philosophy_matches) != 1:
        fail(errors, f"index.html: expected exactly one company philosophy section, found {len(philosophy_matches)}")
    else:
        philosophy = philosophy_matches[0]
        section_start = home.find('<section class="company-philosophy"')
        features_start = home.find('<section class="app-features"')
        features_end = home.find("</section>", features_start) if features_start >= 0 else -1
        footer_start = home.find("<footer")
        if not (features_start >= 0 and features_end >= 0 and section_start > features_end and footer_start > section_start):
            fail(errors, "index.html: company philosophy must follow all app features and precede the footer")
        heading = re.search(r'<h2 id="philosophy-title">([^<]+)</h2>', philosophy)
        if not heading or unescape(heading.group(1)) != "우리가 추구하는 것":
            fail(errors, "index.html: philosophy heading mismatch")
        subheading = re.search(r'<p class="philosophy-subheading">([^<]+)</p>', philosophy)
        if not subheading or unescape(subheading.group(1)) != "생활 속 작은 문제를, 바로 쓸 수 있는 도구로 해결합니다.":
            fail(errors, "index.html: philosophy subheading mismatch")
        for paragraph in PHILOSOPHY_PARAGRAPHS:
            if philosophy.count(paragraph) != 1 or home.count(paragraph) != 1:
                fail(errors, f"index.html: philosophy paragraph missing, changed, or duplicated: {paragraph[:24]}…")
        principle_heading = re.search(r"<h3>([^<]+)</h3>", philosophy)
        if not principle_heading or unescape(principle_heading.group(1)) != "우리가 앱을 만드는 기준":
            fail(errors, "index.html: principles heading mismatch")
        principle_pairs = [
            (unescape(title), unescape(body))
            for title, body in re.findall(r"<li><h4>(.*?)</h4><p>(.*?)</p></li>", philosophy, re.DOTALL)
        ]
        if principle_pairs != list(PHILOSOPHY_PRINCIPLES):
            fail(errors, "index.html: philosophy principle title/body pairs are missing, changed, or out of order")
        if philosophy.count(PHILOSOPHY_CLOSING) != 1 or home.count(PHILOSOPHY_CLOSING) != 1:
            fail(errors, "index.html: philosophy closing statement missing, changed, or duplicated")

    feature_matches = re.findall(
        r'<article class="app-feature\s+app-feature--([a-z0-9-]+)"[^>]*data-app="([a-z0-9-]+)"[^>]*>(.*?)</article>',
        home,
        re.DOTALL,
    )
    if len(feature_matches) != len(HOME_FEATURES):
        fail(errors, f"index.html: expected exactly {len(HOME_FEATURES)} app feature articles, found {len(feature_matches)}")

    def class_text(block: str, class_name: str) -> str:
        match = re.search(rf'class="{re.escape(class_name)}"[^>]*>(.*?)</[^>]+>', block, re.DOTALL)
        if not match:
            return ""
        return unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()

    for expected, actual in zip(HOME_FEATURES, feature_matches):
        class_slug, data_slug, block = actual
        slug = expected["slug"]
        if (class_slug, data_slug) != (slug, slug):
            fail(errors, f"index.html: feature order/slug mismatch, expected {slug}, got {class_slug}/{data_slug}")
        if class_text(block, "app-feature-number") != expected["number"]:
            fail(errors, f"index.html: {slug} number mismatch")
        if class_text(block, "app-feature-platform") != expected["platform"]:
            fail(errors, f"index.html: {slug} platform mismatch")
        if class_text(block, "app-feature-lede") != expected["lede"]:
            fail(errors, f"index.html: {slug} lede must match its detail-page lede exactly")
        name_match = re.search(r"<h2[^>]*>(.*?)</h2>", block, re.DOTALL)
        if not name_match or unescape(re.sub(r"<[^>]+>", "", name_match.group(1))).strip() != expected["name"]:
            fail(errors, f"index.html: {slug} app name mismatch")
        detail_match = re.search(r'<a class="app-feature-detail" href="([^"]+)"', block)
        if not detail_match or detail_match.group(1) != expected["detail"]:
            fail(errors, f"index.html: {slug} detail link mismatch")

        article_parser = PageParser()
        article_parser.feed(block)
        store_links = [href for href, _ in article_parser.hrefs if href in STORE_LINKS]
        if tuple(store_links) != expected["stores"]:
            fail(errors, f"index.html: {slug} store-link mapping mismatch")
        if any(STORE_LINKS[href] != slug for href in store_links):
            fail(errors, f"index.html: {slug} contains another app's store link")
        images = [image for image in article_parser.images if image.get("src", "").startswith("assets/screenshots/")]
        actual_sources = tuple(image.get("src", "") for image in images)
        if actual_sources != expected["screenshots"]:
            fail(errors, f"index.html: {slug} must contain exactly its two matching screenshots")
        if len(images) != 2:
            fail(errors, f"index.html: {slug} expected exactly two screenshots, found {len(images)}")
        for image in images:
            for key in ("alt", "width", "height", "decoding"):
                if not image.get(key):
                    fail(errors, f"index.html: {slug} screenshot missing {key}: {image.get('src', '<missing>')}")
            if image.get("decoding") != "async":
                fail(errors, f"index.html: {slug} screenshot must use decoding=async")

    home_parser = PageParser()
    home_parser.feed(home)
    store_count = sum(1 for href, _ in home_parser.hrefs if href in STORE_LINKS)
    if store_count != 11:
        fail(errors, f"index.html: expected 11 official store links, found {store_count}")


def clean_fragment(fragment: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", fragment))).strip()


def check_detail_content(errors: list[str]) -> None:
    seen_paragraphs: dict[str, str] = {}
    for expected in HOME_FEATURES:
        path = ROOT / expected["detail"] / "index.html"
        if not path.is_file():
            continue
        page = path.read_text(encoding="utf-8")
        section_open_count = len(re.findall(r"<section\b", page))
        section_close_count = len(re.findall(r"</section>", page))
        if section_open_count != 3 or section_close_count != 3:
            fail(
                errors,
                f"{path.relative_to(ROOT)}: expected exactly three balanced detail sections, "
                f"found {section_open_count} opening and {section_close_count} closing tags",
            )
        sections = re.findall(r'<section class="detail-copy"[^>]*>(.*?)</section>', page, re.DOTALL)
        if len(sections) != 1:
            fail(errors, f"{path.relative_to(ROOT)}: expected exactly one detail-copy section, found {len(sections)}")
            continue
        detail = sections[0]
        headings = [clean_fragment(value) for value in re.findall(r"<h[23][^>]*>(.*?)</h[23]>", detail, re.DOTALL)]
        if len(headings) < 3:
            fail(errors, f"{path.relative_to(ROOT)}: expected at least three H2/H3 content headings, found {len(headings)}")
        paragraphs = [clean_fragment(value) for value in re.findall(r"<p(?:\s[^>]*)?>(.*?)</p>", detail, re.DOTALL)]
        substantive = [value for value in paragraphs if len(value) >= 30]
        if len(substantive) < 4:
            fail(errors, f"{path.relative_to(ROOT)}: expected at least four substantive visible paragraphs, found {len(substantive)}")
        for paragraph in substantive:
            prior = seen_paragraphs.get(paragraph)
            if prior and prior != expected["slug"]:
                fail(errors, f"{path.relative_to(ROOT)}: body paragraph is duplicated from {prior}")
            else:
                seen_paragraphs[paragraph] = expected["slug"]
        lists = re.findall(r'<ul class="detail-feature-list">(.*?)</ul>', detail, re.DOTALL)
        if len(lists) != 1:
            fail(errors, f"{path.relative_to(ROOT)}: expected exactly one detail-feature-list, found {len(lists)}")
        elif len(re.findall(r"<li[^>]*>(.*?)</li>", lists[0], re.DOTALL)) < 3:
            fail(errors, f"{path.relative_to(ROOT)}: detail-feature-list must contain at least three items")

        lede_match = re.search(r'<p class="lede">([^<]+)</p>', page)
        if not lede_match:
            fail(errors, f"{path.relative_to(ROOT)}: missing visible detail lede")
            continue
        lede = clean_fragment(lede_match.group(1))
        parser = PageParser()
        parser.feed(page)
        if expected["name"] not in parser.title:
            fail(errors, f"{path.relative_to(ROOT)}: title does not identify {expected['name']}")
        if lede not in parser.description:
            fail(errors, f"{path.relative_to(ROOT)}: meta description does not contain the visible lede")
        if len(parser.jsonld) != 1:
            fail(errors, f"{path.relative_to(ROOT)}: expected exactly one SoftwareApplication JSON-LD block")
        else:
            try:
                data = json.loads(parser.jsonld[0])
            except json.JSONDecodeError as exc:
                fail(errors, f"{path.relative_to(ROOT)}: invalid SoftwareApplication JSON-LD: {exc}")
            else:
                if data.get("name") != expected["name"]:
                    fail(errors, f"{path.relative_to(ROOT)}: JSON-LD name mismatch")
                if data.get("description") != lede:
                    fail(errors, f"{path.relative_to(ROOT)}: JSON-LD description must match the visible lede")


def check_privacy_hub(errors: list[str]) -> None:
    home_path = ROOT / "index.html"
    hub_path = ROOT / "privacy-policy" / "index.html"
    css_path = ROOT / "assets" / "site.css"
    if not home_path.is_file() or not hub_path.is_file() or not css_path.is_file():
        return
    home = home_path.read_text(encoding="utf-8")
    hub = hub_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")
    concise_description = "슬기로운 생활의 Android·iPhone 앱별 개인정보처리방침입니다."
    legacy_lede = "슬기로운 생활 여섯 앱의 제출된 개인정보처리방침 링크를 앱과 플랫폼별로 확인할 수 있습니다."
    legacy_heading = "앱별 제출 링크"
    legacy_explanation = "각 링크는 해당 앱과 플랫폼의 공식 개인정보처리방침으로 연결됩니다."

    hub_parser = PageParser()
    hub_parser.feed(hub)
    if hub_parser.description != concise_description:
        fail(errors, "privacy-policy/index.html: meta description must match the concise privacy copy contract")
    for key in ("og:description", "twitter:description"):
        if hub_parser.meta.get((key, "content")) != concise_description:
            fail(errors, f"privacy-policy/index.html: {key} must match the concise privacy copy contract")
    if "Legal · Privacy" in hub:
        fail(errors, "privacy-policy/index.html: decorative Legal · Privacy eyebrow must be removed")
    if legacy_lede in hub or re.search(r'<p class="privacy-lede">', hub):
        fail(errors, "privacy-policy/index.html: operational privacy lede must be removed")
    if legacy_heading in hub or legacy_explanation in hub:
        fail(errors, "privacy-policy/index.html: submitted-link filler copy must be removed")
    if hub.count('<h2 id="privacy-index-title">앱별 개인정보처리방침</h2>') != 1:
        fail(errors, "privacy-policy/index.html: concise app privacy heading is missing or duplicated")

    if "/privacy-policy/ttcal.html" in home or "/privacy-policy/ttcal.html" in hub or "/privacy-policy/ttcal.html" in css:
        fail(errors, "privacy-policy hub: obsolete /privacy-policy/ttcal.html link remains")
    for motif in PROHIBITED_MOTIFS:
        if motif in hub:
            fail(errors, f"privacy-policy/index.html: prohibited motif remains: {motif}")
    required_selectors = (".privacy-main", ".privacy-entry", ".privacy-platform-row", ".footer-policy-link")
    for selector in required_selectors:
        if selector not in css:
            fail(errors, f"assets/site.css: privacy hub selector is missing: {selector}")

    row_matches = re.findall(
        r'<article class="privacy-entry" data-app="([a-z0-9-]+)"[^>]*>(.*?)</article>',
        hub,
        re.DOTALL,
    )
    if len(row_matches) != len(PRIVACY_POLICY_MAP):
        fail(errors, f"privacy-policy/index.html: expected {len(PRIVACY_POLICY_MAP)} app rows, found {len(row_matches)}")
    for expected, actual in zip(PRIVACY_POLICY_MAP, row_matches):
        expected_slug, expected_name, expected_links = expected
        actual_slug, block = actual
        if actual_slug != expected_slug:
            fail(errors, f"privacy-policy/index.html: app order/slug mismatch, expected {expected_slug}, got {actual_slug}")
        heading = re.search(r"<h3>([^<]+)</h3>", block)
        if not heading or unescape(heading.group(1)) != expected_name:
            fail(errors, f"privacy-policy/index.html: {expected_slug} app name mismatch")
        actual_links = [
            (unescape(platform).strip(), href, unescape(label).strip())
            for platform, href, label in re.findall(
                r'<div class="privacy-platform-row">.*?<span class="privacy-platform">([^<]+)</span>.*?<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                block,
                re.DOTALL,
            )
        ]
        expected_urls = tuple(url for _, url in expected_links)
        actual_tuple = tuple((platform, href) for platform, href, _ in actual_links)
        if actual_tuple != expected_links:
            fail(errors, f"privacy-policy/index.html: {expected_slug} platform/URL mapping mismatch")
        if len(actual_links) != len(expected_links):
            fail(errors, f"privacy-policy/index.html: {expected_slug} expected {len(expected_links)} policy links, found {len(actual_links)}")
        for platform, href, label in actual_links:
            if label != "개인정보처리방침":
                fail(errors, f"privacy-policy/index.html: {expected_slug} {platform} link label mismatch")
            if hub.count(href) != 1:
                fail(errors, f"privacy-policy/index.html: submitted policy URL must appear once: {href}")
            if href not in expected_urls:
                fail(errors, f"privacy-policy/index.html: unexpected policy URL for {expected_slug}: {href}")
        block_parser = PageParser()
        block_parser.feed(block)
        for href, attrs in block_parser.hrefs:
            if attrs.get("target") or attrs.get("rel") or attrs.get("aria-label"):
                fail(errors, f"privacy-policy/index.html: submitted policy link must stay same-tab without new-window attributes: {href}")

    footer_match = re.search(r"<footer\b.*?</footer>", home, re.DOTALL)
    footer_links = re.findall(r'<a class="footer-policy-link" href="privacy-policy/index\.html">([^<]+)</a>', footer_match.group(0) if footer_match else "")
    if footer_links != ["개인정보처리방침"]:
        fail(errors, "index.html: homepage footer must contain exactly one 개인정보처리방침 link to privacy-policy/index.html")


def check_seoulroll_ios_policy(errors: list[str]) -> None:
    path = ROOT / SEOULROLL_IOS_POLICY_PAGE
    if not path.is_file():
        fail(errors, f"missing SeoulRoll iOS privacy policy: {SEOULROLL_IOS_POLICY_PAGE}")
        return
    try:
        source = path.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(source)
        parser.close()
    except (OSError, UnicodeError) as exc:
        fail(errors, f"{SEOULROLL_IOS_POLICY_PAGE}: cannot parse: {exc}")
        return

    if parser.canonical != SEOULROLL_IOS_POLICY_URL:
        fail(errors, f"{SEOULROLL_IOS_POLICY_PAGE}: canonical should be {SEOULROLL_IOS_POLICY_URL}, got {parser.canonical}")
    if parser.title != "서울롤(FilmRoll) iOS 개인정보처리방침 | Privacy Policy":
        fail(errors, f"{SEOULROLL_IOS_POLICY_PAGE}: title does not match the locked iOS policy identity")
    if parser.description != "서울롤(FilmRoll) iOS 앱의 개인정보처리방침":
        fail(errors, f"{SEOULROLL_IOS_POLICY_PAGE}: meta description does not match the locked iOS policy copy")
    if len(parser.h1) != 2:
        fail(errors, f"{SEOULROLL_IOS_POLICY_PAGE}: expected one Korean and one English H1, found {len(parser.h1)}")
    if source.count('data-language="ko"') != 1 or source.count('data-language="en"') != 1:
        fail(errors, f"{SEOULROLL_IOS_POLICY_PAGE}: expected exactly one Korean and one English policy section")
    if source.count('datetime="2026-08-26"') != 2:
        fail(errors, f"{SEOULROLL_IOS_POLICY_PAGE}: both language sections must use effective date 2026-08-26")

    required_anchors = {
        "app identity": ("서울롤", "FilmRoll", "com.thirdtype.seoulroll"),
        "contact": ("thirdtype@nate.com",),
        "photo picker and metadata": ("PhotosPicker", "촬영일·수정일", "capture and modification dates"),
        "local processing": ("기기 안에서", "on the device"),
        "Photos save and share": ("사진 보관함", "iOS 공유 시트", "Photos library", "iOS share sheet"),
        "local settings": ("UserDefaults",),
        "ads and consent": ("Google Mobile Ads", "UMP", "ATT"),
        "StoreKit subscriptions": ("Apple StoreKit", "monthly and annual Premium subscription"),
        "deletion": ("삭제", "deletion"),
        "children": ("만 13세 미만", "children under 13"),
        "policy changes": ("방침 변경", "effective date"),
        "Google and Apple policy links": (GOOGLE_PRIVACY_URL, GOOGLE_ADS_TECHNOLOGY_URL, APPLE_PRIVACY_URL),
    }
    for label, anchors in required_anchors.items():
        if not all(anchor in source for anchor in anchors):
            missing = [anchor for anchor in anchors if anchor not in source]
            fail(errors, f"{SEOULROLL_IOS_POLICY_PAGE}: missing {label} anchor(s): {', '.join(missing)}")

    if len([href for href, _ in parser.hrefs if href == "mailto:thirdtype@nate.com"]) < 2:
        fail(errors, f"{SEOULROLL_IOS_POLICY_PAGE}: expected clickable contact links in both language sections")
    for href in (GOOGLE_PRIVACY_URL, GOOGLE_ADS_TECHNOLOGY_URL, APPLE_PRIVACY_URL):
        if source.count(href) < 2:
            fail(errors, f"{SEOULROLL_IOS_POLICY_PAGE}: expected {href} in both language sections")
    for href, _ in parser.hrefs:
        if href and not href.startswith("#"):
            check_local_target(path, href, errors, "href")

    for forbidden in ("Android", "Google Play", "Google Play Billing", "advertising ID", "광고 ID"):
        if forbidden.lower() in source.lower():
            fail(errors, f"{SEOULROLL_IOS_POLICY_PAGE}: iOS policy contains a platform-mismatched or unsupported claim: {forbidden}")


def check_seoulroll_support(errors: list[str]) -> None:
    path = ROOT / SEOULROLL_SUPPORT_PAGE
    if not path.is_file():
        fail(errors, f"missing SeoulRoll support page: {SEOULROLL_SUPPORT_PAGE}")
        return
    try:
        source = path.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(source)
        parser.close()
    except (OSError, UnicodeError) as exc:
        fail(errors, f"{SEOULROLL_SUPPORT_PAGE}: cannot parse: {exc}")
        return

    if parser.canonical != SEOULROLL_SUPPORT_URL:
        fail(errors, f"{SEOULROLL_SUPPORT_PAGE}: canonical should be {SEOULROLL_SUPPORT_URL}, got {parser.canonical}")
    if parser.title != "서울롤(FilmRoll) iOS 지원 | Support":
        fail(errors, f"{SEOULROLL_SUPPORT_PAGE}: title does not match the locked support identity")
    if parser.description != "서울롤(FilmRoll) iOS 앱 사용 안내와 지원 연락처":
        fail(errors, f"{SEOULROLL_SUPPORT_PAGE}: meta description does not match the locked support copy")
    if len(parser.h1) != 2:
        fail(errors, f"{SEOULROLL_SUPPORT_PAGE}: expected one Korean and one English H1, found {len(parser.h1)}")
    if source.count('data-language="ko"') != 1 or source.count('data-language="en"') != 1:
        fail(errors, f"{SEOULROLL_SUPPORT_PAGE}: expected exactly one Korean and one English support section")

    required_anchors = (
        "서울롤",
        "FilmRoll",
        "필름롤",
        "사진 편집",
        "타임스탬프",
        "구독",
        "복원",
        "Apple 구독 관리",
        "광고",
        "개인정보 선택",
        "Film Roll",
        "Photo Edit",
        "Timestamp",
        "Restore",
        "subscription management",
        "Ads and privacy choices",
        "문의",
        "Contact",
    )
    for anchor in required_anchors:
        if anchor not in source:
            fail(errors, f"{SEOULROLL_SUPPORT_PAGE}: missing support anchor: {anchor}")

    if len([href for href, _ in parser.hrefs if href == "mailto:thirdtype@nate.com"]) != 2:
        fail(errors, f"{SEOULROLL_SUPPORT_PAGE}: expected exactly one contact link per language section")
    if source.count(SEOULROLL_IOS_POLICY_URL) != 2:
        fail(errors, f"{SEOULROLL_SUPPORT_PAGE}: iOS privacy-policy URL must appear once per language section")
    if source.count(APPLE_SUBSCRIPTION_MANAGEMENT_URL) < 2:
        fail(errors, f"{SEOULROLL_SUPPORT_PAGE}: Apple subscription-management URL is missing")
    for href, _ in parser.hrefs:
        if href and not href.startswith("#"):
            check_local_target(path, href, errors, "href")

    forbidden_promises = (
        "24시간",
        "48시간",
        "영업일",
        "응답 시간",
        "응답시간",
        "response time",
        "reply within",
        "guaranteed response",
        "SLA",
    )
    lowered = source.lower()
    for promise in forbidden_promises:
        if promise.lower() in lowered:
            fail(errors, f"{SEOULROLL_SUPPORT_PAGE}: support response-time promise is forbidden: {promise}")


def check_frozen_policy_files(errors: list[str]) -> None:
    for relative, expected_hash in FROZEN_POLICY_HASHES.items():
        path = ROOT / relative
        if not path.is_file():
            fail(errors, f"missing frozen policy file: {relative}")
            continue
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            fail(errors, f"frozen policy hash mismatch for {relative}: expected {expected_hash}, got {actual_hash}")


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
    expected = [
        BASE_URL,
        urljoin(BASE_URL, PRIVACY_POLICY_ROUTE),
        urljoin(BASE_URL, BUSINESS_NEWS_CONTACT_ROUTE),
        SEOULROLL_IOS_POLICY_URL,
        SEOULROLL_SUPPORT_URL,
    ] + [urljoin(BASE_URL, route) for route in EXPECTED_ROUTES]
    if locations != expected:
        fail(errors, f"sitemap URLs differ: expected {expected}, got {locations}")


def check_business_news_contact(errors: list[str]) -> None:
    path = ROOT / BUSINESS_NEWS_CONTACT_PAGE
    if not path.is_file():
        fail(errors, f"missing Business News contact page: {BUSINESS_NEWS_CONTACT_PAGE}")
        return
    try:
        parser = PageParser()
        source = path.read_text(encoding="utf-8")
        parser.feed(source)
        parser.close()
    except (OSError, UnicodeError) as exc:
        fail(errors, f"{BUSINESS_NEWS_CONTACT_PAGE}: cannot parse: {exc}")
        return

    expected = urljoin(BASE_URL, BUSINESS_NEWS_CONTACT_ROUTE)
    if parser.canonical != expected:
        fail(errors, f"{BUSINESS_NEWS_CONTACT_PAGE}: canonical should be {expected}, got {parser.canonical}")
    if len(parser.h1) != 1 or "문의하기" not in parser.h1[0]:
        fail(errors, f"{BUSINESS_NEWS_CONTACT_PAGE}: expected one clear 문의하기 H1")
    if not parser.title or not parser.description:
        fail(errors, f"{BUSINESS_NEWS_CONTACT_PAGE}: title and meta description are required")

    email_links = [href for href, _ in parser.hrefs if href == "mailto:thirdtype@nate.com"]
    if len(email_links) != 1:
        fail(errors, f"{BUSINESS_NEWS_CONTACT_PAGE}: expected one clickable thirdtype@nate.com link")
    if BUSINESS_NEWS_ANDROID_POLICY_URL not in {href for href, _ in parser.hrefs}:
        fail(errors, f"{BUSINESS_NEWS_CONTACT_PAGE}: current Android privacy-policy link is missing")
    if "../../../business-news/privacy-policy.html" in {href for href, _ in parser.hrefs}:
        fail(errors, f"{BUSINESS_NEWS_CONTACT_PAGE}: stale local iOS privacy-policy link is forbidden")

    lowered = source.lower()
    required_anchors = {
        "app name": "경제신문",
        "operator context": "슬기로운 생활",
        "news service": "뉴스",
        "rss aggregator": "rss",
        "regular updates": "정기적으로 업데이트",
        "original publisher/source": "원출처",
        "source attribution": "출처",
        "original article": "원문",
    }
    for label, anchor in required_anchors.items():
        if anchor.lower() not in lowered:
            fail(errors, f"{BUSINESS_NEWS_CONTACT_PAGE}: missing {label} anchor: {anchor}")
    for term in ("iOS 17 이상", "Apple 계정"):
        if term.lower() in lowered:
            fail(errors, f"{BUSINESS_NEWS_CONTACT_PAGE}: iOS-only term is forbidden: {term}")

    for href, _ in parser.hrefs:
        if href and not href.startswith("#"):
            check_local_target(path, href, errors, "href")
    for src in parser.srcs:
        if src:
            check_local_target(path, src, errors, "asset")


def check_business_news_contract(errors: list[str]) -> None:
    home_path = ROOT / "index.html"
    detail_path = ROOT / "apps" / "business-news" / "index.html"
    hub_path = ROOT / "privacy-policy" / "index.html"
    contact_path = ROOT / BUSINESS_NEWS_CONTACT_PAGE
    paths = (home_path, detail_path, hub_path, contact_path)
    if not all(path.is_file() for path in paths):
        return

    home = home_path.read_text(encoding="utf-8")
    detail = detail_path.read_text(encoding="utf-8")
    hub = hub_path.read_text(encoding="utf-8")
    contact = contact_path.read_text(encoding="utf-8")

    home_match = re.search(
        r'<article class="app-feature\s+app-feature--business-news"[^>]*data-app="business-news"[^>]*>(.*?)</article>',
        home,
        re.DOTALL,
    )
    if not home_match:
        fail(errors, "index.html: Business News feature is missing")
    else:
        home_block = home_match.group(1)
        if '<span class="app-feature-platform">Android · iPhone</span>' not in home_block:
            fail(errors, "index.html: Business News must declare Android · iPhone")
        home_parser = PageParser()
        home_parser.feed(home_block)
        home_stores = tuple(href for href, _ in home_parser.hrefs if href in STORE_LINKS and STORE_LINKS[href] == "business-news")
        expected_stores = (BUSINESS_NEWS_PLAY_URL, BUSINESS_NEWS_APPLE_URL)
        if home_stores != expected_stores:
            fail(errors, f"index.html: Business News store links differ: expected {expected_stores}, got {home_stores}")

    detail_parser = PageParser()
    detail_parser.feed(detail)
    if '<p class="eyebrow">Android · iPhone</p>' not in detail:
        fail(errors, "apps/business-news/index.html: detail page must declare Android · iPhone")
    detail_stores = tuple(href for href, _ in detail_parser.hrefs if href in STORE_LINKS and STORE_LINKS[href] == "business-news")
    expected_stores = (BUSINESS_NEWS_PLAY_URL, BUSINESS_NEWS_APPLE_URL)
    if detail_stores != expected_stores:
        fail(errors, f"apps/business-news/index.html: store links differ: expected {expected_stores}, got {detail_stores}")
    if BUSINESS_NEWS_DETAIL_POLICY_HREF not in {href for href, _ in detail_parser.hrefs}:
        fail(errors, f"apps/business-news/index.html: privacy hub link is missing: {BUSINESS_NEWS_DETAIL_POLICY_HREF}")
    if len(detail_parser.jsonld) != 1:
        fail(errors, "apps/business-news/index.html: expected one SoftwareApplication JSON-LD block")
    else:
        try:
            detail_jsonld = json.loads(detail_parser.jsonld[0])
        except json.JSONDecodeError as exc:
            fail(errors, f"apps/business-news/index.html: invalid JSON-LD: {exc}")
        else:
            if detail_jsonld.get("operatingSystem") != "Android, iOS":
                fail(errors, "apps/business-news/index.html: JSON-LD operatingSystem must be Android, iOS")
            download_urls = detail_jsonld.get("downloadUrl")
            if tuple(download_urls) != expected_stores:
                fail(errors, f"apps/business-news/index.html: JSON-LD downloadUrl differs: expected {expected_stores}, got {download_urls}")

    hub_match = re.search(
        r'<article class="privacy-entry" data-app="business-news"[^>]*>(.*?)</article>',
        hub,
        re.DOTALL,
    )
    if not hub_match:
        fail(errors, "privacy-policy/index.html: Business News row 07 is missing")
    else:
        hub_row_parser = PageParser()
        hub_row_parser.feed(hub_match.group(0))
        hub_policy_links = tuple(href for href, _ in hub_row_parser.hrefs if href in {BUSINESS_NEWS_ANDROID_POLICY_URL, BUSINESS_NEWS_IPHONE_POLICY_URL})
        expected_policy_links = (BUSINESS_NEWS_ANDROID_POLICY_URL, BUSINESS_NEWS_IPHONE_POLICY_URL)
        if hub_policy_links != expected_policy_links:
            fail(errors, f"privacy-policy/index.html: Business News policy links differ: expected {expected_policy_links}, got {hub_policy_links}")
    contact_parser = PageParser()
    contact_parser.feed(contact)
    contact_policy_links = tuple(href for href, _ in contact_parser.hrefs if href in {BUSINESS_NEWS_ANDROID_POLICY_URL, BUSINESS_NEWS_IPHONE_POLICY_URL})
    if contact_policy_links != (BUSINESS_NEWS_ANDROID_POLICY_URL,):
        fail(errors, f"{BUSINESS_NEWS_CONTACT_PAGE}: Android company-domain policy link is missing or duplicated: {contact_policy_links}")

    parsed_policy_urls = (urlparse(BUSINESS_NEWS_ANDROID_POLICY_URL), urlparse(BUSINESS_NEWS_IPHONE_POLICY_URL))
    if any(parsed.scheme != "https" or parsed.netloc != "www.thirdtype.net" for parsed in parsed_policy_urls):
        fail(errors, "Business News policy URLs must use https://www.thirdtype.net/")
    for label, parser in (("detail", detail_parser), ("contact", contact_parser)):
        for href, _ in parser.hrefs:
            if any(host in href.lower() for host in BUSINESS_NEWS_FORBIDDEN_POLICY_HOSTS):
                fail(errors, f"Business News {label} has a forbidden policy host: {href}")
    if hub_match:
        for href in re.findall(r'<a\b[^>]*href="([^"]+)"', hub_match.group(0)):
            if any(host in href.lower() for host in BUSINESS_NEWS_FORBIDDEN_POLICY_HOSTS):
                fail(errors, f"Business News privacy row has a forbidden policy host: {href}")


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
        if route == "" or route in EXPECTED_ROUTES or route == PRIVACY_POLICY_ROUTE:
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
            detail_images = [image for image in parser.images if image.get("src", "").startswith("../../assets/screenshots/")]
            if len(detail_images) != 3:
                fail(errors, f"{relative}: expected exactly 3 official detail screenshots, found {len(detail_images)}")
            for image in detail_images:
                for key in ("alt", "width", "height", "decoding", "loading"):
                    if not image.get(key):
                        fail(errors, f"{relative}: detail screenshot missing {key}: {image.get('src', '<missing>')}")
                if image.get("loading") != "lazy" or image.get("decoding") != "async":
                    fail(errors, f"{relative}: detail screenshots must use loading=lazy and decoding=async: {image.get('src', '<missing>')}")
            page_text = path.read_text(encoding="utf-8")
            if len(re.findall(r'class="detail-shot"', page_text)) != 3:
                fail(errors, f"{relative}: expected three alternating detail-shot figures")
            if "detail-shot:nth-child(even)" not in (ROOT / "assets" / "site.css").read_text(encoding="utf-8"):
                fail(errors, "assets/site.css: detail gallery is missing alternating editorial flow")
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
        if store_count != 11:
            fail(errors, f"index.html: expected 11 official store links, found {store_count}")


def check_http(base: str, errors: list[str]) -> None:
    root = base.rstrip("/") + "/"
    routes = ["", PRIVACY_POLICY_ROUTE, BUSINESS_NEWS_CONTACT_ROUTE, SEOULROLL_IOS_POLICY_ROUTE, SEOULROLL_SUPPORT_ROUTE] + EXPECTED_ROUTES
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
    parser.add_argument("--http-base", help="also request home, privacy hub, SeoulRoll iOS pages, Business News contact, and all seven detail routes from a running local server")
    args = parser.parse_args()
    errors: list[str] = []
    check_pages(errors)
    check_naver_verification(errors)
    check_images(errors)
    check_screenshot_assets(errors)
    check_editorial_structure(errors)
    check_detail_content(errors)
    check_privacy_hub(errors)
    check_seoulroll_ios_policy(errors)
    check_seoulroll_support(errors)
    check_frozen_policy_files(errors)
    check_social_image(errors)
    check_sitemap(errors)
    check_business_news_contact(errors)
    check_business_news_contract(errors)
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
    print(f"VALIDATION PASSED: {len(page_files())} canonical HTML pages + Business News contact + SeoulRoll iOS policy/support, 6 local icons, 12 sitemap URLs")
    if args.http_base:
        print(f"HTTP SMOKE PASSED: {args.http_base.rstrip('/')}/ + privacy hub + SeoulRoll iOS policy/support + Business News contact + 7 detail routes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
