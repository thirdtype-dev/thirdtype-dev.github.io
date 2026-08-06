# 슬기로운 생활 회사 사이트 handoff

기록일: 2026-08-06
Spec Lock: `TT-WEB-HANDOFF-20260806 / r1`
콘텐츠 작업 브랜치: `agent/company-website` @ `42d82c798ead1831ed89a9200e62e26d9a808bab`
GitHub Pages 설정: branch `main`, path `/`

## 요약

새로 배포된 `슬기로운 생활` 회사 사이트의 공개 경로와 GitHub Pages 커스텀 도메인 계약을 기록했습니다. `CNAME`은 재빌드 뒤에도 `www.thirdtype.net`을 보존하도록 추가했습니다. GitHub Pages는 `main` 브랜치의 `/` 경로를 사용하며, `agent/company-website`는 콘텐츠 작업 브랜치입니다. 회사 사이트의 동일 tree가 두 브랜치에 별도 커밋된 상태에서 `main`에 추가된 `CNAME`, `business-news/privacy-policy.html`, `business-news/support.html`을 보존하는 non-destructive merge를 수행했습니다. 통합 커밋 `b54470bf1cb06fdee02b10834e1c82d57d8733a7`은 두 원격 ref에서 동일하게 읽혔고 force-push는 사용하지 않았습니다.

## 공개 URL과 콘텐츠 범위

- canonical: <https://www.thirdtype.net/>
- 인증서 발급 중 fallback: <http://www.thirdtype.net/>
- `thirdtype.net` 루트는 GitHub Pages에서 `www.thirdtype.net`으로 리디렉션
- 앱: `/apps/carrotcard/`, `/apps/maedo-signal/`, `/apps/gps-speed-go/`, `/apps/ttcal/`, `/apps/retro-timestamp/`, `/apps/motion-ease/`
- 개인정보 허브: `/privacy-policy/`
- Tumblr는 <https://thirdtype.tumblr.com/>로 분리 유지하며 커스텀 도메인을 되돌리지 않음

## 증거 레이어별 현재 상태

| 레이어 | 기록된 사실 | 경계 |
| --- | --- | --- |
| 소스 | 회사 사이트 콘텐츠 작업 브랜치 `agent/company-website`의 기준 SHA는 `42d82c798ead1831ed89a9200e62e26d9a808bab`; `main`의 `d2842c9`와 동일한 tree `defb5618a2653cfee577d1b72e99b4121e0965cd` | 이후 `main`에 추가된 main-only `CNAME`, `business-news/privacy-policy.html`, `support.html`은 보존 |
| Git 원격 | `origin/main`과 `origin/agent/company-website`에서 통합 커밋 `b54470b` 일치 | 원격 SHA만으로 Pages 빌드를 주장하지 않음 |
| Pages 빌드 | configured source는 `main`, path `/`; 공개 홈페이지와 소스 `index.html` SHA-256 일치 | 최종 handoff 문서 커밋이 새 Pages 빌드를 생성했다는 주장 |
| DNS | apex는 GitHub Pages A 레코드 4개, `www`는 `thirdtype-dev.github.io` CNAME | `api` CNAME과 기존 Google 인증 TXT는 보존; DNS 변경은 하지 않음 |
| 인증서 | GitHub Pages API 상태 `authorization_created`, `https_enforced: false` | HTTPS 발급·강제가 완료되었다고 주장하지 않음 |
| 공개 readback | HTTPS canonical과 HTTP fallback, 루트 리디렉션 및 위 경로를 기록 | HTTP 성공, DNS 수렴, Pages API, 인증서 발급은 서로 대체하지 않음 |

## 남은 작업

1. `_pages-refresh` TXT는 비밀정보가 아닌 전파 확인용 임시 진단 값이므로 제거하고 공개 DNS에서 제거를 다시 읽습니다.
2. 인증서가 승인·강제되면 `authorization_created`/`https_enforced: false` 기록을 새 증거로 갱신합니다.

## 검증 명령

```bash
test "$(cat CNAME)" = "www.thirdtype.net"
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate.py
git diff --check
```

`scripts/validate.py`의 정적 검증은 콘텐츠·메타데이터·링크·자산을 확인하지만 공개 배포, DNS, 인증서, 설치 또는 실제 사용자 결과를 증명하지 않습니다.

## 롤백과 복구

문서 오류는 이 파일과 `README.md`를 수정해 바로잡습니다. 사이트 소스 롤백은 별도 승인과 새 커밋으로 수행하며 원격 이력을 되쓰는 force-push는 사용하지 않습니다. HTTPS 상태가 바뀌면 새 증거로 문서를 갱신합니다.
