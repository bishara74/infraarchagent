# Author lesson runs — deterministic analysis

One run per configuration demonstrates the lesson mechanism; it is not a measured lesson effect. Plans differ between runs. All judgments below use Generator original files; retained-file changes are reported separately. No LLM, provider request or deployment was performed.

| Run | Variant | Lesson 1: outbound | Lesson 2: logging / duplicates | Lesson 3: public LB / two AZs |
|---|---|---|---|---|
| run1 | cost | not applicable | not applicable | not applicable |
| run1 | performance | not applicable | not applicable | not applicable |
| run1 | security | not applicable | not applicable | not applicable |
| run2 | cost | followed | not applicable | not applicable |
| run2 | performance | unknown | not applicable | not applicable |
| run2 | security | unknown | not applicable | not applicable |
| run3 | cost | unknown | not applicable | not applicable |
| run3 | performance | unknown | not followed | not applicable |
| run3 | security | unknown | not applicable | not applicable |
| run4 | cost | followed | not applicable | unknown |
| run4 | performance | not followed | followed | followed |
| run4 | security | not followed | not applicable | not followed |

Exact request-text hashes: 1 distinct across 4 runs; structured plan hashes: 4 distinct.

## Scope and provenance

Telemetry contains 79 distinct model attempts: {'architect': 4, 'generator_cost': 4, 'generator_performance': 4, 'generator_security': 5, 'fixer': 62}. Lesson-enabled attempts: {'generator_cost': 3, 'generator_performance': 3, 'generator_security': 4}. Scope/set/block-hash mismatches: 0. All lesson-bearing calls are Generator calls; Architect/Fixer calls record no lesson use. The manifest call list omits calls without lesson usage, so telemetry is the comparison source.

## Original versus retained files

| Run / variant | Original → final LB flags | Original → final access-log blocks | Duplicate blocks, original → final | Outbound, original → final |
|---|---|---|---:|---|
| run1 / cost | false, omitted → true | 0 → 1 | 9 → 0 | not followed → not followed |
| run1 / performance | false, omitted → false, omitted | 1 → 1 | 1 → 1 | not followed → not followed |
| run1 / security | false → false | 0 → 0 | 0 → 0 | unknown → unknown |
| run2 / cost | false → false | 0 → 0 | 0 → 0 | followed → followed |
| run2 / performance | false, omitted → false, omitted | 1 → 1 | 1 → 1 | unknown → unknown |
| run2 / security | false, omitted, omitted → false | 1 → 1 | 5 → 0 | unknown → unknown |
| run3 / cost | false → true | 0 → 1 | 0 → 0 | unknown → unknown |
| run3 / performance | false → false | 0 → 0 | 0 → 0 | unknown → unknown |
| run3 / security | false → true | 0 → 0 | 0 → 0 | unknown → unknown |
| run4 / cost | false → false | 0 → 0 | 0 → 0 | followed → followed |
| run4 / performance | false → true | 1 → 1 | 0 → 0 | not followed → not followed |
| run4 / security | false → false | 0 → 0 | 0 → 0 | not followed → not followed |

Lesson 1 reaches all three Generators in runs 2–4; the run-3 security Generator has two attempts. NAT declarations alone are insufficient: `analysis.json` records task-subnet default NAT routes and the NAT placement’s default Internet Gateway route. No VPC endpoint resources occur in these snapshots. Relevant ambiguous network bindings remain unknown.

The run-2 performance original has a duplicate LB declaration containing access logs. After lesson 2, the run-3 performance original has no duplicate but also no access_logs block: that is not full instruction following. Run 4 performance restores access logs in its single LB. This coincidence is not attributed causally to the lesson. Other variants also change despite not receiving lesson 2.

Run-3 cost/security and run-4 performance change internal=false to true during remediation. Run-3 cost and run-4 performance carry checks_passed. These are Fixer-stage changes, not evidence that the Generators ignored internet-facing intent. Run-1 cost also changes to internal=true, but its duplicated original LB prevents a unique static exposure classification.

Run 4 performance attaches its tasks to subnets with an IGW default route and disables public task IPs; its declared NAT has no task-subnet default route. Run 4 security has private NAT routes but its NAT subnet has no default IGW route. These do not establish working outbound access. Other unknown cases include input-dependent subnet instance counts; run 3 security references count.index in a route table without count. The analysis does not assume variable defaults are deployment inputs.

## Plan differences and limits

- run1: plan `892e542bb27facb0a26739f51a775122e90c6c5b3515bcc4ff8fe625fbe7e1d8`, services api-service, alb, rds-db, cloudwatch-logs, autoscaling; public alb; private api-service, rds-db; 1 storage entries.
- run2: plan `5f364a194c4dc7b1098f3e0acf4d65285f534d2699110da7cd95eb82280dda3c`, services api-fargate, api-alb, api-rds, api-ecr, api-cloudwatch; public api-alb; private api-fargate, api-rds, api-ecr; 1 storage entries.
- run3: plan `102ec27f37a024d235138d3b2de71df3d21478be036c201b9c12ada201ad3504`, services app-service, load-balancer, database, secret-manager, log-group; public load-balancer; private app-service, database, secret-manager, log-group; 1 storage entries.
- run4: plan `c4d7970e7b81a0f10d937b74802e4f44f32cbb0d9b40ecc9ac34d6e07f699325`, services vpc-main, subnet-a, subnet-b, natgw, alb, acm-cert, ecr-repo, ecs-cluster, api-service, postgres-db, db-secret, log-group; public alb; private api-service, postgres-db, db-secret, log-group; 1 storage entries.

Static configured network subgraph, exact original/retained maps, bounded resolver, no variable-default deployment assumptions. Distinct literal AZs or indices into the same AWS AZ-name data source are configured diversity only. Logging requires enabled access_logs and no duplicate resource blocks. Followed does not prove runtime startup or deployment.

Distinct configured AZ identities do not prove available capacity or successful deployment. Unknown does not mean followed or not followed. `not applicable` means the lesson was absent or not scoped to that Generator; baseline structural observations remain in the JSON.

Run 4’s self-approved provenance is correct for the older active lesson copy. The author reports a later admin-direct duplicate that was retired. Legacy approval_actor=null was never an approval-time identity snapshot; current history display may join today’s user row (D-60/D-63).
