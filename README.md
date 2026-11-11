# Run the Tests or Read the Code?

This repository has the code and data for a Kaggle paper. The paper studies Gemma 4 developer agents on seeded bugs in the CPython standard library. The paper text is in `docs/writeup.md`.

## What is here

- `bench/make_tasks.py` plants one-line mutations in pure-Python standard library modules. It keeps a mutation only when the CPython tests for that module fail.
- `bench/collect.py` reads the task folders and writes the task list.
- `bench/batch1.json` is the list of the 20 tasks in the paper.
- `bench/run.py` runs one model under one condition. The agent is mini-swe-agent, and each run uses a Docker container.
- `bench/cpython/test/` has copies of the CPython test files for the grader.
- `runs/<model>__<condition>/` has one trajectory per task (`*.traj.json`) and one JSON line per run (`results.jsonl`).

## Run the experiment

You need Python 3.13, Docker, and a Gemini API key. The free tier works, but it limits input tokens per minute. Use one worker.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export GEMINI_API_KEY=...
.venv/bin/python bench/run.py --model gemini/gemma-4-31b-it --cond tests --tasks-file bench/batch1.json --steps 12 --workers 1
```

Use `--cond blind` for the condition without tests. The runner skips tasks that already have a line in `results.jsonl`.

## License

The code in this repository uses the Apache License 2.0. The files in `bench/cpython/` and in `bench/tasks/` come from CPython and use the Python Software Foundation License.
