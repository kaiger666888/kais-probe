#!/usr/bin/env python3
# blind_pack.py — kais-probe 阶段4 盲选 PK 打包
# 把各引擎产物匿名化为槽位 (A/B/C...)，生成盲审投票页 ballot.html + 揭底台账 key.json
# 用法:
#   blind_pack.py --out /home/kai/shared/probes/xxx/blind \
#     --entry "yue2:/path/a.flac" --entry "newmodel:/path/b.flac" \
#     [--title "盲审页标题"] [--note "每槽位补充说明"]
# 揭底前 key.json 不给 Kai 看；投票结束后用它对照槽位。
import argparse
import hashlib
import html
import json
import shutil
from pathlib import Path

SLOTS = "ABCDEFGH"

MEDIA_EXT = {
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".webp": "image", ".gif": "image",
    ".mp4": "video", ".webm": "video", ".mov": "video",
    ".flac": "audio", ".wav": "audio", ".mp3": "audio", ".ogg": "audio",
    ".glb": "model", ".gltf": "model",
}


def md5sum(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def media_tag(path: Path) -> str:
    kind = MEDIA_EXT.get(path.suffix.lower())
    name = html.escape(str(path))
    if kind == "image":
        return f'<img src="{name}" style="max-width:90%">'
    if kind == "video":
        return f'<video src="{name}" controls style="max-width:90%"></video>'
    if kind == "audio":
        return f'<audio src="{name}" controls></audio>'
    return f'<a href="{name}">下载产物 ({html.escape(path.suffix)})</a>'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="盲审打包输出目录")
    ap.add_argument("--entry", action="append", required=True,
                    help='打包条目 "引擎名:产物路径"，可多次')
    ap.add_argument("--title", default="盲选 PK")
    ap.add_argument("--note", default="")
    args = ap.parse_args()

    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    slots = []
    for i, raw in enumerate(args.entry):
        name, _, path_str = raw.partition(":")
        src = Path(path_str.strip()).expanduser().resolve()
        if not src.is_file():
            raise SystemExit(f"[FAIL] 产物不存在: {src}")
        slot = SLOTS[i]
        dst = out / f"slot_{slot}{src.suffix.lower()}"
        shutil.copy2(src, dst)
        slots.append({
            "slot": slot, "engine": name.strip(), "source": str(src),
            "packed_as": dst.name, "md5": md5sum(dst),
        })

    key = out / "key.json"
    key.write_text(json.dumps({"title": args.title, "slots": slots},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        (out / "key.json").chmod(0o600)  # 揭底前保密
    except OSError:
        pass

    rows = []
    for s in slots:
        p = out / s["packed_as"]
        rows.append(f"""
  <div class="card">
    <h2>槽位 {s['slot']}</h2>
    {media_tag(p)}
    <p class="muted">{html.escape(args.note)}</p>
  </div>""")

    ballot = out / "ballot.html"
    ballot.write_text(f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>{html.escape(args.title)}</title><style>
body{{font-family:system-ui,sans-serif;background:#111;color:#eee;margin:2rem}}
.card{{background:#1c1c1c;border-radius:12px;padding:1rem 1.5rem;margin:1.5rem 0}}
h2{{color:#7cc4ff}} .muted{{color:#888;font-size:.85rem}}
</style></head><body>
<h1>{html.escape(args.title)}</h1>
<p>匿名槽位，请直接在 chat 里按题投票（例: P1: A / P2: B）。投票结束前勿索要 key.json。</p>
{''.join(rows)}
</body></html>""", encoding="utf-8")

    print(f"[OK] 打包 {len(slots)} 槽位 → {out}")
    print(f"[OK] 盲审页: {ballot}")
    print(f"[秘密] 揭底台账(勿提前展示): {key}")
    for s in slots:
        print(f"  槽位 {s['slot']} ← {s['engine']}  ({s['md5'][:8]}…)")


if __name__ == "__main__":
    main()
