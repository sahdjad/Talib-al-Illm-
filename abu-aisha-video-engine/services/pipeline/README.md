# Pipeline service (Python)

`python -m abu_aisha <command>` · `uvicorn abu_aisha.api:app` · tests: `pytest tests/unit` (repo root of the engine).

## Stages and job states (spec §30.7)

| Stage | Module | Writes | Notes |
|---|---|---|---|
| ANALYZING | `media.py` | `source.probe`, `visual.analysis/stage/mask_auto/freeze_time/mode` | content box (letterbox & pre-baked gradients), face-centred crop, burned-in text bands, first usable frame, audio peak |
| TRANSCRIBING | `asr.py` | `transcript.*` | Whisper large-v3 ONNX (sherpa-onnx) + Silero VAD; word anchors = VAD phrases + energy dips |
| TRANSLATING_DE / SEGMENTING / TRANSLATING_EN | `llm.py` → `pipeline.apply_editorial` | `timeline`, `titles`, `references`, `editorial_notes` | Claude (2 passes: DE master + blocks, then EN from final DE) or `file:` import |
| VERIFYING | `pipeline.verify_references`, `quran.py`, `qa.py` | `references`, `qa` | cue-phrase detection, Qurʾān text match, 12 QA gates |
| COMPOSING | `layout.py`, `render_input.py` | `timeline[].layout`, `visual.boxes` | dynamic font fit with the renderer's font files |
| RENDERING | `pipeline.render` → `apps/renderer/render.mjs` | `renders/`, `previews/`, `render_history` | FFmpeg prepares stage/freeze/audio; Remotion composites; FFmpeg muxes the original audio |

Failures are appended to `errors[]`; the state stays at the last successful stage and `run` resumes (§29).

## ASR notes

* **Byte-split tokens:** sherpa-onnx decodes each BPE token separately, which silently drops Arabic letters whose
  UTF-8 bytes span two tokens (`الزوج` came out as `الوج`). `asr.py` feeds sherpa a tokens file whose symbols
  are the hex of the original bytes and joins the bytes itself (`_hex_tokens_file`, `_decode_tokens`).
* Word timings are approximate *inside* a phrase but exact at pauses — subtitle blocks are anchored to words and
  pauses, and every boundary can be moved to another word in the UI (`boundary`).
* `ABU_AISHA_ASR_MODEL_DIR` must point at a sherpa-onnx Whisper directory (`*encoder*.onnx`, `*decoder*.onnx`,
  `*tokens.txt`); `silero_vad.onnx` is looked up in its parent or via `ABU_AISHA_VAD_MODEL`.

## Editorial package (provider output)

```json
{
  "provider": "...", "prompt_versions": {...},
  "speaker": {"arabic_display": "...", "intro_line": "🎙️ ..."},
  "arabic_corrections": [{"word": 11, "from": "الزوج", "to": "الزوجين", "reason": "...", "lexical_change": true}],
  "transcript_flags": [{"kind": "CHECK_TRANSCRIPT", "word": 81, "time": 61.07, "reason": "..."}],
  "segments": [{"words": [0, 5], "de": "… solange es zu den\nnützlichen Dingen gehört.", "en": "...", "notes": "..."}],
  "titles": {"chosen": {"de": "...", "en": "..."}, "suggestions": [...]},
  "references": [...], "editorial_notes": [...], "trim_suggestion": {...}
}
```

Blocks must cover every transcript word exactly once and in order (`llm.check_coverage`) — nothing added,
nothing dropped. `\n` inside a block is a semantic line break the fitter keeps if at all possible.

## Claude provider

`llm.ClaudeProvider` uses the Anthropic Python SDK (`claude-opus-5-5` by default, override with
`ABU_AISHA_LLM_MODEL` or `--provider <model id>`), streaming, structured JSON output (`output_config.format`),
`effort: high`, and server-side refusal fallbacks (`fallbacks: "default"`, beta `server-side-fallback-2026-07-01`)
so a declined request is retried on a fallback model instead of failing. Credentials are resolved by the SDK
(`ANTHROPIC_API_KEY`, auth token, or an `ant auth login` profile). Unavailable LLM → `LLMUnavailable`; the project
keeps its analysis/ASR state and `run` resumes later.

## Render input contract

`render_input.build()` produces the JSON described by `apps/renderer/src/types.ts`. The renderer draws only what
is in it: stage video/still, mask, intro (freeze frame, speaker line, fitted title), subtitle blocks with their
fitted lines, editorial lines (only `VERIFIED_*`/`APPROVED`), brand lockup. DE and EN inputs differ only in text.

## Environment variables

| Variable | Purpose |
|---|---|
| `ABU_AISHA_ASR_MODEL_DIR` | Whisper ONNX model directory (required for ASR) |
| `ABU_AISHA_VAD_MODEL` | Silero VAD file (optional) |
| `ABU_AISHA_QURAN_TEXT` | canonical Qurʾān text for verification (optional) |
| `ABU_AISHA_LLM_MODEL` | Claude model id (default `claude-opus-5-5`) |
| `ABU_AISHA_PROJECTS` | projects directory (default `data/projects`) |
| `REMOTION_BROWSER` | Chrome/headless-shell path if not auto-detected |
