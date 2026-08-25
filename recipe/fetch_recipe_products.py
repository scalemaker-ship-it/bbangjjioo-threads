#!/usr/bin/env python3
"""레시피 트랙 대표재료 카탈로그 생성 — 검색 → 최적 상품 선정 → 딥링크 → products.json

GitHub Actions에서 돌린다(쿠팡 키가 시크릿에만 있음).
입력: keywords.txt  (한 줄에 "키" TAB "검색어")
출력: recipe/products.json  {"키": {"name","price","url","link","rocket"}}

선정 규칙(prd-레시피.md §2 "대표 재료" 기준):
- 가격 3,000~20,000원 (충동구매 구간). 대용량 업소용은 전환이 안 나오니 제외.
- 로켓배송 우선.
- 위 조건에 맞는 게 없으면 가격이 가장 낮은 것으로 폴백.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from coupang import deeplink, search_products  # noqa: E402

DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(DIR, "products.json")
LO, HI = 3000, 20000


def pick(items: list[dict]) -> dict | None:
    if not items:
        return None
    def price(p):
        try:
            return int(p.get("price") or 0)
        except (TypeError, ValueError):
            return 0
    ok = [p for p in items if LO <= price(p) <= HI]
    if ok:
        rocket = [p for p in ok if p.get("rocket")]
        pool = rocket or ok
        return min(pool, key=price)
    return min(items, key=price)


def main() -> None:
    path = os.path.join(DIR, "keywords.txt")
    pairs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            key, _, kw = line.partition("\t")
            pairs.append((key.strip(), kw.strip()))

    existing = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            existing = json.load(f)

    catalog = dict(existing)
    todo = [(k, kw) for k, kw in pairs if k not in catalog]
    print(f"총 {len(pairs)}개 중 {len(todo)}개 신규 수집 (기존 {len(catalog)}개 유지)")

    chosen = {}
    for key, kw in todo:
        items = search_products(kw, 10)
        best = pick(items)
        if not best:
            print(f"  [건너뜀] {key} ({kw}) — 검색 결과 없음")
            continue
        chosen[key] = best
        print(f"  {key}: {best['name'][:45]} / {best['price']}원 {'로켓' if best.get('rocket') else ''}")

    # 딥링크는 한 번에 일괄 변환(호출 수 절약)
    urls = [b["url"] for b in chosen.values()]
    mapping = deeplink(urls) if urls else {}
    for key, best in chosen.items():
        link = mapping.get(best["url"])
        if not link:
            print(f"  [경고] {key} 딥링크 실패 — 카탈로그에 안 넣음")
            continue
        catalog[key] = {
            "name": best["name"],
            "price": best["price"],
            "url": best["url"],
            "link": link,
            "rocket": bool(best.get("rocket")),
        }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"\nproducts.json 저장: {len(catalog)}개 (이번에 추가 {len(catalog) - len(existing)}개)")
    missing = [k for k, _ in pairs if k not in catalog]
    if missing:
        print(f"⚠️ 아직 없는 키: {missing}")


if __name__ == "__main__":
    main()
