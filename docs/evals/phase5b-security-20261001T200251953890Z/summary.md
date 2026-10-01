# Phase 5b security evaluation

Mode: remediate

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

## Remediation results

| Generator | Plan | Variant | Fixing model | Blocking before → after | Fix passes | Stop reason | Remaining by severity | Fixes accepted / rejected | Rejection reasons | Elapsed seconds | Tokens in / out | Cost |
| --- | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| openai/gpt-oss-120b:nitro | kubernetes_monitoring | cost | openai/gpt-oss-120b:nitro | 46 → 0 | 3 | clean | — | 7 / 0 | — | 21.632 | 11677 / 12232 | 0.009091 |
| openai/gpt-oss-120b:nitro | kubernetes_monitoring | performance | openai/gpt-oss-120b:nitro | 54 → 0 | 2 | clean | — | 6 / 0 | — | 16.423 | 9613 / 9529 | 0.007159 |
| openai/gpt-oss-120b:nitro | kubernetes_monitoring | security | openai/gpt-oss-120b:nitro | 94 → 7 | 3 | iteration limit | MEDIUM:7 | 15 / 0 | — | 29.957 | 23341 / 24225 | 0.018036 |
| openai/gpt-oss-120b:nitro | three_tier | cost | openai/gpt-oss-120b:nitro | 31 → 3 | 3 | iteration limit | HIGH:2, MEDIUM:1 | 3 / 0 | — | 24.758 | 11192 / 13612 | 0.009846 |
| openai/gpt-oss-120b:nitro | three_tier | performance | openai/gpt-oss-120b:nitro | 25 → 5 | 3 | iteration limit | HIGH:4, MEDIUM:1 | 10 / 0 | — | 21.801 | 9308 / 8942 | 0.006761 |
| openai/gpt-oss-120b:nitro | three_tier | security | openai/gpt-oss-120b:nitro | 27 → 1 | 3 | iteration limit | MEDIUM:1 | 3 / 0 | — | 26.101 | 11753 / 14123 | 0.010237 |
| anthropic/claude-sonnet-5 | kubernetes_monitoring | cost | openai/gpt-oss-120b:nitro | 65 → 8 | 3 | iteration limit | MEDIUM:8 | 14 / 0 | — | 26.261 | 14684 / 13539 | 0.010326 |
| anthropic/claude-sonnet-5 | kubernetes_monitoring | performance | openai/gpt-oss-120b:nitro | 67 → 0 | 2 | clean | — | 12 / 1 | new_file_exists:1 | 18.682 | 13402 / 13012 | 0.009817 |
| anthropic/claude-sonnet-5 | kubernetes_monitoring | security | openai/gpt-oss-120b:nitro | 54 → 3 | 3 | iteration limit | MEDIUM:3 | 20 / 0 | — | 27.79 | 22214 / 21683 | 0.016342 |
| anthropic/claude-sonnet-5 | three_tier | cost | openai/gpt-oss-120b:nitro | 28 → 3 | 3 | iteration limit | MEDIUM:3 | 9 / 1 | invalid_structure:1 | 23.423 | 10554 / 11043 | 0.008209 |
| anthropic/claude-sonnet-5 | three_tier | performance | openai/gpt-oss-120b:nitro | 30 → 0 | 3 | clean | — | 11 / 0 | — | 24.012 | 13300 / 13160 | 0.009891 |
| anthropic/claude-sonnet-5 | three_tier | security | openai/gpt-oss-120b:nitro | 16 → 4 | 3 | iteration limit | MEDIUM:4 | 8 / 1 | schema:file.extra:1 | 33.353 | 13181 / 14466 | 0.010657 |

## Fixing model aggregates

- openai/gpt-oss-120b:nitro: blocking 537 → 34; reduction 93.7%; clean rate 33.3%; mean remaining 2.83
