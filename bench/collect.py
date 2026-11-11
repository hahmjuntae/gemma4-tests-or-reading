"""과제 디렉터리에서 변이 줄과 실패 테스트를 다시 읽어 과제 목록 JSON을 만드는 도구"""
import json, subprocess, sys, sysconfig
from pathlib import Path

STD = Path(sysconfig.get_paths()["stdlib"])
ROOT = Path(__file__).resolve().parent / "tasks"


def main(out, skip):
    skip = set(skip)
    tasks = []
    for d in sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name not in skip):
        mod, line, col, kind = d.name.rsplit("-", 3)
        a = (STD / f"{mod}.py").read_text().splitlines()
        b = (d / f"{mod}.py").read_text().splitlines()
        try:
            r = subprocess.run([sys.executable, "-m", "unittest", f"test.test_{mod}"], cwd=d, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            continue
        log = (r.stdout + r.stderr)[-3000:]
        fail = sorted({l.split(" ")[1] for l in log.splitlines() if l.startswith(("FAIL: ", "ERROR: "))})
        if r.returncode == 0:
            continue
        tasks.append({"id": d.name, "module": mod, "line": int(line), "kind": kind, "original": a[int(line) - 1],
                      "mutant": b[int(line) - 1], "failing_tests": fail[:5], "log_tail": log[-1500:]})
    Path(out).write_text(json.dumps(tasks, indent=1))
    print(len(tasks))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
