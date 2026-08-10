#!/usr/bin/env python3
"""쿠파스 광고글 1건 무인 게시 — 이미지 본문(1/2) + 텍스트 답글(2/2).

읽는 파일:
  coupas_image.txt  본문에 넣을 공개 이미지 URL(한 줄)
  coupas_main.txt   본문(1/2) 텍스트
  coupas_reply.txt  댓글(2/2) 텍스트

환경변수(GitHub Secrets):
  THREADS_USER_ID, THREADS_ACCESS_TOKEN
"""
import os
import sys
import time

import requests

API = "https://graph.threads.net/v1.0"


def require(name):
    v = os.environ.get(name)
    if not v:
        sys.exit(f"[오류] 환경변수 {name} 없음")
    return v


def readfile(path):
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def create(uid, tok, fields):
    r = requests.post(f"{API}/{uid}/threads", json={**fields, "access_token": tok}, timeout=60)
    if not r.ok:
        print("[create 실패]", r.status_code, r.text[:500])
        r.raise_for_status()
    return r.json()["id"]


def wait_ready(cid, tok, tries=12):
    """컨테이너 처리 상태를 폴링. FINISHED면 True, ERROR면 False."""
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
    print("[경고] 상태 확인 타임아웃 — 그래도 발행 시도")
    return True


def publish(uid, tok, cid):
    r = requests.post(f"{API}/{uid}/threads_publish", json={"creation_id": cid, "access_token": tok}, timeout=60)
    if not r.ok:
        print("[publish 실패]", r.status_code, r.text[:500])
        r.raise_for_status()
    return r.json()["id"]


def main():
    uid = require("THREADS_USER_ID")
    tok = require("THREADS_ACCESS_TOKEN")
    image_url = readfile("coupas_image.txt")
    main_text = readfile("coupas_main.txt")
    reply_text = readfile("coupas_reply.txt")

    print("=== 본문(1/2) 이미지 컨테이너 생성 ===")
    cid = create(uid, tok, {"media_type": "IMAGE", "image_url": image_url, "text": main_text})
    print("컨테이너:", cid)
    if not wait_ready(cid, tok):
        sys.exit("[중단] 이미지 처리 실패 — 게시 안 함")
    main_id = publish(uid, tok, cid)
    print("본문 게시 완료:", main_id)

    if reply_text:
        print("=== 댓글(2/2) 답글 생성 ===")
        time.sleep(3)
        rcid = create(uid, tok, {"media_type": "TEXT", "text": reply_text, "reply_to_id": main_id})
        wait_ready(rcid, tok, tries=6)
        rid = publish(uid, tok, rcid)
        print("댓글 게시 완료:", rid)

    print("게시 완료. 메인 게시물 ID:", main_id)


if __name__ == "__main__":
    main()
