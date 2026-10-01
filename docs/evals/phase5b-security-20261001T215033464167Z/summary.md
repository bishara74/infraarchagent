# Phase 5b security evaluation

Mode: remediate

| Model | Plan | Variant | Scan | Blocking | Advisory | Checkov HIGH/CRITICAL | Trivy HIGH/CRITICAL | Terraform HIGH/CRITICAL | Combined | FR-G-05 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| anthropic/claude-sonnet-5 | three_tier | security | ok | 16 | 19 | 4 | 4 | 0 | 8 | False |
| anthropic/claude-sonnet-5 | three_tier | cost | ok | 28 | 35 | 5 | 8 | 0 | 13 | — |

## Generator model aggregates

- anthropic/claude-sonnet-5: mean blocking 22.00; clean first scan 0.0%; Checkov HIGH/CRITICAL 9; Trivy HIGH/CRITICAL 12; Terraform HIGH/CRITICAL 0; combined 21; scanner errors 0; syntax-limited scans 0; FR-G-05 FAIL

## External module coverage advisories

None.

## Remediation results

| Generator | Plan | Variant | Fixing model | Blocking before → after | Fix passes | Stop reason | Remaining by severity | Fixes accepted / rejected | Rejection reasons | Elapsed seconds | Tokens in / out | Cost |
| --- | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| anthropic/claude-sonnet-5 | three_tier | security | anthropic/claude-sonnet-5 | 16 → 2 | 3 | iteration limit | HIGH:1, MEDIUM:1 | 9 / 0 | — | 115.639 | 19648 / 23074 | 0.270036 |
| anthropic/claude-sonnet-5 | three_tier | cost | anthropic/claude-sonnet-5 | 28 → 1 | 3 | iteration limit | HIGH:1 | 8 / 0 | — | 81.745 | 14267 / 16472 | 0.193254 |

## Fixing model aggregates

- anthropic/claude-sonnet-5: blocking 44 → 3; reduction 93.2%; clean rate 0.0%; mean remaining 1.50
