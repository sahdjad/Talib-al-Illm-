# Editorial Notes – Durūs al-Muhimmah Unterrichtsausgabe

Lebendes Dokument. Hier stehen alle Unsicherheiten, offenen Punkte, Rechtefragen und
Stellen, die vor Druck noch geprüft werden müssen. Nichts hier wurde stillschweigend
gelöst – siehe Regel „Keine Halluzinationen" im Master-Prompt.

## Status: Phase 2 (Design überarbeitet, Lektion 1 im Ausbau)

**Wichtige Korrektur (22.09.2026):** Die vorherige Entscheidung, die Tafsīr-Auszüge aus
Lektion 1 herauszulassen, war **falsch** und wurde vom Nutzer ausdrücklich zurückgewiesen.
Die vorige Version dieser Datei, die das als "eigenständige Entscheidung" dokumentierte, ist
damit überholt. **Verbindliche Anweisung: nichts aus Sarḥāns Buch wird gekürzt oder
weggelassen.** Alle Tafsīr-Abschnitte kommen vollständig in die jeweilige Lektion.

Design komplett überarbeitet: DEEN-Logo entfernt (nur noch Kunya-Logo), neues
Ornament-Muster (eigene Gestaltung, farblich an das Kunya-Logo angelehnt) auf Cover und
Lektionstrennseiten, hellere Grundfarbe, mehr Farbakzente (Gold/Terracotta). Neuer
Vorwort-Text 1:1 nach Vorgabe des Nutzers übernommen.

## Aufbau von Lektion 1 (Sarḥān, Z. 96–1479 in `erlaeuterung-sarhan.md`)

Sarḥān trennt in seinem Text klar zwischen fortlaufender Erläuterung (Tafsīr) und
eingeschobenen Testfragen-Blöcken ("Fragen zur Exegese von Sūra X"). Diese Struktur wird
1:1 übernommen:
- **Fortlaufende Erläuterung → `lesson.tex`** (Hauptbuch, keine Testfragen).
- **"Fragen zur Exegese …"-Blöcke → `test.tex`** (separate Test-PDF), mit der
  Original-Nummerierung aus Sarḥāns Buch beibehalten.

### Fortschritt Lektion 1 (Stand 22.09.2026)

| Abschnitt | Status |
|---|---|
| Lernmethode, Tafsīr-Buchempfehlung, Umgang mit dem Qurʾān (Z. 98–186) | ✅ fertig |
| Tafsīr Sūrat al-Fātiḥa (Z. 190–317) | ✅ fertig, inkl. arabischem Urtext |
| Fragen 1–34 (Einführung + al-Fātiḥa, Z. 913–1054) | ✅ in `test.tex` übertragen |
| Tafsīr Āyat al-Kursiyy (2:255, Z. 318–381) | ⏳ ausstehend |
| Tafsīr Sūrat az-Zalzala (99, Z. 382–419) | ⏳ ausstehend |
| Tafsīr Sūrat al-ʿĀdiyāt (100, Z. 421–476) | ⏳ ausstehend |
| Tafsīr Sūrat al-Qāriʿa (101, Z. 478–516) | ⏳ ausstehend |
| Tafsīr Sūrat at-Takāṯur (102, Z. 518–561) | ⏳ ausstehend |
| Tafsīr Sūrat al-ʿAṣr (103, Z. 563–592) | ⏳ ausstehend |
| Tafsīr Sūrat al-Humaza (104, Z. 594–629) | ⏳ ausstehend |
| Tafsīr Sūrat al-Fīl (105, Z. 631–652) | ⏳ ausstehend |
| Tafsīr Sūrat Quraiš (106, Z. 654–675) | ⏳ ausstehend |
| Tafsīr Sūrat al-Māʿūn (107, Z. 677–713) | ⏳ ausstehend |
| Tafsīr Sūrat al-Kawṯar (108) | ⏳ ausstehend, Zeilen noch zu ermitteln |
| Tafsīr Sūrat al-Kāfirūn (109) | ⏳ ausstehend |
| Tafsīr Sūrat an-Naṣr (110) | ⏳ ausstehend |
| Tafsīr Sūrat al-Masad (111) | ⏳ ausstehend (im Original ggf. nicht enthalten – prüfen) |
| Tafsīr Sūrat al-Iḫlāṣ (112) | ⏳ ausstehend |
| Tafsīr al-Falaq (113) | ⏳ ausstehend |
| Tafsīr an-Nās (114) | ⏳ ausstehend |
| zugehörige Fragen-Blöcke zu allen obigen Sūren | ⏳ ausstehend, in `test.tex` zu ergänzen |

Arabischer Text für die Kurzsūren (99–114) sowie Āyat al-Kursiyy liegt in Sarḥāns Quelle
**nicht** vor (0 arabische Zeichen im gesamten 166-seitigen Werk, siehe unten) und muss wie
bei al-Fātiḥa aus dem canonical Mushaf-Text (Ḥafṣ ʿan ʿĀṣim) gesetzt werden – Standardtext,
kein Erfinden, aber vor Druck gegen einen Mushaf zu verifizieren.

## Arabischer Urtext (Ibn Bāz' Originallektionen, "Der Shaykh sagt")

- Quelle: `sources/durus-al-muhimmah-arabisch-urtext-scan.pdf` (32 Seiten, vom Nutzer als
  Scan bereitgestellt, **kein** Textlayer).
- Verfahren: Tesseract-OCR (Sprache `ara`) für alle 32 Seiten, Rohergebnis in
  `sources/arabisch-ocr-roh/`. OCR-Rohtext ist **nicht** druckreif (enthält typische
  Lesefehler, z. B. vertauschte Buchstaben, doppelte Alif).
- **Nur Lektion 1 ist bisher visuell gegen den Scan verifiziert** (Seite 4 des Scans, exakt
  gegengelesen, stimmt mit der deutschen Übersetzung überein).
- **Lektionen 2–18: noch nicht geprüft.** Seiten-Zuordnung siehe Tabelle unten; OCR-Rohtext
  muss vor Verwendung einzeln gegen die Scan-Bilder gegengelesen werden.

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

Bisher verwendete Ayāt (Sūrah an-Naḥl 16:18 und die erweiterte Ibn-ʿAbd-al-Wahhāb-Bittgebet-
Passage im Vorwort; Sūrat al-Fātiḥa 1:1–7 und Sūrah al-Furqān 25:30 in Lektion 1) wurden nach
Standard-Mushaf-Text (Uthmani, Ḥafṣ-Riwāya) gesetzt – das ist Standardtext, kein Erfinden.
**Vor Druck dennoch gegen einen Mushaf gegenlesen**, wie in der Master-Spezifikation (§35)
verlangt.

## Deutsche Übersetzung des Ibn-Bāz-Grundtextes

Quelle: `addurus-almuhimmah-ar-de.pdf` (47 Seiten). Enthält nur deutsche Übersetzung, keinen
arabischen Fließtext für den Lektionsinhalt selbst (nur arabische Titelseite). Wird als
Referenz für die deutsche Übersetzung der „Der Shaykh sagt"-Blöcke verwendet, gegengeprüft
gegen den arabischen Urtext, wo verfügbar.

## Erläuterung (Sarḥān)

Quelle: `erlaeuterung-sarhan-original.pdf` (166 Seiten, vom Nutzer nachgereichte
Original-PDF, echter Textlayer, vollständig extrahiert in `erlaeuterung-sarhan.md`).
Enthält **0 arabische Zeichen** im gesamten Werk (geprüft) – jegliches Arabisch (Qurʾān-Ayāt,
Ibn-Bāz-Urtext) muss aus anderen Quellen bzw. aus canonical Mushaf-Text ergänzt werden.

## Tests

Sarḥān trennt Erläuterung und Testfragen bereits im Original klar (siehe oben). Diese
Struktur wird beibehalten: Fragen kommen unverändert (Originalnummerierung) in die
separate Test-PDF je Lektion. Zusätzlich wird der Lehrer nach eigenem Unterricht (inkl.
Aufnahmen) eigene Ergänzungsfragen, Arbeitsblätter und Zusammenfassungen beisteuern –
dafür bleibt in `test.tex` Platz vorgesehen.

## Offene technische Punkte

- Weißer/heller Schimmer um Logos: gehört zu den Original-Artworks (Transparenz-PNG mit
  weichem Glow), kein Rendering-Fehler.
- `\headingfont` (Latin Modern Sans) hat keine Kapitälchen (`sc`-Schnitt) – betrifft die
  laufende Kopfzeile „DURŪS AL-MUHIMMAH"; LaTeX fällt automatisch auf Normalschrift zurück
  (kosmetisch, keine Fehlfunktion).
- **Wichtiger Bugfix (22.09.2026):** TikZ `opacity=` innerhalb eines `eso-pic`-Shipout-
  Hintergrunds erzeugte eine defekte ExtGState-PDF-Ressource – der gesamte Seiteninhalt nach
  dem Hintergrund verschwand kommentarlos. Behoben, indem die Transparenz als vorgemischte
  deckende Farbe (xcolor `Farbe1!X!Farbe2`-Mischung) statt echter Alpha-Transparenz berechnet
  wird. **Nicht wieder auf `opacity=` in Shipout-Hintergründen umstellen.**
- Das Sonderzeichen ʾ (Hamza, U+02BE) wird von mehreren Schriften nicht sauber dargestellt
  (erscheint als hochgestellte Ziffer) – im Fließtext wird durchgängig ’ (U+2019) verwendet.
  Bei künftigen Textübernahmen aus den Quellen immer prüfen/ersetzen.
- Schriften (Latin Modern, Amiri, Amiri Quran) sind alle frei lizenziert (SIL OFL bzw. GUST
  Font License) und für kommerziellen Druck ohne Einschränkung nutzbar.

## Ausstehende Fragen an den Nutzer

- Cover/Design: Rückmeldung zum überarbeiteten Entwurf (Muster, Farben, Kunya-Logo) steht
  noch aus.
- Schriftwahl (Serif/Sans/Kombination) wurde gefragt, aber noch nicht beantwortet – aktuell
  weiterhin Latin Modern (Roman + Sans). Bei Bedarf umstellen.
