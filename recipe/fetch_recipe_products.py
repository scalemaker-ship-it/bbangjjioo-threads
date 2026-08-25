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


def clean_url(url: str) -> str:
    """검색 API가 주는 추적 URL을 딥링크가 받아주는 **깨끗한 상품 URL**로 바꾼다.

    ⚠️ search 결과의 productUrl 은 이미 어필리에이트 추적 링크
    (link.coupang.com/re/AFFSDP?...pageKey=..&itemId=..&vendorItemId=..) 이고,
    이걸 그대로 deeplink API 에 넣으면 **전부 실패한다**(2026-08-25 실측 50/50 실패).
    pageKey/itemId/vendorItemId 를 뽑아 www.coupang.com/vp/products/... 형태로 재조립한다.
    """
    from urllib.parse import parse_qs, urlparse

    if "/vp/products/" in url:
        return url
    q = parse_qs(urlparse(url).query)
    page = (q.get("pageKey") or [""])[0]
    if not page:
        return url
    item = (q.get("itemId") or [""])[0]
    vendor = (q.get("vendorItemId") or [""])[0]
    out = f"https://www.coupang.com/vp/products/{page}"
    params = []
    if item:
        params.append(f"itemId={item}")
    if vendor:
        params.append(f"vendorItemId={vendor}")
    return out + ("?" + "&".join(params) if params else "")


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

    # 딥링크는 10개씩 끊어서 변환한다.
    # ⚠️ 50개를 한 번에 보내면 API가 통째로 실패한다(2026-08-25 실측: 50/50 실패).
    import time as _time

    for b in chosen.values():
        b["url"] = clean_url(b["url"])
    urls = [b["url"] for b in chosen.values()]
    mapping = {}
    CHUNK = 10
    for i in range(0, len(urls), CHUNK):
        batch = urls[i:i + CHUNK]
        got = deeplink(batch)
        if not got:  # 레이트리밋일 수 있으니 한 번 쉬고 재시도
            _time.sleep(5)
            got = deeplink(batch)
        if not got:  # 그래도 안 되면 1개씩
            for u in batch:
                got.update(deeplink([u]))
                _time.sleep(1)
        mapping.update(got)
        print(f"  딥링크 {i + len(batch)}/{len(urls)} — 누적 성공 {len(mapping)}")
        _time.sleep(2)
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
