"""변이 과제 하나를 mini-swe-agent와 Gemma 4로 풀고 숨긴 테스트로 채점하는 실행기"""
import argparse, ast, difflib, json, re, shutil, subprocess, sysconfig, tempfile, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from minisweagent.agents.default import DefaultAgent
from minisweagent.environments.docker import DockerEnvironment
from minisweagent.models.litellm_model import LitellmModel

ROOT = Path(__file__).resolve().parent
PKG = ROOT.parent / ".venv"
TESTS = ROOT / "cpython" / "test"
IMAGE = "python:3.14-slim"
STD = Path(sysconfig.get_paths()["stdlib"])
LOCK = threading.Lock()
LIB = "/usr/local/lib/python3.14"
CFG = yaml.safe_load(next(PKG.glob("lib/python*/site-packages/minisweagent/config/mini.yaml")).read_text())


def symptom(task):
    lines = [l for l in task["log_tail"].splitlines() if l.strip()]
    err = next((l for l in reversed(lines) if re.match(r"^\w*(Error|Exception)\b", l.strip())), lines[-1])
    test = task["failing_tests"][0] if task["failing_tests"] else "a test"
    return f"`{test}` fails with: {err.strip()[:300]}"


def prompt(task, cond):
    mod = task["module"]
    text = (f"The file /work/{mod}.py is a copy of the Python standard library module `{mod}`. "
            f"Python code that runs in /work imports this copy. The copy has one bug. "
            f"A user reports this symptom: {symptom(task)}\n"
            f"Fix the bug in /work/{mod}.py. Change only that file. Make the smallest correct change.")
    if cond == "tests":
        text += f"\nYou can run the official tests with: cd /work && python -m unittest test.test_{mod}"
    else:
        text += "\nThe official test suite is not available. Write your own small checks if you need them."
    return text


def hidden_eval(work, mod):
    try:
        r = subprocess.run(["docker", "run", "--rm", "-v", f"{work}:/work:ro", "-v", f"{TESTS}:{LIB}/test:ro",
                        "-w", "/work", IMAGE, "python", "-m", "unittest", f"test.test_{mod}"],
                       capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return False
    return r.returncode == 0


def run(task, cond, model_name, out_dir, step_limit):
    mod = task["module"]
    work = Path(tempfile.mkdtemp(prefix="g4w-", dir=ROOT / ".work"))
    shutil.copy(ROOT / "tasks" / task["id"] / f"{mod}.py", work / f"{mod}.py")
    args = ["--rm", "-v", f"{work}:/work"]
    if cond == "tests":
        args += ["-v", f"{TESTS}:{LIB}/test:ro"]
    env = DockerEnvironment(image=IMAGE, cwd="/work", run_args=args, timeout=120,
                            env=CFG["environment"].get("env", {}))
    env.execute({"command": f"rm -f {LIB}/{mod}.py {LIB}/__pycache__/{mod}.*.pyc"})
    model = LitellmModel(model_name=model_name,
                         model_kwargs={"drop_params": True, "temperature": 0.0, "num_retries": 6},
                         observation_template=CFG["model"]["observation_template"],
                         format_error_template=CFG["model"]["format_error_template"],
                         cost_tracking="ignore_errors")
    traj = out_dir / f"{task['id']}.traj.json"
    agent = DefaultAgent(model, env, system_template=CFG["agent"]["system_template"],
                         instance_template=CFG["agent"]["instance_template"],
                         step_limit=step_limit, cost_limit=0, output_path=traj)
    t0 = time.time()
    try:
        info = agent.run(prompt(task, cond))
        exit_status = info.get("exit_status", "")
    except Exception as e:
        exit_status = f"crash:{type(e).__name__}:{str(e)[:200]}"
    secs = time.time() - t0
    try:
        env.cleanup()
    except Exception:
        pass
    fixed = (work / f"{mod}.py").read_text()
    orig_line = task["original"]
    lines = fixed.splitlines()
    exact = len(lines) >= task["line"] and lines[task["line"] - 1] == orig_line
    passed = hidden_eval(work, mod)
    orig_src = (ROOT / "tasks" / task["id"] / f"{mod}.py").read_text().splitlines()
    changed = sum(1 for a, b in zip(orig_src, lines) if a != b) + abs(len(orig_src) - len(lines))
    mutant_src = (ROOT / "tasks" / task["id"] / f"{mod}.py").read_text()
    try:
        ast_revert = ast.dump(ast.parse(fixed)) == ast.dump(ast.parse((STD / f"{mod}.py").read_text()))
    except SyntaxError:
        ast_revert = False
    diff = "".join(difflib.unified_diff(mutant_src.splitlines(True), fixed.splitlines(True), n=0))[:4000]
    shutil.rmtree(work, ignore_errors=True)
    return {"id": task["id"], "module": mod, "kind": task["kind"], "cond": cond, "model": model_name,
            "resolved": passed, "exact_revert": exact, "ast_revert": ast_revert, "diff": diff, "lines_changed": changed,
            "steps": agent.n_calls, "exit": exit_status, "seconds": round(secs, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--cond", choices=["blind", "tests"], required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--tasks-file", default=str(ROOT / "tasks" / "tasks.json"))
    a = ap.parse_args()
    (ROOT / ".work").mkdir(exist_ok=True)
    tasks = json.loads(Path(a.tasks_file).read_text())
    if a.only:
        tasks = [t for t in tasks if t["id"] in a.only.split(",")]
    tag = f"{a.model.split('/')[-1]}__{a.cond}"
    out_dir = ROOT.parent / "runs" / tag
    out_dir.mkdir(parents=True, exist_ok=True)
    res_file = out_dir / "results.jsonl"
    done = {json.loads(l)["id"] for l in res_file.read_text().splitlines()} if res_file.exists() else set()
    def one(t):
        r = run(t, a.cond, a.model, out_dir, a.steps)
        with LOCK, res_file.open("a") as f:
            f.write(json.dumps(r) + "\n")
        print(json.dumps({k: r[k] for k in ("id", "resolved", "ast_revert", "steps", "seconds")}), flush=True)

    todo = [t for t in tasks if t["id"] not in done]
    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(one, todo))


if __name__ == "__main__":
    main()
