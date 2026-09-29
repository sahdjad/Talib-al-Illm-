# longform_clip_scoring_v1 (v1.1 — design only)

Given a full lecture transcript with word timings, find self-contained candidate ranges and score 0–10:
benefit, standalone_comprehension, hook_strength, coherence, duration_fit, source_verification_confidence.
Penalties: dangling pronouns/references, starting mid-evidence, ending before the conclusion, uncertain sources,
repetitive filler. Expand boundaries to complete the thought. Never alter the Shaykh's statement.

{{shared_rules}}
