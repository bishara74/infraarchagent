# Phase 9m — Request-path threat model

Scope: natural-language request acceptance through prompts, generated-package
checking, remediation and download. Evidence is local/offline; no real key,
dotenv, inference, cloud deployment or external service is used. Traceability:
FR-I-01, FR-A-05, FR-V-03/04, FR-P-04 and NFR-01; decisions are D-61.

## Assets, trust and injection

Requests, generated source, model replies and tool diagnostics are untrusted.
The assets are credential confidentiality, deterministic policy decisions,
package integrity, prompt integrity and reproducible provenance. Direct prompt
injection can influence the requester's plan/package and consume that run's
bounded budget. It cannot directly change application thresholds, profiles,
readiness functions, schemas or approval rules. Outputs remain untrusted and
pass deterministic parsing, scanning and validation; a passing check is not
proof of safe deployment or universal injection detection.

Stored injection has a different reach: a lesson can affect later users/runs.
D-60's bounded normalization/filtering, named ownership, explicit human approval,
four-eyes default, immutable versions, escaped advisory prompt block, frozen run
snapshot, actual-dispatch provenance and sticky kill switch govern that path.
The v2 filter correction does not replace governance. A malicious administrator,
semantic manipulation and self-approval remain residual risks.

The intended direct-injection scope is one run. That is not a claim of host
containment: subprocesses run under the server identity without an OS filesystem
or network namespace sandbox. Parser/tool vulnerabilities, unknown file-reading
semantics, CPU/memory/output exhaustion and trusted-plugin behavior can cross
that boundary. Timeouts/proxies and static guards reduce exposure but do not
prove isolation against arbitrary malicious inputs or tool defects.

## Executable boundary

All commands use argv arrays, a fixed executable allowlist and no shell. See
`backend/app/scanners/runner.py`, `validation/terraform.py`, `validation/gate.py`,
`validation/syntax.py` and `validation/linters.py`.

| Tool | Request-path arguments and effect |
|---|---|
| Terraform | Native syntax: `fmt -write=false -no-color <file>`; generation formatting: `fmt -recursive -no-color terraform`; initialization: `init -backend=false -input=false -plugin-dir=<mirror> -get=false -no-color`, or `-get=true` only after recursive local-module preflight; validation: `validate -json -no-color`. No plan/apply/destroy/import/refresh. |
| Checkov | `-d . -o json --quiet --compact --skip-download --skip-results-upload --framework terraform,kubernetes,helm,dockerfile`; static scanning. |
| Trivy | `config . --format json --exit-code 0 --quiet --skip-check-update --skip-version-check --disable-telemetry --cache-dir <private>`; static configuration scanning, including chart rendering. |
| Helm | `lint <chart> --skip-schema-validation` and `template infraarch <chart> --skip-schema-validation`; no install/upgrade, dependency update/build, API-version discovery or DNS-enable flag. Chart Files access is chart-local; generated Go templates remain untrusted. Schema URL retrieval is avoided by skipping schema validation. |
| Hadolint | `--format json <Dockerfile>`; no image build or RUN execution. |
| Ansible | `ansible-lint --offline --nocolor -f json --project-dir ansible <playbooks>` and `ansible-playbook --syntax-check -i localhost, <playbook>`; no play execution. Static input guards refuse dynamic lookup/query and escaping input paths. |
| Promtool | `check config <file>` or `check rules <file>`; no Prometheus server or scrape loop. Static guards constrain file references, including rule/TLS/auth/service-discovery files, to the package. |

Terraform initialization normally supports network module/provider retrieval.
Here recursive preflight refuses git, HTTP and registry module sources, missing
local modules and escapes. The only permitted module retrieval is package-local.
A generated private `.terraformrc` has filesystem-mirror installation only;
`-plugin-dir` points to the author's existing mirror. Missing provider versions
remain existing validation errors/skips, never downloads. The separate author-run
`terraform providers mirror` command is not a request-path capability. Validation
loads trusted provider schemas; it does not execute provisioners or external
data-source program attributes. No cloud credentials enter the tool environment.

## Confirmed gap and narrow repair

Before 9m, `file_input_guard()` covered file/filebase64/templatefile/fileset/
fileexists but omitted Terraform's file-hashing functions. An offline synthetic
probe showed `filesha256(<outside path>)` returning a missing-file diagnostic
when absent and passing validation when the synthetic outside file existed.
The guard returned no checks. Scanner validation and `.tf.json` native syntax
also bypassed the engine's guard.

The shared process boundary now checks package documents before every Terraform
init/validate call, including both bypass paths. The existing input policy covers
filemd5, filesha1/256/512 and filebase64sha256/512 too. Paths resolve against the
actual evaluation working directory, with path.module/path.root support. Escapes,
.env paths and unverifiable dynamic filenames are refused before process launch.
It uses existing tool-failure/validation handling; no scanner detection rule,
profile, threshold or readiness function changes. This is a specific gap closure,
not a general interpreter sandbox.

## Credentials, prompts, public surfaces and cleanup

`domain/input_rules.py` accepts 10–2,000 stripped Unicode code points, rejects
controls and requires infrastructure intent. `api/pipeline.py` redacts known
secrets before persistence/dispatch. `agents/prompts/architect.py` escapes opening
angle brackets and places input only in the user-description block with a fixed
system instruction treating it as data. Generator prompts consume the locally
validated DeploymentPlan; no raw request reinterpretation is added.

Provider credentials are SecretStr and enter SDK authentication, not prompt
builders. Credential resolution registers decrypted values with the process
redactor; configured API/LLM keys, registered credentials, bearer values and
recognized key formats are redacted. PublicDataSafety protects events, package
persistence/results and archives. SDK debug logging is suppressed; errors and
normalized tool diagnostics omit raw exception/source text. Arbitrary unrecognized
secrets supplied by a user cannot be universally identified by these heuristics.
The application stores no cloud credential configuration for generated tools.

Tool environments contain PATH, private HOME/TMPDIR, language and specific offline
settings. Application/database/provider credentials are not inherited. Proxy
variables point to a closed loopback port, NO_PROXY is empty; this is not an
OS-enforced network block. Ansible roles/collections/temp directories and
Terraform data directories are private. Working-directory resolution stays under
the package. Scanner attempts use cleaned temporary directories; validation state
is reused only within its package and removed on close. Process sessions/groups
are killed on timeout/cancellation, with bounded pipe cleanup. Scanner defaults
are 120 seconds, validator tools 60, native syntax 10, plus existing stage budgets.

## Evidence and limitations

`test_phase9m_tool_inputs.py` covers all eleven function families in HCL/JSON,
init/validate no-launch assertions, scanner and JSON-syntax entrypoints, dynamic
inputs and real package-local hashing. Existing Terraform tests cover remote
sources, recursive local/JSON sources, mirror errors and network namespaces.
Existing scanner/environment/timeout tests cover secret exclusion, explicit
working directories and forked-worker cleanup. Canary integration tests cover
HTTP, events/database and provider failures; complete-body lesson transport
tests preserve disabled/benchmark/no-hook request bytes. These establish the
implemented boundaries, not universal safety of generated infrastructure.
