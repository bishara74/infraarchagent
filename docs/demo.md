# Reproducible defence data (synthetic stub output)

Use a dedicated, migrated demo database with the normal app/owner roles. Keep
real runs and credentials separate. The seed appends records through the public
application services; it never inserts SQL, forges statuses or deletes history.

Start one dedicated backend with the provider mirror and installed scanners:

```bash
LLM_PROVIDER=stub LLM_API_KEY='' PIPELINE_DEMO_SCENARIO=review \
  LESSONS_ADMIN_DIRECT_ACTIVATION=true make run PORT=8765
```

The author supplies database settings normally. Configure the persistent master
key privately if credential storage will be demonstrated. Create the first named
administrator in the UI; the seed prompts for that account password without
printing or saving it. Do not put passwords into command arguments.

From the repository root, using the installed backend development environment:

```bash
backend/.venv/bin/python -m scripts.phase10_demo --base-url http://127.0.0.1:8765 \
  --output .cache/defence-demo/index.json
```

Choose a fresh index path for each execution. Every submitted request explicitly
selects `provider=stub`, `model=stub` and identifies itself as a **Synthetic defence
demo**. The client only accepts loopback HTTP and does not follow redirects or
use environment proxies. It reads no dotenv or API keys. It logs in through the
existing account API, then uses pipeline, review and lesson services.

| Run in the index | Security variant | Cost/performance | Review history |
|---|---|---|---|
| pending | pending_review | checks_passed | No decision |
| approved | engineer_approved | checks_passed | accepted_risk approval with synthetic reason |
| rejected | rejected | checks_passed | operability rejection with synthetic reason |
| retried | checks_passed after retry | checks_passed | Retry feedback/event and original baseline retained |

The approved run also creates one screened, directly activated admin lesson from
its own authenticated decision. The seed leaves the runtime lesson switch as it
was; an active lesson does not imply enabled injection. The index contains only
run IDs, dispositions, labels and the lesson ID, never account secrets, package
contents, invented timings or model-quality claims. Repeated executions create
new UUIDs/timestamps with the same demonstration cases.

Use Recent runs and Settings → Review history / Lessons to present the records.
Open Findings before a decision; after approval/rejection show the compact summary,
primary labelled ZIP and optional lesson section. Demonstrate reviewer proposals
with a temporary reviewer account, then approve them as the administrator.
All generated demo files are synthetic candidate IaC. No real model output,
security assurance or cloud deployment is represented by these fixtures.

If a run cannot reach its expected label, the script stops and leaves its created
synthetic records for diagnosis. Start with the correct `review` stub scenario and
fix missing scanners/mirrors rather than editing database statuses.
