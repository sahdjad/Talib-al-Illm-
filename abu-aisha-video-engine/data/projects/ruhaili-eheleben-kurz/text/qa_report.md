# QA-Bericht – ruhaili-eheleben-kurz

- Sprecher: الشيخ سليمان الرحيلي حفظه الله (Shaykh Sulaymān ar-Ruḥaylī ḥafiẓahullāh) – Quelle der Identität: Nutzer
- Quelle: drosuae.ae (دروس الإمارات) – Reihe „فقه عوارض الزوجية“
- Verwendeter Bereich: 6.90–60.00 s (53.10 s) · Intro: ja, 4.0 s
- Modus: video · Maske: 0.428–0.588 (automatisch)
- Titel: DE „Was macht das Eheleben schön?“ · EN “What makes married life beautiful?”
- ASR: sherpa-onnx / sherpa-onnx-whisper-large-v3
- Redaktion: claude-code-session (Claude, interaktive Redaktion nach packages/prompts) · Prompts: arabic_cleanup_v1, de_translation_v1, semantic_segmentation_v1, en_from_de_v1, religious_reference_detection_v1, title_generation_v1
- Status: **READY_FOR_REVIEW**

## Qualitäts-Gates (§28)

| # | Gate | OK | Detail |
|---|------|----|--------|
| 1 | Audio vorhanden, Dauer = Quellbereich | ✅ | 53.100s vs 53.100s |
| 2 | Arabisches Transkript vorhanden | ✅ |  |
| 3 | Jeder Block hat DE | ✅ |  |
| 4 | Jeder Block hat aktuelles EN | ✅ |  |
| 5 | Kein Untertitel verlässt den sicheren Bereich | ✅ |  |
| 6 | Branding kollidiert nicht mit Untertiteln | ✅ | Untertitel ≤1470 · Quellenzeile 1484–1560 · Branding 1574–1710 |
| 7 | Intro-Länge exakt wie konfiguriert | ✅ | 4.0s |
| 8 | Kein CHECK_REQUIRED als verifiziert gerendert | ✅ |  |
| 9 | Redaktioneller Kontext visuell getrennt | ✅ | Quellenzeile 40px vs. kleinster Untertitel 68px, eigene Farbe & Spur |
| 10 | DE/EN-Timeline synchron | ✅ | gemeinsame Timing-Map |
| 11 | Keine Blitz-Lücken zwischen Blöcken | ✅ |  |
| 12 | Render öffnet und enthält Audio | ✅ | de: 57.10s, en: 57.10s |

## Zu prüfen

- **UNSICHERES_ARABISCH** @ 01:01.07 „الفضلاء“: Clip endet mitten im Wort/Satz – „الفضلاء“ ist eine Rekonstruktion, bitte anhören.
- **UNSICHERES_ARABISCH** @ 00:09.32 „الزوجين“: „الزوجين“ aus Neudekodierung übernommen – kurz anhören.
- **TRANSKRIPT_KORREKTUR** @ 00:09.32 „الزوج → الزوجين“: Phrase endet am VAD-Schnitt; Neudekodierung mit weiterem Audiofenster (7,5–10,1 s) ergibt eindeutig „بين الزوجين“; nach „بين“ grammatisch erforderlich.
- **TRANSKRIPT_KORREKTUR** @ 01:01.07 „الفضاء → الفضلاء“: „أيها الفضاء“ ist sinnlos; übliche Anrede an das Publikum ist „أيها الفضلاء“. Wort liegt am abgeschnittenen Clip-Ende – unsicher.
- **REDAKTIONELLE_ERGÄNZUNG** @ 00:01.40 „📚 فقه عوارض الزوجية“: source · VERIFIED_EXACT · eingeblendet
- **LESEGESCHWINDIGKEIT**: DE seg_002: 26.6 Zeichen/s bei 2.52s
- **LESEGESCHWINDIGKEIT**: EN seg_002: 21.4 Zeichen/s bei 2.52s
- **NOTIZ** @ 00:01.53 „seg_001“: Clip beginnt mit der Fortsetzung eines vorherigen Satzes (Bezug fehlt) – siehe Trim-Vorschlag.
- **NOTIZ** @ 00:11.16 „seg_003“: همة = Eifer/Tatkraft; أمر حسن نافع = eine gute, nützliche Sache.
- **NOTIZ** @ 00:23.42 „seg_006“: نوع من التجاوز في الأمر = eine Art Überschreitung/Übermaß in der Sache – bewusst nicht verschärft.
- **NOTIZ** @ 00:37.76 „seg_010“: عناية بأمر حسن = Sorgfalt/Einsatz für eine gute Sache.
- **NOTIZ** @ 00:48.86 „seg_013“: فتطيب الحياة – Pointe als eigener Block (semantische Teilung innerhalb einer Sprechphrase).
- **NOTIZ** @ 00:51.26 „seg_014“: ويتشارك الزوجان في أن يأخذ كل واحد منهما … = die Eheleute haben gemeinsam Anteil daran, dass jeder …
- **NOTIZ** @ 01:00.19 „seg_016“: Angeschnittener neuer Satz am Clip-Ende – siehe Trim-Vorschlag.
- **TRIM_VORSCHLAG**: 6.9–60.0 s: Der Clip beginnt mit der Fortsetzung eines vorherigen Satzes (0–5,5 s: „ما دام أنه من الأمور النافعة“) und endet mit einem angeschnittenen neuen Satz (ab 60,2 s: „هذه أيها الفضلاء“). Der eigenständige Gedanke läuft von 7,6 s bis 59,7 s. Nur Vorschlag – der Standard-Render nutzt den vollständigen Clip.

## Freigabe-Checkliste

- [ ] Speaker korrekt?
- [ ] Arabisches Transkript an markierten Stellen korrekt?
- [ ] Deutsche Bedeutung freigegeben?
- [ ] Englisch spiegelt das Deutsche?
- [ ] Quellen freigegeben?
- [ ] Redaktionelle Ergänzungen klar getrennt?
- [ ] Visuelles Layout akzeptabel?

Erst nach dieser Prüfung: APPROVED. Keine automatische Veröffentlichung (v1).
