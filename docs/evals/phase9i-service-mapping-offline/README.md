# phase9i: complete service mapping before the next benchmark

[Offline report and all-plan table](results/README.md) cover the 20 broad and
28 final-set plans. Both serverless scenario-3 contexts rise from zero to **4,471
schema characters**. No saved plan remains without schema guidance.

The Architect originally had no finite service enum: aws_service was a free-form
string. The schema now advertises 33 canonical labels without rejecting existing
free-form plans. Prompt version increases from 2 to 3 because its embedded schema
changed. Coverage checks the advertised vocabulary, observed saved-plan labels
and every selected resource type against AWS 5.100.0 and 6.68.0. Unknown strings
outside that vocabulary cannot be exhaustively mapped.

Plain Prometheus/Grafana use the plan's explicitly selected hosting resources,
as clarified by the author. Managed workspaces require explicit managed labels;
a monitoring-only plan with no named host stays unresolved. No topology is added
solely to make the coverage test pass.

Caps remain 4,500 schema / 1,500 checklist / 6,000 combined characters and the
existing recursive tiers/overflow rules are unchanged. All selected unconditional
cores fit across the 48 saved plans. Conditional overflow affects 10/20 broad
plans and 12/14 plans in each final set; omitted-type lists are in results/plans.json.
No package validity or security gain is attributed to changing guidance.

Reproduce from the original cached snapshots and pinned local schema indexes,
into a new output directory (no model, validator, scanner or cloud calls):

```bash
cd backend
INFRAARCH_TEST_BOOTSTRAP=1 PYTHONPATH="$PWD/tests/bootstrap:$PWD" \
  .venv/bin/python -m scripts.phase9i_service_mapping_report \
  --output /tmp/phase9i-service-mapping-new
```

[baseline.json](baseline.json) freezes prior per-label selection and all 48 plan
contexts from 9031c64. Its source hashes and plan hashes are verified during
reporting; [results/manifest.json](results/manifest.json) hashes the evaluator
sources, unchanged tier implementation and pinned indexes. Historical evidence
and original cached snapshots remain unchanged. Verification logs are in
verification/. No real LLM calls, dotenv reads or pushes.
