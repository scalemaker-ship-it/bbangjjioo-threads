#!/usr/bin/env python3
"""레시피 큐에서 맨 앞 1건을 게시하고 큐에서 제거한다 (하루 1회 크론용).

기존 쿠파스 트랙(queue.json / publish_from_queue.py)과 완전히 분리된 별도 큐다.
규격 단일 출처: recipe/prd-레시피.md

recipe_queue.json 형식:
  {"items": [{"slug": "...", "title": "...", "main": "...", "reply": "...",
              "images": ["https://raw.githubusercontent.com/.../recipe/images/x.png"]}, ...]}

- 본문(1/2) = 1:1 인포그래픽 이미지 1장 + main 텍스트
- 댓글(2/2) = reply 텍스트 (사진 없음)
환경변수: THREADS_USER_ID, THREADS_ACCESS_TOKEN
"""
import json
import os
import sys
import time

import requests

API = "https://graph.threads.net/v1.0"
QUEUE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recipe_queue.json")


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


def verify_thumbnail(post_id, tok, tries=6):
    """댓글에 쿠팡 링크 미리보기 썸네일 카드가 실제로 붙었는지 확인한다.

    썸네일 카드가 안 뜨면 클릭이 안 나고 수수료를 못 받는다 → 발행할 때마다 반드시 확인.
    (링크의 위치·순서는 무관함이 실측됨(2026-08-25, 18/18 카드 정상). 진짜 조건은
     링크가 살아 있어 스레드가 미리보기를 뽑아낼 수 있는가다.)
    카드 생성은 몇 초 늦을 수 있어 재시도한다.
    """
    for i in range(tries):
        r = requests.get(
            f"{API}/{post_id}",
            params={"fields": "link_attachment_url,permalink", "access_token": tok},
            timeout=30,
        )
        d = r.json()
        att = d.get("link_attachment_url")
        if att:
            print(f"✅ 썸네일 카드 확인: {att}")
            return True
        print(f"  썸네일 대기[{i}]…")
        time.sleep(5)
    print("=" * 60)
    print("⚠️ 경고: 댓글에 링크 썸네일 카드가 안 붙었다.")
    print("   → 클릭이 안 나서 수수료를 못 받는다. 딥링크가 죽었는지 확인하고,")
    print("     필요하면 링크를 다시 발급해 앱에서 댓글을 수정할 것.")
    print("=" * 60)
    return False


def main():
    uid = require("THREADS_USER_ID")
    tok = require("THREADS_ACCESS_TOKEN")

    with open(QUEUE, encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items", [])
    if not items:
        print("[큐 비어있음] 게시할 항목 없음. 종료(정상).")
        return

    # 이미지 1장 + 공정위 문구를 갖춘 맨 앞 항목을 찾는다. 미달분은 큐에 남기고 건너뛴다.
    def ready(it):
        return len(it.get("images", [])) >= 1 and "쿠팡 파트너스 활동의 일환" in it.get("reply", "")

    idx = next((i for i, it in enumerate(items) if ready(it)), None)
    if idx is None:
        sys.exit("[중단] 이미지·공정위 문구를 갖춘 항목이 없음.")
    if idx != 0:
        print(f"[건너뜀] 앞 {idx}건은 규격 미달 → 큐에 남기고 다음 항목 게시")

    item = items[idx]
    img = item["images"][0]
    print(f"=== 레시피 큐 {len(items)}건 중 1건 게시: {item.get('title', item.get('slug', ''))} ===")
    print(f"    이미지: {img}")

    # 이미지 1장이므로 캐러셀이 아니라 단일 IMAGE 게시물
    cid = create(uid, tok, {"media_type": "IMAGE", "image_url": img, "text": item["main"]})
    if not wait_ready(cid, tok):
        sys.exit("[중단] 본문 컨테이너 처리 실패")
    main_id = publish(uid, tok, cid)
    print("본문 게시 완료:", main_id)

    thumbnail_ok = True
    reply_text = item.get("reply", "")
    if reply_text:
        time.sleep(3)
        rcid = create(uid, tok, {"media_type": "TEXT", "text": reply_text, "reply_to_id": main_id})
        wait_ready(rcid, tok, tries=6)
        rid = publish(uid, tok, rcid)
        print("댓글 게시 완료:", rid)
        # 썸네일 카드는 수수료의 전제조건 — 붙었는지 반드시 확인한다.
        time.sleep(5)
        if not verify_thumbnail(rid, tok):
            thumbnail_ok = False

    data["items"] = items[:idx] + items[idx + 1:]
    with open(QUEUE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"게시 완료. 남은 큐: {len(data['items'])}건. 메인 ID: {main_id}")
    if not thumbnail_ok:
        sys.exit("[실패] 게시는 됐지만 썸네일 카드가 안 붙었다 — 링크 점검 필요(위 경고 참조).")


if __name__ == "__main__":
    main()
