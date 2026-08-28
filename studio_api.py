#!/usr/bin/env python3
"""쿠파스 스튜디오(coupas-studio.vercel.app) 백엔드 실행기.

Vercel 앱이 GitHub Actions(studio.yml)를 통해 호출한다 — 쿠팡·스레드 키를
Vercel로 옮기지 않고, 시크릿이 있는 이 레포 안에서만 쓰기 위한 프록시.

사용: STUDIO_ACTION / STUDIO_PAYLOAD(JSON) 환경변수를 읽어 result.json을 쓴다.
  action=search   payload={"keyword": "..."}
  action=deeplink payload={"url": "..."}
  action=publish  payload={"main": "...", "reply": "...", "images": [...], "dry_run": bool}
"""
import json
import os
import sys
import time

import requests

from coupang import search_products, deeplink

API = "https://graph.threads.net/v1.0"


def _threads_create(uid, tok, fields):
    r = requests.post(f"{API}/{uid}/threads", json={**fields, "access_token": tok}, timeout=60)
    r.raise_for_status()
    return r.json()["id"]


def _threads_wait(cid, tok, tries=10):
    for _ in range(tries):
        r = requests.get(f"{API}/{cid}", params={"fields": "status,error_message", "access_token": tok}, timeout=30)
        s = r.json()
        if s.get("status") == "FINISHED":
            return
        if s.get("status") == "ERROR":
            raise RuntimeError(f"미디어 처리 실패: {s.get('error_message')}")
        time.sleep(5)


def _threads_publish(uid, tok, cid):
    r = requests.post(f"{API}/{uid}/threads_publish", json={"creation_id": cid, "access_token": tok}, timeout=60)
    r.raise_for_status()
    return r.json()["id"]


def do_publish(p):
    uid = os.environ["THREADS_USER_ID"]
    tok = os.environ["THREADS_ACCESS_TOKEN"]
    main, reply = p.get("main", ""), p.get("reply", "")
    images = [u for u in (p.get("images") or []) if u][:2]
    dry = bool(p.get("dry_run"))
    if not main.strip():
        raise RuntimeError("본문이 비어 있습니다.")

    if len(images) >= 2:
        children = []
        for u in images:
            ch = _threads_create(uid, tok, {"media_type": "IMAGE", "image_url": u, "is_carousel_item": True})
            _threads_wait(ch, tok)
            children.append(ch)
        cid = _threads_create(uid, tok, {"media_type": "CAROUSEL", "children": ",".join(children), "text": main})
    elif len(images) == 1:
        cid = _threads_create(uid, tok, {"media_type": "IMAGE", "image_url": images[0], "text": main})
    else:
        cid = _threads_create(uid, tok, {"media_type": "TEXT", "text": main})
    _threads_wait(cid, tok)

    if dry:  # 컨테이너 생성까지만 검증 — 실제 게시는 하지 않음(공개 글 0개)
        return {"ok": True, "dry_run": True, "container": cid}

    main_id = _threads_publish(uid, tok, cid)
    reply_id = None
    if reply.strip():
        time.sleep(3)
        rc = _threads_create(uid, tok, {"media_type": "TEXT", "text": reply, "reply_to_id": main_id})
        _threads_wait(rc, tok, tries=6)
        reply_id = _threads_publish(uid, tok, rc)
    permalink = None
    try:
        pr = requests.get(f"{API}/{main_id}", params={"fields": "permalink", "access_token": tok}, timeout=30)
        permalink = pr.json().get("permalink")
    except Exception:  # noqa: BLE001
        pass
    return {"ok": True, "mainId": main_id, "replyId": reply_id, "permalink": permalink}


def main():
    action = os.environ.get("STUDIO_ACTION", "")
    payload = json.loads(os.environ.get("STUDIO_PAYLOAD") or "{}")
    try:
        if action == "search":
            result = {"ok": True, "products": search_products(payload.get("keyword", ""), limit=8)}
        elif action == "deeplink":
            links = deeplink([payload.get("url", "")])
            short = next(iter(links.values()), None)
            if not short:
                raise RuntimeError("딥링크 발급 실패 — 쿠팡 URL을 확인하세요.")
            result = {"ok": True, "link": short}
        elif action == "publish":
            result = do_publish(payload)
        else:
            raise RuntimeError(f"알 수 없는 action: {action}")
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": str(exc)}
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    print(json.dumps(result, ensure_ascii=False)[:500])
    if not result.get("ok"):
        sys.exit(0)  # 실패도 결과로 전달 — 워크플로 자체는 성공 처리해 아티팩트를 남긴다


if __name__ == "__main__":
    main()
