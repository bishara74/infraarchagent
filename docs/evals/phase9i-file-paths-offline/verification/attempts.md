# phase9i: path replay verification record

Python verification commands use INFRAARCH_TEST_BOOTSTRAP=1 and put
tests/bootstrap first on PYTHONPATH. Settings dotenv loading is disabled before
settings instantiate. Full make test uses explicit synthetic owner/app URLs for
the disposable PostgreSQL 16 test cluster under /tmp, normal application grants
and stub inference. No real LLM, cloud service, .env read or new benchmark is used.
Native checks and replay run inside a loopback-only user/network namespace with
installed tools and local provider archives.

The initial focused unit/historical/guard group passes 72 tests. Native Terraform
validation verifies a missing module-relative read becomes valid while the target
artifact's content is unchanged. Final focused logs include additional multiline
HCL/JSON arguments, comments and literal-text injection negatives. The initial
full suite before those parser refinements passes 1,971 tests, with six performance
tests deselected. Final full-suite results are recorded separately in backend.txt.
The final source passes 1,978 tests, with zero failures/skips and six performance
tests deselected (441.82 seconds). The final focused path/report suite passes 45;
native integration passes one. The disposable PostgreSQL process is stopped
cleanly after verification; its session exits with status zero.

An initial replay reached its end-of-run source check while the script was being
cleaned up for lint. The guard rejected finalization because the script's hash
changed. The completed report is regenerated after evaluator sources stabilize;
only matching package/code/tool observations can be reused from the native cache.
No partial report is presented as the completed measurement.

Final review also finds that hcl2 includes newline/comment nodes beside literal
function arguments. These nodes must not make a literal path dynamic. Terraform
JSON's escaped multiline interpolations need a decoded-template fallback; that
fallback is confined to one complete quoted template and cannot reinterpret
ordinary JSON text as injected expressions or declarations. Positive and negative
tests cover both cases. Native replay and the full suite are repeated afterward.

All 201 immutable package inputs are measured over the hash-reconstructed retained
v6 baseline. Ten changed proposals receive native before/candidate validation and
scans; 191 byte-identical packages reuse explicitly labelled prior observations.
The 58 unchanged source proofs and additive repair-kind model AST proof bind
validator, scanner and policy behavior. Original snapshots and historical reports
remain unchanged. Rejected proposals retain original bytes. Two historical
validation errors remain errors; no unknown scans are promoted to passes.

Lint runs Ruff, formatting, mypy on 167 application sources and frontend
ESLint/TypeScript. No separate frontend unit/browser suite is run because no
frontend code changes. Repository/all-ref/reflog and final artifact secret checks
exclude .env files before retrieval and record only findings locations, never
matched values. No push runs.
