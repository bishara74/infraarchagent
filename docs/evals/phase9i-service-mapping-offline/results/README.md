# phase9i: service mapping offline coverage

48 saved plans: 20 broad, 14 final-1 and 14 final-2. No LLM calls or package replay. Historical evidence and inputs are unchanged.

| Cohort | Previously unmapped labels (service/storage occurrences) | Schema before → after | Required / conditional overflow plans |
|---|---|---|---|
| broad | acm (2), apigateway (2), dynamodb (2), elasticache (4), elasticloadbalancing (1), elasticloadbalancingv2 (2), lambda (3), natgateway (1), vpc (1) | 0–4493 → 4097–4496 | 0 / 10 |
| final-1 | acm (1), grafana (1), prometheus (1) | 4478–4491 → 4478–4493 | 0 / 12 |
| final-2 | elasticloadbalancing (1), grafana (2), prometheus (2) | 4474–4495 → 4474–4495 | 0 / 12 |

Unqualified API Gateway includes REST and HTTP core types; explicit REST/HTTP labels select the corresponding family. Lambda includes function, permission and IAM role. Storage labels select the named service before generic kind fallbacks.

Prometheus/Grafana inherit explicitly planned EC2/ECS/EKS hosting. Only explicit managed labels select AWS workspaces. A plain monitoring label without a host remains unresolved rather than inventing infrastructure.

The Architect schema now advertises 33 labels and remains free-form for compatibility (prompt version 3). Coverage tests check this vocabulary, all saved spellings and every selected type against both pinned indexes. This finite vocabulary cannot exhaust arbitrary strings allowed by the schema.

All selected unconditional required cores fit; the existing 4,500 schema / 1,500 checklist / 6,000 combined caps and recursive tiers are unchanged. Explicitly reported conditional groups can still overflow. Both serverless scenario-3 plans now receive schema guidance; no zero-schema plans remain.

[plans.json](plans.json) records each plan's service-level previous gaps, selected types, schema/checklist/combined sizes and omitted-type lists. [baseline.json](../baseline.json) freezes pre-mapping selection and context measurements at 9031c64; [manifest.json](manifest.json) binds current code, indexes and source hashes. Guidance size changes alone establish no validity or benchmark-quality improvement.

| Cohort / run | Previously unmapped labels | Schema before → after | Checklist | Total |
|---|---|---|---|---|
| final-1/eb3fca7b-e12c-4ef2-b91b-82a4ba9de4d7 | none | 4490 → 4490 | 1190 | 5680 |
| final-1/95c60392-4ffe-4afb-9882-ef802a45bcdd | none | 4485 → 4485 | 1168 | 5653 |
| final-1/fc77f4a8-0d04-4eb3-aba6-756eab6dbc80 | acm | 4491 → 4493 | 404 | 4897 |
| final-1/d8f1e2bb-b3cf-485b-ba69-a41774f93893 | none | 4490 → 4490 | 1190 | 5680 |
| final-1/6e2ac28e-d152-453c-bbbb-28b72a3da099 | grafana, prometheus | 4480 → 4480 | 1168 | 5648 |
| final-1/9cfb1b01-0754-4796-9443-d88594066dde | none | 4491 → 4491 | 404 | 4895 |
| final-1/8c99c09e-e450-4b34-876c-960a9010b71c | none | 4490 → 4490 | 1190 | 5680 |
| final-1/152dd2d2-e625-4f12-9a40-8f8ab0fc9c0b | none | 4485 → 4485 | 1168 | 5653 |
| final-1/d2512668-53d6-475a-88ae-c5c00f4ddcd1 | none | 4491 → 4491 | 404 | 4895 |
| final-1/a6aad9b7-0d19-4826-bb09-6cd9ce2f7eab | none | 4490 → 4490 | 1190 | 5680 |
| final-1/33dd1a0c-d03b-433d-a165-9ac11af50a10 | none | 4490 → 4490 | 1190 | 5680 |
| final-1/e007d01c-35b1-4939-ab43-52e1fb086001 | none | 4490 → 4490 | 1190 | 5680 |
| final-1/b0f4701c-ffff-420f-bebd-64df235c1187 | none | 4478 → 4478 | 1190 | 5668 |
| final-1/83e65ace-224c-4c93-8ea6-7e69d817d2a5 | none | 4490 → 4490 | 1190 | 5680 |
| final-2/e9cc34d4-6eb1-4829-8622-3b0570f24e2a | none | 4490 → 4490 | 1190 | 5680 |
| final-2/464124e4-03d5-4be3-a1ac-f25ee0d6207f | none | 4485 → 4485 | 1168 | 5653 |
| final-2/0ce03b0b-e05d-476b-a08d-42de4692f6a8 | none | 4495 → 4495 | 404 | 4899 |
| final-2/3bf51f6f-9559-4c4a-851a-2f1551ac4b7b | none | 4474 → 4474 | 1072 | 5546 |
| final-2/eef68d9a-4f49-4c0f-baaf-b7ff9e3d593e | grafana, prometheus | 4485 → 4485 | 1168 | 5653 |
| final-2/b510f683-95e9-4cb0-8482-482e93409ad0 | none | 4491 → 4491 | 404 | 4895 |
| final-2/94cf6e79-169f-4929-8bcf-fef1ac7e4ddc | elasticloadbalancing | 4474 → 4484 | 1299 | 5783 |
| final-2/6460bfee-6f30-4185-9b60-e114da0d82d5 | grafana, prometheus | 4480 → 4480 | 1168 | 5648 |
| final-2/c0d5bbc8-36b6-4641-9a2f-5faeb3b96ba7 | none | 4495 → 4495 | 404 | 4899 |
| final-2/673d533b-6b84-47de-930d-078426b356d0 | none | 4490 → 4490 | 1190 | 5680 |
| final-2/7cd84341-9393-4947-aa26-f14da8cd17d1 | none | 4474 → 4474 | 1072 | 5546 |
| final-2/b937844d-9536-4725-8830-ef89af3a3da5 | none | 4490 → 4490 | 1190 | 5680 |
| final-2/ce347154-cc1a-41d4-89d4-5d79e4e8860d | none | 4490 → 4490 | 1190 | 5680 |
| final-2/40c96191-31a0-4f9b-b7bb-b6d19b7d9934 | none | 4490 → 4490 | 1190 | 5680 |
| broad/f7bdc81f-5f5b-46e4-8cb8-88cc99257710 | lambda | 4097 → 4496 | 404 | 4900 |
| broad/73e03ef0-86b8-45bc-91b1-2148e8a12e65 | none | 4491 → 4491 | 404 | 4895 |
| broad/c81ea7ea-2559-4e20-8173-47f699e12546 | apigateway, dynamodb, lambda | 0 → 4471 | 210 | 4681 |
| broad/34568752-de05-4ede-a5d9-0d22aafeffc6 | none | 4493 → 4493 | 660 | 5153 |
| broad/5fff70ec-0135-4c61-acda-683e7aebb59a | none | 4488 → 4488 | 1190 | 5678 |
| broad/7e050439-3155-40f7-a612-823e7244ff06 | elasticloadbalancingv2 | 4483 → 4480 | 769 | 5249 |
| broad/bf044f12-fcbf-4155-ae14-17d7921b6288 | elasticache | 4474 → 4486 | 1072 | 5558 |
| broad/b7c1aa22-26fa-45a7-9754-ea487df14e75 | none | 4482 → 4482 | 638 | 5120 |
| broad/2917b836-744c-443e-8a7a-10d97ad8f659 | elasticloadbalancing | 4474 → 4489 | 1299 | 5788 |
| broad/da77c0c2-59a4-4a45-bafe-5ae68abf8318 | none | 4485 → 4485 | 1168 | 5653 |
| broad/14decd94-ff04-45f7-9b4f-5c2a0e0ab35e | none | 4485 → 4485 | 1168 | 5653 |
| broad/a4ce7d9a-54e9-4a64-b158-c0e0896c519f | none | 4490 → 4490 | 1190 | 5680 |
| broad/a9e7620f-df79-4124-b53f-50d0f0d00da1 | none | 4482 → 4482 | 638 | 5120 |
| broad/bf327ada-0041-4c90-bea9-de01039fd1b0 | elasticache | 4474 → 4486 | 1072 | 5558 |
| broad/73bb48ca-8599-48a7-854e-79482225406e | acm, elasticloadbalancingv2 | 4483 → 4486 | 769 | 5255 |
| broad/e6dd4c58-6020-4708-bc4a-306885186454 | none | 4488 → 4488 | 1190 | 5678 |
| broad/5c6df590-c0db-4e15-b602-335adc304e94 | natgateway, vpc | 4493 → 4489 | 660 | 5149 |
| broad/f5fd82a1-8048-4d3e-a78b-f4d2e4ecbd5c | apigateway, dynamodb, lambda | 0 → 4471 | 210 | 4681 |
| broad/113c0c5b-49cc-468b-a712-74c7c2d1adf1 | acm | 4491 → 4493 | 404 | 4897 |
| broad/9872a498-f18a-4a9a-a2fa-919c3ca9e983 | none | 4097 → 4097 | 404 | 4501 |
