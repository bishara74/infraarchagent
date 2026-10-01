# Phase 5 security evaluation

Mode: scan_only

| Model | Plan | Variant | Scan | Blocking | Advisory | Checkov HIGH/CRITICAL | tfsec HIGH/CRITICAL | Combined | FR-G-05 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| openai/gpt-oss-120b:nitro | kubernetes_monitoring | cost | syntax-limited (TERRAFORM_SYNTAX) | 30 | 42 | 10 | 1 | 11 | — |
| openai/gpt-oss-120b:nitro | kubernetes_monitoring | performance | ok | 38 | 39 | 8 | 8 | 16 | — |
| openai/gpt-oss-120b:nitro | kubernetes_monitoring | security | ok | 66 | 76 | 10 | 9 | 19 | False |
| openai/gpt-oss-120b:nitro | three_tier | cost | ok | 35 | 29 | 6 | 12 | 18 | — |
| openai/gpt-oss-120b:nitro | three_tier | performance | syntax-limited (TERRAFORM_SYNTAX) | 11 | 27 | 4 | 1 | 5 | — |
| openai/gpt-oss-120b:nitro | three_tier | security | ok | 31 | 27 | 2 | 12 | 14 | False |
| anthropic/claude-sonnet-5 | kubernetes_monitoring | cost | ok | 37 | 48 | 9 | 9 | 18 | — |
| anthropic/claude-sonnet-5 | kubernetes_monitoring | performance | ok | 40 | 49 | 8 | 10 | 18 | — |
| anthropic/claude-sonnet-5 | kubernetes_monitoring | security | ok | 28 | 62 | 7 | 10 | 17 | False |
| anthropic/claude-sonnet-5 | three_tier | cost | ok | 31 | 34 | 5 | 10 | 15 | — |
| anthropic/claude-sonnet-5 | three_tier | performance | ok | 34 | 27 | 5 | 12 | 17 | — |
| anthropic/claude-sonnet-5 | three_tier | security | ok | 21 | 18 | 4 | 8 | 12 | False |

## Generator model aggregates

- anthropic/claude-sonnet-5: mean blocking 31.83; clean first scan 0.0%; Checkov HIGH/CRITICAL 38; tfsec HIGH/CRITICAL 59; combined 97; scanner errors 0; syntax-limited scans 0; FR-G-05 FAIL
- openai/gpt-oss-120b:nitro: mean blocking 35.17; clean first scan 0.0%; Checkov HIGH/CRITICAL 40; tfsec HIGH/CRITICAL 43; combined 83; scanner errors 0; syntax-limited scans 2; FR-G-05 FAIL
