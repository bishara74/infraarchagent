# Phase 10f — final benchmark and requirement closure

Computed from immutable committed JSON. [Calculations](calculations.json) retain exact values; [input manifest](input-manifest.json) records source SHA-256 values. Source summaries were checked against per-package records rather than copied.

## Final reported round

**15/58 (25.86%; 25.9% rounded)** strict checks passed; Wilson 95% CI **16.35–38.38%**. Levels 1–3: **14/30**; levels 4–5: **1/28**. Two variants are missing from the twenty-run schedule. Six packages carry `plan_conformance_conflict`; 43 require review. This is static scan/validation readiness, not cloud deployment success.

| Comparator | Passed/generated | Fisher two-sided p |
|---|---:|---:|
| corrected early pool | 42/120 | 0.23578014 |
| early round 2 | 19/60 | 0.54511520 |
| two later blocking-guard rounds | 22/116 | 0.32827896 |

The package-level Wilson and Fisher calculations are descriptive. Packages share plans/runs and scenarios recur across development revisions. These are not independent held-out trials or evidence of causal improvement. The comparator 22/116 contains only the two later blocking-guard rounds; including the first blocking round would change its denominator.

## Development iterations on the same registered scenarios

| Round suffix | Role | Passed/generated | Missing observed variants |
|---|---|---:|---:|
| [20261020T234203035108Z](../phase9-bench-broad-20261020T234203035108Z/summary.md) | early round 1 | 24/60 | 0 |
| [20261021T200436165739Z](../phase9-bench-broad-20261021T200436165739Z/summary.md) | early round 2 | 19/60 | 0 |
| [20261027T015443795826Z](../phase9-bench-broad-20261027T015443795826Z/summary.md) | 10b blocking guard | 7/60 | 0 |
| [20261027T155607468680Z](../phase9-bench-broad-20261027T155607468680Z/summary.md) | 10c blocking guard | 11/59 | 1 |
| [20261027T205119472235Z](../phase9-bench-broad-20261027T205119472235Z/summary.md) | 10d blocking guard | 11/57 | 3 |
| [20261028T020956988464Z](../phase9-bench-broad-20261028T020956988464Z/summary.md) | 10e aborted, excluded | 8/27 | 0 |
| [20261028T125056656606Z](../phase9-bench-broad-20261028T125056656606Z/summary.md) | 10e final detect-only | 15/58 | 2 |

All rounds record scenario hash `285bcb48c0d569bf06bd6b06d3a5cef52e28c0970ba6662ddc5380fafb6c288f` and registration commit `7884c2f251c02737e02c04a4b3bd109e440f60ce`. The published early pool is 43/120. The committed exposure audit identifies one passing public-to-internal flip, yielding confirmed-only 42/120 (35.0%); unresolved original exposure leaves a 41–42/120 bound. Historical labels and files are unchanged.

The aborted first 10e attempt settled nine runs and captured 27 packages, eight passing. Run 10 could not be observed to settlement; later scheduled rows are not observed executions. Its 8/27 (29.63%) is excluded, never pooled with the final round. The author reported a native `double free or corruption (fasttop)` server abort without a Python traceback, then one repeat with `PYTHONFAULTHANDLER=1` that completed without a crash. The supplied Phase 10f prompt is the provenance for this observation; the frozen benchmark does not include a native crash log or prove its root cause.

## Deadline and routing differences

| Round | Started fix iterations | Before candidate | Deadline-only rollback | Multiple-cause deadline rollback | Iteration-deadline reason records | Repair deadline stops before/after security | Generation-gate deadline outcomes |
|---|---:|---:|---:|---:|---:|---:|---:|
| 20261020T234203035108Z | 163 | 0 | 13 | 8 | 21 | 0/0 | 0 |
| 20261021T200436165739Z | 172 | 0 | 6 | 10 | 16 | 0/0 | 0 |
| 20261027T015443795826Z | 209 | 1 | 1 | 1 | 7 | 0/0 | 0 |
| 20261027T155607468680Z | 188 | 1 | 3 | 9 | 18 | 0/0 | 0 |
| 20261027T205119472235Z | 184 | 1 | 4 | 10 | 15 | 0/0 | 0 |
| 20261028T020956988464Z | 79 | 0 | 6 | 2 | 8 | 0/0 | 0 |
| 20261028T125056656606Z | 178 | 26 | 12 | 4 | 42 | 1/2 | 6 |

Counting units remain separate and may overlap; do not sum columns into a failure or recovered-pass count. Measurements come from recorded event measurement rows and match the committed measurements aggregate, including partial and missing-package attempts. The aborted attempt has additional events outside its 27 settled package snapshots; the counting units must not be conflated.

**Routing qualification:** 426 distinct LLM call IDs are recorded. Cerebras served 305; Near AI 35, CoreWeave 16, Nebius 2 and Groq 4. Another 64 have no recorded provider. Non-Cerebras routing is **57/362 (15.75%) among known-provider calls**, or **57/426 (13.38%) of all recorded calls**; unknown is **64/426 (15.02%)**. Thus “about 16% of calls” requires the known-provider denominator. Deduplicate `results.runs[].telemetry` by `call_id` (fallback `id`) for kind `llm`; unknown values never establish a provider.

## Historical safe-refusal qualification

The committed [Phase 10d diagnosis](../phase10d-diagnosis/README.md) and D-65 record seven previously passing low-complexity packages containing file reads now refused by the mandatory guard. This is a historical diagnosis statement, not seven recovered passes or a correction to today’s denominator. Its raw historical source snapshots are uncommitted and the source-free package projection does not enumerate those seven file-input identities. **The count seven cannot be independently recomputed from the committed inputs available here**; it is disclosed with that evidence limit. The one confirmed early exposure-flip pass is independently recomputed from the committed audit JSON.

## Requirement closure

**46 met / 12 partly met / 1 not met / 0 unverified**, covering 59 requirements/use cases after scoped NFR-04 closure. No proposed requirement or revised PR-03 threshold is adopted.

NFR-04 is met for the author-recorded clean Ubuntu 24.04.5 WSL scope at revision `e6ac33785e3a022550b9c3255c87b3dc194838b0`: seven installation/build steps exit zero, health reports a compatible schema, and the synthetic stub run has three `checks_passed` labels. The author’s later checklist records all nine listed checks passing in Chrome 156.0.8078.73 and Firefox 159.0. Trivy 0.69.3 SHA-256 `8266084a71d2e6a2333bc2c69b91c93c26dee9ef39ac2587ace2df54cc9b746b` is recorded as identical to development.

`outcomes.json` retains `stub_passed_browser_checks_pending`; the later README supplies completed manual browser checks. Both remain immutable. Limits: synthetic model responses; WSL rather than bare-metal/VM Ubuntu; Edge/Safari untested; optional Helm/hadolint/ansible-lint/promtool absent; manual retry-with-feedback and screenshots in both OS colour schemes omitted. This is not a real-provider or cloud deployment demonstration.

PR-03 remains **not met** against the approved ≤1.5× isolated baseline. Recomputed from each set’s first isolated PR-03 duration and the three subsequent concurrent durations, final-set ratios are 2.024947737190979 / 1.9599465459073915 / 1.9008490768807509 and 1.6624905968424453 / 2.0215062779437973 / 1.8348503001487426. CPU-heavy scanners/Terraform contend on the recorded i5/approximately 8 GB WSL host; uncontrolled host load prevents exact causal attribution.

## Reproduction

Use Python’s standard library and the existing `scripts.phase9b_stats.wilson` and `fisher` helpers. Package counts come from `quality/<run>/<variant>.json`, grouped by complexity; missing variants use runs with quality snapshots rather than preallocated schedule rows. The aborted attempt has ten started runs, nine settled runs with quality snapshots and ten unstarted slots; its table reports missing variants only within those nine snapshot-bearing runs. The early correction sums `profiles.strict.corrected_passes` for the two early folders in the committed exposure-audit JSON. Exact derived observations and source paths are in the adjacent JSON reports.

```bash
cd backend
.venv/bin/python - <<'PY'
import hashlib
import json
from collections import Counter
from pathlib import Path
from scripts.phase9b_stats import fisher, wilson

root = Path.cwd().parent
report = root / 'docs/evals/phase10f-final-report'
manifest = json.loads((report / 'input-manifest.json').read_text())['inputs']
for path, expected in manifest.items():
    assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected

recorded = json.loads((report / 'calculations.json').read_text())
for row in recorded['rounds']:
    directory = root / row['folder']
    packages = [json.loads(p.read_text())
                for p in (directory / 'quality').glob('*/*.json')]
    passed = sum(p['status'] == 'checks_passed' for p in packages)
    assert (passed, len(packages)) == (row['passed'], row['packages'])
    levels = {low: [p for p in packages if (p['complexity'] <= 3) == low]
              for low in (True, False)}
    print(directory.name, passed, len(packages),
          [(sum(p['status'] == 'checks_passed' for p in group), len(group))
           for group in levels.values()])
    runs = json.loads((directory / 'results.json').read_text())['runs']
    calls = {t.get('call_id') or t.get('id'): t
             for run in runs for t in run.get('telemetry', [])
             if t.get('kind') == 'llm' and (t.get('call_id') or t.get('id'))}
    print('providers', Counter(t.get('served_by') or 'unknown'
                               for t in calls.values()))
    events = json.loads((directory / 'events.json').read_text())
    measurements = [e['measurement'] for e in events
                    if isinstance(e.get('measurement'), dict)]
    iterations = [m for m in measurements
                  if m['stage'] == 'security_iteration_verification']
    print('before candidate', sum('iteration_deadline' in m.get('reasons', [])
          and m.get('candidate_created') is False for m in iterations))
    print('iteration deadlines', sum('iteration_deadline' in m.get('reasons', [])
                                    for m in iterations))
    print('generation gate deadlines', sum(m['stage'] == 'generation_gate'
          and m.get('outcome') == 'deadline' for m in measurements))

print('final rate / Wilson', 15 / 58, wilson(15, 58))
for passed, total in ((42, 120), (19, 60), (22, 116)):
    print('Fisher', passed, total, fisher(15, 58, passed, total))
for row in recorded['pr03']:
    runs = json.loads((root / row['source']).read_text())['runs']
    selected = [r for r in runs if r['measurement'] == 'pr03']
    ratios = [r['seconds'] / selected[0]['seconds'] for r in selected[1:]]
    assert ratios == row['ratios']
    print('PR-03', ratios)
PY
```

Phase 10f verification is recorded [separately](../phase10f-verification/README.md); collection counts never establish execution success.
