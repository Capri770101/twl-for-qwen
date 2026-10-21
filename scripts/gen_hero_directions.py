import sys, os, random
sys.path.insert(0, os.path.dirname(__file__))
import gen_hero_test as G
import urllib.parse

NEG_BASE = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, "
            "sepia, logo, watermark, signature, text, "
            "anime, manga, cartoon, cel shading, anime face, 1girl, 1boy, person, people, "
            "human face, character, chibi, illustration style")

# 三个方向，都是 21:9 的低分辨率草稿（768x336 够看方向）
CASES = [
    {
        "name": "A_workbench",
        "label": "A · 工作台上正在包花（手部动作）",
        "prompt": ("photograph, realistic photo, florist workbench, wooden table, "
                   "hands arranging eucalyptus and white roses, half-wrapped bouquet, "
                   "florist scissors, twine, kraft paper, petals scattered, "
                   "soft window side light, shallow depth of field, warm beige tones, "
                   "muted colors, editorial photography, natural light, film grain, "
                   "negative space on upper half, minimal, quiet"),
        "lora": ("anima\style\Anima_Real_Skin_Enhancer.safetensors", 0.6),
        "style": ("anima\style\zzz_artstyle_litu_anima.safetensors", 0.0),
    },
    {
        "name": "B_still_life",
        "label": "B · 静物：桌面花束与光影（无手）",
        "prompt": ("photograph, realistic photo, still life, a ceramic vase with white roses "
                   "and eucalyptus on a light wooden table, near a window, "
                   "soft daylight, long soft shadow on wall, large empty wall space, "
                   "muted beige and off-white palette, quiet, minimal, "
                   "editorial interior photography, natural tones, film grain, "
                   "shallow depth of field"),
        "lora": ("anima\style\Anima_Real_Skin_Enhancer.safetensors", 0.5),
        "style": ("anima\style\zzz_artstyle_litu_anima.safetensors", 0.0),
    },
    {
        "name": "C_atelier",
        "label": "C · 花艺工作室空间（环境氛围）",
        "prompt": ("photograph, realistic photo, small flower atelier interior, "
                   "wooden counter, buckets of flowers along the wall, dried flowers hanging, "
                   "paper wrapping rolls, large window with soft light entering, "
                   "empty floor space in foreground, wide angle, "
                   "muted warm palette, quiet morning, "
                   "architectural interior photography, natural light, film grain"),
        "lora": ("anima\style\Anima_Real_Skin_Enhancer.safetensors", 0.5),
        "style": ("anima\style\zzz_artstyle_litu_anima.safetensors", 0.0),
    },
]

for c in CASES:
    print(f"\n{'='*60}\n{c['label']}\n{'='*60}")
    g = G.build(
        prompt=c["prompt"], negative=NEG_BASE,
        w=768, h=336, seed=random.randint(1, 2**31),
        prefix=f"hero_test_{c['name']}",
        lora_name=c["lora"][0], lora_w=c["lora"][1],
        style_lora=c["style"][0], style_w=c["style"][1],
    )
    try:
        imgs, sec = G.run(g)
        print(f"  完成 {sec}s → {imgs}")
        for path, size in G.download(imgs):
            print(f"  {path}  {size//1024} KB")
    except Exception as e:
        print(f"  失败: {e}")
