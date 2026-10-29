# Changelog

## v1.0 — finalised 2026-10-29, not tagged

- Complete the natural-language → Architect → three generators → security
  remediation → validation → engineer review/download workflow, with live SSE.
- Preserve strict readiness, versioned contextual assessments, offline provider
  validation, authenticated review identity, encrypted credentials and preferences.
- Activate screened administrator lessons directly; reviewer lessons require a
  different named admin. Retain exact pre-submit previews, kill switch, immutable
  versions and run/archive provenance. Deprecate the old inverse policy setting.
- Hide settled decision controls, restore primary ZIP, separate lesson proposals,
  improve gate hints, distinguish engineer approval, and add approval categories
  with history/export/accepted-risk insights.
- Add a clean Ubuntu deployment kit, non-root container recipes, synthetic defence
  seed, three-framework traceability, TC mapping and a reviewed evidence index.
- Document authentication scope changes, the final API/data model, measured
  generator directive rates and proposed specification amendments.
- Correct cumulative unified diffs for files without a final newline.
- Detect confirmed plan exposure conflicts on final retained files and require
  engineer review, while other security/validation acceptance gates remain active.
- Report the final registered broad round as **15/58 (25.9%)** strict checks
  passed, Wilson 95% CI 16.35–38.38%, two variants missing and six final conformance
  flags. The [final report](docs/evals/phase10f-final-report/README.md) distinguishes
  development iterations, the corrected early pool and deadline/routing differences.
- Close NFR-04 for the committed clean Ubuntu 24.04.5 WSL/stub deployment and
  Chrome 156 / Firefox 159 checks, with the stated coverage limits.

Known limits: PR-03's approved ≤1.5× isolated-baseline concurrency target is
**not met**: recorded final-set ratios range 1.90–2.02× and 1.66–2.02× on the
CPU-contended scanner/Terraform host. NFR-04 evidence uses stub responses and WSL;
Edge/Safari, optional validators, manual feedback retry and dual-scheme screenshots
were not tested in that clean deployment. The first final-round attempt aborted
at run 10 with the author-observed native `double free or corruption (fasttop)`
message and no Python traceback. One repeat with `PYTHONFAULTHANDLER=1` completed
without a crash; the excluded partial result was 8/27. Root cause is unverified.
Agent recovery/telemetry replaceability, static reference/naming coverage, bounded reports,
generator directives and state/event crash gaps remain explicit partial findings.
No static/human label establishes successful cloud deployment. Containers were
checked statically; no images were built or machines provisioned by the agent.

Upgrade: back up the database/master key, apply migrations through 0016 as the owner,
then restart. Keep historical `self_approved` provenance readable. Explicit legacy
`LESSONS_REQUIRE_SECOND_APPROVER=true` maps to new direct activation false;
legacy false maps to true. An explicit new setting wins; legacy use warns once.

Release commands for the author, from the intended release commit:

```bash
git status --short
git tag -a v1.0 -m "InfraArchAgent v1.0"
git push origin HEAD
git push origin v1.0
```

These commands are supplied only; no tag or push was performed.
