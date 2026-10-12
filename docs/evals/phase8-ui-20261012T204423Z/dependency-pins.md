# Phase 8 dependency pins

These are the exact installed direct packages, approved before the single
`npm install --save-exact --ignore-scripts`. Versions/publish dates were verified
through `npm view`; the cutoff was **2026-10-12 17:35:16 UTC**, at least 14 days
after publication. Dates below use the precision retained in the approved plan.
The npm-generated package-lock.json records the complete resolved graph.

| Package | Exact version | Published, UTC |
|---|---|---|
| react | 19.3.0 | 2026-09-09 |
| react-dom | 19.3.0 | 2026-09-09 |
| react-router | 8.4.0 | 2026-09-15 |
| diff | 9.0.0 | 2026-04-13 |
| vite | 8.3.1 | 2026-09-24 |
| @vitejs/plugin-react | 6.1.1 | 2026-08-28 |
| typescript | 6.0.3 | 2026-04-16 |
| @types/react | 19.3.0 | 2026-09-09 |
| @types/react-dom | 19.3.0 | 2026-09-09 |
| vitest | 5.0.2 | 2026-09-25 |
| jsdom | 30.1.1 | 2026-09-22 |
| @testing-library/react | 16.3.3 | 2026-08-27 |
| @testing-library/user-event | 14.6.7 | 2026-09-02 |
| @testing-library/jest-dom | 7.0.1 | 2026-08-09 |
| eslint | 10.11.0 | 2026-09-18 |
| @eslint/js | 10.0.1 | 2026-02-06 |
| typescript-eslint | 8.71.0 | 2026-09-28 17:12:00.356 |
| eslint-plugin-react-hooks | 7.1.1 | 2026-04-17 |
| globals | 17.12.0 | 2026-09-01 |
| @playwright/test | 1.63.0 | 2026-09-04 |
| @types/node | 24.19.0 | 2026-09-25 |
| @testing-library/dom | 10.4.2 | 2026-09-13 |

Runtime is limited to React, React DOM, React Router and jsdiff. The author
approved @types/node and @testing-library/dom as dev allowlist additions.
TypeScript 6.0.3 is the approved compatibility exception to selecting the newest
major. jsdiff supplies declarations, so @types/diff is omitted. No new runtime
package, installation script or agent-downloaded browser was used.

Node engine: >=22.22.2; developed on Node 24 LTS (24.21.0), npm 11.19.0.
Author-installed browser: Chromium 153.0.8010.12 through Playwright 1.63.0.
