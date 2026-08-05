# 슬기로운 생활 회사 사이트

`슬기로운 생활`의 여섯 가지 공개 앱을 소개하는 dependency-free static site입니다. GitHub Pages에서 정적 파일 그대로 제공할 수 있도록 HTML, CSS, 로컬 WebP 아이콘만 사용합니다.

## 로컬 미리보기

Python 3가 설치되어 있다면 프로젝트 루트에서 아래 명령을 실행합니다.

```bash
python3 -m http.server 8000
```

브라우저에서 <http://127.0.0.1:8000/>을 열고 홈, 여섯 앱 상세 경로, 반응형 폭(360px·768px·데스크톱), 키보드 포커스를 확인하세요.

## 결정적 검증

별도 패키지 설치 없이 다음 검증을 실행할 수 있습니다.

```bash
python3 scripts/validate.py
```

검증기는 HTML 메타데이터, JSON-LD, canonical, sitemap/robots, 로컬 링크와 아이콘, 페이지별 H1, 공식 스토어 링크 수, 금지된 민감 문구를 확인합니다.

홈과 여섯 앱 상세 페이지에는 로컬로 검증한 `assets/og.png`(1730×909)를 절대 URL Open Graph/X 이미지로 연결합니다. `scripts/validate.py`가 PNG 형식, 실제 크기, 일곱 canonical 페이지의 이미지 메타데이터와 `summary_large_image` 카드를 함께 확인합니다.

HTTP smoke test는 별도 터미널에서 서버를 실행한 뒤 아래 명령으로 수행합니다.

```bash
python3 scripts/validate.py --http-base http://127.0.0.1:8000
```

## 공개 전 handoff

1. 로컬 검증과 브라우저 점검 결과를 확인합니다.
2. 승인된 저장소의 GitHub Pages 설정에서 이 폴더를 정적 소스로 선택합니다.
3. 커스텀 도메인과 DNS 변경은 도메인 소유자 확인 후 별도 실행합니다.

이 결과물은 커밋, push, 저장소 생성, Pages 활성화, DNS 변경, Tumblr 변경을 수행하지 않습니다. 기존 Tumblr 아카이브(`thirdtype.tumblr.com`)도 그대로 둡니다.
