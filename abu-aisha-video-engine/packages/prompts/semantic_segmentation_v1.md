# semantic_segmentation_v1 — Abu-Aisha subtitle blocks

Split the German master into subtitle blocks by MEANING and the Shaykh's speech structure — never by a
character or word quota. Each block is anchored to a word range [first, last] of the Arabic transcript.

{{shared_rules}}

Ask for every boundary: Where does a thought end? Where is a natural pause (phrase boundary)? Where does a
new statement start? Where would Abu Aisha switch the subtitle?

Preferred boundaries: sentence/clause completion · rhetorical pause · "Der Gesandte Allahs ﷺ sagte:" as its
own block before the ḥadīth · "Allah ﷻ sagt:" before the āyah · numbered list items (may be one item or even
one word per block) · question → answer · contrast · punch line / conclusion as its own block.

Inside a block, insert "\n" at semantic line breaks (clause boundaries), aiming at roughly 16–26 characters
per line. Target 1–4 lines; up to 6 are allowed when the meaning requires it. Blocks shorter than ~0.7 s
only for deliberate enumeration/emphasis (set "deliberate_fast": true).

Output JSON: {"segments": [{"words": [a, b], "de": "...", "notes": "optional"}]}
