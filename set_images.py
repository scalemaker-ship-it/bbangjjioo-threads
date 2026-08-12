#!/usr/bin/env python3
"""큐 항목에 AI 사용컷 2장 URL을 주입한다(무인 발행용).

쿠파스 규격(prd §2): 본문 사진 = 상세페이지 사용컷 2장(썸네일 1장짜리 지양).
무인 발행 크론(GitHub Actions)에는 힉스필드 MCP가 없으므로, 이미지 생성은
세션에서 미리 하고 **공개 URL을 queue.json 에 구워넣는다**. 이 스크립트가 그 주입기.

사용법:
  python set_images.py <index> <url1> <url2>
  python set_images.py --status          # 각 항목 이미지 장수 요약
"""
import json
import re
import sys

QUEUE = "queue.json"


def load():
    with open(QUEUE, encoding="utf-8") as f:
        return json.load(f)


def save(d):
    with open(QUEUE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def name_of(item):
    m = re.search(r"🔽'(.+?)' 정보는", item.get("reply", ""))
    return m.group(1) if m else "(?)"


def status():
    d = load()
    its = d.get("items", [])
    one = sum(1 for it in its if len(it.get("images", [])) < 2)
    print(f"총 {len(its)}건 · 사용컷 2장 미달 {one}건")
    for i, it in enumerate(its):
        n = len(it.get("images", []))
        flag = "OK " if n >= 2 else "!! "
        print(f"  {flag}[{i}] imgs={n} | {name_of(it)}")


def batch_write(path):
    """{ "3": ["u1","u2"], ... } JSON 파일로 여러 항목 한 번에 주입."""
    d = load()
    its = d["items"]
    pairs = json.load(open(path, encoding="utf-8"))
    n = 0
    for k, urls in pairs.items():
        i = int(k)
        if 0 <= i < len(its) and len(urls) == 2:
            its[i]["images"] = urls
            its[i].pop("needs_ai_images", None)
            n += 1
    save(d)
    print(f"[OK] {n}건 사용컷 2장 주입")


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--status":
        status()
        return
    if len(sys.argv) == 3 and sys.argv[1] == "--batch":
        batch_write(sys.argv[2])
        return
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    idx = int(sys.argv[1])
    url1, url2 = sys.argv[2], sys.argv[3]
    d = load()
    its = d["items"]
    if not (0 <= idx < len(its)):
        sys.exit(f"[오류] index {idx} 범위 밖(0~{len(its)-1})")
    its[idx]["images"] = [url1, url2]
    its[idx].pop("needs_ai_images", None)
    save(d)
    print(f"[OK] item[{idx}] '{name_of(its[idx])}' ← 사용컷 2장 주입")


if __name__ == "__main__":
    main()
