"""CPython 순수 파이썬 모듈에 한 줄 변이를 심고 해당 CPython 테스트가 잡는 변이만 과제로 남김"""
import ast, json, random, shutil, subprocess, sys, sysconfig
from pathlib import Path

STD = Path(sysconfig.get_paths()["stdlib"])
OUT = Path(__file__).resolve().parent / "tasks"
MODULES = ["colorsys", "textwrap", "fnmatch", "shlex", "bisect", "heapq", "graphlib",
           "fractions", "calendar", "quopri", "difflib", "statistics", "ipaddress"]
PER_MODULE = 3
SEED = 20261111

SWAP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
        ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Add: ast.Sub, ast.Sub: ast.Add,
        ast.Mult: ast.FloorDiv, ast.And: ast.Or, ast.Or: ast.And}


def sites(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in SWAP:
            yield node, "cmp"
        elif isinstance(node, ast.BinOp) and type(node.op) in SWAP:
            yield node, "binop"
        elif isinstance(node, ast.BoolOp) and type(node.op) in SWAP:
            yield node, "bool"
        elif isinstance(node, ast.Constant) and type(node.value) is int and node.value in (0, 1, 2):
            yield node, "const"


def mutate_line(src_lines, node, kind):
    seg_line = node.lineno - 1
    line = src_lines[seg_line]
    if node.end_lineno != node.lineno:
        return None
    seg = line[node.col_offset:node.end_col_offset]
    if kind == "const":
        new = str(node.value + 1)
    else:
        if kind == "cmp":
            node.ops = [SWAP[type(node.ops[0])]()]
        elif kind == "binop":
            node.op = SWAP[type(node.op)]()
        else:
            node.op = SWAP[type(node.op)]()
        new = ast.unparse(node)
    if new == seg:
        return None
    return line[:node.col_offset] + new + line[node.end_col_offset:]


def run_tests(workdir, mod):
    r = subprocess.run([sys.executable, "-m", "unittest", f"test.test_{mod}"], cwd=workdir,
                       capture_output=True, text=True, timeout=120)
    return r.returncode == 0, (r.stdout + r.stderr)[-3000:]


def main():
    rng = random.Random(SEED)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    tasks = []
    for mod in MODULES:
        src_path = STD / f"{mod}.py"
        src = src_path.read_text()
        lines = src.splitlines(keepends=True)
        cand = [(n.lineno, n.col_offset, k) for n, k in sites(ast.parse(src))
                if not isinstance(n, ast.Constant) or rng.random() < 0.3]
        rng.shuffle(cand)
        kept = 0
        for lineno, col, kind in cand:
            if kept >= PER_MODULE:
                break
            tree = ast.parse(src)
            node = next((n for n, k in sites(tree) if n.lineno == lineno and n.col_offset == col and k == kind), None)
            if node is None:
                continue
            new_line = mutate_line([l.rstrip("\n") for l in lines], node, kind)
            if new_line is None:
                continue
            tid = f"{mod}-{lineno}-{col}-{kind}"
            d = OUT / tid
            d.mkdir()
            mutated = lines[:]
            mutated[lineno - 1] = new_line + "\n"
            (d / f"{mod}.py").write_text("".join(mutated))
            try:
                ok, log = run_tests(d, mod)
            except subprocess.TimeoutExpired:
                shutil.rmtree(d)
                continue
            if ok:
                shutil.rmtree(d)
                continue
            failing = sorted({l.split(" ")[1] for l in log.splitlines() if l.startswith(("FAIL: ", "ERROR: "))})
            tasks.append({"id": tid, "module": mod, "line": lineno, "kind": kind,
                          "original": lines[lineno - 1].rstrip("\n"), "mutant": new_line,
                          "failing_tests": failing[:5], "log_tail": log[-1500:]})
            kept += 1
    (OUT / "tasks.json").write_text(json.dumps(tasks, indent=1))
    print(len(tasks), "tasks", sys.version.split()[0])


if __name__ == "__main__":
    main()
