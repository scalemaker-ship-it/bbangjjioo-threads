#!/usr/bin/env python3
"""쿠팡 파트너스 Open API — Deeplink(링크 변환) + Product Search(상품 검색).

환경변수(GitHub Secrets):
  COUPANG_ACCESS_KEY   파트너스 API Access Key
  COUPANG_SECRET_KEY   파트너스 API Secret Key

키가 없으면 빈 결과를 돌려주고 예외는 던지지 않는다(발행이 막히지 않도록).

CLI:
  python coupang.py search "틈새 수납 카트|실리콘 밀폐 뚜껑"   # '|'로 여러 키워드
  python coupang.py deeplink "URL1|URL2|URL3"   # '|'로 여러 개
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import quote

_DOMAIN = "https://api-gateway.coupang.com"
_DEEPLINK_PATH = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
_SEARCH_PATH = "/v2/providers/affiliate_open_api/apis/openapi/products/search"


def _authorization(method: str, path: str, query: str, access: str, secret: str) -> str:
    """쿠팡 CEA(HmacSHA256) 서명 헤더. query는 '?' 없는 쿼리스트링(없으면 '')."""
    signed_date = datetime.now(timezone.utc).strftime("%y%m%dT%H%M%SZ")  # GMT
    message = signed_date + method + path + query
    signature = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return (
        f"CEA algorithm=HmacSHA256, access-key={access}, "
        f"signed-date={signed_date}, signature={signature}"
    )


def _keys() -> tuple[str, str] | None:
    access = os.environ.get("COUPANG_ACCESS_KEY")
    secret = os.environ.get("COUPANG_SECRET_KEY")
    if not access or not secret:
        print("[쿠팡] API 키(COUPANG_ACCESS_KEY/SECRET_KEY) 없음.")
        return None
    return access, secret


def deeplink(urls: list[str]) -> dict[str, str]:
    """상품 URL 리스트 → {원본URL: 단축 어필리에이트 링크}. 실패 시 빈 dict."""
    keys = _keys()
    if not keys or not urls:
        return {}
    access, secret = keys
    import requests

    auth = _authorization("POST", _DEEPLINK_PATH, "", access, secret)
    try:
        resp = requests.post(
            _DOMAIN + _DEEPLINK_PATH,
            headers={"Authorization": auth, "Content-Type": "application/json"},
            data=json.dumps({"coupangUrls": urls}),
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()
    except Exception as exc:  # noqa: BLE001
        print(f"[쿠팡] Deeplink 실패 → 링크 생략: {exc}")
        return {}
    out: dict[str, str] = {}
    for item in body.get("data", []) or []:
        original = item.get("originalUrl")
        short = item.get("shortenUrl") or item.get("landingUrl")
        if original and short:
            out[original] = short
    return out


def search_products(keyword: str, limit: int = 5) -> list[dict]:
    """키워드로 상품 검색 → [{name, price, image, url, rocket, category}]. 실패 시 []."""
    keys = _keys()
    if not keys:
        return []
    access, secret = keys
    import requests

    query = f"keyword={quote(keyword)}&limit={limit}"
    auth = _authorization("GET", _SEARCH_PATH, query, access, secret)
    try:
        resp = requests.get(
            f"{_DOMAIN}{_SEARCH_PATH}?{query}",
            headers={"Authorization": auth, "Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()
    except Exception as exc:  # noqa: BLE001
        print(f"[쿠팡] 검색 실패({keyword}): {exc}")
        return []

    data = body.get("data") or {}
    products = data.get("productData") or []
    out = []
    for p in products:
        out.append({
            "name": p.get("productName"),
            "price": p.get("productPrice"),
            "image": p.get("productImage"),
            "url": p.get("productUrl"),
            "rocket": p.get("isRocket"),
            "category": p.get("categoryName"),
        })
    return out


def _cli() -> None:
    if len(sys.argv) < 3:
        print("사용법: python coupang.py search \"kw1|kw2\"  |  python coupang.py deeplink \"URL\"")
        return
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "search":
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        for kw in [k.strip() for k in arg.split("|") if k.strip()]:
            print(f"\n===== 키워드: {kw} =====")
            items = search_products(kw, limit)
            if not items:
                print("  (결과 없음)")
            for i, p in enumerate(items, 1):
                rk = "로켓" if p["rocket"] else "일반"
                print(f"  {i}. [{rk}] {p['name']} / {p['price']}원")
                print(f"     URL: {p['url']}")
                print(f"     IMG: {p['image']}")
    elif cmd == "deeplink":
        # '|' 로 여러 URL 을 한 번에 변환한다(대량 예약 시 dispatch 횟수를 줄이려고).
        urls = [u.strip() for u in arg.split("|") if u.strip()]
        mapping = deeplink(urls)
        for u in urls:
            print(f"MAP\t{u}\t{mapping.get(u, '(실패)')}")
        print(f"총 {len(urls)}개 중 {len(mapping)}개 변환")
    else:
        print(f"알 수 없는 명령: {cmd}")


if __name__ == "__main__":
    _cli()
