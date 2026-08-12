#!/usr/bin/env python3
"""쿠파스 큐 항목별 AI 사용컷 프롬프트 2컷(A=사용장면, B=디테일컷)을 생성해 img_prompts.json 저장.

각 제품 = (queue_index, item_en, use_action, placement).
  A(사용컷): 손으로 실제 쓰는 현장 컷 → 바이럴에 제일 잘 먹힘.
  B(디테일컷): 제품이 집안 표면에 놓인/배치된 근접 컷 → 썸네일과 다른 각도.
톤: 실사 스마트폰 스냅, 한국 가정, 자연광. 텍스트·워터마크·로고·브랜드 없음.
"""
import json

SUF = "photorealistic, natural daylight, real Korean home, no text, no watermark, no logo, no brand name, no words"

# (idx, item_en, use_action, placement)
P = [
    (1, "a handheld one-press garlic chopper", "a hand pressing a one-press garlic chopper to mince garlic on a kitchen cutting board", "next to a small pile of freshly minced garlic on a wooden board"),
    (2, "a stackable egg storage tray", "a hand placing eggs into a clear stackable egg tray inside a fridge", "full of eggs on a refrigerator shelf"),
    (3, "a silicone dish scrubber", "a hand scrubbing a plate with a silicone dish scrubber at the kitchen sink", "resting on the edge of a stainless sink"),
    (4, "colorful bag sealing clips", "a hand sealing an open snack bag with a plastic bag clip", "clipped onto several food bags in a pantry"),
    (5, "a multi vegetable slicer", "a hand slicing a cucumber on a multi vegetable slicer over a bowl", "with neatly sliced vegetables beside it on a counter"),
    (6, "a one-touch can opener", "a hand using a one-touch can opener to open a food can", "sitting on a kitchen counter next to an opened can"),
    (7, "a silicone pot clip holder", "a hand lifting a hot bowl with silicone pot grips", "clipped on the rim of a stainless bowl"),
    (8, "a silicone air fryer mat", "a hand placing food on a silicone air fryer liner mat inside an air fryer basket", "lining the bottom of an air fryer basket"),
    (9, "a jar lid opener gripper", "a hand twisting open a tight jar lid with a rubber lid opener", "resting on the counter beside a glass jar"),
    (10, "a sink drain strainer basket", "a hand placing a mesh drain strainer into a kitchen sink drain", "set inside a stainless sink drain hole"),
    (11, "vertical freezer storage trays", "a hand sliding food pouches into vertical freezer organizer trays", "filled with frozen pouches standing upright in a freezer"),
    (12, "a collapsible silicone water bottle", "a hand folding a collapsible silicone water bottle flat", "half collapsed on a desk"),
    (13, "a cutting board with handle", "a hand carrying a wooden cutting board with a handle holding chopped vegetables", "leaning upright on a kitchen counter"),
    (14, "a slim rolling storage cart", "a hand pulling out a slim rolling storage cart from a narrow kitchen gap", "tucked into a narrow gap between fridge and wall"),
    (15, "clear mesh zip pouches", "a hand organizing items into clear mesh zip pouches", "a few clear mesh pouches laid on a table"),
    (16, "a two-tier shoe rack", "a hand placing shoes on a two-tier shoe organizer rack", "holding several pairs of shoes at an entryway"),
    (17, "adhesive cable organizer clips", "a hand routing a charging cable into an adhesive cable clip on a desk edge", "stuck along the edge of a desk holding cables"),
    (18, "no-slip shoulder hangers", "a hand hanging a knit sweater on a no-slip shoulder hanger", "a row of hangers on a closet rod"),
    (19, "space-saving cascading hangers", "a hand hanging shirts on a space-saving cascading hanger", "hung vertically in a closet saving space"),
    (20, "an under-bed storage box on wheels", "a hand rolling an under-bed storage box out from under a bed", "sliding under a bed frame"),
    (21, "an over-the-door hanging rack", "a hand hanging bags on an over-the-door hook rack", "mounted over the top of a door"),
    (22, "adjustable drawer dividers", "a hand adjusting dividers inside an organized drawer", "separating socks inside an open drawer"),
    (23, "a rotating cosmetics organizer", "a hand spinning a rotating cosmetics organizer on a vanity", "holding makeup bottles on a dresser"),
    (24, "a no-drill wall shelf", "a hand placing items on an adhesive no-drill wall shelf", "mounted on a bathroom tile wall"),
    (25, "strong adhesive wall hooks", "a hand hanging a towel on a strong adhesive wall hook", "stuck on a wall holding a towel"),
    (26, "travel compression bags", "a hand rolling clothes into a travel compression bag", "flattened compressed bags in an open suitcase"),
    (27, "a sofa side caddy hanger", "a hand placing a remote into a sofa side caddy organizer", "draped over the armrest of a sofa"),
    (28, "a magnetic tool holder strip", "a hand attaching scissors to a magnetic tool holder", "mounted on a wall holding metal tools"),
    (29, "a multipurpose gripper clip", "a hand hanging laundry with a multipurpose gripper clip", "clipped on a drying rack"),
    (30, "antibacterial kitchen wipes", "a hand wiping a kitchen counter with a disposable dishcloth wipe", "a stack of kitchen wipes on a counter"),
    (31, "a grease and grime cleaner", "a hand spraying and wiping grease off a stove with a cleaner cloth", "a spray bottle beside a clean stovetop"),
    (32, "a handheld steam cleaner", "a hand steam cleaning bathroom tiles with a handheld steam cleaner", "resting on a bathroom floor with steam"),
    (33, "a window track cleaning brush", "a hand scrubbing a dirty window track with a crevice brush", "lying along a window sill track"),
    (34, "a drain cleaning tool", "a hand using a flexible drain cleaning tool in a bathroom drain", "next to a shower drain"),
    (35, "a static duster", "a hand dusting a shelf with a fluffy static duster", "leaning against a bookshelf"),
    (36, "a folding laundry drying rack", "a hand hanging laundry on a folding drying rack", "unfolded near a window with clothes"),
    (37, "a washing machine tub cleaner", "a hand dropping a washing machine tub cleaner tablet into a washer", "beside an open washing machine"),
    (38, "a lint roller", "a hand rolling a lint roller over a black coat", "resting on a folded sweater"),
    (39, "a handheld garment steamer", "a hand steaming wrinkles out of a hanging shirt with a handheld steamer", "held near a hanging shirt with steam"),
    (40, "a mold remover gel", "a hand applying mold remover gel along bathroom silicone seams", "a tube beside a clean bathroom corner"),
    (41, "a flat mop with electrostatic cloths", "a hand mopping a floor with a flat electrostatic mop", "leaning against a wall on a clean floor"),
    (42, "a shower head filter", "a hand attaching a filter cartridge to a shower head", "installed on a shower head in a bathroom"),
    (43, "a high-pressure shower head", "a hand holding a high-pressure shower head with strong water spray", "mounted in a tiled shower"),
    (44, "a no-drill bathroom shelf", "a hand placing shampoo on an adhesive no-drill bathroom shelf", "mounted on a shower wall holding bottles"),
    (45, "a UV toothbrush sanitizer holder", "a hand placing a toothbrush into a UV sanitizer holder", "mounted on a bathroom wall with toothbrushes"),
    (46, "a drop-in toilet bowl cleaner", "a hand dropping a toilet tank cleaner tablet", "beside a clean toilet"),
    (47, "an automatic soap dispenser", "a hand under an automatic foaming soap dispenser", "on a bathroom sink counter"),
    (48, "an electric foot callus remover", "a hand using an electric foot file on a heel", "resting on a bathroom stool"),
    (49, "quick-dry bathroom slippers", "feet wearing quick-dry bathroom slippers on a wet floor", "a pair of slippers on a bathroom floor"),
    (50, "decorative appliance stickers", "a hand applying a cute character sticker on a refrigerator door", "decorating a white refrigerator"),
    (51, "an adjustable tablet stand and book holder", "a hand adjusting an angle-adjustable tablet stand on a desk", "holding a tablet on a desk"),
    (52, "a clip-on phone holder", "a hand clipping a phone into a clamp phone holder on a desk", "gripping a smartphone on a desk edge"),
    (53, "a one-touch automatic umbrella", "a hand opening a one-touch automatic umbrella", "leaning by a front door"),
    (54, "a zip bag holder stand", "a hand pouring soup into a zip bag held open by a stand", "holding an open zip bag on a counter"),
    (55, "a door gap draft blocker", "a hand pressing a door draft blocker strip along the bottom of a door", "sealing the bottom gap of a door"),
    (56, "an anti-slip mat", "a hand smoothing an anti-slip mat under a rug", "laid flat on a floor"),
    (57, "an office foot rest", "feet resting on an ergonomic foot rest under a desk", "under an office desk"),
    (58, "an electric mosquito trap", "a hand switching on an electric mosquito trap lamp", "glowing on a bedroom nightstand at night"),
    (59, "an automatic sensor trash can", "a hand waving over an automatic sensor lid trash can", "standing in a kitchen corner"),
    (60, "a portable neck fan", "a person wearing a portable neck fan outdoors on a hot day", "resting on a table"),
    (61, "a cooling gel mat", "a hand touching a cooling gel mat on a bed", "spread on top of a bed"),
    (62, "a heated electric mattress pad", "a hand adjusting the controller of a heated mattress pad", "spread on a cozy bed"),
    (63, "a mini humidifier", "a mini humidifier releasing mist on a desk beside a person", "on a bedside table with mist"),
    (64, "an anti-static spray", "a hand spraying anti-static spray on a skirt", "a spray bottle on a dresser"),
    (65, "a shoe waterproof spray", "a hand spraying waterproofing spray on sneakers", "beside a pair of sneakers"),
    (66, "an umbrella rain cover sleeve", "a hand sliding a wet umbrella into a rain cover sleeve", "hanging by a doorway"),
    (67, "a cordless car vacuum", "a hand vacuuming a car seat with a cordless handheld car vacuum", "resting on a car seat"),
    (68, "a car seat gap organizer", "a hand slotting a phone into a car seat gap filler organizer", "wedged between a car seat and console"),
    (69, "a magnetic car phone mount", "a hand attaching a phone to a magnetic car dashboard mount", "mounted on a car air vent"),
    (70, "a car windshield sun shade", "a hand unfolding a windshield sun shade inside a parked car", "covering a car windshield"),
    (71, "a refillable car air freshener", "a hand clipping a car air freshener onto an air vent", "attached to a car air vent"),
    (72, "a windshield frost cover", "a hand spreading a frost cover over a car windshield in winter", "draped over a car windshield"),
    (73, "a mini humidifier mood lamp", "a mini humidifier with a glowing mood light on a nightstand at night", "glowing softly in a dim bedroom"),
    (74, "a mini cordless hair dryer and curler", "a hand styling hair with a mini cordless hair dryer", "resting on a bathroom vanity"),
    (75, "an electric nose and eyebrow trimmer", "a hand using a small electric nose hair trimmer at a mirror", "on a bathroom counter"),
    (76, "a portable mini iron", "a hand pressing wrinkles out of a collar with a portable mini iron", "resting on a folded shirt"),
    (77, "an ultrasonic eyeglass cleaner", "a hand placing glasses into an ultrasonic eyeglass cleaner", "on a desk with glasses inside"),
    (78, "a multi-device wireless charging pad", "a hand placing a phone on a multi-device wireless charging pad", "charging a phone and earbuds on a desk"),
    (79, "a portable mini blender", "a hand blending a fruit smoothie in a portable mini blender", "on a kitchen counter with fruit"),
    (80, "a smart body scale with app", "bare feet standing on a smart body weight scale", "on a bathroom floor"),
    (81, "an automatic pet water fountain", "a cat drinking from an automatic pet water fountain", "on the floor by a wall"),
    (82, "a one-touch pet hair removal brush", "a hand brushing a dog with a one-touch self-cleaning pet brush", "beside a fluffy pet bed"),
    (83, "a pet paw washing cup", "a hand cleaning a dog paw with a paw washing cup", "on the floor by an entryway"),
    (84, "corner safety guards", "a hand pressing a soft corner safety guard onto a table edge", "attached to the corner of a coffee table"),
    (85, "a portable diaper pouch", "a hand pulling wipes from a portable diaper changing pouch", "open on a bed with baby items"),
    (86, "an electric scalp massager", "a hand using an electric scalp massager on the head", "resting on a nightstand"),
    (87, "fresh shine muscat grapes", "a hand rinsing a bunch of green shine muscat grapes", "a bowl of green grapes on a table"),
    (88, "fresh peaches", "a hand holding a ripe peach over a fruit bowl", "a bowl of fresh peaches on a table"),
    (89, "Jeju tangerines", "a hand peeling a fresh tangerine", "a pile of tangerines in a basket"),
    (90, "frozen blueberries", "a hand pouring frozen blueberries into a bowl of yogurt", "frozen blueberries in a bowl"),
    (91, "trimmed chicken breast packs", "a hand opening a pack of trimmed chicken breast in a kitchen", "vacuum packs on a counter"),
    (92, "a meal kit for hotpot", "a hand cooking a spicy hotpot meal kit on a stove", "meal kit ingredients laid on a counter"),
    (93, "frozen beef intestines", "a hand grilling frozen gopchang on a pan", "raw packs beside a grill pan"),
    (94, "semi-dried squid snack", "a hand tearing a piece of semi-dried squid snack", "squid snack on a plate"),
    (95, "induction cooktop cleaning tissues", "a hand wiping an induction cooktop with a cleaning tissue", "a box of tissues on a counter"),
    (96, "kitchen power cleaning wipes", "a hand scrubbing a greasy range hood with a power cleaning wipe", "a pack of wipes on a counter"),
    (97, "multipurpose power cleaning wipes", "a hand wiping a dirty wall switch with a multipurpose cleaning wipe", "a pack of wipes on a table"),
    (98, "citric acid cleaning wipes", "a hand wiping hard water stains off a faucet with a cleaning wipe", "a pack of wipes by a sink"),
    (99, "refrigerator organizing trays", "a hand sliding food containers into clear refrigerator organizer trays", "clear trays filled inside a fridge"),
    (100, "a refrigerator sliding shelf", "a hand pulling out a refrigerator sliding shelf drawer", "installed under a fridge shelf"),
]


def main():
    out = {}
    for idx, item, action, place in P:
        a = f"Realistic candid smartphone photo, {action}, cozy everyday scene, natural window light, shallow depth of field, {SUF}"
        b = f"Realistic close-up smartphone photo of {item} {place}, clean tidy home surface, {SUF}"
        out[str(idx)] = {"name_en": item, "a": a, "b": b}
    json.dump(out, open("img_prompts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{len(out)}개 제품 프롬프트 생성 → img_prompts.json")


if __name__ == "__main__":
    main()
