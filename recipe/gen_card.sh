#!/usr/bin/env bash
# 레시피 1:1 인포그래픽 카드 생성 (codex-image 래퍼)
#
# 사용법:
#   ./gen_card.sh <slug> "<제목(한글)>" "<레이아웃 지시문(영문)>"
#
# ⚠️ 레이아웃 지시문에는 **각 항목의 한글 이름을 그대로 나열**한다.
#    그래야 카드가 정해진 구성대로 나오고 본문 텍스트와 어긋나지 않는다.
#    (2026-08-25: 이름을 안 주면 codex가 임의 메뉴를 만들어 글과 그림이 따로 놀았음)
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
high legibility, no watermark, no logo. \
Use exactly the Korean dish names given above as the card captions, in the same order, spelled exactly."

PROMPT="Korean recipe infographic poster, square 1:1. Title in large Korean Hangul reading '${TITLE}'. ${BODY} ${STYLE}"

echo "[gen_card] slug=$SLUG"

~/.claude/skills/codex-image/scripts/gen.sh \
  --prompt "$PROMPT" \
  --out "$OUT" \
  --orientation square --width 1080 --height 1080 </dev/null

[ -f "$OUT" ] || { echo "[gen_card] 실패: PNG 미생성 $SLUG"; exit 1; }
echo "[gen_card] 완료 → $OUT"
