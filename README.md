# 슬기로운 생활 회사 사이트

`슬기로운 생활`의 여섯 공개 앱과 회사 철학을 소개하는 dependency-free static site입니다. GitHub Pages에서 정적 파일 그대로 제공할 수 있도록 HTML, CSS, 로컬 이미지 자산만 사용합니다. 앱 상세 페이지에는 앱별 사용 맥락과 기능을 설명하는 한국어 콘텐츠가 있고, 개인정보처리방침 허브는 여섯 앱의 제출된 정책 링크를 플랫폼별로 정리합니다.

## 로컬 미리보기

Python 3가 설치되어 있다면 프로젝트 루트에서 아래 명령을 실행합니다.

```bash
python3 -m http.server 8000
```

브라우저에서 <http://127.0.0.1:8000/>을 열고 홈, <http://127.0.0.1:8000/privacy-policy/index.html>, 여섯 앱 상세 경로, 반응형 폭(360px·768px·데스크톱), 키보드 포커스를 확인하세요. 개인정보처리방침 허브의 외부 제출 링크는 현재 탭에서 열리도록 유지합니다.

## 결정적 검증

별도 패키지 설치 없이 다음 검증을 실행할 수 있습니다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate.py
python3 -m py_compile scripts/validate.py
```

검증기는 HTML 메타데이터, JSON-LD, canonical, sitemap/robots, 로컬 링크와 아이콘, 페이지별 H1, 공식 스토어 링크 수를 확인합니다. 여섯 앱 상세 페이지에는 최소 세 개의 H2/H3, 네 개의 실질적인 문단, 기능 목록, 앱별 중복 없는 본문, visible lede·meta description·JSON-LD 설명의 일관성을 요구합니다. 개인정보 허브는 여섯 앱과 아홉 개의 제출 URL을 순서와 플랫폼별로 비교하고, 제출 링크가 새 탭 속성 없이 현재 탭에서 열리는지와 홈페이지의 `privacy-policy/index.html` 링크를 확인합니다.

홈과 여섯 앱 상세 페이지에는 로컬로 검증한 `assets/og.png`(1728×910)를 절대 URL Open Graph/X 이미지로 연결합니다. `assets/screenshots/SOURCES.tsv`는 18개 공식 스토어 화면의 원본 URL과 크기를 기록하며, `scripts/validate.py`가 PNG/JPEG 형식, 실제 크기, 페이지 이미지 메타데이터와 `summary_large_image` 카드를 확인합니다. 네 개의 기존 호환성 개인정보처리방침 파일과 OG/스크린샷 바이트 보존도 별도 SHA-256/byte 비교로 확인합니다.

HTTP smoke test는 별도 터미널에서 서버를 실행한 뒤 아래 명령으로 수행합니다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate.py --http-base http://127.0.0.1:8000
```

홈, 개인정보 허브, 여섯 앱 상세 경로의 정적 HTML 응답을 확인합니다. 외부 정책 URL의 실제 렌더링과 클릭 결과는 브라우저 QA에서 별도로 확인해야 합니다.

## 공개 전 handoff

1. 로컬 검증과 브라우저 점검 결과를 확인합니다.
2. 승인된 저장소의 GitHub Pages 설정에서 이 폴더를 정적 소스로 선택합니다.
3. 커스텀 도메인과 DNS 변경은 도메인 소유자 확인 후 별도 실행합니다.

이 결과물은 커밋, push, 저장소 생성, Pages 활성화, DNS 변경, Tumblr 변경, Gist 수정, 스토어 필드 수정, Search Console 제출을 수행하지 않습니다. 기존 Tumblr 아카이브(`thirdtype.tumblr.com`)와 제출된 개인정보처리방침 주소도 그대로 둡니다.
