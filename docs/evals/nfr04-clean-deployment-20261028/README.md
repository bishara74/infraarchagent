# NFR-04 clean deployment and browser checklist

## Environment (recorded)

| Item | Value |
|---|---|
| Date (UTC) | 2026-10-28 |
| Host OS | Windows 11 Version 26H2 (Build 26300.9711) |
| WSL | WSL 3.0.3.0, kernel 6.18.54.1-1 |
| Clean environment | Fresh WSL distribution `infraarch-clean`, Ubuntu 24.04.5 LTS, x86_64, systemd running |
| CPU / RAM | 8 vCPU / 7.6 GiB |
| Repository revision | `e6ac33785e3a022550b9c3255c87b3dc194838b0` (cloned from GitHub) |
| Python / Node / npm | 3.12.3 / v24.21.0 / 11.19.0 |
| Docker / PostgreSQL | 29.1.3 / 16.15 |
| Checkov / Trivy / Terraform | 3.3.21 / 0.69.3 / 1.16.4 (all checksum-verified at install) |
| Trivy binary SHA-256 | `8266084a71d2e6a2333bc2c69b91c93c26dee9ef39ac2587ace2df54cc9b746b` (identical to the development environment) |
| Optional validators | Helm, hadolint, ansible-lint, promtool not installed (optional; D-35) |
| Scanner note | tfsec is superseded by Trivy 0.69.3 (D-31) |

## Automated deployment result (`outcomes.json`)

| Step | Result |
|---|---|
| Backend dependencies | exit 0 |
| Frontend dependencies | exit 0 |
| Database (separate `infraarch-clean` project) | exit 0 |
| Migrations (schema `0016_fixer_lesson_scope`, current) | exit 0 |
| Provider mirror | exit 0 |
| Provider schemas | exit 0 |
| Frontend build | exit 0 |
| Stub pipeline run `ed893db6-0e6f-454a-8add-2fb8abd332e6` | `success`; cost/performance/security all `checks_passed` (synthetic) |
| Health | status ok, database ok, schema compatible, Checkov/Trivy/Terraform available |

Run window: 2026-10-28 17:05:09 to 17:07:58 UTC. The operator pressed Ctrl+C after
the script had finished; the backend kept running and the results were unaffected.

## Browser checks (no plugins, clean backend at http://127.0.0.1:8000)

| # | Check | Chrome | Firefox |
|---|---|---|---|
| | Version | 156.0.8078.73 (64-bit) | 159.0 (64-bit) |
| 1 | First admin setup, login, reviewer account | OK | OK |
| 2 | New request submitted, stub run starts | OK | OK |
| 3 | Live progress updates without reload; reload restores progress | OK | OK |
| 4 | Comparison cards, each variant's files, findings and validation | OK | OK |
| 5 | Pending download gated with explanation; approve/reject with category and reason; controls disappear; labelled ZIP available | OK | OK |
| 6 | ZIP downloads and opens in Windows | OK | OK |
| 7 | Lessons: reviewer proposal → admin approval; admin lesson active immediately | OK | OK |
| 8 | Settings pages, logout and login | OK | OK |
| 9 | Browser console free of errors | OK | OK |
| | **Result** | **pass** | **pass** |

Engines covered: Chromium/Blink (Chrome) and Gecko (Firefox). Edge was not tested
separately because it uses the same Chromium engine as Chrome. WebKit/Safari is not
available on Windows and was not tested.

Not performed: retry-with-feedback in demo mode (`PIPELINE_DEMO_SCENARIO=review`);
covered by automated tests and earlier manual runs. Screenshots in both OS colour
schemes were not captured.

## Problems observed

- None in the browser checks.
- Optional validators were not installed by the clean-install script (by design).

## Conclusion

NFR-04: **met** for the stated scope. The unmodified backend ran on a clean Ubuntu
24.04 environment with Python 3.12, Checkov 3.x, Trivy (replacing tfsec, D-31) and
PostgreSQL 16, and a pipeline run completed without errors. The frontend ran without
plugins in Chrome and Firefox, covering the two browser engines available on Windows.
Limitations: synthetic (stub) model responses, WSL rather than a physical/VM Ubuntu
host, Edge and Safari not tested separately, optional validators absent.
