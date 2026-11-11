# Run the Tests or Read the Code? Gemma 4 Developer Agents on Seeded Bugs in the CPython Standard Library

## Abstract

Developer agents often get a failing test and a shell. We ask how much of their success comes from the ability to run the test suite. We built a small benchmark of 20 single-line bugs. Each bug is a mutation in a pure-Python module of the CPython standard library, and the module's own CPython tests detect it. We ran two open Gemma 4 models, gemma-4-31b-it and gemma-4-26b-a4b-it, with the mini-swe-agent scaffold in Docker. Each model solved every task under two conditions: with the official tests available, and with only a one-line bug report. The larger model resolved 14 of 20 tasks in both conditions. The smaller model resolved 12 of 20 without tests and 10 of 20 with tests. Test access did not raise the resolve rate for either model under a 12-step limit. We release the task generator, the runner, all trajectories, and the per-run results.

## 1. Introduction

A developer agent reads code, runs commands, and edits files until a task is done. Most public evaluations give the agent a repository and an issue text. The agent can usually run tests, but the evaluation reports only one number: the resolve rate. That number mixes two skills. The first skill is reading code and finding the fault. The second skill is using execution feedback, such as test output, to check a guess and try again.

For small open models this split matters. A small model that runs on one GPU or a laptop is cheap enough to call many times. If test feedback lifts its resolve rate a lot, then a team should spend effort on fast and isolated test execution. If test feedback adds little, the team should spend effort on retrieval and code reading instead.

We study this question with Gemma 4. We make three contributions:

1. A reproducible benchmark generator. It plants one-line mutations in pure-Python standard library modules and keeps only mutations that the official CPython tests detect.
2. A controlled 2 x 2 experiment: two Gemma 4 models, with and without runnable tests, on the same tasks, with the same scaffold, step limit, and temperature.
3. An analysis of where the agents fail: wrong file region, wrong repair, format errors, and step-limit exits.

## 2. Related work

SWE-bench (Jimenez et al., 2024) evaluates agents on real GitHub issues from Python repositories and grades them with the repository tests. SWE-agent (Yang et al., 2024) showed that the agent-computer interface changes results a lot. mini-swe-agent is a small version of SWE-agent. It gives the model only a bash tool, and it is the scaffold that we use. Mutation testing has a long history as a way to make controlled faults (DeMillo et al., 1978; Jia and Harman, 2011). Our tasks use the same idea: a known, single-site fault with a known fix, so we can grade both the test result and the exact repair.

Our work differs in scope. We do not build a large benchmark. We build a small, cheap, and fully reproducible one, and we use it to isolate one factor, test access, for small open models.

## 3. Benchmark

### 3.1 Source modules

We use pure-Python modules from the CPython 3.14 standard library that have a matching test module in `Lib/test`: bisect, colorsys, fnmatch, graphlib, heapq, shlex, and textwrap. The license of the standard library permits this use. The tests come from the same CPython release as the container image (Python 3.14).

### 3.2 Mutations

The generator parses each module with `ast` and lists candidate sites:

- comparison operators (`<` to `<=`, `==` to `!=`, and back),
- arithmetic operators (`+` to `-`, `*` to `//`),
- boolean operators (`and` to `or`),
- small integer constants (`0`, `1`, `2` to the next integer).

It applies one mutation per task, on one source line, with a fixed random seed. It then runs the module's CPython test file. It keeps the mutation only if the tests fail, and it drops mutations that make the tests hang for more than 120 seconds. We keep at most three tasks per module. The result is 20 tasks.

### 3.3 Task prompt

Each task prompt says that `/work/<module>.py` is a copy of a standard library module with one bug. It gives one symptom: the name of the first failing test and the last error line of the test log. In the "tests" condition, the prompt also gives the command that runs the official tests. In the "blind" condition, the test package is not present in the container, and the prompt says so.

We delete the original module file from the container's standard library before the agent starts. Thus the agent cannot use `diff` against the installed copy.

### 3.4 Grading

After the agent stops, we copy the edited file into a fresh container with the official tests and run them. A task is resolved if all tests in the module's test file pass. We also record whether the edited module has the same abstract syntax tree as the original module ("exact repair"), the number of changed lines, the number of model calls, and the exit reason.

## 4. Experimental setup

- Models: `gemma-4-31b-it` and `gemma-4-26b-a4b-it` through the Gemini API free tier.
- Scaffold: mini-swe-agent 2.4.6 with its default `mini.yaml` prompts and the bash tool. Temperature 0. Step limit 12.
- Environment: `python:3.14-slim` Docker image, one fresh container per run.
- Conditions: tests and blind, as in Section 3.3.
- Runs: 20 tasks x 2 models x 2 conditions = 80 runs, one attempt each.

The free tier allows 16,000 input tokens per minute per model. We ran one task at a time per model and condition.

## 5. Results

Table 1 shows the results for all 80 runs. A task counts as resolved only if the hidden CPython tests pass.

| Model | Condition | Resolved | Exact line repair | Same AST as original | Agent submitted | Step limit | Stopped (rate limit or time limit) | Mean steps |
|---|---|---|---|---|---|---|---|---|
| gemma-4-31b-it | blind | 14/20 | 7 | 4 | 9 | 9 | 2 | 10.5 |
| gemma-4-31b-it | tests | 14/20 | 9 | 6 | 4 | 14 | 2 | 11.3 |
| gemma-4-26b-a4b-it | blind | 12/20 | 7 | 5 | 1 | 16 | 2 | 11.6 |
| gemma-4-26b-a4b-it | tests | 10/20 | 5 | 4 | 0 | 18 | 2 | 11.8 |

The free tier stopped 24 runs with a rate-limit error. We ran these 24 runs again with one process for each model, and seven runs completed. Then we ran the remaining 17 runs again one at a time, with a time limit of 25 minutes for each run. Nine more runs completed. Eight runs stay in the table as "stopped". Three of these eight runs are on heapq-161-18-const, which hit the time limit each time. The hidden tests still grade the file that the agent left. One stopped run is resolved.

Paired comparison. We compare the two conditions only on tasks where neither run stopped. For gemma-4-31b-it there are 17 such tasks: 14 resolved in blind and 13 in tests. For gemma-4-26b-a4b-it there are 17 such tasks: 11 resolved in blind and 10 in tests. With test access, one extra task was resolved for the 31B model and two for the 26B model. Without test access, two extra tasks were resolved for the 31B model and three for the 26B model.

By module, over all four configurations, bisect and colorsys were the easiest (11 of 12 runs resolved each). heapq and textwrap were the hardest (4 of 12 each).

## 6. Discussion

Test access did not help in this setup. We see two reasons in the trajectories.

First, the step limit is small. In the tests condition, the agent spends steps on running the suite and on reading long test logs. In the blind condition, the agent reads the module and edits it sooner. The 26B model reached the step limit in most runs in both conditions, and it submitted only once.

Second, the bug report already names the failing test and the error. For a one-line fault in a short module, this symptom is often enough to find the line by reading. The tests then add context cost but little new information.

The models often did not make an exact repair. A run can pass the tests with a different fix. Thus "resolved" and "exact repair" measure different things, and we report both.

These results do not show that test feedback is useless. They show that, for small models with a short step budget and a strict token budget, the cost of running tests can be larger than the benefit. A larger step limit or a summarized test log can change this result. The sample is small (20 tasks, one attempt each), so the differences between conditions are within noise.

## 7. Limitations

- The tasks are small and synthetic. Real bugs often span several lines and files.
- The standard library is in the training data of most models. A model can recall the original line. The blind condition measures this recall together with code reading.
- One attempt per run at temperature 0. We did not measure variance.
- The free API tier limits throughput, so the benchmark has 20 tasks.
- Eight of 80 runs did not complete, because of the rate limit or the time limit. These runs count as unresolved unless the hidden tests pass on the file that the agent left.

## 8. Reproducibility

The repository contains the generator (`bench/make_tasks.py`), the runner (`bench/run.py`), the task list, the copied CPython test files, every trajectory (`runs/*/*.traj.json`), and one JSON line per run (`runs/*/results.jsonl`). `bench/stats.py` makes Table 1 and the paired comparison from these files.

## References

- Jimenez, C. E., et al. SWE-bench: Can Language Models Resolve Real-World GitHub Issues? ICLR 2024.
- Yang, J., et al. SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering. NeurIPS 2024.
- DeMillo, R. A., Lipton, R. J., and Sayward, F. G. Hints on Test Data Selection: Help for the Practicing Programmer. Computer, 1978.
- Jia, Y., and Harman, M. An Analysis and Survey of the Development of Mutation Testing. IEEE TSE, 2011.
- Gemma Team. Gemma 4 model card. Google, 2026.
