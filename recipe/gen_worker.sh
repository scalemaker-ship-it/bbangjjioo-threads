#!/usr/bin/env bash
# cards.tsv 를 지정 순서로 훑으며 아직 없는 카드만 생성. 여러 개 동시에 띄워도 안전(존재 체크로 스킵).
#   $1 = fwd | rev | mid   (훑는 순서)
#   $2 = 동시 실행 수 (기본 3)
cd "$(dirname "$0")"
ORDER="${1:-fwd}"; PAR="${2:-3}"
case "$ORDER" in
  rev) LIST=$(tac cards.tsv 2>/dev/null || tail -r cards.tsv) ;;
  mid) LIST=$(awk 'NR>30 && NR<=60' cards.tsv) ;;
  *)   LIST=$(cat cards.tsv) ;;
esac
N=0
while IFS=$'\t' read -r slug title body; do
  [ -z "$slug" ] && continue
  [ -f "cards/$slug.png" ] && continue
  [ -f "images/$slug.png" ] && continue
  ./gen_card.sh "$slug" "$title" "$body" >/dev/null 2>&1 &
  N=$((N+1))
  [ $((N % PAR)) -eq 0 ] && wait
done <<< "$LIST"
wait
echo "[$ORDER] 종료"
