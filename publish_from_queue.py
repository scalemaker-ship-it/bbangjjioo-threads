#!/usr/bin/env python3
"""쿠파스 큐에서 맨 앞 1건을 게시하고 큐에서 제거한다(하루 3회 크론용).

queue.json 형식:
  {"items": [ {"main": "...", "reply": "...", "images": ["url1","url2"]}, ... ]}

- 본문 = 이미지 캐러셀(images) + main 텍스트
- 댓글 = reply 텍스트(사진 없음)
- 게시 성공 시 items[0]을 제거하고 queue.json 저장(워크플로가 커밋).
환경변수: THREADS_USER_ID, THREADS_ACCESS_TOKEN
"""
import json
import os
import sys
import time

import requests

API = "https://graph.threads.net/v1.0"
QUEUE = "queue.json"


def require(name):
    v = os.environ.get(name)
    if not v:
        sys.exit(f"[오류] 환경변수 {name} 없음")
    return v


def create(uid, tok, fields):
    r = requests.post(f"{API}/{uid}/threads", json={**fields, "access_token": tok}, timeout=60)
    if not r.ok:
        print("[create 실패]", r.status_code, r.text[:400])
        r.raise_for_status()
    return r.json()["id"]


def wait_ready(cid, tok, tries=12):
    for i in range(tries):
        r = requests.get(f"{API}/{cid}", params={"fields": "status,error_message", "access_token": tok}, timeout=30)
        s = r.json()
        st = s.get("status")
        print(f"  상태[{i}]: {st} {s.get('error_message', '')}")
        if st == "FINISHED":
            return True
        if st == "ERROR":
            print("[컨테이너 ERROR]", s)
            return False
        time.sleep(6)
    return True


def publish(uid, tok, cid):
    r = requests.post(f"{API}/{uid}/threads_publish", json={"creation_id": cid, "access_token": tok}, timeout=60)
    if not r.ok:
        print("[publish 실패]", r.status_code, r.text[:400])
        r.raise_for_status()
    return r.json()["id"]


def main():
    uid = require("THREADS_USER_ID")
    tok = require("THREADS_ACCESS_TOKEN")

    with open(QUEUE, encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items", [])
    if not items:
        print("[큐 비어있음] 게시할 항목 없음. 종료(정상).")
        return

    item = items[0]
    images = item.get("images", [])
    main_text = item["main"]
    reply_text = item.get("reply", "")
    print(f"=== 큐 {len(items)}건 중 1건 게시 (이미지 {len(images)}장) ===")

    if len(images) == 1:
        cid = create(uid, tok, {"media_type": "IMAGE", "image_url": images[0], "text": main_text})
        if not wait_ready(cid, tok):
            sys.exit("[중단] 이미지 처리 실패")
        main_id = publish(uid, tok, cid)
    else:
        children = []
        for i, u in enumerate(images, 1):
            ch = create(uid, tok, {"media_type": "IMAGE", "image_url": u, "is_carousel_item": True})
            print(f"  이미지{i} 컨테이너: {ch}")
            if not wait_ready(ch, tok):
                sys.exit(f"[중단] 이미지{i} 처리 실패")
            children.append(ch)
        car = create(uid, tok, {"media_type": "CAROUSEL", "children": ",".join(children), "text": main_text})
        if not wait_ready(car, tok):
            sys.exit("[중단] 캐러셀 처리 실패")
        main_id = publish(uid, tok, car)
    print("본문 게시 완료:", main_id)

    if reply_text:
        time.sleep(3)
        rcid = create(uid, tok, {"media_type": "TEXT", "text": reply_text, "reply_to_id": main_id})
        wait_ready(rcid, tok, tries=6)
        rid = publish(uid, tok, rcid)
        print("댓글 게시 완료:", rid)

    # 성공 → 큐에서 제거
    data["items"] = items[1:]
    with open(QUEUE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"게시 완료. 남은 큐: {len(data['items'])}건. 메인 ID: {main_id}")


if __name__ == "__main__":
    main()
