# Šarḥ al-Fatwā al-Ḥamawiyyah (deutsch)

Deutscher Šarḥ zur *al-Fatwā al-Ḥamawiyyah* von Šayḫ al-Islām Ibn Taymiyyah رحمه الله.
Erklärung: Abū Muḥammad as-Sanzakī. Matn und Šarḥ sind im Buch strikt getrennt
(„هذا المتن“ / „وهذا الشرح“).

- **`Sharh-al-Fatwa-al-Hamawiyyah.pdf`** – fertiges A4-Buch (103 Seiten, 5 Teile, 70 Abschnitte)
- **`buchprojekt/`** – Satzprojekt (Node.js → HTML → Chromium → PDF)
  - `content/*.txt` – Buchtext (Markup siehe `STYLE.md`), `content/_hinweise.html` – Hinweisseite
  - `build.js`, `render.js` – Bau; `tocpages.py` (Seitenzahlen im Inhaltsverzeichnis), `preview.py`, `fill.py` (Prüfhilfen)
  - `ARBEITSNOTIZEN.md` – Notizen zur Quellenlage (Pfade darin beziehen sich auf die Arbeitsumgebung)
- **`quellen/`** – Matn arabisch (Seiten 36–61, PDF und Abschrift) und die Niederschrift der 13 Unterrichte

## Neu bauen
```
cd buchprojekt
npm install
node render.js        # erzeugt out/Sharh-al-Fatwa-al-Hamawiyyah.pdf
```
(`playwright-core` mit installiertem Chromium nötig; `render.js` verweist auf dessen Pfad.)

## Offene Punkte
- Arabischer Matn der Buchseiten 31–35 und nach S. 61 lag nicht vor → aus der Rezitation des Šāriḥ übersetzt (im Buch vermerkt).
- Zu einigen Salaf-Aussagen (Teil V) gibt es keine Erklärung in den Aufnahmen.
- Hadith-Quellen und Buchangaben des Šāriḥ vor dem Druck gegenprüfen.
