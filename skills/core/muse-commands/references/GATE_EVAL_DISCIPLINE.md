# Gate Eval Discipline

Applies to every automated judgment in a project. This file calls them all "gates": identity
checks, output quality or fidelity checks, semantic checks on generated text, classifiers that
pick an action or an expression, voice checks, and so on. Whenever any lane creates a gate or
changes its threshold, follow these five rules.

## 1. Freeze the exam set (so tuning does not turn into cheating)

- Split samples into two sets: a **tuning set** (thresholds and prompts are tuned only here) and
  an **exam set** (frozen, judged once).
- Record the seed, the sample list and the gate version in the report. If the exam set changes,
  give it a new id and stop comparing against old results.
- Never change a test to make it pass. A temporary downgrade needs a written expiry condition and
  is reported to the orchestrator in the same round.

## 2. Report errors separately

- Report **misses** (should have blocked, did not) and **false blocks** (should have passed, was
  blocked) separately, broken down by category. One pass rate is not enough.
- Report probability-like scores (similarity, confidence) as a distribution, separate from hit
  rates.
- Pipelines such as voice or generation follow the same rule: the success-rate denominator is the
  number of attempts, and failures are split by cause (balance, rate limit, concurrency, conflict,
  upstream 5xx, timeout).

## 3. Do not leak the answer

- Strip file names, ids, paths and action or expression names from the judge's input. A file
  named `wave_happy.mp4` writes the answer into the question. Give only images, audio, text and a
  feature list.
- Ground truth is labelled **blind**, by an independent subagent or a different model that cannot
  see the gate's verdicts. Disagreements go to a human.
- Mark older results that saw leaked information as "possibly leaked" and rerun a clean version on
  the tuning set.

## 4. Keep every verdict (data for a smaller model later)

- Each time a gate judges, append one JSONL line: time, gate name and version, input reference
  (path or hash, never the raw content), verdict, score, latency, cost.
- Store test and QA runs in a per-gate log, for example
  `<evidence-root>/<lane>/<gate>/judgments/*.jsonl`.
- Whether to store **production user content** (user-written descriptions, uploaded images), and
  for how long, needs a privacy review first, and the privacy policy must say so. Until then, log
  only verdicts from your own test accounts and QA.

## 5. Distil (after launch, once volume exists)

- Once a pay-per-call gate has enough logged verdicts (suggested: 2,000 or more with blind
  labels), run one small experiment: a large model labels, a small local model is trained, and the
  two are compared side by side on the frozen exam set.
- Replace the original gate only if the small model misses no more, false-blocks no more, and is
  clearly cheaper and faster per call. Report to the orchestrator before replacing; the money and
  security review checks cost and where the data goes.

## How to check

- Report template: one-line verdict first; then tuning set / exam set / seed / gate version; a
  misses table and a false-blocks table by category; the score distribution; how leaks were
  handled; the verdict log path.
- When a review lane reviews a gate change, it checks these five rules one by one. A missing item
  must be fixed before merge.
- The orchestrator spot-checks one gate a week to confirm its verdict log is still growing.
