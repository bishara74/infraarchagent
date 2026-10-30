# Phase 10f — final evaluation account

The final predeclared reported broad round is **15/58 (25.86%; 25.9% rounded)**
strict checks passed, Wilson 95% CI **16.35–38.38%**. Levels 1–3 contribute
**14/30**, levels 4–5 **1/28**, and two variants are missing. Six packages require
review for final `plan_conformance_conflict` evidence. The automatic label describes
static scan/validation readiness; it does not establish deployment success.

The [computed report](../evals/phase10f-final-report/README.md) and
[D-66](../design-deviations.md#d-66--detect-plan-conflicts-on-final-retained-files-phase-10e)
retain the complete development history: early 24/60 and 19/60, published pool
43/120 corrected to 42/120 for one confirmed exposure flip; blocking guard
7/60, 11/59 and 11/57; final detect-only 15/58. Unresolved historical exposure
retains the 41–42/120 bound. All rounds reuse the same pre-registered scenarios;
shared plans and iterative development preclude independent held-out or causal claims.

Two-sided Fisher comparisons of the final round against corrected early 42/120,
round 2's 19/60 and the later guard rounds' 22/116 give p = **0.23578014**,
**0.54511520** and **0.32827896** respectively. These are descriptive package-level
calculations; none removes clustering, model variance or the selection history.

An initial attempt stopped at run 10 with 8/27 passing among nine settled runs;
it is excluded from the final result. The author reported a native
`double free or corruption (fasttop)` server abort with no Python traceback,
then one repeat with `PYTHONFAULTHANDLER=1` that completed without a crash.
The supplied task is the observation record; no native crash log establishes cause.

Final timing differs: 26 deadline-before-candidate records, 42 records carrying an
iteration-deadline reason, three validation-repair deadline stops and six
generation-gate deadline outcomes. These are different, partly overlapping units.
Provider routing differs too: non-Cerebras served 57/362 known-provider calls
(15.75%), with 64/426 calls having unknown provider. The fraction among all recorded
calls is 13.38%, so “about 16% of calls” needs its denominator qualified.

The historical diagnosis states that seven early passing low-complexity packages
contain file inputs now safely refused. Their raw source snapshots are uncommitted;
this count cannot be independently reconstructed from committed projections here.
It is a qualified historical observation, not seven recoverable passes.

NFR-04 is **met for the committed clean Ubuntu 24.04.5 WSL/stub/browser scope**:
seven steps exit zero, three synthetic packages pass, and Chrome 156 and Firefox
159 pass the nine recorded manual checks. The JSON's pending-browser status is an
earlier snapshot than the completed README checklist. Limits include WSL, stub
responses, untested Edge/Safari, absent optional validators, omitted manual feedback
retry and dual-colour-scheme screenshots. The recorded Trivy 0.69.3 hash matches
development. See the [deployment evidence](../evals/nfr04-clean-deployment-20261028/README.md).

PR-03 remains **not met** against ≤1.5× isolated baseline: recorded final-set ratios
span 1.90–2.02× and 1.66–2.02×. CPU-heavy scanner/Terraform contention is consistent
with the measured host, while uncontrolled load prevents precise attribution.
The reviewed 59-ID register now has **46 met, 12 partly met, 1 not met, 0 unverified**.
No approved specification text or historical evidence has been rewritten.
