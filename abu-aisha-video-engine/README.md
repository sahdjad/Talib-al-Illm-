# Abu Aisha al-Kumasi – Video Engine (Core v1)

Aus einem arabischen Shaykh-Clip werden **zwei review-fertige Hochformat-Videos (Deutsch + Englisch)** im
bestehenden Abu-Aisha-Stil: Originalton, 4-Sekunden-Intro, weicher schwarzer Verlauf, sinngemäß getrennte
Untertitel, Branding – plus Transkript, Übersetzungen, Quellen und QA-Bericht.

InShot wird nicht ferngesteuert – der InShot-Arbeitsablauf ist als programmierbare Pipeline nachgebaut. Am Ende
prüfst du nur noch die markierten Stellen und machst bei Bedarf Sound/Bass in InShot.

```
Clip ─► Analyse ─► Arabisch-ASR (lokal) ─► Arabisch prüfen ─► Deutsch (Master) ─► Sinnblöcke
     ─► Englisch aus finalem Deutsch ─► Quellen/Qurʾān-Prüfung ─► Layout (Maske, Schriftgröße)
     ─► Vorschau ─► QA-Gates ─► 1080×1920 DE + EN ─► Textpaket
```

## Beispiel im Repo: Shaykh Sulaymān ar-Ruḥaylī – „Was macht das Eheleben schön?“

`data/projects/ruhaili-eheleben/` ist ein vollständig durchgelaufenes Projekt (das hochgeladene Video):

| Datei | Inhalt |
|---|---|
| `renders/AbuAisha_DE_1080x1920.mp4`, `…_EN_…` | fertige Videos (vollständiger Clip, 65 s inkl. Intro) |
| `text/transcript_ar.txt` | Arabisch geprüft + ASR-Rohfassung + Korrekturprotokoll |
| `text/translation_de.txt`, `translation_en.txt` | Blöcke mit Zeiten + Fließtext |
| `captions/de.srt`, `en.srt` | Zusatz-Untertitel (Zeiten passend zum fertigen Video) |
| `text/references.md`, `text/qa_report.md` | Quellen, redaktionelle Ergänzungen, QA-Gates, Prüfliste |
| `project.json` | die einzige Wahrheit – daraus lässt sich alles neu rendern |
| `editorial/editorial_v1.json` | die redaktionelle Fassung (Import) |

`data/projects/ruhaili-eheleben-kurz/` ist die Variante nach dem **Trim-Vorschlag** (7,6–59,7 s): ohne den
angeschnittenen Satzanfang „… solange es zu den nützlichen Dingen gehört“ und ohne den abgeschnittenen Satz am
Ende. Der Standard-Render kürzt nie still – Kürzen ist immer deine Entscheidung. (Die Kurzfassungs-Videos sind
nicht im Git, um das Repo schlank zu halten: `python3 -m abu_aisha render ruhaili-eheleben-kurz` erzeugt sie neu.)

## Schnellstart

```bash
scripts/setup.sh                      # ffmpeg/Node vorausgesetzt; lädt Whisper large-v3 (~1 GB)
export ABU_AISHA_ASR_MODEL_DIR=~/.cache/abu-aisha/models/sherpa-onnx-whisper-large-v3
export ANTHROPIC_API_KEY=…            # für die automatische Übersetzung (optional)

cd services/pipeline
python3 -m abu_aisha new fawzan-1 --media ~/Downloads/clip.mp4 --speaker "الشيخ صالح الفوزان حفظه الله"
python3 -m abu_aisha run fawzan-1 --provider claude-opus-5-5     # alles bis zu den finalen Videos
```

Oder mit Oberfläche: `scripts/serve.sh` → <http://localhost:8765> (Upload → Text → Timeline → QA → Export).

### Typische Anweisungen

| Du willst … | Befehl |
|---|---|
| kein Intro | `new … --no-intro` oder `intro NAME off` |
| Audio + Bild statt Video | `new … --mode audio_visual --background bild.jpg` |
| Widerlegung (stärkere Intro-Wirkung) | `new … --profile rebuttal` |
| eigenen Titel | `new … --title-de "…" --title-en "…"` oder `title NAME --de … --en …` |
| schwarze Fläche höher | `mask NAME --start 0.40` (Anteil der Bildhöhe; `--auto` zurück) |
| Block ändern | `set-de NAME seg_004 "Text\nmit Sinn-Umbruch"` → EN wird *veraltet* → `regen-en NAME` oder `confirm-en` |
| Block teilen / verbinden | `split NAME seg_013 65 --de "Teil 1" "Teil 2" --en "…" "…"` · `merge NAME seg_012 seg_013` |
| Gemini-Transkript nutzen | `import-transcript NAME transkript.txt` (wird an den Ton ausgerichtet) |
| Kurzfassung | `clone NAME NAME-kurz --use-trim-suggestion` oder `--trim-in 6.9 --trim-out 60` |
| nur Vorschau / Standbilder | `render NAME --preview` · `render NAME --stills 30,450 --debug` |
| Status / Freigabe | `status NAME` · `verify NAME` · `approve NAME` |

## Was hart geregelt ist – und was adaptiv

**Hart:** 9:16 · Originalstimme, 0 dB, keine KI-Stimme · Deutsch ist Master, Englisch nur aus finalem Deutsch ·
keine erfundenen Quellen (unsicher = `CHECK_REQUIRED`, wird **nie** eingeblendet) · gesprochen ≠ redaktionell
(eigene Spur, kleiner, andere Farbe) · Intro standardmäßig 4,0 s · Branding immer sichtbar · keine
Auto-Veröffentlichung.

**Adaptiv:** Maskenhöhe (verdeckt eingebrannte Schrift, erhält möglichst viel Bild), Bildausschnitt (auf das
Gesicht zentriert), Schriftgröße je Block (48–86 px, Sinn-Zeilen haben Vorrang), Zeilenzahl (1–4, bis 6),
Blocklänge (nach Sinn und Sprechpausen, nicht nach Zeichen).

## Aufbau

```
apps/renderer/        Remotion (React) – Classic-Theme: Intro „classic_blade“, Maske, Untertitel, Branding
apps/web/             Review-Oberfläche (ohne Build-Schritt, wird von der API ausgeliefert)
services/pipeline/    Python: Analyse, ASR, Projektmodell, Layout, QA, Exporte, LLM-Provider, CLI, FastAPI
packages/brand/       Logo (aus deinem Kunya-Logo extrahiert, transparent), Schriften (OFL)
packages/prompts/     versionierte Redaktions-Prompts (werden je Projekt mitprotokolliert)
packages/schema/      Standardkonfiguration v1 (Spec §40)
data/projects/        Projekte (Medien/Zwischendateien sind per .gitignore ausgeschlossen)
tests/unit/           Invarianten: Abdeckung aller Wörter, keine Blitz-Lücken, STALE_EN, Maske, Trim, Qurʾān …
```

Technische Details: [`services/pipeline/README.md`](services/pipeline/README.md).

## Offene Punkte / bewusst noch nicht (v1.1+)

- **Original-Lockup:** Dein weißes Lockup (Tropfen-Logo + Schriftzug + Social-Icons) lag nicht als Datei vor. Das
  Branding nutzt die Kalligrafie aus deinem Kunya-Logo + Wortmarke „Abu Aisha al Kumasi“ + Trennlinie + Icons.
  Lege dein Original als transparentes PNG nach `packages/brand/assets/` und trage es in `defaults.json` ein.
- **Schrift:** Die InShot-Schrift ist nicht sicher identifiziert – Roboto Slab ExtraBold ist Platzhalter
  (Konfigurationswert `fonts.subtitle`). Mit einem deiner Referenzvideos lässt sich das 1:1 kalibrieren.
- **Qurʾān-Verifikation** braucht eine lokale, lizenzkonforme Textdatei (`ABU_AISHA_QURAN_TEXT`). Ohne sie bleiben
  Qurʾān-Stellen `CHECK_REQUIRED` (nichts wird geraten). Ḥadīth-Quellen werden nie automatisch verifiziert.
- Langvortrag-Analyse/Clip-Vorschläge, grünes Theme, 4K-Profil: Prompts/Schema sind vorbereitet, Umsetzung v1.1.
