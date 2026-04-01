# Response Variety Rollout Gating

This rollout introduces controlled phrasing and structure variation while preserving SGGS reliability requirements.

## Scope boundaries

- Variety is allowed only in opener/transition/closing phrasing and short vs exploratory rhythm.
- SGGS reliability constraints remain unchanged:
  - no fabricated history, Ang numbers, or Gurbani lines
  - Gurbani quotations must come from retrieved SGGS-backed context
  - explicit uncertainty or refusal token when evidence is insufficient

## Phased rollout

1. Shadow eval only
   - Run `tests/evals/eval_harness.py` against `tests/evals/golden_dataset.json`.
   - Track baseline metrics:
     - `opener_repeat_rate`
     - `closer_repeat_rate`
     - `avg_line_repetition`
     - refusal pass rate (`passed/total`)

2. Dev-flag enablement
   - Enable style rotation in non-production traffic.
   - Verify no increase in grounding repair/retry frequency.
   - Verify refusal behavior for unsupported or out-of-domain prompts remains stable.

3. Incremental production ramp
   - Start with low percentage traffic.
   - Continue monitoring style metrics and reliability metrics.
   - Increase traffic only if all gating criteria remain green.

## Gating criteria

- Reliability gates (must pass):
  - No new failures in `test_gurbani_display.py` and `test_llm_synthesis_grounding.py`.
  - No increase in fabricated Ang/line incidents from spot checks.
  - Refusal pass rate remains at or above baseline.

- Variety gates (should improve):
  - Opener and closer repeat rates trend downward from baseline.
  - No increased repetitive section-order patterns in sampled outputs.

## Rollback triggers

- Any confirmed fabricated Gurbani, fabricated Ang citation, or unsupported historical claim.
- Significant rise in grounding retry/repair rates.
- Refusal pass rate regression against baseline.

On rollback, disable style rotation and keep conservative prompt path active while investigating.
