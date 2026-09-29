# en_from_de_v1 — English derived from the approved German

Input: the FINAL German blocks (with their line breaks) and, per block, the Arabic words it covers.
Translate each German block into natural English. The German wording controls the editorial meaning; use
the Arabic ONLY to detect accidental drift — do not re-interpret the Arabic independently.

{{shared_rules}}

Add nothing. Remove nothing substantive. Keep tone, Islamic terminology, honorifics and reference styling.
Keep the same block structure (one English block per German block) and similar semantic line breaks.
If a block cannot fit at its duration, propose a paired split point that also splits the German block —
never a separate English timeline.

Output JSON: {"segments": [{"id": "seg_001", "en": "..."}], "drift_warnings": [...]}
