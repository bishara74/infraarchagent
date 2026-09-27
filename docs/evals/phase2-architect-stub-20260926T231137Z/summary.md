# Phase 2 ArchitectAgent evaluation

Provider: `stub`
Model: `stub`

## three_tier

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: RDS service
- PASS: object storage
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 0.000
- Input/output tokens: None/None
- Prompt version: 1

## vague_web_app

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: ambiguity recorded
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 0.000
- Input/output tokens: None/None
- Prompt version: 1

## static_site

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: CDN service
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 0.000
- Input/output tokens: None/None
- Prompt version: 1

## data_pipeline

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: queue service
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 0.000
- Input/output tokens: None/None
- Prompt version: 1

## kubernetes_monitoring

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: monitoring file types
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 0.000
- Input/output tokens: None/None
- Prompt version: 1

## correction diagnostic

- PASS: invalid dependency corrected on second plan attempt
- Plan attempts: 2
- LLM attempts: 2
- Validation errors, attempt 1:
  - dependencies.0.target: unknown service 'unknown-service'

