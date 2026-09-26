# Source Map – Durūs al-Muhimmah Unterrichtsausgabe

Ordnet jeden Buchabschnitt seiner Quelle zu.

| Abschnitt | Quelle | Datei | Status |
|---|---|---|---|
| Titelseite (Arabisch, „ad-Durūs al-Muhimmah…") | Arabischer Urtext (Titel) | `sources/durus-al-muhimmah-arabisch-urtext-scan.pdf`, S. 1 | geprüft |
| Vorwort – Ibn ʿAbd al-Wahhāb-Zitat (AR+DE) | direkt vom Nutzer im Chat geliefert | `templates/vorwort.tex` | vom Nutzer bestätigt |
| Vorwort – Sūrah an-Naḥl 16:18 | Standard-Mushaf-Text + vom Nutzer gelieferte Übersetzung | `templates/vorwort.tex` | Mushaf-Text vor Druck gegenprüfen |
| Vorwort – Haupttext „Vorwort des Bearbeiters" | vom Nutzer im Chat geliefert, redaktionell korrigiert (Anrede) | `templates/vorwort.tex` | vom Nutzer bestätigt (mit Korrektur) |
| Lektion 1 – „Der Shaykh sagt" (Arabisch) | Arabischer Urtext, S. 4, visuell verifiziert | `content/lesson-01/lesson.tex` | geprüft |
| Lektion 1 – „Der Shaykh sagt" (Deutsch) | `addurus-almuhimmah-ar-de.pdf`, S. 4 | `content/lesson-01/lesson.tex` | geprüft, deckt sich mit Arabisch |
| Lektion 1 – Erläuterung (Lernmethode, Tafsīr-Empfehlung, Grundhaltungen) | `erlaeuterung-sarhan-original.pdf` / `erlaeuterung-sarhan.md`, Z. 98–186 | `content/lesson-01/lesson.tex` | didaktisch umformuliert, inhaltlich treu |
| Lektion 1 – Sūrah al-Furqān 25:30 | Standard-Mushaf-Text + Sarḥān-Übersetzung | `content/lesson-01/lesson.tex` | Mushaf-Text vor Druck gegenprüfen |
| Lektion 1 – Tafsīr al-Fātiḥa | `erlaeuterung-sarhan.md`, Z. 188–317 | `content/lesson-01/lesson.tex` | vollständig übernommen |
| Lektion 1 – Tafsīr Āyat al-Kursiyy (2:255) | `erlaeuterung-sarhan.md`, Z. 318–381 | `content/lesson-01/lesson.tex` | vollständig übernommen |
| Lektion 1 – Tafsīr az-Zalzala bis an-Nās (99–114) | `erlaeuterung-sarhan.md`, Z. 382–910 | `content/lesson-01/lesson.tex` | vollständig übernommen |
| Lektion 1 – arabischer Urtext zu Āyat al-Kursiyy und Sūren 99–114 | Standard-Mushaf-Text (Ḥafṣ ʿan ʿĀṣim), da in Sarḥāns Quelle nicht enthalten | `content/lesson-01/lesson.tex` | Standardtext, **vor Druck gegen Mushaf-Scan zu verifizieren** |
| Lektion 1 – Fragen 35–148 (Thronvers + Kurzsuren) | `erlaeuterung-sarhan.md`, Z. 1055–1479 | `content/lesson-01/test.tex` | Original-Nummerierung beibehalten |
| Lektionen 2–18 | Arabisch: `sources/arabisch-ocr-roh/p*.txt` (roh, ungeprüft); Deutsch: `addurus-almuhimmah-ar-de.pdf`; Erläuterung: `erlaeuterung-sarhan.md` | noch nicht angelegt | ausstehend |
| Logo DEEN Bildungszentrum | vom Nutzer als Bild/PNG geliefert (identisch mit `DBZ-App/client/public/logo.png`) | `assets/logo-deen.png` | vom Nutzer bestätigt |
| Logo Kunya „Abū ʿĀʾisha al-Kūmāsī" | vom Nutzer als Bild geliefert (2×) | `assets/logo-kunya.jpg` | vom Nutzer bestätigt |
| Farbpalette | automatisiert aus beiden Logos extrahiert (Pixel-Sampling) | `styles/colors.tex` | eigenständige Designentscheidung |

## Quelldateien im Repo

- `sources/durus-al-muhimmah-arabisch-urtext-scan.pdf` – arabischer Urtext (Scan, 32 S.)
- `sources/arabisch-ocr-roh/p01.txt` … `p32.txt` – OCR-Rohtext je Scan-Seite (ungeprüft)
- `../addurus-almuhimmah-ar-de.pdf` – deutsche Übersetzung (mit arab. Titel), 47 S.
- `../important-lessons-for-the-muslim-ummah-en.pdf` – englische Vergleichsübersetzung, 26 S.
- `../erlaeuterung-sarhan-original.pdf` / `../erlaeuterung-sarhan.md` – vollständige
  Erläuterung von Shaykh Hayṯam Sarḥān, 166 S., Hauptreferenz für Erläuterungsabschnitte
