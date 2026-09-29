# arabic_cleanup_v1

You receive Arabic ASR output as numbered words with timings, grouped into phrases (pauses).
Task: produce `arabic_corrections` — a list of word-level corrections — and `transcript_flags`.

{{shared_rules}}

Allowed:
- fix obvious ASR misspellings of words, especially proper names and Islamic terms, when the evidence is strong
  (grammar, fixed expressions, repetition elsewhere in the clip);
- join words wrongly split by ASR (report as a correction on the first word and an empty `to` on the second);
- normalise punctuation.

Forbidden:
- paraphrasing, completing sentences the speaker did not finish, adding omitted words;
- adding tashkīl.

Every correction: {"word": index, "from": "...", "to": "...", "reason": "...", "lexical_change": true|false}.
Any low-confidence name, book title, quotation, number or cut-off word → a CHECK_TRANSCRIPT flag
{"kind": "CHECK_TRANSCRIPT", "word": index, "time": seconds, "reason": "..."}.

Output JSON only: {"arabic_corrections": [...], "transcript_flags": [...]}
