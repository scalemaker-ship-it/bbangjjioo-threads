#!/usr/bin/env python3
"""큐의 상품명들로 실시간 검색 → 진짜 상품 이미지(productImage 긴 URL) + 딥링크를 products.json 에 모은다.

- 쿠파스 규격(prd §7): 이미지는 링크 상품과 반드시 일치. git에 저장된 짧은 ads-partners URL은
  만료돼 '쿠팡 특가' 배너로 폴백되므로 쓰지 말고, 여기서 새로 받은 긴 URL을 쓴다.
- 레이트리밋 대비 재시도/백오프. 이미 채운 상품은 건너뛰어 재실행 시 누락분만 보충(멱등).
출력: products.json = { "상품명": {"img": <productImage>, "link": <deeplink>}, ... }
"""
import json
import re
import time
from urllib.parse import urlparse, parse_qs

from coupang import search_products, deeplink

QUEUE = "queue.json"
OUT = "products.json"


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


def names():
    d = json.load(open(QUEUE, encoding="utf-8"))
    out = []
    for it in d["items"]:
        m = re.search(r"🔽'(.+?)' 정보는", it.get("reply", ""))
        if m:
            out.append(m.group(1))
    return out


def main():
    try:
        prod = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        prod = {}
    todo = [n for n in names() if n not in prod or not prod.get(n, {}).get("img") or not prod.get(n, {}).get("link")]
    print(f"대상 {len(todo)}건 / 이미확보 {len(prod)}건")

    found = {}
    for n in todo:
        for attempt in range(4):
            res = search_products(n, 1)
            if res and res[0].get("image") and res[0].get("url"):
                found[n] = {"img": res[0]["image"], "url": clean_url(res[0]["url"])}
                print("OK", n)
                break
            time.sleep(1.5 * (attempt + 1))
        else:
            print("검색X", n)
        time.sleep(0.8)

    urls = [v["url"] for v in found.values()]
    links = {}
    for i in range(0, len(urls), 20):
        links.update(deeplink(urls[i:i + 20]))
        time.sleep(0.5)

    for n, v in found.items():
        prod[n] = {"img": v["img"], "link": links.get(v["url"], v["url"])}

    json.dump(prod, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"이번 {len(found)}건 확보 → 총 {len(prod)}건 저장")


if __name__ == "__main__":
    main()
