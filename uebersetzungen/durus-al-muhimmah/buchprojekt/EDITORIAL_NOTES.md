# Editorial Notes – Durūs al-Muhimmah Unterrichtsausgabe

Lebendes Dokument. Hier stehen alle Unsicherheiten, offenen Punkte, Rechtefragen und
Stellen, die vor Druck noch geprüft werden müssen. Nichts hier wurde stillschweigend
gelöst – siehe Regel „Keine Halluzinationen" im Master-Prompt.

## Status: Phase 1 (Machbarkeitsnachweis)

Bisher fertiggestellt: komplettes Satzsystem (XeLaTeX + Polyglossia/Bidi + Amiri-Schrift),
Farbpalette aus den Logos, Titelseite, Impressum, Vorwort, Lektion 1 (Buch + Test-Layout
ohne Fragen). 17 weitere Lektionen stehen noch aus.

## Arabischer Urtext

- Quelle: `sources/durus-al-muhimmah-arabisch-urtext-scan.pdf` (32 Seiten, vom Nutzer als
  Scan bereitgestellt, **kein** Textlayer).
- Verfahren: Tesseract-OCR (Sprache `ara`) für alle 32 Seiten, Rohergebnis in
  `sources/arabisch-ocr-roh/`. OCR-Rohtext ist **nicht** druckreif (enthält typische
  Lesefehler, z. B. vertauschte Buchstaben, doppelte Alif).
- **Lektion 1 ist die einzige bisher visuell gegen den Scan verifizierte und korrigierte
  Lektion** (Seite 4 des Scans, exakt gegengelesen, stimmt mit der deutschen Übersetzung
  überein). Der Text in `content/lesson-01/lesson.tex` ist geprüft und darf als verlässlich
  gelten.
- **Lektionen 2–18: noch nicht geprüft.** Die Seiten-Zuordnung wurde bereits ermittelt
  (siehe unten), aber der OCR-Rohtext muss vor Verwendung im Buch noch einzeln gegen die
  Scan-Bilder gegengelesen werden, genau wie bei Lektion 1.

### Seiten-Zuordnung im Arabisch-Scan (ermittelt, ungeprüft für Lektion 2–18)

| Lektion | Scan-Seite |
|---|---|
| 1 | 4 |
| 2 | 4 |
| 3 | 5 |
| 4 | 6 |
| 5 | 10 |
| 6 | 11 |
| 7 | 11 |
| 8 | 12 |
| 9 | 12 |
| 10 | 14 |
| 11 | 17 |
| 12 | 18 |
| 13 | 18 |
| 14 | 19 |
| 15 | 20 |
| 16 | 21 |
| 17 | 22 |
| 18 | 23 |

## Qur'ān-Ayāt

Bisher verwendete Ayāt (Sūrah an-Naḥl 16:18 im Vorwort, Sūrah al-Furqān 25:30 in Lektion 1)
wurden nach Standard-Mushaf-Text (Uthmani, Hafs-Riwāya) gesetzt – das ist Standardtext,
kein Erfinden. **Vor Druck dennoch gegen einen Mushaf gegenlesen**, wie in der
Master-Spezifikation (§35) verlangt.

## Deutsche Übersetzung des Ibn-Bāz-Grundtextes

Quelle: `addurus-almuhimmah-ar-de.pdf` (47 Seiten). Enthält nur deutsche Übersetzung, keinen
arabischen Fließtext für den Lektionsinhalt selbst (nur arabische Titelseite). Wird als
Referenz für die deutsche Übersetzung der „Der Shaykh sagt"-Blöcke verwendet, gegengeprüft
gegen den arabischen Urtext, wo verfügbar.

## Erläuterung (Sarḥān)

Quelle: `erlaeuterung-sarhan-original.pdf` (166 Seiten, vom Nutzer nachgereichte
Original-PDF, echter Textlayer, vollständig extrahiert in `erlaeuterung-sarhan.md`).

**Editorische Entscheidung zu Lektion 1:** Der Sarḥān-Text zu Lektion 1 ist mit ca. 1400
Zeilen extrem umfangreich, weil er neben der eigentlichen Lernmethode auch eine vollständige
Tafsīr-Auswahl zu Sūrat al-Fātiḥa und allen kurzen Sūren (Juz ʿAmma) enthält. Für die
Kernlektion wurde nur der eigentliche lektionsrelevante Teil verwendet (Lernmethode,
Tafsīr-Buchempfehlung, Umgang mit dem Qurʾān). **Die ausführlichen Tafsīr-Auszüge
(„Auszüge aus dem Exegese-Buch … und Fragen dazu", Zeilen 188–1479 in
`erlaeuterung-sarhan.md`) wurden bewusst nicht in die Kernlektion aufgenommen** und sollten
als eigenständiges Vertiefungsmaterial/Anhang für Lektion 1 behandelt werden. Diese
Entscheidung wurde eigenständig getroffen (siehe Master-Prompt §49, „arbeite eigenständig");
bei Bedarf bitte Rückmeldung geben, falls die Tafsīr-Auszüge doch vollständig ins Buch
sollen.

## Tests

Gemäß Nutzeraussage (Chat vom 22.09.2026): Tests werden vom Bearbeiter selbst erstellt,
basierend auf aufgezeichnetem eigenen Unterricht (inkl. eigener Ergänzungen zum
Sarḥān-Text). `content/lesson-01/test.tex` enthält daher nur das fertige Layout
(Kopfzeile, Namensfeld, Punktefeld) ohne Fragen – bewusst als Platzhalter, nicht
automatisch aus Sarḥān generiert, obwohl Sarḥān z. T. eigene „Fragen"-Abschnitte enthält
(z. B. „Fragen zum Gebet" am Ende der elften Lektion). Diese vorhandenen Fragen könnten als
Inspiration dienen, wurden aber nicht automatisch übernommen.

## Offene technische Punkte

- Weißer/heller Schimmer um das DEEN-Logo auf dem dunklen Cover: gehört zum Original-Artwork
  (Transparenz-PNG mit weichem Glow), kein Rendering-Fehler – bei Bedarf mit dem
  Grafik-Ersteller klären, ob eine Variante ohne Glow gewünscht ist.
- Für Lektionstrennseiten wird aktuell kein Logo verwendet (nur Farbe + Text); eine weiße/
  invertierte Logo-Variante könnte ergänzt werden.
- `\headingfont` (Latin Modern Sans) hat keine Kapitälchen (`sc`-Schnitt) – betrifft die
  laufende Kopfzeile „DURŪS AL-MUHIMMAH"; LaTeX fällt automatisch auf Normalschrift zurück
  (kosmetisch, keine Fehlfunktion).
- Schriften (Latin Modern, Amiri, Amiri Quran) sind alle frei lizenziert (SIL OFL bzw. GUST
  Font License) und für kommerziellen Druck ohne Einschränkung nutzbar.
