# Recorded local scanner outputs

Captured on 2026-10-01 with Checkov 3.3.21 and tfsec v1.28.14. `vulnerable/`
contains public S3 access, an unencrypted/public RDS instance, open SSH,
wildcard IAM, and a privileged root container. `fixed/` closes those issues
and satisfies the blocking policy without suppressions. Absolute package
roots in the JSON are replaced with `/__RECORDED_ROOT__`; tests substitute
the temporary package root when loading a recording. No capture-machine path
belongs in a committed fixture.

From this repository root, the capture commands were:

```sh
checkov -d backend/tests/fixtures/security/vulnerable -o json --quiet --compact --skip-download --skip-results-upload --framework terraform,kubernetes,helm,dockerfile > /tmp/checkov-vulnerable.raw.json
tfsec backend/tests/fixtures/security/vulnerable --format json --no-color --soft-fail --no-module-downloads > /tmp/tfsec-vulnerable.raw.json
python3 backend/scripts/normalize_security_fixture.py backend/tests/fixtures/security/vulnerable /tmp/checkov-vulnerable.raw.json backend/tests/fixtures/security/checkov-vulnerable.json
python3 backend/scripts/normalize_security_fixture.py backend/tests/fixtures/security/vulnerable /tmp/tfsec-vulnerable.raw.json backend/tests/fixtures/security/tfsec-vulnerable.json
```

Checkov can exit 1 when it finds violations; the captured JSON is still
valid. Repeat the commands with `fixed` in place of `vulnerable` for the fixed
outputs. The normalization script requires the absolute package root to be
present and checks that the result is JSON. `helm` was not installed; Checkov
skipped Helm chart scanning.
