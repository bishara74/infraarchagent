# Phase 2 ArchitectAgent evaluation

Provider: `openai`
Model: `anthropic/claude-sonnet-5`

## three_tier

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: relational database
- PASS: object storage
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 14.053
- Input/output tokens: 1861/1474
- Prompt version: 2

## vague_web_app

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: ambiguity recorded
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 11.559
- Input/output tokens: 1822/1196
- Prompt version: 2

## static_site

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: CDN service
- Plan attempts: 1
- LLM attempts: 3
- Elapsed seconds: 38.644
- Input/output tokens: 1844/1440
- Prompt version: 2

## data_pipeline

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: queue service
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 16.372
- Input/output tokens: 1853/1874
- Prompt version: 2

## kubernetes_monitoring

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: monitoring file types
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 18.862
- Input/output tokens: 1860/2300
- Prompt version: 2

