#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""topics_spec.py + products.json → 카드 프롬프트 / 본문·댓글 / 큐 생성.

카드 프롬프트와 본문을 **같은 스펙에서** 뽑기 때문에 글과 그림이 어긋날 수 없다.
(2026-08-25 교훈: 따로 만들면 codex가 임의 메뉴를 만들어 본문과 불일치)

사용법:
  python build_recipe_queue.py prompts   # cards.tsv 생성(gen_card.sh 입력)
  python build_recipe_queue.py texts     # texts/<slug>.main / .reply 생성
  python build_recipe_queue.py queue     # images/ 에 있는 것만 recipe_queue.json 에 적재
"""
from __future__ import annotations

import json
import os
import sys

from topics_spec import TOPICS as _ALL_TOPICS

DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTS = os.path.join(DIR, "products.json")
QUEUE = os.path.join(DIR, "recipe_queue.json")
RAW = "https://raw.githubusercontent.com/scalemaker-ship-it/bbangjjioo-threads/main/recipe/images"
DISCLOSURE = "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
LIMIT = 500

# 계란이 주제인 카드는 제외한다(2026-08-26, 계란 글이 연달아 나가 사용자 요청).
# 재료로 계란이 들어가는 것은 허용 — 제목/주제가 계란인 것만 뺀다.
EXCLUDE = {"eggs-6ways", "s-eggjangjorim", "s-gyeranmari", "egg-diet-4"}

LAYOUT = {
    "grid2x2": "Four labeled photo cards arranged in a 2x2 grid, each card showing the finished dish with its Korean caption underneath.",
    "grid2x3": "Six labeled photo cards arranged in a 2x3 grid, each card showing the finished dish with its Korean caption underneath.",
    "rank3": "Three cards stacked vertically with large number badges 1, 2, 3, each showing the finished dish photo with its Korean caption and a short Korean one-line comment.",
    # 단일 레시피 상세형 — 레퍼런스(딸기샌드위치·과일샌드위치 인포그래픽) 구조.
    "single": ("One large hero photo of the single finished dish at the top. Below it, an ingredient row with "
               "small cut-out photos of each ingredient labeled in Korean, then the numbered cooking steps in a row, "
               "each step with a small photo and its Korean caption underneath."),
}


TOPICS = [t for t in _ALL_TOPICS if t[0] not in EXCLUDE]


def clean_name(name: str) -> str:
    """상품명을 댓글에 쓸 만하게 다듬는다.

    쿠팡 상품명엔 [로켓프레시]·[즉시출고] 같은 머리표와 ", 2kg, 1개" 옵션 꼬리가 붙어
    그대로 자르면 "…단호박 1kg 2" 처럼 지저분해진다. 머리표·옵션을 떼고 앞부분만 쓴다.
    """
    import re

    n = re.sub(r"\[[^\]]*\]", "", name)          # [로켓프레시] 등 대괄호 태그 제거
    n = n.split(",")[0]                            # ", 2kg, 1개" 옵션 꼬리 제거
    n = re.sub(r"\([^)]*\)", "", n)                # (냉동) 등 괄호 설명 제거
    n = re.sub(r"\s+", " ", n).strip(" -·")
    words = n.split()
    while words and len(" ".join(words)) > 24:     # 너무 길면 뒤에서부터 줄이기
        words.pop()
    return " ".join(words) or name[:24]


def products() -> dict:
    with open(PRODUCTS, encoding="utf-8") as f:
        return json.load(f)


def prompt_for(t) -> str:
    slug, title, layout, items, *_ = t
    names = ", ".join(n for n, _ in items)
    base = LAYOUT[layout]
    # 한글 캡션을 그대로 박아야 카드가 스펙대로 나온다(gen_card.sh 주석 참조).
    if layout == "single":
        return (f"{base} The {len(items)} step captions in Korean are exactly, in this order: {names}. "
                f"The dish is {title}.")
    return f"{base} The {len(items)} captions in Korean are exactly, in this order: {names}."


def texts_for(t, prod) -> tuple[str, str]:
    slug, title, layout, items, hook, tip, ingredients, pkey = t
    lines = [f"{i}. {name} — {how}" for i, (name, how) in enumerate(items, 1)]
    head = f"📌 {title} 만드는 법" if layout == "single" else f"📌 {title}"
    main = f"{hook}\n\n{head}\n" + "\n".join(lines) + f"\n\n{tip}\n재료는 댓글에 적어둘게!"

    p = prod[pkey]
    ing = "\n".join(f"• {x}" for x in ingredients)
    reply = (
        f"[광고] 재료 정리해둘게!\n\n"
        f"📍재료\n{ing}\n\n"
        f"🔽'{clean_name(p['name'])}' 정보는 아래에🔽\n\n"
        f"{DISCLOSURE}\n{p['link']}\n{p['link']}"
    )
    return main, reply


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "prompts"
    prod = products()

    missing = sorted({t[7] for t in TOPICS} - set(prod))
    if missing:
        sys.exit(f"[중단] products.json 에 없는 제품키: {missing}")

    if cmd == "prompts":
        out = os.path.join(DIR, "cards.tsv")
        with open(out, "w", encoding="utf-8") as f:
            for t in TOPICS:
                f.write(f"{t[0]}\t{t[1]}\t{prompt_for(t)}\n")
        print(f"cards.tsv 생성: {len(TOPICS)}건")
        return

    if cmd == "texts":
        d = os.path.join(DIR, "texts")
        os.makedirs(d, exist_ok=True)
        bad = []
        for t in TOPICS:
            m, r = texts_for(t, prod)
            if len(m) > LIMIT or len(r) > LIMIT:
                bad.append((t[0], len(m), len(r)))
            open(os.path.join(d, t[0] + ".main"), "w", encoding="utf-8").write(m)
            open(os.path.join(d, t[0] + ".reply"), "w", encoding="utf-8").write(r)
        print(f"texts/ 생성: {len(TOPICS)}건")
        if bad:
            print("⚠️ 500자 초과 — 손봐야 함:")
            for s, a, b in bad:
                print(f"   {s}: 본문 {a} / 댓글 {b}")
        else:
            print("전부 500자 이내 OK")
        return

    if cmd == "queue":
        items = []
        skipped = []
        for t in TOPICS:
            slug = t[0]
            png = os.path.join(DIR, "images", slug + ".png")
            if not os.path.exists(png):
                skipped.append(slug)
                continue
            m, r = texts_for(t, prod)
            items.append({"slug": slug, "title": t[1], "main": m, "reply": r,
                          "images": [f"{RAW}/{slug}.png"]})
        with open(QUEUE, encoding="utf-8") as f:
            data = json.load(f)
        have = {i.get("slug") for i in data.get("items", [])}
        added = [i for i in items if i["slug"] not in have]
        data["items"] = data.get("items", []) + added
        with open(QUEUE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"큐 적재: +{len(added)}건 → 총 {len(data['items'])}건")
        if skipped:
            print(f"이미지 없어서 건너뜀 {len(skipped)}건: {skipped[:8]}{'…' if len(skipped) > 8 else ''}")
        return

    sys.exit(f"알 수 없는 명령: {cmd}")


if __name__ == "__main__":
    main()
