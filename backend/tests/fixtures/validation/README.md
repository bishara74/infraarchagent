# Phase 6 validation recordings

Captured on 2026-10-09 with Terraform v1.16.4, after the sole authorized
`make providers` invocation succeeded. Mirror provenance and seven archive
hashes are in `tools/terraform-providers/README.md`; the mirror contains
391,710,515 file bytes (373.56 MiB).

`PYTHONPATH=backend backend/.venv/bin/python
backend/tests/fixtures/validation/capture_terraform.py` reproduces the captures
without downloading. The script uses `ProcessToolRunner`, fresh temporary
homes and Terraform data directories, and black-hole proxies. Each fixture
uses exact random 3.9.1 and the mirror:

- `terraform init -backend=false -input=false -plugin-dir=<mirror>
  -get=false -no-color`
- `terraform validate -json -no-color`

The valid, invalid-resource and invalid-argument fixtures initialized
successfully. Syntax failed init and was still validated to collect its actual
diagnostic. JSON paths are normalized to `/__RECORDED_ROOT__`; source snippets
are omitted, preserving diagnostic titles, details, severity and positions.
Init captures replace temporary roots and mirror paths. No LLM is involved.

Linter captures use Helm v4.3.0+gbec5b06, hadolint 2.15.1, ansible-lint 26.9.0
and promtool 3.15.0. Reproduce with `PYTHONPATH=backend backend/.venv/bin/python
backend/tests/fixtures/validation/capture_linters.py`. Each JSON record includes
the exact command, exit status, source map, and normalized stdout/stderr.
Ansible captures use the actual Code Climate issue-array format and both
observed location representations. All commands use the offline runner.
