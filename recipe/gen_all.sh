#!/usr/bin/env bash
# cards.tsv 전건을 3개씩 병렬로 생성. 이미 있는 카드는 건너뛴다(재실행 안전).
cd "$(dirname "$0")"
N=0
while IFS=$'\t' read -r slug title body; do
  [ -f "cards/$slug.png" ] && continue
  [ -f "images/$slug.png" ] && continue
  ./gen_card.sh "$slug" "$title" "$body" >/dev/null 2>&1 &
  N=$((N+1))
  if [ $((N % 3)) -eq 0 ]; then wait; echo "진행: $(ls cards/*.png 2>/dev/null | wc -l | tr -d ' ')장"; fi
done < cards.tsv
wait
echo "완료: $(ls cards/*.png 2>/dev/null | wc -l | tr -d ' ')장"
