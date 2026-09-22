# Build-Anleitung – Durūs al-Muhimmah Unterrichtsausgabe

## Benötigte Software

Ubuntu/Debian:

```bash
apt-get install texlive-xetex texlive-lang-arabic texlive-lang-german \
  texlive-latex-extra texlive-fonts-extra texlive-fonts-recommended \
  fonts-noto fonts-hosny-amiri
```

Wichtig: `fonts-hosny-amiri` stellt die Schriften **Amiri** (arabischer Fließtext) und
**Amiri Quran** (für Qurʾān-Ayāt) bereit. Für alle anderen Texte wird **Latin Modern**
(Roman/Sans) verwendet, Teil von `texlive-fonts-recommended`.

Für OCR neuer Scan-Seiten (nur nötig, wenn weitere Lektionen aus dem Arabisch-Scan
transkribiert werden):

```bash
apt-get install tesseract-ocr tesseract-ocr-ara
```

## Projektstruktur

```
buchprojekt/
  sources/            Original-PDFs (arabischer Scan, OCR-Rohtext) – nie verändern
  assets/             Logos (logo-deen.png, logo-kunya.jpg)
  styles/
    colors.tex        Farbpalette (aus den Logos extrahiert)
    preamble.tex       zentrale Präambel: Sprachen, Schriften, Umgebungen
  templates/
    titelseite.tex     Cover/Titelseite
    impressum.tex      Impressum
    vorwort.tex        Vorwort des Bearbeiters
  content/
    gesamtbuch.tex      Treiberdatei fürs Gesamtbuch (ohne Tests)
    lesson-01/
      lesson.tex        Inhalt der Lektion (wird in gesamtbuch.tex eingebunden)
      lesson01.tex       Treiberdatei: Lektion 1 als eigenständiges PDF
      test.tex           Test-Layout zu Lektion 1 (aktuell ohne Fragen)
      lesson01_test.tex  Treiberdatei: Test als eigenständiges PDF
    lesson-02/ …          weitere Lektionen nach demselben Muster
  build/               Ausgabeverzeichnis (aktuell werden PDFs direkt neben den
                        Treiberdateien erzeugt; bei Bedarf umstellen)
  EDITORIAL_NOTES.md    offene Punkte, Unsicherheiten, Quellenprobleme
  SOURCE_MAP.md         Herkunftsnachweis jedes Abschnitts
```

## Bauen

Jede „Treiberdatei" (`*.tex` mit `\documentclass`) wird einzeln mit `xelatex` gebaut.
**Zweimal ausführen**, damit Inhaltsverzeichnis, Kopfzeilen und Referenzen stimmen.

### Gesamtbuch (ohne Tests)

```bash
cd content
xelatex -interaction=nonstopmode gesamtbuch.tex
xelatex -interaction=nonstopmode gesamtbuch.tex
```

Ergebnis: `content/gesamtbuch.pdf`

### Einzelne Lektion

```bash
cd content/lesson-01
xelatex -interaction=nonstopmode lesson01.tex
```

Ergebnis: `content/lesson-01/lesson01.pdf`

### Test zu einer Lektion

```bash
cd content/lesson-01
xelatex -interaction=nonstopmode lesson01_test.tex
```

Ergebnis: `content/lesson-01/lesson01_test.pdf`

## Farben ändern

In `styles/colors.tex`. Jede Lektion hat eine eigene Akzentfarbe (`Lesson01` … `Lesson18`),
zusätzlich die Basis-Palette (`PrimaryGreen`, `DarkGreen`, `DeepestGreen`, `SecondaryGreen`,
`LightSage`, `LightBackground`, `OffWhite`, `NeutralText`, `MutedText`, `Accent`).

## Logo austauschen

Datei in `assets/` ersetzen (gleicher Dateiname behalten, sonst `titelseite.tex` und
`preamble.tex`/`lektionstrennseite` anpassen).

## Neue Lektion ergänzen

1. Ordner `content/lesson-XX/` anlegen (nach Muster `lesson-01/`).
2. `lesson.tex` mit den Umgebungen `lernziele`, `shaykhsagt`, `merke`, `beispiel`,
   `begriffe`, `quranvers`, `zusammenfassung` befüllen (siehe `preamble.tex` für alle
   verfügbaren Umgebungen).
3. Am Anfang `\lektionstrennseite{XX}{XX}{Titel}` setzen (erstes und zweites Argument
   müssen der Lektionsnummer entsprechen, damit die passende `LessonXX`-Farbe greift).
4. `lessonXX.tex` und `lessonXX_test.tex` als Treiberdateien nach dem Muster von
   `lesson-01` anlegen.
5. In `content/gesamtbuch.tex` die Zeile `% \input{lesson-XX/lesson.tex}` einkommentieren
   bzw. ergänzen.
6. In `SOURCE_MAP.md` und ggf. `EDITORIAL_NOTES.md` den Ursprung der Inhalte dokumentieren.

## Wichtige technische Hinweise

- Das `bidi`-Paket (für Arabisch/RTL) **muss** über `\usepackage{polyglossia}` +
  `\setotherlanguage{arabic}` **als letztes** Sprach-/Layoutpaket geladen werden – nach
  `amsmath`, `xcolor`, `graphicx`, `tikz`, `tcolorbox`, `fancyhdr`, `hyperref`. Diese
  Reihenfolge in `preamble.tex` nicht ohne Grund verändern, sonst bricht der Build mit
  einer `bidi`-Fehlermeldung ab.
- Arabischer Text wird über `\ar{...}` (kurze Ehrenformeln etc.) oder direkt per
  `{\arabicfont\begin{Arabic}...\end{Arabic}}` gesetzt. Qurʾān-Ayāt sollten die
  `\quranfont`/`\quran{...}`-Variante (Amiri Quran) nutzen.
- Das Sonderzeichen ʾ (Hamza, U+02BE) wird von der Sans-Schrift nicht sauber dargestellt –
  im Fließtext wird stattdessen ’ (U+2019) verwendet.

## Cover / Hardcover

Noch nicht final umsetzbar – siehe Master-Spezifikation §26: Rückenbreite kann erst nach
Festlegung von Gesamtseitenzahl, Papierstärke und Druckereivorgaben berechnet werden.
`templates/titelseite.tex` liefert bereits das digitale Vordercover-Design als Grundlage.
