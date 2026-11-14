# Final test run, 14 November 2026

Revision: v1.1.1 (working tree on top of 35a86b6, committed and tagged as v1.1.1 together with these logs)
Date: 2026-11-14
Host: WSL2 6.18.58.1-microsoft-standard-WSL2, 8 vCPU, ~7.6 GiB
Results: pytest 2958 passed / 6 deselected (perf); vitest 485 passed (47 files); playwright 37 passed; lint clean (ruff, mypy 194 files, eslint, prettier, tsc)

Notes:
- All runs used the stub LLM provider. The provider=openai lines in the Playwright log come from its in-process mock transport; no real provider was called.
- The backend suite ran against a disposable, loopback-only PostgreSQL instance instead of the Docker Compose database.
- Commands: make test, make frontend-test, make test-e2e, make lint (output captured with tee).

SHA-256:
ba9e74027d627671f9b50581df74fe4d8e2666532d007fa23370f2f531ad0b6b  backend-pytest.txt
dccef7e415a6daed9ea2ea495641ebbedf530a75ac39ec1d4415c3f177789b92  e2e-playwright.txt
d259ee8189adb764b80db957d23443a9d1d2647caafcf6ca4e8fadcfe9568d8b  frontend-vitest.txt
bf84e62fc145541b5ab4a67a85bc81ca1d928628cc0759b3e46c6e5fb0661e79  lint.txt
