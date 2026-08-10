#!/usr/bin/env python3
"""꿀템100.md 상품들을 쿠팡 검색→링크→글로 만들어 queue.json 에 예약(중복 방지·자동 재시도).

- 이미 큐에 있는 상품(상품명 기준)은 건너뛰고, 아직 안 된 것만 검색 → 쿠팡 레이트리밋 재유발 최소화.
- 목표(TARGET) 이상이면 종료. 2시간 크론이 돌면서 쿠팡이 풀리는 대로 알아서 100+ 채움.
- 본문(1/2): 후킹 로테이션 + 후킹포인트. 이미지 = 쿠팡 대표컷 1장. 댓글(2/2): [광고]+🔽상품명+링크2+공정위.
환경변수: COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY, QUEUE_MD(기본 꿀템100.md)
"""
import json
import os
import re
import time
from urllib.parse import urlparse, parse_qs

from coupang import search_products, deeplink

MD = os.environ.get("QUEUE_MD") or "꿀템100.md"
QUEUE = "queue.json"
TARGET = int(os.environ.get("QUEUE_TARGET", "110"))
DISCLOSURE = "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
OPENERS = [
    "와 이거 진짜 왜 이제 샀지;;", "우리 집 필수템 이걸로 바뀜;;", "이거 없이 어떻게 살았지 싶음;;",
    "하도 추천이라 반신반의로 샀는데 대박;;", "남들이 사길래 따라 샀는데 이해함;;",
    "다들 사라 할 때 콧방귀 뀌었는데 반성 중;;", "이거 보고 바로 결제 눌렀음;;",
    "다이소 갔다가 사람들이 죄다 집길래;;",
]
CLOSERS = [
    "이런 걸 왜 이제 알았지 싶음ㅠㅠ", "은근 없으면 허전해짐ㄷㄷ", "사길 진짜 잘했음ㄷㄷ",
    "요즘 이것만 쓰는 중ㅋㅋ", "당장 사라고 하고 싶음ㅠㅠ",
]


def parse_md(path):
    out = []
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^\s*(\d+)\.\s*(.+?)\s*[—-]{1,2}\s*(.+?)\s*$", line)
        if m:
            out.append((m.group(2).strip(), m.group(3).strip().strip('"')))
    return out


def clean_url(re_url):
    q = parse_qs(urlparse(re_url).query)
    pk = (q.get("pageKey") or [None])[0]
    it = (q.get("itemId") or [None])[0]
    vi = (q.get("vendorItemId") or [None])[0]
    if pk:
        u = f"https://www.coupang.com/vp/products/{pk}"
        if it and vi:
            u += f"?itemId={it}&vendorItemId={vi}"
        return u
    return re_url


def main():
    prods = parse_md(MD)
    try:
        data = json.load(open(QUEUE, encoding="utf-8"))
    except Exception:
        data = {"items": []}
    existing = data.get("items", [])
    queued = set()
    for it in existing:
        m = re.search(r"🔽'(.+?)' 정보는", it.get("reply", ""))
        if m:
            queued.add(m.group(1))
    print(f"현재 큐 {len(existing)}건 / 목표 {TARGET}")
    if len(existing) >= TARGET:
        print("목표 달성 — 종료.")
        return

    todo = [(n, h) for (n, h) in prods if n not in queued]
    print(f"리스트 {len(prods)}개 중 미예약 {len(todo)}개만 검색")
    found, idx0 = [], len(existing)
    for name, hook in todo:
        res = search_products(name, 1)
        time.sleep(0.6)
        if not res or not res[0].get("image") or not res[0].get("url"):
            print(f"  검색X: {name}")
            continue
        r = res[0]
        found.append({"kw": name, "hook": hook, "img": r["image"], "cu": clean_url(r["url"])})
        print(f"  {name} OK")

    links = {}
    urls = [f["cu"] for f in found]
    for j in range(0, len(urls), 20):
        links.update(deeplink(urls[j:j + 20]))
        time.sleep(0.5)

    added = []
    for k, f in enumerate(found):
        link = links.get(f["cu"]) or f["cu"]
        opener = OPENERS[(idx0 + k) % len(OPENERS)]
        closer = CLOSERS[(idx0 + k) % len(CLOSERS)]
        main_text = f"{opener}\n\n{f['hook']}\n\n{closer}"
        reply = (
            f"[광고] '{f['kw']}' 궁금하면ㅠㅠ\n\n"
            f"🔽'{f['kw']}' 정보는 아래에🔽\n{link}\n{link}\n\n{DISCLOSURE}"
        )
        added.append({"main": main_text, "reply": reply, "images": [f["img"]]})

    data["items"] = existing + added
    json.dump(data, open(QUEUE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"이번 {len(added)}건 추가 → 총 {len(data['items'])}건")


if __name__ == "__main__":
    main()
