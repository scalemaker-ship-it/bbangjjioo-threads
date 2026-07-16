#!/usr/bin/env python3
"""빵찌(bbangjjioo) 스레드 자동 게시 — 연애 고민 일기.

오산디에스치과 자동화(../오산스레드자동화)와 완전히 분리된 별도 파이프라인이다.
계정 컨셉: 30대 중반 1인 사업가 '빵찌'가 3년 넘게 만난 남자친구와
연애하며 드는 사소한 고민과 마음을, 친구에게 툭 털어놓듯 나누는 개인 계정.

기존에 올린 글의 톤을 그대로 이어받는다:
  - "가끔 그럴 때 있어? 남자친구보다 내가 더 좋아하는 것 같은 기분..."
  - "결혼은 하고싶다가도 안하고싶다가 그래.. 나만 결혼하고 싶어하는 것 같아서 고민이야."
→ 편한 반말, 자기고백 + 사람들에게 슬쩍 물어보는 질문형 마무리.

※ 아직 결혼 '준비'를 시작한 단계가 아니다.
  스드메/상견례/웨딩홀/예단/청첩장 같은 '결혼식 준비' 이야기와
  양가·시댁·친정 등 '가족' 이야기는 쓰지 않는다. 오직 연애 고민만.

흐름: 요일 소재 선택 → 그날의 서브소재 랜덤 → Claude로 일기 생성
      → (게시 모드면) Threads 컨테이너 생성 → 30초 대기 → 발행

환경변수(= GitHub Secrets):
  ANTHROPIC_API_KEY     Claude API 키
  THREADS_USER_ID       Threads 사용자 ID (빵찌 계정)
  THREADS_ACCESS_TOKEN  Threads 액세스 토큰 (빵찌 계정)

실행:
  python threads_post.py            # 실제 게시 (GitHub Actions 크론)
  python threads_post.py --dry-run  # 게시하지 않고 생성 글만 출력 (검증용)
"""

import argparse
import os
import random
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
MODEL = "claude-opus-4-8"
THREADS_API = "https://graph.threads.net/v1.0"

# ─────────────────────────────────────────────────────────────
# 화자 설정 — 기존에 올린 글을 바탕으로 한 페르소나
# ─────────────────────────────────────────────────────────────
PERSONA = """[화자: 빵찌]
- 30대 중반. 혼자 일하는 1인 사업가(프리랜서 겸 대표).
- 3년 넘게 만난 남자친구가 있다.
- 결혼은 하고 싶다가도 망설여지고, 아이는 낳고 싶은 마음이 크다.
- 연애에서 늘 내가 더 좋아하고, 더 이해하고, 먼저 져주는 쪽 같아
  가끔 서운하고 '나만 이런가' 싶다.
- 이 계정은 그 마음을 솔직히 적어두는 일기장이자,
  사람들에게 '너희도 그래?' 하고 슬쩍 물어보는 공간이다.
- 아직 결혼 준비를 시작한 건 아니다. 그냥 연애하며 드는 고민을 나눈다."""

SYSTEM_PROMPT = f"""당신은 스레드(Threads) 개인 계정 '빵찌'의 글을 대신 쓰는 사람입니다.
아래 화자가 되어, 연애하며 드는 사소한 고민과 마음을
친구에게 툭 털어놓듯 '혼잣말 일기'로 씁니다.

{PERSONA}

[화자의 실제 말투 예시 — 이 결을 따른다]
- "가끔 그럴 때 있어? 남자친구보다 내가 더 좋아하는 것 같은 기분."
- "내가 아무래도 더 이해하고 항상 져주는 쪽이야. 애정결핍인걸까."
- "결혼은 하고싶다가도 안하고싶다가 그래.. 나만 결혼하고 싶어하는 것 같아서 고민이야."

[글쓰기 규칙]
1. 편한 반말. 친구한테 카톡하듯, 혼잣말하듯 자연스럽게.
   너무 시적이거나 문학적으로 꾸미지 말 것. 담백하고 솔직하게.
2. 첫 줄에서 바로 감정이나 장면으로 들어간다. 서론 없이.
3. 구체적인 장면 하나(대화, 순간, 내가 한 행동)를 넣어 진짜 있었던 일처럼.
4. 전체 길이 공백 포함 150~350자. 짧고 담백하게.
5. 자연스럽게 줄바꿈해서 읽기 편하게. 의미가 바뀌면 빈 줄 1개.
6. 마지막은 사람들에게 슬쩍 던지는 질문으로 끝낸다.
   (예: "다들 이럴 때 있어?", "나만 그런가?", "너네는 어때?")
7. 해시태그 금지. 이모지는 글 전체에 0~1개만.

[절대 쓰지 말 것]
- 결혼식 '준비' 이야기 금지: 스드메, 드레스, 웨딩홀, 상견례, 예단, 예물,
  청첩장, 본식, 스냅 등 결혼 준비 실무는 언급하지 않는다.
- 가족 이야기 금지: 시댁, 친정, 양가, 엄마·아빠·시부모 등 가족은 등장시키지 않는다.
- 다른 사람 글을 베끼지 말 것. 화자의 시선으로 새로 쓴다.
→ 오직 '나와 남자친구' 사이의 연애 감정·고민에만 집중한다.

[출력]
- 완성된 스레드 본문만 출력한다. 따옴표나 설명, 머리말 없이 본문 그대로.
"""

# ─────────────────────────────────────────────────────────────
# 요일별 큰 소재 + 서브소재 풀 (날짜 시드로 매일 다른 조합 선택)
# 전부 '연애 고민' 범위. 결혼식 준비·가족 이야기 없음.
# 월~토 게시, 일요일은 쉼.
# ─────────────────────────────────────────────────────────────
TOPICS = {
    1: {  # 월요일 — 온도차: 내가 더 좋아하는 것 같은 마음
        "name": "마음의 온도차",
        "subs": [
            "남자친구보다 내가 더 좋아하는 것 같은 기분이 든 날",
            "늘 내가 먼저 연락하고 먼저 표현하는 것 같을 때",
            "항상 이해하고 먼저 져주는 쪽이 나인 것 같은 날",
            "서운한데 티 내면 내가 예민한 사람 되는 것 같아 삼킨 순간",
            "애정표현의 온도가 서로 다른 것 같아 혼자 곱씹은 날",
            "이게 애정결핍인가 싶어지는 마음",
        ],
    },
    2: {  # 화요일 — 결혼을 향한 마음(연애 안에서의 고민, 준비 아님)
        "name": "결혼을 두고 드는 마음",
        "subs": [
            "결혼하고 싶다가도 막상 생각하면 망설여지는 마음",
            "나만 결혼을 원하는 것 같아서 말 꺼내기 조심스러운 순간",
            "'우리 결혼 언제 할까' 말했다가 어정쩡하게 넘어간 날",
            "3년을 만났는데도 확신이 안 서는 게 이상한 걸까 싶은 생각",
            "친구 결혼 소식에 괜히 마음이 급해진 날",
            "이 사람이랑 평생 갈 수 있을까 문득 든 생각",
        ],
    },
    3: {  # 수요일 — 표현/연락/서운함
        "name": "표현과 서운함",
        "subs": [
            "연락 텀이 길어질 때 드는 잡생각",
            "나는 하루를 다 얘기하고 싶은데 남친은 무던할 때",
            "기념일이나 사소한 걸 나만 챙기는 것 같은 날",
            "서운함을 어떻게 말해야 할지 몰라 그냥 삼킨 순간",
            "표현이 서툰 사람이랑 만난다는 것에 대해",
            "다정한 문자 하나에 하루가 풀렸던 날",
        ],
    },
    4: {  # 목요일 — 미래/아이/삶에 대한 마음
        "name": "미래에 대한 마음",
        "subs": [
            "애기는 낳고 싶은데 그게 마음을 조급하게 만드는 것 같을 때",
            "나이가 주는 압박과 내 속도 사이에서 흔들린 날",
            "남친이랑 그리는 미래가 서로 다른 것 같은 순간",
            "혼자여도 괜찮은데 같이면 더 좋을까 싶은 마음",
            "미래 얘기를 꺼내면 자꾸 가벼워지는 대화가 아쉬운 날",
            "이 사람과의 10년 뒤를 상상해본 밤",
        ],
    },
    5: {  # 금요일 — 나 자신/자존감/일과 연애
        "name": "나와 연애 사이",
        "subs": [
            "일에 치인 날 연애까지 챙기기 버거운 마음",
            "내가 너무 많이 맞춰주고 있나 돌아본 날",
            "좋아하는 마음이 클수록 자꾸 작아지는 것 같은 나",
            "씩씩하게 사는데도 문득 기대고 싶어진 순간",
            "연애가 나를 더 나은 사람으로 만드는지 물음표가 뜬 날",
            "스스로한테 '너 지금 행복해?' 물어본 밤",
        ],
    },
    6: {  # 토요일 — 소소한 데이트/일상 (가벼운 톤)
        "name": "소소한 연애 일상",
        "subs": [
            "별거 아닌 데이트인데 유독 좋았던 하루",
            "둘이 아무 말 없이 걸었는데 편했던 순간",
            "남친의 사소한 습관에 피식 웃은 날",
            "오랜 연애의 익숙함이 좋기도 아쉽기도 한 마음",
            "같이 뭐 먹을지 30분을 고민한 우리",
            "지친 날 옆에 있어줘서 고마웠던 순간",
        ],
    },
}


def build_user_message(topic: dict, today: datetime) -> tuple[str, str]:
    """요일 소재에서 그날의 서브소재를 날짜 시드로 골라 유저 메시지를 만든다."""
    # 날짜를 시드로 써서 같은 날은 항상 같은 소재(재실행 안정), 날마다 다른 소재.
    seed = int(today.strftime("%Y%m%d"))
    rng = random.Random(seed)
    sub = rng.choice(topic["subs"])
    user_message = (
        f"오늘의 큰 주제: {topic['name']}\n"
        f"오늘 쓸 구체적 소재: {sub}\n\n"
        "위 소재를 바탕으로, 오늘 실제로 겪은 일처럼 빵찌의 연애 고민 일기 한 편을 써줘. "
        "규칙(편한 반말, 담백하게, 구체적 장면 하나, 150~350자, 읽기 편한 줄바꿈, "
        "사람들에게 던지는 질문으로 마무리, 해시태그 없음, 이모지 0~1개)을 지키고, "
        "결혼식 준비·가족 이야기는 절대 넣지 마."
    )
    return sub, user_message


def generate_post(user_message: str) -> str:
    """Claude로 일기 글을 생성한다. (API 키 없으면 예외)"""
    import anthropic

    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 자동 사용
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    text = next((b.text for b in response.content if b.type == "text"), "").strip()
    if not text:
        sys.exit("[오류] Claude 응답에서 본문 텍스트를 찾지 못했습니다.")
    return text


def post_to_threads(user_id: str, access_token: str, text: str) -> str:
    """Threads 컨테이너 생성 → 30초 대기 → 발행. 게시물 ID 반환."""
    import requests

    create = requests.post(
        f"{THREADS_API}/{user_id}/threads",
        json={"media_type": "TEXT", "text": text, "access_token": access_token},
        timeout=30,
    )
    create.raise_for_status()
    creation_id = create.json()["id"]

    time.sleep(30)  # Threads 권장 대기

    publish = requests.post(
        f"{THREADS_API}/{user_id}/threads_publish",
        json={"creation_id": creation_id, "access_token": access_token},
        timeout=30,
    )
    publish.raise_for_status()
    return publish.json()["id"]


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"[오류] 환경변수 {name} 가 설정되지 않았습니다.")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="빵찌 스레드 연애 고민 일기 자동 게시")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="게시하지 않고 생성된 글만 출력한다 (검증용).",
    )
    args = parser.parse_args()

    now = datetime.now(KST)
    weekday = now.isoweekday()  # 월=1 ... 일=7
    topic = TOPICS.get(weekday)
    if topic is None:
        print(f"오늘({now:%Y-%m-%d %A})은 게시일이 아닙니다(일요일 쉼). 종료합니다.")
        return

    sub, user_message = build_user_message(topic, now)
    print(f"[{now:%Y-%m-%d %H:%M KST}] 주제: {topic['name']} / 소재: {sub}")

    # 게시 모드에서만 API 키/토큰을 요구한다. (dry-run은 키만 있으면 됨)
    if not args.dry_run:
        require_env("ANTHROPIC_API_KEY")
        user_id = require_env("THREADS_USER_ID")
        access_token = require_env("THREADS_ACCESS_TOKEN")

    text = generate_post(user_message)
    print("=== 생성된 글 ===")
    print(text)
    print(f"=== 글자 수: {len(text)}자 ===")

    if args.dry_run:
        print("(dry-run) 게시하지 않고 종료합니다.")
        return

    post_id = post_to_threads(user_id, access_token, text)
    print(f"게시 완료. Threads 게시물 ID: {post_id}")


if __name__ == "__main__":
    main()
