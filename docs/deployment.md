# Clean Ubuntu 24.04 deployment (NFR-04)

Status: **unverified**. These files were statically checked; the author must run
them on a genuinely clean Ubuntu 24.04 amd64 installation. Existing workstation
tests, stub recordings and container recipes are not clean-deployment evidence.

1. Create a separately named Ubuntu 24.04 WSL distribution or a fresh VM. Enable
   systemd in WSL, restart that distribution, and record Windows/WSL/Ubuntu and
   CPU/RAM versions. Do not reuse the author's Python, Node, Docker volumes,
   provider mirror, configuration or home directory. Reserve ports 5432/8000.
2. Copy `tools/deployment/clean-ubuntu.sh` into the clean environment. Supply the
   public HTTPS repository address and the **full 40-character Phase 10 commit**.
   The script installs Git, clones that exact revision, checks Ubuntu/amd64,
   then installs the documented prerequisites. All online work is author-run.

   ```bash
   bash clean-ubuntu.sh https://github.com/OWNER/REPOSITORY.git FULL_COMMIT \
     "$HOME/infraarch-clean" "$HOME/infraarch-clean-evidence"
   ```

   Replace both placeholders first. Exact application dependencies come from
   `backend/requirements.lock` and `frontend/package-lock.json`. The installer
   pins Node 24.21.0, Checkov 3.3.21, Terraform 1.16.4 and Trivy **0.69.3**;
   downloaded binaries are checksum-verified before installation. Ubuntu's
   Python 3.12, Docker/Compose and PostgreSQL 16 container provide the remaining
   prerequisites. OS packages follow Ubuntu updates; record their actual versions.
3. The driver generates database passwords, a master key and a local API key
   locally without printing them. Restart configuration and operator logs stay
   in a mode-0700 folder under `~/.local/state/infraarchagent/`, with mode-0600
   files. Never copy this folder, `runtime.json` or its logs into evidence or Git.
   The application master key must survive restarts and be backed up privately.
4. PostgreSQL uses a separate `infraarch-clean` Compose project. The driver
   installs application dependencies, runs owner migrations, provisions the
   pinned provider mirror, exports schemas, builds the frontend, starts one
   loopback backend, checks health and submits an explicitly **stub** request.
   No LLM service or cloud credentials are needed. It requires three
   `checks_passed` packages; a failure produces `status: failed`, never a pass.
   Provider provisioning can refresh the clone's tool provenance files; retain
   their output separately from the immutable thesis evidence.
5. Open `http://127.0.0.1:8000`, create the first administrator and complete the
   browser checklist below. The backend remains running for these checks.
   Use the PID in private state to stop that specific process afterwards.
   To restart without displaying secrets:

   ```bash
   python3 tools/deployment/private-run.py PRIVATE_STATE/runtime.json \
     backend/.venv/bin/python -m app.server --port 8000
   ```

   Run from the clone root. To stop only this database project:
   `sudo docker compose --env-file /dev/null -p infraarch-clean stop postgres`.
   Do not remove volumes before collecting results.
6. Copy only the generated `health.json`, `versions.json`, `outcomes.json` and
   the filled browser checklist into a **new** dated evidence folder. Record
   failures, omissions, revision, commands, host and UTC times. Run
   `make secret-scan` before committing evidence. Update NFR-04 only after the
   author reviews the complete results. tfsec is superseded by Trivy (D-31).

The driver has a read-only plan mode:

```bash
python3 tools/deployment/clean_deploy.py --checkout /path/to/clone \
  --evidence /path/to/new-evidence
```

Optional local validation coverage uses the existing
`bash tools/install_validators.sh` (Helm 4.3.0, hadolint 2.15.1, promtool 3.15.0,
ansible-lint 26.9.0). Record optional skips honestly; D-35 documents built-in
validation replacing cluster/server-dependent checks.

## Windows browser checklist — no plugins

Repeat independently in current Chrome, Firefox and Edge on Windows. Record the
exact browser version, Ubuntu backend revision and test time. Use the clean
backend, rather than a developer server. Use one temporary reviewer account.

| Browser | Login/setup | New request | Live progress | Compare/files | Review approve/reject/retry | ZIP opens | Settings/account | Console/errors | Result |
|---|---|---|---|---|---|---|---|---|---|
| Chrome, version: ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | unverified |
| Firefox, version: ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | unverified |
| Edge, version: ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | unverified |

For each: reload a progress deep link; verify SSE updates without refreshing;
inspect each variant and validation result; confirm pending ZIP is gated; record
category/reason on approve/reject, verify controls disappear and the labelled ZIP
returns; inspect the decision and lesson preview; test reviewer proposal/admin
approval and direct admin activation; verify Settings and logout/login. For retry,
restart the stub backend with `PIPELINE_DEMO_SCENARIO=review`, then retry Security
with feedback. Inspect download files and readiness/lesson metadata. Record
screenshots at 1280×800 in both OS colour-scheme settings. The application has
one dark console palette; the OS preference does not imply a separate light theme.

## Troubleshooting

| Symptom | Action |
|---|---|
| Docker daemon unavailable | Start Docker/systemd in this distribution; retry the failed step. Do not borrow an existing volume. |
| Port already in use | Stop the identified competing process, or run the backend driver with `--port 8765` and use that URL. Database port 5432 must be free. |
| HTTP 503 schema mismatch | Run owner migrations with the same private runtime configuration, then restart. Never auto-downgrade an ahead schema. |
| Master key not loaded | Restart with the same private runtime state/key version; a newly generated key cannot decrypt existing credentials. |
| Scanner/provider unavailable | Verify pinned tool PATH, mirror archives and exported indexes; do not count a degraded run as portability success. |
| CRLF / `bash\r` errors | In the copied shell script run `sed -i 's/\r$//' SCRIPT.sh`, then `bash -n SCRIPT.sh`. Use LF checkout scripts. |
| Failed author install/build | Keep its nonzero result. Inspect private operator logs locally; sanitise any excerpt before adding it to evidence. |
