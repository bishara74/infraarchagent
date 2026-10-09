# Phase 6b validation comparison

Previous: [phase6-validation-20261009T175917789637Z](../phase6-validation-20261009T175917789637Z/summary.md).

Current: [phase6-validation-20261009T211526321570Z](summary.md), produced by `make eval-validation`.

All twelve input source hashes and tool versions match the retained previous report. The existing provider mirror was used; no download, installation, database access or LLM call occurred during evaluation.

| Model | Plan | Variant | Previous | Current | Reference failures before → after |
|---|---|---|---|---|---:|
| gpt-oss | kubernetes_monitoring | cost | invalid | invalid | 1 → 1 |
| gpt-oss | kubernetes_monitoring | performance | invalid | invalid | 1 → 1 |
| gpt-oss | kubernetes_monitoring | security | invalid | invalid | 3 → 3 |
| gpt-oss | three_tier | cost | invalid | invalid | 19 → 1 |
| gpt-oss | three_tier | performance | invalid | invalid | 6 → 6 |
| gpt-oss | three_tier | security | invalid | invalid | 0 → 0 |
| Sonnet | kubernetes_monitoring | cost | invalid | valid | 1 → 0 |
| Sonnet | kubernetes_monitoring | performance | invalid | invalid | 1 → 1 |
| Sonnet | kubernetes_monitoring | security | invalid | valid | 1 → 0 |
| Sonnet | three_tier | cost | valid | valid | 0 → 0 |
| Sonnet | three_tier | performance | valid | valid | 0 → 0 |
| Sonnet | three_tier | security | invalid | invalid | 0 → 0 |

**Totals:** 2 valid / 10 invalid / 0 error → **4 valid / 8 invalid / 0 error**.

Sonnet monitoring cost now resolves the literal Helm Service in namespace `apps`; its templated port remains a warning. Sonnet monitoring security warns for the templated Service identity. Sonnet monitoring performance still fails: the Ingress defaults to namespace `default`, while the literal Helm Service is in `monitoring`. No source package was modified.

The Sonnet three-tier security Terraform diagnostic is **Cycle**, a genuine circular dependency among the ALB, application and RDS security groups. Offline init succeeded and validate failed. Terraform supplied no range; the report attaches the failure to `terraform/alb.tf:1`, the first root `.tf` file (this package has no `terraform/main.tf`), as a remediation anchor. Graph listings and source excerpts are excluded from the report.

The gpt-oss three-tier cost package now emits one `local.common_tags is not declared` reference finding at its first actual occurrence, rather than nineteen duplicate findings. Its four Terraform diagnostics remain; the package is still invalid.

Both known gpt-oss syntax failures remain confirmed from real Terraform output. The gpt-oss three-tier performance remote module remains unavailable offline (one required skip); existing configuration failures make its overall result invalid.

The Aurora cluster without database instances remains an undetected semantic deployment gap. Static validity does not prove deployability.
