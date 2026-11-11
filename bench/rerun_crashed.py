"""API 한도로 끊긴(crash) 실행만 결과 파일에서 떼어 crash 기록으로 옮기고 과제 id 목록을 출력"""
import json, sys
from pathlib import Path

tag = sys.argv[1]
f = Path(__file__).resolve().parent.parent / "runs" / tag / "results.jsonl"
rows = [json.loads(l) for l in f.read_text().splitlines()]
keep = [r for r in rows if not r["exit"].startswith("crash")]
bad = [r for r in rows if r["exit"].startswith("crash")]
with (f.parent / "results-crash.jsonl").open("a") as g:
    for r in bad:
        g.write(json.dumps(r) + "\n")
f.write_text("".join(json.dumps(r) + "\n" for r in keep))
print(",".join(r["id"] for r in bad))
