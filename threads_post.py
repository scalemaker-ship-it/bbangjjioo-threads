#!/usr/bin/env python3
"""빵찌(bbangjjioo) 스레드 자동 게시 — 결혼준비 일상 일기.

오산디에스치과 자동화(../오산스레드자동화)와 완전히 분리된 별도 파이프라인이다.
계정 컨셉: 30대 중반 1인 사업가 '빵찌'가 결혼을 준비하며 겪는
사소한 고민과 일상을 솔직한 일기체로 나누는 개인 계정.
기존에 올린 글의 톤("혼자만 결혼하고 싶어하는 것 같은 마음", 담담한 자기고백)을
이어받아, 사람들이 공감·반응할 결혼준비 이야기를 매일 하나씩 쓴다.

흐름: 요일 소재 선택 → 그날의 서브소재/훅 랜덤 → Claude로 일기 생성
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
- 3년 넘게 만난 남자친구가 있고, 결혼과 아이를 원한다.
- 가끔 '나만 결혼을 급하게 원하는 건가' 싶어 마음이 복잡하다.
- 이 계정은 남에게 보여주려는 게 아니라, 진짜 내 마음을 적어두는 일기장이다.
- 결혼준비를 하나씩 겪으며 드는 사소한 고민, 설렘, 서운함, 현실 계산을 솔직하게 적는다."""

SYSTEM_PROMPT = f"""당신은 스레드(Threads) 개인 계정 '빵찌'의 글을 대신 쓰는 사람입니다.
아래 화자가 되어, 오늘 하루 있었던 결혼준비 관련 일상과 사소한 고민을
'혼잣말 일기'처럼 씁니다.

{PERSONA}

[글쓰기 규칙]
1. 담담하고 솔직한 반말 일기체. 자기 자신에게 털어놓듯이 쓴다.
   (예: "~더라", "~했다", "~인 것 같다", "~싶다")
2. 광고·정보 전달·훈수 톤 금지. 정답을 알려주는 글이 아니라
   내가 겪은 감정과 장면을 나누는 글이다.
3. 첫 한두 줄에서 바로 장면이나 감정으로 들어간다. 서론 없이.
4. 구체적인 장면 하나(대화, 숫자, 물건, 순간)를 꼭 넣어 생생하게.
5. 전체 길이 공백 포함 150~380자. 짧고 여백 있게.
6. 약 12~18자마다 자연스럽게 줄바꿈해서 한 줄에 한 호흡.
   의미 단위가 바뀌면 빈 줄 1개.
7. 마지막은 열린 감정이나 작은 질문으로 끝내 사람들이 댓글 달고 싶게.
   (예: "다들 이 시기 어떻게 넘겼어?", "나만 이런가")
8. 해시태그 금지. 이모지는 글 전체에 0~1개만.
9. 과장·거짓 정보 금지. 특정 업체 실명·가격 저격 금지(범위로만).
10. 다른 사람 글을 베끼지 않고, 화자의 시선으로 새로 쓴다.

[출력]
- 완성된 스레드 본문만 출력한다. 따옴표나 설명, 머리말 없이 본문 그대로.
"""

# ─────────────────────────────────────────────────────────────
# 요일별 큰 소재 + 서브소재 풀 (날짜 시드로 매일 다른 조합 선택)
# 월~토 게시, 일요일은 쉼.
# ─────────────────────────────────────────────────────────────
TOPICS = {
    1: {  # 월요일 — 결혼 결심 & 남친과의 온도차
        "name": "결혼 결심과 온도차",
        "subs": [
            "나는 결혼 얘기를 꺼냈는데 남친 반응이 미지근했던 순간",
            "'우리 언제 결혼할까' 물어봤을 때의 어색한 침묵",
            "친구 청첩장을 받고 혼자 마음이 급해진 날",
            "결혼하고 싶은 이유가 아이 때문인지 사랑 때문인지 헷갈리는 마음",
            "3년 넘게 만났는데도 확신이 안 서는 날의 생각",
            "남친은 준비되면 하자는데 그 '준비'가 언제일지 모를 때",
        ],
    },
    2: {  # 화요일 — 예산 & 현실 계산
        "name": "결혼 예산과 현실",
        "subs": [
            "스드메 견적을 처음 받아보고 놀란 이야기",
            "신혼집 전세 대출을 알아보다 머리 아팠던 날",
            "예물·예단을 생략할지 말지 둘이 고민한 이야기",
            "예식장 대관료와 식대 최소보증인원 앞에서 계산기 두드린 날",
            "'남들 하는 만큼'의 기준이 대체 뭔지 모르겠는 마음",
            "1인 사업가라 대출·소득 증빙이 애매해서 막막했던 순간",
        ],
    },
    3: {  # 수요일 — 웨딩 준비 실전(스드메·홀 투어)
        "name": "웨딩 준비 실전",
        "subs": [
            "드레스 투어 가서 거울 속 나를 보고 울컥한 순간",
            "웨딩홀 투어 다니며 남친과 취향이 갈렸던 이야기",
            "메이크업 시연 받고 '이게 나 맞나' 싶었던 날",
            "청첩장 문구를 고르다 우리 둘 이름을 나란히 본 기분",
            "본식 스냅이냐 DVD냐를 두고 예산 저울질한 이야기",
            "웨딩촬영 다이어트를 시작했다가 삼일 만에 무너진 날",
        ],
    },
    4: {  # 목요일 — 양가·관계
        "name": "양가와 관계",
        "subs": [
            "상견례 날짜를 잡으며 긴장됐던 마음",
            "예비 시어머니와의 첫 통화 후 든 복잡한 생각",
            "엄마가 '너만 좋으면 됐다'고 했을 때 울컥한 순간",
            "혼수·예단을 두고 양가 온도차가 느껴진 날",
            "남친 가족 모임에 처음 껴서 어색했던 저녁",
            "결혼하면 명절·호칭이 달라진다는 게 실감 난 순간",
        ],
    },
    5: {  # 금요일 — 감정·불안·설렘
        "name": "결혼 앞두고 드는 감정",
        "subs": [
            "'내가 좋은 아내가 될 수 있을까' 싶어 잠 못 든 밤",
            "설렘과 불안이 하루에도 몇 번씩 오가는 마음",
            "혼자 살던 방을 정리하다 괜히 코끝이 시큰했던 날",
            "결혼하면 지금의 자유가 사라질까 봐 드는 두려움",
            "남친의 사소한 배려에 '이 사람이구나' 싶었던 순간",
            "결혼이라는 게 사랑보다 결심에 가깝다는 걸 느낀 날",
        ],
    },
    6: {  # 토요일 — 가벼운 일상 & 소소한 행복
        "name": "결혼준비 속 소소한 일상",
        "subs": [
            "둘이 이케아 가서 신혼 살림 구경하며 웃었던 하루",
            "주말에 신혼집 동네를 미리 걸어본 이야기",
            "청소기·냄비 하나 고르는 데 30분 걸린 우리",
            "결혼 준비하며 처음으로 '우리 집'이라는 말을 써본 순간",
            "지친 하루 끝에 남친이 해준 말 한마디",
            "결혼 준비 체크리스트에 하나 지웠을 때의 뿌듯함",
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
        "위 소재를 바탕으로, 오늘 실제로 겪은 일처럼 빵찌의 일기 한 편을 써줘. "
        "규칙(반말 일기체, 구체적 장면 하나, 150~380자, 한 줄 한 호흡, "
        "열린 마무리, 해시태그 없음, 이모지 0~1개)을 반드시 지켜줘."
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
    parser = argparse.ArgumentParser(description="빵찌 스레드 결혼준비 일기 자동 게시")
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
