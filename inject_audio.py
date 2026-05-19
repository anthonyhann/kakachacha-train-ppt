#!/usr/bin/env python3
"""
咔嚓咔嚓号小火车 · 音效注入脚本
将 audio/ 目录下的 MP3 文件嵌入 index.html，生成 index_with_audio.html

使用方法：
  python3 inject_audio.py
  python3 inject_audio.py --input index.html --output index_with_audio.html
"""

import argparse
import base64
import os
import re

AUDIO_MAP = {
    "s01": "audio/s01_station_start.mp3",
    "s02": "audio/s02_train_moving.mp3",
    "s03": "audio/s03_forest_station.mp3",
    "s04": "audio/s04_farewell_forest.mp3",
    "s05": "audio/s05_animal_park.mp3",
    "s06": "audio/s06_sunset_journey.mp3",
    "s07": "audio/s07_school_station.mp3",
}

AUDIO_JS = """
// ===== AUDIO ENGINE =====
const audioEngine = (() => {
  const tracks = {};
  let currentTrack = null;
  let fadeTimer = null;

  // 预加载所有音轨
  function preload(audioMap) {
    Object.entries(audioMap).forEach(([slideId, src]) => {
      const audio = new Audio(src);
      audio.loop = slideId !== 's07'; // 最后一幕不循环
      audio.volume = 0;
      audio.preload = 'auto';
      tracks[slideId] = audio;
    });
  }

  // 淡入淡出切换
  function switchTo(slideId, targetVol = 0.65) {
    const next = tracks[slideId];
    if (!next) return;
    if (currentTrack === next) return;

    // 淡出当前
    if (currentTrack) {
      const prev = currentTrack;
      fadeOut(prev, 600, () => { prev.pause(); prev.currentTime = 0; });
    }

    // 淡入新轨
    currentTrack = next;
    next.currentTime = 0;
    next.play().catch(() => {
      // 浏览器自动播放策略：等待用户交互后重试
      document.addEventListener('click', () => next.play().catch(() => {}), { once: true });
    });
    fadeIn(next, 800, targetVol);
  }

  function fadeIn(audio, duration, targetVol) {
    clearInterval(fadeTimer);
    const steps = 20;
    const interval = duration / steps;
    const step = targetVol / steps;
    let vol = 0;
    fadeTimer = setInterval(() => {
      vol = Math.min(vol + step, targetVol);
      audio.volume = vol;
      if (vol >= targetVol) clearInterval(fadeTimer);
    }, interval);
  }

  function fadeOut(audio, duration, callback) {
    const steps = 20;
    const interval = duration / steps;
    const step = audio.volume / steps;
    let vol = audio.volume;
    const timer = setInterval(() => {
      vol = Math.max(vol - step, 0);
      audio.volume = vol;
      if (vol <= 0) {
        clearInterval(timer);
        if (callback) callback();
      }
    }, interval);
  }

  function setVolume(vol) {
    if (currentTrack) currentTrack.volume = Math.max(0, Math.min(1, vol));
  }

  function mute() { if (currentTrack) currentTrack.volume = 0; }
  function unmute() { if (currentTrack) currentTrack.volume = 0.65; }

  return { preload, switchTo, setVolume, mute, unmute };
})();

// 幕次 → 音轨映射
const SLIDE_AUDIO = {
  0: 's01', 1: 's02', 2: 's03', 3: 's04',
  4: 's05', 5: 's06', 6: 's07'
};

// 音量配置（各幕情绪不同，音量略有差异）
const SLIDE_VOLUME = {
  0: 0.6,  // 始发站：欢快
  1: 0.7,  // 火车开动：活力
  2: 0.55, // 森林站：灵动
  3: 0.5,  // 告别森林：轻柔
  4: 0.75, // 动物乐园：热闹
  5: 0.5,  // 夕阳归途：舒缓
  6: 0.55, // 学校站：温情
};

// 音频文件路径（相对路径）
const AUDIO_SOURCES = {
  's01': 'audio/s01_station_start.mp3',
  's02': 'audio/s02_train_moving.mp3',
  's03': 'audio/s03_forest_station.mp3',
  's04': 'audio/s04_farewell_forest.mp3',
  's05': 'audio/s05_animal_park.mp3',
  's06': 'audio/s06_sunset_journey.mp3',
  's07': 'audio/s07_school_station.mp3',
};

// 初始化音频引擎
audioEngine.preload(AUDIO_SOURCES);

// 拦截 showSlide，在切换幕次时同步切换音轨
const _origShowSlide = showSlide;
showSlide = function(index, animate = true) {
  _origShowSlide(index, animate);
  const trackId = SLIDE_AUDIO[index];
  if (trackId) {
    audioEngine.switchTo(trackId, SLIDE_VOLUME[index] || 0.6);
  }
};

// 音量控制 UI
function toggleMute() {
  const btn = document.getElementById('mute-btn');
  if (btn.dataset.muted === '1') {
    audioEngine.unmute();
    btn.textContent = '🔊';
    btn.dataset.muted = '0';
  } else {
    audioEngine.mute();
    btn.textContent = '🔇';
    btn.dataset.muted = '1';
  }
}

// 键盘快捷键：M 静音
document.addEventListener('keydown', e => {
  if (e.key === 'm' || e.key === 'M') toggleMute();
});
// ===== END AUDIO ENGINE =====
"""

MUTE_BTN_HTML = """
  <!-- MUTE BUTTON -->
  <button id="mute-btn" data-muted="0" onclick="toggleMute()"
    style="position:fixed;bottom:24px;left:24px;width:44px;height:44px;
    border-radius:50%;border:2px solid rgba(255,255,255,0.4);
    background:rgba(0,0,0,0.5);backdrop-filter:blur(8px);
    color:#fff;font-size:20px;cursor:pointer;z-index:200;
    display:flex;align-items:center;justify-content:center;
    transition:all 0.2s;" title="静音/取消静音 (M)">🔊</button>
"""


def inject(html_path: str, output_path: str, base_dir: str):
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 检查哪些音频文件存在
    found = []
    missing = []
    for slide_id, rel_path in AUDIO_MAP.items():
        abs_path = os.path.join(base_dir, rel_path)
        if os.path.exists(abs_path):
            found.append(slide_id)
        else:
            missing.append((slide_id, rel_path))

    if missing:
        print(f"⚠️  以下音频文件缺失（将跳过对应幕次）：")
        for sid, p in missing:
            print(f"   {sid}: {p}")
        print()

    if not found:
        print("❌ 没有找到任何音频文件，请先运行 generate_sfx.py")
        return False

    print(f"✅ 找到 {len(found)}/{len(AUDIO_MAP)} 个音频文件: {found}")

    # 注入静音按钮（在 </body> 前）
    html = html.replace("</body>", MUTE_BTN_HTML + "\n</body>")

    # 注入音频引擎 JS（在最后一个 </script> 前）
    # 找到最后一个 </script> 标签
    last_script_end = html.rfind("</script>")
    if last_script_end == -1:
        print("❌ 未找到 </script> 标签")
        return False

    html = html[:last_script_end] + AUDIO_JS + "\n" + html[last_script_end:]

    # 更新 key hint 提示（加上 M 键说明）
    html = html.replace(
        "H 显示/隐藏提示",
        "H 显示/隐藏提示<br>\n  M 静音/取消静音"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(output_path) // 1024
    print(f"\n✅ 已生成: {output_path} ({size_kb} KB)")
    print(f"   包含音效的幕次: {found}")
    return True


def main():
    parser = argparse.ArgumentParser(description="将 AI 音效注入 HTML PPT")
    parser.add_argument("--input", default="index.html")
    parser.add_argument("--output", default="index_with_audio.html")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_dir, args.input)
    output_path = os.path.join(base_dir, args.output)

    if not os.path.exists(html_path):
        print(f"❌ 找不到 {html_path}")
        return

    print(f"🎵 音效注入器 · 咔嚓咔嚓号小火车")
    print(f"   输入: {html_path}")
    print(f"   输出: {output_path}\n")

    ok = inject(html_path, output_path, base_dir)
    if ok:
        print(f"\n🚀 下一步：")
        print(f"   用浏览器打开 {output_path}")
        print(f"   或运行本地服务器: python3 -m http.server 8080")
        print(f"   ⚠️  注意：音频需要 HTTP 服务器才能正常播放（不能直接双击打开）")


if __name__ == "__main__":
    main()
