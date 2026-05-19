#!/usr/bin/env python3
"""
咔嚓咔嚓号小火车 · AI 音效批量生成脚本
使用 ElevenLabs Sound Effects API 生成 7 幕背景音效

使用方法：
  1. 获取 API Key: https://elevenlabs.io (免费注册，每月10,000字符)
  2. 运行: python3 generate_sfx.py --api-key YOUR_KEY
  3. 或设置环境变量: export ELEVENLABS_API_KEY=YOUR_KEY && python3 generate_sfx.py

输出目录: ./audio/
"""

import argparse
import os
import sys
import json
import time
import urllib.request
import urllib.error

# ===== 7幕音效配置 =====
SOUND_EFFECTS = [
    {
        "id": "BGM-01",
        "slide": "S01",
        "act": "第一幕·始发站",
        "filename": "s01_station_start.mp3",
        "duration_seconds": 10,
        "prompt": (
            "Steam train whistle blowing twice, cheerful crowd of children cheering and laughing, "
            "colorful balloons, festive train station atmosphere, xylophone melody, "
            "bright joyful and warm, Ghibli style children animation sound"
        ),
    },
    {
        "id": "BGM-02",
        "slide": "S02",
        "act": "第二幕·火车开动",
        "filename": "s02_train_moving.mp3",
        "duration_seconds": 10,
        "prompt": (
            "Steam locomotive rhythmic chug-chug-chug accelerating, train wheels clacking on tracks, "
            "steam hissing from chimney, children laughing inside train, "
            "upbeat and energetic, speed and joy, whistling melody"
        ),
    },
    {
        "id": "BGM-03",
        "slide": "S03",
        "act": "第三幕·森林站",
        "filename": "s03_forest_station.mp3",
        "duration_seconds": 10,
        "prompt": (
            "Magical forest ambience, multiple birds chirping and singing melodically, "
            "gentle breeze rustling leaves, train bell arriving, "
            "harp and flute melody, warm sunlight through trees, "
            "peaceful and wondrous, Ghibli forest atmosphere"
        ),
    },
    {
        "id": "BGM-04",
        "slide": "S04",
        "act": "第四幕·告别森林站",
        "filename": "s04_farewell_forest.mp3",
        "duration_seconds": 10,
        "prompt": (
            "Train rhythmic clacking gradually fading, soft wind, "
            "distant birds calling goodbye, gentle string pizzicato, "
            "nostalgic and bittersweet but hopeful, train moving away into distance"
        ),
    },
    {
        "id": "BGM-05",
        "slide": "S05",
        "act": "第五幕·动物乐园站",
        "filename": "s05_animal_park.mp3",
        "duration_seconds": 12,
        "prompt": (
            "Lively festive animal sounds, dog barking happily, cat meowing playfully, "
            "duck quacking, bees buzzing, butterflies fluttering, "
            "children clapping hands in rhythm, group laughter, "
            "friendship song melody, upbeat and celebratory, BPM 120"
        ),
    },
    {
        "id": "BGM-06",
        "slide": "S06",
        "act": "第六幕·夕阳归途",
        "filename": "s06_sunset_journey.mp3",
        "duration_seconds": 10,
        "prompt": (
            "Peaceful evening train journey, soft gentle wind, "
            "distant train chugging slowly, warm sunset ambience, "
            "piano and cello duet, slow tender melody, "
            "grateful and heartwarming, golden hour atmosphere"
        ),
    },
    {
        "id": "BGM-07",
        "slide": "S07",
        "act": "第七幕·学校站",
        "filename": "s07_school_station.mp3",
        "duration_seconds": 12,
        "prompt": (
            "Train gently arriving at station, soft bell chime, "
            "children saying goodbye warmly, children choir humming softly, "
            "single clear whistle sound, then one final chug-chug fading to silence, "
            "magical heartwarming ending, emotional and complete"
        ),
    },
]


def generate_sfx_elevenlabs(api_key: str, prompt: str, duration: int) -> bytes:
    """调用 ElevenLabs Sound Effects API 生成音效"""
    url = "https://api.elevenlabs.io/v1/sound-generation"
    payload = json.dumps({
        "text": prompt,
        "duration_seconds": duration,
        "prompt_influence": 0.3,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def main():
    parser = argparse.ArgumentParser(description="咔嚓咔嚓号 AI 音效生成器")
    parser.add_argument("--api-key", default=os.environ.get("ELEVENLABS_API_KEY", ""),
                        help="ElevenLabs API Key (或设置 ELEVENLABS_API_KEY 环境变量)")
    parser.add_argument("--output-dir", default="audio",
                        help="音频输出目录 (默认: ./audio)")
    parser.add_argument("--slides", nargs="*",
                        help="只生成指定幕次，如 --slides S01 S03 S07")
    parser.add_argument("--dry-run", action="store_true",
                        help="只打印配置，不实际生成")
    args = parser.parse_args()

    if not args.api_key and not args.dry_run:
        print("❌ 缺少 API Key！")
        print("   方法1: python3 generate_sfx.py --api-key YOUR_KEY")
        print("   方法2: export ELEVENLABS_API_KEY=YOUR_KEY")
        print("   获取免费 Key: https://elevenlabs.io (每月10,000字符免费)")
        sys.exit(1)

    # 创建输出目录
    out_dir = os.path.join(os.path.dirname(__file__), args.output_dir)
    os.makedirs(out_dir, exist_ok=True)

    # 过滤幕次
    targets = SOUND_EFFECTS
    if args.slides:
        targets = [s for s in SOUND_EFFECTS if s["slide"] in args.slides]
        print(f"🎯 只生成: {[s['slide'] for s in targets]}")

    print(f"\n🎵 咔嚓咔嚓号 AI 音效生成器")
    print(f"   输出目录: {out_dir}")
    print(f"   待生成: {len(targets)} 个音效\n")

    results = []
    for i, sfx in enumerate(targets, 1):
        out_path = os.path.join(out_dir, sfx["filename"])
        print(f"[{i}/{len(targets)}] {sfx['act']} ({sfx['id']})")
        print(f"  Prompt: {sfx['prompt'][:60]}...")

        if args.dry_run:
            print(f"  [DRY RUN] 跳过生成 → {out_path}\n")
            results.append({"id": sfx["id"], "status": "dry-run", "path": out_path})
            continue

        if os.path.exists(out_path):
            print(f"  ⏭️  已存在，跳过: {sfx['filename']}\n")
            results.append({"id": sfx["id"], "status": "skipped", "path": out_path})
            continue

        try:
            print(f"  ⏳ 生成中（约10-20秒）...")
            audio_data = generate_sfx_elevenlabs(
                api_key=args.api_key,
                prompt=sfx["prompt"],
                duration=sfx["duration_seconds"],
            )
            with open(out_path, "wb") as f:
                f.write(audio_data)
            size_kb = len(audio_data) // 1024
            print(f"  ✅ 完成: {sfx['filename']} ({size_kb} KB)\n")
            results.append({"id": sfx["id"], "status": "ok", "path": out_path})
            # 避免触发速率限制
            if i < len(targets):
                time.sleep(2)

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"  ❌ HTTP {e.code}: {body[:200]}\n")
            results.append({"id": sfx["id"], "status": f"error-{e.code}", "path": None})
        except Exception as e:
            print(f"  ❌ 错误: {e}\n")
            results.append({"id": sfx["id"], "status": "error", "path": None})

    # 输出结果摘要
    ok = sum(1 for r in results if r["status"] == "ok")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors = sum(1 for r in results if r["status"].startswith("error"))

    print("=" * 50)
    print(f"✅ 生成成功: {ok}  ⏭️ 已跳过: {skipped}  ❌ 失败: {errors}")

    if ok > 0 or skipped > 0:
        print(f"\n📁 音频文件位于: {out_dir}/")
        print("\n下一步：运行以下命令将音效嵌入 HTML PPT：")
        print(f"  python3 inject_audio.py")


if __name__ == "__main__":
    main()
