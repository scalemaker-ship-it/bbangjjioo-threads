#!/usr/bin/env bash
# 남은 카드만 2개씩 순차 생성. 워커가 조용히 죽는 문제 대비로 결과를 매번 로그에 남긴다.
cd "$(dirname "$0")"
while IFS=$'\t' read -r slug title body; do
  [ -z "$slug" ] && continue
  [ -f "cards/$slug.png" ] && continue
  [ -f "images/$slug.png" ] && continue
  ./gen_card.sh "$slug" "$title" "$body" >/dev/null 2>&1 </dev/null \
    && echo "OK  $slug" || echo "FAIL $slug"
done < cards.tsv
echo "== 종료: $(ls cards/*.png 2>/dev/null | wc -l | tr -d ' ')장 =="
