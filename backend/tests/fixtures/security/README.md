# Recorded local scanner outputs

Captured with Checkov 3.3.21, Trivy 0.69.3 and Terraform 1.16.4 on
2026-10-01. Vulnerable/fixed inputs contain Terraform and Kubernetes resources.
The fixed package has only advisory findings under policy 2. Paths are portable:
`/__RECORDED_ROOT__` replaces absolute roots, while relative Trivy `Target`
paths remain relative. Checkov recordings from Phase 5 are retained.

Capture commands (repeat for `fixed` and `syntax_error`):

```bash
TASK_ROOT=$(realpath backend/tests/fixtures/security/vulnerable)
TASK_CACHE=$(mktemp -d)
TASK_ENV=(env -i "PATH=$PATH" "HOME=$TASK_CACHE" LANG=C.UTF-8 "TMPDIR=$TASK_CACHE" HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 ALL_PROXY=http://127.0.0.1:9 http_proxy=http://127.0.0.1:9 https_proxy=http://127.0.0.1:9 all_proxy=http://127.0.0.1:9 NO_PROXY= no_proxy= GIT_TERMINAL_PROMPT=0)
(cd "$TASK_ROOT" && "${TASK_ENV[@]}" trivy config . --format json --exit-code 0 --quiet --skip-check-update --skip-version-check --disable-telemetry --cache-dir "$TASK_CACHE/trivy") > /tmp/trivy-vulnerable.raw.json
(cd "$TASK_ROOT/terraform" && "${TASK_ENV[@]}" "TF_DATA_DIR=$TASK_CACHE/terraform" CHECKPOINT_DISABLE=1 TF_IN_AUTOMATION=1 terraform validate -json -no-color) > /tmp/terraform-vulnerable.raw.json
python3 backend/scripts/normalize_security_fixture.py "$TASK_ROOT" /tmp/trivy-vulnerable.raw.json backend/tests/fixtures/security/trivy-vulnerable.json
python3 backend/scripts/normalize_security_fixture.py "$TASK_ROOT" /tmp/terraform-vulnerable.raw.json backend/tests/fixtures/security/terraform-vulnerable.json
rm -rf "$TASK_CACHE"
```

Terraform exits 1 for diagnostics, including missing providers; that output is
valid JSON. No `init` is run. `syntax_error` contains an extraneous locals label;
Checkov reports zero parsing errors and Trivy exits zero with no findings.
Terraform supplies the critical syntax finding. Separate `unclosed_block`,
`duplicate_argument`, and `missing_newline` inputs have real Terraform outputs.
Native duplicate arguments produce “Attribute redefined”; JSON duplicates
produce “Duplicate argument” or “Duplicate attribute definition”.

`terraform-diagnostics.json` stores 23 independent source/output probes. Each
case was created in an empty temporary `terraform/` directory and captured with
`terraform validate -json -no-color` in the same minimal environment. The tests
can recreate every case using its `files` map, compare its `expected` summary,
and check provider/module/reference/type/schema diagnostics are ignored.

Only FAIL misconfigurations count. Trivy's emitted `AWS-0133` on the vulnerable
RDS instance confirms the sole Trivy variant exemption. It emits `ID` rather
than `AVDID`; the parser preserves that ID without fabricating an AVD prefix.
Helm uses Trivy's built-in renderer; it does not require the Helm executable.

`single_argument_block` is the two-argument one-line HCL error. `helm` is a
templated chart with a privileged container; `remote_module` combines a
registry module with insecure local RDS. Their Trivy/Terraform recordings use
the same capture commands with those directory names substituted. Captures
were made in disposable copies, so scanner caches never enter fixture inputs.
