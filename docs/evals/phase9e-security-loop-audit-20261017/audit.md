# Phase 9e security-loop follow-up audit

This is a sanitized correction of the historical
`phase9-bench-real-20261016T210350514549Z` evidence, not a new real benchmark.
Original reports and `.cache/phase9e-results/` were read only. `loop-audit.json`
contains counts and SHA-256 hashes of the 14 input files, without source code,
diffs, prompts or raw tool output. The `quality/` projections and `quality.json`
use the corrected reporting reader. Readiness remains **1/40**, with two missing
variants and 39 packages having unresolved security findings.

## Confirmed stopping condition

The former SecurityAgent branch was:

```python
elif fingerprints in seen:
    reason = "no progress"
```

It dates to Phase 5, commit `91633dc`, 1 October 2026. Phase 9e commit `5584316`
added validity rollback and retained-baseline scan reuse. A rejected candidate
therefore returned the same fingerprints, causing the old shortcut to end the
loop despite unused attempt allowance and stage time.

Saved sessions contain 44 attempts: 38 packages made one pass, one made two,
and one made four. Terminal reasons are 38 `no progress`, one clean and one
iteration limit. All 38 `no progress` exits repeat a prior fingerprint set.
Iteration outcomes are three accepted, 23 rolled back and 18 no change;
rollback causes are 12 Terraform regressions, ten new blocking findings and
one unavailable Terraform comparison. Security stages lasted 6.589–64.650
seconds; there were no deadline or exception stops. Generation-gate time was
outside the fresh security-stage budget.

For run `12a0fcfb-f1d9-41c8-9fa9-8dac962a9b6f`, the performance variant's first
iteration raises Terraform failures from one to six, restores its Terraform
files, then terminates on the unchanged six scanner findings. The security
variant similarly restores a zero-to-one Terraform regression. These are
rejected candidates, not evidence that further attempts had no possible value.

## Grounding was present

Saved JSON has **52 proposal context measurements: 44 positive and eight zero**.
Of 45 Terraform proposals, 44 are positive and one zero; seven other-file
proposals have zero context. The historical zero summary read top-level
`security_report.iterations`, while persisted proposals are nested under
`security_report.sessions[].iterations[].fixes[]`.

Concrete pointers in the read-only
`12a0fcfb-f1d9-41c8-9fa9-8dac962a9b6f.json`:

| JSON pointer | Recorded characters | Regenerated version-correct context |
|---|---:|---|
| `/packages/1/security_report/sessions/0/iterations/0/fixes/0/schema_context_chars` | 11,689 | 11,689; AWS 6.68.0 and random 3.9.1, nine schema entries |
| `/packages/2/security_report/sessions/0/iterations/0/fixes/0/schema_context_chars` | 15,452 | 15,452; AWS 5.100.0, twelve schema entries |

FixAgent passes the same context string to `user_prompt(schema_context=...)`
and records its length. The exact regenerated lengths plus the saved proposal
metadata establish that grounding was sent; this was a reporting-only bug.
The sole zero Terraform context belongs to run `9d635e37…`, security variant:
malformed HCL and syntax-only findings with no resource type to infer.
Historical reason metadata was absent and remains `unknown` in projections;
the audit does not invent schemas or retrofit reason fields.

## Reproduce the corrected quality projection

With dotenv-disabled, synthetic verification settings:

```bash
backend/.venv/bin/python -m scripts.benchmark quality \
  --results-dir docs/evals/phase9-bench-real-20261016T210350514549Z \
  --snapshots-dir .cache/phase9e-results \
  --output-dir <new-separate-output-directory>
```

The correction does not change readiness/blocking rules, models or thresholds.
Follow-up stub and injected-clock results are separate evidence and do not
predict improvements in a future author-run real comparison.
