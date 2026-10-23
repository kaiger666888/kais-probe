#!/usr/bin/env python3
# blind_pack.py — kais-probe 阶段4 盲选 PK 打包
# 生成 kais-html 标准格式盲审页（严格复刻 yue2_generalize_blind.html 范本：
# GitHub-dark 配色 / 粘性头 / 判读指引 / 优良中差+★最佳 / 对照锚题 / 底部导出栏 /
# localStorage 续答 / char-code 臂位揭晓），并落 key.json 揭底台账。
#
# 用法:
#   blind_pack.py --out DIR --title "盲选 PK · newmodel vs yue2" \
#     --sub "同题同参 · 开箱默认档 · 2026-10-23" \
#     --media audio \
#     --axes "判读轴：<按模态写，如 人声质感/咬字/旋律/编曲/混音>" \
#     --arms "newmodel" --arms "yue2" \
#     --q "P1 题说明::/path/new1.flac::/path/yue2_1.flac" \
#     --q "P2 题说明::/path/new2.flac::/path/yue2_2.flac" \
#     [--ctl "/path/a.flac::/path/b.flac"]
#
# 每个 --q = "题说明::臂1文件::臂2文件..."（文件数必须等于 --arms 个数）。
# 槽位文件落盘为 p{题号}_{轨位}{ext}；臂位每题乱序（确定性种子）防位置偏差。
# 投票回传格式（导出栏复制）: "N题盲选PK P1: 轨1优 轨2差 ★轨1 | ... | CTL=同"
import argparse
import hashlib
import html
import json
import random
import shutil
from pathlib import Path

GRADE_BTNS = ["优", "良", "中", "差"]


def md5sum(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def media_tag(src: str, media: str) -> str:
    if media == "audio":
        return f'<audio controls preload="metadata" src="{html.escape(src)}"></audio>'
    if media == "video":
        return f'<video controls preload="metadata" src="{html.escape(src)}"></video>'
    return f'<img src="{html.escape(src)}" style="width:100%;border-radius:8px">'


def charcodes(s: str) -> list:
    return [ord(c) for c in s]


CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0d1117; color:#c9d1d9; font-family:-apple-system,'PingFang SC',sans-serif; padding-bottom:150px; }
.header { position:sticky; top:0; z-index:100; background:#161b22; border-bottom:1px solid #30363d; padding:14px 20px 10px; }
.header h1 { font-size:19px; color:#e6edf3; }
.header .sub { font-size:12px; color:#8b949e; margin-top:4px; }
.wrap { max-width:1000px; margin:0 auto; padding:16px; }
.guide { background:#111a24; border:1px solid #23364a; border-left:3px solid #4C9AFF; border-radius:8px; padding:12px 14px; font-size:13px; margin-bottom:16px; line-height:1.7; }
.guide b { color:#79c0ff; }
.q { background:#161b22; border:1px solid #30363d; border-radius:12px; padding:16px; margin-bottom:18px; }
.q h2 { font-size:16px; color:#e6edf3; margin-bottom:4px; }
.q .brief { font-size:12.5px; color:#8b949e; margin-bottom:12px; line-height:1.6; }
.quad { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
@media (max-width:700px){ .quad { grid-template-columns:1fr; } }
.slot { background:#0d1117; border:1px solid #30363d; border-radius:10px; padding:12px; }
.slot h3 { font-size:14px; color:#c9d1d9; margin-bottom:8px; }
audio, video { width:100%; }
img { max-width:100%; }
.rates { display:flex; gap:6px; margin-top:8px; flex-wrap:wrap; }
.rates button { background:#1a2634; color:#c9d1d9; border:1px solid #2c3e52; padding:6px 14px; border-radius:6px; cursor:pointer; font-size:13px; }
.gbtn.active[data-g="优"]{ background:#1a7f4b; border-color:#2ea86a; color:#fff; }
.gbtn.active[data-g="良"]{ background:#1f6feb; border-color:#3083ff; color:#fff; }
.gbtn.active[data-g="中"]{ background:#9e6a03; border-color:#d29922; color:#fff; }
.gbtn.active[data-g="差"]{ background:#b62324; border-color:#f85149; color:#fff; }
.sbtn.active { background:#8957e5; border-color:#a371f7; color:#fff; }
.ctl { background:#161b22; border:1px dashed #d29922; border-radius:12px; padding:14px 16px; margin-bottom:18px; }
.ctl h2 { font-size:15px; color:#d8b56a; margin-bottom:6px; }
.ctl audio, .ctl video { width:48%; }
.ctl img { width:48%; }
@media (max-width:700px){ .ctl audio, .ctl video, .ctl img { width:100%; } }
.ctl .cbtns { margin-top:10px; display:flex; gap:8px; align-items:center; }
.ctl .cbtns button { background:#1a2634; color:#c9d1d9; border:1px solid #2c3e52; padding:7px 16px; border-radius:6px; cursor:pointer; font-size:13px; }
.ctl .cbtns button.active[data-v="同"]{ background:#1a7f4b; border-color:#2ea86a; color:#fff; }
.ctl .cbtns button.active[data-v="异"]{ background:#b62324; border-color:#f85149; color:#fff; }
#ctlWarn { display:none; color:#f85149; font-weight:700; margin-top:8px; }
.qcmt { width:100%; margin-top:10px; background:#0a0e14; color:#c9d1d9; border:1px solid #23364a; border-radius:6px; padding:8px 10px; font-size:13px; }
#revealBox { display:none; background:#111a24; border:1px solid #8957e5; border-radius:10px; padding:14px; margin-bottom:18px; font-size:13px; line-height:1.8; }
#revealBtn { background:#8957e5; color:#fff; border:none; padding:9px 18px; border-radius:8px; cursor:pointer; font-size:13px; margin-bottom:16px; }
.footnote { font-size:11px; color:#667788; line-height:1.6; }
.exportbar { position:fixed; left:0; right:0; bottom:0; z-index:50; display:flex; gap:10px; align-items:center; padding:10px 14px; background:rgba(1,4,9,.94); border-top:1px solid #30363d; backdrop-filter:blur(4px); }
.exportbar textarea { flex:1; min-height:46px; background:#0a0e14; color:#7ee787; border:1px solid #30363d; border-radius:8px; padding:8px 10px; font-family:ui-monospace,monospace; font-size:12px; resize:none; }
.exportbar button { flex-shrink:0; padding:13px 18px; border:none; border-radius:9px; background:#1f6feb; color:#fff; font-weight:700; font-size:14px; cursor:pointer; }
#cpStatus { font-size:12px; color:#3fb950; width:100%; }
"""

JS = """
var LS='@LSKEY@';
var QIDS=@QIDS@;
var N=@N@;
var S=JSON.parse(localStorage.getItem(LS)||'{"g":{},"star":{},"c":{},"ctl":null,"rev":false}');
function save(){ localStorage.setItem(LS, JSON.stringify(S)); }
function rate(q,pos,g,btn){
  var k=q+'_'+pos;
  if(S.g[k]===g){ delete S.g[k]; } else { S.g[k]=g; }
  paintQ(q); updateBar(); save();
}
function setStar(q,pos,btn){
  S.star[q]=(S.star[q]===pos)?0:pos;
  paintQ(q); updateBar(); save();
}
function setCtl(v,btn){
  S.ctl=(S.ctl===v)?null:v;
  paintCtl(); updateBar(); save();
}
function setComment(q,val){ S.c[q]=(val||'').replace(/[|=]/g,' ').slice(0,80); updateBar(); save(); }
function paintQ(q){
  document.querySelectorAll('.slot[data-q="'+q+'"]').forEach(function(sl){
    var pos=sl.getAttribute('data-pos');
    sl.querySelectorAll('.gbtn').forEach(function(b){
      b.classList.toggle('active', S.g[q+'_'+pos]===b.getAttribute('data-g'));
    });
    var sb=sl.querySelector('.sbtn');
    sb.classList.toggle('active', S.star[q]==pos);
  });
  var c=document.getElementById('cmt_'+q);
  if(c && document.activeElement!==c) c.value=S.c[q]||'';
}
function paintCtl(){
  document.querySelectorAll('.cbtn').forEach(function(b){
    b.classList.toggle('active', S.ctl===b.getAttribute('data-v'));
  });
  document.getElementById('ctlWarn').style.display = (S.ctl==='异')?'block':'none';
}
function buildSummary(){
  var parts=[];
  QIDS.forEach(function(q){
    var seg=[];
    for(var p=1;p<=N[q];p++){
      var g=S.g[q+'_'+p];
      seg.push('轨'+p+(g||'?'));
    }
    if(S.star[q]) seg.push('★轨'+S.star[q]);
    if(S.c[q]) seg.push('['+S.c[q]+']');
    parts.push(q+': '+seg.join(' '));
  });
  @CTL_LINE@
  var s='@NQ@题盲选PK '+parts.join(' | ');
  if(S.rev) s+=' | 揭底已看';
  return s;
}
function updateBar(){ document.getElementById('sumbox').value=buildSummary(); }
function copySummary(){
  var t=buildSummary();
  var ta=document.getElementById('sumbox'); ta.value=t;
  var ok=function(){ document.getElementById('cpStatus').textContent='✅ 已复制，贴回群里即完成回传'; setTimeout(function(){ document.getElementById('cpStatus').textContent=''; },3000); };
  if(window.isSecureContext && navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(t).then(ok, function(){ fb(); });
  } else { fb(); }
  function fb(){ ta.focus(); ta.select(); try{ document.execCommand('copy'); }catch(e){} ok(); }
}
var REV=@REV@;
function doReveal(){
  if(S.rev){ return; }
  S.rev=true; save();
  var box=document.getElementById('revealBox');
  var h='<b>臂位揭晓</b><br>';
  QIDS.forEach(function(q){
    h+='<b>'+q+'</b>：';
    REV[q].forEach(function(v,i){
      h+='轨'+(i+1)+'='+String.fromCharCode.apply(null,v.e)+'　';
    });
    h+='<br>';
  });
  box.innerHTML=h;
  box.style.display='block';
  document.getElementById('revealBtn').style.display='none';
  updateBar();
}
QIDS.forEach(paintQ); @PAINT_CTL@
if(S.rev){ S.rev=false; } /* 揭晓不跨会话持久回放, 刷新重揭 */
updateBar();
"""


def slot_html(qid: str, pos: int, fname: str, media: str) -> str:
    rates = "".join(
        f'<button class="gbtn" data-q="{qid}" data-pos="{pos}" data-g="{g}" '
        f'onclick="rate(\'{qid}\',{pos},\'{g}\',this)">{g}</button>'
        for g in GRADE_BTNS
    )
    return (f'<div class="slot" data-q="{qid}" data-pos="{pos}">\n'
            f'  <h3>轨{pos}</h3>\n'
            f'  {media_tag(fname, media)}\n'
            f'  <div class="rates">{rates}\n'
            f'    <button class="sbtn" data-q="{qid}" data-pos="{pos}" '
            f'onclick="setStar(\'{qid}\',{pos},this)">★最佳</button>\n'
            f'  </div>\n'
            f'</div>')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="盲审打包输出目录")
    ap.add_argument("--title", required=True)
    ap.add_argument("--sub", default="", help="副标题：条件说明（同参/档位/日期）")
    ap.add_argument("--media", choices=["audio", "video", "image"], required=True)
    ap.add_argument("--axes", required=True, help="判读轴说明（写进判读指引）")
    ap.add_argument("--arms", action="append", required=True,
                    help="臂名（引擎/档位），按 --q 文件顺序声明，可多个")
    ap.add_argument("--q", dest="questions", action="append", required=True,
                    help='"题说明::臂1文件::臂2文件..."，文件数=臂数')
    ap.add_argument("--ctl", default=None, help='可选对照锚 "文件A::文件B"（同源两份）')
    args = ap.parse_args()

    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    arms = [a.strip() for a in args.arms]
    n_arms = len(arms)

    qs = []          # {id, desc, files:[(slot_pos, src, packed, md5, arm_at_pos)]}
    key_slots = []
    for qi, raw in enumerate(args.questions, 1):
        parts = [p for p in raw.split("::")]
        desc, files = parts[0].strip(), [x.strip() for x in parts[1:]]
        if len(files) != n_arms:
            raise SystemExit(f"[FAIL] 题{qi}: 文件数 {len(files)} != 臂数 {n_arms}")
        qid = f"P{qi}"
        order = list(range(n_arms))
        random.Random(f"{args.title}|{qid}").shuffle(order)  # 每题乱序防位置偏差
        slots, rev = [], []
        for pos, arm_idx in enumerate(order, 1):
            src = Path(files[arm_idx]).expanduser().resolve()
            if not src.is_file():
                raise SystemExit(f"[FAIL] 题{qi} 臂'{arms[arm_idx]}' 文件不存在: {src}")
            packed = f"p{qi}_{pos}{src.suffix.lower()}"
            shutil.copy2(src, out / packed)
            slots.append({"q": qid, "pos": pos, "arm": arms[arm_idx],
                          "source": str(src), "packed_as": packed, "md5": md5sum(out / packed)})
            rev.append({"e": charcodes(arms[arm_idx])})
        key_slots.extend(slots)
        qs.append({"id": qid, "desc": desc, "slots": slots, "rev": rev})

    ctl_html, ctl_line, paint_ctl = "", "parts.push('CTL='+(S.ctl||'?'));", "paintCtl();"
    if args.ctl:
        cfiles = [x.strip() for x in args.ctl.split("::")]
        ctl_names = []
        for ci, f in enumerate(cfiles, 1):
            src = Path(f).expanduser().resolve()
            if not src.is_file():
                raise SystemExit(f"[FAIL] 对照锚文件不存在: {src}")
            packed = f"ctl_{ci}{src.suffix.lower()}"
            shutil.copy2(src, out / packed)
            ctl_names.append(packed)
            key_slots.append({"q": "CTL", "pos": ci, "arm": "anchor",
                              "source": str(src), "packed_as": packed, "md5": md5sum(out / packed)})
        ctl_media = "".join(media_tag(n, args.media) for n in ctl_names)
        ctl_html = (f'<div class="ctl" id="q_CTL">\n'
                    f'    <h2>⚓ 对照锚题（校验用，判「异」= 本轮判读作废）</h2>\n'
                    f'    {ctl_media}\n'
                    f'    <div class="cbtns">\n'
                    f'      <span style="font-size:13px;color:#8b949e">两份是否同源：</span>\n'
                    f'      <button class="cbtn" data-v="同" onclick="setCtl(\'同\',this)">同源</button>\n'
                    f'      <button class="cbtn" data-v="异" onclick="setCtl(\'异\',this)">异源</button>\n'
                    f'    </div>\n'
                    f'    <div id="ctlWarn">⚠ 判「异」= 判读状态异常，本轮评级作废（请刷新重听/重看）</div>\n'
                    f'  </div>\n')
    else:
        ctl_html = ""
        ctl_line = ""
        paint_ctl = ""

    q_html = []
    for q in qs:
        slots = "".join(slot_html(q["id"], s["pos"], s["packed_as"], args.media)
                        for s in q["slots"])
        q_html.append(f'''
<div class="q" id="q_{q["id"]}">
  <h2>第 {q["id"][1:]} 题 · {html.escape(q["desc"])}</h2>
  <div class="brief">{n_arms} 个匿名轨位，{html.escape(" vs ".join(arms))} 中每臂恰占一个（每题臂位乱序）。</div>
  <div class="quad">{slots}</div>
  <div class="pickrow"><span class="pickbtns">
    <button class="sbtn star-null" onclick="setStar('{q["id"]}',0,this)">取消★</button>
  </span></div>
  <input class="qcmt" id="cmt_{q["id"]}" placeholder="本组意见（可选）" oninput="setComment('{q["id"]}',this.value)">
</div>''')

    lskey = "blindpk_" + out.name.replace("-", "_").replace(".", "_") + "_state"
    js = (JS.replace("@LSKEY@", lskey)
            .replace("@QIDS@", json.dumps([q["id"] for q in qs]))
            .replace("@N@", json.dumps({q["id"]: n_arms for q in qs}))
            .replace("@NQ@", str(len(qs)))
            .replace("@CTL_LINE@", ctl_line)
            .replace("@REV@", json.dumps({q["id"]: q["rev"] for q in qs}))
            .replace("@PAINT_CTL@", paint_ctl))

    verb = {"audio": "听", "video": "看", "image": "看"}[args.media]
    page = f'''<!DOCTYPE html><html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(args.title)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="header">
  <h1>🎭 {html.escape(args.title)}</h1>
  <div class="sub">{html.escape(args.sub)}</div>
</div>
<div class="wrap">
  <div class="guide">
    <b>判读指引：</b>逐轨{verb}，按 <b>优/良/中/差</b> 四档评级（可多轨同档，再点撤销）；每组标一个 <b>★最佳</b>（可取消重标）。{html.escape(args.axes)}。臂位每题独立乱序，请只凭本页判读。全部评完点底部 <b>📋 复制发回群里</b>。
  </div>
{ctl_html}{''.join(q_html)}
  <button id="revealBtn" onclick="doReveal()">🔓 评完揭晓臂位</button>
  <div id="revealBox"></div>
  <div class="footnote">槽位匿名 · 臂位映射以揭底台账 key.json（md5 图谱）为准 · 由 kais-probe blind_pack.py 生成</div>
</div>
<div class="exportbar">
  <textarea id="sumbox" readonly></textarea>
  <button onclick="copySummary()">📋 复制发回群里</button>
  <span id="cpStatus"></span>
</div>
<script>{js}</script>
</body></html>'''

    (out / "ballot.html").write_text(page, encoding="utf-8")
    key = {"title": args.title, "sub": args.sub, "media": args.media,
           "arms": arms, "slots": key_slots,
           "rev": {q["id"]: q["rev"] for q in qs}}
    kp = out / "key.json"
    kp.write_text(json.dumps(key, ensure_ascii=False, indent=2), encoding="utf-8")
    kp.chmod(0o600)  # 揭底台账保密

    print(f"[OK] kais-html 盲审页: {out / 'ballot.html'}（{len(qs)} 题 × {n_arms} 臂）")
    print(f"[秘密] 揭底台账(勿提前展示): {kp}")
    for q in qs:
        m = "  ".join(f"轨{s['pos']}←{s['arm']}" for s in q["slots"])
        print(f"  {q['id']}: {m}")


if __name__ == "__main__":
    main()
