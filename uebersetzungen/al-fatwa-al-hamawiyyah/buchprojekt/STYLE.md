# STILLEITFADEN – Šarḥ al-Fatwā al-Ḥamawiyyah (bitte nach jeder Kontextkürzung neu lesen)

## Projekt / Pfade
- Satzprojekt: /tmp/claude-0/-home-user-DBZ-App/9f000e22-9720-5a4f-a995-52937d58ca31/scratchpad/book  (build.js, render.js, content/*.txt, out/)
- Quellen: scratchpad/sharh/a.txt (Transkription, 7662 Zeilen, Unterricht-Starts: U1=3,U2=523,U3=930,U4=1347,U5=1731,U6=2255,U7=3170,U8=3861,U9=4756,U10=5414,U11=5975,U12=6767,U13=7293)
- Arab. Matn S.36-61: scratchpad/sharh/work/matn_ar.txt ; Seitenbilder: scratchpad/sharh/img/b01..b26.png
- Bisherige dt. Matn: scratchpad/hamawiyyah/Discipline-German-Books-Archive/01-Muqaddimah/src/content.js (Muqaddimah) und 02-.../src/content_ham.js (ʿuluww-Teil bis "verneint es!")
- Notizen Pass 1: scratchpad/sharh/work/notes_pass1.md
- NICHT ins DBZ-App-Repo committen. Alles bleibt im Scratchpad; Auslieferung per SendUserFile.
- Build: `cd book && node build.js` (nur HTML + Qur'an-Check), `node render.js` (PDF, 2-Pass TOC) -> out/Sharh-al-Fatwa-al-Hamawiyyah.pdf
- PDF-Seiten ansehen: pypdfium2 -> PNG -> Read-Tool (pdftoppm gibt es NICHT)

## Sprecher / Rollen
- Matn = Šayḫ al-Islām Ibn Taymiyyah رحمه الله. Erklärer (Šāriḥ) = Abū Muḥammad as-Sidjākī (Schreibung laut Nutzer; frühere Archive: "as-Sanzakī" -> im Abschlussbericht beim Nutzer nachfragen).
- Frage des Fragestellers und einleitende Notiz sind NICHT von Ibn Taymiyyah -> eigener Matn-Block mit eigener Beschriftung: `[[MATN Die Frage an Šayḫ al-Islām]]`, `[[MATN Einleitende Notiz zur Fatwa]]`.
- Matn und Šarḥ nie vermischen. Matn-Block = nur übersetzter Text; Šarḥ-Block = Erklärung. Zitate des Šāriḥ aus Dritten (Ibn al-Qayyim, ar-Rāzī, Imam Mālik ...) stehen im Šarḥ und werden benannt.
- Gegnerische Positionen immer als Fremdposition formulieren ("Sie behaupten:", "Nach ihrer Auffassung ..."), nie als Aussage des Autors.

## Ehrenformeln (Nutzervorgabe)
- Allah ﷻ (nach Nennung; nicht bei jeder Nennung nötig, aber bei erster Nennung je Absatz üblich; im Matn wie in früherer Übersetzung konsequent), Muḥammad ﷺ, der Prophet ﷺ
- Ṣaḥābah: رضي الله عنه / رضي الله عنها / رضي الله عنهما / رضي الله عنهم ; verstorbene Gelehrte: رحمه الله
- Arabische Schrift im Fließtext wird vom Builder automatisch als RTL-Span gesetzt. Nur ﷻ ﷺ und diese Formeln arabisch schreiben.
- Ibn Taymiyyah/Šayḫ al-Islām: "Šayḫ al-Islām Ibn Taymiyyah رحمه الله" beim ersten Auftreten eines Abschnitts, sonst kurz "Šayḫ al-Islām" / "Ibn Taymiyyah" (رحمه الله nicht dauernd wiederholen, aber an Absatzanfängen von Matn-Labels automatisch).

## Transliteration (einheitlich!)
š ḫ ṯ ḏ j(=ج) ġ ṣ ḍ ṭ ẓ ḥ ʿ ʾ ā ī ū ; Begriffe: Šarḥ, Šāriḥ, Matn, Qurʾān, Sunnah, Ḥadīth (Pl. Aḥādīṯ), Ṣaḥābah, Tābiʿūn, Salaf, Ḫalaf, ʿAqīdah, Ṣifāt, Taʾwīl, Taḥrīf, Taʿṭīl, Takyīf, Tamthīl, Tafwīḍ, Tašbīh, Tajsīm, Takhyīl→**Taḫyīl**, Tajhīl, Mufawwiḍah, Muʾawwilah, Mutakallimūn, Ašāʿirah (Sg. Ašʿarī), Māturīdiyyah, Muʿtazilah, Jahmiyyah, Kullābiyyah, Murjiʾah, Falāsifah, Bāṭiniyyah, Nuṣayriyyah, Ismāʿīliyyah, Qarāmiṭah, Ahl as-Sunnah wa-l-Jamāʿah, ʿUluww, Istiwāʾ, Fiṭrah, Ijmāʿ, Ṭāġūt/Ṭawāġīt, Dunyā, Jannah, Dschahannam→Jahannam, Šīʿah, Ṣūfiyyah.
- Orte/Personen: al-Ḥamawiyyah, al-Wāsiṭiyyah, Ḥamāh, Ḥarrān, ar-Rāzī (Faḫr ad-Dīn), al-Juwaynī, al-Ġazālī, aš-Šahrastānī, al-Āmidī, Bišr al-Marīsī, Jaʿd ibn Dirham, Jahm ibn Ṣafwān, ad-Dārimī, al-Lālakāʾī, Ibn Baṭṭah, al-Bayhaqī, Imam Mālik, Aḥmad, aš-Šāfiʿī, Abū Ḥanīfah, al-Buḫārī, Muslim, Abū Dāwūd, at-Tirmiḏī, Ibn Māja, Ibn al-Qayyim, aṭ-Ṭabarī, Ibn ʿAbbās, Mujāhid.
- Titel in Anführung/Kursiv: *al-Wāsiṭiyyah*. Arabische Fachbegriffe kursiv beim ersten Auftreten im Abschnitt, danach normal. Keine Doppelschreibungen (kein "Dschahmiyyah", "Aschā'irah", "Taymiyya").

## Terminologie (aus früheren Reviews, verbindlich)
naṣṣ = „eindeutiger Wortlaut“ ; ẓāhir = „offenkundige Bedeutung“ ; al-mutakallifūn = „Scholastiker“ bzw. „sich unnötig Bemühende“ ; ṭawāġīt = „falsche Richter“ (im Schiedskontext, sonst Götzen) ; ummah = „Gemeinschaft (Ummah)“ ; risālah = „Botschaft“ ; maqāyīs = „Analogien“ ; Muhājirūn/Anṣār = „Auswanderer und Helfer“ ; Überprüft von … nicht relevant. Kapitel „Einleitung“ (Muqaddimah). Weitere Standardwörter: Eigenschaften (Ṣifāt), Namen und Eigenschaften Allahs, Erhabenheit (ʿuluww), Erheben (istiwāʾ), Verähnlichung (tamthīl), Ablehnung/Entleerung (taʿṭīl), Verfälschung (taḥrīf), Art und Weise (kayfiyyah/takyīf), Anvertrauen (tafwīḍ).
- Stil wie bisherige Ḥamawiyyah-Übersetzung: klar, präzise, nicht hochgestochen; eingeschobene Ergänzungen des Übersetzers in [eckigen Klammern]; Qurʾān inline als {{Text|Sure:Vers}}.

## Markup (content/*.txt)
```
# Teil I – Titel | Untertitel          (neue Seite, Teilüberschrift)
## Abschnittstitel                      (nummeriert automatisch)
[[MATN]] ... [[/MATN]]                  (Absätze durch Leerzeile; Matn-Block)
[[MATN Eigene Beschriftung]] ... [[/MATN]]
[[SHARH]] ... [[/SHARH]]
### Zwischenüberschrift (innerhalb Šarḥ)
- Aufzählung  /  1. nummerierte Aufzählung (nur wenn alle Zeilen so beginnen)
[[Q 20:5]]  ar: (optional Fragment ohne Vokalzeichen)  de: deutsche Übersetzung  [[/Q]]   (Arabisch wird aus dem Datensatz geholt+geprüft; ar: - = ohne Arabisch)
[[H Quelle]] Text [[/H]]  (Ḥadīth-Box)   [[P]] Zeilen [[/P]] (Gedicht)   [[NOTE]] ... [[/NOTE]] (redaktionelle Anmerkung)   [[SRC Quelle]]
{{Text|35:10}} = Qurʾān-Zitat im Satz;  *kursiv*  **fett**  [[eckige Ergänzung]] = redaktionelle Einfügung (wird kursiv in [ ])
[ar]...[/ar] = arabischer Einschub
```
- Keine Fußnoten für den Šarḥ. Quellenangaben nur aus den Materialien (Endnoten der Muqaddimah; vom Šāriḥ genannte). Nichts erfinden.

## Redaktionsregeln für den Šarḥ
- Aus Klassengespräch wird fließende Schrift: keine Anreden an Teilnehmer ("Ichwān", "antwortet mir", Chat, Namen der Teilnehmer, Aufnahme-/Technikhinweise, Zeit-/Pausen-/Terminorganisation, Werbung für Ijāzah etc.).
- Rhetorische Fragen des Unterrichts bleiben als "Man fragt: ... Antwort: ..." erhalten, wenn inhaltlich tragend.
- Beispiele des Šāriḥ bleiben (Löwe 80/20, Pijesak=Sand, Schüssel/Saft, Vogel-Flügel, Schwert/Stock usw.), Namen von Teilnehmern in Beispielen werden neutralisiert.
- Unsichere Angaben des Šāriḥ ("ich glaube") – Nebensächliches weglassen; Wichtiges mit "vermutlich/nach dem Šāriḥ" kennzeichnen; Zahlen nur wenn sicher.
- Wiederholungen am Stundenanfang ("Wir sind stehen geblieben bei ...") streichen/zusammenführen.
- Der Šāriḥ spricht in "wir/ich": darf als "wir" bleiben (Lehrerstimme) oder zu "man" werden; konsistent halten: bevorzugt neutral/"man", gelegentlich "wir" (z. B. "wie wir in al-Wāsiṭiyyah gesehen haben" -> "wie in al-Wāsiṭiyyah erklärt wurde").
- Starke Wertungen/Verwünschungen des Šāriḥ sinngemäß erhalten, aber nüchtern formulieren (Takfīr-Aussagen als Aussage des Šāriḥ bzw. der zitierten Gelehrten kennzeichnen).
