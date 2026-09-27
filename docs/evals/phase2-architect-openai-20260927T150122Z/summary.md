# Phase 2 ArchitectAgent evaluation

Provider: `openai`
Model: `openai/gpt-oss-120b`

## three_tier

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: RDS service
- PASS: object storage
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 5.318
- Input/output tokens: 1334/2227
- Prompt version: 2

## vague_web_app

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: ambiguity recorded
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 4.488
- Input/output tokens: 1312/1927
- Prompt version: 2

## static_site

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: CDN service
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 4.607
- Input/output tokens: 1320/1776
- Prompt version: 2

## data_pipeline

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: queue service
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 4.744
- Input/output tokens: 1327/2091
- Prompt version: 2

## kubernetes_monitoring

- PASS: plan produced
- PASS: terraform included
- PASS: dependency graph valid
- PASS: monitoring file types
- Plan attempts: 1
- LLM attempts: 1
- Elapsed seconds: 6.017
- Input/output tokens: 1327/2556
- Prompt version: 2

