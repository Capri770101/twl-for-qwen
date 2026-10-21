# -*- coding: utf-8 -*-
"""
跳舞兰 H5 商品图批量生成
"""
import json, urllib.request, time, os, shutil

SERVER = "http://127.0.0.1:8188"
OUT = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\assets\products"
SRC = r"D:\ComfyUI\output"

UNET = "anima-aesthetic-v1.1.safetensors"
CLIP = "qwen_3_06b_base.safetensors"
VAE = "qwen_image_vae.safetensors"

STEPS, CFG = 32, 5.0
SAMPLER, SCHEDULER = "er_sde", "simple"

NEG = """
lowres, bad quality, worst quality, blurry, jpeg artifacts,
watermark, signature, text, logo, border, frame,
illustration, anime, cartoon, drawing, painting, sketch, 3d render, cgi,
cluttered background, busy background, colored background,
multiple bouquets, hands, people, vase, table,
deformed, distorted, extra objects
"""

COMMON = """
professional product photography, single flower bouquet,
wrapped in frosted matte paper with satin ribbon,
pure white seamless background, soft even studio lighting,
centered composition, full bouquet visible top to bottom,
sharp focus, ultra detailed, commercial flower shop catalog photo,
clean minimal aesthetic
"""

# (seed, 文件名, 花材描述)
JOBS = [
    (300001, "01_chenguang", "twenty champagne roses, baby's breath, eucalyptus leaves, cream paper, champagne ribbon"),
    (300002, "02_xiaoman",   "twelve white tulips, eucalyptus branches, white paper, white ribbon"),
    (300003, "03_wuye",      "three blue purple hydrangeas, silver dusty miller leaves, deep blue paper, navy ribbon"),
    (300004, "04_muxing",    "six sunflowers, eucalyptus leaves, kraft paper, brown twine"),
    (300005, "05_xueluo",    "thirty three white roses, silver dusty miller leaves, ivory paper, white ribbon"),
    (300006, "06_shancha",   "nine red camellia flowers, dried branches, dark red paper, black ribbon"),
]

def api(path, data=None):
    url = SERVER + path
    req = urllib.request.Request(url) if data is None else \
          urllib.request.Request(url, data=json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode())

def build(seed, prefix, flowers):
    pos = f"a bouquet of {flowers}.\n{COMMON.strip()}"
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "stable_diffusion", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG.strip(), "clip": ["2", 0]}},
        "6": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": STEPS, "cfg": CFG,
            "sampler_name": SAMPLER, "scheduler": SCHEDULER, "denoise": 1.0,
            "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": prefix, "images": ["8", 0]}},
    }

def main():
    os.makedirs(OUT, exist_ok=True)
    ids = []
    for seed, name, flowers in JOBS:
        r = api("/prompt", {"prompt": build(seed, name, flowers), "client_id": "twl"})
        print(f"[queued] {name}", flush=True)
        ids.append((name, r.get("prompt_id")))

    deadline = time.time() + 3600
    done = set()
    while time.time() < deadline and len(done) < len(ids):
        for name, pid in ids:
            if name in done: continue
            try:
                h = api(f"/history/{pid}")
            except Exception:
                continue
            if pid in h:
                outs = h[pid].get("outputs", {})
                for node in outs.values():
                    for img in node.get("images", []):
                        src = os.path.join(SRC, img.get("subfolder",""), img["filename"])
                        if os.path.exists(src):
                            dst = os.path.join(OUT, name + ".png")
                            shutil.copy2(src, dst)
                            print(f"[saved] {dst}", flush=True)
                done.add(name)
                print(f"[done] {name}", flush=True)
        if len(done) < len(ids):
            time.sleep(5)
    print(f"[summary] {len(done)}/{len(ids)}", flush=True)

if __name__ == "__main__":
    main()
