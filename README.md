# 빵찌(bbangjjioo) 연애 고민 스레드 자동화

30대 중반 1인 사업가 '빵찌'가 3년 넘게 만난 남자친구와 연애하며 겪는
**사소한 고민과 마음**을, 친구에게 툭 털어놓듯 매일 하나씩 스레드(Threads)에
올리는 자동화입니다. 기존에 올린 글의 톤(편한 반말, "내가 더 좋아하는 것 같은
기분", "나만 결혼하고 싶어하는 것 같아서 고민이야")을 이어받아,
사람들이 공감·반응할 **연애 고민 이야기**를 씁니다.

> ⚠️ 아직 결혼 '준비' 단계가 아닙니다. 스드메·상견례·웨딩홀 같은 결혼식 준비와
> 시댁·친정 등 **가족 이야기는 쓰지 않고**, 오직 '나와 남자친구' 사이의 연애 고민만 다룹니다.

> **이 폴더는 오산디에스치과 자동화(`../오산스레드자동화`)와 완전히 분리되어 있습니다.**
> 별도의 GitHub 저장소·Secrets로 운영하므로 기존 자동화에 전혀 영향을 주지 않습니다.

## 구조

| 파일 | 역할 |
|---|---|
| `threads_post.py` | 요일 소재 선택 → 서브소재/톤 랜덤 → Claude 일기 생성 → Threads 게시 |
| `.github/workflows/threads-daily.yml` | 월~토 09:00 KST 크론 스케줄 |
| `requirements.txt` | 파이썬 패키지 (anthropic, requests) |

### 요일별 소재 (일요일은 쉼)

| 요일 | 큰 주제 |
|---|---|
| 월 | 마음의 온도차 (내가 더 좋아하는 것 같은 마음) |
| 화 | 결혼을 두고 드는 마음 (하고싶다↔망설임, 나만 원하는 듯) |
| 수 | 표현과 서운함 (연락·표현 방식 차이) |
| 목 | 미래에 대한 마음 (아이·나이·서로 다른 그림) |
| 금 | 나와 연애 사이 (일·자존감·맞춰주는 마음) |
| 토 | 소소한 연애 일상 (가벼운 데이트 감정) |

각 요일마다 6개의 서브소재 풀이 있고, **날짜를 시드로** 하나를 골라 매일 다른 이야기를 씁니다.
같은 날 재실행해도 같은 소재가 나와 안전합니다(중복 게시 방지).

## 최초 설정 (1회만)

### 1. GitHub 저장소 만들기
1. github.com 로그인 → **New repository** → 이름 자유(예: `bbangjjioo-threads`), **Private** 권장 → Create.
2. 이 `빵찌결혼준비자동화` 폴더의 파일들을 그 저장소에 올립니다(드래그 업로드 또는 git push).

> ⚠️ 오산 저장소(`osan-threads`)와 **다른 새 저장소**를 만드세요. 섞이면 안 됩니다.

### 2. Secrets 등록
저장소 → **Settings → Secrets and variables → Actions → New repository secret** 에서 3개 등록:

| 이름 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic 콘솔 API 키 (`console.anthropic.com`) |
| `THREADS_USER_ID` | **빵찌 계정**의 Threads 사용자 ID |
| `THREADS_ACCESS_TOKEN` | **빵찌 계정**의 Threads 액세스 토큰 |

> Threads User ID / Access Token 은 **빵찌 계정** 것을 넣어야 합니다.
> 오산 계정 토큰을 넣으면 오산 계정에 글이 올라가니 주의하세요.

### 3. 동작 테스트
저장소 → **Actions** 탭 → "빵찌 연애고민 스레드 자동 게시" → **Run workflow** 로 즉시 1회 실행.
로그에 "게시 완료"가 뜨고 빵찌 스레드에 글이 올라오면 성공입니다.

## 로컬에서 미리보기 (게시 없이 글만 확인)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...      # Threads 토큰 없이 API 키만 있으면 됨
python threads_post.py --dry-run  # 오늘 요일에 맞는 글을 생성만 하고 출력
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
- **편한 반말 일기체**, 친구에게 툭 털어놓듯. 광고/훈수/시적 과잉 금지.
- **연애 고민만** 다룬다. 결혼식 준비(스드메·상견례·웨딩홀 등)와 가족(시댁·친정·양가) 이야기 금지.
- 남친 미화·비난 금지, 있는 그대로의 온도차를 담담히.
- 해시태그 없음, 이모지 0~1개, 사람들에게 던지는 질문으로 마무리(댓글 유도).
