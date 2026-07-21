# 빵찌(bbangjjioo) 자기관리·재테크·피부 일상 스레드 자동화

30대 중반 1인 사업가 '빵찌'가 혼자 일하며 챙기는 **자기관리·재테크·피부 고민**을,
친구에게 툭 털어놓듯 매일 하나씩 스레드(Threads)에 올리는 자동화입니다.
기존에 올린 글의 톤(편한 반말, 질문형 마무리 "다들 이럴 때 있어?")을 이어받아,
사람들이 공감·저장·댓글로 반응할 **일상 고민 이야기**를 씁니다.

세 축:
- **자기관리** — 헬스·운동, 스트레스, 수면 부족
- **재테크** — 경기도 부동산, 전세/매매, 현금흐름
- **피부케어** — 민감성 트러블·좁쌀·여드름 흉터(얼굴), 등드름·몸드름·목드름·머리숱(바디)

> ⚠️ 결혼식 준비(스드메·홀 투어·상견례 등)와 가족(시댁·친정·양가) 이야기는 쓰지 않습니다.
> 위 세 축의 '일상 고민'만 다룹니다.

> **이 폴더는 오산디에스치과 자동화(`../오산스레드자동화`)와 완전히 분리되어 있습니다.**
> 별도의 GitHub 저장소·Secrets로 운영하므로 기존 자동화에 전혀 영향을 주지 않습니다.

## 구조

| 파일 | 역할 |
|---|---|
| `threads_post.py` | 시간대·요일로 주제 선택 → 서브소재/형식 랜덤 → Claude 글 생성 → Threads 게시 |
| `.github/workflows/threads-daily.yml` | **하루 2회** 크론 (오전·심야), 랜덤 지연 포함 |
| `docs/글쓰기_가이드.md` | 글쓰기 기준(구조·톤·금지어·체크리스트) |
| `docs/시드_기존글.md` | 톤 참고용 기존 글 모음 |
| `requirements.txt` | 파이썬 패키지 (anthropic, requests) |

### 발행 스케줄 — 하루 2회 (일요일은 쉼)

| 슬롯 | 크론(UTC) | 게시 시각(KST) | 성격 |
|---|---|---|---|
| **오전** | `0 22 * * 0-5` | 07:00 + 랜덤 0~120분 → **07:00~09:00** | 하루를 시작하며 실천하는 주제 |
| **심야** | `0 13 * * 1-6` | 22:00 + 랜덤 0~90분 → **22:00~23:30** | 하루를 마무리하며 돌아보는 주제 |

랜덤 지연으로 매일 게시 시각이 조금씩 달라져 사람처럼 보입니다.

> 심야 슬롯의 지연 상한이 90분인 이유: GitHub 크론은 혼잡할 때 수십 분 늦게 뜹니다.
> 자정을 넘기면 날짜가 바뀌어 **다음 날 주제로** 발행돼버리므로, 23:30에서 끊고
> 30분의 여유를 남겨둡니다.

슬롯은 워크플로우가 **크론 식을 보고 명시로 `--slot`을 넘깁니다.** 스크립트의 시각
자동 판별에 맡기면 크론이 늦게 떠 자정을 넘겼을 때 슬롯이 `morning`으로 뒤집힙니다.

### 요일 × 시간대 편성 (각 주제 주 2회)

| 요일 | 오전 | 심야 |
|---|---|---|
| 월 | 운동·헬스 | 얼굴 피부 |
| 화 | 재테크·경기도 부동산 | 바디·두피 |
| 수 | 스트레스·수면 | 소소한 자기관리 일상 |
| 목 | 운동·헬스 | 바디·두피 |
| 금 | 재테크·경기도 부동산 | 얼굴 피부 |
| 토 | 스트레스·수면 | 소소한 자기관리 일상 |

같은 날 오전/심야는 **주제도 소재도 서로 다르게** 생성됩니다(날짜+슬롯 시드).

각 요일마다 6개의 서브소재 풀이 있고, **날짜를 시드로** 하나를 골라 매일 다른 이야기를 씁니다.
같은 날 재실행해도 같은 소재가 나와 안전합니다(중복 게시 방지).

## 현재 상태 — 가동 중 ✅ (2026-07-21)

| 항목 | 상태 |
|---|---|
| 저장소 `scalemaker-ship-it/bbangjjioo-threads` (private) | ✅ |
| 글 생성 (Claude) | ✅ dry-run으로 오전/심야 양쪽 검증 |
| 크론 스케줄 (오전 1개 / 심야 1개) | ✅ |
| 시크릿 3종 (`ANTHROPIC_API_KEY`, `THREADS_USER_ID`, `THREADS_ACCESS_TOKEN`) | ✅ |
| **실제 발행** | ✅ **성공** — 2026-07-21 00:04 KST, 게시물 ID `18096870098210197` |

`THREADS_USER_ID` = `37012355505078650` (Threads 스코프 ID).
Meta 콘솔 state 파라미터에 보이는 `17841...`는 Instagram 스코프 ID라 **쓰면 안 됩니다.**

### 토큰 재발급 절차 (약 60일마다 필요)

Meta의 "액세스 토큰 생성하기"는 `window.open` 팝업이라 브라우저 자동화로는 못 엽니다.
대신 아래 경로로 우회했습니다 — 다음에도 동일하게 하면 됩니다.

1. [앱 설정 → 이용 사례 → Threads API 액세스 → 설정](https://developers.facebook.com/apps/1333145695571887/use_cases/customize/settings/?product_route=threads-api)
   맨 아래 **사용자 토큰 생성기**
2. 페이지 컨텍스트에서 `window.open`을 후킹해 **팝업 URL을 가로챈다**
   (URL은 `threads.com/oauth/authorize/` — 표준 OAuth)
3. 그 URL로 **같은 탭에서** 이동 → 동의 화면에서 "bbangjjioo 계정으로 계속"
4. `developers.facebook.com/threads/token_generator/oauth/?code=...` 로 리디렉션됨.
   이 페이지는 팝업 전용이라 화면은 비어 있지만, **HTML 안에 장기 토큰이 들어 있다.**
   `document.documentElement.outerHTML` 에서 `/TH[A-Za-z0-9_\-]{60,}/` 로 추출.
5. 검증 후 시크릿 등록:
   ```bash
   curl -s "https://graph.threads.net/v1.0/me?fields=id,username&access_token=<토큰>"
   gh secret set THREADS_ACCESS_TOKEN --repo scalemaker-ship-it/bbangjjioo-threads
   ```

> 막다른 길 2개(재시도하지 말 것):
> - **authorization code 직접 교환 불가** — `redirect_uri`가 Meta 생성기 전용이라
>   우리 client_secret으로 교환하면 `Invalid redirect_uri (code 191)`.
> - **OAuth 리디렉션 자체 등록 불가** — 이용 사례 설정의 "리디렉션 콜백 URL" 폼이
>   저장 자체가 안 됨(2026-07-20 재확인, 여전히 빈칸). Meta 쪽 문제로 추정.

> 폴백: 토큰이 계속 안 풀리면 빵찌 로그인된 Threads 웹 UI에 직접 붙여넣어 발행하는
> 경로가 확인돼 있습니다(2026-07-16 테스트 발행 성공). 다만 무인 자동화는 안 됩니다.

> Threads User ID / Access Token 은 반드시 **빵찌 계정** 것을 넣으세요.
> 오산 계정 토큰을 넣으면 오산 계정에 글이 올라갑니다.

> ⚠️ Threads 토큰은 약 60일 후 만료됩니다. 만료되면 위 4~5단계를 다시 수행하세요.

## 로컬에서 미리보기 (게시 없이 글만 확인)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...      # Threads 토큰 없이 API 키만 있으면 됨
python threads_post.py --dry-run                    # 지금 시각의 슬롯으로 생성
python threads_post.py --dry-run --slot morning     # 오전 글 강제 생성
python threads_post.py --dry-run --slot evening     # 심야 글 강제 생성
```

## 로컬에서 실제 게시

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
export THREADS_USER_ID=...
export THREADS_ACCESS_TOKEN=...
python threads_post.py
```

## 참고
- 모델: `claude-opus-4-8`.
- Threads API는 무료, Claude API는 하루 1회 짧은 글만 생성하므로 비용이 매우 적습니다.
- 스케줄 변경: `.github/workflows/threads-daily.yml`의 `cron` 값 수정(UTC 기준).
- 소재를 늘리거나 톤을 바꾸려면 `threads_post.py`의 `TOPICS`, `SYSTEM_PROMPT`만 수정하면 됩니다.

## 톤 & 안전 원칙
- **편한 반말 일상글**, 친구에게 툭 털어놓듯. 광고/훈수/시적 과잉 금지.
- **자기관리·재테크·피부** 세 축만 다룬다. 결혼식 준비·가족 이야기 금지.
- 피부/건강: 의학적 단정("완치"·"100%")·제품 실명·병원 저격 금지. '내 경험상 ~해봤더니' 식으로만.
- 재테크: 단정적 투자 권유·수익 보장 금지. 개인 관찰·경험으로만.
- 해시태그 없음, **이모지 전면 금지**(프롬프트 지시 + `strip_emoji()`로 발행 직전 실제 제거).
  감정은 `ㅜㅜ`, `..`, `ㅋㅋ` 같은 텍스트로만.
- 사람들에게 던지는 질문으로 마무리(댓글·경험 공유 유도).
