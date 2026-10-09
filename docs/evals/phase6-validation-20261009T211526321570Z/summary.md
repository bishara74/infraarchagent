# Phase 6 offline validation

12 original packages: error:0, invalid:8, valid:4.

Local tools only, black-hole proxies, no database or LLM. Original files are unchanged; source hashes identify the inputs.

| Package | Result | Failures by category | Warnings | Skips/reasons | Seconds |
|---|---|---|---:|---|---:|
| openai_gpt-oss-120b_nitro-065f667f/kubernetes_monitoring/cost | invalid | lint:2, reference:1, structure:4, terraform:1 | 17 | — | 0.313 |
| openai_gpt-oss-120b_nitro-065f667f/kubernetes_monitoring/performance | invalid | reference:1, structure:3, terraform:2 | 15 | — | 11.722 |
| openai_gpt-oss-120b_nitro-065f667f/kubernetes_monitoring/security | invalid | reference:3, structure:2, terraform:2 | 18 | — | 10.000 |
| openai_gpt-oss-120b_nitro-065f667f/three_tier/cost | invalid | reference:1, terraform:4 | 3 | — | 7.685 |
| openai_gpt-oss-120b_nitro-065f667f/three_tier/performance | invalid | reference:6, terraform:1 | 4 | remote_module_not_available_offline:1 | 0.111 |
| openai_gpt-oss-120b_nitro-065f667f/three_tier/security | invalid | terraform:1 | 3 | — | 15.045 |
| anthropic_claude-sonnet-5-2cd37409/kubernetes_monitoring/cost | valid | — | 11 | — | 8.502 |
| anthropic_claude-sonnet-5-2cd37409/kubernetes_monitoring/performance | invalid | reference:1 | 10 | — | 7.875 |
| anthropic_claude-sonnet-5-2cd37409/kubernetes_monitoring/security | valid | — | 11 | — | 8.253 |
| anthropic_claude-sonnet-5-2cd37409/three_tier/cost | valid | — | 1 | — | 9.571 |
| anthropic_claude-sonnet-5-2cd37409/three_tier/performance | valid | — | 0 | — | 7.881 |
| anthropic_claude-sonnet-5-2cd37409/three_tier/security | invalid | terraform:1 | 3 | — | 7.175 |

Tool versions: ansible-lint: ansible-lint 26.9.0 using ansible-core:2.21.5 ansible-compat:26.9.0 ruamel-yaml:0.19.1; hadolint: Haskell Dockerfile Linter 2.15.1; helm: v4.3.0+gbec5b06; promtool: promtool, version 3.15.0 (branch: HEAD, revision: 5241a27fe3c6983549fccc32f6e65917408c63cd); terraform: Terraform v1.16.4

Known syntax failure gpt-oss/kubernetes_monitoring/cost: confirmed from Terraform diagnostics.
Known syntax failure gpt-oss/three_tier/performance: confirmed from Terraform diagnostics.

An Aurora cluster without database instances is a semantic deployment gap: none of these static checks detects it. Valid does not prove deployability.

Full checks, file/line locations, skip reasons, omitted counts and remediation targets are in results.json.
