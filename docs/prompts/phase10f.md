# Codex task — Phase 10f: final documentation update (documentation only)

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-63 to D-66),
the latest `docs/IMPLEMENTATION_LOG.md` entries, `docs/evals/EVIDENCE.md` and
the script that generates it, `CHANGELOG.md`, `README.md`,
`docs/deployment.md`, and these committed evidence folders:

- final round `docs/evals/phase9-bench-broad-20261028T125056656606Z`
- aborted first attempt `docs/evals/phase9-bench-broad-20261028T020956988464Z`
- earlier rounds `…20261020T234203035108Z`, `…20261021T200436165739Z`,
  `…20261027T015443795826Z`, `…20261027T155607468680Z`,
  `…20261027T205119472235Z`
- NFR-04 evidence `docs/evals/nfr04-clean-deployment-20261028/`

## Rules

Documentation and generated reports only: **no application, test or
configuration code changes**, no `.env` reads, no network, no installs, no
push. **Never modify `docs/spec/`** (approved baseline) or any committed
evidence folder. Recompute every number from committed evidence; report any
mismatch with the figures below instead of copying them. Plan mode first.
Commit prefix `phase10f:`.

## 1. Final benchmark result (D-66, thesis notes, CHANGELOG)

Record the final reported round as declared in D-66:

- strict checks passed **15/58 (25.9%)**, Wilson 95% CI about 16–38%;
  levels 1–3: 14/30; levels 4–5: 1/28; 2 missing variants.
- Fisher two-sided: vs the corrected early pool 42/120, p ≈ 0.24; vs round 2
  19/60, p ≈ 0.55; vs the two blocking-guard rounds 22/116, p ≈ 0.33.
- The development history, honestly labelled as development iterations on
  the same pre-registered scenarios: early rounds 24/60 and 19/60 (43/120,
  corrected 42/120); blocking guard 7/60, 11/59, 11/57 (10b–10d); detect-only
  guard final 15/58 (10e).
- The first 10e attempt aborted at run 10 because the server process died
  with a native `double free or corruption (fasttop)` abort (no Python
  traceback available); it was repeated once with `PYTHONFAULTHANDLER=1` and
  no crash occurred. Record the 8/27 partial result as not reported.
- Disclose differences in the final round: higher deadline counts
  (deadline-before-candidate, iteration-deadline stops, generation-gate
  deadlines) and provider fallbacks (about 16% of calls served by providers
  other than Cerebras); 6 packages flagged `plan_conformance_conflict`.
- Seven early passes contained dynamic file inputs that the current safe
  refusal blocks; one early pass was a confirmed exposure flip.

## 2. Requirement status

- NFR-04: **met** for the stated scope, from the committed evidence (clean
  Ubuntu 24.04.5 WSL, revision e6ac337…, all steps exit 0, stub run three
  `checks_passed`, Trivy 0.69.3 hash identical to the development
  environment, Chrome 156 and Firefox 159 passed all checks). State the
  limits (stub responses, WSL, Edge/Safari not tested, optional validators
  absent).
- PR-03 remains **not met** (CPU-bound scanners), with the recorded
  measurements.
- Regenerate `docs/evals/EVIDENCE.md` with its script and update the
  traceability report if the tooling requires it.

## 3. README and CHANGELOG

- README: current status, final result with a link to D-66, the deployment
  guide, and the troubleshooting cases seen in practice (migration not
  applied, master key not loaded, Ctrl+C in the terminal stops scripts, WSL
  instances share ports, CRLF in downloaded scripts).
- CHANGELOG: finalise the v1.0 entry (features, known limitations including
  PR-03 and the native crash observation) and keep the author-only tag/push
  commands.

## Finish

Run `make lint`, `make secret-scan` and the evidence/traceability generators
(real counts). Summary in the `AGENTS.md` §10 format, starting with any
number that differs from the figures above, then the requirement status
counts, then the exact tag commands.
