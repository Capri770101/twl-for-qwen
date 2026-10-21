"""
把选定的方向图放大到 21:9 可用尺寸。
配方：1024x439 出图 → lanczos 到 1344x576 → 2x-AnimeSharpV4 → 2688x1152
（照 anima_00 通用工作流的纯放大链，不做二段采样）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(__file__))
import gen_hero_test as G

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, "
       "logo, watermark, signature, text, "
       "anime, manga, cartoon, cel shading, anime face, 1girl, 1boy, person, people, "
       "human face, character, chibi, illustration style")

PRESETS = {
    "A": ("photograph, realistic photo, florist workbench, wooden table, "
          "hands arranging eucalyptus and white roses, half-wrapped bouquet, "
          "florist scissors, twine, kraft paper, petals scattered, "
          "soft window side light, shallow depth of field, warm beige tones, "
          "muted colors, editorial photography, natural light, film grain, "
          "negative space on upper half, minimal, quiet"),
    "B": ("photograph, realistic photo, still life, a ceramic vase with white roses "
          "and eucalyptus on a light wooden table, near a window, "
          "soft daylight, long soft shadow on wall, large empty wall space, "
          "muted beige and off-white palette, quiet, minimal, "
          "editorial interior photography, natural tones, film grain, "
          "shallow depth of field"),
    "C": ("photograph, realistic photo, small flower atelier interior, "
          "wooden counter, buckets of flowers along the wall, dried flowers hanging, "
          "paper wrapping rolls, large window with soft light entering, "
          "empty floor space in foreground, wide angle, "
          "muted warm palette, quiet morning, "
          "architectural interior photography, natural light, film grain"),
}


def upscale_chain(graph):
    """在 graph 里加 lanczos + 2x 模型放大 + 保存。"""
    graph["12"] = {"class_type": "ImageScale",
                   "inputs": {"image": ["11", 0], "upscale_method": "lanczos",
                              "width": 1344, "height": 576, "crop": "disabled"}}
    graph["13"] = {"class_type": "UpscaleModelLoader",
                   "inputs": {"model_name": "2x-AnimeSharpV4_RCAN.safetensors"}}
    graph["14"] = {"class_type": "ImageUpscaleWithModel",
                   "inputs": {"upscale_model": ["13", 0], "image": ["12", 0]}}
    graph["save_big"] = {"class_type": "SaveImage",
                         "inputs": {"images": ["14", 0], "filename_prefix": "hero_final"}}
    return graph


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "B"
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else random.randint(1, 2**31)
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 2

    prompt = PRESETS[which]
    print(f"方向 {which} | seed {seed} | 出 {n} 张")
    print(f"  1024x439 → 1344x576 → 2x → 2688x1152")
    for i in range(n):
        g = G.build(prompt=prompt, negative=NEG, w=1024, h=439,
                    seed=seed + i, prefix=f"hero_{which}_draft",
                    lora_name=r"anima\style\Anima_Real_Skin_Enhancer.safetensors",
                    lora_w=0.5,
                    style_lora=r"anima\style\zzz_artstyle_litu_anima.safetensors",
                    style_w=0.0)
        g = upscale_chain(g)
        try:
            imgs, sec = G.run(g, timeout=900)
            for path, size in G.download(imgs):
                print(f"  ✓ {os.path.basename(path)}  {size//1024} KB  ({sec}s)")
        except Exception as e:
            print(f"  ✗ {e}")
