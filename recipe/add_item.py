#!/usr/bin/env python3
"""레시피 큐(recipe_queue.json)에 항목 1건을 규격 검증하며 추가한다.

규격 단일 출처: recipe/prd-레시피.md §3

사용법:
  python add_item.py --slug egg-sandwich-6 \
      --title "계란샌드위치 6가지" \
      --main-file main.txt --reply-file reply.txt \
      --link "https://link.coupang.com/a/XXXX"

  이미지 URL은 --image 로 직접 주거나, 생략하면 slug로 raw URL을 자동 조립한다.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(DIR, "recipe_queue.json")
RAW_BASE = "https://raw.githubusercontent.com/scalemaker-ship-it/bbangjjioo-threads/main/recipe/images"
DISCLOSURE = "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
LIMIT = 500

# prd §6 — 효능 단정 금지어. 걸리면 추가를 막고 순화하도록 알린다.
BANNED = ["살 빠진다", "살이 빠진다", "완치", "100%", "낫는다", "치료된다", "붓기가 빠진다", "효과 확실"]


def check_text(label: str, text: str, errors: list[str]) -> None:
    n = len(text)
    if n == 0:
        errors.append(f"{label}: 비어 있음")
    if n > LIMIT:
        errors.append(f"{label}: {n}자 — 스레드 500자 초과 ({n - LIMIT}자 줄여야 함)")
    for w in BANNED:
        if w in text:
            errors.append(f"{label}: 효능 단정 표현 '{w}' 포함 (prd §6) — 체감·전언 톤으로 순화 필요")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--main-file", required=True)
    ap.add_argument("--reply-file", required=True)
    ap.add_argument("--image", help="이미지 URL (생략 시 slug로 raw URL 자동 조립)")
    ap.add_argument("--link", help="쿠팡 /a/ 딥링크 — reply 안에 2번 들어있는지 검증")
    args = ap.parse_args()

    main_text = open(args.main_file, encoding="utf-8").read().strip()
    reply_text = open(args.reply_file, encoding="utf-8").read().strip()
    image = args.image or f"{RAW_BASE}/{args.slug}.png"

    errors: list[str] = []
    check_text("본문(1/2)", main_text, errors)
    check_text("댓글(2/2)", reply_text, errors)

    if not reply_text.startswith("[광고]"):
        errors.append("댓글(2/2): 첫 줄이 '[광고]' 로 시작해야 함 (prd §6)")
    if DISCLOSURE not in reply_text:
        errors.append("댓글(2/2): 공정위 대가성 표준 문구 누락 (prd §6)")
    if args.link:
        n_link = reply_text.count(args.link)
        if n_link != 2:
            errors.append(f"댓글(2/2): 쿠팡 링크가 2번 들어가야 함 (현재 {n_link}번)")
        # 링크 위치·순서는 썸네일과 무관하다(2026-08-25 실측: 18/18 전부 카드 붙음).
        # 진짜 조건은 '링크가 살아 있어서 스레드가 미리보기를 만들 수 있는가' → 발행 후
        # publish_recipe.py 가 link_attachment_url 로 검증한다.
        if not args.link.startswith("https://link.coupang.com/a/"):
            errors.append(f"댓글(2/2): 쿠팡 딥링크(/a/ 짧은 링크)가 아님: {args.link}")

    # 이미지가 로컬 images/ 에 실제로 있는지 (커밋 전 누락 방지)
    local_png = os.path.join(DIR, "images", f"{args.slug}.png")
    if args.image is None and not os.path.exists(local_png):
        errors.append(f"이미지 없음: {local_png} — 검수 통과분을 images/ 로 옮기고 커밋해야 raw URL이 산다")

    if errors:
        print("=== 규격 위반 — 큐에 추가하지 않음 ===")
        for e in errors:
            print(" ✗", e)
        sys.exit(1)

    with open(QUEUE, encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("items", []).append({
        "slug": args.slug,
        "title": args.title,
        "main": main_text,
        "reply": reply_text,
        "images": [image],
    })
    with open(QUEUE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✓ 큐에 추가: {args.title}")
    print(f"  본문 {len(main_text)}자 / 댓글 {len(reply_text)}자 / 이미지 {image}")
    print(f"  대기 중: {len(data['items'])}건")


if __name__ == "__main__":
    main()
