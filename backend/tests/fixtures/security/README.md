# Recorded local scanner outputs

Captured on 2026-10-01 with Checkov 3.3.21 and tfsec v1.28.14. `vulnerable/`
contains public S3 access, an unencrypted/public RDS instance, open SSH,
wildcard IAM, and a privileged root container. `fixed/` closes those issues
and satisfies the blocking policy without suppressions. Scanner JSON is kept
as emitted, except for pretty-printing and the original absolute paths.
Tests rebase those absolute paths to their temporary package directory.

From this repository root, the capture commands were:

```sh
checkov -d backend/tests/fixtures/security/vulnerable -o json --quiet --compact --skip-download --skip-results-upload --framework terraform,kubernetes,helm,dockerfile
tfsec backend/tests/fixtures/security/vulnerable --format json --no-color --soft-fail --no-module-downloads
```

The same commands with `fixed` in place of `vulnerable` produced the fixed
outputs. `helm` was not installed; Checkov skipped Helm chart scanning.
