#!/usr/bin/env bash
# One-time setup: system tools, Python + Node dependencies, local ASR model.
# Usage: scripts/setup.sh [models-dir]   (default: ~/.cache/abu-aisha/models)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODELS="${1:-$HOME/.cache/abu-aisha/models}"

command -v ffmpeg >/dev/null || { echo "Bitte ffmpeg installieren (z. B. apt-get install ffmpeg / brew install ffmpeg)"; exit 1; }
command -v node >/dev/null || { echo "Bitte Node.js ≥ 18 installieren"; exit 1; }

python3 -m pip install -r "$ROOT/services/pipeline/requirements.txt"
(cd "$ROOT/apps/renderer" && npm ci)

mkdir -p "$MODELS"
REL=https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models
if [ ! -d "$MODELS/sherpa-onnx-whisper-large-v3" ]; then
  echo "Lade Whisper large-v3 (ONNX, ~1 GB) …"
  curl -L "$REL/sherpa-onnx-whisper-large-v3.tar.bz2" | tar xj -C "$MODELS"
fi
[ -f "$MODELS/silero_vad.onnx" ] || curl -L -o "$MODELS/silero_vad.onnx" "$REL/silero_vad.onnx"

cat <<MSG

Fertig. In deine Shell-Konfiguration übernehmen:
  export ABU_AISHA_ASR_MODEL_DIR="$MODELS/sherpa-onnx-whisper-large-v3"
  # optional, für Qurʾān-Verifikation (z. B. Tanzil „simple-clean“, Format sura|aya|text):
  # export ABU_AISHA_QURAN_TEXT=/pfad/quran-simple-clean.txt
  # optional, für automatische Übersetzung per Claude:
  # export ANTHROPIC_API_KEY=…
  # optional, falls Chrome nicht automatisch gefunden wird:
  # export REMOTION_BROWSER=/pfad/zu/chrome-headless-shell
MSG
