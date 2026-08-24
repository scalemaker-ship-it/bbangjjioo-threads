#!/usr/bin/env bash
# 레시피 1:1 인포그래픽 카드 생성 (codex-image 래퍼)
#
# 사용법:
#   ./gen_card.sh <slug> "<제목(한글)>" "<레이아웃 지시문(영문)>"
#
# 예:
#   ./gen_card.sh egg-sandwich-6 "계란샌드위치 6가지" \
#     "Six labeled photo cards of different Korean egg sandwiches in a 2x3 grid, each with a short Korean caption underneath."
#
# 산출물: ./cards/<slug>.png  (검수 통과하면 images/ 로 옮겨 커밋)
set -euo pipefail

SLUG="${1:?slug 필요}"
TITLE="${2:?제목 필요}"
BODY="${3:?레이아웃 지시문 필요}"

DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$DIR/cards"
OUT="$DIR/cards/${SLUG}.png"

# prd-레시피.md §4 고정 스타일 블록 — 바꾸려면 PRD를 먼저 고칠 것.
STYLE="Warm cream paper background, clean editorial magazine layout, generous whitespace, \
handwritten Korean pen-style annotations with hand-drawn arrows, soft natural food photography, \
high legibility, no watermark, no logo."

PROMPT="Korean recipe infographic poster, square 1:1. Title in large Korean Hangul reading '${TITLE}'. ${BODY} ${STYLE}"

echo "[gen_card] slug=$SLUG"
echo "[gen_card] out=$OUT"

~/.claude/skills/codex-image/scripts/gen.sh \
  --prompt "$PROMPT" \
  --out "$OUT" \
  --orientation square --width 1080 --height 1080 </dev/null

[ -f "$OUT" ] || { echo "[gen_card] 실패: PNG 미생성"; exit 1; }
echo "[gen_card] 완료 → $OUT"
echo "[gen_card] 검수 후: mv cards/${SLUG}.png images/${SLUG}.png && git add -f images/${SLUG}.png"
