# Phase 5b security evaluation

Mode: scan_only

| Model | Plan | Variant | Scan | Blocking | Advisory | Checkov HIGH/CRITICAL | Trivy HIGH/CRITICAL | Terraform HIGH/CRITICAL | Combined | FR-G-05 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| openai/gpt-oss-120b:nitro | kubernetes_monitoring | cost | syntax-limited (TERRAFORM_SYNTAX) | 46 | 64 | 10 | 6 | 1 | 17 | — |
| openai/gpt-oss-120b:nitro | kubernetes_monitoring | performance | ok | 54 | 61 | 8 | 14 | 0 | 22 | — |
| openai/gpt-oss-120b:nitro | kubernetes_monitoring | security | ok | 94 | 121 | 10 | 18 | 0 | 28 | False |
| openai/gpt-oss-120b:nitro | three_tier | cost | ok | 31 | 30 | 6 | 9 | 0 | 15 | — |
| openai/gpt-oss-120b:nitro | three_tier | performance | syntax-limited (TERRAFORM_SYNTAX) | 25 | 37 | 4 | 12 | 1 | 17 | — |
| openai/gpt-oss-120b:nitro | three_tier | security | ok | 27 | 28 | 2 | 9 | 0 | 11 | False |
| anthropic/claude-sonnet-5 | kubernetes_monitoring | cost | ok | 65 | 72 | 9 | 21 | 0 | 30 | — |
| anthropic/claude-sonnet-5 | kubernetes_monitoring | performance | ok | 67 | 76 | 8 | 21 | 0 | 29 | — |
| anthropic/claude-sonnet-5 | kubernetes_monitoring | security | ok | 54 | 96 | 7 | 20 | 0 | 27 | False |
| anthropic/claude-sonnet-5 | three_tier | cost | ok | 28 | 35 | 5 | 8 | 0 | 13 | — |
| anthropic/claude-sonnet-5 | three_tier | performance | ok | 30 | 29 | 5 | 9 | 0 | 14 | — |
| anthropic/claude-sonnet-5 | three_tier | security | ok | 16 | 19 | 4 | 4 | 0 | 8 | False |

## Generator model aggregates

- anthropic/claude-sonnet-5: mean blocking 43.33; clean first scan 0.0%; Checkov HIGH/CRITICAL 38; Trivy HIGH/CRITICAL 83; Terraform HIGH/CRITICAL 0; combined 121; scanner errors 0; syntax-limited scans 0; FR-G-05 FAIL
- openai/gpt-oss-120b:nitro: mean blocking 46.17; clean first scan 0.0%; Checkov HIGH/CRITICAL 40; Trivy HIGH/CRITICAL 68; Terraform HIGH/CRITICAL 2; combined 110; scanner errors 0; syntax-limited scans 2; FR-G-05 FAIL

## External module coverage advisories

- openai/gpt-oss-120b:nitro / three_tier / performance: module.vpc at terraform/main.tf:8 (EXTERNAL_MODULE_NOT_SCANNED, advisory).

## Comparison with the last tfsec scan-only report

| Model / package | Blocking old → new | Checkov H/C old = new | tfsec H/C old | Trivy H/C new | Terraform H/C new | Combined H/C old → new |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-oss / kubernetes_monitoring / cost | 30 → 46 | 10 | 1 | 6 | 1 | 11 → 17 |
| gpt-oss / kubernetes_monitoring / performance | 38 → 54 | 8 | 8 | 14 | 0 | 16 → 22 |
| gpt-oss / kubernetes_monitoring / security | 66 → 94 | 10 | 9 | 18 | 0 | 19 → 28 |
| gpt-oss / three_tier / cost | 35 → 31 | 6 | 12 | 9 | 0 | 18 → 15 |
| gpt-oss / three_tier / performance | 11 → 25 | 4 | 1 | 12 | 1 | 5 → 17 |
| gpt-oss / three_tier / security | 31 → 27 | 2 | 12 | 9 | 0 | 14 → 11 |
| Sonnet / kubernetes_monitoring / cost | 37 → 65 | 9 | 9 | 21 | 0 | 18 → 30 |
| Sonnet / kubernetes_monitoring / performance | 40 → 67 | 8 | 10 | 21 | 0 | 18 → 29 |
| Sonnet / kubernetes_monitoring / security | 28 → 54 | 7 | 10 | 20 | 0 | 17 → 27 |
| Sonnet / three_tier / cost | 31 → 28 | 5 | 10 | 8 | 0 | 15 → 13 |
| Sonnet / three_tier / performance | 34 → 30 | 5 | 12 | 9 | 0 | 17 → 14 |
| Sonnet / three_tier / security | 21 → 16 | 4 | 8 | 4 | 0 | 12 → 8 |

All 12 scans completed with zero scanner errors and zero timeouts. One external
module advisory is recorded: gpt-oss three_tier/performance, module.vpc at
`terraform/main.tf:8` (a registry source). Its downloaded contents were unavailable
but local findings were retained; all other module sources are local. Checkov counts are
identical per package. Mean blocking counts changed from 35.17 to 46.17 for
gpt-oss and 31.83 to 43.33 for Sonnet. All packages still have blocking findings;
FR-G-05 still fails for both models. HIGH/CRITICAL totals: gpt-oss Checkov 40
unchanged, old tfsec 43 versus new Trivy 68 plus Terraform 2; Sonnet Checkov 38
unchanged, old tfsec 59 versus new Trivy 83 plus Terraform 0.

Both gpt-oss syntax findings remain: kubernetes_monitoring/cost at
`terraform/main.tf:172` (Invalid single-argument block definition) and
three_tier/performance at `terraform/ecs.tf:24` (Extraneous label for locals).
The old tfsec syntax count is replaced by Terraform, not added to Trivy.

Large increases occur in monitoring packages (+16/+16/+28 for gpt-oss,
+28/+27/+26 for Sonnet) and the syntax-limited gpt-oss three-tier performance
package (+14). Likely causes are additional Kubernetes and Helm coverage,
including Kubernetes findings despite failed Terraform parsing. A direct Trivy
probe of Sonnet monitoring/cost confirms both rendered Helm workloads, with
13 findings and three HIGH/CRITICAL findings each; gpt-oss monitoring/cost
still has no Terraform findings but scans both Kubernetes deployments. Trivy
can also omit unrenderable templates; built-in Helm support is not universal
chart validation. Three-tier reductions of 3–5 findings are consistent with
rule/severity differences in the pinned embedded library; Checkov's severity
policy did not change. No remediation quality or timing speedup is inferred.
