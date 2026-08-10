# 슬기로운 생활 회사 사이트 handoff

최초 기록일: 2026-08-06
최근 갱신: 2026-08-10
Spec Lock: `TT-WEB-HANDOFF-20260806 / r1`
콘텐츠 작업 브랜치: `agent/company-website` @ `42d82c798ead1831ed89a9200e62e26d9a808bab`
GitHub Pages 설정: branch `main`, path `/`

## 요약

새로 배포된 `슬기로운 생활` 회사 사이트의 공개 경로와 GitHub Pages 커스텀 도메인 계약을 기록했습니다. `CNAME`은 재빌드 뒤에도 `www.thirdtype.net`을 보존하도록 추가했습니다. GitHub Pages는 `main` 브랜치의 `/` 경로를 사용하며, `agent/company-website`는 콘텐츠 작업 브랜치입니다. 회사 사이트의 동일 tree가 두 브랜치에 별도 커밋된 상태에서 `main`에 추가된 `CNAME`, `business-news/privacy-policy.html`, `business-news/support.html`을 보존하는 non-destructive merge를 수행했습니다. 통합 커밋 `b54470bf1cb06fdee02b10834e1c82d57d8733a7`은 두 원격 ref에서 동일하게 읽혔고 force-push는 사용하지 않았습니다.

## 2026-08-10 개인정보처리방침 링크 복구

개인정보처리방침 허브에서 총명함과 GPS Speed Go 링크가 GitHub Gist 또는 HTML Preview 화면으로 이동하던 문제를 복구했습니다. 플랫폼별 정책 원본을 `www.thirdtype.net`에서 직접 제공하도록 변경했고, 앱 저장소 정책 원본과 바이트 단위로 일치시켰습니다.

- 소스·배포 커밋: `1d0115b6dcf774a367e3dced058c1bb07a3e08a5`
- 원격 readback: `refs/heads/main` = `1d0115b6dcf774a367e3dced058c1bb07a3e08a5`
- GitHub Pages: build `1142064770`, commit `1d0115b`, status `built`
- Pages 설정: `main` / `/`, `cname=www.thirdtype.net`, certificate `approved`, `https_enforced=true`
- 총명함 Android: <https://www.thirdtype.net/privacy-policy/carrotcard-android.html>
- 총명함 iPhone: <https://www.thirdtype.net/privacy-policy/carrotcard-ios.html>
- GPS Speed Go Android: <https://www.thirdtype.net/privacy-policy/gps-speed-go-android.html>
- GPS Speed Go iPhone: <https://www.thirdtype.net/gps-speed-go/privacy-policy.html>
- 공개 브라우저 readback: 허브의 네 URL과 네 정책 문서 제목을 직접 확인
- 로컬 검증: `VALIDATION PASSED: 9 HTML pages, 6 local icons, 8 sitemap URLs`

## 공개 URL과 콘텐츠 범위

- canonical: <https://www.thirdtype.net/>
- HTTPS 인증서 승인 및 강제 적용 확인: `https_enforced=true`
- `thirdtype.net` 루트는 GitHub Pages에서 `www.thirdtype.net`으로 리디렉션
- 앱: `/apps/carrotcard/`, `/apps/maedo-signal/`, `/apps/gps-speed-go/`, `/apps/ttcal/`, `/apps/retro-timestamp/`, `/apps/motion-ease/`
- 개인정보 허브: `/privacy-policy/`
- Tumblr는 <https://thirdtype.tumblr.com/>로 분리 유지하며 커스텀 도메인을 되돌리지 않음

## 증거 레이어별 현재 상태

| 레이어 | 기록된 사실 | 경계 |
| --- | --- | --- |
| 소스 | 회사 사이트 콘텐츠 작업 브랜치 `agent/company-website`의 기준 SHA는 `42d82c798ead1831ed89a9200e62e26d9a808bab`; `main`의 `d2842c9`와 동일한 tree `defb5618a2653cfee577d1b72e99b4121e0965cd` | 이후 `main`에 추가된 main-only `CNAME`, `business-news/privacy-policy.html`, `support.html`은 보존 |
| Git 원격 | `origin/main`에서 개인정보 링크 복구 커밋 `1d0115b` readback | 원격 SHA만으로 Pages 빌드나 공개 전파를 주장하지 않음 |
| Pages 빌드 | build `1142064770`, commit `1d0115b`, status `built`; configured source `main` / `/` | CDN 공개 전파를 대신하지 않음 |
| DNS | apex는 GitHub Pages A 레코드 4개, `www`는 `thirdtype-dev.github.io` CNAME | `api` CNAME과 기존 Google 인증 TXT는 보존; DNS 변경은 하지 않음 |
| 인증서 | GitHub Pages API에서 certificate `approved`, `https_enforced: true` | 개별 공개 정책 문서의 내용 정확성을 대신하지 않음 |
| 공개 readback | HTTPS canonical과 HTTP fallback, 루트 리디렉션 및 위 경로를 기록 | HTTP 성공, DNS 수렴, Pages API, 인증서 발급은 서로 대체하지 않음 |

## 남은 작업

1. `_pages-refresh` TXT는 비밀정보가 아닌 전파 확인용 임시 진단 값이므로 제거하고 공개 DNS에서 제거를 다시 읽습니다.
2. 개인정보처리방침 링크 복구 범위에는 남은 작업이 없습니다. 이후 정책 내용 변경 시 앱 저장소 원본과 사이트 사본을 함께 갱신하고 바이트 보존 검증을 통과시킵니다.

## 검증 명령

```bash
test "$(cat CNAME)" = "www.thirdtype.net"
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate.py
git diff --check
```

`scripts/validate.py`의 정적 검증은 콘텐츠·메타데이터·링크·자산을 확인하지만 공개 배포, DNS, 인증서, 설치 또는 실제 사용자 결과를 증명하지 않습니다.

## 롤백과 복구

문서 오류는 이 파일과 `README.md`를 수정해 바로잡습니다. 사이트 소스 롤백은 별도 승인과 새 커밋으로 수행하며 원격 이력을 되쓰는 force-push는 사용하지 않습니다. HTTPS 상태가 바뀌면 새 증거로 문서를 갱신합니다.
