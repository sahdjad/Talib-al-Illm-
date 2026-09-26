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

**Dritte Design-Rückmeldung, umgesetzt (22.09.2026):**
- Schriften erneut gewechselt: Überschriften jetzt **TeX Gyre Heros**, Arabisch/Qurʾān jetzt
  **Noto Naskh Arabic** (statt Amiri/Amiri Quran) – Nutzerfeedback: die vorige Wahl wirkte
  wie Handschrift ("Kinderschrift"), es sollte "computerschriftartig" aussehen.
- Überschriften (`\section`, `\subsection`, `\subsubsection`, Lektionstrennseiten-Titel)
  werden jetzt automatisch in GROSSBUCHSTABEN gesetzt (`titlesec` + `\MakeUppercase`).
- Silbentrennung am Zeilenende komplett deaktiviert (`hyphenat[none]` + `ragged2e`
  `\RaggedRight` + `\hyphenpenalty=\exhyphenpenalty=10000`) – keine Bindestriche mehr im
  Blocksatz, außer dort, wo sie inhaltlich zum Begriff gehören (z. B. „al-Fātiḥa").
- Satzspiegel deutlich vergrößert (Ränder verkleinert:
  `inner=14mm,outer=10mm,top=12mm,bottom=12mm,bindingoffset=4mm`), die Seite wird jetzt
  wesentlich vollständiger ausgenutzt.
- Cover: Kunya-Logo entfernt, arabischer Buchtitel dafür deutlich größer gesetzt; die Zeile
  „Deenbildungszentrum" wurde vom Cover entfernt.
- Impressum („Hinweis zur Ausgabe"): „Verwendung" und Schlusszeile entinstitutionalisiert –
  nicht mehr an ein konkretes Bildungszentrum gebunden, sondern allgemein an „alle, die
  dieses Buch gemeinsam mit mir lesen und lernen" gerichtet.
- Neuer Abschnitt `templates/worum-es-geht.tex` („Worum es in diesem Buch geht") zwischen
  Vorwort und Inhaltsverzeichnis eingefügt, angelehnt an Sarḥāns eigene Einführung
  (`erlaeuterung-sarhan.md`, Z. 1–95). Enthält die vom Nutzer geforderte Klarstellung, dass
  sich die Bearbeitung durchgehend an Sarḥāns Šarḥ orientiert und keinen eigenständigen Šarḥ
  darstellt.
- **Bugfix Cover-Titelfarbe:** Die rein-arabische Titelzeile auf dem Cover erschien trotz
  gesetzter Farbe (`AccentLight`, dann `OffWhite`) schwarz/dunkel, während inline in
  lateinischen Zeilen eingebettetes Arabisch (z. B. „ibn Bāz `\ar{...}`") korrekt eingefärbt
  wurde. Ursache: Beginnt eine ganze Zeile direkt mit der bidi-`Arabic`-Umgebung, geht die
  von außen gesetzte Farbe beim Zeilen-Reordering verloren. Behoben, indem der Zeile ein
  leerer `\mbox{}`-Anker vorangestellt wird, sodass sie – wie die bereits funktionierenden
  Fälle – als lateinische Zeile mit eingebettetem `\ar{...}`-Block beginnt.

## Aufbau von Lektion 1 (Sarḥān, Z. 96–1479 in `erlaeuterung-sarhan.md`)

Sarḥān trennt in seinem Text klar zwischen fortlaufender Erläuterung (Tafsīr) und
eingeschobenen Testfragen-Blöcken ("Fragen zur Exegese von Sūra X"). Diese Struktur wird
1:1 übernommen:
- **Fortlaufende Erläuterung → `lesson.tex`** (Hauptbuch, keine Testfragen).
- **"Fragen zur Exegese …"-Blöcke → `test.tex`** (separate Test-PDF), mit der
  Original-Nummerierung aus Sarḥāns Buch beibehalten.

### Fortschritt Lektion 1 (Stand 26.09.2026)

| Abschnitt | Status |
|---|---|
| Lernmethode, Tafsīr-Buchempfehlung, Umgang mit dem Qurʾān (Z. 98–186) | ✅ fertig |
| Tafsīr Sūrat al-Fātiḥa (Z. 190–317) | ✅ fertig, inkl. arabischem Urtext |
| Fragen 1–34 (Einführung + al-Fātiḥa, Z. 913–1054) | ✅ in `test.tex` übertragen |
| Tafsīr Āyat al-Kursiyy (2:255, Z. 318–381) | ✅ fertig, inkl. arabischem Urtext |
| Tafsīr Sūrat az-Zalzala (99, Z. 382–419) | ✅ fertig, inkl. arabischem Urtext |
| Tafsīr Sūrat al-ʿĀdiyāt (100, Z. 421–476) | ✅ fertig, inkl. arabischem Urtext |
| Tafsīr Sūrat al-Qāriʿa (101, Z. 478–516) | ✅ fertig, inkl. arabischem Urtext |
| Tafsīr Sūrat at-Takāṯur (102, Z. 518–561) | ✅ fertig, inkl. arabischem Urtext |
| Tafsīr Sūrat al-ʿAṣr (103, Z. 563–592) | ✅ fertig, inkl. arabischem Urtext |
| Tafsīr Sūrat al-Humaza (104, Z. 594–629) | ✅ fertig, inkl. arabischem Urtext |
| Tafsīr Sūrat al-Fīl (105, Z. 631–652) | ✅ fertig, inkl. arabischem Urtext |
| Tafsīr Sūrat Quraiš (106, Z. 654–675) | ✅ fertig, inkl. arabischem Urtext |
| Tafsīr Sūrat al-Māʿūn (107, Z. 677–713) | ✅ fertig, inkl. arabischem Urtext |
| Tafsīr Sūrat al-Kawṯar (108, Z. 715–739) | ✅ fertig, inkl. arabischem Urtext |
| Tafsīr Sūrat al-Kāfirūn (109, Z. 741–756) | ✅ fertig, inkl. arabischem Urtext |
| Tafsīr Sūrat an-Naṣr (110, Z. 758–795) | ✅ fertig, inkl. arabischem Urtext |
| Tafsīr Sūrat al-Masad (111, Z. 797–826) | ✅ fertig, inkl. arabischem Urtext (im Original enthalten) |
| Tafsīr Sūrat al-Iḫlāṣ (112, Z. 828–848) | ✅ fertig, inkl. arabischem Urtext |
| Tafsīr al-Falaq (113, Z. 850–876) | ✅ fertig, inkl. arabischem Urtext |
| Tafsīr an-Nās (114, Z. 878–910) | ✅ fertig, inkl. arabischem Urtext |
| zugehörige Fragen-Blöcke zu allen obigen Sūren (Fragen 35–148, Z. 1055–1479) | ✅ vollständig in `test.tex` übertragen (mit `enumitem`-`resume`, damit die Original-Nummerierung erhalten bleibt) |

**Damit ist Lektion 1 (Text und Test) inhaltlich vollständig** – nichts aus Sarḥāns Erläuterung zu
al-Fātiḥa, dem Thronvers und den 15 kurzen Sūren wurde gekürzt oder weggelassen.

Arabischer Text für die Kurzsūren (99–114) sowie Āyat al-Kursiyy lag in Sarḥāns Quelle
**nicht** vor (0 arabische Zeichen im gesamten 166-seitigen Werk, siehe unten) und wurde wie
bei al-Fātiḥa aus dem canonical Mushaf-Text (Ḥafṣ ʿan ʿĀṣim), sorgfältig mit vollständiger
Taschkīl transkribiert, gesetzt – Standardtext, kein Erfinden von Ayāt, **aber unbedingt vor
Druck Wort für Wort gegen einen gedruckten Mushaf zu verifizieren**, da hier (anders als bei
al-Fātiḥa) noch kein Abgleich mit einem Scan erfolgt ist.

Beide Treiberdateien (`lesson01.tex` und `lesson01_test.tex`) sowie `gesamtbuch.tex` wurden
nach Ergänzung dieser Abschnitte erfolgreich mit `xelatex` (zweimal) durchgebaut, ohne Fehler
oder „Missing character“-Warnungen (nach Nachinstallation des `tex-gyre`-Pakets, siehe
„Offene technische Punkte" unten).

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

- **Build-Voraussetzung `tex-gyre`-Paket (26.09.2026):** `BUILD_README.md` listet die
  benötigten `apt`-Pakete, aber `texlive-fonts-extra`/`-recommended` allein stellen die
  Schriftfamilie „TeX Gyre Heros" (für `\headingfont`) nicht bereit – der Build brach beim
  Testen mit „Font … not loadable" ab. Zusätzlich `apt-get install tex-gyre` nötig; sollte in
  `BUILD_README.md` ergänzt werden.
- **Hartkodierter `\PROJROOT`-Pfad ist Groß-/Kleinschreibungs-abhängig:** In `lesson01.tex`,
  `lesson01_test.tex` und `gesamtbuch.tex` steht
  `/home/user/talib-al-illm-/uebersetzungen/...` (klein geschrieben). In dieser Umgebung heißt
  das Repo-Verzeichnis tatsächlich `/home/user/Talib-al-Illm-/...` (Groß-/Kleinschreibung
  gemischt), wodurch der Build ohne Workaround mit „File not found" abbricht. Für das Testen
  in dieser Sitzung wurde ein Symlink außerhalb des Repos angelegt; im Repo selbst wurde
  nichts geändert, da unklar ist, ob der Pfad in der Zielumgebung des Nutzers ggf. tatsächlich
  klein geschrieben ist. **Bitte prüfen und ggf. `\PROJROOT` in allen drei Dateien anpassen.**
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

**Neue Sektion "Einleitung des Autors" (22.09.2026):** Auf Nutzerwunsch wurde Ibn Bāz'
eigene Einleitung (arabische "مقدمة") zum Originalwerk als eigener Abschnitt
(`templates/einleitung-ibnbaz.tex`) zwischen dem Vorwort des Bearbeiters und "Worum es in
diesem Buch geht" eingefügt.
- Arabischer Urtext: sorgfältig von Hand vom Scan transkribiert (nicht aus dem fehlerhaften
  OCR-Rohtext übernommen) – `sources/durus-al-muhimmah-arabisch-urtext-scan.pdf`, Seite 3.
- Deutsche Übersetzung: `addurus-almuhimmah-ar-de.pdf`, S. 4 ("Einleitung des Autors").
- **Technischer Hinweis:** Noto Naskh Arabic enthält keine lateinischen Klammerzeichen
  `(`/`)` (Missing-Character-Fehler beim Kompilieren). Für die im arabischen Buchtitel
  verwendeten Klammern wurden stattdessen die arabischen Zierklammern `﴾ ﴿` (U+FD3E/FD3F)
  verwendet, die im Font vorhanden sind und in der arabischen Typografie für Buch-/Verstitel
  ohnehin gebräuchlich sind. Bei künftigen Arabisch-Passagen mit Klammern denselben Ansatz
  verwenden statt `(`/`)` oder `\LR{...}` (Letzteres wechselt nur die Schreibrichtung, nicht
  die Schriftart, und behebt das Problem nicht).

## Ausstehende Fragen an den Nutzer

- Schriftwahl ist mit der dritten Rückmeldung (22.09.2026) geklärt: TeX Gyre Heros
  (Überschriften) + Noto Naskh Arabic (Arabisch/Qurʾān) + weiterhin Latin Modern Roman
  (Fließtext). Rückmeldung zur aktuellen Fassung des Covers/Designs steht noch aus.
