# Phase 1 LLM timing spike

Provider: `openai`; max output tokens: 16000.

| Mode | Runs | Median wall s | Max wall s | Output tokens/s | Parsed calls | Truncated calls |
|---|---:|---:|---:|---:|---:|---:|
| full | 1 | 24.575 | 24.575 | 474.47 | 1/1 | **0/1** |
| split | 1 | 0.286 | 0.286 | 0.00 | 0/9 | **0/9** |

- full: **fits 30 s**; truncated 0/1 calls; parsed 1/1; max wall 24.575 s.
- split: **does not fit 30 s**; truncated 0/9 calls; parsed 0/9; max wall 0.286 s.
