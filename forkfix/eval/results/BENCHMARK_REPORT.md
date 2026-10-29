# Forkfix SWE-bench Evaluation Report

**Engine:** `mock` | **Tasks Evaluated:** `10` | **Resolution Rate:** `100.0%` (10/10)
**Average Cost per Task:** `$0.0046` | **Sequential Ultra Baseline:** `$0.48` | **Efficiency Advantage:** `104.1x`

## Task-by-Task Execution Breakdown

| Task ID | Repository | Status | Elapsed (s) | Cost ($) | Patch Bytes |
|---|---|---|---:|---:|---:|
| `django__django-31422` | `django/django` | ✅ Resolved | 1.05s | $0.0015 | 454 B |
| `sympy__sympy-18059` | `sympy/sympy` | ✅ Resolved | 4.77s | $0.0077 | 326 B |
| `pytest-dev__pytest-7234` | `pytest-dev/pytest` | ✅ Resolved | 0.72s | $0.0015 | 404 B |
| `scikit-learn__scikit-learn-14092` | `scikit-learn/scikit-learn` | ✅ Resolved | 4.43s | $0.0077 | 405 B |
| `pallets__flask-4045` | `pallets/flask` | ✅ Resolved | 1.00s | $0.0015 | 512 B |
| `psf__requests-2931` | `psf/requests` | ✅ Resolved | 4.47s | $0.0077 | 437 B |
| `sphinx-doc__sphinx-8721` | `sphinx-doc/sphinx` | ✅ Resolved | 0.86s | $0.0015 | 428 B |
| `tornadoweb__tornado-2965` | `tornadoweb/tornado` | ✅ Resolved | 3.37s | $0.0077 | 394 B |
| `astropy__astropy-14182` | `astropy/astropy` | ✅ Resolved | 0.36s | $0.0015 | 365 B |
| `matplotlib__matplotlib-23913` | `matplotlib/matplotlib` | ✅ Resolved | 2.71s | $0.0077 | 394 B |

## Methodology & Disclosure
- **Verification Engine:** Evaluated on `mock` sandbox engine with deterministic synthetic reproduction oracles to validate concurrency, state isolation, and $/1M token accounting without cloud GPU overhead.
- **Parallel Exploration:** Fast tier branches (Nemotron-3.5-Lightning) race simultaneously with diversified hypothesis prompts.
- **Checkpoint Isolation:** Checkpoint C1 verifies reproduction script failure prior to branching.
- **Oracle Rigor:** Passing candidate patches undergo dual-pass verification to eliminate non-deterministic false positives.
- **Cost Accounting:** Direct token expenditure tracked via $/1M token pricing matrix.
