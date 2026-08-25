#!/usr/bin/env python3
"""큐에 든 쿠팡 딥링크가 살아 있는지(=썸네일 카드가 뜰 수 있는지) 사전 점검한다.

썸네일 카드가 안 뜨면 클릭이 안 나고 수수료를 못 받는다. 카드가 사라지는 원인은
링크 순서가 아니라 **딥링크가 죽었을 때**다(prd-레시피.md §3).
→ 발행 전에 여기서 걸러내고, 발행 후에는 publish_recipe.py 가 실제 부착을 재확인한다.

사용법:
  python check_links.py              # recipe_queue.json 전체 점검
  python check_links.py <URL> ...    # 지정한 링크만 점검
종료코드: 죽은 링크가 하나라도 있으면 1
"""
from __future__ import annotations

import json
import os
import sys

import requests

DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(DIR, "recipe_queue.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"


def check(url: str) -> tuple[bool, str]:
    """딥링크가 쿠팡 **상품 페이지**로 이어지는지 확인.

    쿠팡 본문은 봇 요청을 403으로 막으므로 본문을 받아보면 안 된다.
    대신 리다이렉트를 따라가지 말고 **Location 헤더**만 본다(2026-08-25 실측):
      살아있는 링크 → 302, Location = .../vp/products/<id>...
      죽은 링크     → 302, Location = https://www.coupang.com/   (홈으로 튕김)
    """
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=20, allow_redirects=False)
    except Exception as exc:  # noqa: BLE001
        return False, f"요청 실패: {exc}"
    loc = r.headers.get("Location", "")
    if r.status_code not in (301, 302, 303, 307, 308):
        return False, f"리다이렉트 아님 (HTTP {r.status_code})"
    if "/vp/products/" not in loc:
        return False, f"상품 페이지로 안 감(죽은 링크) → {loc[:80] or '(Location 없음)'}"
    return True, loc.split("?")[0]


def main() -> None:
    if len(sys.argv) > 1:
        targets = [(a, f"인자{i+1}") for i, a in enumerate(sys.argv[1:])]
    else:
        with open(QUEUE, encoding="utf-8") as f:
            items = json.load(f).get("items", [])
        targets = []
        seen = set()
        for it in items:
            for line in it.get("reply", "").splitlines():
                line = line.strip()
                if line.startswith("https://link.coupang.com/") and line not in seen:
                    seen.add(line)
                    targets.append((line, it.get("title", it.get("slug", ""))))

    if not targets:
        print("점검할 링크 없음.")
        return

    dead = 0
    for url, label in targets:
        ok, info = check(url)
        mark = "O" if ok else "X"
        print(f"[{mark}] {label}\n    {url}\n    {info}")
        if not ok:
            dead += 1

    print("-" * 60)
    print(f"총 {len(targets)}개 중 정상 {len(targets) - dead} / 불량 {dead}")
    if dead:
        sys.exit(f"[실패] 죽은 링크 {dead}개 — 썸네일이 안 뜬다. 딥링크 재발급 필요.")


if __name__ == "__main__":
    main()
