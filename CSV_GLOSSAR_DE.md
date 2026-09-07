# CSV-Spalten und Fußballkennzahlen erklärt

Deutschsprachiges Nachschlagewerk für alle **110 Spalten** in [bundesliga_2025_26_all_players.csv](bundesliga_2025_26_all_players.csv). Stand: 05.09.2026, Saison 2025/26. Die Tabellen folgen der Reihenfolge der CSV.

## Schnellstart für deinen 3D-Plot

| Achse | CSV-Spalte | Bedeutung |
| --- | --- | --- |
| X | `fbref_standard_playing_time_min` | Gespielte Minuten |
| Y | `fbref_standard_age` | Alter am Saisonbeginn |
| Z | `fbref_standard_performance_gls` | Tore insgesamt |
| Alternative Z | `fbref_standard_per_90_minutes_gls` | Tore pro 90 Minuten |
| Beschriftung | `player` und `team` | Spielername und Verein |

Bei Toren pro 90 Minuten hilft ein Mindestminutenfilter: Ein Tor in 10 Minuten entspricht 9 Toren pro 90 und ist keine belastbare Saisonleistung.

## So liest du die Spaltennamen

Beispiel: `fbref_standard_playing_time_min` bedeutet Quelle **FBref**, Tabelle **Standard**, Bereich **Spielzeit**, Kennzahl **Minuten**.

| Bestandteil | Bedeutung |
| --- | --- |
| `fbref` | Fußballstatistik-Website FBref; Hauptquelle |
| `bundesliga` | Offizielle Bundesliga-Website; ergänzende Quelle |
| `standard` | Basisstatistiken; innerhalb von shooting der Tabellenbereich mit Schusswerten |
| `shooting` | Schussstatistiken |
| `playing_time` | Einsatzzeit |
| `misc` | Miscellaneous: sonstige Aktionen |
| `keeper` | Torhüterstatistiken |
| `performance` | Leistungs-/Ereigniswerte |
| `per_90_minutes`, `per_90`, `90` am Kennzahlende | Auf 90 gespielte Minuten normiert |
| `team_success` | Mannschaftsergebnisse im Zusammenhang mit dem Einsatz des Spielers |
| `starts` / `subs` | Startelf / Einwechslungen |
| `penalty_kicks` | Elfmeter |
| `pct` | Percentage: Prozent; 75 bedeutet 75 %, nicht 0,75 |
| `per` | „pro“ bzw. geteilt durch; ersetzt meist einen Schrägstrich |
| `plus` / `plus_minus` | Pluszeichen / Tordifferenz |
| `km` / `kmh` | Kilometer / Kilometer pro Stunde |

**Achtung bei Minuszeichen:** Die Namensbereinigung entfernt Bindestriche. `g_pk` steht für **G−PK**, `g_plus_a_pk` für **G+A−PK**. Die Abkürzung `90s` steht für Minuten geteilt durch 90, nicht für Sekunden.

## Grundregeln zur Interpretation

- Eine Zeile ist ein Spieler-/Vereins-/Saisondatensatz. Bei Vereinswechseln sind mehrere Zeilen für denselben Spieler möglich.
- Zählwerte sind grundsätzlich Summen für den jeweiligen Datensatz. Quoten, Durchschnitte, Alter und Höchstgeschwindigkeit sind keine Summen.
- Fehlend bedeutet **unbekannt/nicht verfügbar**, nicht null. Für einen Plot mit drei Achsen nur Zeilen mit allen drei Werten verwenden und die ausgeschlossene Anzahl anzeigen.
- FBref-Felder werden aus mehreren Tabellen übernommen. Alter, Position, Minuten, Tore usw. kommen deshalb mehrfach vor; sie sind keine zusätzlichen unabhängigen Leistungen. Nicht addieren. Für allgemeine Achsen bevorzugt die Standard-Tabelle verwenden.
- Bundesliga-Ranglisten sind spielerbezogen und werden über Namen angefügt. Bei mehrdeutigen Namen oder mehreren FBref-Zeilen lässt der Downloader die Werte im Regelfall fehlen. Aus ihnen keine vereinsbezogenen Teilwerte erfinden.
- Torhüterspalten sind für Feldspieler normalerweise leer.
- Die aktuell geprüfte CSV nutzt **Semikolon als Trennzeichen und Dezimalkomma**. Beispiel: `pd.read_csv(datei, sep=";", decimal=",")`. Nach einer Neuerstellung das tatsächliche Exportformat prüfen.
- `pro 90 = Wert × 90 / Minuten`. Keine Division bei null oder fehlenden Minuten. Bereits normierte Werte nicht nochmals normieren.

## 1. Identifikation

| Exakte CSV-Spalte | Abkürzung / Englisch | Deutsche Erklärung und Einheit |
| --- | --- | --- |
| `player` | Player | Spielername in FBref-Schreibweise. |
| `team` | Team / Squad | Verein dieser Spieler-Saison-Zeile. |
| `season` | Season | Saisoncode; 2526 bedeutet 2025/26, nicht das Jahr 2526. |
| `league` | League | Wettbewerb; GER-Bundesliga bedeutet deutsche Bundesliga. |

## 2. FBref – Basisdaten

| Exakte CSV-Spalte | Abkürzung / Englisch | Deutsche Erklärung und Einheit |
| --- | --- | --- |
| `fbref_standard_nation` | Nation / Nationality | Nationalität bzw. Zuordnung zum Nationalverband; Text/Ländercode, keine Messzahl. |
| `fbref_standard_pos` | Pos / Position | Hauptposition(en); Positionscodes siehe unten. |
| `fbref_standard_age` | Age | Alter in Jahren am Saisonbeginn; laut FBref bei Winterligen am 1. August, hier 01.08.2025. Nicht das heutige Alter. |
| `fbref_standard_born` | Born | Geburtsjahr; Kalenderjahr. |
| `fbref_standard_playing_time_mp` | MP / Matches Played | Spiele mit Einsatz, auch kurze Einwechslungen; Anzahl. |
| `fbref_standard_playing_time_starts` | Starts | Spiele in der Startelf; Anzahl. |
| `fbref_standard_playing_time_min` | Min / Minutes | Gespielte Minuten; Summe. |
| `fbref_standard_playing_time_90s` | 90s / 90s Played | Gespielte Minuten geteilt durch 90; Anzahl rechnerischer voller Spiele, nicht Anzahl Einsätze. |
| `fbref_standard_performance_gls` | Gls / Goals | Erzielte Tore einschließlich verwandelter Elfmeter; Anzahl. Eigentore werden separat erfasst. |
| `fbref_standard_performance_ast` | Ast / Assists | Torvorlagen gemäß FBref; Anzahl. |
| `fbref_standard_performance_g_plus_a` | G+A / Goals + Assists | Tore plus Torvorlagen; Anzahl direkter Torbeteiligungen. |
| `fbref_standard_performance_g_pk` | G-PK / Non-Penalty Goals | Tore ohne verwandelte Elfmeter; Gls − PK. Nicht nur Tore aus dem offenen Spiel: z. B. direkte Freistöße zählen mit. |
| `fbref_standard_performance_pk` | PK / Penalty Kicks Made | Verwandelte Elfmeter; Anzahl. |
| `fbref_standard_performance_pkatt` | PKatt / Penalty Kicks Attempted | Geschossene Elfmeter einschließlich Fehlversuchen; Anzahl. |
| `fbref_standard_performance_crdy` | CrdY / Yellow Cards | Gelbe Karten; Anzahl gemäß FBref. |
| `fbref_standard_performance_crdr` | CrdR / Red Cards | Rote Karten; Anzahl gemäß FBref. Gelb-Rot steht zusätzlich unter 2CrdY; Kategorien nicht ungeprüft addieren. |
| `fbref_standard_per_90_minutes_gls` | Gls / Goals per 90 | Tore je 90 gespielte Minuten. |
| `fbref_standard_per_90_minutes_ast` | Ast / Assists per 90 | Torvorlagen je 90 Minuten. |
| `fbref_standard_per_90_minutes_g_plus_a` | G+A / Goals + Assists per 90 | Tore plus Torvorlagen je 90 Minuten. |
| `fbref_standard_per_90_minutes_g_pk` | G-PK / Non-Penalty Goals per 90 | Tore ohne Elfmeter je 90 Minuten. |
| `fbref_standard_per_90_minutes_g_plus_a_pk` | G+A-PK / Non-Penalty Goals + Assists per 90 | Tore plus Torvorlagen minus verwandelte Elfmeter, je 90 Minuten. |

## 3. FBref – Schüsse

| Exakte CSV-Spalte | Abkürzung / Englisch | Deutsche Erklärung und Einheit |
| --- | --- | --- |
| `fbref_shooting_nation` | Nation / Nationality | Nationalität bzw. Zuordnung zum Nationalverband; Text/Ländercode, keine Messzahl. |
| `fbref_shooting_pos` | Pos / Position | Hauptposition(en); Positionscodes siehe unten. |
| `fbref_shooting_age` | Age | Alter in Jahren am Saisonbeginn; laut FBref bei Winterligen am 1. August, hier 01.08.2025. Nicht das heutige Alter. |
| `fbref_shooting_born` | Born | Geburtsjahr; Kalenderjahr. |
| `fbref_shooting_90s` | 90s / 90s Played | Gespielte Minuten geteilt durch 90; Anzahl rechnerischer voller Spiele, nicht Anzahl Einsätze. |
| `fbref_shooting_standard_gls` | Gls / Goals | Erzielte Tore einschließlich verwandelter Elfmeter; Anzahl. Eigentore werden separat erfasst. |
| `fbref_shooting_standard_sh` | Sh / Shots | Schüsse insgesamt; Anzahl gemäß aktueller FBref-Tabelle. Siehe Hinweis zur Elfmeterbehandlung unten. |
| `fbref_shooting_standard_sot` | SoT / Shots on Target | Schüsse auf das Tor; Anzahl. Nicht mit allen Schussversuchen gleichsetzen. |
| `fbref_shooting_standard_sotpct` | SoT% / Shots on Target Percentage | Anteil der Schüsse auf das Tor: 100 × SoT / Sh; Prozent. |
| `fbref_shooting_standard_sh_per_90` | Sh/90 / Shots per 90 | Schüsse je 90 Minuten. |
| `fbref_shooting_standard_sot_per_90` | SoT/90 / Shots on Target per 90 | Schüsse auf das Tor je 90 Minuten. |
| `fbref_shooting_standard_g_per_sh` | G/Sh / Goals per Shot | Tore je Schuss; Verhältnis, kein Prozentwert. 0,30 entspricht 30 Toren je 100 Schüsse. FBref-Wert übernehmen; siehe Hinweis unten. |
| `fbref_shooting_standard_g_per_sot` | G/SoT / Goals per Shot on Target | Tore je Schuss auf das Tor; Verhältnis, kein Prozentwert. |
| `fbref_shooting_standard_pk` | PK / Penalty Kicks Made | Verwandelte Elfmeter; Anzahl. |
| `fbref_shooting_standard_pkatt` | PKatt / Penalty Kicks Attempted | Geschossene Elfmeter einschließlich Fehlversuchen; Anzahl. |

## 4. FBref – Einsatzzeit und Mannschaftserfolg

| Exakte CSV-Spalte | Abkürzung / Englisch | Deutsche Erklärung und Einheit |
| --- | --- | --- |
| `fbref_playing_time_nation` | Nation / Nationality | Nationalität bzw. Zuordnung zum Nationalverband; Text/Ländercode, keine Messzahl. |
| `fbref_playing_time_pos` | Pos / Position | Hauptposition(en); Positionscodes siehe unten. |
| `fbref_playing_time_age` | Age | Alter in Jahren am Saisonbeginn; laut FBref bei Winterligen am 1. August, hier 01.08.2025. Nicht das heutige Alter. |
| `fbref_playing_time_born` | Born | Geburtsjahr; Kalenderjahr. |
| `fbref_playing_time_playing_time_mp` | MP / Matches Played | Spiele mit Einsatz, auch kurze Einwechslungen; Anzahl. |
| `fbref_playing_time_playing_time_min` | Min / Minutes | Gespielte Minuten; Summe. |
| `fbref_playing_time_playing_time_mn_per_mp` | Mn/MP / Minutes per Match Played | Durchschnittliche Minuten je Einsatz: Minuten / MP; Minuten. |
| `fbref_playing_time_playing_time_minpct` | Min% / Percentage of Minutes Played | Anteil der Mannschaftsspielzeit, während der der Spieler auf dem Platz stand; Prozent. Nicht durch die aufsummierten Minuten aller elf Spieler teilen. |
| `fbref_playing_time_playing_time_90s` | 90s / 90s Played | Gespielte Minuten geteilt durch 90; Anzahl rechnerischer voller Spiele, nicht Anzahl Einsätze. |
| `fbref_playing_time_starts_starts` | Starts | Startelfeinsätze; Anzahl. |
| `fbref_playing_time_starts_mn_per_start` | Mn/Start / Minutes per Start | Durchschnittliche Einsatzminuten in Spielen mit Startelfeinsatz; Minuten. |
| `fbref_playing_time_starts_compl` | Compl / Complete Matches | Vollständig absolvierte Spiele; Anzahl. |
| `fbref_playing_time_subs_subs` | Subs / Substitute Appearances | Spiele mit Einwechslung; Anzahl. Keine Auswechslungen. |
| `fbref_playing_time_subs_mn_per_sub` | Mn/Sub / Minutes per Substitution | Durchschnittliche gespielte Minuten bei Einwechslungen; Minuten. |
| `fbref_playing_time_subs_unsub` | unSub / Unused Substitute | Spiele als nicht eingesetzter Ersatzspieler auf der Bank; Anzahl. |
| `fbref_playing_time_team_success_ppm` | PPM / Points per Match | Durchschnittliche Mannschaftspunkte in Spielen mit Einsatz dieses Spielers; Punkte pro Spiel, normalerweise 0 bis 3. |
| `fbref_playing_time_team_success_ong` | onG / Goals For while On Pitch | Tore der eigenen Mannschaft während der Spieler auf dem Feld war; Anzahl, nicht seine persönlichen Tore. |
| `fbref_playing_time_team_success_onga` | onGA / Goals Against while On Pitch | Gegentore der Mannschaft während seiner Einsatzzeit; Anzahl. |
| `fbref_playing_time_team_success_plus_minus` | +/- / Plus-Minus | Tordifferenz während seiner Einsatzzeit: onG − onGA; Tore. |
| `fbref_playing_time_team_success_plus_minus90` | +/-90 / Plus-Minus per 90 | Tordifferenz während seiner Einsatzzeit je 90 Minuten. |
| `fbref_playing_time_team_success_on_off` | On-Off / Plus-Minus Net per 90 | Mannschafts-Tordifferenz pro 90 mit Spieler minus Tordifferenz pro 90 ohne Spieler; Tore je 90 Minuten. Positiv bedeutet bessere Bilanz mit ihm; kein kausaler Beweis seiner Wirkung. |

## 5. FBref – Sonstige Aktionen

| Exakte CSV-Spalte | Abkürzung / Englisch | Deutsche Erklärung und Einheit |
| --- | --- | --- |
| `fbref_misc_nation` | Nation / Nationality | Nationalität bzw. Zuordnung zum Nationalverband; Text/Ländercode, keine Messzahl. |
| `fbref_misc_pos` | Pos / Position | Hauptposition(en); Positionscodes siehe unten. |
| `fbref_misc_age` | Age | Alter in Jahren am Saisonbeginn; laut FBref bei Winterligen am 1. August, hier 01.08.2025. Nicht das heutige Alter. |
| `fbref_misc_born` | Born | Geburtsjahr; Kalenderjahr. |
| `fbref_misc_90s` | 90s / 90s Played | Gespielte Minuten geteilt durch 90; Anzahl rechnerischer voller Spiele, nicht Anzahl Einsätze. |
| `fbref_misc_performance_crdy` | CrdY / Yellow Cards | Gelbe Karten; Anzahl gemäß FBref. |
| `fbref_misc_performance_crdr` | CrdR / Red Cards | Rote Karten; Anzahl gemäß FBref. Gelb-Rot steht zusätzlich unter 2CrdY; Kategorien nicht ungeprüft addieren. |
| `fbref_misc_performance_2crdy` | 2CrdY / Second Yellow Card | Platzverweise durch zweite gelbe Karte (Gelb-Rot); Anzahl. |
| `fbref_misc_performance_fls` | Fls / Fouls Committed | Begangene Fouls; Anzahl. |
| `fbref_misc_performance_fld` | Fld / Fouls Drawn | Erhaltene Fouls: Wie oft der Spieler gefoult wurde; Anzahl. |
| `fbref_misc_performance_off` | Off / Offsides | Abseitsstellungen; Anzahl. Nicht mit On-Off verwechseln. |
| `fbref_misc_performance_crs` | Crs / Crosses | Flanken gemäß FBref; Anzahl. Nicht automatisch dieselbe Abgrenzung wie Bundesliga-Flanken aus dem offenen Spiel. |
| `fbref_misc_performance_int` | Int / Interceptions | Abgefangene gegnerische Pässe; Anzahl. Hier keine intensiven Läufe. |
| `fbref_misc_performance_tklw` | TklW / Tackles Won | Tacklings, nach denen die Mannschaft des tackelnden Spielers Ballbesitz gewinnt; Anzahl. Nicht alle gewonnenen Zweikämpfe. |
| `fbref_misc_performance_pkwon` | PKwon / Penalty Kicks Won | Herausgeholte Elfmeter; Anzahl, unabhängig vom anschließenden Torerfolg. |
| `fbref_misc_performance_pkcon` | PKcon / Penalty Kicks Conceded | Verursachte Elfmeter; Anzahl. |
| `fbref_misc_performance_og` | OG / Own Goals | Eigentore; Anzahl. |

## 6. FBref – Torhüter

| Exakte CSV-Spalte | Abkürzung / Englisch | Deutsche Erklärung und Einheit |
| --- | --- | --- |
| `fbref_keeper_nation` | Nation / Nationality | Nationalität bzw. Zuordnung zum Nationalverband; Text/Ländercode, keine Messzahl. |
| `fbref_keeper_pos` | Pos / Position | Hauptposition(en); Positionscodes siehe unten. |
| `fbref_keeper_age` | Age | Alter in Jahren am Saisonbeginn; laut FBref bei Winterligen am 1. August, hier 01.08.2025. Nicht das heutige Alter. |
| `fbref_keeper_born` | Born | Geburtsjahr; Kalenderjahr. |
| `fbref_keeper_playing_time_mp` | MP / Matches Played | Spiele mit Einsatz, auch kurze Einwechslungen; Anzahl. |
| `fbref_keeper_playing_time_starts` | Starts | Spiele in der Startelf; Anzahl. |
| `fbref_keeper_playing_time_min` | Min / Minutes | Gespielte Minuten; Summe. |
| `fbref_keeper_playing_time_90s` | 90s / 90s Played | Gespielte Minuten geteilt durch 90; Anzahl rechnerischer voller Spiele, nicht Anzahl Einsätze. |
| `fbref_keeper_performance_ga` | GA / Goals Against | Kassierte Gegentore während der Torhütereinsatzzeit; Anzahl. |
| `fbref_keeper_performance_ga90` | GA90 / Goals Against per 90 | Gegentore je 90 Minuten im Tor. |
| `fbref_keeper_performance_sota` | SoTA / Shots on Target Against | Gegnerische Schüsse auf das Tor; Anzahl. |
| `fbref_keeper_performance_saves` | Saves | Paraden bzw. abgewehrte Schüsse; Anzahl gemäß FBref. |
| `fbref_keeper_performance_savepct` | Save% / Save Percentage | Abwehrquote; Prozent. FBref beschreibt 100 × (SoTA − GA) / SoTA und weist darauf hin, dass auch Feldspieler Schüsse auf das Tor abwehren können. |
| `fbref_keeper_performance_w` | W / Wins | Siege in der Torhüterstatistik; Anzahl. |
| `fbref_keeper_performance_d` | D / Draws | Unentschieden in der Torhüterstatistik; Anzahl. |
| `fbref_keeper_performance_l` | L / Losses | Niederlagen in der Torhüterstatistik; Anzahl. |
| `fbref_keeper_performance_cs` | CS / Clean Sheets | Vollständig absolvierte Torhüterspiele ohne Gegentor; Anzahl. |
| `fbref_keeper_performance_cspct` | CS% / Clean Sheet Percentage | Anteil der Spiele ohne Gegentor gemäß FBref; Prozent. |
| `fbref_keeper_penalty_kicks_pkatt` | PKatt / Penalty Kicks Attempted | Gegnerische Elfmeter gegen den Torhüter; Anzahl. Im Feldspielerbereich meint PKatt eigene Versuche. |
| `fbref_keeper_penalty_kicks_pka` | PKA / Penalty Kicks Allowed | Durch gegnerische Elfmeter kassierte Tore; Anzahl. |
| `fbref_keeper_penalty_kicks_pksv` | PKsv / Penalty Kicks Saved | Gehaltene gegnerische Elfmeter; Anzahl. |
| `fbref_keeper_penalty_kicks_pkm` | PKm / Penalty Kicks Missed | Gegnerische Elfmeter, die das Tor verfehlen; Anzahl. Nicht als gehaltene Elfmeter zählen. |
| `fbref_keeper_penalty_kicks_savepct` | Save% / Penalty Save Percentage | Elfmeter-Abwehrquote: 100 × PKsv / (PKatt − PKm); Prozent. Fehlschüsse werden aus dem Nenner ausgeschlossen. Siehe Quellenhinweis zum widersprüchlichen FBref-Tooltip. |

## Positionscodes

| Code | Englisch | Deutsch |
| --- | --- | --- |
| GK | Goalkeeper | Torhüter |
| DF | Defender | Verteidiger |
| MF | Midfielder | Mittelfeldspieler |
| FW | Forward | Angreifer |
| FB | Fullback | Außenverteidiger |
| LB / RB | Left / Right Back | Linker / rechter Außenverteidiger |
| CB | Centre Back | Innenverteidiger |
| DM | Defensive Midfielder | Defensives Mittelfeld |
| CM | Central Midfielder | Zentrales Mittelfeld |
| LM / RM | Left / Right Midfielder | Linkes / rechtes Mittelfeld |
| WM | Wide Midfielder | Außenmittelfeld |
| LW / RW | Left / Right Winger | Linksaußen / Rechtsaußen |
| AM | Attacking Midfielder | Offensives Mittelfeld |

Kombinationen wie `DF,MF` bedeuten mehrere Positionszuordnungen. Die Tabelle erklärt auch FBref-Unterpositionen, die nicht zwingend in dieser CSV vorkommen.

## Beispiele und Abgrenzungen

- **Minuten vs. Einsätze:** 900 Minuten entsprechen 10 `90s`, können aber auf 20 Einsätze verteilt sein.
- **Summe vs. Rate:** 10 Tore in 1.800 Minuten ergeben 0,50 Tore pro 90.
- **Quote vs. Verhältnis:** `sotpct = 40` bedeutet 40 % Schüsse auf das Tor; `g_per_sh = 0,20` bedeutet 0,20 Tore je Schuss.
- **Eigene Tore vs. Mannschaftstore:** `gls` sind persönliche Tore; `ong` zählt alle Tore der eigenen Mannschaft während der Einsatzzeit.
- **Zweikampf vs. Tackling:** Ein gewonnenes Luftduell ist nicht automatisch ein gewonnenes Tackling. Metriken verschiedener Anbieter nicht als austauschbar behandeln.
- **PPM und On-Off:** Beide hängen auch von Mannschaft, Gegnern und Einsatzsituationen ab. Sie sind keine isolierten Qualitätsnoten.
- **Fehlende Passzahl:** Die CSV enthält eine erfolgreiche-Pässe-Quote aus offenem Spiel, aber keine verlässliche absolute Zahl aller angekommenen Pässe.
- **Nicht vorhanden:** xG (Expected Goals, erwartete Tore), xA (Expected Assists, erwartete Torvorlagen) und progressive Pässe sind keine Spalten dieser CSV.

## Quellen, überprüfte Besonderheiten und Grenzen

### FBref

Die Definitionen wurden anhand der Kopfzeilen-Erklärungen der vom Downloader gespeicherten **Spielertabellen** geprüft. Lokale Belege liegen unter `C:/Users/grund/soccerdata/data/FBref/players_GER-Bundesliga_2526_<tabelle>.html`; dieser Cache ist nicht Teil des Repositorys.

Online-Quellen: [Basisdaten](https://fbref.com/en/comps/20/2025-2026/standard/2025-2026-Bundesliga-Stats), [Schüsse](https://fbref.com/en/comps/20/2025-2026/shooting/2025-2026-Bundesliga-Stats), [Einsatzzeit](https://fbref.com/en/comps/20/2025-2026/playingtime/2025-2026-Bundesliga-Stats), [Sonstige Aktionen](https://fbref.com/en/comps/20/2025-2026/misc/2025-2026-Bundesliga-Stats), [Torhüter](https://fbref.com/en/comps/20/2025-2026/keepers/2025-2026-Bundesliga-Stats).

**Schussquoten und Elfmeter:** Keine historische FBref-Konvention ungeprüft übernehmen. In der aktuellen CSV hat Harry Kane 36 Tore, 119 Schüsse, 10 Elfmetertore und `G/Sh = 0,30`. Das passt gerundet zu 36/119, nicht zu (36−10)/119. Das ist eine Prüfung dieses Datensatzes, keine universelle Aussage für alle FBref-Saisons. Die gespeicherten Quoten unverändert verwenden und Elfmeter bei eigenen Berechnungen ausdrücklich definieren.

**Elfmeter-Abwehrquote:** Der gespeicherte FBref-Tooltip ist widersprüchlich: Er bezeichnet das Feld als Abwehrquote, nennt aber Gegentore im Formeltext. Die CSV-Werte stützen stattdessen `100 × gehalten / (Versuche − Fehlschüsse)`: 10 Versuche, 2 gehalten und 2 verfehlt ergeben 25 %. Die Erklärung oben folgt den beobachteten Werten und der Bedeutung „Abwehrquote“; der Widerspruch ist damit offengelegt.

### Bundesliga.com

Die neun Zusatzfelder stammen aus den [Spielerranglisten 2025/26](https://www.bundesliga.com/en/bundesliga/stats/players/sprints/2025-2026). Die jeweiligen Statistiknamen und URLs sind in `BUNDESLIGA_STATS` in [data_downloader.py](data_downloader.py) hinterlegt.

**Neue Sprintdefinition:** Ab 2025/26 gilt über 25 km/h bei mindestens 0,5 Sekunden im Bereich. Schnelles Rennen/Tempolauf liegt bei über 20 bis 25 km/h, ebenfalls mindestens 0,5 Sekunden. Deshalb Sprints nicht direkt mit Vorjahreszahlen vergleichen. Die genaue Aggregation des Ranglistenfeldes „Intensive runs“ wurde durch diese Quelle nicht eindeutig aufgelöst. [Offizielle Änderungen 2025/26, Abschnitt Tempobereiche](https://www.bundesliga.com/de/bundesliga/news/schiedsrichter-durchsagen-spieler-tracking-abseits-anderungen-saison-2025-26-33291).

### Vollständigkeit

Alle 110 CSV-Spalten sind oben einzeln aufgeführt; auch wiederholte Felder haben eine eigene Zeile. Das Glossar erklärt die Bedeutung, bestätigt aber nicht die Richtigkeit jedes einzelnen heruntergeladenen Werts. Bei neuen Spalten muss es ergänzt werden.

