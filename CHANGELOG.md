# Changelog

## v1.0 — prepared 2026-10-26, not tagged

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

Known limits: PR-03's approved concurrency target is **not met**; NFR-04 clean
deployment is **unverified** until the author commits actual results. Agent
recovery/telemetry replaceability, static reference/naming coverage, bounded reports,
generator directives and state/event crash gaps remain explicit partial findings.
No static/human label establishes successful cloud deployment. Containers were
checked statically; no images were built or machines provisioned by the agent.

Upgrade: back up the database/master key, apply migration 0015 as the owner,
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
