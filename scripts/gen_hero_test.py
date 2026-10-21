"""
跳舞兰首页 21:9 通栏图 · 方向测试
用 anima-aesthetic-v1.1 出图，先低分辨率试方向，选定后再放大。
"""
import json, urllib.request, io, os, sys, time, random

API = "http://127.0.0.1:8188"
OUT = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\assets\hero\_test"
os.makedirs(OUT, exist_ok=True)


def build(prompt, negative, w, h, seed, prefix, steps=30, cfg=4.0,
          lora_name=None, lora_w=0.0, style_lora=None, style_w=0.0):
    """按 anima_00 通用工作流的官方配方搭 API 格式工作流。"""
    g = {
        "1": {"class_type": "UNETLoader",
              "inputs": {"unet_name": "anima-aesthetic-v1.1.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": "qwen_3_06b_base.safetensors", "type": "stable_diffusion"}},
        "3": {"class_type": "VAELoader",
              "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["6", 1], "text": prompt}},
        "8": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["6", 1], "text": negative}},
        "9": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "10": {"class_type": "KSampler",
               "inputs": {"model": ["6", 0], "positive": ["7", 0], "negative": ["8", 0],
                          "latent_image": ["9", 0], "seed": seed, "steps": steps, "cfg": cfg,
                          "sampler_name": "er_sde", "scheduler": "simple", "denoise": 1.0}},
        "11": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["3", 0]}},
        "12": {"class_type": "SaveImage", "inputs": {"images": ["11", 0], "filename_prefix": prefix}},
        # LoRA 链：5=角色位（这里放风格/质感），6=画风位
        "5": {"class_type": "LoraLoader",
              "inputs": {"model": ["1", 0], "clip": ["2", 0],
                         "lora_name": lora_name or "anima\style\Anima_Detail_Tweaker.safetensors",
                         "strength_model": lora_w, "strength_clip": lora_w}},
        "6": {"class_type": "LoraLoader",
              "inputs": {"model": ["5", 0], "clip": ["5", 1],
                         "lora_name": style_lora or "anima\style\zzz_artstyle_litu_anima.safetensors",
                         "strength_model": style_w, "strength_clip": style_w}},
    }
    return g


def run(graph, timeout=600):
    data = json.dumps({"prompt": graph, "client_id": "twl_hero"}).encode()
    req = urllib.request.Request(f"{API}/prompt", data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"提交失败 {e.code}: {body[:800]}")
    pid = r["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            h = json.loads(urllib.request.urlopen(f"{API}/history/{pid}", timeout=10).read())
        except Exception:
            time.sleep(1); continue
        if pid in h:
            entry = h[pid]
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError("生成报错: " + json.dumps(status)[:800])
            imgs = []
            for node_out in entry.get("outputs", {}).values():
                for im in node_out.get("images", []):
                    imgs.append((im["filename"], im.get("subfolder", "")))
            return imgs, round(time.time() - t0, 1)
        time.sleep(1)
    raise TimeoutError("超时")


def download(imgs):
    got = []
    for fn, sub in imgs:
        q = urllib.parse.urlencode({"filename": fn, "subfolder": sub, "type": "output"})
        raw = urllib.request.urlopen(f"{API}/view?{q}", timeout=60).read()
        dst = os.path.join(OUT, fn)
        with open(dst, "wb") as f:
            f.write(raw)
        got.append((dst, len(raw)))
    return got


if __name__ == "__main__":
    import urllib.parse
