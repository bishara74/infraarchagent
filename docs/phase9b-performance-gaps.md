# Phase 9b performance gaps and attribution

## PR-03: recorded failure, unchanged threshold

The official criterion remains three simultaneous identical-prompt runs, each
at most 1.5 times an isolated baseline. Final set 1 ratios are 2.0249, 1.9599,
1.9008; set 2 ratios are 1.6625, 2.0215, 1.8349. Both sets FAIL. Using the
repeated PR-01 prompt median as the secondary reference gives 2.0795/2.0127/
1.9520 and 1.7468/2.1240/1.9278 respectively. Those secondary references do not
replace the isolated-baseline acceptance method (D-43).

Sources: [set 1](evals/phase9-bench-real-20261020T010134093069Z/results.json),
[set 2](evals/phase9-bench-real-20261020T013911945957Z/results.json),
[D-54 attribution](phase9-runtime-attribution.md).

The captured host is an i5-1135G7, eight logical CPUs, approximately 8 GB RAM,
WSL2. Each pipeline includes CPU-heavy Checkov/Trivy and Terraform work. Running
three pipelines overlaps that work and consumes shared tool capacity. This is
consistent with contention, not a controlled proof that CPU alone causes every
extra second: host load, content, scheduling, provider routing and cache warming
were uncontrolled. D-54's one ordered replay per configuration cannot estimate
small instrumentation overhead. Its 266.48 → 239.74-second smoke estimate is a
counterfactual projection, not a measured speedup. No runtime quality optimization
or threshold relaxation is made in Phase 9b.

### Draft target for author/supervisor agreement — not adopted

> On the declared resource-constrained development host, the system shall accept
> three simultaneous runs and preserve package/result correctness and ordered,
> isolated event streams. Report per-run latency inflation and per-agent deadline
> outcomes alongside this functional concurrency result. Evaluate the existing
> 50% latency-inflation target separately on a dedicated reference host with
> capacity for three concurrent local-tool workloads.

This is a proposed separation of functional concurrency and hardware-dependent
latency, not a retrospective PASS. Before adopting it, predeclare host resources,
provider/model/prompt versions, tool versions and cache state; use the same
prompt/configuration for paired isolated baselines and three-run cohorts across
at least ten repeated cohorts per prompt. Alternate ordering, record individual
ratios, CPU/memory/load, queue and local-tool times, API settlement, deadline
failures, correctness and event isolation. Retain all failures and state whether
provider degradation exclusion was invoked. The supervisor must agree the final
reference hardware and criterion before new acceptance measurements.

## PR-04: quiet offline session-check measurement

The historical [9h stub benchmark](evals/phase9-bench-stub-20261019T154457135290Z/summary.md)
remains FAIL: median 1.988 seconds, maximum 2.653 seconds. Median below two seconds
is insufficient when individual downloads exceed the threshold.

New [quiet evidence](evals/phase9b-download-quiet/summary.md) uses the same seeded,
synthetic, rejected 9,989,906-byte ZIP for every condition, real disposable
PostgreSQL 16, a loopback HTTP server, two warm-ups and ten alternating complete
response-body measurements per condition. No LLM, cloud, scanner or validator
execution occurs. No other verification job overlapped the quiet run.

| Condition | Median seconds | Maximum seconds | Every request ≤2 s |
|---|---:|---:|---|
| Account session | 0.700893 | 0.721118 | PASS |
| Shared key | 0.698920 | 0.730615 | PASS |
| Prevalidated session control | 0.695996 | 0.734234 | attribution only |

Median session-touch work is 0.003275 seconds; user lookup 0.001837 seconds;
ZIP work 0.358360 seconds; recorded SQL execution totals 0.072830 seconds.
These are independent medians with nested intervals, not an additive breakdown.
Session minus prevalidated median is about 4.9 ms. Ten descriptive observations
cannot establish a small causal overhead, but no clear session-check bottleneck
appears. No production authentication/download change is justified. Restoring the
real guard and revoking the synthetic session returned HTTP 401.

An initial exploratory run overlapped a later frontend verification job. Its
uncommitted folder `phase9b-download/` is excluded from official report inputs;
only `phase9b-download-quiet/` supports the result above. Existing historical
folders remain unchanged. The new local HTTP measurement is not curl and is not
a clean-machine or deployment proof; the report retains this method difference.
