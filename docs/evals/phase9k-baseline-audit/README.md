# Phase 9k baseline architecture audit

Independent deterministic observation of the two recorded real broad-v1 rounds.
No inference, rescans or changes to historical evidence or IaC. `audit.json`
records all **40** source snapshot hashes, **40** plan observations and **120**
package observations, validated against committed run/quality records. Its input
manifest hashes committed evidence; analysis_sources hashes the classifier and
existing parser/resolver sources.

Retained configured Terraform schemes: **37 public, 7 internal, 73 absent,
3 unknown**. Plan, original and retained observations are separate. Absent means
no explicit AWS LB declaration, not proof of a private architecture. Dynamic
expressions, external modules and parse failures remain unknown. Internal=false
means configured internet-facing scheme, not proof of deployed reachability.

Omitted aws_lb/aws_alb.internal follows the documented default false from the
[pinned AWS provider reference](https://github.com/hashicorp/terraform-provider-aws/blob/v6.68.0/website/docs/r/lb.html.markdown).
Custom providers and omitted classic ELB scheme remain unknown. No scanner,
profile, acceptance or readiness rule is changed.

Reproduce into a fresh destination (the raw snapshots remain untracked):

```bash
PYTHONPATH="$PWD/backend" backend/.venv/bin/python -m scripts.phase9k_audit --output /tmp/phase9k-new-audit.json
```

Run from backend with its Python on PATH, or set PYTHONPATH to the absolute
backend directory when invoking from the repository root. This tool does not
instantiate operator settings or read dotenv. Source paths in audit.json are
relative to .cache/; no source contents are committed.
