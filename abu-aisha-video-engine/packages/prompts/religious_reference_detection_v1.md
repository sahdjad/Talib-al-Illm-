# religious_reference_detection_v1

Tag spans of the reviewed Arabic transcript as QURAN_QUOTE, HADITH_QUOTE, SCHOLAR_QUOTE, BOOK_REFERENCE,
HISTORICAL_FACT, LEGAL_THEOLOGICAL_CLAIM, HONORIFIC or NORMAL_SPEECH.

{{shared_rules}}

- Qurʾān: propose sūrah:āyah candidates ONLY; verification is done by the Qurʾān text matcher (quran.py),
  never by you. Abbreviated recitations are allowed — do not pretend the whole āyah was recited.
- Ḥadīth: you may say "likely a ḥadīth"; you may NOT supply a collection, number or grading unless the Shaykh
  said it. Status is CHECK_REQUIRED unless verified by a human/verification adapter.
- Books: Arabic title/author without ḥarakāt when reliable, format "📚 [author]، [title]".
- Dates/explanations are EDITORIAL_CONTEXT suggestions, never part of spoken subtitles.

Output JSON: {"references": [...], "editorial_notes": [...]} with status CHECK_REQUIRED unless verified.
