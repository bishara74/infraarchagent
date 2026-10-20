# Phase 9h runtime attribution (PR-01, PR-05, FR-P-04, NFR-01)

This investigation and implementation make no real LLM requests and do not read
dotenv. Historical evaluation directories, cached results and the supplied
smoke terminal log are read-only. No raw terminal logs are included here.

## Findings

PR-01 requires a median ≤300 seconds across ten real runs under normal provider
conditions. A3 has a 134.67-second median; smoke has a 266.48-second median over
only three runs. Smoke is below the numeric threshold but cannot establish full
PR-01 compliance; its slowest run took 332.78 seconds.

Security iteration verification excludes fixer LLM calls. Its median increased
10.37 → 36.46 seconds: Terraform verification 0.003 → 12.97 seconds; candidate
scanner batches 7.68 → 17.76 seconds. These are independent medians, not an
additive decomposition. Completed partial-group evaluations increased 11/115
iterations → 28/34 iterations. A3 rejected 124/140 security proposals for
schema:file.missing; smoke accepted 47/49 proposals before verification. The 9g
fixer schema correction exposes more downstream local work.

Security fixer output-token medians decreased 3625.5 → 2297. A3 proposal records
are not established attempt counts and do not retain latency/reasoning counts.
Smoke's 49 recorded security attempts have median latency 1.58 seconds. The
separate terminal excerpt contains 68 successful calls, all recording effort low,
nonzero reasoning counts (median 212, range 73–535) and serving provider Cerebras.
It is partial coverage, not a full-benchmark latency distribution. A3 reasoning
tokens remain unknown. Recorded low effort plus offline wire tests establish
that the legacy false capability default does not suppress configured effort.

Some local tool durations also increased: final scans 5.30 → 7.29 seconds;
generation-gate init 9.44 → 13.07 and validate 5.46 → 8.76 seconds. Load is
plausible but the historical records cannot distinguish it exactly from content
and scheduling differences. The increase is not uniform across local and LLM
stages.

## Counterfactual estimate, not a measured speedup

Use each package's final-scan duration as a proxy for avoided repair scans:
two batches for no_improvement, one for invalid_patch, none for improvements.
Cap savings by each repair duration minus summed LLM attempt times, propagate
through the generator barrier, and recompute the latest parallel variant finish.
This avoids summing savings across parallel branches or double-counting the
generation repair nested inside its gate.

| Smoke prompt | Recorded seconds | Estimated after scan short-circuit |
|---|---:|---:|
| ECS | 266.48 | 239.74 |
| EKS | 332.78 | 297.99 |
| Static site | 218.33 | 201.85 |
| Median | 266.48 | 239.74 |

Estimated median saving: 26.75 seconds (about 10%), avoiding 34 scan batches
across 20 rounds. Proxy factors 0.5–1.5 produce medians 252.95–227.80 seconds.
This is sensitivity analysis, not a confidence interval. Saved outcomes, later
stage durations and inputs are held fixed; changed scheduling and deadline
outcomes can invalidate the projection. The telemetry addition has no algorithmic
speedup and adds collection/publication overhead. The replay command measures
local collection overhead only, not database publication or full PR-01.

## Further options (proposed only)

If a later ten-run median exceeds 300 seconds, consider sharing successful scan
results for identical complete package snapshots within the same run/variant
and scanner/policy configuration. CandidateGuard already has a per-instance
cache; any proposal must demonstrate reuse beyond that cache. Candidate-dependent
checks could also be reused for duplicate partial-group candidates while
baseline-dependent comparisons are repeated. Keep group accounting, ordering,
limits and all deadline checks unchanged. Unchanged individual files alone are
not sufficient: Terraform, Helm and policy checks can depend on other files.

## Verification

Fixed-input replay used the three original packages from smoke ECS run
3951c593-06e8-4335-91f1-fb63c3b13ffd, fresh workspaces, and one repetition of the
same cohort per configuration. Baseline application source was extracted from
84c0198 into a temporary directory. Checkov 3.3.21, Trivy 0.69.3 and Terraform
1.16.4 were identical across all six runs, as were the input SHA-256 and the
finding/validation outcomes. No test/lint jobs overlapped these replays.

| Application / collection | Sequential cohort seconds | Three-package concurrent cohort seconds |
|---|---:|---:|
| Before (84c0198), collection unavailable | 27.225 | 20.582 |
| Current, collection off | 27.783 | 19.919 |
| Current, collection on | 27.052 | 18.428 |

The current collection-on cohorts contain 15 tool-invocation records each (three
Checkov, three Trivy, three scanner Terraform validate, three Terraform init,
three initialized Terraform validate), plus enclosing scan/verification spans.
There were no skipped Terraform checks. Finding counts by cost/performance/
security were 22/10/16 and failed validation checks 0/1/1 in every configuration.
These are raw tool outcomes, not readiness labels.

CPU busy fractions during the cohorts ranged 20.7–45.4%; starting one-minute
load ranged 1.28–3.87, partly reflecting preceding replay work. Physical host
load was not controlled. One ordered cohort per configuration cannot quantify
small instrumentation overhead, establish a speedup, or isolate cache warming
and load variation. The replay does not include database publication or the
remediation loop, and does not validate the counterfactual PR-01 estimate.
It shows no obvious persistent tool-path slowdown for these fixed inputs.
Detailed derived JSON is kept untracked under .cache/runtime-attribution/;
historical benchmark inputs and terminal logs were not changed.

Final lint/test results are recorded in IMPLEMENTATION_LOG.md. A controlled
author-run ten-sample benchmark remains necessary to establish current
real-provider PR-01 performance.
