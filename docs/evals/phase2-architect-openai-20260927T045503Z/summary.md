# Phase 2 ArchitectAgent evaluation

Provider: `openai`
Model: `openai/gpt-oss-120b`

## three_tier

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: RDS service
- PASS: object storage
- Validation errors, attempt 1:
  - dependencies.4.target: unknown service 'app-bucket'
  - dependencies.5.target: unknown service 'app-bucket'
- Plan attempts: 2
- LLM attempts: 2
- Elapsed seconds: 7.672
- Input/output tokens: 3135/2995
- Prompt version: 1

## vague_web_app

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: ambiguity recorded
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 5.057
- Input/output tokens: 1201/2243
- Prompt version: 1

## static_site

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: CDN service
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 5.722
- Input/output tokens: 1209/2453
- Prompt version: 1

## data_pipeline

- FAIL: plan produced
- FAIL: terraform included
- FAIL: dependency graph valid
- FAIL: queue service
- Error category: `llm_failure`
- Validation errors, attempt 1:
  - dependencies.2.target: unknown service 'raw-data-bucket'
- LLM category: `rate_limit`
- Plan attempts: 2
- LLM attempts: 4
- Elapsed seconds: 24.999
- Input/output tokens: None/None
- Prompt version: 1

## kubernetes_monitoring

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: monitoring file types
- Validation errors, attempt 1:
  - dependencies.0.source: unknown service 'helm'
- Plan attempts: 2
- LLM attempts: 3
- Elapsed seconds: 16.926
- Input/output tokens: 3097/3881
- Prompt version: 1

