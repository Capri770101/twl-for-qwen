# -*- coding: utf-8 -*-
"""
跳舞兰 H5 素材生成 —— 花艺商品图 / 场景图
ComfyUI + Anima (Qwen-Image 底座)
"""
import json, urllib.request, urllib.error, time, os

SERVER = "http://127.0.0.1:8188"
OUT_DIR = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\assets"

UNET = "anima-aesthetic-v1.1.safetensors"
CLIP = "qwen_3_06b_base.safetensors"
VAE = "qwen_image_vae.safetensors"

STEPS = 32
CFG = 5.0
SAMPLER = "er_sde"
SCHEDULER = "simple"

# 通用负向：压制二次元/插画，逼向摄影
NEG_BASE = """
lowres, bad quality, worst quality, blurry, jpeg artifacts,
watermark, signature, text, logo, border, frame,
illustration, anime, cartoon, drawing, painting, sketch, 3d render, cgi,
cluttered background, busy background,
deformed, distorted, extra objects, duplicate
"""

# ---------------------------------------------------------------
# 任务列表：(seed, 文件名, 宽, 高, 正向提示词)
JOBS = [

    # 测试 1：白底花束 —— 商品图
    (200001, "test_product_rose", 1024, 1024, """
professional product photography of a bouquet,
champagne roses, twenty stems, baby's breath, eucalyptus leaves,
wrapped in frosted matte paper with champagne ribbon,
pure white seamless background, soft studio lighting, even illumination,
centered composition, full bouquet visible, sharp focus, high detail,
commercial flower shop product photo, clean and minimal
"""),

    # 测试 2：花艺师工作场景 —— Hero
    (200002, "test_hero_workshop", 1408, 832, """
editorial photography, a florist's hands arranging flowers on a wooden workbench,
scattered rose petals, eucalyptus branches, pruning shears, kraft paper,
warm natural window light from the left, shallow depth of field,
muted earthy tones, film grain, documentary style,
soft shadows, cozy atelier atmosphere, candid moment
"""),
]

def api(path, data=None):
    url = SERVER + path
    if data is None:
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))

def build(seed, prefix, w, h, positive, negative=NEG_BASE):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "stable_diffusion", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": positive.strip(), "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": negative.strip(), "clip": ["2", 0]}},
        "6": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": STEPS, "cfg": CFG,
            "sampler_name": SAMPLER, "scheduler": SCHEDULER, "denoise": 1.0,
            "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": prefix, "images": ["8", 0]}},
    }

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    ids = []
    for seed, prefix, w, h, pos in JOBS:
        g = build(seed, prefix, w, h, pos)
        r = api("/prompt", {"prompt": g, "client_id": "tiaowulan"})
        print(f"[queued] {prefix}  {w}x{h}  seed={seed}  id={r.get('prompt_id')}", flush=True)
        ids.append((prefix, r.get("prompt_id")))

    deadline = time.time() + 3000
    done = set()
    while time.time() < deadline and len(done) < len(ids):
        for prefix, pid in ids:
            if prefix in done: continue
            try:
                h = api(f"/history/{pid}")
            except Exception:
                continue
            if pid in h:
                print(f"[done] {prefix}", flush=True)
                done.add(prefix)
        if len(done) < len(ids):
            time.sleep(5)
    print(f"[summary] {len(done)}/{len(ids)}", flush=True)

if __name__ == "__main__":
    main()
