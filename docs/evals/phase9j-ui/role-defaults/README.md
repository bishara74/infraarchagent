# Independent model defaults — Phase 9j corrective follow-up

The selected-credential Architect fallback affected actual Generator/Fixer
requests as well as the UI. Resolution now checks run, personal, administrator,
then environment for each role independently; specificity precedes the Generators
group only within one tier. The former shared fixture endorsing Architect
inheritance has been corrected.

The browser server uses synthetic credentials, a mocked OpenRouter catalogue and
mocked inference HTTP. Its stub environment also declares a versioned model/low
effort baseline for interactive selected-provider tests; no real LLM calls occur.
The production environment and stored user settings are not modified.

## Screens

All captures are 1280×800 Chromium viewports. Long per-variant source text wraps;
model inputs retain keyboard navigation, focus outlines and full accessible text.

| Capture | Verified state |
|---|---|
| [Architect only](architect-only.png) | Explicit Architect with Generator/Fixer still using their own server defaults. |
| [Per-variant sources](per-variant-sources.png) | Personal Generators group beats the administrator's Cost override; explicit run Security override wins. |
| [My defaults](personal-settings-sources.png) | Personal editing tier and environment fallback. |
| [Administrator defaults](settings-sources.png) | Administrator editing tier, including specific Cost override. |

## Coverage

- Shared 64-case tier/group matrix × all three generator roles in Vitest and
  the actual Python resolver; expected model, thinking and UI source labels.
- Architect isolation at run/personal/admin tiers, with/without selected
  credentials and independent Fixer environment settings.
- Missing role default is unavailable; all explicit roles work without an
  environment model. Explicit null thinking remains provider default.
- Component and input-screen selection/reset/thinking tests retain sparse
  Architect-only POST configuration and independent sibling defaults.
- Real PostgreSQL account API tests freeze and persist all five role selections.
- Actual factory adapters and saved-credential material resolution send mocked
  HTTP: fixed prompts produce byte-identical Generator/Fixer bodies, endpoint,
  method and authorization when only Architect changes. These tests hold prompt
  content fixed to isolate configuration; different real Architect plans can
  naturally change downstream prompt content.
- Existing header benchmark golden-wire fixtures remain unchanged.
- Playwright exercises the actual submission/results API, keyboard selection and
  reset, per-variant sources, Settings previews and page overflow.

Verification logs and the secret-scan report are in [verification](verification/).
Historical runs and existing explicit choices are not rewritten. No migration,
new dependency, public wire/schema change, real inference or push is included.
