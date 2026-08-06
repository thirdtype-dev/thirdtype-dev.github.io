# 슬기로운 생활 회사 사이트 handoff

기록일: 2026-08-06
Spec Lock: `TT-WEB-HANDOFF-20260806 / r1`
콘텐츠 작업 브랜치: `agent/company-website` @ `42d82c798ead1831ed89a9200e62e26d9a808bab`
GitHub Pages 설정: branch `main`, path `/`

## 요약

새로 배포된 `슬기로운 생활` 회사 사이트의 공개 경로와 GitHub Pages 커스텀 도메인 계약을 기록했습니다. `CNAME`은 재빌드 뒤에도 `www.thirdtype.net`을 보존하도록 추가했습니다. GitHub Pages는 `main` 브랜치의 `/` 경로를 사용하며, `agent/company-website`는 회사 사이트 콘텐츠를 준비하는 working branch입니다. 회사 사이트 콘텐츠는 이미 `main`의 `d2842c9`에 있고, `d2842c9`와 working branch의 `42d82c7`은 동일한 tree `defb5618a2653cfee577d1b72e99b4121e0965cd`를 가집니다. 이후 `main`에 추가된 main-only `CNAME`, `business-news/privacy-policy.html`, `support.html`은 보존해야 합니다. Coder 단계에서는 로컬 문서만 변경했으며 외부 상태를 변경하지 않았습니다. Lead closeout에서 이 변경을 커밋하고 main-only 파일을 보존하는 non-destructive merge/integration을 수행한 뒤 두 원격 ref를 `git ls-remote`로 읽어 옵니다. 최근 fetch 뒤 `origin/main`은 `66a2f5053ecf8e3ca372603d8331ddfdce4c0956`으로 이동했고 `origin/main...HEAD = 13 2`로 분기했으므로 force-push하지 않습니다. DNS, Tumblr, 스토어 또는 Pages 설정은 각 권한과 검증 증거에 따라 별도 확인합니다.

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
| Pages 빌드 | configured source는 `main`, path `/`; 회사 사이트 콘텐츠는 이미 `main`에 있음 | 최근 fetch 뒤 `origin/main`은 `66a2f5053ecf8e3ca372603d8331ddfdce4c0956`이고 `origin/main...HEAD = 13 2`로 분기했으므로 non-destructive merge/integration 후 두 원격 ref를 `git ls-remote`로 확인하며 force-push하지 않음 |
| DNS | apex는 GitHub Pages A 레코드 4개, `www`는 `thirdtype-dev.github.io` CNAME | `api` CNAME과 기존 Google 인증 TXT는 보존; DNS 변경은 하지 않음 |
| 인증서 | GitHub Pages API 상태 `authorization_created`, `https_enforced: false` | HTTPS 발급·강제가 완료되었다고 주장하지 않음 |
| 공개 readback | HTTPS canonical과 HTTP fallback, 루트 리디렉션 및 위 경로를 기록 | HTTP 성공, DNS 수렴, Pages API, 인증서 발급은 서로 대체하지 않음 |

## 남은 작업

1. `_pages-refresh` TXT는 비밀정보가 아닌 전파 확인용 임시 진단 값이므로 제거하고 공개 DNS에서 제거를 다시 읽습니다.
2. 최근 fetch 뒤 `origin/main`이 `66a2f5053ecf8e3ca372603d8331ddfdce4c0956`으로 이동하고 `origin/main...HEAD = 13 2`로 분기했으므로 이전 fast-forward 계획은 폐기합니다. Lead는 최종 handoff 커밋을 만들 때 main-only `CNAME`, `business-news/privacy-policy.html`, `support.html`을 보존하는 non-destructive merge/integration을 수행하고 force-push하지 않으며, 통합 후 `origin/main`과 `origin/agent/company-website`를 `git ls-remote`로 확인합니다.
3. Lead가 GitHub Pages API, authoritative/public DNS, Tumblr HTTP 응답, 여덟 공개 경로를 각각 확인합니다.
4. 인증서가 승인·강제되면 `authorization_created`/`https_enforced: false` 기록을 새 증거로 갱신합니다.

## 검증 명령

```bash
test "$(cat CNAME)" = "www.thirdtype.net"
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate.py
git diff --check
```

`scripts/validate.py`의 정적 검증은 콘텐츠·메타데이터·링크·자산을 확인하지만 공개 배포, DNS, 인증서, 설치 또는 실제 사용자 결과를 증명하지 않습니다.

## 롤백과 복구

문서 오류는 이 파일과 `README.md`를 수정해 바로잡습니다. 사이트 소스 롤백은 이전 `main` SHA 복원 권한이 명시적으로 부여된 경우에만 Lead가 수행하며, Coder 단계에서는 force-push하지 않고 Lead closeout도 main-only 파일을 보존하는 non-destructive merge/integration만 사용합니다. HTTPS 상태가 바뀌기 전에 커밋된다면 커밋 전 문서를 먼저 갱신합니다.
