"""결과 파일에서 Table 1, 짝 비교, 모듈별 해결률을 계산하고 Kaggle 카드 이미지(560x280)를 그리는 도구

재실행에서도 행이 남지 않은 과제(25분 제한 초과)는 처음 실행의 중단 행을 그대로 씁니다.
"""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = [t["id"] for t in json.load(open(ROOT / "bench" / "batch1.json"))]
TAGS = ["gemma-4-31b-it__blind", "gemma-4-31b-it__tests", "gemma-4-26b-a4b-it__blind", "gemma-4-26b-a4b-it__tests"]


def load(tag):
    d = ROOT / "runs" / tag
    rows = {}
    crash = d / "results-crash.jsonl"
    if crash.exists():
        for l in crash.read_text().splitlines():
            r = json.loads(l); r["stopped"] = True; rows[r["id"]] = r
    for l in (d / "results.jsonl").read_text().splitlines():
        r = json.loads(l); r["stopped"] = r["exit"].startswith("crash"); rows[r["id"]] = r
    return {i: rows[i] for i in TASKS if i in rows}


def main():
    data = {t: load(t) for t in TAGS}
    out = ["| Model | Condition | Resolved | Exact line repair | Same AST as original | Agent submitted | Step limit | Stopped early | Mean steps |",
           "|---|---|---|---|---|---|---|---|---|"]
    summary = {}
    for tag, rows in data.items():
        m, c = tag.split("__")
        rs = list(rows.values())
        n = len(rs)
        res = sum(r["resolved"] for r in rs)
        summary[tag] = res
        out.append(f"| {m} | {c} | {res}/{n} | {sum(r['exact_revert'] for r in rs)} | {sum(r['ast_revert'] for r in rs)} | "
                   f"{sum(r['exit'] == 'Submitted' for r in rs)} | {sum(r['exit'] == 'LimitsExceeded' for r in rs)} | "
                   f"{sum(r['stopped'] for r in rs)} | {sum(r['steps'] for r in rs) / n:.1f} |")
    print("\n".join(out))
    print()
    for m in ["gemma-4-31b-it", "gemma-4-26b-a4b-it"]:
        b, t = data[f"{m}__blind"], data[f"{m}__tests"]
        both = [i for i in TASKS if i in b and i in t and not b[i]["stopped"] and not t[i]["stopped"]]
        rb = sum(b[i]["resolved"] for i in both); rt = sum(t[i]["resolved"] for i in both)
        ob = sum(b[i]["resolved"] and not t[i]["resolved"] for i in both)
        ot = sum(t[i]["resolved"] and not b[i]["resolved"] for i in both)
        print(f"paired {m}: n={len(both)} blind={rb} tests={rt} only_blind={ob} only_tests={ot}")
    mod = defaultdict(Counter)
    for rows in data.values():
        for r in rows.values():
            mod[r["module"]]["n"] += 1; mod[r["module"]]["ok"] += r["resolved"]
    print("modules:", {k: f"{v['ok']}/{v['n']}" for k, v in sorted(mod.items(), key=lambda kv: -kv[1]['ok'] / kv[1]['n'])})
    print("stopped total:", sum(r["stopped"] for rows in data.values() for r in rows.values()))
    if "--card" in sys.argv:
        card(summary, sys.argv[sys.argv.index("--card") + 1])


def card(summary, path):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1120, 560
    im = Image.new("RGB", (W, H), "#0f1720")
    d = ImageDraw.Draw(im)
    f = lambda s, b=False: ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if b else "/System/Library/Fonts/Supplemental/Arial.ttf", s)
    d.text((48, 40), "Run the tests or read the code?", font=f(46, True), fill="#ffffff")
    d.text((48, 100), "Gemma 4 agents on 20 seeded CPython bugs", font=f(28), fill="#9fb3c8")
    groups = [("Gemma 4 31B", "gemma-4-31b-it"), ("Gemma 4 26B A4B", "gemma-4-26b-a4b-it")]
    x0, base, scale = 330, 500, 15
    d.text((48, 170), "Tasks resolved (of 20)", font=f(24), fill="#9fb3c8")
    for gi, (label, m) in enumerate(groups):
        gx = x0 + gi * 380
        for bi, (cond, col) in enumerate([("blind", "#4fb3ff"), ("tests", "#ffb347")]):
            v = summary[f"{m}__{cond}"]
            bx = gx + bi * 140
            d.rectangle([bx, base - v * scale, bx + 110, base], fill=col)
            d.text((bx + 55, base - v * scale - 40), str(v), font=f(32, True), fill="#ffffff", anchor="mt")
            d.text((bx + 55, base + 8), cond, font=f(22), fill="#cfd8e3", anchor="mt")
        d.text((gx + 125, 215), label, font=f(26, True), fill="#ffffff", anchor="mt")
    d.rectangle([48, 230, 72, 254], fill="#4fb3ff"); d.text((84, 228), "no test access", font=f(22), fill="#cfd8e3")
    d.rectangle([48, 270, 72, 294], fill="#ffb347"); d.text((84, 268), "can run tests", font=f(22), fill="#cfd8e3")
    im.resize((560, 280), Image.LANCZOS).save(path)
    im.save(path.replace(".png", "@2x.png"))
    print("card", path)


if __name__ == "__main__":
    main()
