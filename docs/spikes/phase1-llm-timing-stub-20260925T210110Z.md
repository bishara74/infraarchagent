# Phase 1 LLM timing spike

Provider: `stub`; max output tokens: 16000.

| Mode | Runs | Median wall s | Max wall s | Output tokens/s | Parsed calls | Truncated calls |
|---|---:|---:|---:|---:|---:|---:|
| full | 3 | 0.000 | 0.000 | 258128.91 | 3/3 | **0/3** |
| split | 3 | 0.000 | 0.000 | 341608.70 | 27/27 | **0/27** |

- full: **fits 30 s**; truncated 0/3 calls; parsed 3/3; max wall 0.000 s.
- split: **fits 30 s**; truncated 0/27 calls; parsed 27/27; max wall 0.000 s.
